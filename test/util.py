from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import os
import shutil
import tempfile

import grab

# The port on which the fake http server listens requests
FAKE_SERVER_PORT = 9876

# Simple URL which could be used in tests
BASE_URL = 'http://localhost:%d' % FAKE_SERVER_PORT

# This global objects is used by Fake HTTP Server
# It return content of HTML variable for any GET request
RESPONSE = {}
RESPONSE_ONCE = {}
RESPONSE_ONCE_HEADERS = []

# Fake HTTP Server saves request details
# into global REQUEST variable
REQUEST = {'get': None, 'post': None, 'headers': None,
           'path': None}

SLEEP = {'get': 0, 'post': 0}

TEST_DIR = os.path.dirname(os.path.realpath(__file__))

# Global variable which is used in all tests to build
# Grab instance with specific transport layer
GRAB_TRANSPORT = None

# TODO: wrap all RESPONSE* things into class

def reset_env():
    RESPONSE.update({'get': '', 'post': '', 'cookies': None,
                     'once_code': None, 'get_callback': None})
    RESPONSE_ONCE.update({'get': None, 'post': None})
    for x in xrange(len(RESPONSE_ONCE_HEADERS)):
        RESPONSE_ONCE_HEADERS.pop()

# Initial env configuration
reset_env()

def prepare_test_environment():
    global TMP_DIR, TMP_FILE

    TMP_DIR = tempfile.mkdtemp()
    TMP_FILE = os.path.join(TMP_DIR, '__temp')


def clear_test_environment():
    remove_directory(TMP_DIR)


def remove_directory(path):
    for root, dirs, files in os.walk(path):
        for fname in files:
            os.unlink(os.path.join(root, fname))
        for _dir in dirs:
            shutil.rmtree(os.path.join(root, _dir))


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

                print '<-- (GET)'
                time.sleep(SLEEP['get'])

                REQUEST['headers'] = self.headers
                REQUEST['path'] = self.path

                if RESPONSE['get_callback'] is not None:
                    RESPONSE['get_callback'](self)
                else:
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
    it should not be tested if test is performed for
    specified transport
    """

    def wrapper(func):
        def test_method(*args, **kwargs):
            if GRAB_TRANSPORT == transport:
                return
            else:
                func(*args, **kwargs)
        return test_method
    return wrapper
