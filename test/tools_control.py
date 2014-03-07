# coding: utf-8
from unittest import TestCase
import time

from grab.tools.control import sleep, repeat

class ControlToolsTestCase(TestCase):
    def test_sleep(self):
        now = time.time()
        sleep(0.9, 1.1)
        self.assertTrue(1.2 > (time.time() - now) > 0.8)

        now = time.time()
        sleep(0, 0.5)
        self.assertTrue(0 < (time.time() - now) < 0.6)

    def test_repeat(self):
        COUNTER = [0]

        def foo(counter=COUNTER):
            counter[0] += 1
            if counter[0] == 1:
                raise ValueError
            elif counter[0] == 2:
                raise IndexError
            else:
                return 4

        COUNTER[0] = 0
        self.assertRaises(ValueError, lambda: repeat(foo, limit=1))

        COUNTER[0] = 0
        self.assertRaises(IndexError, lambda: repeat(foo, limit=2))

        COUNTER[0] = 0
        self.assertEqual(4, repeat(foo, limit=3))

        COUNTER[0] = 0
        self.assertRaises(IndexError,
                          lambda: repeat(foo, limit=2, fatal_exceptions=(IndexError,)))

    def test_repeat_args(self):
        result = []

        def foo(val):
            result.append(val)

        repeat(foo, args=[1])

        self.assertEqual(1, result[0])


    def test_repeat_kwargs(self):
        result = []

        def foo(**kwargs):
            result.append(kwargs['val'])

        repeat(foo, kwargs={'val': 3})

        self.assertEqual(3, result[0])
