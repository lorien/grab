#!/usr/bin/env python
# coding: utf-8
import unittest
import sys
from optparse import OptionParser
import logging

from test.util import prepare_test_environment, clear_test_environment
import test.util
from grab.tools.watch import watch
from test.tornado_util import start_server, stop_server

TEST_CASE_LIST = (
    # Main features
    'test.base_interface',
    'test.post_feature',
    'test.grab_proxy',
    'test.upload_file',
    'test.limit_option',
    'test.cookies',
    'test.response_class',
    'test.charset_issue',
    'test.grab_pickle',
    'test.grab_transport',
    # *** Tornado Test Server
    'test.tornado_server',
    # *** grab.tools
    'test.text_tools',
    'test.lxml_tools',
    'test.tools_account',
    'test.tools_control',
    # *** Extension sub-system
    'test.extension',
    # *** Extensions
    'test.text_extension',
    'test.lxml_extension',
    'test.form_extension',
    'test.doc_extension',
    # *** Item
    'test.item',
    # *** Selector
    'test.selector',
    # *** IDN
    'test.i18n',
)


def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = OptionParser()
    parser.add_option('-t', '--test', help='Run only specified tests')
    parser.add_option('--transport', help='Test specified transport',
                      default='grab.transport.curl.CurlTransport')
    opts, args = parser.parse_args()

    test.util.GRAB_TRANSPORT = opts.transport

    prepare_test_environment()
    # Check tests integrity
    # Ensure that all test modules are imported correctly
    for path in TEST_CASE_LIST:
        __import__(path, None, None, ['foo'])

    loader = unittest.TestLoader()
    if opts.test:
        if opts.test.count('.') == 1:
            __import__(opts.test, None, None, ['foo'])
        suite = loader.loadTestsFromName(opts.test)
    else:
        suite = loader.loadTestsFromNames(TEST_CASE_LIST)
    runner = unittest.TextTestRunner()

    start_server()
    result = runner.run(suite)
    stop_server()

    clear_test_environment()
    if result.wasSuccessful():
        return 0
    else:
        return -1


if __name__ == '__main__':
    watch()
    main()
