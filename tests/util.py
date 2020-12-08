import os
from unittest import TestCase
import logging
from contextlib import contextmanager
from tempfile import mkdtemp, mkstemp
from shutil import rmtree
import platform
import itertools

from test_server import TestServer

from grab import Grab
from grab import base

logger = logging.getLogger('tests.util') # pylint: disable=invalid-name
TEST_DIR = os.path.dirname(os.path.realpath(__file__))
RAW_SERVER_PORT = 9875
TEST_SERVER_PORT = 9876
ADDRESS = '127.0.0.1'
EXTRA_PORT1 = TEST_SERVER_PORT + 1
EXTRA_PORT2 = TEST_SERVER_PORT + 2
NON_ROUTABLE_IP = '10.0.0.0'

GLOBAL = {
    'backends': [],
    'grab_transport': None,
    'network_service': None,
}


@contextmanager
def temp_dir(root_dir=None):
    dir_ = mkdtemp(dir=root_dir)
    yield dir_
    rmtree(dir_)


@contextmanager
def temp_file(root_dir=None):
    fdesc, file_ = mkstemp(dir=root_dir)
    yield file_
    os.close(fdesc)
    try:
        os.unlink(file_)
    except (IOError, OSError):
        if 'Windows' in platform.system():
            logger.error('Ignoring IOError raised when trying to delete'
                         ' temp file %s created in `temp_file` context'
                         ' manager', file_)
        else:
            raise


def build_grab(*args, **kwargs):
    """Builds the Grab instance with default options."""
    kwargs.setdefault('transport', GLOBAL['grab_transport'])
    return Grab(*args, **kwargs)


def build_spider(cls, **kwargs):
    """Builds the Spider instance with default options."""
    kwargs.setdefault('grab_transport', GLOBAL['grab_transport'])
    kwargs.setdefault('network_service', GLOBAL['network_service'])
    return cls(**kwargs)


class BaseGrabTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = start_server()

    def setUp(self):
        self.server.reset()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()


def start_server():
    logger.debug('Starting test server on %s:%s', ADDRESS, TEST_SERVER_PORT)
    server = TestServer(address=ADDRESS, port=TEST_SERVER_PORT)
    server.start()
    return server


def exclude_grab_transport(*names):
    def decorator(func):
        def caller(*args, **kwargs):
            if GLOBAL['grab_transport'] in names:
                func_name = '%s:%s' % (func.__module__, func.__name__)
                logger.debug('Running test %s for grab transport %s is'
                             ' restricted', func_name,
                             GLOBAL['grab_transport'])
                return None
            else:
                return func(*args, **kwargs)
        return caller
    return decorator


def only_grab_transport(*names):
    def decorator(func):
        def caller(*args, **kwargs):
            if GLOBAL['grab_transport'] in names:
                return func(*args, **kwargs)
            else:
                func_name = '%s:%s' % (func.__module__, func.__name__)
                logger.debug('Running test %s for grab transport %s is'
                             ' restricted', func_name,
                             GLOBAL['grab_transport'])
                return None
        return caller
    return decorator


def skip_test_if(condition, why_message):
    def decorator(func):
        def caller(*args, **kwargs):
            if condition():
                func_name = '%s:%s' % (func.__module__, func.__name__)
                logger.debug('Skipping test %s because %s',
                             func_name, why_message)
                return None
            else:
                return func(*args, **kwargs)
        return caller
    return decorator


def run_test_if(condition, why_message):
    def decorator(func):
        def caller(*args, **kwargs):
            if condition():
                return func(*args, **kwargs)
            else:
                func_name = '%s:%s' % (func.__module__, func.__name__)
                logger.debug('Running test %s is restricted because'
                             ' it is not %s', func_name, why_message)
                return None
        return caller
    return decorator


def reset_request_counter():
    base.REQUEST_COUNTER = itertools.count(1)


def start_raw_server():
    from socketserver import TCPServer, StreamRequestHandler
    from threading import Thread

    class RawTCPServer(TCPServer):
        allow_reuse_address = True
        response = {
            'data': b'HTTP/1.1 200 OK\r\n\r\nraw-server',
        }

        def get_url(self):
            return 'http://%s:%d/' % (ADDRESS, RAW_SERVER_PORT)

    class RawTCPHandler(StreamRequestHandler):
        def handle(self):
            self.rfile.readline()
            self.wfile.write(self.server.response['data'])
            #invalid_url = b'http://\xa0zzz'
            #resp = (
            #    b'HTTP/1.1 200 OK\r\n' +
            #    b'URL: %s\r\n'
            #    b'\r\n'
            #    b'bar'
            #    % invalid_url
            #)
            #self.wfile.write(resp)

    server = RawTCPServer((ADDRESS, RAW_SERVER_PORT), RawTCPHandler)

    th = Thread(target=server.serve_forever)
    th.daemon = True
    th.start()
    return server


def stop_raw_server(server):
    server.shutdown()
