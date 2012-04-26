# coding: utf-8
from unittest import TestCase
import time

from grab.tools.control import sleep

class ControlToolsTestCase(TestCase):
    def test_sleep(self):
        now = time.time()
        sleep(0.9, 1.1)
        self.assertTrue(1.2 > (time.time() - now) > 0.8)

        now = time.time()
        sleep(0, 0.5)
        self.assertTrue(0 < (time.time() - now) < 0.6)
