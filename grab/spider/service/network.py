import time
from queue import Empty
from typing import Any, Dict, cast

from grab.error import (
    GrabInvalidResponse,
    GrabInvalidUrl,
    GrabNetworkError,
    GrabTooManyRedirectsError,
    OriginalExceptionGrabError,
)
from grab.util.misc import camel_case_to_underscore

from ..interface import BaseSpider
from ..task import Task
from .base import BaseService, ServiceWorker

NetworkResult = Dict[str, Any]


def make_class_abbr(name: str) -> str:
    val = camel_case_to_underscore(name)
    return val.replace("_", "-")


class NetworkServiceThreaded(BaseService):
    def __init__(self, spider: BaseSpider, thread_number: int) -> None:
        super().__init__(spider)
        self.thread_number = thread_number
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
                task = self.spider.get_task_from_queue()
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

    def process_task(self, task: Task) -> None:
        task.network_try_count += 1  # pylint: disable=no-member
        is_valid, reason = self.spider.check_task_limits(task)
        if is_valid:
            grab = self.spider.setup_grab_for_task(task)
            # TODO: almost duplicate of
            # Spider.submit_task_to_transport
            grab_config_backup = grab.dump_config()
            self.spider.process_grab_proxy(task, grab)
            self.spider.stat.inc("spider:request-network")
            self.spider.stat.inc("spider:task-%s-network" % task.name)

            # self.freelist.pop()
            try:
                result = {
                    "ok": True,
                    "ecode": None,
                    "emsg": None,
                    "error_abbr": None,
                    "grab": grab,
                    "grab_config_backup": (grab_config_backup),
                    "task": task,
                    "exc": None,
                }
                try:
                    grab.request()
                except (
                    GrabNetworkError,
                    GrabInvalidUrl,
                    GrabInvalidResponse,
                    GrabTooManyRedirectsError,
                ) as ex:
                    is_redir_err = isinstance(ex, GrabTooManyRedirectsError)
                    orig_exc_name = (
                        ex.original_exc.__class__.__name__
                        if hasattr(ex, "original_exc")
                        else None
                    )
                    # UnicodeError: see #323
                    if (
                        not isinstance(ex, OriginalExceptionGrabError)
                        or isinstance(ex, GrabInvalidUrl)
                        or orig_exc_name == "error"
                        or orig_exc_name == "UnicodeError"
                    ):
                        ex_cls = ex
                    else:
                        # ex_cls.original_exc
                        ex_cls = cast(OriginalExceptionGrabError, ex).original_exc
                    result.update(
                        {
                            "ok": False,
                            "exc": ex,
                            "error_abbr": (
                                "too-many-redirects"
                                if is_redir_err
                                else make_class_abbr(ex_cls.__class__.__name__)
                            ),
                        }
                    )
                (self.spider.task_dispatcher.input_queue.put((result, task, None)))
            finally:
                pass
                # self.freelist.append(1)
        else:
            self.spider.log_rejected_task(task, reason)
            # pylint: disable=no-member
            handler = self.spider.get_fallback_handler(task)
            # pylint: enable=no-member
            if handler:
                handler(task)
