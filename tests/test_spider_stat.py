from test_server import Response

from grab.spider import Spider, Task
from tests.util import BaseTestCase


class BasicSpiderTestCase(BaseTestCase):
    def setUp(self):
        self.server.reset()

    def test_counters_and_collections(self) -> None:
        class TestSpider(Spider):
            def prepare(self):
                self.stat.logging_period = 0
                self.stat.inc("foo")

            def task_page_valid(self, unused_grab, unused_task):
                self.stat.inc("foo")

            def task_page_fail(self, unused_grab, unused_task):
                raise Exception("Shit happens!")

        self.server.add_response(Response(), count=2)
        bot = TestSpider()
        bot.add_task(Task("page_valid", url=self.server.get_url()))
        bot.add_task(Task("page_fail", url=self.server.get_url()))
        bot.run()
        self.assertEqual(2, bot.stat.counters["foo"])
        self.assertEqual(1, len(bot.runtime_events["fatal"]))

    def test_render_stats(self) -> None:
        self.server.add_response(Response())

        class TestSpider(Spider):
            def prepare(self):
                self.stat.logging_period = 0
                self.stat.inc("foo")

            def task_page(self, grab, task):
                pass

        bot = TestSpider()
        bot.add_task(Task("page", url=self.server.get_url()))
        bot.run()
        bot.render_stats()
