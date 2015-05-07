import os
import shutil
import tempfile
import functools
from test_server import TestServer
from unittest import TestCase

from grab import Grab

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_SERVER_PORT = 9876
TMP_DIR = None
TMP_FILE = None

GLOBAL = {
    'backends': [],
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
    """Build the Grab instance with default options."""
    return Grab(*args, **kwargs)


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
