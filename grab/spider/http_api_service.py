import logging
import os
import json

from six.moves.SimpleHTTPServer import SimpleHTTPRequestHandler
from six.moves.socketserver import TCPServer
from weblib.encoding import make_str

from grab.spider.base_service import BaseService

# pylint: disable=invalid-name
logger = logging.getLogger('grab.spider.http_api_service')
# pylint: enable=invalid-name
BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


class ApiHandler(SimpleHTTPRequestHandler):
    def do_GET(self): # pylint: disable=invalid-name
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
        #if result and self.cache_reader_service:
        #    result = result and (
        #        not self.cache_reader_service.input_queue.qsize()
        #        and not self.cache_writer_service.input_queue.qsize()
        info = {
            'counters': self.spider.stat.counters,
            'collections': dict((x, len(y)) for (x, y)
                                in self.spider.stat.collections.items()),
            'thread_number': self.spider.thread_number,
            'parser_pool_size': self.spider.parser_pool_size,
            'task_queue': self.spider.task_queue.size(),
            'task_dispatcher_input_queue': (
                self.spider.task_dispatcher.input_queue.qsize()
            ),
            'parser_service_input_queue': (
                self.spider.parser_service.input_queue.qsize()
            ),
            'network_service_active_threads': (
                self.spider.network_service.get_active_threads_number()
            ),
            'cache_reader_input_queue': (
                self.spider.cache_reader_service.input_queue.size()
                if self.spider.cache_reader_service else '--'
            ),
            'cache_writer_input_queue': (
                self.spider.cache_writer_service.input_queue.qsize()
                if self.spider.cache_writer_service else '--'
            ),
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


class HttpApiService(BaseService):
    def __init__(self, spider):
        self.spider = spider
        self.worker = self.create_worker(self.worker_callback)
        self.register_workers(self.worker)
        self.server = None

    def pause(self):
        return

    def resume(self):
        return

    def stop(self):
        # It freezes
        #if self.server:
        #    self.server.shutdown()
        pass

    def worker_callback(self, unused_worker):
        ApiHandler.spider = self.spider
        self.server = ReuseTCPServer(("", self.spider.http_api_port),
                                     ApiHandler)
        logging.debug('Serving HTTP API on localhost:%d',
                      self.spider.http_api_port)
        self.server.serve_forever()
