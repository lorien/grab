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

    def test_slugify_transliteration(self):
        self.assertEqual('fu', slugify('фу'))
        self.assertEqual('fu', slugify('фу#'))
        self.assertEqual('fu-bin', slugify('фу#bin'))
        self.assertEqual('bin', slugify('####bin'))
        self.assertEqual('bin', slugify('####бин'))

    def test_slugify_dot_processing(self):
        self.assertEqual('bi-n', slugify('####би.н'))
        self.assertEqual('bi.n', slugify('####би.н', dot_allowed=True))

    def test_slugify_limit(self):
        self.assertEqual('bi-n', slugify('####би.н'))
        self.assertEqual('bi-n', slugify('####би.н', limit=100))
        self.assertEqual('bi-n', slugify('####би.н', limit=4))
        self.assertEqual('bi-', slugify('####би.н', limit=3))

    def test_slugify_lower(self):
        # by default lower option is True
        self.assertEqual('bi-n', slugify('####БИ.н'))

        self.assertEqual('BI-n', slugify('####БИ.н', lower=False))

        # test also english letters
        self.assertEqual('bi-n', slugify('####bi.н'))
        self.assertEqual('BI-n', slugify('####BI.н', lower=False))

    def test_slugify_default(self):
        self.assertEqual('', slugify('####'))
        self.assertEqual('z', slugify('####', default='z'))
        self.assertEqual(None, slugify('####', default=None))
