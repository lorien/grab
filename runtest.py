#!/usr/bin/env python
# coding: utf-8
import unittest
import sys
from optparse import OptionParser
import logging
from copy import copy

from test.util import prepare_test_environment, clear_test_environment
import test.util
from grab.tools.watch import watch
from test.tornado_util import start_server, stop_server

# **********
# Grab Tests
# * pycurl transport
# * extensions
# * tools
# **********
GRAB_TEST_LIST = (
    # Internal API
    'test.grab_api',
    'test.grab_transport',
    'test.response_class',
    # Network
    'test.grab_get_request',
    'test.grab_post_request',
    'test.grab_user_agent',
    'test.grab_cookies',
    'test.grab_xml_processing',
    'test.grab_response_body_processing',
    # Refactor
    'test.grab_proxy',
    'test.upload_file',
    'test.limit_option',
    'test.charset_issue',
    'test.grab_pickle',
    # *** Extension sub-system
    'test.extension',
    # *** Extensions
    'test.text_extension',
    'test.lxml_extension',
    #'test.form_extension',
    'test.doc_extension',
    #'test.structured_extension',
    # *** Tornado Test Server
    'test.tornado_server',
    # *** grab.tools
    'test.text_tools',
    'test.tools_html',
    'test.lxml_tools',
    'test.tools_account',
    'test.tools_control',
    'test.tools_content',
    # *** Item
    'test.item',
    # *** Selector
    'test.selector',
    # *** IDN
    'test.i18n',
    # *** Mock transport
    'test.grab_transport_mock',
    # Javascript features
    'test.grab_js',
)

GRAB_EXTRA_TEST_LIST = ()

# *******************************************
# Kit Tests
# * All Grab tests with enabled Kit Transport
# * Kit Selectors
# *******************************************

KIT_TEST_LIST = list(GRAB_TEST_LIST)
KIT_TEST_LIST += [
    'test.selector_kit',
]
for name in (
    'test.grab_proxy',
    'test.upload_file',
    'test.limit_option',
):
    KIT_TEST_LIST.remove(name)

KIT_EXTRA_TEST_LIST = list(GRAB_EXTRA_TEST_LIST)
KIT_EXTRA_TEST_LIST += [
    'test.kit_live_sites',
]

# ************
# Spider Tests
# ************

SPIDER_TEST_LIST = (
    'test.spider',
    #'tests.test_distributed_spider',
    'test.spider_task',
    'test.spider_proxy',
    'test.spider_queue',
    'test.spider_misc',
    'test.spider_meta',
)

SPIDER_EXTRA_TEST_LIST = (
    'test.spider_mongo_queue',
    'test.spider_redis_queue',
    'test.spider_mongo_cache',
    'test.spider_mysql_cache',
    'test.spider_command_controller',
)


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
    parser.add_option('--test-kit', action='store_true',
                      default=False, help='Run tests for Grab with WebKit transport')
    opts, args = parser.parse_args()

    test.util.GRAB_TRANSPORT = opts.transport
    if opts.test_kit:
        test.util.GRAB_TRANSPORT = 'grab.transport.kit.KitTransport'

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

    if opts.test_kit:
        test_list += KIT_TEST_LIST
        if opts.extra:
            test_list += KIT_EXTRA_TEST_LIST

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
    suite = loader.loadTestsFromNames(test_list)
    runner = unittest.TextTestRunner()

    start_server()
    result = runner.run(suite)
    stop_server()

    clear_test_environment()
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
