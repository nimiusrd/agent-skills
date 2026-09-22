import unittest

from src.labels import format_label


class FormatLabelTests(unittest.TestCase):
    def test_display_labels(self):
        cases = [
            (None, False, ""),
            (None, True, ""),
            ("", False, ""),
            ("", True, ""),
            (" \t\n", False, ""),
            (" \t\n", True, ""),
            ("  Alice\tSmith ", False, "alice smith"),
            ("  Alice\tSmith ", True, "ALICE SMITH"),
            (" Straße 東京 ", False, "straße 東京"),
            (" Straße 東京 ", True, "STRASSE 東京"),
        ]
        for label, uppercase, expected in cases:
            with self.subTest(label=label, uppercase=uppercase):
                self.assertEqual(format_label(label, uppercase), expected)

    def test_default_is_lowercase(self):
        self.assertEqual(format_label("HELLO"), "hello")
