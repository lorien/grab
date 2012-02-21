#!/usr/bin/env python
# coding: utf-8
import unittest
import sys
from optparse import OptionParser
import logging

TEST_CASE_LIST = (
    'tests.test_text_extension',
    'tests.test_lxml_extension',
    'tests.test_form_extension',
    'tests.test_fake_server',
    'tests.test_base_interface',
    'tests.test_post_feature',
    'tests.test_proxy_feature',
    'tests.test_upload_file',
    'tests.test_limit_option',
    'tests.test_cookies',
    'tests.test_text_tools',
    'tests.test_lxml_tools',
    'tests.test_response_class',
)

def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = OptionParser()
    parser.add_option('-t', '--test', help='Run only specified tests')
    parser.add_option('--transport', help='Test specified transport',
                      default='GrabCurl')
    opts, args = parser.parse_args()

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


if __name__ == '__main__':
    main()
