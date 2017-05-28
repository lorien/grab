import time
import six

from grab.spider.base_service import BaseService


class TaskGeneratorService(BaseService):
    def __init__(self, real_generator, spider):
        self.real_generator = real_generator
        self.spider = spider
        self.task_queue_threshold = max(200, self.spider.thread_number * 2)
        self.worker = self.create_worker(self.worker_callback)
        self.register_workers(self.worker)

    def worker_callback(self, worker):
        while not worker.stop_event.is_set():
            worker.process_pause_signal()
            queue_size = max(
                self.spider.task_queue.size(),
                (self.spider.cache_reader_service.input_queue.size()
                 if self.spider.cache_reader_service else 0),
                self.spider.parser_service.input_queue.qsize(),
            )
            if queue_size < self.task_queue_threshold:
                try:
                    for _ in six.moves.range(
                            self.task_queue_threshold - queue_size):
                        if worker.pause_event.is_set():
                            return
                        task = next(self.real_generator)
                        self.spider.task_dispatcher.input_queue.put((
                            task, None, {'source': 'task_generator'}
                        ))
                except StopIteration:
                    return
            else:
                time.sleep(0.1)
