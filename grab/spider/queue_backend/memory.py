from __future__ import absolute_import

from .base import QueueInterface
from Queue import PriorityQueue, Empty

class QueueBackend(QueueInterface):
    def __init__(self, spider_name, **kwargs):
        super(QueueInterface, self).__init__(**kwargs)
        self.queue_object = PriorityQueue()

    def put(self, task, priority):
        self.queue_object.put((priority, task))

    def get(self):
        priority, task = self.queue_object.get(block=False)
        return task

    def size(self):
        return self.queue_object.qsize()

    def clear(self):
        try:
            while True:
                self.queue_object.get(False)
        except Empty:
            pass
