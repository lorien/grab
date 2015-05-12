"""
This module contains Stat class. It is used inside
Grab::Spider to collect statistics about events happening
during the scraping session.
"""
import logging
from collections import defaultdict
import time
from contextlib import contextmanager

DEFAULT_COUNTER_KEY = 'DEFAULT'


class Stat(object):
    def __init__(self, logger_name='grab.stat', log_file=None,
                 logging_period=5):
        self.time = time.time()
        self.logging_period = logging_period
        self.count_prev = 0
        self.counters = defaultdict(int)
        self.collections = defaultdict(list)
        self.time_points = {}
        self.timers = defaultdict(int)
        self.logger_name = logger_name
        self.logger = logging.getLogger(logger_name)
        self.setup_logging_file(log_file)
        self.logging_ignore_prefixes = ['spider:']

    def setup_logging_file(self, log_file):
        self.log_file = log_file
        if log_file:
            self.logger.addHandler(logging.FileHandler(log_file, 'w'))
            self.logger.setLevel(logging.DEBUG)

    def get_counters_line(self):
        items = []
        for key in sorted(self.counters.keys()):
            if not any(key.startswith(x)
                       for x in self.logging_ignore_prefixes):
                items.append('%s=%d' % (key, self.counters[key]))
        return ', '.join(items)

    def inc(self, key=DEFAULT_COUNTER_KEY, delta=1):
        self.counters[key] += delta
        now = time.time()
        if now - self.time > self.logging_period:
            count_current = self.counters[DEFAULT_COUNTER_KEY]
            diff = count_current - self.count_prev
            qps = diff / (now - self.time) 
            self.logger.debug(
                'rps: %.2f [%s]' % (qps, self.get_counters_line()))
            self.count_prev = count_current
            self.time = now

    def append(self, key, val):
        self.collections[key].append(val)

    def start_timer(self, key):
        self.time_points[key] = time.time()

    def stop_timer(self, key):
        start = self.time_points[key]
        now = time.time()
        total = now - start
        self.timers[key] += total
        del self.time_points[key]
        return total

    @contextmanager
    def log_time(self, key):
        self.start_timer(key)
        try:
            yield
        finally:
            self.stop_timer(key)
