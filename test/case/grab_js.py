# coding: utf-8
from unittest import TestCase
import os

from grab import Grab, GrabMisuseError
from test.util import build_grab, ignore_transport, only_transport
from test.server import SERVER
from grab.extension import register_extensions


class GrabSimpleTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    @only_transport('grab.transport.kit.KitTransport')
    def test_simple_js(self):
        SERVER.RESPONSE['get'] = ''''
            <body>
            <script>
                var num = 22 * 3;
                document.write(num);
            </script>
            </body>
        '''
        g = build_grab()
        g.go(SERVER.BASE_URL)
        self.assertTrue(b'66' in g.response.runtime_body)

    @only_transport('grab.transport.kit.KitTransport')
    def test_js_dom(self):
        SERVER.RESPONSE['get'] = ''''
            <body>
            <script>
                var num = 22 * 3;
                document.write('<span id="foo">' + num + '</span>');
            </script>
            </body>
        '''
        g = build_grab()
        g.go(SERVER.BASE_URL)
        self.assertEqual(g.doc.select('//span[@id="foo"]').text(), '66')
