# TODO: is Lock still required?
import select
from threading import Lock
import time

import pycurl
import six

from grab.util.log import PycurlSigintHandler
from grab.error import GrabTooManyRedirectsError
from grab.transport.curl import build_grab_exception
from grab.spider.base_service import BaseService

ERROR_TOO_MANY_REFRESH_REDIRECTS = -2
#ERROR_INTERNAL_GRAB_ERROR = -3
ERROR_ABBR = {
    ERROR_TOO_MANY_REFRESH_REDIRECTS: 'too-many-refresh-redirects',
    #ERROR_INTERNAL_GRAB_ERROR: 'internal-grab-error',
}
for key in dir(pycurl):
    if key.startswith('E_'):
        abbr = key[2:].lower().replace('_', '-')
        ERROR_ABBR[getattr(pycurl, key)] = abbr


class NetworkServiceMulticurl(BaseService):
    def __init__(self, spider, socket_number):
        """
        Args:
            spider: argument is not used in multicurl transport
        """

        self.spider = spider
        self.socket_number = socket_number
        self.multi = pycurl.CurlMulti()
        self.multi.handles = []
        self.freelist = []
        self.registry = {}
        self.connection_count = {}
        self.sigint_handler = PycurlSigintHandler()
        self.network_op_lock = Lock()

        # Create curl instances
        for _ in six.moves.range(self.socket_number):
            curl = pycurl.Curl()
            self.connection_count[id(curl)] = 0
            self.freelist.append(curl)
            # self.multi.handles.append(curl)

        self.spawner = self.create_worker(self.spawner_callback)
        self.async_loop = self.create_worker(self.async_loop_callback)
        self.register_workers(self.spawner, self.async_loop)

    def async_loop_callback(self, worker):
        while not worker.stop_event.is_set():
            worker.process_pause_signal()
            self.process_handlers()
            time.sleep(0.01)

    def spawner_callback(self, worker):
        while not worker.stop_event.is_set():
            worker.process_pause_signal()
            if self.get_free_threads_number():
                task = self.spider.get_task_from_queue()
                if task is None or task is True:
                    time.sleep(0.1)
                else:
                    worker.is_busy_event.set()
                    try:
                        task.network_try_count += 1 # pylint: disable=no-member
                        is_valid, reason = self.spider.check_task_limits(task)
                        if is_valid:
                            grab = self.spider.setup_grab_for_task(task)
                            self.spider.submit_task_to_transport(task, grab)
                        else:
                            self.spider.log_rejected_task(task, reason)
                            # pylint: disable=no-member
                            handler = task.get_fallback_handler(self.spider)
                            # pylint: enable=no-member
                            if handler:
                                handler(task)
                    finally:
                        worker.is_busy_event.clear()

            for result, task in self.iterate_results():
                self.spider.task_dispatcher.input_queue.put(
                    (result, task, None),
                )

    def ready_for_task(self):
        return len(self.freelist)

    def get_free_threads_number(self):
        return len(self.freelist)

    def get_active_threads_number(self):
        return self.socket_number - len(self.freelist)

    def process_connection_count(self, curl):
        curl_id = id(curl)
        self.connection_count[curl_id] += 1
        if self.connection_count[curl_id] > 100:
            del self.connection_count[curl_id]
            del curl
            new_curl = pycurl.Curl()
            self.connection_count[id(new_curl)] = 1
            return new_curl
        else:
            return curl

    def start_task_processing(self, task, grab, grab_config_backup):
        curl = self.process_connection_count(self.freelist.pop())

        self.registry[id(curl)] = {
            'grab': grab,
            'grab_config_backup': grab_config_backup,
            'task': task,
        }
        grab.transport.curl = curl
        try:
            grab.prepare_request()
            # Enable pycurl built-in redirect processing
            # In non-spider mode Grab handles redirects itself
            # by parsing headers and following Location URls
            # In spider mode that would require to create
            # new Task objects for each 30* redirect
            # Maybe that would be implemented in future
            # For now multicurl transport just uses builtin pycurl
            # ability to handle 30* redirects
            grab.transport.curl.setopt(
                pycurl.FOLLOWLOCATION,
                1 if grab.config['follow_location'] else 0
            )
            grab.log_request()
        except Exception:
            # If some error occurred while processing the request arguments
            # then we should put curl object back to free list
            del self.registry[id(curl)]
            self.freelist.append(curl)
            raise
        else:
            # Add configured curl instance to multi-curl processor
            try:
                self.network_op_lock.acquire()
                with self.sigint_handler.handle_sigint():
                    self.multi.add_handle(curl)
            finally:
                self.network_op_lock.release()

    def process_handlers(self):
        try:
            self.network_op_lock.acquire()
            with self.sigint_handler.handle_sigint():
                rlist, wlist, xlist = self.multi.fdset()
            if rlist or wlist or xlist:
                with self.sigint_handler.handle_sigint():
                    timeout = self.multi.timeout()
                if timeout and timeout > 0:
                    select.select(rlist, wlist, xlist, timeout / 1000.0)
            else:
                pass
            while True:
                with self.sigint_handler.handle_sigint():
                    status, _ = self.multi.perform()
                if status != pycurl.E_CALL_MULTI_PERFORM:
                    break
        finally:
            self.network_op_lock.release()

    def iterate_results(self):
        while True:
            try:
                self.network_op_lock.acquire()
                with self.sigint_handler.handle_sigint():
                    queued_messages, ok_list, fail_list = (
                        self.multi.info_read()
                    )
            finally:
                self.network_op_lock.release()
            #except Exception as ex:
            #    # Usually that should not happen
            #    logging.error('', exc_info=ex)
            #    continue

            results = []
            for curl in ok_list:
                results.append((True, curl, None, None, None))
            for curl, ecode, emsg in fail_list:
                curl.grab_callback_interrupted = False
                try:
                    raise pycurl.error(ecode, emsg)
                except Exception as exc: # pylint: disable=broad-except
                    grab_exc = build_grab_exception(exc, curl)
                # grab_exc could be None if the pycurl error
                # was expected (could be in case of
                # body_maxsize and other options)
                if grab_exc:
                    results.append((False, curl, ecode, emsg, grab_exc))
                else:
                    results.append((True, curl, None, None, None))

            for is_ok, curl, ecode, emsg, grab_exc in results:
                # FORMAT: {is_ok, grab, grab_config_backup, task,
                #          ecode, emsg, error_abbr, exc}

                curl_id = id(curl)
                task = self.registry[curl_id]['task']
                grab = self.registry[curl_id]['grab']
                grab_config_backup =\
                    self.registry[curl_id]['grab_config_backup']

                try:
                    self.network_op_lock.acquire()
                    grab.process_request_result()
                except GrabTooManyRedirectsError:
                    ecode = ERROR_TOO_MANY_REFRESH_REDIRECTS
                    emsg = 'Too many meta refresh redirects'
                    is_ok = False
                finally:
                    self.network_op_lock.release()
                #except Exception as ex:
                #    logging.error('', exc_info=ex)
                #    ecode = ERROR_INTERNAL_GRAB_ERROR
                #    emsg = 'Internal grab error'
                #    is_ok = False

                grab.doc.error_code = ecode
                grab.doc.error_msg = emsg
                grab.exception = grab_exc

                # Free resources
                del self.registry[curl_id]
                grab.transport.curl = None

                if is_ok:
                    error_abbr = None
                else:
                    error_abbr = ERROR_ABBR.get(ecode, 'unknown-%d' % ecode)
                yield {
                    'ok': is_ok,
                    'ecode': ecode,
                    'emsg': emsg,
                    'error_abbr': error_abbr,
                    'exc': grab_exc,
                    'grab': grab,
                    'grab_config_backup': grab_config_backup,
                }, task

                try:
                    self.network_op_lock.acquire()
                    with self.sigint_handler.handle_sigint():
                        self.multi.remove_handle(curl)
                finally:
                    self.network_op_lock.release()

                curl.reset()
                self.freelist.append(curl)

            if not queued_messages:
                break
