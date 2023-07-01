from __future__ import annotations

import functools
import json
import logging
import os
import platform
from collections.abc import Generator, MutableMapping
from contextlib import contextmanager
from copy import deepcopy
from shutil import rmtree
from tempfile import mkdtemp, mkstemp
from typing import Any
from unittest import TestCase

from test_server import TestServer

logger = logging.getLogger(__file__)
TEST_DIR = os.path.dirname(os.path.realpath(__file__))
ADDRESS = "127.0.0.1"
NON_ROUTABLE_IP = "10.0.0.0"
DEFAULT_CONFIG: MutableMapping[str, Any] = {
    "mongodb_task_queue": {
        "connection_args": {},
    },
    "redis_task_queue": {
        "connection_args": {},
    },
}


@functools.lru_cache
def load_test_config() -> MutableMapping[str, Any]:
    config = deepcopy(DEFAULT_CONFIG)
    try:
        with open("test_config", encoding="utf-8") as inp:
            local_config = json.load(inp)
    except FileNotFoundError:
        pass
    else:
        for key, val in local_config.items():
            if key in DEFAULT_CONFIG:
                raise KeyError("Invalid config key: {}".format(key))
            config[key] = val
    return config


@contextmanager
def temp_dir(root_dir: None | str = None) -> Generator[str, None, None]:
    dir_ = mkdtemp(dir=root_dir)
    yield dir_
    rmtree(dir_)


@contextmanager
def temp_file(root_dir: None | str = None) -> Generator[str, None, None]:
    fdesc, file_ = mkstemp(dir=root_dir)
    yield file_
    os.close(fdesc)
    try:
        os.unlink(file_)
    except OSError:
        if "Windows" in platform.system():
            logger.error(  # noqa: TRY400
                "Ignoring IOError raised when trying to delete"
                " temp file %s created in `temp_file` context"
                " manager",
                file_,
            )
        else:
            raise


class BaseTestCase(TestCase):
    server: TestServer

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = start_server()

    def setUp(self) -> None:
        self.server.reset()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop()


def start_server() -> TestServer:
    server = TestServer(address=ADDRESS, port=0)
    server.start()
    logger.debug("Started test server on %s:%s", ADDRESS, server.port)
    return server
