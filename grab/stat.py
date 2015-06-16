"""
This module contains Stat class. It is used inside
Grab::Spider to collect statistics about events happening
during the scraping session.
"""
import logging
from collections import defaultdict
import time
from contextlib import contextmanager

DEFAULT_SPEED_KEY = 'spider:request-processed'
DEFAULT_LOGGING_PERIOD = 1


class Stat(object):
    def __init__(self, logger_name='grab.stat', log_file=None,
                 logging_period=DEFAULT_LOGGING_PERIOD,
                 extra_speed_keys=None):
        self.setup_speed_keys(extra_speed_keys)
        self.time = time.time()
        self.logging_ignore_prefixes = ['spider:', 'parser:']
        self.logging_period = logging_period
        self.count_prev = 0
        self.logger_name = logger_name
        self.logger = logging.getLogger(logger_name)
        self.setup_logging_file(log_file)
        self.reset()

    def setup_speed_keys(self, extra_keys):
        keys = [DEFAULT_SPEED_KEY]
        if extra_keys:
            keys.extend(extra_keys)
        self.speed_keys = keys

    def reset(self):
        self.counters = defaultdict(int)
        self.collections = defaultdict(list)
        self.counters_prev = defaultdict(int)

    def setup_logging_file(self, log_file):
        self.log_file = log_file
        if log_file:
            self.logger.addHandler(logging.FileHandler(log_file, 'w'))
            self.logger.setLevel(logging.DEBUG)

    def get_counter_line(self):
        result = []
        for key in self.counters.keys():
            if not any(key.startswith(x)
                       for x in self.logging_ignore_prefixes):
                result.append((key, '%s=%d' % (key, self.counters[key])))
        for key in self.collections.keys():
            if not any(key.startswith(x)
                       for x in self.logging_ignore_prefixes):
                result.append((key,
                               '%s=%d' % (key, len(self.collections[key]))))
        tokens = [x[1] for x in sorted(result, key=lambda x: x[0])]
        return ', '.join(tokens)

    def get_speed_line(self, now):
        items = []
        for key in self.speed_keys:
            count_current = self.counters[key]
            diff = count_current - self.counters_prev[key]
            qps = diff / (now - self.time) 
            self.counters_prev[key] = count_current
            if key == DEFAULT_SPEED_KEY:
                label = 'RPS'
            else:
                label = key
            items.append('%s: %.2f' % (label, qps))
        return ', '.join(items)

    def print_progress_line(self):
        now = time.time()
        self.logger.debug('%s [%s]' % (self.get_speed_line(now),
                                       self.get_counter_line()))

    def inc(self, key, delta=1):
        self.counters[key] += delta
        now = time.time()
        if self.logging_period and now - self.time > self.logging_period:
            self.print_progress_line()
            self.time = now

    def collect(self, key, val):
        self.collections[key].append(val)

    def append(self, key, val):
        logging.error('Method `Stat::append` is deprecated. '
                      'Use `Stat::collect` method.')
        self.collect(key, val)


class Timer(object):
    def __init__(self):
        self.time_points = {}
        self.timers = defaultdict(int)

    def start(self, key):
        self.time_points[key] = time.time()

    def stop(self, key):
        start = self.time_points[key]
        total = time.time() - start
        self.timers[key] += total
        del self.time_points[key]
        return total

    def inc_timer(self, key, value):
        self.timers[key] += value

    @contextmanager
    def log_time(self, key):
        self.start(key)
        try:
            yield
        finally:
            self.stop(key)
