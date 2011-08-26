#!/usr/bin/env python
# coding: utf-8
import unittest
import re

from grab import Grab, GrabMisuseError, DataNotFound

class TextExtensionTest(unittest.TestCase):
    def setUp(self):
        # Create fake grab instance with fake response
        # Note that we use cp1251 encoding to fully test
        # unicode/non-unicode issues
        self.g = Grab()
        self.g.response.body = u'<strong>фыва</strong>'.encode('cp1251')
        self.g.response.charset = 'cp1251'

    def test_search(self):
        self.assertTrue(self.g.search(u'фыва'.encode('cp1251'), byte=True))
        self.assertTrue(self.g.search(u'фыва'))
        self.assertFalse(self.g.search(u'фыва2'))

    def test_search_usage_errors(self):
        self.assertRaises(GrabMisuseError,
            lambda: self.g.search(u'фыва', byte=True))
        self.assertRaises(GrabMisuseError,
            lambda: self.g.search('фыва'))

    def test_search_rex(self):
        # Search unicode rex in unicode body - default case
        rex = re.compile(u'фыва', re.U)
        self.assertEqual(u'фыва', self.g.search_rex(rex).group(0))

        # Search non-unicode rex in byte-string body
        rex = re.compile(u'фыва'.encode('cp1251'))
        self.assertEqual(u'фыва'.encode('cp1251'), self.g.search_rex(rex, byte=True).group(0))

        # Search for non-unicode rex in unicode body shuld fail
        rex = re.compile('фыва')
        self.assertEqual(None, self.g.search_rex(rex))

        # Search for unicode rex in byte-string body shuld fail
        rex = re.compile(u'фыва', re.U)
        self.assertEqual(None, self.g.search_rex(rex, byte=True))

        # Search for unexesting fragment
        rex = re.compile(u'фыва2', re.U)
        self.assertEqual(None, self.g.search_rex(rex))

    def test_assert_substring(self):
        self.g.assert_substring(u'фыва')
        self.g.assert_substring(u'фыва'.encode('cp1251'), byte=True)
        self.assertRaises(DataNotFound,
            lambda: self.g.assert_substring(u'фыва2'))

    def test_assert_rex(self):
        self.g.assert_rex(re.compile(u'фыва'))
        self.g.assert_rex(re.compile(u'фыва'.encode('cp1251')), byte=True)
        self.assertRaises(DataNotFound,
            lambda: self.g.assert_rex(re.compile(u'фыва2')))

    def test_find_number(self):
        self.assertEqual('2', self.g.find_number('2'))
        self.assertEqual('2', self.g.find_number('foo 2 4 bar'))
        self.assertEqual('24', self.g.find_number('foo 2 4 bar', ignore_spaces=True))
        self.assertEqual('24', self.g.find_number(u'бешеный 2 4 барсук', ignore_spaces=True))
        self.assertRaises(DataNotFound,
            lambda: self.g.find_number('foo'))
        self.assertRaises(DataNotFound,
            lambda: self.g.find_number(u'фыва'))

    def test_drop_spaces(self):
        self.assertEqual('', self.g.drop_spaces(' '))
        self.assertEqual('f', self.g.drop_spaces(' f '))
        self.assertEqual('fb', self.g.drop_spaces(' f b '))
        self.assertEqual(u'триглаза', self.g.drop_spaces(u' тр и гла' + '\t' + '\n' + u' за '))


if __name__ == '__main__':
    unittest.main()
