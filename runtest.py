#!/usr/bin/env python
# coding: utf-8
import logging
import sys
import threading
import unittest
from optparse import OptionParser

from tests.util import GLOBAL

# **********
# Grab Tests
# **********

GRAB_TEST_LIST = (
    "tests.ext_doc",
    "tests.ext_form",
    "tests.ext_lxml",
    "tests.ext_pyquery",
    "tests.ext_rex",
    "tests.ext_text",
    "tests.grab_api",
    "tests.grab_charset",
    "tests.grab_charset_issue",
    "tests.grab_cookies",
    "tests.grab_debug",
    "tests.grab_defusedxml",
    "tests.grab_deprecated",
    "tests.grab_document",
    "tests.grab_error",
    "tests.grab_get_request",
    "tests.grab_limit_option",
    "tests.grab_pickle",
    "tests.grab_post_request",
    "tests.grab_proxy",
    "tests.grab_redirect",
    "tests.grab_request",
    "tests.grab_response_body_processing",
    "tests.grab_sigint",
    "tests.grab_timeout",
    "tests.grab_transport",
    "tests.grab_upload_file",
    "tests.grab_url_processing",
    "tests.grab_user_agent",
    "tests.grab_xml_processing",
    "tests.proxy",
    "tests.pycurl_cookie",
    "tests.raw_server",
    "tests.response_class",
    "tests.script_crawl",
    "tests.util_config",
    "tests.util_log",
    "tests.util_module",
)

# ************
# Spider Tests
# ************

SPIDER_TEST_LIST = (
    "tests.spider",
    "tests.spider_cache",  # backends: mongodb, mysql, postgresql
    #'tests.spider_data',
    "tests.spider_error",
    "tests.spider_meta",
    "tests.spider_misc",
    "tests.spider_multiprocess",
    "tests.spider_proxy",
    "tests.spider_queue",  # backends: redis, mongodb
    "tests.spider_sigint",
    "tests.spider_stat",
    "tests.spider_task",
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
        ("pymongo", logging.INFO),
    ):
        logger = logging.getLogger(name)
        logger.setLevel(level)


def main():
    setup_logging()
    parser = OptionParser()
    parser.add_option("-t", "--test", help="Run only specified tests")
    parser.add_option("--grab-transport", default="pycurl")
    parser.add_option("--network-service", default="multicurl")
    parser.add_option(
        "--test-grab",
        action="store_true",
        default=False,
        help="Run tests for Grab::Spider",
    )
    parser.add_option(
        "--test-spider", action="store_true", default=False, help="Run tests for Grab"
    )
    parser.add_option(
        "--test-all",
        action="store_true",
        default=False,
        help="Run tests for both Grab and Grab::Spider",
    )
    parser.add_option(
        "--backend-mongodb",
        action="store_true",
        default=False,
        help="Run extra tests that depends on mongodb",
    )
    parser.add_option(
        "--backend-redis",
        action="store_true",
        default=False,
        help="Run extra tests that depends on redis",
    )
    parser.add_option(
        "--backend-mysql",
        action="store_true",
        default=False,
        help="Run extra tests that depends on mysql",
    )
    parser.add_option(
        "--backend-postgresql",
        action="store_true",
        default=False,
        help="Run extra tests that depends on postgresql",
    )
    parser.add_option(
        "--mp-mode",
        action="store_true",
        default=False,
        help="Enable multiprocess mode in spider tests",
    )
    parser.add_option(
        "--profile", action="store_true", default=False, help="Do profiling"
    )
    parser.add_option(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose logging",
    )
    opts, _ = parser.parse_args()

    GLOBAL["grab_transport"] = opts.grab_transport
    GLOBAL["network_service"] = opts.network_service

    if opts.backend_mongodb:
        GLOBAL["backends"].append("mongodb")

    if opts.backend_redis:
        GLOBAL["backends"].append("redis")

    if opts.backend_mysql:
        GLOBAL["backends"].append("mysql")

    if opts.backend_postgresql:
        GLOBAL["backends"].append("postgresql")

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

    GLOBAL["mp_mode"] = opts.mp_mode

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

    runner = unittest.TextTestRunner()

    if opts.profile:
        import cProfile
        import pstats

        import pyprof2calltree

        profile_tree_file = "var/test.prof.out"
        prof = cProfile.Profile()
        result = prof.runcall(runner.run, suite)
        stats = pstats.Stats(prof)
        stats.strip_dirs()
        pyprof2calltree.convert(stats, profile_tree_file)
    else:
        result = runner.run(suite)

    th_list = list(threading.enumerate())
    print("Active threads ({}):".format(len(th_list)))
    for th in th_list:
        print("Thread: {} (isAlive:{})".format(th, th.is_alive()))

    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
