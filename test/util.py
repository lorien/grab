import os
import shutil
import tempfile
import functools
from test_server import TestServer
from unittest import TestCase
import logging

from grab import Grab

logger = logging.getLogger('test.util')
TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_SERVER_PORT = 9876
TMP_DIR = None
TMP_FILE = None

GLOBAL = {
    'backends': [],
    'multiprocess': False,
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
    `multiprocess` option that is configured globally."""
    kwargs.setdefault('multiprocess', GLOBAL['multiprocess'])
    return cls(**kwargs)


class BaseGrabTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = TestServer(address='localhost', port=TEST_SERVER_PORT)
        cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def setUp(self):
        self.server.reset()


def multiprocess_mode(mode):
    def wrapper_builder(func):
        def wrapper(self, *args, **kwargs):
            if mode != GLOBAL['multiprocess']:
                logger.debug('Skipping %s:%s:%s. Reason: need '
                             'multiprocess mode=%s' % (
                                 func.__module__,
                                 self.__class__.__name__,
                                 func.__name__, GLOBAL['multiprocess']))
            else:
                return func(self, *args, **kwargs)
        return wrapper
    return wrapper_builder
