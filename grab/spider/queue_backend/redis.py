"""
Spider task queue backend powered by redis
"""
from __future__ import absolute_import

from .base import QueueInterface
from qr import PriorityQueue
import Queue
import random

class QueueBackend(QueueInterface):
    def __init__(self, prefix='spider_task', **kwargs):
        super(QueueInterface, self).__init__(**kwargs)
        self.queue_object = PriorityQueue(prefix)

    def put(self, task, priority):
        # Add attribute with random value
        # This is required because qr library
        # does not allow to store multiple values with same hash
        # in the PriorityQueue
        task._rnd = random.random()
        self.queue_object.push(task, priority)

    def get(self, timeout):
        task = self.queue_object.pop()
        if task is None:
            raise Queue.Empty()
        else:
            return task

    def size(self):
        return len(self.queue_object)

    def clear(self):
        try:
            while True:
                self.get(0)
        except Queue.Empty:
            pass
