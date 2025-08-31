from __future__ import annotations

import logging
import pickle
import queue
from datetime import datetime, timezone
from typing import Any, cast

import pymongo
from bson import Binary
from pymongo import MongoClient
from pymongo.collection import Collection

from grab.spider.queue_backend.base import BaseTaskQueue
from grab.spider.task import Task

LOG = logging.getLogger("grab.spider.queue_backend.mongodb")


class MongodbTaskQueue(BaseTaskQueue):
    def __init__(
        self,
        connection_args: None | dict[str, Any] = None,
        collection_name: None | str = None,
        database_name: str = "grab_spider",
    ) -> None:
        super().__init__()
        self.database_name: str = database_name
        self.collection_name: str = collection_name or self.random_queue_name()
        self.connection: MongoClient[Any] = MongoClient(**(connection_args or {}))
        self.collection: Collection[Any] = self.connection[self.database_name][
            self.collection_name
        ]
        LOG.debug(
            "Using collection %s in database %s",
            self.collection_name,
            self.database_name,
        )
        self.collection.create_index([("priority", 1)])

    def size(self) -> int:
        return self.collection.count_documents({})

    def put(
        self,
        task: Task,
        priority: int,
        schedule_time: None | datetime = None,
    ) -> None:
        if schedule_time is None:
            schedule_time = datetime.now(timezone.utc)
        item = {
            "task": Binary(pickle.dumps(task)),
            "priority": priority,
            "schedule_time": schedule_time,
        }
        self.collection.insert_one(item)

    def get(self) -> Task:
        item = self.collection.find_one_and_delete(
            {"schedule_time": {"$lt": datetime.now(timezone.utc)}},
            sort=[("priority", pymongo.ASCENDING)],
        )
        if item is None:
            raise queue.Empty
        return cast(Task, pickle.loads(item["task"]))  # noqa: S301

    def clear(self) -> None:
        self.collection.delete_many({})

    def close(self) -> None:
        self.connection.close()
