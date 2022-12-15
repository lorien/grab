from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Any
from uuid import uuid4

from grab.spider.task import Task


class BaseTaskQueue:
    def __init__(self, **kwargs: Any) -> None:
        pass

    def random_queue_name(self) -> str:
        return "task_queue_{}".format(str(uuid4()).replace("-", "_"))

    def put(
        self,
        task: Task,
        priority: int,
        schedule_time: None | datetime = None,
    ) -> None:  # pragma: no cover
        raise NotImplementedError

    def get(self) -> Task:  # pragma: no cover
        """Return `Task` object or raise `Queue.Empty` exception.

        @returns: `grab.spider.task.Task` object
        @raises: `Queue.Empty` exception
        """
        raise NotImplementedError

    @abstractmethod
    def size(self) -> int:  # pragma: no cover
        raise NotImplementedError

    def clear(self) -> None:  # pragma: no cover
        """Remove all tasks from the queue."""
        raise NotImplementedError

    def close(self) -> None:  # pragma: no cover
        raise NotImplementedError
