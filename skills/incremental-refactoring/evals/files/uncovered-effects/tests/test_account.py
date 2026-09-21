import unittest
from account import deposit

class AccountTests(unittest.TestCase):
    def test_deposit(self):
        self.assertEqual(deposit(10, 1, lambda v: None, lambda *a: None), 11)
