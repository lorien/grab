import six
from grab.spider import Spider, Task
from tempfile import mkstemp
import os
from six import StringIO
import mock
import sys

from test.util import TMP_DIR
from test.util import BaseGrabTestCase, build_spider


class BasicSpiderTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_stop_timer_invalid_input(self):
        class TestSpider(Spider):
            pass

        bot = build_spider(TestSpider)
        self.assertRaises(KeyError, bot.timer.stop, 'zzz')

    def test_counters_and_collections(self):
        class TestSpider(Spider):
            def prepare(self):
                self.stat.logging_period = 0
                self.stat.inc('foo')

            def task_page_valid(self, grab, task):
                self.stat.inc('foo')

            def task_page_fail(self, grab, task):
                1/0

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page_valid', url=self.server.get_url()))
        bot.add_task(Task('page_fail', url=self.server.get_url()))
        bot.run()
        self.assertEqual(2, bot.stat.counters['foo'])
        self.assertEqual(1, len(bot.stat.collections['fatal']))

    def test_render_stats(self):
        class TestSpider(Spider):
            def prepare(self):
                self.stat.logging_period = 0
                self.stat.inc('foo')

            def task_page(self, grab, task):
                pass

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        stats = bot.render_stats()
        stats = bot.render_stats(timing=True)
