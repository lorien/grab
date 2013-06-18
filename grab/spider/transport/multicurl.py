import pycurl

from grab.util.py3k_support import *

class MulticurlTransport(object):
    def __init__(self, thread_number):
        self.thread_number = thread_number
        self.multi = pycurl.CurlMulti()
        self.multi.handles = []
        self.freelist = []
        self.registry = {}

        # Create curl instances
        for x in xrange(self.thread_number):
            curl = pycurl.Curl()
            self.freelist.append(curl)
            self.multi.handles.append(curl)

    def ready_for_task(self):
        return len(self.freelist)

    def active_task_number(self):
        return self.thread_number - len(self.freelist)

    def process_task(self, task, grab, grab_config_backup):
        curl = self.freelist.pop()
        curl.task = task
        self.registry[id(curl)] = {
            'grab': grab,
            'grab_config_backup': grab_config_backup,
            'task': task,
        }
        grab.transport.curl = curl
        grab.prepare_request()
        grab.log_request()

        # Add configured curl instance to multi-curl processor
        self.multi.add_handle(curl)

    def process_handlers(self):
        # http://curl.haxx.se/libcurl/c/curl_multi_perform.html
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
                    if getattr(curl, '_callback_interrupted', None) == True:
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

                grab.process_request_result()

                # Free resources
                del self.registry[curl_id]

                yield {'ok': ok, 'emsg': emsg, 'grab': grab,
                       'grab_config_backup': grab_config_backup, 'task': task}

                self.multi.remove_handle(curl)
                self.freelist.append(curl)

            if not queued_messages:
                break

    def select(self, timeout=0.01):
        return self.multi.select(timeout)
