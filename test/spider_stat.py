import six
from grab.spider import Spider, Task
from tempfile import mkstemp
import os
from six import StringIO
import mock
import sys

from test.util import TMP_DIR
from test.util import BaseGrabTestCase


class BasicSpiderTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    """
    def test_save_list(self):
        class TestSpider(Spider):
            pass

        fh, path = mkstemp()
        bot = TestSpider()
        bot.add_item('foo', 'bar')
        bot.add_item('foo2', 'bar2')
        bot.save_list('foo', path)
        self.assertTrue('bar' in open(path).read())
        self.assertFalse('bar2' in open(path).read())
        os.unlink(path)

    def test_save_list_json_value(self):
        class TestSpider(Spider):
            pass

        fh, path = mkstemp()
        bot = TestSpider()
        bot.add_item('foo', {'key': 3})
        bot.save_list('foo', path)
        self.assertTrue('{"key": 3}' in open(path).read())
        os.unlink(path)
    """

    def test_stop_timer_invalid_input(self):
        class TestSpider(Spider):
            pass

        bot = TestSpider()
        self.assertRaises(KeyError, bot.stop_timer, 'zzz')

    def test_counters_and_collections(self):
        from grab.stat import DEFAULT_COUNTER_KEY

        class TestSpider(Spider):
            def prepare(self):
                self.stat.logging_period = 0
                self.stat.inc()

            def task_page(self, grab, task):
                1/0

        bot = TestSpider()
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        self.assertEqual(1, bot.stat.counters[DEFAULT_COUNTER_KEY])
        self.assertEqual(1, len(bot.stat.collections['fatal']))

    def test_render_stats(self):
        class TestSpider(Spider):
            def prepare(self):
                self.stat.logging_period = 0
                self.stat.inc()

            def task_page(self, grab, task):
                pass

        bot = TestSpider()
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        stats = bot.render_stats()
        stats = bot.render_stats(timing=True)
