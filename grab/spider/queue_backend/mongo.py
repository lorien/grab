from Queue import Queue
from time import time
from cPickle import dumps, loads

from pymongo import Connection, ASCENDING
from pymongo.binary import Binary


class QueueBackend(Queue):
    def __init__(self, database, **kwargs):
        clear_on_init = kwargs.get('clear_on_init', False)
        clear_on_del = kwargs.get('clear_on_init', False)
        name = kwargs.get('name', None)

        if not name:
            name = 'queue_%s' % str(time())
            if clear_on_init:
                raise Exception('Not named queue!')
            self.clear_on_del = True

        self.database = database
        self.name = name
        self.clear_on_init = clear_on_init
        self.clear_on_del = clear_on_del

        Queue.__init__(self, **kwargs)

    def __del__(self):
        if self.clear_on_del:
            self.clear()

    def _init(self, maxsize):
        connection = Connection()
        database = connection[self.database]

        self.queue = database[self.name]

        if self.clear_on_init:
            self.clear()

    def clear(self):
        if not self.empty():
            self.queue.drop()

    def _qsize(self, len=len):
        return self.queue.count()

    def _put(self, item):
        priority, value = item[:2]
        item = {
            'value': Binary(dumps(value)),
            'priority': priority,
            }
        self.queue.save(item)

    def _get(self):
        item = self.queue.find_and_modify(
            sort={'priority': ASCENDING},
            remove=True
        )
        priority = item.get('priority', 0)
        value = item.get('value', None)
        return (priority, loads(value))
