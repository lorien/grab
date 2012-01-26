from random import randint

from error import SpiderMisuseError

class Task(object):
    """
    Task for spider.
    """

    def __init__(self, name, url=None, grab=None, priority=None,
                 network_try_count=0, task_try_count=0, 
                 disable_cache=False, refresh_cache=False,
                 **kwargs):
        """
        Create `Task` object.

        Args:
            :param name: name of the task. After successfull network operation
                task's result will be passed to `task_<name>` method.
            :param url: URL of network document. Any task requires `url` or `grab`
                option to be specified.
            :param grab: configured `Grab` instance. You can use that option in case
                when `url` option is not enought. Do not forget to configure `url` option
                of `Grab` instance because in this case the `url` option of `Task`
                constructor will be ignored.
            :param priority: - priority of the Task. Tasks with lower priority will be
                processed earlier. By default each new task is assigned with random
                priority from (80, 100) range.
            :param network_try_count: you'll probably will not need to use it. It is used
                internally to control how many times this task was restarted due to network
                errors. The `Spider` instance has `network_try_limit` option. When
                `network_try_count` attribut of the task exceeds the `network_try_limit`
                attribut then processing of the task is abandoned.
            :param task_try_count: the as `network_try_count` but it increased only then you
                use `clone` method. Also you can set it manually. It is usefull if you want
                to restart the task after it was cacelled due to multiple network errors.
                As you might guessed there is `task_try_limit` option in `Spider` instance.
                Both options `network_try_count` and `network_try_limit` guarantee you that
                you'll not get infinite loop of restarting some task.
            :param disable_cache: if `True` disable cache subsystem. The document will be
                fetched from the Network and it will not be saved to cache.
            :param refresh_cache: if `True` the document will be fetched from the Network
                and saved to cache.

            Any non-standard named arguments passed to `Task` constructor will be saved as
            attributes of the object. You can get their values later as attributes or with
            `get` method which allows to use default value if attrubute does not exist.
        """

        self.name = name
        if url is None and grab is None:
            raise SpiderMisuseError('Either url of grab option of '\
                                    'Task should be not None')
        if priority is None:
            priority = randint(80, 100)
        self.url = url
        self.grab = grab
        self.priority = priority
        if self.grab:
            self.url = grab.config['url']
        self.network_try_count = network_try_count
        self.task_try_count = task_try_count
        self.disable_cache = disable_cache
        self.refresh_cache = refresh_cache
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get(self, key, default=None):
        """
        Return value of attribute or None if such attribute
        does not exist.
        """
        return getattr(self, key, default)

    def clone(self, **kwargs):
        """
        Clone Task instance.

        Reset network_try_count, increase task_try_count.
        Also reset grab property
        TODO: maybe do not reset grab
        """

        task = Task(self.name, self.url)

        for key, value in self.__dict__.items():
            if key != 'grab':
                setattr(task, key, getattr(self, key))

        task.network_try_count = 0
        task.task_try_count += 1
        task.grab = None

        for key, value in kwargs.items():
            setattr(task, key, value)
            
        if 'grab' in kwargs:
            task.url = kwargs['grab'].config['url']

        return task
