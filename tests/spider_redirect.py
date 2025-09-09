from grab import Grab
from grab.spider import Spider, Task
from tests.util import BaseGrabTestCase, build_spider, start_raw_server, stop_raw_server


class BasicSpiderTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_too_many_redirects(self):
        class TestSpider(Spider):
            def task_page(self, unused_grab, unused_task):
                pass

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task("page", url=self.server.get_url()))

        self.server.add_response(
            Response(
                headers=[
                    ("Location", self.server.get_url()),
                ]
            ),
            count=1,
        )
        self.server.add_response(Response(status=302), count=1)
        bot.run()

        self.assertEqual(1, len(bot.stat.collections["network-count-rejected"]))
        self.assertTrue("error:too-many-redirects" in bot.stat.counters)

    def test_redirect_with_invalid_byte(self):
        raw_server = start_raw_server()
        try:
            invalid_url = b"http://\xa0" + self.server.get_url().encode("ascii")

            raw_server.response["data"] = (
                b"HTTP/1.1 301 Moved\r\n" b"Location: %s\r\n" b"\r\nFOO" % invalid_url
            )

            class TestSpider(Spider):
                def task_generator(self):
                    grab = Grab(url=raw_server.get_url())
                    yield Task("page", grab=grab)

                def task_page(self, unused_grab, unused_task):
                    pass

            bot = build_spider(TestSpider)
            bot.run()
            # Different errors depending on combination
            # of network service and transport used
            self.assertEqual(1, len(bot.stat.collections["network-count-rejected"]))
            self.assertTrue(
                bot.stat.counters["error:new-connection-error"] == 5
                or bot.stat.counters["error:grab-could-not-resolve-host-error"] == 5
                or bot.stat.counters["error:couldnt-resolve-host"] == 5
            )
        finally:
            stop_raw_server(raw_server)
