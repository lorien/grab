"""QueueInterface defines interface of queue backend."""
from datetime import datetime
from typing import Any, Optional

from grab.spider.task import Task


class QueueInterface:
    def __init__(self, spider_name: str, **kwargs: Any) -> None:
        pass

    def put(
        self,
        task: Task,
        priority: int,
        schedule_time: Optional[datetime] = None,
    ) -> None:
        raise NotImplementedError

    def get(self) -> Task:
        """
        Return `Task` object or raise `Queue.Empty` exception.

        @returns: `grab.spider.task.Task` object
        @raises: `Queue.Empty` exception
        """
        raise NotImplementedError

    def size(self) -> int:
        raise NotImplementedError

    def clear(self) -> None:
        """Remove all tasks from the queue."""
        raise NotImplementedError
