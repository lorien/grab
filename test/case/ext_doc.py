# coding: utf-8
from unittest import TestCase
from grab import Grab, DataNotFound

from test.util import build_grab
from test.server import SERVER

HTML = b"""
<html>
    <body>
        <h1>test</h1>
    </body>
</html>
"""

class DocExtensionTest(TestCase):
    def setUp(self):
        SERVER.reset()

        # Create fake grab instance with fake response
        self.g = build_grab(document_body=HTML)

    def test_extension_in_general(self):
        self.assertTrue(self.g.doc)

    def test_select_method(self):
        self.assertEqual('test', self.g.doc.select('//h1').text())
