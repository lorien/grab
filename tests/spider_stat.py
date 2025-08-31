from grab.spider import Spider, Task

from tests.util import BaseGrabTestCase, build_spider


class BasicSpiderTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    #def test_stop_timer_invalid_input(self):
    #    class TestSpider(Spider):
    #        pass

    #    bot = build_spider(TestSpider)
    #    self.assertRaises(KeyError, bot.timer.stop, 'zzz')

    def test_counters_and_collections(self):
        class TestSpider(Spider):
            def prepare(self):
                self.stat.logging_period = 0
                self.stat.inc('foo')

            def task_page_valid(self, unused_grab, unused_task):
                self.stat.inc('foo')

            def task_page_fail(self, unused_grab, unused_task):
                raise Exception('Shit happens!')

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page_valid', url=self.server.get_url()))
        bot.add_task(Task('page_fail', url=self.server.get_url()))
        bot.run()
        self.assertEqual(2, bot.stat.counters['foo'])
        self.assertEqual(1, len(bot.stat.collections['fatal']))

    def test_render_stats(self):
        class TestSpider(Spider):
            def prepare(self):
                self.stat.logging_period = 0
                self.stat.inc('foo')

            def task_page(self, grab, task):
                pass

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        bot.render_stats()
