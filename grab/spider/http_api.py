from six.moves.SimpleHTTPServer import SimpleHTTPRequestHandler
from six.moves.socketserver import TCPServer
import logging
import os
import threading
import json
from weblib.encoding import make_str

logger = logging.getLogger('grab.spider.http_api')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


class ApiHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.home()
        elif self.path == '/api/info':
            self.api_info()
        elif self.path == '/api/stop':
            self.api_stop()
        else:
            self.not_found()

    def response(self, code=200, content=b'',
                 content_type='text/html; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-type', content_type)
        self.end_headers()
        self.wfile.write(content)

    def not_found(self):
        self.response(404)

    def api_info(self):
        info = {
            'counters': self.spider.stat.counters,
            'collections': dict((x, len(y)) for (x, y)
                                in self.spider.stat.collections.items()),
            'thread_number': self.spider.thread_number,
            'parser_pool_size': self.spider.parser_pool_size,
        }
        content = make_str(json.dumps(info))
        self.response(content=content)

    def api_stop(self):
        self.response()
        self.spider.stop()

    def home(self):
        html_file = os.path.join(BASE_DIR, 'spider/static/http_api.html')
        content = open(html_file, 'rb').read()
        self.response(content=content)


class ReuseTCPServer(TCPServer):
    allow_reuse_address = True


class HttpApiThread(threading.Thread):
    def __init__(self, spider, *args, **kwargs):
        self.spider = spider
        super(HttpApiThread, self).__init__(*args, **kwargs)

    def run(self):
        ApiHandler.spider = self.spider
        self.server = ReuseTCPServer(("", self.spider.http_api_port),
                                     ApiHandler)
        logging.debug('Serving HTTP API on localhost:%d'
                      % self.spider.http_api_port)
        self.server.serve_forever()
