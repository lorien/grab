from __future__ import absolute_import
import logging
import time
from grab.base import GLOBAL_STATE
from weblib.encoding import smart_str
import os
from contextlib import contextmanager
import json
import six

from weblib import metric

logger = logging.getLogger('grab.spider.stat')


class SpiderStat(object):
    """
    This base-class defines methods to use for
    collecting statistics about spider work.
    """

    def add_item(self, list_name, item):
        """
        You can call multiply time this method in process of parsing.

        self.add_item('foo', 4)
        self.add_item('foo', 'bar')

        and after parsing you can access to all saved values:

        spider_instance.items['foo']
        """

        lst = self.items.setdefault(list_name, [])
        lst.append(item)

    def inc_count(self, key, count=1):
        """
        You can call multiply time this method in process of parsing.

        self.inc_count('regurl')
        self.inc_count('captcha')

        and after parsing you can access to all saved values:

        print 'Total: %(total)s, captcha: %(captcha)s' % spider_obj.counters
        """

        self.counters[key] += count
        return self.counters[key]

    def start_timer(self, key):
        self.time_points['start-%s' % key] = time.time()

    def stop_timer(self, key):
        now = time.time()
        start_key = 'start-%s' % key
        try:
            start = self.time_points[start_key]
        except KeyError:
            logger.error('Could not find start point with key %s' % key)
            return 0
        else:
            total = now - start
            if key not in self.timers:
                self.timers[key] = 0
            self.timers[key] += total
            del self.time_points[start_key]
            return total

    @contextmanager
    def save_timer(self, key):
        self.start_timer(key)
        try:
            yield
        finally:
            self.stop_timer(key)
