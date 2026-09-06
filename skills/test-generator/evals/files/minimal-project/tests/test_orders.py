import unittest

from src.orders import total_price


class TotalPriceTests(unittest.TestCase):
    def test_positive_quantity(self):
        self.assertEqual(total_price(2), 200)
