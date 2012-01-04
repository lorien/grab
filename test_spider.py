#!/usr/bin/env python
# coding: utf-8
import unittest
import sys
from optparse import OptionParser
import logging

TEST_CASE_LIST = (
    'tests.test_spider',
    'tests.test_distributed_spider',
)

def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = OptionParser()
    parser.add_option('-t', '--test', help='Run only specified tests')
    opts, args = parser.parse_args()

    loader = unittest.TestLoader()
    if opts.test:
        suite = loader.loadTestsFromName(opts.test)
    else:
        suite = loader.loadTestsFromNames(TEST_CASE_LIST)
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
