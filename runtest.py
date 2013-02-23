#!/usr/bin/env python
# coding: utf-8
import unittest
import sys
from optparse import OptionParser
import logging

from test.util import prepare_test_environment, clear_test_environment
import test.util
from grab.tools.watch import watch

TEST_CASE_LIST = (
    'test.base_interface',
    'test.post_feature',
    'test.grab_proxy',
    'test.upload_file',
    'test.limit_option',
    'test.cookies',
    'test.response_class',
    'test.charset_issue',
    # test server
    'test.fake_server',
    # tools
    'test.text_tools',
    'test.lxml_tools',
    'test.tools_account',
    'test.tools_control',
    # extension sub-system
    'test.extension',
    # extensions
    'test.text_extension',
    'test.lxml_extension',
    'test.form_extension',
    # test containers
    'test.item',
    # idn
    'test.i18n',
)

def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = OptionParser()
    parser.add_option('-t', '--test', help='Run only specified tests')
    parser.add_option('--transport', help='Test specified transport',
                      default='curl.CurlTransport')
    opts, args = parser.parse_args()

    prepare_test_environment()

    test.util.GRAB_TRANSPORT = opts.transport

    loader = unittest.TestLoader()
    if opts.test:
        suite = loader.loadTestsFromName(opts.test)
    else:
        suite = loader.loadTestsFromNames(TEST_CASE_LIST)
    runner = unittest.TextTestRunner()
    runner.run(suite)

    clear_test_environment()


if __name__ == '__main__':
    watch()
    main()
