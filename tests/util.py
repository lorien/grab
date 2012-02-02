from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import os
import shutil

import grab

# The port on which the fake http server listens requests
FAKE_SERVER_PORT = 9876

# Simple URL which could be used in tests
BASE_URL = 'http://localhost:%d' % FAKE_SERVER_PORT

# This global objects is used by Fake HTTP Server
# It return content of HTML variable for any GET request
RESPONSE = {'get': '', 'post': '', 'cookies': None,
            'once_code': None}
RESPONSE_ONCE = {'get': None, 'post': None}
RESPONSE_ONCE_HEADERS = []

# Fake HTTP Server saves request details
# into global REQUEST variable
REQUEST = {'get': None, 'post': None, 'headers': None,
           'path': None}

SLEEP = {'get': 0, 'post': 0}

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TMP_DIR = os.path.join(TEST_DIR, 'tmp')

def prepare_temp_dir():
    if not os.path.exists(TMP_DIR):
        os.mkdir(TMP_DIR)
    else:
        for root, dirs, files in os.walk(TMP_DIR):
            for fname in files:
                os.unlink(os.path.join(root, fname))
            for _dir in dirs:
                shutil.rmtree(os.path.join(root, _dir))
    return TMP_DIR

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

                time.sleep(SLEEP['get'])
                if RESPONSE['once_code']:
                    self.send_response(RESPONSE['once_code'])
                    RESPONSE['once_code'] = None
                else:
                    self.send_response(200)
                if RESPONSE['cookies']:
                    for name, value in RESPONSE['cookies'].items():
                        self.send_header('Set-Cookie', '%s=%s' % (name, value))
                while RESPONSE_ONCE_HEADERS:
                    self.send_header(*RESPONSE_ONCE_HEADERS.pop())
                self.end_headers()
                if RESPONSE_ONCE['get'] is not None:
                    self.wfile.write(RESPONSE_ONCE['get'])
                    RESPONSE_ONCE['get'] = None
                else:
                    self.wfile.write(RESPONSE['get'])
                REQUEST['headers'] = self.headers
                REQUEST['path'] = self.path
                print '<-- (GET)'

            def log_message(*args, **kwargs):
                "Do not log to console"
                pass

            def do_POST(self):
                time.sleep(SLEEP['post'])
                post_size = int(self.headers.getheader('content-length'))
                REQUEST['post'] = self.rfile.read(post_size)
                REQUEST['headers'] = self.headers
                REQUEST['path'] = self.path

                if RESPONSE['once_code']:
                    self.send_response(RESPONSE['once_code'])
                    RESPONSE['once_code'] = None
                else:
                    self.send_response(200)
                while RESPONSE_ONCE_HEADERS:
                    self.send_header(*RESPONSE_ONCE_HEADERS.pop())
                self.end_headers()
                if RESPONSE_ONCE['post'] is not None:
                    self.wfile.write(RESPONSE_ONCE['post'])
                    RESPONSE_ONCE['post'] = None
                else:
                    self.wfile.write(RESPONSE['post'])

        server_address = ('localhost', FAKE_SERVER_PORT)
        try:
            httpd = HTTPServer(server_address, RequestHandlerClass)
            httpd.serve_forever()
        except IOError:
            # Do nothing if server alrady is running
            pass

def ignore_transport(transport):
    """
    If test function is wrapped into this decorator then
    it does not do testing if test is performed for
    specified transport
    """

    def wrapper(func):
        def test_method(*args, **kwargs):
            cls = getattr(grab, transport)
            if grab.Grab == cls:
                return
            else:
                func(*args, **kwargs)
        return test_method
    return wrapper
