from __future__ import annotations

import logging
import sys
from collections.abc import Callable, Iterable
from queue import Queue
from threading import Event, Thread
from types import TracebackType
from typing import Any, Tuple, Type, cast

from grab.spider.interface import FatalErrorQueueItem

logger = logging.getLogger(__name__)


class ServiceWorker:
    def __init__(
        self,
        fatal_error_queue: Queue[FatalErrorQueueItem],
        worker_callback: Callable[..., Any],
    ) -> None:
        self.fatal_error_queue = fatal_error_queue
        self.thread = Thread(
            target=self.worker_callback_wrapper(worker_callback), args=[self]
        )
        self.thread.daemon = True
        self.thread.name = self.build_thread_name(worker_callback)
        self.pause_event = Event()
        self.stop_event = Event()
        self.resume_event = Event()
        self.activity_paused = Event()
        self.is_busy_event = Event()

    def build_thread_name(self, worker_callback: Callable[..., Any]) -> str:
        cls_name = (
            worker_callback.__self__.__class__.__name__
            if hasattr(worker_callback, "__self__")
            else "NA"
        )
        return "worker:{}:{}".format(cls_name, worker_callback.__name__)

    def worker_callback_wrapper(
        self, callback: Callable[..., Any]
    ) -> Callable[..., None]:
        def wrapper(*args: Any, **kwargs: Any) -> None:
            try:
                callback(*args, **kwargs)
            except Exception as ex:
                logger.exception("Spider Service Fatal Error", exc_info=ex)
                # pylint: disable=deprecated-typing-alias
                self.fatal_error_queue.put(
                    cast(
                        Tuple[Type[Exception], Exception, TracebackType], sys.exc_info()
                    )
                )

        return wrapper

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()

    def process_pause_signal(self) -> None:
        if self.pause_event.is_set():
            self.activity_paused.set()
            self.resume_event.wait()

    def pause(self) -> None:
        self.resume_event.clear()
        self.pause_event.set()
        while True:
            if self.activity_paused.wait(0.1):
                break
            if not self.is_alive():
                break

    def resume(self) -> None:
        self.pause_event.clear()
        self.activity_paused.clear()
        self.resume_event.set()

    def is_alive(self) -> bool:
        return self.thread.is_alive()


class BaseService:
    def __init__(self, fatal_error_queue: Queue[FatalErrorQueueItem]) -> None:
        self.fatal_error_queue = fatal_error_queue
        self.worker_registry: list[ServiceWorker] = []

    def create_worker(self, worker_action: Callable[..., None]) -> ServiceWorker:
        return ServiceWorker(self.fatal_error_queue, worker_action)

    def iterate_workers(self, objects: list[ServiceWorker]) -> Iterable[ServiceWorker]:
        for obj in objects:
            assert isinstance(obj, (ServiceWorker, list))
            if isinstance(obj, ServiceWorker):
                yield obj
            elif isinstance(obj, list):
                yield from obj

    def start(self) -> None:
        for worker in self.iterate_workers(self.worker_registry):
            worker.start()

    def stop(self) -> None:
        for worker in self.iterate_workers(self.worker_registry):
            worker.stop()

    def pause(self) -> None:
        for worker in self.iterate_workers(self.worker_registry):
            worker.pause()

    def resume(self) -> None:
        for worker in self.iterate_workers(self.worker_registry):
            worker.resume()

    def register_workers(self, *args: Any) -> None:
        self.worker_registry = list(args)

    def is_busy(self) -> bool:
        return any(
            x.is_busy_event.is_set() for x in self.iterate_workers(self.worker_registry)
        )

    def is_alive(self) -> bool:
        return any(x.is_alive() for x in self.iterate_workers(self.worker_registry))
