from pprint import pprint  # pylint: disable=unused-import

from test_server import Response

from grab import Grab
from grab.spider import Spider, Task
from tests.util import BaseGrabTestCase, build_spider


class BasicSpiderTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_too_many_redirects(self):
        class TestSpider(Spider):
            def task_page(self, unused_grab, unused_task):
                pass

        bot = build_spider(TestSpider)
        bot.add_task(Task("page", url=self.server.get_url()))

        self.server.add_response(
            Response(
                headers=[("Location", self.server.get_url())],
                status=302,
            ),
            count=-1,
        )
        bot.run()

        self.assertEqual(1, len(bot.runtime_events["network-count-rejected"]))
        self.assertTrue("error:GrabTooManyRedirectsError" in bot.stat.counters)

    def test_redirect_with_invalid_byte(self):
        server = self.server

        def callback():
            invalid_url = b"http://\xa0" + server.get_url().encode("ascii")
            return (
                b"HTTP/1.1 301 Moved\r\n" b"Location: %s\r\n" b"\r\nFOO" % invalid_url
            )

        self.server.add_response(Response(raw_callback=callback), count=-1)

        class TestSpider(Spider):
            def task_generator(self):
                grab = Grab(url=server.get_url())
                yield Task("page", grab=grab)

            def task_page(self, unused_grab, unused_task):
                pass

        bot = build_spider(TestSpider)
        bot.run()
        # Different errors depending on combination
        # of network service and transport used
        self.assertEqual(1, len(bot.runtime_events["network-count-rejected"]))
        self.assertTrue(
            # bot.stat.counters["error:new-connection-error"] == 5
            bot.stat.counters["error:LocationParseError"]
            # or bot.stat.counters["error:grab-could-not-resolve-host-error"] == 5
            # or bot.stat.counters["error:couldnt-resolve-host"] == 5
        )
