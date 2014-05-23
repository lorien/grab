from unittest import TestCase

from grab import Grab
from grab.spider import Spider, Task, Data
from test.server import SERVER

class MiscTest(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_null_grab_bug(self):
        # Test following bug:
        # Create task and process it
        # In task handler spawn another task with grab instance
        # received in arguments of current task
        class SimpleSpider(Spider):
            def prepare(self):
                self.page_count = 0

            def task_generator(self):
                yield Task('one', url=SERVER.BASE_URL)

            def task_one(self, grab, task):
                self.page_count += 1
                yield Task('two', grab=grab)

            def task_two(self, grab, task):
                self.page_count += 1

        bot = SimpleSpider(thread_number=1)
        bot.run()
        self.assertEqual(2, bot.page_count)
