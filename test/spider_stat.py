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

    """
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
    """

    def test_stop_timer_invalid_input(self):
        class TestSpider(Spider):
            pass

        bot = TestSpider()
        self.assertRaises(KeyError, bot.stop_timer, 'zzz')
