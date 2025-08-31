import time

from six.moves.queue import Queue, Empty

from grab.spider.base_service import BaseService
from grab.spider.queue_backend import memory


class CacheServiceBase(BaseService):
    def __init__(self, spider, backend):
        self.spider = spider
        self.backend = backend
        self.queue_size_limit = 100
        # pylint: disable=no-member
        self.input_queue = self.create_input_queue()
        self.worker = self.create_worker(self.worker_callback)
        # pylint: enable=no-member
        self.register_workers(self.worker)

    def stop(self):
        super(CacheServiceBase, self).stop()
        self.backend.close()


class CacheReaderService(CacheServiceBase):
    def create_input_queue(self):
        return memory.QueueBackend(spider_name=None)

    def worker_callback(self, worker):
        while not worker.stop_event.is_set():
            worker.process_pause_signal()
            try:
                # Can't use (block=True, timeout=0.1) because
                # the backend could be mongodb, mysql, etc
                task = self.input_queue.get()
            except Empty:
                time.sleep(0.1)
            else:
                grab = self.spider.setup_grab_for_task(task)
                item = None
                if self.is_read_allowed(task, grab):
                    item = self.load_from_cache(task, grab)
                    if item:
                        result, task = item
                        self.spider.task_dispatcher.input_queue.put(
                            (result, task, None)
                        )
                if not item:
                    self.spider.task_dispatcher.input_queue.put((
                        task, None, {'source': 'cache_reader'}
                    ))

    def is_read_allowed(self, task, grab):
        return (
            not task.get('refresh_cache', False)
            and not task.get('disable_cache', False)
            and grab.detect_request_method() == 'GET'
        )

    def load_from_cache(self, task, grab):
        cache_item = self.backend.get_item(grab.config['url'])
        if cache_item is None:
            self.spider.stat.inc('cache:req-miss')
        else:
            grab.prepare_request()
            self.backend.load_response(grab, cache_item)
            grab.log_request('CACHED')
            self.spider.stat.inc('cache:req-hit')

            return {
                'ok': True,
                'grab': grab,
                'grab_config_backup': grab.dump_config(),
                'emsg': None,
                'from_cache': True,
            }, task


class CacheWriterService(CacheServiceBase):
    def create_input_queue(self):
        return Queue()

    def worker_callback(self, worker):
        while not worker.stop_event.is_set():
            worker.process_pause_signal()
            try:
                task, grab = self.input_queue.get(True, 0.1)
            except Empty:
                pass
            else:
                if self.is_write_allowed(task, grab):
                    self.backend.save_response(task.url, grab)

    def is_write_allowed(self, task, grab):
        return (
            grab.request_method == 'GET'
            and not task.get('disable_cache')
            and self.spider.is_valid_network_response_code(
                grab.doc.code, task
            )
        )
