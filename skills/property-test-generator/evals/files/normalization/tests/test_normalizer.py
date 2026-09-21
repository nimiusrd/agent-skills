import unittest
from normalizer import normalize_words

class NormalizerTests(unittest.TestCase):
    def test_example(self):
        self.assertEqual(normalize_words(" A  b "), "A b")
