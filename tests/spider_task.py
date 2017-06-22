from weblib.error import ResponseNotValid

from tests.util import BaseGrabTestCase, build_grab, build_spider
from grab import Grab
from grab.spider import base
from grab.spider import Spider, Task, SpiderMisuseError, NoTaskHandler
from grab.spider.error import SpiderError


class SimpleSpider(Spider):
    def task_baz(self, grab, unused_task):
        pass


class TestSpiderTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_task_priority(self):
        # Automatic random priority
        base.RANDOM_TASK_PRIORITY_RANGE = (10, 20)
        bot = build_spider(SimpleSpider, priority_mode='random')
        bot.setup_queue()
        task = Task('baz', url='http://xxx.com')
        self.assertEqual(task.priority, None)
        bot.add_task(task)
        self.assertTrue(10 <= task.priority <= 20)

        # Automatic constant priority
        base.DEFAULT_TASK_PRIORITY = 33
        bot = build_spider(SimpleSpider, priority_mode='const')
        bot.setup_queue()
        task = Task('baz', url='http://xxx.com')
        self.assertEqual(task.priority, None)
        bot.add_task(task)
        self.assertEqual(33, task.priority)

        # Automatic priority does not override explictily setted priority
        base.DEFAULT_TASK_PRIORITY = 33
        bot = build_spider(SimpleSpider, priority_mode='const')
        bot.setup_queue()
        task = Task('baz', url='http://xxx.com', priority=1)
        self.assertEqual(1, task.priority)
        bot.add_task(task)
        self.assertEqual(1, task.priority)

        self.assertRaises(SpiderMisuseError,
                          lambda: SimpleSpider(priority_mode='foo'))

    def test_task_url(self):
        bot = build_spider(SimpleSpider, )
        bot.setup_queue()
        task = Task('baz', url='http://xxx.com')
        self.assertEqual('http://xxx.com', task.url)
        bot.add_task(task)
        self.assertEqual('http://xxx.com', task.url)
        self.assertEqual(None, task.grab_config)

        grab = Grab(url='http://yyy.com')
        task = Task('baz', grab=grab)
        bot.add_task(task)
        self.assertEqual('http://yyy.com', task.url)
        self.assertEqual('http://yyy.com', task.grab_config['url'])

    def test_task_clone(self):
        bot = build_spider(SimpleSpider, )
        bot.setup_queue()

        task = Task('baz', url='http://xxx.com')
        bot.add_task(task.clone())

        # Pass grab to clone
        task = Task('baz', url='http://xxx.com')
        grab = Grab()
        grab.setup(url='zzz')
        bot.add_task(task.clone(grab=grab))

        # Pass grab_config to clone
        task = Task('baz', url='http://xxx.com')
        grab = Grab()
        grab.setup(url='zzz')
        bot.add_task(task.clone(grab_config=grab.config))

    def test_task_clone_with_url_param(self):
        task = Task('baz', url='http://example.com/path')
        task2 = task.clone(url='http://example.com/new')
        self.assertEqual(task2.name, 'baz')
        self.assertEqual(task2.url, 'http://example.com/new')

    def test_task_useragent(self):
        bot = build_spider(SimpleSpider, )
        bot.setup_queue()

        grab = Grab()
        grab.setup(url=self.server.get_url())
        grab.setup(user_agent='Foo')

        task = Task('baz', grab=grab)
        bot.add_task(task.clone())
        bot.run()
        self.assertEqual(self.server.request['headers']['User-Agent'], 'Foo')

    def test_task_nohandler_error(self):
        class TestSpider(Spider):
            pass

        bot = build_spider(TestSpider, )
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        self.assertRaises(NoTaskHandler, bot.run)

    def test_task_raw(self):
        class TestSpider(Spider):
            def task_page(self, grab, unused_task):
                self.stat.collect('codes', grab.doc.code)

        self.server.response['code'] = 502

        bot = build_spider(TestSpider, network_try_limit=1)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        self.assertEqual(0, len(bot.stat.collections['codes']))

        bot = build_spider(TestSpider, network_try_limit=1)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url(), raw=True))
        bot.add_task(Task('page', url=self.server.get_url(), raw=True))
        bot.run()
        self.assertEqual(2, len(bot.stat.collections['codes']))

    def test_task_callback(self):
        class TestSpider(Spider):
            def task_page(self, unused_grab, unused_task):
                self.meta['tokens'].append('0_handler')

        class FuncWithState(object):
            def __init__(self, tokens):
                self.tokens = tokens

            def __call__(self, grab, task):
                self.tokens.append('1_func')

        tokens = []
        func = FuncWithState(tokens)

        bot = build_spider(TestSpider, )
        bot.meta['tokens'] = tokens
        bot.setup_queue()
        # classic handler
        bot.add_task(Task('page', url=self.server.get_url()))
        # callback option overried classic handler
        bot.add_task(Task('page', url=self.server.get_url(), callback=func))
        # callback and null task name
        bot.add_task(Task(name=None, url=self.server.get_url(), callback=func))
        # callback and default task name
        bot.add_task(Task(url=self.server.get_url(), callback=func))
        bot.run()
        self.assertEqual(['0_handler', '1_func', '1_func', '1_func'],
                         sorted(tokens))

    def test_task_url_and_grab_options(self):
        class TestSpider(Spider):
            def setup(self):
                # pylint: disable=attribute-defined-outside-init
                self.done = False

            def task_page(self, unused_grab, unused_task):
                # pylint: disable=attribute-defined-outside-init
                self.done = True

        bot = build_spider(TestSpider, )
        bot.setup_queue()
        grab = Grab()
        grab.setup(url=self.server.get_url())
        self.assertRaises(SpiderMisuseError, Task,
                          'page', grab=grab, url=self.server.get_url())

    def test_task_invalid_name(self):
        self.assertRaises(SpiderMisuseError, Task,
                          'generator', url='http://example.com')

    def test_task_constructor_invalid_args(self):
        # no url, no grab, no grab_config
        self.assertRaises(SpiderMisuseError, Task, 'foo')
        # both url and grab_config
        self.assertRaises(SpiderMisuseError, Task, 'foo',
                          url=1, grab_config=1)
        # both grab and grab_config
        self.assertRaises(SpiderMisuseError, Task, 'foo',
                          grab=1, grab_config=1)

    def test_task_clone_invalid_args(self):
        task = Task('foo', url='http://example.com')
        # both url and grab
        self.assertRaises(SpiderMisuseError, task.clone,
                          url=1, grab=1)
        # both url and grab_config
        self.assertRaises(SpiderMisuseError, task.clone,
                          url=1, grab_config=1)
        # both grab_config and grab
        self.assertRaises(SpiderMisuseError, task.clone,
                          grab=1, grab_config=1)

    def test_task_clone_grab_config_and_url(self):
        grab = build_grab()
        grab.setup(url='http://foo.com/')
        task = Task('foo', grab=grab)
        task2 = task.clone(url='http://bar.com/')
        self.assertEqual(task2.url, 'http://bar.com/')
        self.assertEqual(task2.grab_config['url'], 'http://bar.com/')

    def test_task_clone_kwargs(self):
        grab = build_grab()
        grab.setup(url='http://foo.com/')
        task = Task('foo', grab=grab, foo=1)
        task2 = task.clone(foo=2)
        self.assertEqual(2, task2.foo) # pylint: disable=no-member

    def test_task_comparison(self):
        task1 = Task('foo', url='http://foo.com/', priority=1)
        task2 = Task('foo', url='http://foo.com/', priority=2)
        task3 = Task('foo', url='http://foo.com/')
        # If both tasks have priorities then task are
        # compared by their priorities
        self.assertTrue(task1 < task2)
        # If any of compared tasks does not have priority
        # than tasks are equal
        self.assertTrue(task1 == task3)
        self.assertTrue(task3 == task3)

    def test_task_get_fallback_handler(self):
        class TestSpider(Spider):
            def do_smth(self, task):
                pass

            def task_bar_fallback(self, task):
                pass

        task1 = Task('foo', url='http://foo.com/', fallback_name='do_smth')
        task2 = Task('bar', url='http://foo.com/')
        task3 = Task(url='http://foo.com/')

        bot = build_spider(TestSpider, )

        self.assertEqual(task1.get_fallback_handler(bot), bot.do_smth)
        self.assertEqual(task2.get_fallback_handler(bot),
                         bot.task_bar_fallback)
        self.assertEqual(task3.get_fallback_handler(bot), None)

    def test_update_grab_instance(self):
        class TestSpider(Spider):
            def update_grab_instance(self, grab):
                grab.setup(timeout=77)

            def task_generator(self):
                yield Task('page', url=self.meta['server'].get_url())
                yield Task('page', grab=Grab(url=self.meta['server'].get_url(),
                                             timeout=1))

            def task_page(self, grab, unused_task):
                self.stat.collect('points', grab.config['timeout'])

        bot = build_spider(TestSpider, meta={'server': self.server})
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.add_task(Task('page', grab=Grab(url=self.server.get_url(),
                                            timeout=1)))
        bot.run()
        self.assertEqual(set([77]), set(bot.stat.collections['points']))

    def test_create_grab_instance(self):
        class TestSpider(Spider):
            def create_grab_instance(self, **kwargs):
                grab = super(TestSpider, self).create_grab_instance(**kwargs)
                grab.setup(timeout=77)
                return grab

            def task_generator(self):
                yield Task('page', url=self.meta['server'].get_url())
                yield Task('page', grab=Grab(url=self.meta['server'].get_url(),
                                             timeout=76))

            def task_page(self, grab, unused_task):
                self.stat.collect('points', grab.config['timeout'])

        bot = build_spider(TestSpider, meta={'server': self.server})
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.add_task(Task('page', grab=Grab(url=self.server.get_url(),
                                            timeout=75)))
        bot.run()
        self.assertEqual(set([77, 76, 75]),
                         set(bot.stat.collections['points']))

    def test_add_task_invalid_url_no_error(self):
        class TestSpider(Spider):
            pass

        bot = build_spider(TestSpider, )
        bot.setup_queue()
        bot.add_task(Task('page', url='zz://zz'))
        self.assertEqual(0, bot.task_queue.size())
        bot.add_task(Task('page', url='zz://zz'), raise_error=False)
        self.assertEqual(0, bot.task_queue.size())
        bot.add_task(Task('page', url='http://example.com/'))
        self.assertEqual(1, bot.task_queue.size())

    def test_add_task_invalid_url_raise_error(self):
        class TestSpider(Spider):
            pass

        bot = build_spider(TestSpider, )
        bot.setup_queue()
        self.assertRaises(SpiderError, bot.add_task,
                          Task('page', url='zz://zz'), raise_error=True)
        self.assertEqual(0, bot.task_queue.size())
        bot.add_task(Task('page', url='http://example.com/'))
        self.assertEqual(1, bot.task_queue.size())

    def test_worker_restored(self):
        class TestSpider(Spider):
            def task_page(self, unused_grab, unused_task):
                pass

        bot = build_spider(
            TestSpider,
            parser_requests_per_process=2,
        )
        bot.setup_queue()
        for _ in range(5):
            bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        self.assertTrue(bot.stat.counters['parser:worker-restarted'] == 2)

    def test_task_clone_post_request(self):
        class TestSpider(Spider):
            def task_foo(self, unused_grab, task):
                if not task.get('fin'):
                    yield task.clone(fin=True)

        bot = build_spider(TestSpider)
        bot.setup_queue()

        grab = Grab()
        grab.setup(url=self.server.get_url(), post={'x': 'y'})
        task = Task('foo', grab=grab)
        bot.add_task(task)
        bot.run()
        self.assertEqual('POST', self.server.request['method'])

    def test_response_not_valid(self):
        class SomeSimpleSpider(Spider):
            def task_page(self, unused_grab, unused_task):
                self.stat.inc('xxx')
                raise ResponseNotValid

        bot = build_spider(SomeSimpleSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        self.assertEqual(bot.task_try_limit, bot.stat.counters['xxx'])

    def test_task_clone_without_modification(self):
        class TestSpider(Spider):
            def task_page(self, grab, unused_task):
                grab2 = grab.clone()
                yield Task('page2', grab=grab2)

            def task_page2(self, grab, task):
                pass

        bot = build_spider(TestSpider)
        bot.setup_queue()
        task = Task('page', url=self.server.get_url())
        bot.add_task(task)
        bot.run()
        self.assertEqual(1, bot.stat.counters['spider:task-page'])
        self.assertEqual(1, bot.stat.counters['spider:task-page2'])
