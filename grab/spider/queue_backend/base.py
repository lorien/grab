from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Any

from grab.spider.task import Task


class BaseTaskQueue:
    def __init__(self, spider_name: str, **kwargs: Any) -> None:
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
