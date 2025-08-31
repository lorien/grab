from __future__ import annotations

import logging
import time
import typing
from collections.abc import Callable, Iterator
from datetime import datetime, timezone
from queue import Empty, Queue
from secrets import SystemRandom
from traceback import format_exception, format_stack
from types import TracebackType
from typing import Any, Literal, cast

from procstat import Stat
from proxylist import ProxyList, ProxyServer
from proxylist.base import BaseProxySource

from grab import Grab
from grab.base import BaseTransport
from grab.document import Document
from grab.errors import (
    GrabFeatureIsDeprecatedError,
    GrabInvalidResponseError,
    GrabInvalidUrlError,
    GrabMisuseError,
    GrabNetworkError,
    GrabTooManyRedirectsError,
    OriginalExceptionGrabError,
    ResponseNotValidError,
)
from grab.request import HttpRequest
from grab.util.metrics import format_traffic_value

from .errors import FatalError, NoTaskHandlerError, SpiderError, SpiderMisuseError
from .interface import FatalErrorQueueItem
from .queue_backend.base import BaseTaskQueue
from .queue_backend.memory import MemoryTaskQueue
from .service.base import BaseService
from .service.network import BaseNetworkService, NetworkResult, NetworkServiceThreaded
from .service.parser import ParserService
from .service.task_dispatcher import TaskDispatcherService
from .service.task_generator import TaskGeneratorService
from .task import Task

