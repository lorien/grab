from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import threading
import time

# The port on which the fake http server listens requests
FAKE_SERVER_PORT = 9876

# Simple URL which could be used in tests
BASE_URL = 'http://localhost:%d' % FAKE_SERVER_PORT

# This global objects is used by Fake HTTP Server
# It return content of HTML variable for any GET request
RESPONSE = {'get': '', 'post': '', 'cookies': None,
            'once_code': None}
RESPONSE_ONCE_HEADERS = []

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
                self.wfile.write(RESPONSE['get'])
                REQUEST['headers'] = self.headers
                print '<-- (GET)'

            def log_message(*args, **kwargs):
                "Do not log to console"
                pass

            def do_POST(self):
                post_size = int(self.headers.getheader('content-length'))
                REQUEST['post'] = self.rfile.read(post_size)
                REQUEST['headers'] = self.headers

                if RESPONSE['once_code']:
                    self.send_response(RESPONSE['once_code'])
                    RESPONSE['once_code'] = None
                else:
                    self.send_response(200)
                while RESPONSE_ONCE_HEADERS:
                    self.send_header(*RESPONSE_ONCE_HEADERS.pop())
                self.end_headers()
                self.wfile.write(RESPONSE['post'])

        server_address = ('localhost', FAKE_SERVER_PORT)
        try:
            httpd = HTTPServer(server_address, RequestHandlerClass)
            httpd.serve_forever()
        except IOError:
            # Do nothing if server alrady is running
            pass
