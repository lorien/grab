from __future__ import annotations

# pylint: disable=too-many-lines
import logging
import time
from copy import deepcopy
from datetime import datetime
from queue import Empty, Queue
from random import randint
from traceback import format_exception, format_stack
from types import TracebackType
from typing import Any, Callable, Iterator, Optional, Union, cast

from grab.base import Grab
from grab.error import raise_feature_is_deprecated
from grab.proxylist import BaseProxySource, Proxy, ProxyList
from grab.spider.error import NoTaskHandler, SpiderError, SpiderMisuseError
from grab.spider.queue_backend.base import BaseTaskQueue
from grab.spider.service.base import BaseService
from grab.spider.task import Task
from grab.stat import Stat
from grab.util.metrics import format_traffic_value
from grab.util.misc import camel_case_to_underscore
from grab.util.warning import warn

from .interface import BaseSpider
from .service.network import NetworkResult
from .service.parser import ParserService
from .service.task_dispatcher import TaskDispatcherService
from .service.task_generator import TaskGeneratorService

DEFAULT_TASK_PRIORITY = 100
DEFAULT_NETWORK_STREAM_NUMBER = 3
DEFAULT_TASK_TRY_LIMIT = 5
DEFAULT_NETWORK_TRY_LIMIT = 5
RANDOM_TASK_PRIORITY_RANGE = (50, 100)

