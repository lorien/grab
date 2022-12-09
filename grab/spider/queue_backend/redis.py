"""Spider task queue backend powered by redis."""
from __future__ import annotations

import logging
import pickle
import queue
import random
import time
from datetime import datetime
from typing import Any, Optional, cast

from fastrq.priorityqueue import PriorityQueue  # pytype: disable=import-error
from redis import Redis

from grab.spider.error import SpiderMisuseError
from grab.spider.queue_backend.base import BaseTaskQueue
from grab.spider.task import Task


class CustomPriorityQueue(PriorityQueue):  # type: ignore
    def __init__(self, key: str, **kwargs: Any) -> None:
        # sets `key` to `self._key`
        super().__init__(key)
        self._conn_kwargs = kwargs

    # https://github.com/limen/fastrq/blob/master/fastrq/base.py
    def connect(self) -> Redis[Any]:
        if self._redis is None:
            self._redis: Redis[Any] = Redis(decode_responses=False, **self._conn_kwargs)
        return self._redis

    def clear(self) -> None:
        if self._redis:
            self._redis.delete(self._key)


class RedisTaskQueue(BaseTaskQueue):
    def __init__(
        self, spider_name: str, queue_name: Optional[str] = None, **kwargs: Any
    ) -> None:
        super().__init__(spider_name, **kwargs)
        self.spider_name = spider_name
        if queue_name is None:
            queue_name = "task_queue_%s" % spider_name
        self.queue_name = queue_name
        self.queue_object = CustomPriorityQueue(queue_name, **kwargs)
        logging.debug("Redis queue key: %s", self.queue_name)

    def put(
        self,
        task: Task,
        priority: int,
        schedule_time: Optional[datetime] = None,
    ) -> None:
        if schedule_time is not None:
            raise SpiderMisuseError("Redis task queue does not support delayed task")
        # Add attribute with random value
        # This is required because qr library
        # does not allow to store multiple values with same hash
        # in the PriorityQueue

        task.store["redis_qr_time"] = time.time()
        task.store["redis_qr_rnd"] = random.random()
        self.queue_object.push({pickle.dumps(task): priority})

    def get(self) -> Task:
        task = self.queue_object.pop()
        if task is None:
            raise queue.Empty()
        return cast(
            Task, pickle.loads(task[0])  # pylint: disable=unsubscriptable-object
        )

    def size(self) -> int:
        return len(self.queue_object)

    def clear(self) -> None:
        self.queue_object.clear()

    def close(self) -> None:
        # get connection opened by qr and close it
        pass
