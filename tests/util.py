import itertools
import logging
import os
import platform
from contextlib import contextmanager
from shutil import rmtree
from tempfile import mkdtemp, mkstemp
from unittest import TestCase

from test_server import TestServer

from grab import Grab, base

logger = logging.getLogger("tests.util")  # pylint: disable=invalid-name
TEST_DIR = os.path.dirname(os.path.realpath(__file__))
ADDRESS = "127.0.0.1"
NON_ROUTABLE_IP = "10.0.0.0"

GLOBAL = {
    "backends": [],
    "network_service": None,
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
    except OSError:
        if "Windows" in platform.system():
            logger.error(
                "Ignoring IOError raised when trying to delete"
                " temp file %s created in `temp_file` context"
                " manager",
                file_,
            )
        else:
            raise


def build_grab(*args, **kwargs):
    """Build the Grab instance with default options."""
    kwargs.setdefault("transport", "urllib3")
    return Grab(*args, **kwargs)


def build_spider(cls, **kwargs):
    """Build the Spider instance with default options."""
    kwargs.setdefault("grab_transport", "urllib3")
    kwargs.setdefault("network_service", GLOBAL["network_service"])
    return cls(**kwargs)


class BaseGrabTestCase(TestCase):
    server: TestServer

    @classmethod
    def setUpClass(cls):
        cls.server = start_server()

    def setUp(self):
        self.server.reset()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()


def start_server():
    server = TestServer(address=ADDRESS, port=0)
    server.start()
    logger.debug("Started test server on %s:%s", ADDRESS, server.port)
    return server


def skip_test_if(condition, why_message):
    def decorator(func):
        def caller(*args, **kwargs):
            if condition():
                func_name = "%s:%s" % (func.__module__, func.__name__)
                logger.debug("Skipping test %s because %s", func_name, why_message)
                return None
            return func(*args, **kwargs)

        return caller

    return decorator


def reset_request_counter():
    base.REQUEST_COUNTER = itertools.count(1)
