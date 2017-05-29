import time

from six.moves.queue import Empty

from grab.error import GrabNetworkError
from grab.util.misc import camel_case_to_underscore
from grab.spider.base_service import BaseService

ERROR_TOO_MANY_REFRESH_REDIRECTS = -2
ERROR_ABBR = {
    ERROR_TOO_MANY_REFRESH_REDIRECTS: 'too-many-refresh-redirects',
}


def make_class_abbr(name):
    val = camel_case_to_underscore(name)
    return val.replace('_', '-')


class NetworkServiceThreaded(BaseService):
    def __init__(self, spider, thread_number):
        self.spider = spider
        self.thread_number = thread_number
        self.worker_pool = []
        for _ in range(self.thread_number):
            self.worker_pool.append(self.create_worker(self.worker_callback))
        self.register_workers(self.worker_pool)

    def get_active_threads_number(self):
        return sum(1 for x in self.iterate_workers(self.worker_registry)
                   if x.is_busy_event.is_set())

    # TODO: supervisor worker to restore failed worker threads
    def worker_callback(self, worker):
        while not worker.stop_event.is_set():
            worker.process_pause_signal()
            try:
                task = self.spider.get_task_from_queue()
            except Empty:
                time.sleep(0.1)
            else:
                if task is None or task is True:
                    time.sleep(0.1)
                else:
                    worker.is_busy_event.set()
                    try:
                        task.network_try_count += 1 # pylint: disable=no-member
                        is_valid, reason = self.spider.check_task_limits(task)
                        if is_valid:
                            grab = self.spider.setup_grab_for_task(task)
                            # TODO: almost duplicate of
                            # Spider.submit_task_to_transport
                            if self.spider.only_cache:
                                self.spider.stat.inc(
                                    'spider:'
                                    'request-network-disabled-only-cache'
                                )
                            else:
                                grab_config_backup = grab.dump_config()
                                self.spider.process_grab_proxy(task, grab)
                                self.spider.stat.inc('spider:request-network')
                                self.spider.stat.inc(
                                    'spider:task-%s-network' % task.name
                                )

                                #self.freelist.pop()
                                try:
                                    result = {
                                        'ok': True,
                                        'ecode': None,
                                        'emsg': None,
                                        'error_abbr': None,
                                        'grab': grab,
                                        'grab_config_backup': (
                                            grab_config_backup
                                        ),
                                        'task': task,
                                        'exc': None
                                    }
                                    try:
                                        grab.request()
                                    except GrabNetworkError as ex:
                                        if (ex.original_exc.__class__.__name__
                                                == 'error'):
                                            ex_cls = ex
                                        else:
                                            ex_cls = ex.original_exc
                                        result.update({
                                            'ok': False,
                                            'exc': ex,
                                            'error_abbr': make_class_abbr(
                                                ex_cls.__class__.__name__
                                            ),
                                        })
                                    (self.spider.task_dispatcher
                                     .input_queue.put((result, task, None)))
                                finally:
                                    pass
                                    #self.freelist.append(1)
                        else:
                            self.spider.log_rejected_task(task, reason)
                            # pylint: disable=no-member
                            handler = task.get_fallback_handler(self.spider)
                            # pylint: enable=no-member
                            if handler:
                                handler(task)
                    finally:
                        worker.is_busy_event.clear()
