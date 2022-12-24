import functools
import json
import logging
import os
import platform
from contextlib import contextmanager
from copy import deepcopy
from shutil import rmtree
from tempfile import mkdtemp, mkstemp
from unittest import TestCase

from test_server import TestServer

logger = logging.getLogger(__file__)
TEST_DIR = os.path.dirname(os.path.realpath(__file__))
ADDRESS = "127.0.0.1"
NON_ROUTABLE_IP = "10.0.0.0"
DEFAULT_CONFIG = {
    "mongodb_task_queue": {
        "connection_args": {},
    },
    "redis_task_queue": {
        "connection_args": {},
    },
}


@functools.lru_cache
def load_test_config():
    config = deepcopy(DEFAULT_CONFIG)
    try:
        with open("test_config", encoding="utf-8") as inp:
            local_config = json.load(inp)
    except FileNotFoundError:
        pass
    else:
        for key, val in local_config.items():
            if key in DEFAULT_CONFIG:
                raise Exception("Invalid config key: {}".format(key))
            config[key] = val
    return config


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
