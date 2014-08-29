try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty
from threading import Thread

from grab.error import GrabNetworkError
from grab.tools.work import make_work
from grab.util.py3k_support import *

STOP = object()


class Worker(Thread):
    def __init__(self, taskq, resultq, *args, **kwargs):
        self.taskq = taskq
        self.resultq = resultq
        self.busy = False
        Thread.__init__(self, *args, **kwargs)


    def run(self):
        while True:
            self.busy = False
            info = self.taskq.get()
            if info is STOP:
                return
            else:
                self.busy = True
                try:
                    info['grab'].request()
                except GrabNetworkError as ex:
                    ok = False
                    emsg = unicode(ex)
                except Exception as ex:
                    raise
                    # TODO: WTF?
                else:
                    ok = True
                    emsg = None
                self.resultq.put({'ok': ok, 'emsg': emsg, 'task': info['task'],
                                  'grab': info['grab'],
                                  'grab_config_backup': info['grab_config_backup']})


class ThreadPoolTransport(object):
    def __init__(self, thread_number):
        self.thread_number = thread_number
        self.taskq = Queue()
        self.resultq = Queue()
        self.threads = []
        for x in xrange(self.thread_number):
            t = Worker(self.taskq, self.resultq)
            t.daemon = True
            t.start()
            self.threads.append(t)

    def ready_for_task(self):
        return self.active_task_number() < self.thread_number

    def active_task_number(self):
        return sum(1 if x.busy else 0 for x in self.threads)

    def process_task(self, task, grab, grab_config_backup):
        grab.prepare_request()
        grab.log_request()
        self.taskq.put({'grab': grab, 'grab_config_backup': grab_config_backup,
                        'task': task})

    def wait_result(self):
        pass

    def iterate_results(self):
        while True:
            try:
                yield self.resultq.get(False)
            except Empty:
                break

    def select(self):
        pass
        #self.multi.select(0.01)

    def repair_grab(self, grab):
        # `curl` attribute should not be None
        # If it is None (which could be if we fire Task
        # object with grab object which was received in
        # as input argument of response handler function)
        # then `prepare_request` method will failed
        # because it assumes that Grab instance
        # has valid `curl` attribute
        # TODO: Looks strange
        # Maybe refactor prepare_request method
        # to not fail on grab instance with empty curl instance
        if grab.curl is None:
            grab.curl = CURL_OBJECT
