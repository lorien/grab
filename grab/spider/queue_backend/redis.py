"""Spider task queue backend powered by redis."""
from __future__ import annotations

import logging
import pickle
import queue
import time
from datetime import datetime
from secrets import SystemRandom
from typing import Any, cast

from fastrq.priorityqueue import PriorityQueue  # pytype: disable=import-error
from redis import Redis

from grab.spider.errors import SpiderMisuseError
from grab.spider.task import Task

from .base import BaseTaskQueue

system_random = SystemRandom()


class CustomPriorityQueue(PriorityQueue):  # type: ignore # TODO: fix
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
        self,
        queue_name: None | str = None,
        connection_args: None | dict[str, Any] = None,
    ) -> None:
        super().__init__()
        self.queue_name: str = (
            queue_name if queue_name is not None else self.random_queue_name()
        )
        self.queue_object = CustomPriorityQueue(
            self.queue_name, **(connection_args or {})
        )
        logging.debug("Redis queue key: %s", self.queue_name)

    def put(
        self,
        task: Task,
        priority: int,
        schedule_time: None | datetime = None,
    ) -> None:
        if schedule_time is not None:
            raise SpiderMisuseError("Redis task queue does not support delayed task")
        # Add attribute with random value
        # This is required because qr library
        # does not allow to store multiple values with same hash
        # in the PriorityQueue

        task.store["redis_qr_time"] = time.time()
        task.store["redis_qr_rnd"] = system_random.random()
        self.queue_object.push({pickle.dumps(task): priority})

    def get(self) -> Task:
        task: None | tuple[Any, int] = self.queue_object.pop()
        if task is None:
            raise queue.Empty
        return cast(
            Task,
            pickle.loads(task[0]),  # noqa: S301 pylint: disable=unsubscriptable-object
        )

    def size(self) -> int:
        return len(self.queue_object)

    def clear(self) -> None:
        self.queue_object.clear()

    def close(self) -> None:
        # get connection opened by qr and close it
        pass
