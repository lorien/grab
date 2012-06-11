from __future__ import absolute_import 

from .base import QueueInterface
from Queue import PriorityQueue

class QueueBackend(QueueInterface):
    def __init__(self, **kwargs):
        super(QueueInterface, self).__init__(**kwargs)
        self.queue_object = PriorityQueue()

    def put(self, task, priority):
        self.queue_object.put((priority, task))

    def get(self, timeout):
        priority, task = self.queue_object.get(True, timeout) 
        return task

    def size(self):
        return self.queue_object.qsize()
