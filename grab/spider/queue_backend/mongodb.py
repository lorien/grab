import logging
import pickle
import queue
from datetime import datetime
from typing import Any, Optional, cast

import pymongo
from bson import Binary
from pymongo import MongoClient
from pymongo.collection import Collection

from grab.spider.queue_backend.base import BaseTaskQueue
from grab.spider.task import Task
from grab.types import JsonDocument

LOG = logging.getLogger("grab.spider.queue_backend.mongodb")


class MongodbTaskQueue(BaseTaskQueue):
    def __init__(
        self,
        spider_name: str,
        database: str,
        queue_name: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        # All "unexpected" kwargs goes to "pymongo.MongoClient()" method
        if queue_name is None:
            queue_name = "task_queue_%s" % spider_name

        self.database = database
        self.queue_name = queue_name
        self.connection: MongoClient[JsonDocument] = MongoClient(**kwargs)
        self.collection: Collection[JsonDocument] = self.connection[self.database][
            self.queue_name
        ]
        LOG.debug("Using collection: %s", self.collection)

        self.collection.create_index([("priority", 1)])

        super().__init__(spider_name, **kwargs)

    def size(self) -> int:
        return self.collection.count_documents({})

    def put(
        self,
        task: Task,
        priority: int,
        schedule_time: Optional[datetime] = None,
    ) -> None:
        if schedule_time is None:
            schedule_time = datetime.utcnow()
        item = {
            "task": Binary(pickle.dumps(task)),
            "priority": priority,
            "schedule_time": schedule_time,
        }
        self.collection.insert_one(item)

    def get(self) -> Task:
        item = self.collection.find_one_and_delete(
            {"schedule_time": {"$lt": datetime.utcnow()}},
            sort=[("priority", pymongo.ASCENDING)],
        )
        if item is None:
            raise queue.Empty()
        return cast(Task, pickle.loads(item["task"]))

    def clear(self) -> None:
        self.collection.delete_many({})

    def close(self) -> None:
        self.connection.close()
