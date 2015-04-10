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

    def save_list(self, list_name, path):
        """
        Save items from list to the file.
        """

        with open(path, 'wb') as out:
            lines = []
            for item in self.items.get(list_name, []):
                if isinstance(item, (six.text_type, six.binary_type)):
                    lines.append(smart_str(item))
                else:
                    lines.append(smart_str(json.dumps(item)))
            out.write(b'\n'.join(lines) + b'\n')

    def render_stats(self, timing=True):
        out = []
        out.append('Counters:')
        # Sort counters by its names
        items = sorted(self.counters.items(), key=lambda x: x[0], reverse=True)
        out.append('  %s' % '\n  '.join('%s: %s' % x for x in items))
        out.append('\nLists:')
        # Sort lists by number of items
        items = [(x, len(y)) for x, y in self.items.items()]
        items = sorted(items, key=lambda x: x[1], reverse=True)
        out.append('  %s' % '\n  '.join('%s: %s' % x for x in items))

        if 'download-size' in self.counters:
            out.append('Network download: %s' % metric.format_traffic_value(
                self.counters['download-size']))
        out.append('Queue size: %d' % self.taskq.size()
                   if self.taskq else 'NA')
        out.append('Threads: %d' % self.thread_number)

        if timing:
            out.append(self.render_timing())
        return '\n'.join(out) + '\n'

    def render_timing(self):
        out = []
        out.append('Timers:')
        out.append('  DOM: %.3f' % GLOBAL_STATE['dom_build_time'])
        out.append('  selector: %.03f' % GLOBAL_STATE['selector_time'])
        items = [(x, y) for x, y in self.timers.items()]
        items = sorted(items, key=lambda x: x[1])
        out.append('  %s' % '\n  '.join('%s: %.03f' % x for x in items))
        return '\n'.join(out) + '\n'

    def save_all_lists(self, dir_path):
        """
        Save each list into file in specified directory.
        """

        for key, items in self.items.items():
            path = os.path.join(dir_path, '%s.txt' % key)
            self.save_list(key, path)

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
