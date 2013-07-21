"""
Spider task queue backend powered by redis
"""
from __future__ import absolute_import

from redis import StrictRedis
from qr import PriorityQueue
try:
    import Queue as queue
except ImportError:
    import queue
import random

from .base import QueueInterface
from ..error import SpiderMisuseError

class QueueBackend(QueueInterface):
    def __init__(self, spider_name, queue_name=None, **kwargs):
        super(QueueInterface, self).__init__(**kwargs)
        self.spider_name = spider_name
        if queue_name is None:
            queue_name = 'task_queue_%s' % spider_name
        self.queue_name = queue_name
        self.queue_object = PriorityQueue(queue_name)

    def put(self, task, priority, schedule_time=None):
        # Add attribute with random value
        # This is required because qr library
        # does not allow to store multiple values with same hash
        # in the PriorityQueue

        if schedule_time is not None:
            raise SpiderMisuseError('Redis task queue does not support delayed task') 
        task._rnd = random.random()
        self.queue_object.push(task, priority)


    def get(self):
        task = self.queue_object.pop()
        if task is None:
            raise queue.Empty()
        else:
            return task

    def size(self):
        return len(self.queue_object)

    def clear(self):
        con = StrictRedis()
        con.delete(self.queue_name)
        #try:
            #while True:
                #self.get()
        #except queue.Empty:
            #pass
