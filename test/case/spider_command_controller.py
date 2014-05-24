from unittest import TestCase

from grab import Grab
from grab.spider import Spider, Task, Data
from test.server import SERVER

class MiscTest(TestCase):
    _backend = 'redis'

    def setUp(self):
        SERVER.reset()

    def test_null_grab_bug(self):
        class SimpleSpider(Spider):
            def task_page(self, grab, task):
                pass

        # Build controller to get redis interface
        bot = SimpleSpider()
        iface = bot.controller.add_interface('redis')
        rid = iface.put_command({'name': 'get_stats'})

        bot = SimpleSpider(thread_number=1)
        bot.setup_queue()
        bot.controller.add_interface('redis')
        bot.run()

        self.assertTrue('Threads:' in iface.pop_result(rid)['data'])
