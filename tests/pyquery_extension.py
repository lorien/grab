# coding: utf-8
from grab import Grab
from tests.util import BaseGrabTestCase

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


class PyqueryExtensionTest(BaseGrabTestCase):
    def setUp(self):
        # Create fake grab instance with fake response
        self.grab = Grab(HTML, charset='cp1251')

    def test_some_things(self):
        from pyquery import PyQuery

        self.assertEqual(self.grab.pyquery('#num-1').text(), u'item #100 2')
        self.assertEqual(self.grab.pyquery('li').filter(
            lambda x: '#2' in PyQuery(x).text()).text(), u'item #2')
