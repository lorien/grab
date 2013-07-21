from threading import Thread
from tornado.ioloop import IOLoop
import tornado.web
import time
import collections

from grab.util.py3k_support import *

class ServerState(object):
    PORT = 9876
    EXTRA_PORT1 = 9877
    EXTRA_PORT2 = 9878
    BASE_URL = None
    REQUEST = {}
    RESPONSE = {}
    RESPONSE_ONCE = {'headers': []}
    SLEEP = {}

    def reset(self):
        self.BASE_URL = 'http://localhost:%d' % self.PORT
        self.REQUEST.update({
            'args': {},
            'headers': {},
            'path': None,
            'method': None,
            'charset': 'utf-8',
        })
        self.RESPONSE.update({
            'get': '',
            'post': '',
            'cookies': None,
            'headers': [],
            'get_callback': None,
            'code': 200,
        })
        self.RESPONSE_ONCE.update({
            'get': None,
            'post': None,
            'code': None,
        })
        self.SLEEP.update({
            'get': 0,
            'post': 0,
        })
        for x in xrange(len(self.RESPONSE_ONCE['headers'])):
            self.RESPONSE_ONCE['headers'].pop()

SERVER = ServerState()

class MainHandler(tornado.web.RequestHandler):
    def decode_argument(self, value, **kwargs):
        return value.decode(SERVER.REQUEST['charset'])

    def method_handler(self):
        method_name = self.request.method.lower()

        time.sleep(SERVER.SLEEP['get'])
        SERVER.REQUEST['args'] = {}
        for key in self.request.arguments.keys():
            SERVER.REQUEST['args'][key] = self.get_argument(key)
        SERVER.REQUEST['headers'] = self.request.headers
        SERVER.REQUEST['path'] = self.request.path
        SERVER.REQUEST['method'] = self.request.method
        charset = SERVER.REQUEST['charset']
        # py3 hack
        if PY3K and (charset not in ('utf-8', 'utf8')):
            SERVER.REQUEST['post'] = self.request.body.decode('utf-8').encode(charset)
        else:
            SERVER.REQUEST['post'] = self.request.body

        callback_name = '%s_callback' % method_name
        if SERVER.RESPONSE.get(callback_name) is not None:
            SERVER.RESPONSE[callback_name](self)
        else:
            headers_sent = set()

            if SERVER.RESPONSE_ONCE['code']:
                self.set_status(SERVER.RESPONSE_ONCE['code'])
                SERVER.RESPONSE_ONCE['code'] = None
            else:
                self.set_status(SERVER.RESPONSE['code'])

            if SERVER.RESPONSE['cookies']:
                for name, value in sorted(SERVER.RESPONSE['cookies'].items()):
                    self.set_header('Set-Cookie', '%s=%s' % (name, value))

            if SERVER.RESPONSE['headers']:
                for name, value in SERVER.RESPONSE['headers']:
                    self.set_header(name, value)

            while SERVER.RESPONSE_ONCE['headers']:
                key, value = SERVER.RESPONSE_ONCE['headers'].pop()
                self.set_header(key, value)
                headers_sent.add(key)

            self.set_header('Listen-Port', str(self.application._listen_port))

            if not 'Content-Type' in headers_sent:
                charset = 'utf-8'
                self.set_header('Content-Type', 'text/html; charset=%s' % charset)
                headers_sent.add('Content-Type')

            if SERVER.RESPONSE_ONCE.get(method_name) is not None:
                self.write(SERVER.RESPONSE_ONCE[method_name])
                SERVER.RESPONSE_ONCE[method_name] = None
            else:
                resp = SERVER.RESPONSE.get(method_name, '')
                if isinstance(resp, collections.Callable):
                    self.write(resp())
                else:
                    self.write(resp)

    get = method_handler
    post = method_handler
    put = method_handler
    patch = method_handler
    delete = method_handler

app1 = tornado.web.Application([
    (r"^.*", MainHandler),
])
app1._listen_port = SERVER.PORT

app2 = tornado.web.Application([
    (r"^.*", MainHandler),
])
app2._listen_port = SERVER.EXTRA_PORT1

app3 = tornado.web.Application([
    (r"^.*", MainHandler),
])
app3._listen_port = SERVER.EXTRA_PORT2

app1.listen(app1._listen_port)
app2.listen(app2._listen_port)
app3.listen(app3._listen_port)

def start_server():
    def func():
        tornado.ioloop.IOLoop.instance().start()

    SERVER.reset()
    th = Thread(target=func)
    th.daemon = True
    th.start()
    time.sleep(0.5)


def stop_server():
    tornado.ioloop.IOLoop.instance().stop()
