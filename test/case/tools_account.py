# coding: utf-8
from unittest import TestCase

from grab.tools import account

class TestAccount(TestCase):
    def test_misc(self):
        bday = account.random_birthday()
        self.assertTrue(bday['month'].isdigit())
