#!/usr/bin/env python3
from __future__ import annotations

import logging
import sys
import threading
import unittest
from argparse import ArgumentParser

from tests.util import GLOBAL

VALID_BACKENDS = {"mongodb", "redis", "pyquery"}

# **********
# Grab Tests
# **********

# FIXME:
# * Test redirect and response.url after redirect
GRAB_TEST_LIST = (
    # *** Internal API
    "tests.test_grab_api",
    "tests.test_grab_transport",
    "tests.test_grab_response",
    # *** Response processing
    "tests.test_grab_xml_processing",
    "tests.test_grab_response_body_processing",
    "tests.test_grab_charset",
    "tests.test_grab_redirect",
    "tests.test_grab_document",
    # *** Network
    "tests.test_grab_get_request",
    "tests.test_grab_post_request",
    "tests.test_grab_request",
    "tests.test_grab_user_agent",
    "tests.test_grab_cookies",
    "tests.test_grab_url_processing",
    "tests.test_grab_timeout",
    # *** Refactor
    "tests.test_grab_proxy",
    "tests.test_grab_upload_file",
    "tests.test_grab_charset_issue",
    "tests.test_grab_pickle",
    "tests.test_proxylist",
    # *** Extensions
    "tests.test_ext_text",
    "tests.test_ext_rex",
    "tests.test_ext_lxml",
    "tests.test_ext_form",
    # *** grab.export
    "tests.test_grab_error",
    "tests.test_ext_pyquery",
    # *** Other things
    "tests.test_xml_security",
    "tests.test_server",
)

# ************
# Spider Tests
# ************

SPIDER_TEST_LIST = (
    "tests.test_spider_task",
    "tests.test_spider",
    "tests.test_spider_proxy",
    "tests.test_spider_queue",
    "tests.test_spider_misc",
    "tests.test_spider_error",
    "tests.test_spider_stat",
    "tests.test_spider_multiprocess",
)


def setup_logging():
    logging.basicConfig(level=logging.DEBUG)
    for name, level in (
        ("grab.network", logging.INFO),
        ("tornado.access", logging.ERROR),
        ("tests.util", logging.INFO),
        ("grab.util", logging.INFO),
        ("grab.base", logging.INFO),
        ("grab.spider.base", logging.INFO),
        ("grab.spider.parser_pipeline", logging.INFO),
    ):
        logger = logging.getLogger(name)
        logger.setLevel(level)
    for hdl in logging.getLogger().handlers:
        hdl.setFormatter(logging.Formatter("[%(levelname)s] %(name)s -- %(message)s"))


def parse_backend_argument(inp: None | str) -> list[str]:
    ret = set()
    if inp is None:
        return ret
    for item in inp.split(","):
        if item not in VALID_BACKENDS:
            raise Exception("Invalid backend value: {}".format(item))
        ret.add(item)
    return ret


def main():
    setup_logging()
    parser = ArgumentParser()
    parser.add_argument("-t", "--test", help="Run only specified tests")
    parser.add_argument("--network-service", default=None)
    parser.add_argument(
        "--test-grab",
        action="store_true",
        help="Run tests for Grab::Spider",
    )
    parser.add_argument("--test-spider", action="store_true", help="Run tests for Grab")
    parser.add_argument(
        "--test-all",
        action="store_true",
        help="Run tests for both Grab and Grab::Spider",
    )
    parser.add_argument(
        "--backend",
        help=(
            "Run extra tests that depends on given backends. Multiple backends"
            " are delimited by comma."
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument("--failfast", action="store_true", help="Stop at first fail")
    opts = parser.parse_args()
    GLOBAL["network_service"] = opts.network_service
    GLOBAL["backends"].update(parse_backend_argument(opts.backend))
    test_list = []

    if opts.test_all:
        test_list += GRAB_TEST_LIST
        test_list += SPIDER_TEST_LIST

    if opts.test_grab:
        test_list += GRAB_TEST_LIST

    if opts.test_spider:
        test_list += SPIDER_TEST_LIST

    if opts.test:
        test_list += [opts.test]

    if opts.verbose:
        from grab.spider.base import logger_verbose

        logger_verbose.setLevel(logging.DEBUG)

    # Check tests integrity
    # Ensure that all test modules are imported correctly
    for path in test_list:
        __import__(path, None, None, ["foo"])

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for path in test_list:
        mod_suite = loader.loadTestsFromName(path)
        for some_suite in mod_suite:
            for test in some_suite:
                if not hasattr(test, "backend") or test.backend in GLOBAL["backends"]:
                    suite.addTest(test)
    runner = unittest.TextTestRunner(failfast=opts.failfast)
    result = runner.run(suite)
    th_list = list(threading.enumerate())
    print("Active threads (%d):" % len(th_list))
    for th in th_list:
        print(" - %s (is_alive:%s)" % (th, th.is_alive()))

    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
