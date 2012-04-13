#!/usr/bin/env python
# coding: utf-8
import unittest
import sys
from optparse import OptionParser
import logging

from test.util import prepare_test_environment, clear_test_environment

TEST_CASE_LIST = (
    'test.test_text_extension',
    'test.test_lxml_extension',
    'test.test_form_extension',
    'test.test_fake_server',
    'test.test_base_interface',
    'test.test_post_feature',
    'test.test_proxy_feature',
    'test.test_upload_file',
    'test.test_limit_option',
    'test.test_cookies',
    'test.test_text_tools',
    'test.test_lxml_tools',
    'test.test_response_class',
    'test.test_tools_account',
)

def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = OptionParser()
    parser.add_option('-t', '--test', help='Run only specified tests')
    parser.add_option('--transport', help='Test specified transport',
                      default='GrabCurl')
    opts, args = parser.parse_args()

    prepare_test_environment()

    import grab
    transport = getattr(grab, opts.transport)
    grab.Grab = transport

    loader = unittest.TestLoader()
    if opts.test:
        suite = loader.loadTestsFromName(opts.test)
    else:
        suite = loader.loadTestsFromNames(TEST_CASE_LIST)
    runner = unittest.TextTestRunner()
    runner.run(suite)

    clear_test_environment()


if __name__ == '__main__':
    main()
