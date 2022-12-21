from test_server import Response

from grab import Grab
from grab.spider import Spider, Task
from grab.spider.error import FatalError, SpiderError
from tests.util import BaseGrabTestCase, build_spider


class SimpleSpider(Spider):
    def task_baz(self, grab, unused_task):
        self.collect_runtime_event("SAVED_ITEM", grab.doc.body)


class BasicSpiderTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_spider(self):
        self.server.add_response(Response(data=b"Hello spider!"))
        bot = build_spider(SimpleSpider)
        bot.add_task(Task("baz", self.server.get_url()))
        bot.run()
        self.assertEqual(b"Hello spider!", bot.runtime_events["SAVED_ITEM"][0])

    def test_network_limit(self):
        class CustomSimpleSpider(SimpleSpider):
            def create_grab_instance(self, **kwargs):
                return Grab(connect_timeout=1, timeout=1)

        self.server.add_response(Response(data=b"Hello spider!", sleep=1.1))

        bot = build_spider(CustomSimpleSpider, network_try_limit=1)
        bot.add_task(Task("baz", self.server.get_url()))
        bot.run()
        self.assertEqual(bot.stat.counters["spider:request-network"], 1)

        bot = build_spider(CustomSimpleSpider, network_try_limit=2)
        bot.add_task(Task("baz", self.server.get_url()))
        bot.run()
        self.assertEqual(bot.stat.counters["spider:request-network"], 2)

    def test_task_limit(self):
        class CustomSimpleSpider(SimpleSpider):
            def create_grab_instance(self, **kwargs):
                return Grab(connect_timeout=1, timeout=1)

        self.server.add_response(Response(data=b"Hello spider!", sleep=1.1))

        bot = build_spider(CustomSimpleSpider, network_try_limit=1)
        bot.add_task(Task("baz", self.server.get_url()))
        bot.run()
        self.assertEqual(bot.stat.counters["spider:task-baz"], 1)

        bot2 = build_spider(SimpleSpider, task_try_limit=2)
        bot2.add_task(Task("baz", self.server.get_url(), task_try_count=3))
        bot2.run()
        self.assertEqual(bot2.stat.counters.get("spider:request-network", 0), 0)

    def test_task_retry(self):
        self.server.add_response(Response(status=403))
        self.server.add_response(Response(data=b"xxx"))
        bot = build_spider(SimpleSpider)
        bot.add_task(Task("baz", self.server.get_url()))
        bot.run()
        self.assertEqual(b"xxx", bot.runtime_events["SAVED_ITEM"][0])

    def test_generator(self):
        server = self.server
        server.add_response(Response(), count=13)

        class TestSpider(Spider):
            def task_generator(self):
                for _ in range(13):
                    yield Task("page", url=server.get_url())

            def task_page(self, unused_grab, unused_task):
                self.stat.inc("count")

        bot = build_spider(TestSpider)
        bot.run()
        self.assertEqual(bot.stat.counters["count"], 13)

    def test_handler_result_none(self):
        class TestSpider(Spider):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.points = []

            def prepare(self):
                self.points = []

            def task_page(self, unused_grab, unused_task):
                yield None

        self.server.add_response(Response(), count=-1)
        bot = build_spider(TestSpider)
        bot.add_task(Task("page", url=self.server.get_url()))
        bot.run()

    def test_fallback_handler_by_default_name(self):
        class TestSpider(Spider):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.points = []

            def prepare(self):
                self.points = []

            def task_page(self, grab, task):
                pass

            def task_page_fallback(self, unused_task):
                self.points.append(1)

        self.server.add_response(Response(status=403))

        bot = build_spider(TestSpider, network_try_limit=1)
        bot.add_task(Task("page", url=self.server.get_url()))
        bot.run()
        self.assertEqual(bot.points, [1])

    def test_fallback_handler_by_fallback_name(self):
        class TestSpider(Spider):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.points = []

            def prepare(self):
                self.points = []

            def task_page(self, grab, task):
                pass

            def fallback_zz(self, unused_task):
                self.points.append(1)

        self.server.add_response(Response(status=403))

        bot = build_spider(TestSpider, network_try_limit=1)
        bot.add_task(
            Task("page", url=self.server.get_url(), fallback_name="fallback_zz")
        )
        bot.run()
        self.assertEqual(bot.points, [1])

    def test_check_task_limits_invalid_value(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                pass

            def check_task_limits(self, task):
                return False, "zz"

        bot = build_spider(TestSpider)
        bot.add_task(
            Task("page", url=self.server.get_url(), fallback_name="fallback_zz")
        )
        self.assertRaises(SpiderError, bot.run)

    def test_handler_result_invalid(self):
        class TestSpider(Spider):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.points = []

            def prepare(self):
                self.points = []

            def task_page(self, unused_grab, unused_task):
                yield 1

        self.server.add_response(Response(), count=-1)
        bot = build_spider(TestSpider)
        bot.add_task(Task("page", url=self.server.get_url()))
        self.assertRaises(SpiderError, bot.run)

    def test_task_queue_clear(self):
        class TestSpider(Spider):
            def task_page(self, unused_grab, unused_task):
                self.stop()

        self.server.add_response(Response(), count=-1)
        bot = build_spider(TestSpider)
        for _ in range(5):
            bot.add_task(Task("page", url=self.server.get_url()))
        self.assertEqual(5, bot.task_queue.size())
        bot.run()
        self.assertEqual(0, bot.task_queue.size())

    def test_fatal_error(self):
        class TestSpider(Spider):
            def task_page(self, unused_grab, unused_task):
                raise FatalError

        self.server.add_response(Response(), count=-1)
        bot = build_spider(TestSpider)
        bot.add_task(Task("page", url=self.server.get_url()))
        self.assertRaises(FatalError, bot.run)
