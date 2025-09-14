try:
    import Queue as queue
except ImportError:
    import queue
try:
    import cPickle as pickle
except ImportError:
    import pickle

import logging
from datetime import datetime

import pymongo
from bson import Binary

from grab.spider.queue_backend.base import QueueInterface

# pylint: disable=invalid-name
logger = logging.getLogger("grab.spider.queue_backend.mongodb")
# pylint: enable=invalid-name


class QueueBackend(QueueInterface):
    def __init__(self, spider_name, database=None, queue_name=None, **kwargs):
        """
        All "unexpected" kwargs goes to `pymongo.MongoClient()` method
        """
        if queue_name is None:
            queue_name = "task_queue_%s" % spider_name
        self.dbname = database
        self.queue_name = queue_name
        self.init_kwargs = kwargs
        self.connection, self.collection = self.connect()
        self.collection.create_index("priority")
        logger.debug("Using collection: %s", self.collection)
        super(QueueBackend, self).__init__(spider_name, **kwargs)

    def connect(self):
        conn = pymongo.MongoClient(**self.init_kwargs)
        coll = conn[self.dbname][self.queue_name]
        return conn, coll

    def reconnect(self):
        self.connection, self.collection = self.connect()

    def size(self):
        return self.collection.count_documents({})

    def put(self, task, priority, schedule_time=None):
        if schedule_time is None:
            schedule_time = datetime.utcnow()

        item = {
            "task": Binary(pickle.dumps(task)),
            "priority": priority,
            "schedule_time": schedule_time,
        }
        self.collection.insert_one(item)

    def get(self):
        item = self.collection.find_one_and_delete(
            {"schedule_time": {"$lt": datetime.utcnow()}},
            sort=[("priority", pymongo.ASCENDING)],
        )
        if item is None:
            raise queue.Empty()
        else:
            return pickle.loads(item["task"])

    def clear(self):
        self.collection.delete_many({})

    def close(self):
        self.connection.close()
