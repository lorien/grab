# coding: utf-8
from unittest import TestCase
from grab import Grab, DataNotFound
from grab.tools.text import find_number, drop_space, normalize_space

class TextExtensionTest(TestCase):

    def test_find_number(self):
        self.assertEqual('2', find_number('2'))
        self.assertEqual('2', find_number('foo 2 4 bar'))
        self.assertEqual('24', find_number('foo 2 4 bar', ignore_spaces=True))
        self.assertEqual('24', find_number(u'бешеный 2 4 барсук', ignore_spaces=True))
        self.assertRaises(DataNotFound,
            lambda: find_number('foo'))
        self.assertRaises(DataNotFound,
            lambda: find_number(u'фыва'))

    def test_drop_space(self):
        self.assertEqual('', drop_space(' '))
        self.assertEqual('f', drop_space(' f '))
        self.assertEqual('fb', drop_space(' f b '))
        self.assertEqual(u'триглаза', drop_space(u' тр и гла' + '\t' + '\n' + u' за '))
        
    def test_normalize_space(self):
        self.assertEqual('', normalize_space(' '))
        self.assertEqual('f', normalize_space(' f '))
        self.assertEqual('f b', normalize_space(' f b '))
        self.assertEqual(u'тр и гла за', normalize_space(u' тр и гла' + '\t' + '\n' + u' за '))
        self.assertEqual(u'тр_и_гла_за', normalize_space(u' тр и гла' + '\t' + '\n' + u' за ', replace='_'))
        self.assertEqual(u'трABCиABCглаABCза', normalize_space(u' тр и гла' + '\t' + '\n' + u' за ', replace='ABC'))
