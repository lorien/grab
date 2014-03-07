# coding: utf-8
from unittest import TestCase

from grab.tools.russian import slugify, parse_ru_month

class ToolsRussianTestCase(TestCase):
    def test_parse_ru_month(self):
        self.assertEqual(1, parse_ru_month(u'Январь'))
        self.assertEqual(1, parse_ru_month(u'Января'))
        self.assertEqual(1, parse_ru_month(u'январь'))
        self.assertEqual(1, parse_ru_month(u'января'))
        self.assertEqual(1, parse_ru_month(u'яНВарЬ'))
        self.assertEqual(12, parse_ru_month(u'деКАБрЯ'))

    def test_slugify(self):
        self.assertEqual('fu', slugify('фу'))
        self.assertEqual('fu', slugify('фу#'))
        self.assertEqual('fu-bin', slugify('фу#bin'))
        self.assertEqual('bin', slugify('####bin'))
        self.assertEqual('bin', slugify('####бин'))
