from unittest import TestCase
#try:
#    import cPickle as pickle
#except ImportError:
#    import pickle

import grab.spider.base
from grab import Grab
from grab.spider import Spider, Task, Data, SpiderMisuseError, NoTaskHandler

from .tornado_util import SERVER

class SimpleSpider(Spider):
    base_url = 'http://google.com'

    def task_baz(self, grab, task):
        self.SAVED_ITEM = grab.response.body

class TestSpider(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_task_priority(self):
        #SERVER.RESPONSE['get'] = 'Hello spider!'
        #SERVER.SLEEP['get'] = 0
        #sp = SimpleSpider()
        #sp.add_task(Task('baz', SERVER.BASE_URL))
        #sp.run()
        #self.assertEqual('Hello spider!', sp.SAVED_ITEM)

        # Automatic random priority
        grab.spider.base.RANDOM_TASK_PRIORITY_RANGE = (10, 20)
        bot = SimpleSpider(priority_mode='random')
        bot.setup_queue()
        task = Task('baz', url='xxx')
        self.assertEqual(task.priority, None)
        bot.add_task(task)
        self.assertTrue(10 <= task.priority <= 20)

        # Automatic constant priority
        grab.spider.base.DEFAULT_TASK_PRIORITY = 33
        bot = SimpleSpider(priority_mode='const')
        bot.setup_queue()
        task = Task('baz', url='xxx')
        self.assertEqual(task.priority, None)
        bot.add_task(task)
        self.assertEqual(33, task.priority)

        # Automatic priority does not override explictily setted priority
        grab.spider.base.DEFAULT_TASK_PRIORITY = 33
        bot = SimpleSpider(priority_mode='const')
        bot.setup_queue()
        task = Task('baz', url='xxx', priority=1)
        self.assertEqual(1, task.priority)
        bot.add_task(task)
        self.assertEqual(1, task.priority)

        self.assertRaises(SpiderMisuseError,
                          lambda: SimpleSpider(priority_mode='foo'))

    def test_task_url(self):
        bot = SimpleSpider()
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
        bot = SimpleSpider()
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

    def test_task_clone_with_url_param(self):
        task = Task('baz', url='xxx')
        task.clone(url='http://yandex.ru/')


    def test_task_useragent(self):
        bot = SimpleSpider()
        bot.setup_queue()

        g = Grab()
        g.setup(url=SERVER.BASE_URL)
        g.setup(user_agent='Foo')

        task = Task('baz', grab=g)
        bot.add_task(task.clone())
        bot.run()
        self.assertEqual(SERVER.REQUEST['headers']['User-Agent'], 'Foo')

    #def test_task_relative_url_error(self):
        #class SimpleSpider(Spider):
            #def task_one(self, grab, task):
                #yield Task('second', '/')

        #bot = SimpleSpider()
        #bot.setup_queue()
        #bot.add_task(Task('one', SERVER.BASE_URL))
        #bot.run()

    def test_task_nohandler_error(self):
        class TestSpider(Spider):
            pass

        bot = TestSpider()
        bot.setup_queue()
        bot.add_task(Task('page', url=SERVER.BASE_URL))
        self.assertRaises(NoTaskHandler, bot.run)

    def test_task_raw(self):
        class TestSpider(Spider):
            def prepare(self):
                self.codes = []

            def task_page(self, grab, task):
                self.codes.append(grab.response.code)

        SERVER.RESPONSE['code'] = 502

        bot = TestSpider(network_try_limit=1)
        bot.setup_queue()
        bot.add_task(Task('page', url=SERVER.BASE_URL))
        bot.add_task(Task('page', url=SERVER.BASE_URL))
        bot.run()
        self.assertEqual(0, len(bot.codes))

        bot = TestSpider(network_try_limit=1)
        bot.setup_queue()
        bot.add_task(Task('page', url=SERVER.BASE_URL, raw=True))
        bot.add_task(Task('page', url=SERVER.BASE_URL, raw=True))
        bot.run()
        self.assertEqual(2, len(bot.codes))

    def test_task_callback(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                self.meta['tokens'].append('0_handler')

        class FuncWithState(object):
            def __init__(self, tokens):
                self.tokens = tokens

            def __call__(self, grab, task):
                self.tokens.append('1_func')

        tokens = []
        func = FuncWithState(tokens)

        bot = TestSpider()
        bot.meta['tokens'] = tokens
        bot.setup_queue()
        # classic handler
        bot.add_task(Task('page', url=SERVER.BASE_URL))
        # callback option overried classic handler
        bot.add_task(Task('page', url=SERVER.BASE_URL, callback=func))
        # callback and null task name
        bot.add_task(Task(name=None, url=SERVER.BASE_URL, callback=func))
        # callback and default task name
        bot.add_task(Task(url=SERVER.BASE_URL, callback=func))
        bot.run()
        self.assertEqual(['0_handler', '1_func', '1_func', '1_func'],
                         sorted(tokens))


    #def test_task_callback_serialization(self):
        # 8-(
        # FIX: pickling the spider instance completely does not work
        # 8-(

        #class FuncWithState(object):
            #def __init__(self, tokens):
                #self.tokens = tokens

            #def __call__(self, grab, task):
                #self.tokens.append('func')

        #tokens = []
        #func = FuncWithState(tokens)

        #bot = SimpleSpider()
        #bot.setup_queue()
        ##bot.add_task(Task(url=SERVER.BASE_URL, callback=func))

        #dump = pickle.dumps(bot)
        #bot2 = pickle.loads(dump)

        #bot.run()
        #self.assertEqual(['func'], tokens)

    def test_task_fallback(self):
        class TestSpider(Spider):
            def prepare(self):
                self.tokens = []

            def task_page(self, grab, task):
                self.tokens.append('task')

            def task_page_fallback(self, task):
                self.tokens.append('fallback')

        SERVER.RESPONSE['code'] = 403
        bot = TestSpider(network_try_limit=2)
        bot.setup_queue()
        bot.add_task(Task('page', url=SERVER.BASE_URL))
        bot.run()
        self.assertEqual(bot.tokens, ['fallback'])

    def test_task_fallback_yields_new_task(self):
        class TestSpider(Spider):
            def prepare(self):
                self.tokens = []

            def task_page(self, grab, task):
                self.tokens.append('task')
                SERVER.RESPONSE['code'] = 403
                yield Task('page2', url=SERVER.BASE_URL)

            def task_page_fallback(self, task):
                self.tokens.append('fallback')
                SERVER.RESPONSE['code'] = 200
                self.add_task(Task('page', url=SERVER.BASE_URL))

            def task_page2(self, grab, task):
                pass

            def task_page2_fallback(self, task):
                self.tokens.append('fallback2')

        SERVER.RESPONSE['code'] = 403
        bot = TestSpider(network_try_limit=2)
        bot.setup_queue()
        bot.add_task(Task('page', url=SERVER.BASE_URL))
        bot.run()
        self.assertEqual(bot.tokens, ['fallback', 'task', 'fallback2'])

    def test_task_url_and_grab_options(self):
        class TestSpider(Spider):
            def setup(self):
                self.done = False

            def task_page(self, grab, task):
                self.done = True

        bot = TestSpider()
        bot.setup_queue()
        g = Grab()
        g.setup(url=SERVER.BASE_URL)
        self.assertRaises(SpiderMisuseError, 
            lambda: bot.add_task(Task('page', grab=g, url=SERVER.BASE_URL)))
