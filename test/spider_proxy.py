from unittest import TestCase

from grab.spider import Spider, Task, Data
from util import (FakeServerThread, BASE_URL, RESPONSE, SLEEP, FAKE_SERVER_PORT,
                  REQUEST)

PORT1 = FAKE_SERVER_PORT + 1
PORT2 = FAKE_SERVER_PORT + 2
PORT3 = FAKE_SERVER_PORT + 3
PROXY1 = 'localhost:%d' % PORT1
PROXY2 = 'localhost:%d' % PORT2
PROXY3 = 'localhost:%d' % PORT3

class SimpleSpider(Spider):
    def prepare(self):
        self.ports = set()

    def task_baz(self, grab, task):
        self.ports.add(int(grab.response.headers.get('Listen-Port', 0)))

class TestSpider(TestCase):
    def setUp(self):
        FakeServerThread(port=FAKE_SERVER_PORT).start()
        FakeServerThread(port=PORT1).start()
        FakeServerThread(port=PORT2).start()
        FakeServerThread(port=PORT3).start()

    def test_setup_proxylist(self):
        content = '%s\n%s\n%s' % (PROXY1, PROXY2, PROXY3)
        open('/tmp/__proxy.txt', 'w').write(content)

        # Simple test, one task
        bot = SimpleSpider(thread_number=1)
        bot.setup_proxylist('/tmp/__proxy.txt')
        bot.setup_queue()
        bot.add_task(Task('baz', 'http://yandex.ru'))
        bot.run()

        self.assertEqual(REQUEST['headers']['host'], 'yandex.ru')
        self.assertTrue(len(bot.ports) == 1)

        # By default auto_change is True
        bot = SimpleSpider(thread_number=1)
        bot.setup_proxylist('/tmp/__proxy.txt')
        bot.setup_queue()
        for x in xrange(10):
            bot.add_task(Task('baz', 'http://yandex.ru'))
        bot.run()

        self.assertEqual(REQUEST['headers']['host'], 'yandex.ru')
        self.assertTrue(len(bot.ports) > 1)

        # DO the same test with load_proxylist method
        bot = SimpleSpider(thread_number=1)
        bot.load_proxylist('/tmp/__proxy.txt', 'text_file')
        bot.setup_queue()
        for x in xrange(10):
            bot.add_task(Task('baz', 'http://yandex.ru'))
        bot.run()

        self.assertEqual(REQUEST['headers']['host'], 'yandex.ru')
        self.assertTrue(len(bot.ports) > 1)

        # Disable auto_change
        # By default auto_init is True
        bot = SimpleSpider(thread_number=1)
        bot.setup_proxylist('/tmp/__proxy.txt', auto_change=False)
        bot.setup_queue()
        for x in xrange(10):
            bot.add_task(Task('baz', 'http://yandex.ru'))
        bot.run()

        self.assertEqual(REQUEST['headers']['host'], 'yandex.ru')
        self.assertTrue(len(bot.ports) == 1)

        # Disable auto_change
        # Disable auto_init
        # Proxylist will not be used by default
        bot = SimpleSpider(thread_number=1)
        bot.setup_proxylist('/tmp/__proxy.txt', auto_change=False, auto_init=False)
        bot.setup_queue()
        for x in xrange(10):
            bot.add_task(Task('baz', BASE_URL))
        bot.run()

        self.assertEqual(REQUEST['headers'].get('host'),
                         '%s:%s' % ('localhost', FAKE_SERVER_PORT))
        self.assertTrue(len(bot.ports) == 1)
        self.assertEqual(list(bot.ports)[0], FAKE_SERVER_PORT)

    def test_setup_grab(self):
        # Simple test, one task
        bot = SimpleSpider(thread_number=1)
        bot.setup_grab(proxy=PROXY1)
        bot.setup_queue()
        bot.add_task(Task('baz', 'http://yandex.ru'))
        bot.run()

        self.assertEqual(REQUEST['headers']['host'], 'yandex.ru')
        self.assertEqual(bot.ports, set([PORT1]))
        self.assertTrue(len(bot.ports) == 1)

        content = '%s\n%s' % (PROXY1, PROXY2)
        open('/tmp/__proxy.txt', 'w').write(content)

        # If proxy is configured with both methods (setup_grab and load_proxylist)
        # then proxylist has priority
        bot = SimpleSpider(thread_number=1)
        bot.load_proxylist('/tmp/__proxy.txt', 'text_file')
        bot.setup_queue()
        for x in xrange(10):
            bot.add_task(Task('baz', 'http://yandex.ru'))
        bot.setup_grab(proxy=PROXY3)
        bot.run()

        self.assertEqual(REQUEST['headers']['host'], 'yandex.ru')
        self.assertTrue(not PORT3 in bot.ports)
