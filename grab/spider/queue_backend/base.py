from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Any
from uuid import uuid4

from grab.spider.task import Task


class BaseTaskQueue:
    def __init__(self, **kwargs: Any) -> None:
        pass

    def put(
        self,
        task: Task,
        priority: int,
        schedule_time: None | datetime = None,
    ) -> None:
        raise NotImplementedError

    def get(self) -> Task:
        """Return `Task` object or raise `Queue.Empty` exception.

        @returns: `grab.spider.task.Task` object
        @raises: `Queue.Empty` exception
        """
        raise NotImplementedError

    @abstractmethod
    def size(self) -> int:
        raise NotImplementedError

    def clear(self) -> None:
        """Remove all tasks from the queue."""
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def random_queue_name(self) -> str:
        return "task_queue_{}".format(str(uuid4()).replace("-", "_"))
