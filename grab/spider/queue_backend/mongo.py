from __future__ import absolute_import
import Queue
from time import time
import cPickle as pickle
import uuid
from bson import Binary
import logging
import pymongo

from .base import QueueInterface

logger = logging.getLogger('grab.spider.queue_backend.mongo')

class QueueBackend(QueueInterface):
    def __init__(self, spider_name, database=None, queue_name=None,
                 **kwargs):
        """
        All "unexpected" kwargs goes to `pymongo.Connection()` method
        """
        if queue_name is None:
            queue_name = 'task_queue_%s' % spider_name

        self.database = database
        self.queue_name = queue_name
        conn = pymongo.Connection(**kwargs)
        self.collection = conn[self.database][self.queue_name]
        logger.debug('Using collection: %s' % self.collection)

        self.collection.ensure_index('priority')

        super(QueueInterface, self).__init__(**kwargs)

    def clear_collection(self):
        logger.debug('Deleting collection: %s' % self.collection)
        self.collection.drop()

    def size(self):
        return self.collection.count()

    def put(self, task, priority):
        item = {
            'task': Binary(pickle.dumps(task)),
            'priority': priority,
        }
        self.collection.save(item)

    def get(self):
        item = self.collection.find_and_modify(
            sort=[('priority', pymongo.ASCENDING)],
            remove=True
        )
        if item is None:
            raise Queue.Empty()
        else:
            return pickle.loads(item['task'])

    def clear(self):
        self.collection.remove()
