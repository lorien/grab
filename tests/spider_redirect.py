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
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))

        self.server.response['headers'] = [
            ('Location', self.server.get_url()),
        ]
        self.server.response['code'] = 302
        bot.run()

        print('counters', bot.stat.counters)
        print('items', bot.stat.collections)
        self.assertEqual(
            1, len(bot.stat.collections['network-count-rejected'])
        )
        self.assertTrue('error:too-many-redirects' in bot.stat.counters)
