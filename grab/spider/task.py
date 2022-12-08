from __future__ import absolute_import

from datetime import datetime, timedelta

from grab.base import copy_config
from grab.error import raise_feature_is_deprecated
from grab.spider.error import SpiderMisuseError


class BaseTask:
    pass


class Task(BaseTask):
    """
    Task for spider.
    """

    def __init__(
        self,
        name=None,
        url=None,
        grab=None,
        grab_config=None,
        priority=None,
        priority_set_explicitly=True,
        network_try_count=0,
        task_try_count=1,
        valid_status=None,
        use_proxylist=True,
        delay=None,
        raw=False,
        callback=None,
        fallback_name=None,
        # deprecated
        disable_cache=False,
        refresh_cache=False,
        cache_timeout=None,
        # kwargs
        **kwargs
    ):
        """
        Create `Task` object.

        If more than one of url, grab and grab_config options are non-empty
        then they processed in following order:
        * grab overwrite grab_config
        * grab_config overwrite url

        Args:
            :param name: name of the task. After successful network operation
                task's result will be passed to `task_<name>` method.
            :param url: URL of network document. Any task requires `url` or
                `grab` option to be specified.
            :param grab: configured `Grab` instance. You can use that option in
                case when `url` option is not enough. Do not forget to
                configure `url` option of `Grab` instance because in this case
                the `url` option of `Task` constructor will be overwritten
                with `grab.config['url']`.
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
        self.grab_config = None
        if disable_cache or refresh_cache or cache_timeout:
            raise_feature_is_deprecated("Cache feature")

        if name == "generator":
            # The name "generator" is restricted because
            # `task_generator` handler could not be created because
            # this name is already used for special method which
            # generates new tasks
            raise SpiderMisuseError('Task name could not be "generator"')

        self.name = name

        if url is None and grab is None and grab_config is None:
            raise SpiderMisuseError(
                "Either url, grab or grab_config argument "
                "of Task constructor should not be None"
            )

        if url is not None and grab is not None:
            raise SpiderMisuseError("Options url and grab could not be used together")

        if url is not None and grab_config is not None:
            raise SpiderMisuseError(
                "Options url and grab_config could not be used together"
            )

        if grab is not None and grab_config is not None:
            raise SpiderMisuseError(
                "Options grab and grab_config could not be used together"
            )

        if grab:
            self.setup_grab_config(grab.dump_config())
        elif grab_config:
            self.setup_grab_config(grab_config)
        else:
            self.grab_config = None
            self.url = url

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
        self.coroutines_stack = []
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get(self, key, default=None):
        """
        Return value of attribute or None if such attribute
        does not exist.
        """
        return getattr(self, key, default)

    def process_delay_option(self, delay):
        if delay:
            self.schedule_time = datetime.utcnow() + timedelta(seconds=delay)
        else:
            self.schedule_time = None

    def setup_grab_config(self, grab_config):
        self.grab_config = copy_config(grab_config)
        self.url = grab_config["url"]

    def clone(self, **kwargs):
        """
        Clone Task instance.

        Reset network_try_count, increase task_try_count.
        Reset priority attribute if it was not set explicitly.
        """

        # First, create exact copy of the current Task object
        attr_copy = self.__dict__.copy()
        if attr_copy.get("grab_config") is not None:
            del attr_copy["url"]
        if not attr_copy["priority_set_explicitly"]:
            attr_copy["priority"] = None
        task = Task(**attr_copy)

        # Reset some task properties if they have not
        # been set explicitly in kwargs
        if "network_try_count" not in kwargs:
            task.network_try_count = 0
        if "task_try_count" not in kwargs:
            task.task_try_count = self.task_try_count + 1

        if kwargs.get("url") is not None and kwargs.get("grab") is not None:
            raise SpiderMisuseError("Options url and grab could not be used together")

        if kwargs.get("url") is not None and kwargs.get("grab_config") is not None:
            raise SpiderMisuseError(
                "Options url and grab_config could not be used together"
            )

        if kwargs.get("grab") is not None and kwargs.get("grab_config") is not None:
            raise SpiderMisuseError(
                "Options grab and grab_config could not be used together"
            )

        if kwargs.get("grab"):
            task.setup_grab_config(kwargs["grab"].dump_config())
            del kwargs["grab"]
        elif kwargs.get("grab_config"):
            task.setup_grab_config(kwargs["grab_config"])
            del kwargs["grab_config"]
        elif kwargs.get("url"):
            task.url = kwargs["url"]
            if task.grab_config:
                task.grab_config["url"] = kwargs["url"]
            del kwargs["url"]

        for key, value in kwargs.items():
            setattr(task, key, value)

        task.process_delay_option(None)

        return task

    def __repr__(self):
        return "<Task: %s>" % self.url

    def __lt__(self, other):
        return self.priority < other.priority

    def __eq__(self, other):
        if not self.priority or not other.priority:
            return True
        return self.priority == other.priority

    def get_fallback_handler(self, spider):
        if self.fallback_name:
            return getattr(spider, self.fallback_name)
        if self.name:
            fb_name = "task_%s_fallback" % self.name
            if hasattr(spider, fb_name):
                return getattr(spider, fb_name)
        return None
