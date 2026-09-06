import unittest

from src.labels import display_name


class DisplayNameTests(unittest.TestCase):
    def test_trim(self):
        self.assertEqual(display_name("  花子  "), "花子")