# pylint: disable=invalid-name
logger = logging.getLogger("grab.spider.base")
# pylint: disable=invalid-name


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class Spider(BaseSpider):
    """Asynchronous scraping framework."""

    spider_name = None

    # You can define here some urls and initial tasks
    # with name "initial" will be created from these
    # urls
    # If the logic of generating initial tasks is complex
    # then consider to use `task_generator` method instead of
    # `initial_urls` attribute
    initial_urls: list[str] = []

    # *************
    # Class Methods
    # *************

    @classmethod
    def update_spider_config(cls, config: dict[str, Any]) -> None:
        pass

    @classmethod
    def get_spider_name(cls) -> str:
        if cls.spider_name:
            return cls.spider_name
        return camel_case_to_underscore(cls.__name__)

    # **************
    # Public Methods
    # **************

    # pylint: disable=too-many-locals, too-many-arguments
    def __init__(
        self,
        thread_number: Optional[int] = None,
        network_try_limit: Optional[int] = None,
        task_try_limit: Optional[int] = None,
        priority_mode: str = "random",
        meta: Optional[dict[str, Any]] = None,
        config: Optional[dict[str, Any]] = None,
        args: Optional[dict[str, Any]] = None,
        parser_requests_per_process: int = 10000,
        parser_pool_size: int = 1,
        network_service: str = "threaded",
        grab_transport: str = "urllib3",
        # Deprecated
        request_pause: Any = None,
        only_cache: bool = False,
        transport: Any = None,
    ) -> None:
        """
        Create Spider instance, duh.

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
        * retry_rebuild_user_agent - generate new random user-agent for each
            network request which is performed again due to network error
        * args - command line arguments parsed with `setup_arg_parser` method
        """
        self.fatal_error_queue: Queue[
            tuple[type[Exception], Exception, TracebackType]
        ] = Queue()
        self.task_queue_parameters = None
        self._started: Optional[float] = None
        assert grab_transport in ["urllib3"]
        self.grab_transport_name = grab_transport
        self.parser_requests_per_process = parser_requests_per_process
        self.stat = Stat()
        self.task_queue: Optional[BaseTaskQueue] = None
        if args is None:
            self.args = {}
        else:
            self.args = args
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
        self._grab_config: dict[str, Any] = {}
        if priority_mode not in ["random", "const"]:
            raise SpiderMisuseError(
                'Value of priority_mode option should be "random" or "const"'
            )
        self.priority_mode = priority_mode
        if only_cache:
            raise_feature_is_deprecated("Cache feature")
        self.work_allowed = True
        if request_pause is not None:
            warn("Option `request_pause` is deprecated and is not supported anymore")
        self.proxylist_enabled: Optional[bool] = None
        self.proxylist: Optional[ProxyList] = None
        self.proxy: Optional[Proxy] = None
        self.proxy_auto_change = False
        self.interrupted = False
        self.parser_pool_size = parser_pool_size
        self.parser_service = ParserService(
            spider=self,
            pool_size=self.parser_pool_size,
        )
        if transport is not None:
            warn(
                'The "transport" argument of Spider constructor is'
                ' deprecated. Use "network_service" argument.'
            )
            network_service = transport
        assert network_service in ("threaded",)
        if network_service == "threaded":
            # pylint: disable=no-name-in-module, import-error
            # pylint: disable=import-outside-toplevel
            from .service.network import NetworkServiceThreaded

            # pylint: enable=import-outside-toplevel

            self.network_service = NetworkServiceThreaded(self, self.thread_number)
        self.task_dispatcher = TaskDispatcherService(self)
        self.task_generator_service = TaskGeneratorService(self, self.task_generator())

    # pylint: enable=too-many-locals, too-many-arguments

    def setup_cache(
        self, *_args: Any, **_kwargs: Any
    ) -> None:  # pylint: disable=unused-argument
        raise_feature_is_deprecated("Cache feature")

    def load_queue_class(self, backend: str) -> type[BaseTaskQueue]:
        # pylint: disable=import-outside-toplevel
        if backend == "mongodb":
            from grab.spider.queue_backend.mongodb import MongodbTaskQueue

            return MongodbTaskQueue
        if backend == "redis":
            from grab.spider.queue_backend.redis import RedisTaskQueue

            return RedisTaskQueue
        if backend == "memory":
            from grab.spider.queue_backend.memory import MemoryTaskQueue

            return MemoryTaskQueue
        raise SpiderMisuseError(f"Invalid task queue backend name: {backend}")

    def setup_queue(self, backend: str = "memory", **kwargs: Any) -> None:
        """
        Set up queue.

        :param backend: Backend name
            Should be one of the following: 'memory', 'redis' or 'mongo'.
        :param kwargs: Additional credentials for backend.
        """
        if backend == "mongo":
            warn('Backend name "mongo" is deprecated. Use "mongodb" instead.')
            backend = "mongodb"
        logger.debug("Using %s backend for task queue", backend)
        queue_cls = self.load_queue_class(backend)
        # mod = __import__(
        #    "grab.spider.queue_backend.%s" % backend, globals(), locals(), ["foo"]
        # )
        self.task_queue = queue_cls(spider_name=self.get_spider_name(), **kwargs)

    def add_task(
        self,
        task: Task,
        queue: Optional[BaseTaskQueue] = None,
        raise_error: bool = False,
    ) -> bool:
        """Add task to the task queue."""
        if queue is None:
            queue = self.task_queue
        if queue is None:
            raise SpiderMisuseError(
                "You should configure task queue before "
                "adding tasks. Use `setup_queue` method."
            )
        if task.priority is None or not task.priority_set_explicitly:
            task.priority = self.generate_task_priority()
            task.priority_set_explicitly = False
        else:
            task.priority_set_explicitly = True

        if not task.url or not task.url.startswith(
            ("http://", "https://", "ftp://", "file://", "feed://")
        ):
            self.stat.collect("task-with-invalid-url", task.url)
            msg = "Invalid task URL: %s" % task.url
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
        source: Union[str, BaseProxySource],
        source_type: Optional[str] = None,
        proxy_type: str = "http",
        auto_init: bool = True,
        auto_change: bool = True,
    ) -> None:
        """
        Load proxy list.

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
        self.proxylist = ProxyList()
        if isinstance(source, BaseProxySource):
            self.proxylist.set_source(source)
        elif isinstance(source, str):
            if source_type == "text_file":
                self.proxylist.load_file(source, proxy_type=proxy_type)
            elif source_type == "url":
                self.proxylist.load_url(source, proxy_type=proxy_type)
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
            self.proxy = self.proxylist.get_random_proxy()
        self.proxy_auto_change = auto_change

    def process_next_page(
        self,
        grab: Grab,
        task: Task,
        xpath: str,
        resolve_base: bool = False,
        **kwargs: Any,
    ) -> bool:
        r"""
        Generate task for next page.

        :param grab: Grab instance
        :param task: Task object which should be assigned to next page url
        :param xpath: xpath expression which calculates list of URLS
        :param \\**kwargs: extra settings for new task object

        Example::

            self.follow_links(grab, 'topic', '//div[@class="topic"]/a/@href')
        """
        try:
            # next_url = grab.xpath_text(xpath)
            next_url = grab.doc.select(xpath).text()
        except IndexError:
            return False
        else:
            url = grab.make_url_absolute(next_url, resolve_base=resolve_base)
            page = task.get("page", 1) + 1
            grab2 = grab.clone()
            grab2.setup(url=url)
            task2 = task.clone(task_try_count=1, grab=grab2, page=page, **kwargs)
            self.add_task(task2)
            return True

    def render_stats(self, timing: None = None) -> str:
        if timing is not None:
            warn(
                "Option timing of method render_stats is deprecated."
                " There is no more timing feature."
            )
        out = [
            "------------ Stats: ------------",
            "Counters:",
        ]

        # Process counters
        items = sorted(self.stat.counters.items(), key=lambda x: x[0], reverse=True)
        for item in items:
            out.append("  %s: %s" % item)
        out.append("")

        out.append("Lists:")
        # Process collections sorted by size desc
        col_sizes = [(x, len(y)) for x, y in self.stat.collections.items()]
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
        if self._started:
            elapsed = time.time() - self._started
        else:
            elapsed = 0
        hours, seconds = divmod(elapsed, 3600)
        minutes, seconds = divmod(seconds, 60)
        out.append("Time elapsed: %d:%d:%d (H:M:S)" % (hours, minutes, seconds))
        out.append(
            "End time: %s" % datetime.utcnow().strftime("%d %b %Y, %H:%M:%S UTC")
        )
        return "\n".join(out) + "\n"

    # ********************************
    # Methods for spider customization
    # ********************************

    def prepare(self) -> None:
        """
        Do additional spider customization here.

        This method runs before spider has started working.
        """

    def shutdown(self) -> None:
        """Override this method to do some final actions after parsing has been done."""

    def update_grab_instance(self, grab: Grab) -> None:
        """
        Update config of any `Grab` instance created by the spider.

        WTF it means?
        """

    def create_grab_instance(self, **kwargs: Any) -> Grab:
        # Back-ward compatibility for deprecated `grab_config` attribute
        # Here I use `_grab_config` to not trigger warning messages
        kwargs["transport"] = self.grab_transport_name
        if self._grab_config and kwargs:
            merged_config = deepcopy(self._grab_config)
            merged_config.update(kwargs)
            grab = Grab(**merged_config)
        elif self._grab_config and not kwargs:
            grab = Grab(**self._grab_config)
        else:
            grab = Grab(**kwargs)
        return grab  # noqa: R504

    def task_generator(self) -> Iterator[Task]:
        """
        You can override this method to load new tasks smoothly.

        It will be used each time as number of tasks
        in task queue is less then number of threads multiplied on 2
        This allows you to not overload all free memory if total number of
        tasks is big.
        """
        if False:  # pylint: disable=using-constant-test
            # Some magic to make this function empty generator
            yield ":-)"

    # ***************
    # Private Methods
    # ***************

    def check_task_limits(self, task: Task) -> tuple[bool, Optional[str]]:
        """
        Check that task's network & try counters do not exceed limits.

        Returns:
        * if success: (True, None)
        * if error: (False, reason)

        """
        if task.task_try_count > self.task_try_limit:
            return False, "task-try-count"

        if task.network_try_count > self.network_try_limit:
            return False, "network-try-count"

        return True, None

    def generate_task_priority(self) -> int:
        if self.priority_mode == "const":
            return DEFAULT_TASK_PRIORITY
        return randint(*RANDOM_TASK_PRIORITY_RANGE)

    def process_initial_urls(self) -> None:
        if self.initial_urls:
            for url in self.initial_urls:
                self.add_task(Task("initial", url=url))

    def get_task_from_queue(self) -> Optional[Union[bool, Task]]:
        try:
            return cast(BaseTaskQueue, self.task_queue).get()
        except Empty:
            size = cast(BaseTaskQueue, self.task_queue).size()
            if size:
                return True
            return None

    def setup_grab_for_task(self, task: Task) -> Grab:
        grab = self.create_grab_instance()
        if task.grab_config:
            grab.load_config(task.grab_config)
        else:
            grab.setup(url=task.url)

        # Generate new common headers
        grab.config["common_headers"] = grab.common_headers()
        self.update_grab_instance(grab)
        grab.setup_transport(self.grab_transport_name)
        return grab

    def is_valid_network_response_code(self, code: int, task: Task) -> bool:
        """
        Test if response is valid.

        Valid response is handled with associated task handler.
        Failed respoosne is processed with error handler.
        """
        return code < 400 or code == 404 or code in task.valid_status

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

        task_url = task.url if task else None
        self.stat.collect(
            "fatal",
            "%s|%s|%s|%s" % (func_name, ex.__class__.__name__, str(ex), task_url),
        )

    def find_task_handler(self, task: Task) -> Callable[..., Any]:
        callback = task.get("callback")
        if callback:
            return cast(Callable[..., Any], callback)
        try:
            handler = getattr(self, "task_%s" % task.name)
        except AttributeError as ex:
            raise NoTaskHandler(
                "No handler or callback defined for " "task %s" % task.name
            ) from ex
        else:
            return cast(Callable[..., Any], handler)

    def log_network_result_stats(self, res: NetworkResult, task: Task) -> None:
        # Increase stat counters
        self.stat.inc("spider:request-processed")
        self.stat.inc("spider:task")
        self.stat.inc("spider:task-%s" % task.name)
        if task.network_try_count == 1 and task.task_try_count == 1:
            self.stat.inc("spider:task-%s-initial" % task.name)

        # Update traffic statistics
        if res["grab"] and res["grab"].doc:
            doc = res["grab"].doc
            self.stat.inc("spider:download-size", doc.download_size)
            self.stat.inc("spider:upload-size", doc.upload_size)

    def process_grab_proxy(self, task: Task, grab: Grab) -> None:
        """Assign new proxy from proxylist to the task."""
        if task.use_proxylist and self.proxylist_enabled:
            if self.proxy_auto_change:
                self.change_active_proxy(task, grab)
            if self.proxy:
                grab.setup(
                    proxy=self.proxy.get_address(),
                    proxy_userpwd=self.proxy.get_userpwd(),
                    proxy_type=self.proxy.proxy_type,
                )

    # pylint: disable=unused-argument
    def change_active_proxy(self, task: Task, grab: Grab) -> None:
        self.proxy = cast(ProxyList, self.proxylist).get_random_proxy()

    # pylint: enable=unused-argument

    # def submit_task_to_transport(self, task, grab):
    #    grab_config_backup = grab.dump_config()
    #    self.process_grab_proxy(task, grab)
    #    self.stat.inc("spider:request-network")
    #    self.stat.inc("spider:task-%s-network" % task.name)
    #    try:
    #        # pylint: disable=no-member
    #        self.network_service.start_task_processing(task, grab, grab_config_backup)
    #        # pylint: enable=no-member
    #    except GrabInvalidUrl:
    #        # TODO: log error
    #        # TODO: show traceback
    #        logger.debug("Task %s has invalid URL: %s", task.name, task.url)
    #        self.stat.collect("invalid-url", task.url)

    def run(self) -> None:  # noqa: C901
        self._started = time.time()
        services = []
        try:
            self.prepare()
            if self.task_queue is None:
                self.setup_queue()
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
                    # The trackeback of fatal error MUST BE
                    # rendered by the sender
                    raise exc_info[1]
                if self.is_idle():
                    for srv in services:
                        srv.pause()
                    if self.is_idle():
                        break
                    for srv in services:
                        srv.resume()
        except KeyboardInterrupt:
            self.interrupted = True
            raise
        finally:
            self.shutdown_services(services)

    def shutdown_services(self, services: list[BaseService]) -> None:
        # TODO:
        # print('Start stopping services')
        for srv in services:
            # Resume service if it has been paused
            # to allow service to process stop signal
            srv.resume()
            srv.stop()
        # print('Called .stop() for all services')
        start = time.time()
        while any(x.is_alive() for x in services):
            time.sleep(0.1)
            if time.time() - start > 10:
                break
        for srv in services:
            if srv.is_alive():
                print("The %s has not stopped :(" % srv)
        self.stat.print_progress_line()
        self.shutdown()
        if self.task_queue:
            self.task_queue.clear()
            self.task_queue.close()
        logger.debug("Work done")

    def is_idle(self) -> bool:
        return (
            not self.task_generator_service.is_alive()
            and not cast(BaseTaskQueue, self.task_queue).size()
            and not self.task_dispatcher.input_queue.qsize()
            and not self.parser_service.input_queue.qsize()
            and not self.parser_service.is_busy()
            and not self.network_service.get_active_threads_number()
            and not self.network_service.is_busy()
        )

    def log_failed_network_result(self, res: NetworkResult) -> None:
        if res["ok"]:
            msg = "http-%s" % res["grab"].doc.code
        else:
            msg = res["error_abbr"]
        self.stat.inc("error:%s" % msg)

    def log_rejected_task(self, task: Task, reason: str) -> None:
        if reason == "task-try-count":
            self.stat.collect("task-count-rejected", task.url)
        elif reason == "network-try-count":
            self.stat.collect("network-count-rejected", task.url)
        else:
            raise SpiderError("Unknown response from " "check_task_limits: %s" % reason)

    def get_fallback_handler(self, task: Task) -> Optional[Callable[..., Any]]:
        if task.fallback_name:
            return cast(Callable[..., Any], getattr(self, task.fallback_name))
        if task.name:
            fb_name = "task_%s_fallback" % task.name
            if hasattr(self, fb_name):
                return cast(Callable[..., Any], getattr(self, fb_name))
        return None

    # ################
    # Deprecated Things
    # #################

    @property
    def cache_reader_service(self) -> None:
        raise_feature_is_deprecated("Cache feature")

    @cache_reader_service.setter
    def cache_reader_service(self, _: Any) -> None:
        raise_feature_is_deprecated("Cache feature")

    @property
    def cache_writer_service(self) -> None:
        raise_feature_is_deprecated("Cache feature")

    @cache_writer_service.setter
    def cache_writer_service(self, _: Any) -> None:
        raise_feature_is_deprecated("Cache feature")


# pylint: enable=too-many-instance-attributes, too-many-public-methods
