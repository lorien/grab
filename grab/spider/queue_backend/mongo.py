try:
    import Queue as queue
except ImportError:
    import queue
try:
    import cPickle as pickle
except ImportError:
    import pickle
from bson import Binary
import logging
import pymongo
from datetime import datetime

from grab.spider.queue_backend.base import QueueInterface
from grab.spider.error import SpiderMisuseError

logger = logging.getLogger('grab.spider.queue_backend.mongo')


class QueueBackend(QueueInterface):
    def __init__(self, spider_name, database=None, queue_name=None,
                 **kwargs):
        """
        All "unexpected" kwargs goes to `pymongo.MongoClient()` method
        """
        if queue_name is None:
            queue_name = 'task_queue_%s' % spider_name

        self.database = database
        self.queue_name = queue_name
        conn = pymongo.MongoClient(**kwargs)
        self.collection = conn[self.database][self.queue_name]
        logger.debug('Using collection: %s' % self.collection)

        self.collection.ensure_index('priority')

        super(QueueInterface, self).__init__()

    def size(self):
        return self.collection.count()

    def put(self, task, priority, schedule_time=None):
        if schedule_time is None:
            schedule_time = datetime.utcnow()

        item = {
            'task': Binary(pickle.dumps(task)),
            'priority': priority,
            'schedule_time': schedule_time,
        }
        self.collection.save(item)

    def get(self):
        item = self.collection.find_one_and_delete(
            {'schedule_time': {'$lt': datetime.utcnow()}},
            sort=[('priority', pymongo.ASCENDING)]
        )
        if item is None:
            raise queue.Empty()
        else:
            return pickle.loads(item['task'])

    def clear(self):
        self.collection.remove()
