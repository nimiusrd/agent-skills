import unittest
from account import deposit, withdraw


class AccountTests(unittest.TestCase):
    def test_success_and_exact_balance(self):
        for fn, amount, expected, kind in [(deposit, 1, 11, "deposit"), (withdraw, 1, 9, "withdraw"), (withdraw, 10, 0, "withdraw")]:
            events = []
            self.assertEqual(fn(10, amount, lambda v: events.append(("save", v)), lambda k, v: events.append((k, v))), expected)
            self.assertEqual(events, [("save", expected), (kind, expected)])

    def test_invalid_amount_has_no_effects(self):
        for fn in (deposit, withdraw):
            for amount in (0, -1, True, False, 1.5, "1", None):
                with self.subTest(fn=fn.__name__, amount=amount):
                    events = []
                    with self.assertRaisesRegex(ValueError, "positive integer required"):
                        fn(10, amount, events.append, lambda *a: events.append(a))
                    self.assertEqual(events, [])
        events = []
        with self.assertRaisesRegex(ValueError, "insufficient funds"):
            withdraw(10, 11, events.append, lambda *a: events.append(a))
        self.assertEqual(events, [])

    def test_save_failure_does_not_notify(self):
        for fn in (deposit, withdraw):
            events = []
            error = RuntimeError("save failed")
            def save(value):
                events.append(("save", value))
                raise error
            with self.assertRaises(RuntimeError) as caught:
                fn(10, 1, save, lambda *a: events.append(a))
            self.assertIs(caught.exception, error)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0][0], "save")

    def test_notify_failure_propagates_after_save(self):
        for fn in (deposit, withdraw):
            events = []
            error = RuntimeError("notify failed")
            def notify(kind, value):
                events.append((kind, value))
                raise error
            with self.assertRaises(RuntimeError) as caught:
                fn(10, 1, lambda v: events.append(("save", v)), notify)
            self.assertIs(caught.exception, error)
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0][0], "save")
