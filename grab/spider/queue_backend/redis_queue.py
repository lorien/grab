"""
Spider task queue backend powered by redis
"""
try:
    import Queue as queue
except ImportError:
    import queue

import logging
import pickle
import random

from fastrq.priorityqueue import PriorityQueue
from redis import StrictRedis

from grab.spider.error import SpiderMisuseError
from grab.spider.queue_backend.base import QueueInterface


class CustomPriorityQueue(PriorityQueue):
    def __init__(self, key, **kwargs):
        # sets `key` to `self._key`
        super(CustomPriorityQueue, self).__init__(key)
        self._conn_kwargs = kwargs

    # https://github.com/limen/fastrq/blob/master/fastrq/base.py
    def connect(self):
        if self._redis is None:
            self._redis = StrictRedis(decode_responses=False, **self._conn_kwargs)
        return self._redis

    def clear(self):
        if self._redis:
            self._redis.delete(self._key)


class QueueBackend(QueueInterface):
    def __init__(self, spider_name, queue_name=None, **kwargs):
        super(QueueBackend, self).__init__(spider_name, **kwargs)
        self.spider_name = spider_name
        if queue_name is None:
            queue_name = "task_queue_%s" % spider_name
        self.queue_name = queue_name
        self.queue_object = CustomPriorityQueue(queue_name, **kwargs)
        logging.debug("Redis queue key: %s", self.queue_name)

    def put(self, task, priority, schedule_time=None):
        if schedule_time is not None:
            raise SpiderMisuseError("Redis task queue does not support " "delayed task")
        # Add attribute with random value
        # This is required because qr library
        # does not allow to store multiple values with same hash
        # in the PriorityQueue

        task.redis_qr_rnd = random.random()
        self.queue_object.push({pickle.dumps(task): priority})

    def get(self):
        task = self.queue_object.pop()
        if task is None:
            raise queue.Empty()
        else:
            return pickle.loads(task[0])

    def size(self):
        return len(self.queue_object)

    def clear(self):
        self.queue_object.clear()

    def close(self):
        # get conneciton opened by qr and close it
        pass
