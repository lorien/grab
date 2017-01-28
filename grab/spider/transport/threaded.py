import six
from threading import Thread
from six.moves.queue import Queue, Empty

from grab.error import GrabNetworkError

ERROR_TOO_MANY_REFRESH_REDIRECTS = -2
ERROR_ABBR = {
    ERROR_TOO_MANY_REFRESH_REDIRECTS: 'too-many-refresh-redirects',
}


def worker_thread(task_queue, result_queue, freelist, shutdown_event):
    while True:
        try:
            task, grab, grab_config_backup = task_queue.get(block=True, timeout=0.1)
        except Empty:
            if shutdown_event.is_set():
                return
        else:
            try:
                freelist.pop()
                result = {
                    'ok': True,
                    'ecode': None,
                    'emsg': None,
                    'error_abbr': None,
                    'grab': grab,
                    'grab_config_backup': grab_config_backup,
                    'task': task,
                }
                try:
                    grab.request()
                except GrabNetworkError:
                    result.update({
                        'ok': False,
                    })
                result_queue.put(result)
            finally:
                freelist.append(1)


class ThreadedTransport(object):
    def __init__(self, spider, thread_number):
        self.spider = spider
        self.thread_number = thread_number
        self.task_queue = Queue()
        self.result_queue = Queue()

        self.workers = []
        self.freelist = []
        for _ in six.moves.range(self.thread_number):
            th = Thread(target=worker_thread, args=[self.task_queue,
                                                    self.result_queue,
                                                    self.freelist,
                                                    self.spider.shutdown_event])
            th.daemon = True
            self.workers.append(th)
            self.freelist.append(1)
            th.start()

    def ready_for_task(self):
        return len(self.freelist)

    def get_free_threads_number(self):
        return len(self.freelist)

    def get_active_threads_number(self):
        return self.thread_number - len(self.freelist)

    def start_task_processing(self, task, grab, grab_config_backup):
        self.task_queue.put((task, grab, grab_config_backup))

    def process_handlers(self):
        pass

    def iterate_results(self):
        while True:
            try:
                result = self.result_queue.get_nowait()
            except Empty:
                break
            else:
                # FORMAT: {ok, grab, grab_config_backup, task, emsg, error_abbr}
                #grab.doc.error_code = None
                #grab.doc.error_msg = None
                yield result
