# coding: utf-8
from unittest import TestCase
from grab import Grab, DataNotFound

from test.util import (GRAB_TRANSPORT, RESPONSE, BASE_URL,
                       FakeServerThread)

HTML = u"""
<html>
    <body>
        <h1>test</h1>
    </body>
</html>
"""

XML = """
<root>
    <man>
        <age>25</age>
        <weight><![CDATA[30]]></weight>
    </man>
</root>
"""


class DocExtensionTest(TestCase):
    def setUp(self):
        # Create fake grab instance with fake response
        self.g = Grab(HTML, transport=GRAB_TRANSPORT)
        FakeServerThread().start()

    def test_extension_in_general(self):
        self.assertTrue(self.g.doc)
