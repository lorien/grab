from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

from grab.errors import GrabMisuseError
from grab.request import HttpRequest

from .errors import SpiderMisuseError


class BaseTask:
    pass


class Task(BaseTask):  # pylint: disable=too-many-instance-attributes
    """Task for spider."""

    # pylint:disable=too-many-arguments,too-many-locals,too-many-branches
    def __init__(  # noqa: PLR0913
        self,
        name: None | str = None,
        url: None | str | HttpRequest = None,
        request: None | HttpRequest = None,
        priority: None | int = None,
        priority_set_explicitly: bool = True,
        network_try_count: int = 0,
        task_try_count: int = 1,
        valid_status: None | list[int] = None,
        use_proxylist: bool = True,
        delay: None | float = None,
        raw: bool = False,
        callback: None | Callable[..., None] = None,
        fallback_name: None | str = None,
        store: None | dict[str, Any] = None,
        **kwargs: Any,
    ) -> None:
        """Create `Task` object.

        If more than one of url, grab_config options are non-empty
        then they processed in following order:
        * grab_config overwrite url

        Args:
            :param name: name of the task. After successful network operation
                task's result will be passed to `task_<name>` method.
            :param priority: priority of the Task. Tasks with lower priority
                will be processed earlier. By default each new task is assigned
                with random priority from (80, 100) range.
            :param priority_set_explicitly: internal flag which tells if that
                task priority was assigned manually or generated by spider
                according to priority generation rules.
            :param network_try_count: you'll probably will not need to use it.
                It is used internally to control how many times this task was
                restarted due to network errors. The `Spider` instance has
                `network_try_limit` option. When `network_try_count` attribute
                of the task exceeds the `network_try_limit` attribute then
                processing of the task is abandoned.
            :param task_try_count: the as `network_try_count` but it increased
                only then you use `clone` method. Also you can set it manually.
                It is useful if you want to restart the task after it was
                cancelled due to multiple network errors. As you might guessed
                there is `task_try_limit` option in `Spider` instance. Both
                options `network_try_count` and `network_try_limit` guarantee
                you that you'll not get infinite loop of restarting some task.
            :param valid_status: extra status codes which counts as valid
            :param use_proxylist: it means to use proxylist which was
                configured via `setup_proxylist` method of spider
            :param delay: if specified tells the spider to schedule the task
                and execute    it after `delay` seconds
            :param raw: if `raw` is True then the network response is
                forwarding to the corresponding handler without any check of
                HTTP status code of network error, if `raw` is False (by
                default) then failed response is putting back to task queue or
                if tries limit is reached then the processing of this  request
                is finished.
            :param callback: if you pass some function in `callback` option
                then the network response will be passed to this callback and
                the usual 'task_*' handler will be ignored and no error will be
                raised if such 'task_*' handler does not exist.
            :param fallback_name: the name of method that is called when spider
                gives up to do the task (due to multiple network errors)

            Any non-standard named arguments passed to `Task` constructor will
            be saved as attributes of the object. You can get their values
            later as attributes or with `get` method which allows to use
            default value if attribute does not exist.
        """
        self.check_init_kwargs(kwargs)
        if url is not None and request is not None:
            raise GrabMisuseError("Options url and ruquest are mutually exclusive")
        if request is not None:
            if not isinstance(request, HttpRequest):
                raise TypeError("Option 'requst' must be HttpRequest instance")
            self.request = request
        elif url is not None:
            if isinstance(url, str):
                self.request = HttpRequest(method="GET", url=url)
            elif isinstance(url, HttpRequest):
                self.request = url
            else:
                raise TypeError("Parameter 'url' must be str or HttpRequest instance")
        else:
            raise GrabMisuseError("Either url or request option must be set")
        self.schedule_time: None | datetime = None
        if name == "generator":
            # The name "generator" is restricted because
            # `task_generator` handler could not be created because
            # this name is already used for special method which
            # generates new tasks
            raise SpiderMisuseError('Task name could not be "generator"')
        self.name = name
        if valid_status is None:
            self.valid_status = []
        else:
            self.valid_status = valid_status
        self.process_delay_option(delay)
        self.fallback_name = fallback_name
        self.priority_set_explicitly = priority_set_explicitly
        self.priority = priority
        self.network_try_count = network_try_count
        self.task_try_count = task_try_count
        self.use_proxylist = use_proxylist
        self.raw = raw
        self.callback = callback
        self.store = store if store else {}
        for key, value in kwargs.items():
            setattr(self, key, value)

    # pylint:enable=too-many-arguments,too-many-locals,too-many-branches

    def check_init_kwargs(self, kwargs: Mapping[str, Any]) -> None:
        if "grab" in kwargs:
            raise GrabMisuseError("Task does not accept 'grab' parameter")
        if "grab_config" in kwargs:
            raise GrabMisuseError("Task does not accept 'grab_config' parameter")

    def get(self, key: str, default: Any = None) -> Any:
        """Return value of attribute or None if such attribute does not exist."""
        return getattr(self, key, default)

    def process_delay_option(self, delay: None | float) -> None:
        if delay:
            self.schedule_time = datetime.now(timezone.utc) + timedelta(seconds=delay)
        else:
            self.schedule_time = None

    def clone(
        self, url: None | str = None, request: None | HttpRequest = None, **kwargs: Any
    ) -> Task:
        """Clone Task instance.

        Reset network_try_count, increase task_try_count.
        Reset priority attribute if it was not set explicitly.
        """
        if url and request:
            raise GrabMisuseError("Options url and request are mutually exclusive")
        # First, create exact copy of the current Task object
        attr_copy = deepcopy(self.__dict__)
        if not attr_copy["priority_set_explicitly"]:
            attr_copy["priority"] = None
        task = Task(**attr_copy)
        if url:
            task.request.url = url
        if request:
            task.request = request
        # Reset some task properties if they have not
        # been set explicitly in kwargs
        if "network_try_count" not in kwargs:
            task.network_try_count = 0
        if "task_try_count" not in kwargs:
            task.task_try_count = self.task_try_count + 1
        for key, value in kwargs.items():
            setattr(task, key, value)
        task.process_delay_option(None)
        return task

    def __repr__(self) -> str:
        return "<Task: %s>" % self.request.url

    def __lt__(self, other: Task) -> bool:
        if self.priority is None or other.priority is None:
            return False
        return self.priority < other.priority

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        if not self.priority or not other.priority:
            # WTF???
            return True
        return self.priority == other.priority
