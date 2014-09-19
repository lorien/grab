import random
try:
    import Queue as queue
except ImportError:
    import queue
import logging
import uuid
import pickle

from grab.spider.error import SpiderMisuseError

class RedisCommandInterface(object):
    def __init__(self, spider_name, **kwargs):
        import redis

        self.redisdb = redis.StrictRedis()
        self.spider_name = spider_name
        self.input_queue_name = 'command_input_%s' % spider_name
        self.output_hash_name = 'command_output_%s' % spider_name
        logging.debug('Command input queue redis key: %s'
                      % self.input_queue_name)
        logging.debug('Command output hash redis key: %s'
                      % self.output_hash_name)

    def put_command(self, command):
        command['uid'] = str(uuid.uuid4())
        self.redisdb.rpush(self.input_queue_name, pickle.dumps(command))
        return command['uid']

    def pop_command(self):
        command_dump = self.redisdb.lpop(self.input_queue_name)
        if command_dump is None:
            return None
        else:
            return pickle.loads(command_dump)

    def put_result(self, key, result):
        result_dump = pickle.dumps(result)
        self.redisdb.hset(self.output_hash_name, key, result_dump)

    def pop_result(self, key):
        result_dump = self.redisdb.hget(self.output_hash_name, key)
        if result_dump is None:
            return None
        else:
            return pickle.loads(result_dump)

    #def size(self):
        #return len(self.queue_object)

    def clear(self):
        self.redisdb.delete(self.input_queue_name)
        self.redisdb.delete(self.output_hash_name)


class CommandController(object):
    def __init__(self, spider):
        self.spider = spider
        self.enabled = False
        self.ifaces = {}

    def add_interface(self, backend=None, **kwargs):
        if backend == 'redis':
            iface = RedisCommandInterface(self.spider.get_name(), **kwargs)
            self.ifaces[backend] = iface
            self.enabled = True
            return iface
        else:
            raise SpiderMisuseError('Unknown command interface: %s' % backend)

    def process_commands(self):
        for iface in self.ifaces.values():
            command = iface.pop_command()
            if command is not None:
                iface.put_result(command['uid'], self.process_command(command))

    def process_command(self, command):
        cname = command['name']
        handler = getattr(self.spider, 'command_%s' % cname, None)
        if handler is not None:
            return handler(command)
        else:
            return {'error': 'unknown command'}
