"""外部依存なしで偽 Vitest を起動し、coverage CLI の成否契約を検証する。"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check-coverage.sh"
BASH = os.environ.get("TEST_BASH", "/bin/bash")

FAKE_VITEST = r'''
import json
import os
from pathlib import Path
import sys

Path("invocation.json").write_text(json.dumps(sys.argv[1:]))
print("fake test stdout", flush=True)
print("fake test stderr", file=sys.stderr, flush=True)
if sys.argv[1:].count("--coverage") > 1:
    print("Expected a single value for option '--coverage'", file=sys.stderr)
    sys.exit(1)
prefix = "--coverage.reportsDirectory="
directories = [arg[len(prefix):] for arg in sys.argv[1:] if arg.startswith(prefix)]
if len(directories) != 1:
    sys.exit(98)
if os.environ.get("FAKE_SKIP_REPORT") != "1":
    destination = Path(directories[0]) / "coverage-final.json"
    destination.write_text(Path(os.environ["FAKE_REPORT"]).read_text())
sys.exit(int(os.environ.get("FAKE_EXIT", "0")))
'''


class CheckCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="coverage cli test ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        (self.root / "tmp").mkdir()
        self.vitest = self.root / "node_modules" / ".bin" / "vitest"
        self.vitest.parent.mkdir(parents=True)
        self.vitest.write_text(f"#!{sys.executable}\n" + FAKE_VITEST)
        self.vitest.chmod(0o755)
        self.fixture = self.root / "fixture.json"
        self.environment = {
            **os.environ,
            "TMPDIR": str(self.root / "tmp"),
            "FAKE_REPORT": str(self.fixture),
            "FAKE_EXIT": "0",
            "FAKE_SKIP_REPORT": "0",
        }
        self.write_report({"src/a.ts": [1, 1, 1, 1, 0]})

    def entry(self, relative, hits):
        filename = str(self.root / relative)
        return {
            "path": filename,
            "statementMap": {
                str(index): {
                    "start": {"line": index + 1, "column": 0},
                    "end": {"line": index + 1, "column": 5},
                }
                for index in range(len(hits))
            },
            "s": {str(index): hit for index, hit in enumerate(hits)},
            "fnMap": {},
            "f": {},
            "branchMap": {},
            "b": {},
        }

    def write_report(self, files):
        self.fixture.write_text(json.dumps({
            str(self.root / relative): self.entry(relative, hits)
            for relative, hits in files.items()
        }))

    def run_check(self, *arguments, **environment):
        return subprocess.run(
            [BASH, str(SCRIPT), *map(str, arguments)],
            cwd=self.root,
            env={**self.environment, **environment},
            capture_output=True,
            text=True,
            timeout=15,
        )

    def assert_error(self, result, message):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ERROR:", result.stderr)
        self.assertIn(message, result.stderr)
        self.assertNotIn("PASS ", result.stdout)

    def report_path(self, result):
        line = next(line for line in result.stdout.splitlines() if line.startswith("Coverage report: "))
        return Path(line.removeprefix("Coverage report: "))

    def test_default_threshold_and_local_vitest_need_no_config_file(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS 80.0% src/a.ts (4/5 statements)", result.stdout)
        self.assertIn("fake test stdout", result.stdout)
        self.assertIn("fake test stderr", result.stderr)
        arguments = json.loads((self.root / "invocation.json").read_text())
        self.assertEqual(arguments[:3], ["run", "--coverage.enabled=true", "--coverage.reporter=json"])
        self.assertTrue(self.report_path(result).is_file())

    def test_each_invocation_uses_a_new_directory_and_keeps_old_coverage(self):
        previous = self.root / "coverage" / "coverage-final.json"
        previous.parent.mkdir()
        previous.write_text("old report is unchanged")
        first, second = self.run_check("80"), self.run_check("80")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertNotEqual(self.report_path(first), self.report_path(second))
        self.assertTrue(self.report_path(first).is_file())
        self.assertEqual(previous.read_text(), "old report is unchanged")

    def test_test_failure_preserves_exit_code_logs_and_never_reports_pass(self):
        self.write_report({"src/a.ts": [1]})
        result = self.run_check("80", FAKE_EXIT="7")
        self.assert_error(result, "test command failed (exit 7)")
        self.assertEqual(result.returncode, 7)
        self.assertIn("fake test stdout", result.stdout)
        self.assertIn("fake test stderr", result.stderr)
        self.assertTrue(self.report_path(result).is_file())

    def test_success_without_new_report_does_not_reuse_stale_passing_report(self):
        old = self.root / "coverage" / "coverage-final.json"
        old.parent.mkdir()
        old.write_text(self.fixture.read_text())
        result = self.run_check("80", FAKE_SKIP_REPORT="1")
        self.assert_error(result, "did not create")
        self.assertEqual(old.read_text(), self.fixture.read_text())

    def test_failed_tests_without_report_still_return_test_exit_code(self):
        result = self.run_check("80", FAKE_SKIP_REPORT="1", FAKE_EXIT="9")
        self.assert_error(result, "test command failed (exit 9)")
        self.assertEqual(result.returncode, 9)

    def test_selects_only_exact_normalized_paths(self):
        self.write_report({"src/a.ts": [1], "src/a.tsx": [0], "other/src/a.ts": [0]})
        for target in ["src/a.ts", "./src/a.ts", "src/../src/a.ts", self.root / "src/a.ts"]:
            with self.subTest(target=target):
                result = self.run_check("100", target)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("PASS 100.0% src/a.ts", result.stdout)
                self.assertNotIn("FAIL", result.stdout)

    def test_missing_target_fails_even_when_another_target_passes(self):
        result = self.run_check("80", "src/a.ts", "src/missing.ts")
        self.assert_error(result, "requested files are missing")

    def test_filename_substring_is_not_a_target_match(self):
        self.assert_error(self.run_check("80", "a.ts"), "requested files are missing")

    def test_mixed_coverage_fails_if_one_selected_file_is_below_threshold(self):
        self.write_report({"src/a.ts": [1], "src/b.ts": [0]})
        result = self.run_check("80")
        self.assertEqual(result.returncode, 1)
        self.assertIn("PASS 100.0% src/a.ts", result.stdout)
        self.assertIn("FAIL 0.0% src/b.ts", result.stdout)

    def test_rounding_to_threshold_does_not_turn_failure_into_pass(self):
        self.write_report({"src/a.ts": [1] * 1999 + [0] * 501})
        result = self.run_check("80")
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL 80.0% src/a.ts (1999/2500 statements)", result.stdout)

    def test_decimal_and_endpoint_thresholds(self):
        for threshold, hits, status in [
            ("80.01", [1] * 4 + [0], 1),
            ("0", [0], 0),
            ("100.0", [1], 0),
            ("58", [1] * 29 + [0] * 21, 0),
            ("80.0000000000000000001", [1] * 4 + [0], 1),
        ]:
            with self.subTest(threshold=threshold):
                self.write_report({"src/a.ts": hits})
                result = self.run_check(threshold)
                self.assertEqual(result.returncode, status, result.stdout + result.stderr)

    def test_invalid_thresholds_fail_before_running_tests(self):
        for threshold in ["-1", "100.1", "101", "NaN", "80; touch injected", ""]:
            with self.subTest(threshold=threshold):
                result = self.run_check(threshold)
                self.assert_error(result, "threshold must be")
                self.assertFalse((self.root / "invocation.json").exists())

    def test_empty_command_separator_fails_before_running_tests(self):
        self.assert_error(self.run_check("80", "--"), "command is required")
        self.assertFalse((self.root / "invocation.json").exists())

    def test_explicit_command_preserves_arguments_without_shell_evaluation(self):
        target = "src/with spaces $(touch injected).ts"
        self.write_report({target: [1]})
        literal = "a b; $(touch injected) `touch injected`"
        result = self.run_check("80", target, "--", sys.executable, self.vitest, "test", "--", literal)
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments = json.loads((self.root / "invocation.json").read_text())
        self.assertEqual(arguments[:3], ["test", "--", literal])
        self.assertEqual(arguments[3:5], ["--coverage.enabled=true", "--coverage.reporter=json"])
        self.assertIn(f"PASS 100.0% {target}", result.stdout)
        self.assertFalse((self.root / "injected").exists())

    def test_existing_coverage_command_does_not_receive_duplicate_boolean_flag(self):
        result = self.run_check("80", "--", self.vitest, "run", "--coverage")
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments = json.loads((self.root / "invocation.json").read_text())
        self.assertEqual(arguments.count("--coverage"), 1)
        self.assertIn("--coverage.enabled=true", arguments)
        self.assertIn("PASS 80.0% src/a.ts", result.stdout)

    def test_missing_explicit_command_is_reported_with_nonzero_status(self):
        result = self.run_check("80", "--", self.root / "missing-command")
        self.assert_error(result, "test command failed")

    def test_malformed_json_is_explained(self):
        self.fixture.write_text("{broken json")
        self.assert_error(self.run_check("80"), "coverage report validation failed")

    def test_empty_or_wrong_json_root_is_rejected(self):
        for report in [{}, [], None, "text", 42]:
            with self.subTest(report=report):
                self.fixture.write_text(json.dumps(report))
                self.assert_error(self.run_check("80"), "non-empty Istanbul file map")

    def test_missing_or_invalid_statement_counters_are_rejected(self):
        for counter in [None, [], "invalid"]:
            with self.subTest(counter=counter):
                entry = self.entry("src/a.ts", [1])
                entry["s"] = counter
                self.fixture.write_text(json.dumps({entry["path"]: entry}))
                self.assert_error(self.run_check("80"), "s must be an object")
        entry = self.entry("src/a.ts", [1])
        del entry["s"]
        self.fixture.write_text(json.dumps({entry["path"]: entry}))
        self.assert_error(self.run_check("80"), "s must be an object")

    def test_invalid_hit_counts_are_rejected(self):
        for hit in [-1, 0.5, "1", True, None, 2**53]:
            with self.subTest(hit=hit):
                self.write_report({"src/a.ts": [hit]})
                self.assert_error(self.run_check("0"), "non-negative integer hit counts")

    def test_statement_map_must_match_counter_ids(self):
        for statement_map in [None, {}, {"1": {}}]:
            with self.subTest(statement_map=statement_map):
                entry = self.entry("src/a.ts", [1])
                entry["statementMap"] = statement_map
                self.fixture.write_text(json.dumps({entry["path"]: entry}))
                self.assert_error(self.run_check("80"), "statementMap and s do not match")

    def test_path_mismatch_and_duplicate_normalized_paths_are_rejected(self):
        entry = self.entry("src/a.ts", [1])
        self.fixture.write_text(json.dumps({str(self.root / "src/b.ts"): entry}))
        self.assert_error(self.run_check("80"), "file path mismatch")
        self.fixture.write_text(json.dumps({entry["path"]: entry, str(self.root) + "/./src/a.ts": entry}))
        self.assert_error(self.run_check("80"), "duplicate normalized file path")

    def test_non_statement_hit_counts_are_validated_if_present(self):
        for key, counters in [("f", {"0": -1}), ("b", {"0": [1, -1]}), ("b", {"0": 1})]:
            with self.subTest(key=key, counters=counters):
                entry = self.entry("src/a.ts", [1])
                entry[key] = counters
                self.fixture.write_text(json.dumps({entry["path"]: entry}))
                self.assert_error(self.run_check("80"), "coverage report validation failed")

    def test_zero_statements_are_na_alongside_measurable_files(self):
        self.write_report({"src/a.ts": [1], "src/types.ts": []})
        result = self.run_check("80")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("N/A src/types.ts (no executable statements)", result.stdout)
        self.assertNotIn("PASS 100.0% src/types.ts", result.stdout)

    def test_only_zero_statement_targets_cannot_pass(self):
        self.write_report({"src/a.ts": [1], "src/types.ts": []})
        result = self.run_check("80", "src/types.ts")
        self.assert_error(result, "no statements to evaluate")
        self.assertIn("N/A src/types.ts", result.stdout)
        self.write_report({"src/types.ts": []})
        self.assert_error(self.run_check("0"), "no statements to evaluate")


if __name__ == "__main__":
    unittest.main()
