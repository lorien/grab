#!/usr/bin/env python
# coding: utf-8
import unittest
from unittest import TestCase
import re
import threading
import time
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import urllib

import logging
logging.basicConfig(level=logging.DEBUG)

from grab import GrabMisuseError, DataNotFound, UploadContent
from grab import Grab as GrabPycurl, GrabSelenium
from grab.spider import Spider, Task, Data

# The port on which the fake http server listens requests
FAKE_SERVER_PORT = 9876

# Simple URL which could be used in tests
BASE_URL = 'http://localhost:%d' % FAKE_SERVER_PORT

# This global objects is used by Fake HTTP Server
# It return content of HTML variable for any GET request
RESPONSE = {'get': '', 'post': ''}

# Fake HTTP Server saves request details
# into global REQUEST variable
REQUEST = {'get': None, 'post': None, 'headers': None}

class FakeServerThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(FakeServerThread, self).__init__(*args, **kwargs)
        self.daemon = True

    def start(self):
        super(FakeServerThread, self).start()
        time.sleep(0.1)

    def run(self):
        # TODO: reset REQUEST before each get/post request
        class RequestHandlerClass(BaseHTTPRequestHandler):
            def do_GET(self):
                """
                Process GET request.

                Reponse body contains content from ``RESPONSE['get']``
                """

                self.send_response(200)
                self.end_headers()
                self.wfile.write(RESPONSE['get'])
                REQUEST['headers'] = self.headers

            def log_message(*args, **kwargs):
                "Do not log to console"
                pass

            def do_POST(self):
                post_size = int(self.headers.getheader('content-length'))
                REQUEST['post'] = self.rfile.read(post_size)
                REQUEST['headers'] = self.headers
                self.send_response(200)
                self.end_headers()
                self.wfile.write(RESPONSE['post'])

        server_address = ('localhost', FAKE_SERVER_PORT)
        try:
            httpd = HTTPServer(server_address, RequestHandlerClass)
            httpd.serve_forever()
        except IOError:
            # Do nothing if server alrady is running
            pass


class TestGrab(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_basic(self):
        html = 'the cat'

        RESPONSE['get'] = '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8" /></head><body>крокодил</body></html>'
        g = Grab()
        g.setup(xserver_display=0)
        g.go(BASE_URL)
        expected_body = '<HTML><HEAD><META content="text/html; charset=utf-8" http-equiv="Content-Type"/></HEAD><BODY>крокодил</BODY></HTML>'
        self.assertEqual(expected_body, g.response.body)


if __name__ == '__main__':
    Grab = GrabSelenium
    unittest.main()
