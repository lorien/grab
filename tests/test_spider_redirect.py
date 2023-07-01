from __future__ import annotations

from collections.abc import Generator

from test_server import Response

from grab import Document
from grab.spider import Spider, Task
from tests.util import BaseTestCase


class BasicSpiderTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    # def test_too_many_redirects(self):
    #    class TestSpider(Spider):
    #        def task_page(self, unused_grab, unused_task):
    #            pass

    #    bot = TestSpider()
    #    bot.add_task(Task("page", url=self.server.get_url()))

    #    self.server.add_response(
    #        Response(
    #            headers=[("Location", self.server.get_url())],
    #            status=302,
    #        ),
    #        count=-1,
    #    )
    #    bot.run()

    #    self.assertEqual(1, len(bot.runtime_events["network-count-rejected"]))
    #    self.assertTrue("error:GrabTooManyRedirectsError" in bot.stat.counters)

    def test_redirect_with_invalid_byte(self) -> None:
        server = self.server

        def callback() -> bytes:
            invalid_url = b"http://\xa0" + server.get_url().encode("ascii")
            return b"HTTP/1.1 301 Moved\r\nLocation: %s\r\n\r\nFOO" % invalid_url

        self.server.add_response(Response(raw_callback=callback), count=-1)

        class TestSpider(Spider):
            def task_generator(self) -> Generator[Task, None, None]:
                yield Task("page", server.get_url())

            def task_page(self, _doc: Document, _task: Task) -> None:
                pass

        bot = TestSpider()
        bot.run()
        # Different errors depending on combination
        # of network service and transport used
        self.assertEqual(1, len(bot.runtime_events["network-count-rejected"]))
        self.assertTrue(bot.stat.counters["error:LocationParseError"])
