import six
from grab.spider import Spider, Task
from grab.spider.error import SpiderError, FatalError
import os
import signal
import mock
from grab.spider.decorators import integrity

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

        def check_integrity(self, grab):
            pass

        @integrity('check_integrity')
        def task_page2(self, grab, task):
            if True:#not task.get('last'):
                yield task.clone(last=True)

        def shutdown(self):
            self.foo_count += 1

    def setUp(self):
        self.server.reset()

    @multiprocess_mode(False)
    def test_spider_nonmp_changes(self):
        """This test tests that in non-multiprocess-mode changes made
        inside handler applied to main spider instance."""
        bot = build_spider(self.SimpleSpider)
        bot.setup_queue()
        bot.meta['url'] = self.server.get_url()
        bot.add_task(Task('page', self.server.get_url()))
        bot.run()
        self.assertEqual(4, bot.foo_count)

    @multiprocess_mode(True)
    def test_spider_mp_changes(self):
        bot = build_spider(self.SimpleSpider)
        bot.setup_queue()
        bot.meta['url'] = self.server.get_url()
        bot.add_task(Task('page', self.server.get_url()))
        bot.run()
        self.assertEqual(2, bot.foo_count)

    @multiprocess_mode(True)
    def test_integrity_decorator_in_mp_mode(self):
        bot = build_spider(self.SimpleSpider)
        bot.setup_queue()
        bot.add_task(Task('page2', self.server.get_url()))
        bot.run()

    @multiprocess_mode(True)
    def test_requests_per_process(self):
        url = self.server.get_url()

        class TestSpider(Spider):
            def task_generator(self):
                for x in range(3):
                    yield Task('page', url=url)

            def task_page(self, grab, task):
                self.stat.collect('pid', os.getpid())

        bot = TestSpider(mp_mode=True, parser_pool_size=1)
        bot.run()
        self.assertEqual(1, len(set(bot.stat.collections['pid'])))

        bot = TestSpider(mp_mode=True, parser_pool_size=1, parser_requests_per_process=1)
        bot.run()
        self.assertEqual(3, len(set(bot.stat.collections['pid'])))

        bot = TestSpider(mp_mode=True, parser_pool_size=1, parser_requests_per_process=2)
        bot.run()
        self.assertEqual(2, len(set(bot.stat.collections['pid'])))

        bot = TestSpider(mp_mode=True, parser_pool_size=1, parser_requests_per_process=3)
        bot.run()
        self.assertEqual(1, len(set(bot.stat.collections['pid'])))

    '''
    @multiprocess_mode(True)
    def test_task_callback(self):
        """
        This freezes the sipder in MP-mode
        Traceback (most recent call last):
          File "/usr/lib/python2.7/multiprocessing/queues.py", line 266, in _feed
            send(obj)
        PicklingError: Can't pickle <class 'test.spider_multiprocess.FuncWithState'>: attribute lookup test.spider_multiprocess.FuncWithState failed

        """
        class TestSpider(Spider):
            def task_page(self, grab, task):
                pass

        class FuncWithState(object):
            def __call__(self, grab, task):
                pass

        func = FuncWithState()
        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task(url=self.server.get_url(), callback=func))
        bot.run()
    '''
