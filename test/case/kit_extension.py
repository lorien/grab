# coding: utf-8
from unittest import TestCase
from grab import Grab, DataNotFound

from test.server import SERVER

GRAB_TRANSPORT = 'grab.transport.kit.KitTransport'

HTML = u"""
<html>
    <body>
        <h1>test</h1>
    </body>
</html>
"""

class KitExtensionTest(TestCase):
    def setUp(self):
        SERVER.reset()
        SERVER.RESPONSE['get'] = HTML
        self.g = Grab(transport=GRAB_TRANSPORT)
        self.g.go(SERVER.BASE_URL)

    def test_extension_in_general(self):
        self.assertTrue(self.g.kit)

    def test_select_method(self):
        self.assertEqual('test', self.g.kit.select('h1').text())
