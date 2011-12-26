# coding: utf-8
from unittest import TestCase
from grab import Grab, DataNotFound, GrabMisuseError
import re

HTML = u"""
<head>
    <title>фыва</title>
    <meta http-equiv="Content-Type" content="text/html; charset=cp1251" />
</head>
<body>
    <div id="bee">
        <div class="wrapper">
            <strong id="bee-strong">пче</strong><em id="bee-em">ла</em>
        </div>
        <script type="text/javascript">
        mozilla = 777;
        </script>
        <style type="text/css">
        body { color: green; }
        </style>
    </div>
    <div id="fly">
        <strong id="fly-strong">му\n</strong><em id="fly-em">ха</em>
    </div>
    <ul id="num">
        <li id="num-1">item #100 2</li>
        <li id="num-2">item #2</li>
    </ul>
""".encode('cp1251')

class TextExtensionTest(TestCase):
    def setUp(self):
        # Create fake grab instance with fake response
        self.g = Grab()
        self.g.fake_response(HTML, charset='cp1251')

    def test_search(self):
        self.assertTrue(self.g.search(u'фыва'.encode('cp1251'), byte=True))
        self.assertTrue(self.g.search(u'фыва'))
        self.assertFalse(self.g.search(u'фыва2'))

    def test_search_usage_errors(self):
        self.assertRaises(GrabMisuseError,
            lambda: self.g.search(u'фыва', byte=True))
        self.assertRaises(GrabMisuseError,
            lambda: self.g.search('фыва'))

    def test_rex(self):
        # Search unicode rex in unicode body - default case
        rex = re.compile(u'(фыва)', re.U)
        self.assertEqual(u'фыва', self.g.rex(rex).group(1))

        # Search non-unicode rex in byte-string body
        rex = re.compile(u'(фыва)'.encode('cp1251'))
        self.assertEqual(u'фыва'.encode('cp1251'), self.g.rex(rex, byte=True).group(1))

        ## Search for non-unicode rex in unicode body shuld fail
        rex = re.compile('(фыва)')
        self.assertRaises(DataNotFound, lambda: self.g.rex(rex))

        ## Search for unicode rex in byte-string body shuld fail
        rex = re.compile(u'фыва', re.U)
        self.assertRaises(DataNotFound, lambda: self.g.rex(rex, byte=True))

        ## Search for unexesting fragment
        rex = re.compile(u'(фыва2)', re.U)
        self.assertRaises(DataNotFound, lambda: self.g.rex(rex))

    def test_assert_substring(self):
        self.g.assert_substring(u'фыва')
        self.g.assert_substring(u'фыва'.encode('cp1251'), byte=True)
        self.assertRaises(DataNotFound,
            lambda: self.g.assert_substring(u'фыва2'))

    def test_assert_substrings(self):
        self.g.assert_substrings((u'фыва',))
        self.g.assert_substrings((u'фывы нет', u'фыва'))
        self.g.assert_substrings((u'фыва'.encode('cp1251'), 'где ты фыва?'), byte=True)
        self.assertRaises(DataNotFound,
            lambda: self.g.assert_substrings((u'фыва, вернись', u'фыва-а-а-а')))

    def test_assert_rex(self):
        self.g.assert_rex(re.compile(u'фыва'))
        self.g.assert_rex(re.compile(u'фыва'.encode('cp1251')), byte=True)
        self.assertRaises(DataNotFound,
            lambda: self.g.assert_rex(re.compile(u'фыва2')))

    #def test_find_number(self):
        #self.assertEqual('2', self.g.find_number('2'))
        #self.assertEqual('2', self.g.find_number('foo 2 4 bar'))
        #self.assertEqual('24', self.g.find_number('foo 2 4 bar', ignore_spaces=True))
        #self.assertEqual('24', self.g.find_number(u'бешеный 2 4 барсук', ignore_spaces=True))
        #self.assertRaises(DataNotFound,
            #lambda: self.g.find_number('foo'))
        #self.assertRaises(DataNotFound,
            #lambda: self.g.find_number(u'фыва'))

    #def test_drop_space(self):
        #self.assertEqual('', self.g.drop_space(' '))
        #self.assertEqual('f', self.g.drop_space(' f '))
        #self.assertEqual('fb', self.g.drop_space(' f b '))
        #self.assertEqual(u'триглаза', self.g.drop_space(u' тр и гла' + '\t' + '\n' + u' за '))
