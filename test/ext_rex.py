# coding: utf-8
import re
from weblib.error import DataNotFound
import six

from test.util import build_grab
from test.util import BaseGrabTestCase

HTML = u"""
<head>
    <title>фыва</title>
    <meta http-equiv="Content-Type" content="text/html; charset=cp1251" />
</head>
<body>
    <div id="bee">
        <div class="wrapper">
            # russian LA
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
        # russian XA
        <strong id="fly-strong">му\n</strong><em id="fly-em">ха</em>
    </div>
    <ul id="num">
        <li id="num-1">item #100 2</li>
        <li id="num-2">item #2</li>
    </ul>
""".encode('cp1251')


class ExtensionRexTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

        # Create fake grab instance with fake response
        self.g = build_grab()
        self.g.fake_response(HTML, charset='cp1251')

    def test_rex(self):
        # Search unicode rex in unicode body - default case
        rex = re.compile(u'(фыва)', re.U)
        self.assertEqual(u'фыва', self.g.rex(rex).group(1))

        # Search non-unicode rex in byte-string body
        rex = re.compile(u'(фыва)'.encode('cp1251'))
        self.assertEqual(u'фыва'.encode('cp1251'),
                         self.g.rex(rex, byte=True).group(1))

        # # Search for non-unicode rex in unicode body should fail
        pattern = '(фыва)'
        # py3 hack
        if six.PY3:
            pattern = pattern.encode('utf-8')
        rex = re.compile(pattern)
        self.assertRaises(DataNotFound, lambda: self.g.rex(rex))

        # # Search for unicode rex in byte-string body shuld fail
        rex = re.compile(u'фыва', re.U)
        self.assertRaises(DataNotFound, lambda: self.g.rex(rex, byte=True))

        # # Search for unexesting fragment
        rex = re.compile(u'(фыва2)', re.U)
        self.assertRaises(DataNotFound, lambda: self.g.rex(rex))

    def test_assert_rex(self):
        self.g.assert_rex(re.compile(u'фыва'))
        self.g.assert_rex(re.compile(u'фыва'.encode('cp1251')), byte=True)

    def test_assert_rex_text(self):
        self.assertEqual(u'ха', self.g.rex_text('<em id="fly-em">([^<]+)'))
