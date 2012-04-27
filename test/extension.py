from __future__ import absolute_import
from grab.extension import ExtensionManager
from unittest import TestCase

GLOBAL = {}

class ExtensionA(object):
    def extra_foo(self):
        GLOBAL['items'].append('a')

class ExtensionB(object):
    def extra_foo(self):
        GLOBAL['items'].append('b')

class Worker(ExtensionA,  ExtensionB):
    __metaclass__ = ExtensionManager

    extension_points = ('foo',)

    def do_something(self):
        GLOBAL['items'].append('c')
        self.trigger_extensions('foo')


class ExtensionTestCase(TestCase):
    def setUp(self):
        GLOBAL['items'] = []

    def test_extensions(self):
        worker = Worker()
        worker.do_something()
        self.assertEqual(set(GLOBAL['items']), set(['a', 'b', 'c']))
