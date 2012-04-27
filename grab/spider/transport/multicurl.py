import pycurl

CURL_OBJECT = pycurl.Curl()

class MulticurlTransport(object):
    def __init__(self, thread_number):
        self.thread_number = thread_number
        self.multi = pycurl.CurlMulti()
        self.multi.handles = []
        self.freelist = []

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
        # All this shit looks strange
        # Maybe we should not assign extra attributes to
        # curls instance but just maintain some mapping
        # where all extra attributes will be stored
        curl.grab = grab
        curl.grab_config_backup = grab_config_backup
        curl.grab.transport.curl = curl
        curl.grab.prepare_request()
        curl.grab.log_request()
        curl.task = task
        # Add configured curl instance to multi-curl processor
        self.multi.add_handle(curl)

    def wait_result(self):
        if self.active_task_number():
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
                # Do not treat 23 error code as failed
                # It just means that some callback explicitly 
                # breaked response processing, e.g. nobody option
                # Maybe this leads to some unexpected errors :)
                if ecode == 23:
                    ecode = None
                    emsge = None
                    results.append((True, curl, None, None))
                else:
                    results.append((False, curl, ecode, emsg))

            for ok, curl, ecode, emsg in results:
                #res = self.process_multicurl_response(ok, curl, ecode, emsg)
                # FORMAT: {ok, grab, grab_config_backup, task, emsg}

                task = curl.task
                grab = curl.grab
                # GRAB CLONE ISSUE
                grab_config_backup = curl.grab_config_backup

                grab.process_request_result()

                # Break links, free resources
                curl.grab.transport.curl = None
                curl.grab = None
                curl.task = None

                yield {'ok': ok, 'emsg': emsg, 'grab': grab,
                       'grab_config_backup': grab_config_backup, 'task': task}

                self.multi.remove_handle(curl)
                self.freelist.append(curl)
                #yield res
                #self.inc_count('request')

            if not queued_messages:
                break

    def select(self):
        self.multi.select(0.01)

    def repair_grab(self, grab):
        # `curl` attribute should not be None
        # If it is None (which could be if we fire Task
        # object with grab object which was recevied in
        # as input argument of response handler function)
        # then `prepare_request` method will failed
        # because it asssumes that Grab instance
        # has valid `curl` attribute
        # TODO: Looks strange
        # Maybe refactor prepare_request method
        # to not fail on grab instance with empty curl instance
        if getattr(grab, 'curl', None) is None:
            grab.transport.curl = CURL_OBJECT
