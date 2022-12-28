from __future__ import annotations

from collections.abc import Generator
from typing import Any

from test_server import Response

from grab import Document, HttpRequest
from grab.spider import Spider, Task
from tests.util import BaseTestCase

# That URLs breaks Grab's URL normalization process
# with error "label empty or too long"
INVALID_URL = (
    "http://13354&altProductId=6423589&productId=6423589"
    "&altProductStoreId=13713&catalogId=10001"
    "&categoryId=28678&productStoreId=13713"
    "http://www.textbooksnow.com/webapp/wcs/stores"
    "/servlet/ProductDisplay?langId=-1&storeId="
)


class SpiderErrorTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_generator_with_invalid_url(self) -> None:
        class SomeSpider(Spider):
            def task_generator(self) -> Generator[Task, None, None]:
                yield Task("page", url=INVALID_URL)

        bot = SomeSpider()
        bot.run()

    def test_redirect_with_invalid_url(self) -> None:

        server = self.server

        class TestSpider(Spider):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, **kwargs)
                self.done_counter = 0

            def task_generator(self) -> Generator[Task, None, None]:
                self.done_counter = 0
                yield Task("page", url=server.get_url())

            def task_page(self, _doc: Document, task: Task) -> None:
                pass

        self.server.add_response(
            Response(
                status=301,
                headers=[("Location", INVALID_URL)],
            )
        )
        bot = TestSpider(network_try_limit=1)
        bot.run()

    def test_stat_error_name_threaded_urllib3(self) -> None:

        server = self.server
        server.add_response(Response(sleep=2))

        class SimpleSpider(Spider):
            def prepare(self) -> None:
                self.network_try_limit = 1

            def task_generator(self) -> Generator[Task, None, None]:
                yield Task(
                    "page", HttpRequest(method="GET", url=server.get_url(), timeout=1)
                )

            def task_page(self, _doc: Document, _task: Task) -> None:
                pass

        bot = SimpleSpider()
        bot.run()
        self.assertTrue("error:ReadTimeoutError" in bot.stat.counters)
