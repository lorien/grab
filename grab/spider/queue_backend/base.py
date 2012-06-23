"""
QueueInterface defines interface of queue backend.
"""

class QueueInterface(object):
    def __init__(self, **kwargs):
        pass

    def put(self, task, priority):
        pass

    def get(self, timeout):
        """
        Return `Task` object or raise `Queue.Empty` exception
        after `timeout` seconds.

        @returns: `grab.spider.task.Task` object
        @raises: `Queue.Empty` exception
        """

    def size(self):
        pass
