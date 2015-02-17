#!/usr/bin/env python
# coding: utf-8
import unittest
import sys
from optparse import OptionParser
import logging
from copy import copy

from test.util import prepare_test_environment, clear_test_environment, GLOBAL
from test.server import start_server, stop_server
from tools.watch import watch

# **********
# Grab Tests
# * pycurl transport
# * extensions
# **********
GRAB_TEST_LIST = (
    # Internal API
    'test.case.grab_api',
    'test.case.grab_transport',
    'test.case.response_class',
    'test.case.grab_debug',
    # Response processing
    'test.case.grab_xml_processing',
    'test.case.grab_response_body_processing',
    #'test.case.grab_charset',
    # Network
    'test.case.grab_get_request',
    'test.case.grab_post_request',
    'test.case.grab_user_agent',
    'test.case.grab_cookies',
    # Refactor
    'test.case.grab_proxy',
    'test.case.grab_upload_file',
    'test.case.grab_limit_option',
    'test.case.grab_charset_issue',
    'test.case.grab_pickle',
    # *** Extension sub-system
    'test.case.extension',
    # *** Extensions
    'test.case.ext_text',
    'test.case.ext_rex',
    'test.case.ext_lxml',
    #'test.case.ext_form',
    'test.case.ext_doc',
    'test.case.ext_structured',
    # *** Tornado Test Server
    'test.case.debug_server',
    # *** Item
    # FIXME: disabled because it fails test
    # and it will be removed in near future
    # 'test.case.item',
    # pycurl tests
    'test.case.pycurl_cookie',
)

GRAB_EXTRA_TEST_LIST = (
    'test.case.grab_django',
    'test.case.ext_pyquery',
)

# ************
# Spider Tests
# ************

SPIDER_TEST_LIST = (
    'test.case.spider',
    #'tests.test_distributed_spider',
    'test.case.spider_task',
    'test.case.spider_proxy',
    'test.case.spider_queue',
    'test.case.spider_misc',
    'test.case.spider_meta',
    'test.case.spider_error',
    'test.case.spider_cache',
    'test.case.spider_command_controller',
)

SPIDER_EXTRA_TEST_LIST = ()


def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = OptionParser()
    parser.add_option('-t', '--test', help='Run only specified tests')
    parser.add_option('--transport', help='Test specified transport',
                      default='grab.transport.curl.CurlTransport')
    parser.add_option('--extra', action='store_true',
                      default=False, help='Run extra tests for specific backends')
    parser.add_option('--test-grab', action='store_true',
                      default=False, help='Run tests for Grab::Spider')
    parser.add_option('--test-spider', action='store_true',
                      default=False, help='Run tests for Grab')
    parser.add_option('--test-all', action='store_true',
                      default=False, help='Run tests for both Grab and Grab::Spider')
    parser.add_option('--backend-mongo', action='store_true',
                      default=False, help='Run extra tests that depends on mongodb')
    parser.add_option('--backend-redis', action='store_true',
                      default=False, help='Run extra tests that depends on redis')
    parser.add_option('--backend-mysql', action='store_true',
                      default=False, help='Run extra tests that depends on mysql')
    parser.add_option('--backend-postgresql', action='store_true',
                      default=False, help='Run extra tests that depends on postgresql')
    opts, args = parser.parse_args()

    GLOBAL['transport'] = opts.transport

    if opts.backend_mongo:
        GLOBAL['backends'].append('mongo')

    if opts.backend_redis:
        GLOBAL['backends'].append('redis')

    if opts.backend_mysql:
        GLOBAL['backends'].append('mysql')

    if opts.backend_postgresql:
        GLOBAL['backends'].append('postgresql')

    prepare_test_environment()
    test_list = []

    if opts.test_all:
        test_list += GRAB_TEST_LIST
        test_list += SPIDER_TEST_LIST
        if opts.extra:
            test_list += GRAB_EXTRA_TEST_LIST
            test_list += SPIDER_EXTRA_TEST_LIST

    if opts.test_grab:
        test_list += GRAB_TEST_LIST
        if opts.extra:
            test_list += GRAB_EXTRA_TEST_LIST

    if opts.test_spider:
        test_list += SPIDER_TEST_LIST
        if opts.extra:
            test_list += SPIDER_EXTRA_TEST_LIST

    if opts.test:
        test_list += [opts.test]

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
                if not hasattr(test, '_backend') or test._backend in GLOBAL['backends']:
                    suite.addTest(test)

    runner = unittest.TextTestRunner()

    start_server()
    result = runner.run(suite)

    clear_test_environment()
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
