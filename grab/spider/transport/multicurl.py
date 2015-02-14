import pycurl
import select
import time

from grab.error import GrabTooManyRedirectsError
from grab.util.py3k_support import *


class MulticurlTransport(object):
    def __init__(self, thread_number):
        self.thread_number = thread_number
        self.multi = pycurl.CurlMulti()
        self.multi.handles = []
        self.freelist = []
        self.registry = {}
        self.connection_count = {}

        # Create curl instances
        for x in xrange(self.thread_number):
            curl = pycurl.Curl()
            self.connection_count[id(curl)] = 0
            self.freelist.append(curl)
            #self.multi.handles.append(curl)

    def ready_for_task(self):
        return len(self.freelist)

    def get_free_threads_number(self):
        return len(self.freelist)

    def active_task_number(self):
        return self.thread_number - len(self.freelist)

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

    def process_task(self, task, grab, grab_config_backup):
        curl = self.process_connection_count(self.freelist.pop())

        self.registry[id(curl)] = {
            'grab': grab,
            'grab_config_backup': grab_config_backup,
            'task': task,
        }
        grab.transport.curl = curl
        try:
            grab.prepare_request()
            grab.log_request()
        except Exception as ex:
            # If some error occurred while processing the request arguments
            # then we should put curl object back to free list
            del self.registry[id(curl)]
            self.freelist.append(curl)
            raise
        else:
            # Add configured curl instance to multi-curl processor
            self.multi.add_handle(curl)

    def process_handlers(self):
        # Ok, frankly I have real bad understanding of
        # how to deal with multicurl sockets ;-)
        # It is a sort of miracle that Grab is used by some people
        # and they managed to get job done
        rlist, wlist, xlist = self.multi.fdset()
        if rlist or wlist or xlist:
            timeout = self.multi.timeout()
            if timeout and timeout > 0:
                select.select(rlist, wlist, xlist, timeout / 1000.0)
        else:
            pass
            #time.sleep(0.1)
            # Ok, that that was a bad idea :D

        while True:
            status, active_objects = self.multi.perform()
            if status != pycurl.E_CALL_MULTI_PERFORM:
                break

    def iterate_results(self):
        while True:
            queued_messages, ok_list, fail_list = self.multi.info_read()

            results = []
            for curl in ok_list:
                results.append((True, curl, None, None))
            for curl, ecode, emsg in fail_list:
                # CURLE_WRITE_ERROR (23)
                # An error occurred when writing received data to a local file, or
                # an error was returned to libcurl from a write callback.
                # This exception should be ignored if _callback_interrupted flag
                # is enabled (this happens when nohead or nobody options enabeld)
                #
                # Also this error is raised when curl receives KeyboardInterrupt
                # while it is processing some callback function
                # (WRITEFUNCTION, HEADERFUNCTIO, etc)
                if ecode == 23:
                    if getattr(curl, '_callback_interrupted', None) is True:
                        curl._callback_interrupted = False
                        ecode = None
                        emsge = None
                        results.append((True, curl, None, None))
                    else:
                        results.append((False, curl, ecode, emsg))
                else:
                    results.append((False, curl, ecode, emsg))

            for ok, curl, ecode, emsg in results:
                # FORMAT: {ok, grab, grab_config_backup, task, emsg}

                curl_id = id(curl)
                task = self.registry[curl_id]['task']
                grab = self.registry[curl_id]['grab']
                grab_config_backup = self.registry[curl_id]['grab_config_backup']

                try:
                    grab.process_request_result()
                except GrabTooManyRedirectsError:
                    ecode = -1
                    emsg = 'Too many meta refresh redirects'
                grab.response.error_code = ecode
                grab.response.error_msg = emsg

                # Free resources
                del self.registry[curl_id]
                grab.transport.curl = None

                #if emsg and 'Operation timed out after' in emsg:
                    #num =  int(emsg.split('Operation timed out after')[1].strip().split(' ')[0])
                    #if num > 20000:
                        #import pdb; pdb.set_trace()

                yield {'ok': ok, 'emsg': emsg, 'grab': grab,
                       'grab_config_backup': grab_config_backup, 'task': task}

                self.multi.remove_handle(curl)
                self.freelist.append(curl)

            if not queued_messages:
                break
