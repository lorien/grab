#!/usr/bin/env python
# coding: utf-8
import unittest
import sys
from optparse import OptionParser
import logging

from test.tornado_util import start_server, stop_server

TEST_CASE_LIST = (
    'test.spider',
    #'tests.test_distributed_spider',
    'test.spider_task',
    'test.spider_proxy',
    'test.spider_queue',
)

EXTRA_TEST_LIST = (
    'test.spider_mongo_queue',
    'test.spider_redis_queue',
    'test.spider_cache',
)

def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = OptionParser()
    parser.add_option('-t', '--test', help='Run only specified tests')
    parser.add_option('--extra', action='store_true',
                      default=False, help='Run extra tests for specific backends')
    opts, args = parser.parse_args()

    loader = unittest.TestLoader()

    # Check tests integrity
    # Ensure that all test modules are imported correctly
    for path in TEST_CASE_LIST:
        __import__(path, None, None, ['foo'])

    if opts.test:
        if opts.test.count('.') == 1:
            __import__(opts.test, None, None, ['foo'])
        suite = loader.loadTestsFromName(opts.test)
    else:
        compiled_test_list = TEST_CASE_LIST
        if opts.extra:
            compiled_test_list += EXTRA_TEST_LIST
        suite = loader.loadTestsFromNames(compiled_test_list)
    runner = unittest.TextTestRunner()

    start_server()
    result = runner.run(suite)
    stop_server()

    if result.wasSuccessful():
        return 0
    else:
        return -1


if __name__ == '__main__':
    main()
