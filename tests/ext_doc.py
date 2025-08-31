# coding: utf-8
from unittest import TestCase

from tests.util import build_grab

HTML = b"""
<html>
    <body>
        <h1>test</h1>
    </body>
</html>
"""


class DocExtensionTest(TestCase):
    def setUp(self):
        # Create fake grab instance with fake response
        self.grab = build_grab(document_body=HTML)

    def test_extension_in_general(self):
        self.assertTrue(self.grab.doc)

    def test_select_method(self):
        self.assertEqual('test', self.grab.doc.select('//h1').text())
