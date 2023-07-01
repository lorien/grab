from test_server import Response

from grab.document import Document
from grab.spider import Spider, Task
from tests.util import BaseTestCase


class BasicSpiderTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_counters_and_collections(self) -> None:
        class TestSpider(Spider):
            def prepare(self) -> None:
                self.stat.logging_interval = 0
                self.stat.inc("foo")

            def task_page_valid(self, _doc: Document, _task: Task) -> None:
                self.stat.inc("foo")

            def task_page_fail(self, _doc: Document, _task: Task) -> None:
                raise RuntimeError("Shit happens!")

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
            def prepare(self) -> None:
                self.stat.logging_interval = 0
                self.stat.inc("foo")

            def task_page(self, _doc: Document, _task: Task) -> None:
                pass

        bot = TestSpider()
        bot.add_task(Task("page", url=self.server.get_url()))
        bot.run()
        bot.render_stats()
