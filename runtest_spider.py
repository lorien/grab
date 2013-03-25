#!/usr/bin/env python
# coding: utf-8
import unittest
import sys
from optparse import OptionParser
import logging

TEST_CASE_LIST = (
    'test.spider',
    #'tests.test_distributed_spider',
    'test.spider_task',
    'test.spider_proxy',
)

EXTRA_TEST_LIST = (
    'test.spider_mongo_queue',
)

def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = OptionParser()
    parser.add_option('-t', '--test', help='Run only specified tests')
    parser.add_option('--extra', action='store_true',
                      default=False, help='Run extra tests for specific backends')
    opts, args = parser.parse_args()

    loader = unittest.TestLoader()
    if opts.test:
        suite = loader.loadTestsFromName(opts.test)
    else:
        compiled_test_list = TEST_CASE_LIST
        if opts.extra:
            compiled_test_list += EXTRA_TEST_LIST
        suite = loader.loadTestsFromNames(compiled_test_list)
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
