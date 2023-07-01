from __future__ import annotations

from collections.abc import Generator
from typing import Any

from test_server import Response

from grab import Document
from grab.spider import Spider, Task
from tests.util import BaseTestCase


class BasicSpiderTestCase(BaseTestCase):
    class SimpleSpider(Spider):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.foo_count = 1

        # TODO: is it required yet, after createing __init__
        # check all other similar cases
        def prepare(self) -> None:
            self.foo_count = 1

        def task_page(self, _doc: Document, task: Task) -> Generator[Task, None, None]:
            self.foo_count += 1
            if not task.get("last"):
                yield Task("page", url=self.meta["url"], last=True)

        def task_page2(self, _doc: Document, task: Task) -> Generator[Task, None, None]:
            yield task.clone(last=True)

        def shutdown(self) -> None:
            self.foo_count += 1

    def setUp(self) -> None:
        self.server.reset()

    def test_spider_nonmp_changes(self) -> None:
        # This test tests that in non-multiprocess-mode changes made
        # inside handler applied to main spider instance.
        self.server.add_response(Response(), count=-1)
        bot = self.SimpleSpider()
        bot.meta["url"] = self.server.get_url()
        bot.add_task(Task("page", self.server.get_url()))
        bot.run()
        self.assertEqual(4, bot.foo_count)
