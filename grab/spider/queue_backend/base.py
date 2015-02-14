"""
QueueInterface defines interface of queue backend.
"""


class QueueInterface(object):
    def __init__(self, spider_name, **kwargs):
        pass

    def put(self, task, priority):
        pass

    def get(self):
        """
        Return `Task` object or raise `Queue.Empty` exception

        @returns: `grab.spider.task.Task` object
        @raises: `Queue.Empty` exception
        """

    def size(self):
        pass

    def clear(self):
        """
        Remove all tasks from the queue.
        """
