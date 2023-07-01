from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from queue import Queue

from grab.spider.interface import FatalErrorQueueItem
from grab.spider.queue_backend.base import BaseTaskQueue
from grab.spider.task import Task

from .base import BaseService, ServiceWorker
from .parser import ParserService
from .task_dispatcher import TaskDispatcherService


class TaskGeneratorService(BaseService):
    def __init__(
        self,
        fatal_error_queue: Queue[FatalErrorQueueItem],
        real_generator: Iterator[Task],
        thread_number: int,
        get_task_queue: Callable[[], BaseTaskQueue],
        parser_service: ParserService,
        task_dispatcher: TaskDispatcherService,
    ) -> None:
        super().__init__(fatal_error_queue)
        self.real_generator = real_generator
        self.task_queue_threshold = max(200, thread_number * 2)
        self.get_task_queue = get_task_queue
        self.parser_service = parser_service
        self.task_dispatcher = task_dispatcher
        self.worker = self.create_worker(self.worker_callback)
        self.register_workers(self.worker)

    def worker_callback(self, worker: ServiceWorker) -> None:
        # at this point I guess the task queue is set
        # i.e. "spider.run()" is called
        task_queue = self.get_task_queue()
        while not worker.stop_event.is_set():
            worker.process_pause_signal()
            queue_size = max(
                task_queue.size(),
                self.parser_service.input_queue.qsize(),
            )
            if queue_size < self.task_queue_threshold:
                try:
                    for _ in range(self.task_queue_threshold - queue_size):
                        if worker.pause_event.is_set():
                            return
                        task = next(self.real_generator)
                        self.task_dispatcher.input_queue.put(
                            (task, None, {"source": "task_generator"})
                        )
                except StopIteration:
                    return
            else:
                time.sleep(0.1)
