import six
from grab.spider import Spider, Task
from grab.spider.error import SpiderError, FatalError
import os
import signal
import mock

from test.util import BaseGrabTestCase, build_spider, multiprocess_mode


class BasicSpiderTestCase(BaseGrabTestCase):
    class SimpleSpider(Spider):
        def prepare(self):
            self.foo_count = 1

        def prepare_parser(self):
            self.foo_count = 1

        def task_page(self, grab, task):
            self.foo_count += 1
            if not task.get('last'):
                yield Task('page', url=self.meta['url'], last=True)

        def shutdown(self):
            self.foo_count += 1

    def setUp(self):
        self.server.reset()

    @multiprocess_mode(False)
    def test_spider(self):
        """This test tests that in non-multiprocess-mode changes made
        inside handler applied to main spider instance."""
        bot = build_spider(self.SimpleSpider)
        bot.setup_queue()
        bot.meta['url'] = self.server.get_url()
        bot.add_task(Task('page', self.server.get_url()))
        bot.run()
        self.assertEqual(4, bot.foo_count)

    @multiprocess_mode(True)
    def test_spider(self):
        bot = build_spider(self.SimpleSpider)
        bot.setup_queue()
        bot.meta['url'] = self.server.get_url()
        bot.add_task(Task('page', self.server.get_url()))
        bot.run()
        self.assertEqual(2, bot.foo_count)
