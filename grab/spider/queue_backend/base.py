"""
QueueInterface defines interface of queue backend.
"""


class QueueInterface(object):
    def __init__(self, spider_name, **kwargs):
        pass

    def put(self, task, priority):
        raise NotImplementedError

    def get(self):
        """
        Return `Task` object or raise `Queue.Empty` exception

        @returns: `grab.spider.task.Task` object
        @raises: `Queue.Empty` exception
        """
        raise NotImplementedError

    def size(self):
        raise NotImplementedError

    def clear(self):
        """Remove all tasks from the queue."""
        raise NotImplementedError
