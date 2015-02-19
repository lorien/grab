from grab.spider import Spider, Task
from test.util import BaseGrabTestCase


class MiscTest(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_null_grab_bug(self):
        # Test following bug:
        # Create task and process it
        # In task handler spawn another task with grab instance
        # received in arguments of current task
        server = self.server

        class SimpleSpider(Spider):
            def prepare(self):
                self.page_count = 0

            def task_generator(self):
                yield Task('one', url=server.get_url())

            def task_one(self, grab, task):
                self.page_count += 1
                yield Task('two', grab=grab)

            def task_two(self, grab, task):
                self.page_count += 1

        bot = SimpleSpider(thread_number=1)
        bot.run()
        self.assertEqual(2, bot.page_count)
