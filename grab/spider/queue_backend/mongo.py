from Queue import Queue
from time import time
from cPickle import dumps, loads

from pymongo import Connection, ASCENDING
from pymongo.binary import Binary


class QueueBackend(Queue):
    def __init__(self, database, **kwargs):
        clear_on_init = kwargs.pop('clear_on_init', False)
        clear_on_del = kwargs.pop('clear_on_del', False)
        name = kwargs.pop('name', None)

        if name is None:
            name = 'queue_%s' % str(time())
            if clear_on_init:
                raise Exception('Not named queue!')
            clear_on_del = True

        self.database_name = database
        self.collection_name = name
        self.clear_on_init = clear_on_init
        self.clear_on_del = clear_on_del

        Queue.__init__(self, **kwargs)

    def __del__(self):
        if self.clear_on_del:
            self.clear()

    def _init(self, maxsize):
        connection = Connection()
        database = connection[self.database_name]
        self.collection = database[self.collection_name]

        if self.clear_on_init:
            self.clear()

    def clear(self):
        self.collection.drop()

    def _qsize(self, len=len):
        return self.collection.count()

    def _put(self, item):
        priority, value = item[:2]
        item = {
            'value': Binary(dumps(value)),
            'priority': priority,
            }
        self.collection.save(item)

    def _get(self):
        item = self.collection.find_and_modify(
            sort={'priority': ASCENDING},
            remove=True
        )
        priority = item.get('priority', 0)
        value = item.get('value', None)
        return (priority, loads(value))
