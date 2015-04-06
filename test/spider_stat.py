import six
from grab.spider import Spider, Task
from tempfile import mkstemp
import os
from six import StringIO
import mock
import sys

from test.util import TMP_DIR
from test.util import BaseGrabTestCase


class BasicSpiderTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_save_list(self):
        class TestSpider(Spider):
            pass

        fh, path = mkstemp()
        bot = TestSpider()
        bot.add_item('foo', 'bar')
        bot.add_item('foo2', 'bar2')
        bot.save_list('foo', path)
        self.assertTrue('bar' in open(path).read())
        self.assertFalse('bar2' in open(path).read())
        os.unlink(path)

    def test_save_list_json_value(self):
        class TestSpider(Spider):
            pass

        fh, path = mkstemp()
        bot = TestSpider()
        bot.add_item('foo', {'key': 3})
        bot.save_list('foo', path)
        self.assertTrue('{"key": 3}' in open(path).read())
        os.unlink(path)

    def test_save_all_lists(self):
        class TestSpider(Spider):
            pass

        bot = TestSpider()
        bot.add_item('foo', 'bar')
        bot.add_item('foo2', 'bar2')
        bot.save_all_lists(TMP_DIR)
        self.assertTrue('bar' in
                        open(os.path.join(TMP_DIR, 'foo.txt')).read())
        self.assertTrue('bar2' in
                        open(os.path.join(TMP_DIR, 'foo2.txt')).read())

    def test_stop_timer_invalid_input(self):
        class TestSpider(Spider):
            pass

        bot = TestSpider()
        self.assertEqual(0, bot.stop_timer('zzz'))