DEFAULT_TASK_PRIORITY = 100
DEFAULT_NETWORK_STREAM_NUMBER = 3
DEFAULT_TASK_TRY_LIMIT = 5
DEFAULT_NETWORK_TRY_LIMIT = 5
RANDOM_TASK_PRIORITY_RANGE = (50, 100)
logger = logging.getLogger("grab.spider.base")
system_random = SystemRandom()
HTTP_STATUS_ERROR = 400
HTTP_STATUS_NOT_FOUND = 404
WAIT_SERVICE_SHUTDOWN_SEC = 10


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class Spider:
    """Asynchronous scraping framework."""

    spider_name = None

    # You can define here some urls and initial tasks
    # with name "initial" will be created from these
    # urls
    # If the logic of generating initial tasks is complex
    # then consider to use `task_generator` method instead of
    # `initial_urls` attribute
    initial_urls: list[str] = []

    # **************
    # Public Methods
    # **************

    # pylint: disable=too-many-locals, too-many-arguments
    def __init__(  # noqa: PLR0913
        self,
        task_queue: None | BaseTaskQueue = None,
        thread_number: None | int = None,
        network_try_limit: None | int = None,
        task_try_limit: None | int = None,
        priority_mode: str = "random",
        meta: None | dict[str, Any] = None,
        config: None | dict[str, Any] = None,
        parser_requests_per_process: int = 10000,
        parser_pool_size: int = 1,
        network_service: None | BaseNetworkService = None,
        grab_transport: None
        | BaseTransport[HttpRequest, Document]
        | type[BaseTransport[HttpRequest, Document]] = None,
    ) -> None:
        """Create Spider instance, duh.

        Arguments:
        * thread-number - Number of concurrent network streams
        * network_try_limit - How many times try to send request
            again if network error was occurred, use 0 to disable
        * task_try_limit - Limit of tries to execute some task
            this is not the same as network_try_limit
            network try limit limits the number of tries which
            are performed automatically in case of network timeout
            of some other physical error
            but task_try_limit limits the number of attempts which
            are scheduled manually in the spider business logic
        * priority_mode - could be "random" or "const"
        * meta - arbitrary user data
        """
        self.fatal_error_queue: Queue[FatalErrorQueueItem] = Queue()
        self._started: None | float = None
        self.grab_transport = grab_transport
        self.parser_requests_per_process = parser_requests_per_process
        self.stat = Stat()
        self.runtime_events: dict[str, list[None | str]] = {}
        self.task_queue: BaseTaskQueue = task_queue if task_queue else MemoryTaskQueue()
        if config is not None:
            self.config = config
        else:
            self.config = {}
        if meta:
            self.meta = meta
        else:
            self.meta = {}
        self.thread_number = thread_number or int(
            self.config.get("thread_number", DEFAULT_NETWORK_STREAM_NUMBER)
        )
        self.task_try_limit = task_try_limit or int(
            self.config.get("task_try_limit", DEFAULT_TASK_TRY_LIMIT)
        )
        self.network_try_limit = network_try_limit or int(
            self.config.get("network_try_limit", DEFAULT_NETWORK_TRY_LIMIT)
        )
        if priority_mode not in ["random", "const"]:
            raise SpiderMisuseError(
                'Value of priority_mode option should be "random" or "const"'
            )
        self.priority_mode = priority_mode
        self.work_allowed = True
        self.proxylist_enabled: None | bool = None
        self.proxylist: None | ProxyList = None
        self.proxy: None | ProxyServer = None
        self.proxy_auto_change = False
        self.parser_pool_size = parser_pool_size
        assert network_service is None or isinstance(
            network_service, BaseNetworkService
        )
        self.network_service = (
            network_service
            if network_service is not None
            else NetworkServiceThreaded(
                self.fatal_error_queue,
                self.thread_number,
                process_task=self.srv_process_task,
                get_task_from_queue=self.get_task_from_queue,
            )
        )
        self.task_dispatcher = TaskDispatcherService(
            self.fatal_error_queue,
            process_service_result=self.srv_process_service_result,
        )
        self.parser_service = ParserService(
            fatal_error_queue=self.fatal_error_queue,
            pool_size=self.parser_pool_size,
            task_dispatcher=self.task_dispatcher,
            stat=self.stat,
            parser_requests_per_process=self.parser_requests_per_process,
            find_task_handler=self.find_task_handler,
        )
        self.task_generator_service = TaskGeneratorService(
            self.fatal_error_queue,
            self.task_generator(),
            thread_number=self.thread_number,
            get_task_queue=self.get_task_queue,
            parser_service=self.parser_service,
            task_dispatcher=self.task_dispatcher,
        )

    def collect_runtime_event(self, name: str, value: None | str) -> None:
        self.runtime_events.setdefault(name, []).append(value)

    # pylint: enable=too-many-locals, too-many-arguments

    def setup_queue(self, *_args: Any, **_kwargs: Any) -> None:
        """Set up queue."""
        raise GrabFeatureIsDeprecatedError(
            """Method Spider.setup_queue is deprecated. Now MemoryTaskQueue is used
            by default. If you need custom task queue pass instance of queue class
            in task_queue parameter in constructor of Spider class."""
        )

    def add_task(
        self,
        task: Task,
        queue: None | BaseTaskQueue = None,
        raise_error: bool = False,
    ) -> bool:
        """Add task to the task queue."""
        if queue is None:
            queue = self.task_queue
        if task.priority is None or not task.priority_set_explicitly:
            task.priority = self.generate_task_priority()
            task.priority_set_explicitly = False
        else:
            task.priority_set_explicitly = True

        if not task.request.url or not task.request.url.startswith(
            ("http://", "https://", "ftp://", "file://", "feed://")
        ):
            self.collect_runtime_event("task-with-invalid-url", task.request.url)
            msg = "Invalid task URL: %s" % task.request.url
            if raise_error:
                raise SpiderError(msg)
            logger.error(
                "%s\nTraceback:\n%s",
                msg,
                "".join(format_stack()),
            )
            return False
        # TODO: keep original task priority if it was set explicitly
        # WTF the previous comment means?
        queue.put(task, priority=task.priority, schedule_time=task.schedule_time)
        return True

    def stop(self) -> None:
        """Instruct spider to stop processing new tasks and start shutting down."""
        self.work_allowed = False

    def load_proxylist(
        self,
        source: str | BaseProxySource,
        source_type: None | str = None,
        proxy_type: str = "http",
        auto_init: bool = True,
        auto_change: bool = True,
    ) -> None:
        """Load proxy list.

        :param source: Proxy source.
            Accepts string (file path, url) or ``BaseProxySource`` instance.
        :param source_type: The type of the specified source.
            Should be one of the following: 'text_file' or 'url'.
        :param proxy_type:
            Should be one of the following: 'socks4', 'socks5' or'http'.
        :param auto_change:
            If set to `True` then automatically random proxy rotation
            will be used.

        Proxy source format should be one of the following (for each line):
        - ip:port
        - ip:port:login:password
        """
        if isinstance(source, BaseProxySource):
            self.proxylist = ProxyList(source)
        elif isinstance(source, str):
            if source_type == "text_file":
                self.proxylist = ProxyList.from_local_file(
                    source, proxy_type=proxy_type
                )
            elif source_type == "url":
                self.proxylist = ProxyList.from_network_file(
                    source, proxy_type=proxy_type
                )
            else:
                raise SpiderMisuseError(
                    "Method `load_proxylist` received "
                    "invalid `source_type` argument: %s" % source_type
                )
        else:
            raise SpiderMisuseError(
                "Method `load_proxylist` received "
                "invalid `source` argument: %s" % source
            )

        self.proxylist_enabled = True
        self.proxy = None
        if not auto_change and auto_init:
            self.proxy = self.proxylist.get_random_server()
            if not self.proxy.proxy_type:
                raise GrabMisuseError("Could not use proxy without defined proxy type")
        self.proxy_auto_change = auto_change

    def render_stats(self) -> str:
        out = [
            "------------ Stats: ------------",
            "Counters:",
        ]

        # Process counters
        items = sorted(self.stat.counters.items(), key=lambda x: x[0], reverse=True)
        for item in items:
            out.append("  {}: {}".format(item[0], item[1]))
        out.append("")

        out.append("Lists:")
        # Process event lists sorted by size in descendant order
        col_sizes = [(x, len(y)) for x, y in self.runtime_events.items()]
        col_sizes = sorted(col_sizes, key=lambda x: x[1], reverse=True)
        for col_size in col_sizes:
            out.append("  %s: %d" % col_size)
        out.append("")

        # Process extra metrics
        if "download-size" in self.stat.counters:
            out.append(
                "Network download: %s"
                % format_traffic_value(self.stat.counters["download-size"])
            )
        out.append(
            "Queue size: %d" % self.task_queue.size() if self.task_queue else "NA"
        )
        out.append("Network streams: %d" % self.thread_number)
        elapsed = (time.time() - self._started) if self._started else 0
        hours, seconds = divmod(elapsed, 3600)
        minutes, seconds = divmod(seconds, 60)
        out.append("Time elapsed: %d:%d:%d (H:M:S)" % (hours, minutes, seconds))
        out.append(
            "End time: %s"
            % datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M:%S UTC")
        )
        return "\n".join(out) + "\n"

    # ********************************
    # Methods for spider customization
    # ********************************

    def prepare(self) -> None:
        """Do additional spider customization here.

        This method runs before spider has started working.
        """

    def shutdown(self) -> None:
        """Override this method to do some final actions after parsing has been done."""

    def create_grab_instance(self, **kwargs: Any) -> Grab:
        return Grab(transport=self.grab_transport, **kwargs)

    def task_generator(self) -> Iterator[Task]:
        """You can override this method to load new tasks.

        It will be used each time as number of tasks
        in task queue is less then number of threads multiplied on 2
        This allows you to not overload all free memory if total number of
        tasks is big.
        """
        yield from ()

    # ***************
    # Private Methods
    # ***************

    def check_task_limits(self, task: Task) -> tuple[bool, str]:
        """Check that task's network & try counters do not exceed limits.

        Returns:
        * if success: (True, None)
        * if error: (False, reason)

        """
        if task.task_try_count > self.task_try_limit:
            return False, "task-try-count"

        if task.network_try_count > self.network_try_limit:
            return False, "network-try-count"

        return True, "ok"

    def generate_task_priority(self) -> int:
        if self.priority_mode == "const":
            return DEFAULT_TASK_PRIORITY
        return system_random.randint(*RANDOM_TASK_PRIORITY_RANGE)

    def process_initial_urls(self) -> None:
        if self.initial_urls:
            for url in self.initial_urls:
                self.add_task(Task(name="initial", request=HttpRequest(url)))

    def get_task_from_queue(self) -> None | Literal[True] | Task:
        try:
            return self.task_queue.get()
        except Empty:
            size = self.task_queue.size()
            if size:
                return True
            return None

    def is_valid_network_response_code(self, code: int, task: Task) -> bool:
        """Test if response is valid.

        Valid response is handled with associated task handler.
        Failed respoosne is processed with error handler.
        """
        return (
            code < HTTP_STATUS_ERROR
            or code == HTTP_STATUS_NOT_FOUND
            or code in task.valid_status
        )

    def process_parser_error(
        self,
        func_name: str,
        task: Task,
        exc_info: tuple[type[Exception], Exception, TracebackType],
    ) -> None:
        _, ex, _ = exc_info
        self.stat.inc("spider:error-%s" % ex.__class__.__name__.lower())

        logger.error(
            "Task handler [%s] error\n%s",
            func_name,
            "".join(format_exception(*exc_info)),
        )

        task_url = task.request.url if task else None
        self.collect_runtime_event(
            "fatal",
            "{}|{}|{}|{}".format(func_name, ex.__class__.__name__, str(ex), task_url),
        )

    def find_task_handler(self, task: Task) -> Callable[..., Any]:
        callback = task.get("callback")
        if callback:
            # pylint: disable=deprecated-typing-alias
            return cast(typing.Callable[..., Any], callback)
            # pylint: enable=deprecated-typing-alias
        try:
            # pylint: disable=deprecated-typing-alias
            return cast(typing.Callable[..., Any], getattr(self, "task_%s" % task.name))
            # pylint: enable=deprecated-typing-alias
        except AttributeError as ex:
            raise NoTaskHandlerError(
                "No handler or callback defined for task {}".format(task.name)
            ) from ex

    def log_network_result_stats(self, res: NetworkResult, task: Task) -> None:
        # Increase stat counters
        self.stat.inc("spider:request-processed")
        self.stat.inc("spider:task")
        self.stat.inc("spider:task-%s" % task.name)
        if task.network_try_count == 1 and task.task_try_count == 1:
            self.stat.inc("spider:task-%s-initial" % task.name)

        # Update traffic statistics
        if res["grab"] and res["doc"]:
            doc = res["doc"]
            self.stat.inc("spider:download-size", doc.download_size)
            self.stat.inc("spider:upload-size", doc.upload_size)

    def process_grab_proxy(self, task: Task, grab: Grab) -> None:
        """Assign new proxy from proxylist to the task."""
        if task.use_proxylist and self.proxylist_enabled:
            if self.proxy_auto_change:
                self.change_active_proxy(task, grab)
            if self.proxy:
                raise RuntimeError("Look like it is not called from tests")
                # grab.zzzz(
                #    proxy=self.proxy.get_address(),
                #    proxy_userpwd=self.proxy.get_userpwd(),
                #    proxy_type=self.proxy.proxy_type,
                # )

    def change_active_proxy(self, task: Task, grab: Grab) -> None:  # noqa: ARG002
        # pylint: disable=unused-argument
        self.proxy = cast(ProxyList, self.proxylist).get_random_server()
        if not self.proxy.proxy_type:
            raise SpiderMisuseError(
                'Value of priority_mode option should be "random" or "const"'
            )

    def get_task_queue(self) -> BaseTaskQueue:
        # this method is expected to be called
        # after "spider.run()" is called
        # i.e. the "self.task_queue" is set
        return self.task_queue

    def is_idle_estimated(self) -> bool:
        return (
            not self.task_generator_service.is_alive()
            and not self.task_queue.size()
            and not self.task_dispatcher.input_queue.qsize()
            and not self.parser_service.input_queue.qsize()
            and not self.parser_service.is_busy()
            and not self.network_service.get_active_threads_number()
            and not self.network_service.is_busy()
        )

    def is_idle_confirmed(self, services: list[BaseService]) -> bool:
        """Test if spider is fully idle.

        WARNING: As side effect it stops all services to get state of queues
        anaffected by sercies.

        Spider is full idle when all conditions are met:
        * all services are paused i.e. the do not change queues
        * all queues are empty
        * task generator is completed
        """
        if self.is_idle_estimated():
            for srv in services:
                srv.pause()
            if self.is_idle_estimated():
                return True
            for srv in services:
                srv.resume()
        return False

    def run(self) -> None:
        self._started = time.time()
        services = []
        try:
            self.prepare()
            self.process_initial_urls()
            services = [
                self.task_dispatcher,
                self.task_generator_service,
                self.parser_service,
                self.network_service,
            ]
            for srv in services:
                srv.start()
            while self.work_allowed:
                try:
                    exc_info = self.fatal_error_queue.get(True, 0.5)
                except Empty:
                    pass
                else:
                    # WTF: why? (see below)
                    # The trackeback of fatal error MUST BE rendered by the sender
                    raise exc_info[1]
                if self.is_idle_confirmed(services):
                    break
        finally:
            self.shutdown_services(services)
            self.stat.shutdown(join_threads=True)

    def shutdown_services(self, services: list[BaseService]) -> None:
        for srv in services:
            # Resume service if it has been paused
            # to allow service to process stop signal
            srv.resume()
            srv.stop()
        start = time.time()
        while any(x.is_alive() for x in services):
            time.sleep(0.1)
            if time.time() - start > WAIT_SERVICE_SHUTDOWN_SEC:
                break
        for srv in services:
            if srv.is_alive():
                logger.error("The %s has not stopped :(", srv)
        self.stat.render_moment()
        self.shutdown()
        self.task_queue.clear()
        self.task_queue.close()
        logger.debug("Work done")

    def log_failed_network_result(self, res: NetworkResult) -> None:
        orig_exc = (
            res["exc"].original_exc
            if isinstance(res["exc"], OriginalExceptionGrabError)
            else res["exc"]
        )
        msg = (
            ("http-%s" % res["doc"].code) if res["ok"] else orig_exc.__class__.__name__
        )

        self.stat.inc("error:%s" % msg)

    def log_rejected_task(self, task: Task, reason: str) -> None:
        if reason == "task-try-count":
            self.collect_runtime_event("task-count-rejected", task.request.url)
        elif reason == "network-try-count":
            self.collect_runtime_event("network-count-rejected", task.request.url)
        else:
            raise SpiderError("Unknown response from check_task_limits: %s" % reason)

    def get_fallback_handler(self, task: Task) -> None | Callable[..., Any]:
        if task.fallback_name:
            # pylint: disable=deprecated-typing-alias
            return cast(typing.Callable[..., Any], getattr(self, task.fallback_name))
            # pylint: enable=deprecated-typing-alias
        if task.name:
            fb_name = "task_%s_fallback" % task.name
            if hasattr(self, fb_name):
                # pylint: disable=deprecated-typing-alias
                return cast(typing.Callable[..., Any], getattr(self, fb_name))
                # pylint: enable=deprecated-typing-alias
        return None

    # #################
    # REFACTORING STUFF
    # #################
    def srv_process_service_result(
        self,
        result: Task | None | Exception | dict[str, Any],
        task: Task,
        meta: None | dict[str, Any] = None,
    ) -> None:
        """Process result submitted from any service to task dispatcher service.

        Result could be:
        * Task
        * None
        * Task instance
        * ResponseNotValidError-based exception
        * Arbitrary exception
        * Network response:
            {ok, ecode, emsg, exc, grab, grab_config_backup}

        Exception can come only from parser_service and it always has
        meta {"from": "parser", "exc_info": <...>}
        """
        if meta is None:
            meta = {}
        if isinstance(result, Task):
            self.add_task(result)
        elif result is None:
            pass
        elif isinstance(result, ResponseNotValidError):
            self.add_task(task.clone())
            error_code = result.__class__.__name__.replace("_", "-")
            self.stat.inc("integrity:%s" % error_code)
        elif isinstance(result, Exception):
            if task:
                handler = self.find_task_handler(task)
                handler_name = getattr(handler, "__name__", "NONE")
            else:
                handler_name = "NA"
            self.process_parser_error(
                handler_name,
                task,
                meta["exc_info"],
            )
            if isinstance(result, FatalError):
                self.fatal_error_queue.put(meta["exc_info"])
        elif isinstance(result, dict) and "grab" in result:
            self.srv_process_network_result(result, task)
        else:
            raise SpiderError("Unknown result received from a service: %s" % result)

    def srv_process_network_result(self, result: NetworkResult, task: Task) -> None:
        # TODO: Move to network service
        # starts
        self.log_network_result_stats(result, task)
        # ends
        is_valid = False
        if task.get("raw"):
            is_valid = True
        elif result["ok"]:
            res_code = result["doc"].code
            is_valid = self.is_valid_network_response_code(res_code, task)
        if is_valid:
            self.parser_service.input_queue.put((result, task))
        else:
            self.log_failed_network_result(result)
            # Try to do network request one more time
            if self.network_try_limit > 0:
                self.add_task(task)
        self.stat.inc("spider:request")

    def srv_process_task(self, task: Task) -> None:
        task.network_try_count += 1
        is_valid, reason = self.check_task_limits(task)
        if is_valid:
            grab = self.create_grab_instance()
            self.process_grab_proxy(task, grab)
            self.stat.inc("spider:request-network")
            self.stat.inc("spider:task-%s-network" % task.name)

            try:
                result: dict[str, Any] = {
                    "ok": True,
                    "ecode": None,
                    "emsg": None,
                    "grab": grab,
                    "task": task,
                    "exc": None,
                    "doc": None,
                }
                try:
                    result["doc"] = grab.request(task.request)
                except (
                    GrabNetworkError,
                    GrabInvalidUrlError,
                    GrabInvalidResponseError,
                    GrabTooManyRedirectsError,
                ) as ex:
                    result.update({"ok": False, "exc": ex})
                self.task_dispatcher.input_queue.put((result, task, None))
            finally:
                pass
        else:
            self.log_rejected_task(task, reason)
            handler = self.get_fallback_handler(task)
            if handler:
                handler(task)


# pylint: enable=too-many-instance-attributes, too-many-public-methods
