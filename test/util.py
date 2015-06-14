import os
import shutil
import tempfile
import functools
from test_server import TestServer
from unittest import TestCase
import logging
from six.moves.urllib.request import urlopen
import socket
import time

from grab import Grab

logger = logging.getLogger('test.util')
TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_SERVER_PORT = 9876
ADDRESS = 'localhost'
EXTRA_PORT1 = TEST_SERVER_PORT + 1
EXTRA_PORT2 = TEST_SERVER_PORT + 2
TMP_DIR = None
TMP_FILE = None

GLOBAL = {
    'backends': [],
    'mp_mode': False,
    #'test_server': None,
}


def prepare_test_environment():
    global TMP_DIR, TMP_FILE

    TMP_DIR = tempfile.mkdtemp()
    TMP_FILE = os.path.join(TMP_DIR, '__temp')


def clear_test_environment():
    clear_directory(TMP_DIR)


def clear_directory(path):
    for root, dirs, files in os.walk(path):
        for fname in files:
            os.unlink(os.path.join(root, fname))
        for _dir in dirs:
            shutil.rmtree(os.path.join(root, _dir))


def get_temp_file():
    handler, path = tempfile.mkstemp(dir=TMP_DIR)
    return path


def build_grab(*args, **kwargs):
    """Builds the Grab instance with default options."""
    return Grab(*args, **kwargs)


def build_spider(cls, **kwargs):
    """Builds the Spider instance with default options. Also handles
    `--mp-mode` option that is configured globally."""
    kwargs.setdefault('mp_mode', GLOBAL['mp_mode'])
    if kwargs['mp_mode']:
        kwargs.setdefault('parser_pool_size', 2)
    else:
        kwargs['parser_pool_size'] = 1
    return cls(**kwargs)


class BaseGrabTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = start_server()#GLOBAL['test_server']

    def setUp(self):
        self.server.reset()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()


def multiprocess_mode(mode):
    def wrapper_builder(func):
        def wrapper(self, *args, **kwargs):
            if mode != GLOBAL['mp_mode']:
                logger.debug('Skipping %s:%s:%s. Reason: need '
                             '--mp-mode=%s' % (
                                 func.__module__,
                                 self.__class__.__name__,
                                 func.__name__, GLOBAL['mp_mode']))
            else:
                return func(self, *args, **kwargs)
        return wrapper
    return wrapper_builder


def start_server():
    logger.debug('Starting test server on %s:%s' % (ADDRESS, TEST_SERVER_PORT))
    server = TestServer(address=ADDRESS, port=TEST_SERVER_PORT,
                        extra_ports=[EXTRA_PORT1, EXTRA_PORT2])
    server.start()
    '''
    # Ensure that test server works
    old_timeout = socket.getdefaulttimeout()
    ok = False
    for x in range(6):
        socket.setdefaulttimeout(0.5)
        try:
            urlopen('http://localhost:%d/' % TEST_SERVER_PORT).read()
        except Exception as ex:
            logger.error('', exc_info=ex)
            time.sleep(0.1)
        else:
            ok = True
            break
    socket.setdefaulttimeout(old_timeout)
    if not ok:
        raise Exception('Test server does not respond.')
    else:
    '''
    #GLOBAL['test_server'] = server
    return server


def stop_server():
    logger.debug('Stopping test server')
    #GLOBAL['test_server'].stop()
