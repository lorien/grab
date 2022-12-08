from grab.spider import Spider, Task
from test_server import Response
from tests.util import BaseGrabTestCase, build_spider


class BasicSpiderTestCase(BaseGrabTestCase):
    class SimpleSpider(Spider):
        def prepare(self):
            # pylint: disable=attribute-defined-outside-init
            self.foo_count = 1

        def prepare_parser(self):
            # pylint: disable=attribute-defined-outside-init
            self.foo_count = 1

        def task_page(self, unused_grab, task):
            self.foo_count += 1
            if not task.get("last"):
                yield Task("page", url=self.meta["url"], last=True)

        def task_page2(self, unused_grab, task):
            yield task.clone(last=True)

        def shutdown(self):
            self.foo_count += 1

    def setUp(self):
        self.server.reset()

    def test_spider_nonmp_changes(self):
        # This test tests that in non-multiprocess-mode changes made
        # inside handler applied to main spider instance.
        self.server.add_response(Response(), count=-1)
        bot = build_spider(self.SimpleSpider)
        bot.setup_queue()
        bot.meta["url"] = self.server.get_url()
        bot.add_task(Task("page", self.server.get_url()))
        bot.run()
        self.assertEqual(4, bot.foo_count)
