import unittest
from unittest import TestCase
import sys
import os.path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from grab import Grab

class GrabTestCase(TestCase):
    def test_input_value(self):
        g = Grab()
        g.response_body = '<input name="foo" value="bar" />';
        self.assertEqual('bar', g.input_value('foo'))
        g.response_body = '<input value="bar" name="foo" />';
        self.assertEqual('bar', g.input_value('foo'))
        g.response_body = "<input value='bar' name='foo' />";
        self.assertEqual('bar', g.input_value('foo'))
        g.response_body = '<input value=bar name=foo />';
        self.assertEqual('bar', g.input_value('foo'))
        g.response_body = '<input name="foo2" value="bar" />';
        self.assertEqual(None, g.input_value('foo'))
        g.response_body = ''
        self.assertEqual(None, g.input_value('foo'))

    def test_user_agent(self):
        g = Grab()
        self.assertTrue(len(g.config['user_agent']) > 1)


if __name__ == '__main__':
    unittest.main()
