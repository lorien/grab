from test_server import Response

from grab.spider import Spider, Task
from tests.util import BaseTestCase


class MiscTest(BaseTestCase):
    def setUp(self):
        self.server.reset()

    def test_null_grab_bug(self) -> None:
        # Test following bug:
        # Create task and process it
        # In task handler spawn another task with grab instance
        # received in arguments of current task
        server = self.server
        server.add_response(Response(), count=2)

        class SimpleSpider(Spider):
            def task_generator(self):
                yield Task("one", url=server.get_url())

            def task_one(self, _grab, task):
                self.stat.inc("page_count")
                yield Task("two", task.request)

            def task_two(self, unused_grab, unused_task):
                self.stat.inc("page_count")

        bot = SimpleSpider(thread_number=1)
        bot.run()
        self.assertEqual(2, bot.stat.counters["page_count"])
