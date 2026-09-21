import unittest
from unique import unique_in_order

class UniqueTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(unique_in_order([]), [])

    def test_duplicates(self):
        self.assertEqual(unique_in_order(["A", "A", "B"]), ["A", "B"])
