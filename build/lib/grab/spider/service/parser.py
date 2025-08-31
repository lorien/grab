from __future__ import annotations

import sys
import time
from collections.abc import Callable
from queue import Empty, Queue
from typing import Any

from procstat import Stat

from grab import Grab
from grab.spider.errors import NoTaskHandlerError
from grab.spider.interface import FatalErrorQueueItem
from grab.spider.task import Task

from .base import BaseService, ServiceWorker
from .network import NetworkResult
from .task_dispatcher import TaskDispatcherService


class ParserService(BaseService):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        fatal_error_queue: Queue[FatalErrorQueueItem],
        pool_size: int,
        task_dispatcher: TaskDispatcherService,
        stat: Stat,
        parser_requests_per_process: int,
        find_task_handler: Callable[[Task], Callable[..., None]],
    ) -> None:
        super().__init__(fatal_error_queue)
        self.task_dispatcher = task_dispatcher
        self.stat = stat
        self.parser_requests_per_process = parser_requests_per_process
        self.find_task_handler = find_task_handler
        self.input_queue: Queue[Any] = Queue()
        self.pool_size = pool_size
        self.workers_pool = []
        for _ in range(self.pool_size):
            self.workers_pool.append(self.create_worker(self.worker_callback))
        self.supervisor = self.create_worker(self.supervisor_callback)
        self.register_workers(self.workers_pool, self.supervisor)

    def check_pool_health(self) -> None:
        to_remove = []
        for worker in self.workers_pool:
            if not worker.is_alive():
                self.stat.inc("parser:worker-restarted")
                new_worker = self.create_worker(self.worker_callback)
                self.workers_pool.append(new_worker)
                new_worker.start()
                to_remove.append(worker)
        for worker in to_remove:
            self.workers_pool.remove(worker)

    def supervisor_callback(self, worker: ServiceWorker) -> None:
        while not worker.stop_event.is_set():
            worker.process_pause_signal()
            self.check_pool_health()
            time.sleep(1)

    def worker_callback(self, worker: ServiceWorker) -> None:
        process_request_count = 0
        while not worker.stop_event.is_set():
            worker.process_pause_signal()
            try:
                result, task = self.input_queue.get(True, 0.1)
            except Empty:
                pass
            else:
                worker.is_busy_event.set()
                try:
                    process_request_count += 1
                    try:
                        handler = self.find_task_handler(task)
                    except NoTaskHandlerError as ex:
                        self.task_dispatcher.input_queue.put(
                            (ex, task, {"exc_info": sys.exc_info()})
                        )
                        self.stat.inc("parser:handler-not-found")
                    else:
                        self.execute_task_handler(handler, result, task)
                        self.stat.inc("parser:handler-processed")
                    if self.parser_requests_per_process and (
                        process_request_count >= self.parser_requests_per_process
                    ):
                        self.stat.inc(
                            "parser:handler-req-limit",
                        )
                        return
                finally:
                    worker.is_busy_event.clear()

    def execute_task_handler(
        self, handler: Callable[[Grab, Task], None], result: NetworkResult, task: Task
    ) -> None:
        try:
            handler_result = handler(result["doc"], task)
            if handler_result is None:
                pass
            else:
                for item in handler_result:
                    self.task_dispatcher.input_queue.put(
                        (item, task, None),
                    )
        except Exception as ex:
            self.task_dispatcher.input_queue.put(
                (
                    ex,
                    task,
                    {
                        "exc_info": sys.exc_info(),
                        "from": "parser",
                    },
                )
            )
