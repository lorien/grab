# coding: utf-8
from grab import DataNotFound, GrabMisuseError
import six

from tests.util import build_grab
from tests.util import BaseGrabTestCase

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


class TextExtensionTest(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

        # Create fake grab instance with fake response
        self.grab = build_grab()
        self.grab.setup_document(HTML, charset='cp1251')

    def test_search(self):
        self.assertTrue(self.grab.doc.text_search(u'фыва'.encode('cp1251'),
                                                  byte=True))
        self.assertTrue(self.grab.doc.text_search(u'фыва'))
        self.assertFalse(self.grab.doc.text_search(u'фыва2'))

    def test_search_usage_errors(self):
        with self.assertRaises(GrabMisuseError):
            self.grab.doc.text_search(u'фыва', byte=True)
        anchor = 'фыва'
        # py3 hack
        if six.PY3:
            anchor = anchor.encode('utf-8')
        self.assertRaises(GrabMisuseError, self.grab.doc.text_search, anchor)

    def test_assert_substring(self):
        self.grab.doc.text_assert(u'фыва')
        self.grab.doc.text_assert(u'фыва'.encode('cp1251'), byte=True)
        self.assertRaises(DataNotFound, self.grab.doc.text_assert, u'фыва2')

    def test_assert_substrings(self):
        self.grab.doc.text_assert_any((u'фыва',))
        self.grab.doc.text_assert_any((u'фывы нет', u'фыва'))
        self.grab.doc.text_assert_any((u'фыва'.encode('cp1251'),
                                       'где ты фыва?'),
                                      byte=True)
        self.assertRaises(DataNotFound, self.grab.doc.text_assert_any,
                          (u'фыва, вернись', u'фыва-а-а-а'))
