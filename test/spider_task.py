from unittest import TestCase

import grab.spider.base
from grab import Grab
from grab.spider import Spider, Task, Data, SpiderMisuseError
from util import FakeServerThread, BASE_URL, RESPONSE, SLEEP

class TestSpider(TestCase):

    class SimpleSpider(Spider):
        base_url = 'http://google.com'

        def task_baz(self, grab, task):
            return Data('foo', grab.response.body)

        def data_foo(self, item):
            self.SAVED_ITEM = item
           
    def setUp(self):
        FakeServerThread().start()

    def test_task_priority(self):
        #RESPONSE['get'] = 'Hello spider!'
        #SLEEP['get'] = 0
        #sp = self.SimpleSpider()
        #sp.add_task(Task('baz', BASE_URL))
        #sp.run()
        #self.assertEqual('Hello spider!', sp.SAVED_ITEM)

        # Automatic random priority
        grab.spider.base.RANDOM_TASK_PRIORITY_RANGE = (10, 20)
        bot = self.SimpleSpider(priority_mode='random')
        bot.setup_queue()
        task = Task('baz', url='xxx')
        self.assertEqual(task.priority, None)
        bot.add_task(task)
        self.assertTrue(10 <= task.priority <= 20)

        # Automatic constant priority
        grab.spider.base.DEFAULT_TASK_PRIORITY = 33
        bot = self.SimpleSpider(priority_mode='const')
        bot.setup_queue()
        task = Task('baz', url='xxx')
        self.assertEqual(task.priority, None)
        bot.add_task(task)
        self.assertEqual(33, task.priority)

        # Automatic priority does not override explictily setted priority
        grab.spider.base.DEFAULT_TASK_PRIORITY = 33
        bot = self.SimpleSpider(priority_mode='const')
        bot.setup_queue()
        task = Task('baz', url='xxx', priority=1)
        self.assertEqual(1, task.priority)
        bot.add_task(task)
        self.assertEqual(1, task.priority)

        self.assertRaises(SpiderMisuseError,
                          lambda: self.SimpleSpider(priority_mode='foo'))

    def test_task_url(self):
        bot = self.SimpleSpider()
        bot.setup_queue()
        task = Task('baz', url='xxx')
        self.assertEqual('xxx', task.url)
        bot.add_task(task)
        self.assertEqual('http://google.com/xxx', task.url)
        self.assertEqual(None, task.grab_config)

        g = Grab(url='yyy')
        task = Task('baz', grab=g)
        bot.add_task(task)
        self.assertEqual('http://google.com/yyy', task.url)
        self.assertEqual('http://google.com/yyy', task.grab_config['url'])

    def test_task_clone(self):
        bot = self.SimpleSpider()
        bot.setup_queue()

        task = Task('baz', url='xxx')
        bot.add_task(task.clone())

        # Pass grab to clone
        task = Task('baz', url='xxx')
        g = Grab()
        g.setup(url='zzz')
        bot.add_task(task.clone(grab=g))

        # Pass grab_config to clone
        task = Task('baz', url='xxx')
        g = Grab()
        g.setup(url='zzz')
        bot.add_task(task.clone(grab_config=g.config))
