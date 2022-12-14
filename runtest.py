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
    "tests.grab_api",
    "tests.grab_transport",
    "tests.response_class",
    "tests.grab_debug",
    # *** Response processing
    "tests.grab_xml_processing",
    "tests.grab_response_body_processing",
    "tests.grab_charset",
    "tests.grab_redirect",
    "tests.grab_document",
    # *** Network
    "tests.grab_get_request",
    "tests.grab_post_request",
    "tests.grab_request",
    "tests.grab_user_agent",
    "tests.grab_cookies",
    "tests.grab_url_processing",
    "tests.grab_timeout",
    # *** Refactor
    "tests.grab_proxy",
    "tests.grab_upload_file",
    "tests.grab_limit_option",
    "tests.grab_charset_issue",
    "tests.grab_pickle",
    "tests.proxy",
    # *** Extensions
    "tests.ext_text",
    "tests.ext_rex",
    "tests.ext_lxml",
    "tests.ext_form",
    "tests.ext_doc",
    # *** util.module
    "tests.util_log",
    # *** grab.export
    "tests.grab_error",
    "tests.ext_pyquery",
    # *** Other things
    "tests.xml_security",
    "tests.raw_server",
    "tests.misc",
    "tests.test_util_http",
)

# ************
# Spider Tests
# ************

SPIDER_TEST_LIST = (
    "tests.spider_task",
    "tests.spider",
    "tests.spider_proxy",
    "tests.spider_queue",
    "tests.spider_misc",
    "tests.spider_error",
    "tests.spider_stat",
    "tests.spider_multiprocess",
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
        ("grab.stat", logging.INFO),
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
