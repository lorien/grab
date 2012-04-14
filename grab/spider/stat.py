from __future__ import absolute_import
import logging
import time
from grab.base import GLOBAL_STATE

logger = logging.getLogger('grab.spider.stat')

class SpiderStat(object):
    """
    This base-class defines methods to use for
    collecting statistics about spider work.
    """

    def add_item(self, list_name, item, display=False):
        """
        You can call multiply time this method in process of parsing.

        self.add_item('foo', 4)
        self.add_item('foo', 'bar')

        and after parsing you can acces to all saved values:

        spider_instance.items['foo']
        """

        lst = self.items.setdefault(list_name, [])
        lst.append(item)
        if display:
            logger.debug(list_name)

    def save_list(self, list_name, path):
        """
        Save items from list to the file.
        """

        with open(path, 'w') as out:
            lines = []
            for item in self.items.get(list_name, []):
                if isinstance(item, basestring):
                    lines.append(item)
                else:
                    lines.append(json.dumps(item))
            out.write('\n'.join(lines))

    def render_stats(self):
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

        total_time = time.time() - self.start_time
        out.append('Queue size: %d' % self.taskq.qsize())
        out.append('Threads: %d' % self.thread_number)
        out.append('DOM build time: %.3f' % GLOBAL_STATE['dom_build_time'])
        out.append('Time: %.2f sec' % total_time)
        return '\n'.join(out)

    def save_all_lists(self, dir_path):
        """
        Save each list into file in specified diretory.
        """

        for key, items in self.items.items():
            path = os.path.join(dir_path, '%s.txt' % key)
            self.save_list(key, path)

    def inc_count(self, key, display=False, count=1):
        """
        You can call multiply time this method in process of parsing.

        self.inc_count('regurl')
        self.inc_count('captcha')

        and after parsing you can acces to all saved values:

        print 'Total: %(total)s, captcha: %(captcha)s' % spider_obj.counters
        """

        self.counters[key] += count
        if display:
            logger.debug(key)
        return self.counters[key]

