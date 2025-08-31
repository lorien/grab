from __future__ import annotations

import time
from abc import abstractmethod
from collections.abc import Callable
from queue import Empty, Queue
from typing import Any, Dict, Literal

from grab.spider.interface import FatalErrorQueueItem
from grab.spider.task import Task

from .base import BaseService, ServiceWorker

NetworkResult = Dict[str, Any]  # pylint: disable=deprecated-typing-alias


class BaseNetworkService(BaseService):
    @abstractmethod
    def get_active_threads_number(self) -> int:  # pragma: no cover
        raise NotImplementedError


class NetworkServiceThreaded(BaseNetworkService):
    def __init__(
        self,
        fatal_error_queue: Queue[FatalErrorQueueItem],
        thread_number: int,
        process_task: Callable[[Task], None],
        get_task_from_queue: Callable[[], None | Literal[True] | Task],
    ) -> None:
        super().__init__(fatal_error_queue)
        self.thread_number = thread_number
        self.process_task = process_task
        self.get_task_from_queue = get_task_from_queue
        self.worker_pool = []
        for _ in range(self.thread_number):
            self.worker_pool.append(self.create_worker(self.worker_callback))
        self.register_workers(self.worker_pool)

    def get_active_threads_number(self) -> int:
        return sum(
            1
            for x in self.iterate_workers(self.worker_registry)
            if x.is_busy_event.is_set()
        )

    # TODO: supervisor worker to restore failed worker threads
    def worker_callback(self, worker: ServiceWorker) -> None:
        while not worker.stop_event.is_set():
            worker.process_pause_signal()
            try:
                task = self.get_task_from_queue()
            except Empty:
                time.sleep(0.1)
            else:
                if task is None or task is True:
                    time.sleep(0.1)
                else:
                    worker.is_busy_event.set()
                    try:
                        self.process_task(task)
                    finally:
                        worker.is_busy_event.clear()
