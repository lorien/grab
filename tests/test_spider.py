from __future__ import annotations

from collections.abc import Generator, Iterator
from typing import Any

from test_server import Response

from grab import Document, HttpRequest
from grab.spider import Spider, Task
from grab.spider.errors import FatalError, SpiderError
from grab.util.timeout import Timeout
from tests.util import BaseTestCase


class SimpleSpider(Spider):
    def task_baz(self, doc: Document, _task: Task) -> None:
        self.collect_runtime_event("SAVED_ITEM", doc.unicode_body())


class BasicSpiderTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_spider(self) -> None:
        self.server.add_response(Response(data=b"Hello spider!"))
        bot = SimpleSpider()
        bot.add_task(Task("baz", self.server.get_url()))
        bot.run()
        self.assertEqual("Hello spider!", bot.runtime_events["SAVED_ITEM"][0])

    def test_network_limit(self) -> None:
        class CustomSimpleSpider(SimpleSpider):
            pass
            # def create_grab_instance(self, **kwargs):
            #    return Grab(timeout=Timeout(connect=1, total=1))

        self.server.add_response(Response(data=b"Hello spider!", sleep=1.1))

        bot = CustomSimpleSpider(network_try_limit=1)
        bot.add_task(
            Task(
                "baz",
                HttpRequest(
                    method="GET",
                    url=self.server.get_url(),
                    timeout=Timeout(connect=1, total=1),
                ),
            )
        )
        bot.run()
        self.assertEqual(bot.stat.counters["spider:request-network"], 1)

        bot = CustomSimpleSpider(network_try_limit=2)
        bot.add_task(
            Task(
                "baz",
                HttpRequest(
                    method="GET",
                    url=self.server.get_url(),
                    timeout=Timeout(connect=1, total=1),
                ),
            )
        )
        bot.run()
        self.assertEqual(bot.stat.counters["spider:request-network"], 2)

    def test_task_limit(self) -> None:
        class CustomSimpleSpider(SimpleSpider):
            pass
            # def create_grab_instance(self, **kwargs):
            #    return Grab(timeout=Timeout(connect=1, total=1))

        self.server.add_response(Response(data=b"Hello spider!", sleep=1.1))

        bot = CustomSimpleSpider(network_try_limit=1)
        bot.add_task(
            Task(
                "baz",
                HttpRequest(
                    method="GET",
                    url=self.server.get_url(),
                    timeout=Timeout(connect=1, total=1),
                ),
            )
        )
        bot.run()
        self.assertEqual(bot.stat.counters["spider:task-baz"], 1)

        bot2 = SimpleSpider(task_try_limit=2)
        bot2.add_task(
            Task(
                "baz",
                HttpRequest(
                    method="GET",
                    url=self.server.get_url(),
                    timeout=Timeout(connect=1, total=1),
                ),
                task_try_count=3,
            )
        )
        bot2.run()
        self.assertEqual(bot2.stat.counters.get("spider:request-network", 0), 0)

    def test_task_retry(self) -> None:
        self.server.add_response(Response(status=403))
        self.server.add_response(Response(data=b"xxx"))
        bot = SimpleSpider()
        bot.add_task(Task("baz", self.server.get_url()))
        bot.run()
        self.assertEqual("xxx", bot.runtime_events["SAVED_ITEM"][0])

    def testz_generator(self) -> None:
        number = 13
        server = self.server
        server.add_response(Response(), count=number)

        class TestSpider(Spider):
            def task_generator(self) -> Iterator[Task]:
                for _ in range(number):
                    yield Task("page", url=server.get_url())

            def task_page(self, _doc: Document, _task: Task) -> None:
                self.stat.inc("count")

        bot = TestSpider()
        bot.run()
        self.assertEqual(bot.stat.counters["count"], number)

    def test_handler_result_none(self) -> None:
        class TestSpider(Spider):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, **kwargs)
                self.points: list[int] = []

            def prepare(self) -> None:
                self.points = []

            def task_page(
                self, _doc: Document, _task: Task
            ) -> Generator[None, None, None]:
                yield None

        self.server.add_response(Response(), count=-1)
        bot = TestSpider()
        bot.add_task(Task("page", url=self.server.get_url()))
        bot.run()

    def test_fallback_handler_by_default_name(self) -> None:
        class TestSpider(Spider):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, **kwargs)
                self.points: list[int] = []

            def prepare(self) -> None:
                self.points = []

            def task_page(self, _doc: Document, _task: Task) -> None:
                pass

            def task_page_fallback(self, _task: Task) -> None:
                self.points.append(1)

        self.server.add_response(Response(status=403))

        bot = TestSpider(network_try_limit=1)
        bot.add_task(Task("page", url=self.server.get_url()))
        bot.run()
        self.assertEqual(bot.points, [1])

    def test_fallback_handler_by_fallback_name(self) -> None:
        class TestSpider(Spider):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, **kwargs)
                self.points: list[int] = []

            def prepare(self) -> None:
                self.points = []

            def task_page(self, _doc: Document, task: Task) -> None:
                pass

            def fallback_zz(self, _task: Task) -> None:
                self.points.append(1)

        self.server.add_response(Response(status=403))

        bot = TestSpider(network_try_limit=1)
        bot.add_task(
            Task("page", url=self.server.get_url(), fallback_name="fallback_zz")
        )
        bot.run()
        self.assertEqual(bot.points, [1])

    def test_check_task_limits_invalid_value(self) -> None:
        class TestSpider(Spider):
            def task_page(self, _doc: Document, _task: Task) -> None:
                pass

            def check_task_limits(self, _task: Task) -> tuple[bool, str]:
                return False, "zz"

        bot = TestSpider()
        bot.add_task(
            Task("page", url=self.server.get_url(), fallback_name="fallback_zz")
        )
        self.assertRaises(SpiderError, bot.run)

    def test_handler_result_invalid(self) -> None:
        class TestSpider(Spider):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, **kwargs)
                self.points: list[int] = []

            def prepare(self) -> None:
                self.points = []

            def task_page(
                self, _doc: Document, _task: Task
            ) -> Generator[int, None, None]:
                yield 1

        self.server.add_response(Response(), count=-1)
        bot = TestSpider()
        bot.add_task(Task("page", url=self.server.get_url()))
        self.assertRaises(SpiderError, bot.run)

    def test_task_queue_clear(self) -> None:
        class TestSpider(Spider):
            def task_page(self, _doc: Document, _task: Task) -> None:
                self.stop()

        self.server.add_response(Response(), count=-1)
        bot = TestSpider()
        for _ in range(5):
            bot.add_task(Task("page", url=self.server.get_url()))
        self.assertEqual(5, bot.task_queue.size())
        bot.run()
        self.assertEqual(0, bot.task_queue.size())

    def test_fatal_error(self) -> None:
        class TestSpider(Spider):
            def task_page(self, _doc: Document, _task: Task) -> None:
                raise FatalError

        self.server.add_response(Response(), count=-1)
        bot = TestSpider()
        bot.add_task(Task("page", url=self.server.get_url()))
        self.assertRaises(FatalError, bot.run)
