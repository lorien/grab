from __future__ import absolute_import
from datetime import datetime

from .base import QueueInterface
try:
    from Queue import PriorityQueue, Empty
except ImportError:
    from queue import PriorityQueue, Empty

class QueueBackend(QueueInterface):
    def __init__(self, spider_name, **kwargs):
        super(QueueInterface, self).__init__(**kwargs)
        self.queue_object = PriorityQueue()
        self.schedule_list = []

    def put(self, task, priority, schedule_time=None):
        if schedule_time is None:
            self.queue_object.put((priority, task))
        else:
            self.schedule_list.append((schedule_time, task))

    def get(self):
        now = datetime.now()

        removed_indexes = []
        idx = 0
        for schedule_time, task in self.schedule_list:
            if schedule_time <= now:
                self.put(task, 1)
                removed_indexes.append(idx)
            idx += 1

        self.schedule_list = [x for idx, x in enumerate(self.schedule_list)
                              if not idx in removed_indexes]

        priority, task = self.queue_object.get(block=False)
        return task

    def size(self):
        return self.queue_object.qsize() + len(self.schedule_list)

    def clear(self):
        try:
            while True:
                self.queue_object.get(False)
        except Empty:
            pass
        self.schedule_list = []
