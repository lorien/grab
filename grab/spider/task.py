from random import randint

from error import SpiderMisuseError

class Task(object):
    """
    Task for spider.
    """

    def __init__(self, name, url=None, grab=None, priority=None,
                 network_try_count=0, task_try_count=0, **kwargs):
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
