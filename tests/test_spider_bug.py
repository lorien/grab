from unittest import TestCase
import pymongo

from grab.spider import Spider, Task
from util import FakeServerThread, BASE_URL, RESPONSE, SLEEP

db = pymongo.Connection()['spider_test']

class SimpleSpider(Spider):
    def task_foo(self, grab, task):
        grab.setup(url=BASE_URL)
        yield Task('bar', grab=grab)

    def task_bar(self, grab, task):
        pass


class TestSpider(TestCase):
    """
    Test the bug: when settings new task with grab object from
    previous requiest, then
    exception is raised if requested url is cached.
    """

    def setUp(self):
        FakeServerThread().start()

    def test_bug(self):
        db.cache.remove({})
        bot = SimpleSpider(
            use_cache=True,
            cache_db='spider_test',
        )
        bot.add_task(Task('foo', BASE_URL))
        bot.run()
