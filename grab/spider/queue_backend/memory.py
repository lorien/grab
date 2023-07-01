from __future__ import annotations

from contextlib import suppress
from datetime import datetime, timezone
from queue import Empty, PriorityQueue

from grab.spider.queue_backend.base import BaseTaskQueue
from grab.spider.task import Task


class MemoryTaskQueue(BaseTaskQueue):
    def __init__(self) -> None:
        super().__init__()
        self.queue_object: PriorityQueue[tuple[int, Task]] = PriorityQueue()
        self.schedule_list: list[tuple[datetime, Task]] = []

    def put(
        self, task: Task, priority: int, schedule_time: None | datetime = None
    ) -> None:
        if schedule_time is None:
            self.queue_object.put((priority, task))
        else:
            self.schedule_list.append((schedule_time, task))

    def get(self) -> Task:
        now = datetime.now(timezone.utc)

        removed_indexes = []
        for idx, item in enumerate(self.schedule_list):
            schedule_time, task = item
            if schedule_time <= now:
                self.put(task, 1)
                removed_indexes.append(idx)

        self.schedule_list = [
            x for idx, x in enumerate(self.schedule_list) if idx not in removed_indexes
        ]

        _, task = self.queue_object.get(block=False)
        return task

    def size(self) -> int:
        return self.queue_object.qsize() + len(self.schedule_list)

    def clear(self) -> None:
        with suppress(Empty):
            while True:
                self.queue_object.get(False)
        self.schedule_list = []

    def close(self) -> None:
        pass
