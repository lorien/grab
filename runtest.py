#!/usr/bin/env python
# coding: utf-8
import unittest
import sys
from optparse import OptionParser
import logging
import threading

from tests.util import GLOBAL

# **********
# Grab Tests
# **********

# FIXME:
# * Test redirect and response.url after redirect
GRAB_TEST_LIST = (
    # *** Internal API
    'tests.grab_api',
    'tests.grab_transport',
    'tests.response_class',
    'tests.grab_debug', # FIXME: fix tests excluded for urllib3
    # *** Response processing
    'tests.grab_xml_processing',
    'tests.grab_response_body_processing',
    'tests.grab_charset',
    'tests.grab_redirect',
    'tests.grab_defusedxml',
    # *** Network
    'tests.grab_get_request',
    'tests.grab_post_request',
    'tests.grab_request', # FIXME: fix tests excluded for urllib3
    'tests.grab_user_agent',
    'tests.grab_cookies', # FIXME: fix tests excluded for urllib3
    'tests.grab_url_processing',
    'tests.grab_timeout',
    # *** Refactor
    'tests.grab_proxy',
    'tests.grab_upload_file',
    'tests.grab_limit_option',
    'tests.grab_charset_issue',
    'tests.grab_pickle', # FIXME: fix tests excluded for urllib3
    'tests.proxy',
    # *** Extensions
    'tests.ext_text',
    'tests.ext_rex',
    'tests.ext_lxml',
    'tests.ext_form',
    'tests.ext_doc',
    'tests.ext_structured',
    # *** Pycurl Test
    'tests.pycurl_cookie',
    # *** util.module
    'tests.util_module',
    'tests.util_log',
    # *** grab.export
    'tests.util_config',
    'tests.script_crawl',
    'tests.grab_error',
    'tests.grab_deprecated',
    'tests.ext_pyquery',
    # *** process control
    'tests.grab_sigint',
    'tests.spider_sigint',
)

# ************
# Spider Tests
# ************

SPIDER_TEST_LIST = (
    'tests.spider_task',
    'tests.spider',
    'tests.spider_proxy',
    'tests.spider_queue',
    'tests.spider_misc',
    'tests.spider_meta',
    'tests.spider_error',
    'tests.spider_cache',
    #'tests.spider_data',
    'tests.spider_stat',
    'tests.spider_multiprocess',
)


def setup_logging():
    logging.basicConfig(level=logging.DEBUG)
    for name, level in (
        ('grab.network', logging.INFO),
        ('tornado.access', logging.ERROR),
        ('tests.util', logging.INFO),
        ('grab.util', logging.INFO),
        ('grab.base', logging.INFO),
        ('grab.spider.base', logging.INFO),
        ('grab.spider.parser_pipeline', logging.INFO),
        ('grab.stat', logging.INFO),
    ):
        logger = logging.getLogger(name)
        logger.setLevel(level)


def main():
    setup_logging()
    parser = OptionParser()
    parser.add_option('-t', '--test', help='Run only specified tests')
    parser.add_option('--grab-transport', default='pycurl')
    parser.add_option('--network-service', default='multicurl')
    parser.add_option('--test-grab', action='store_true',
                      default=False, help='Run tests for Grab::Spider')
    parser.add_option('--test-spider', action='store_true',
                      default=False, help='Run tests for Grab')
    parser.add_option('--test-all', action='store_true',
                      default=False,
                      help='Run tests for both Grab and Grab::Spider')
    parser.add_option('--backend-mongodb', action='store_true',
                      default=False,
                      help='Run extra tests that depends on mongodb')
    parser.add_option('--backend-redis', action='store_true',
                      default=False,
                      help='Run extra tests that depends on redis')
    parser.add_option('--backend-mysql', action='store_true',
                      default=False,
                      help='Run extra tests that depends on mysql')
    parser.add_option('--backend-postgresql', action='store_true',
                      default=False,
                      help='Run extra tests that depends on postgresql')
    parser.add_option('--mp-mode', action='store_true', default=False,
                      help='Enable multiprocess mode in spider tests')
    parser.add_option('--profile', action='store_true', default=False,
                      help='Do profiling')
    parser.add_option('-v', '--verbose', action='store_true', default=False,
                      help='Enable verbose logging')
    opts, _ = parser.parse_args()

    GLOBAL['grab_transport'] = opts.grab_transport
    GLOBAL['network_service'] = opts.network_service

    if opts.backend_mongodb:
        GLOBAL['backends'].append('mongodb')

    if opts.backend_redis:
        GLOBAL['backends'].append('redis')

    if opts.backend_mysql:
        GLOBAL['backends'].append('mysql')

    if opts.backend_postgresql:
        GLOBAL['backends'].append('postgresql')

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

    GLOBAL['mp_mode'] = opts.mp_mode

    # Check tests integrity
    # Ensure that all test modules are imported correctly
    for path in test_list:
        __import__(path, None, None, ['foo'])

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for path in test_list:
        mod_suite = loader.loadTestsFromName(path)
        for some_suite in mod_suite:
            for test in some_suite:
                if (not hasattr(test, '_backend') or
                        test._backend in GLOBAL['backends']):
                    suite.addTest(test)

    runner = unittest.TextTestRunner()

    if opts.profile:
        import cProfile
        import pyprof2calltree
        import pstats

        profile_tree_file = 'var/test.prof.out'
        prof = cProfile.Profile()
        result = prof.runcall(runner.run, suite)
        stats = pstats.Stats(prof)
        stats.strip_dirs()
        pyprof2calltree.convert(stats, profile_tree_file)
    else:
        result = runner.run(suite)

    th_list = list(threading.enumerate())
    print('Active threads (%d):' % len(th_list))
    for th in th_list:
        print('Thread: %s (isAlive:%s)' % (th, th.isAlive()))

    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
