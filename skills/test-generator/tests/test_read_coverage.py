"""既存 Istanbul JSON を指定する読み取り専用 CLI の契約を標準 unittest で検証する。"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "read-coverage.cjs"
NODE = shutil.which("node")


class ReadCoverageTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(NODE, "node is required to test the reader CLI")
        self.temporary = tempfile.TemporaryDirectory(prefix="coverage reader test ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.fixture = self.root / "fixture.json"
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

    def run_cli(self, *arguments, **environment):
        return subprocess.run(
            [NODE, str(SCRIPT), *map(str, arguments)],
            cwd=self.root,
            env={**os.environ, **environment},
            capture_output=True,
            text=True,
            timeout=15,
        )

    def read_report(self, threshold="80", *targets):
        return self.run_cli(self.fixture, threshold, *targets)

    def assert_error(self, result, message):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ERROR:", result.stderr)
        self.assertIn(message, result.stderr)
        self.assertNotIn("PASS ", result.stdout)

    def snapshot_files(self):
        return {
            str(file.relative_to(self.root)): (file.read_bytes(), file.stat().st_mtime_ns)
            for file in self.root.rglob("*") if file.is_file()
        }

    def test_help_describes_read_only_scope_without_requiring_a_report(self):
        self.fixture.unlink()
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Usage: node read-coverage.cjs <report.json> <threshold> [files...]", result.stdout)
        self.assertIn("読み取り専用", result.stdout)
        self.assertIn("テスト成功や鮮度を保証しません", result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertEqual(self.snapshot_files(), {})

    def test_missing_arguments_show_usage_and_fail(self):
        for arguments in [[], [self.fixture], ["", "80"]]:
            with self.subTest(arguments=arguments):
                result = self.run_cli(*arguments)
                self.assert_error(result, "report path and threshold are required")
                self.assertIn("Usage:", result.stderr)

    def test_reports_threshold_result_and_explicitly_limits_pass_scope(self):
        result = self.read_report()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS 80.0% src/a.ts (4/5 statements)", result.stdout)
        self.assertIn(f"Report: {self.fixture}", result.stdout)
        self.assertIn("test success and report freshness are not verified", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_uses_only_the_explicit_report_without_searching_other_coverage(self):
        other = self.root / "coverage" / "coverage-final.json"
        other.parent.mkdir()
        other.write_text(self.fixture.read_text())
        self.write_report({"src/a.ts": [0]})
        result = self.read_report()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL 0.0% src/a.ts", result.stdout)
        self.fixture.unlink()
        self.assert_error(self.read_report(), "ENOENT")

    def test_relative_report_path_is_resolved_from_project_cwd(self):
        result = self.run_cli("fixture.json", "80")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"Report: {self.fixture}", result.stdout)

    def test_valid_old_report_can_pass_but_freshness_is_not_claimed(self):
        os.utime(self.fixture, (1, 1))
        result = self.read_report()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS 80.0% src/a.ts", result.stdout)
        self.assertIn("report freshness are not verified", result.stdout)

    def test_success_and_failure_leave_input_and_project_files_unchanged(self):
        source = self.root / "src" / "a.ts"
        source.parent.mkdir()
        source.write_text("export const value = 1;\n")
        for hits in [[1], [0]]:
            with self.subTest(hits=hits):
                self.write_report({"src/a.ts": hits})
                before = self.snapshot_files()
                self.read_report()
                self.assertEqual(self.snapshot_files(), before)
        self.fixture.write_text("broken JSON")
        before = self.snapshot_files()
        self.assert_error(self.read_report(), "coverage report validation failed")
        self.assertEqual(self.snapshot_files(), before)

    def test_paths_with_shell_syntax_are_literal_and_need_no_shell_on_path(self):
        target = "src/with spaces $(touch injected) `touch injected`.ts"
        self.write_report({target: [1]})
        unusual_report = self.root / "report; touch injected.json"
        self.fixture.rename(unusual_report)
        before = self.snapshot_files()
        result = self.run_cli(unusual_report, "80", target, PATH="")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"PASS 100.0% {target}", result.stdout)
        self.assertEqual(self.snapshot_files(), before)
        self.assertFalse((self.root / "injected").exists())

    def test_report_is_parsed_as_json_never_executed_as_a_node_module(self):
        executable_report = self.root / "report.cjs"
        executable_report.write_text("require('node:fs').writeFileSync('injected', 'executed');")
        self.assert_error(self.run_cli(executable_report, "80"), "coverage report validation failed")
        self.assertFalse((self.root / "injected").exists())

    def test_selects_only_exact_normalized_paths(self):
        self.write_report({"src/a.ts": [1], "src/a.tsx": [0], "other/src/a.ts": [0]})
        for target in ["src/a.ts", "./src/a.ts", "src/../src/a.ts", self.root / "src/a.ts"]:
            with self.subTest(target=target):
                result = self.read_report("100", target)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("PASS 100.0% src/a.ts", result.stdout)
                self.assertNotIn("FAIL", result.stdout)

    def test_duplicate_target_spellings_are_reported_once(self):
        result = self.read_report("80", "src/a.ts", "./src/a.ts", self.root / "src/a.ts")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("PASS 80.0% src/a.ts"), 1)

    def test_missing_target_fails_even_when_another_target_passes(self):
        self.assert_error(self.read_report("80", "src/a.ts", "src/missing.ts"), "requested files are missing")

    def test_filename_substring_is_not_a_target_match(self):
        self.assert_error(self.read_report("80", "a.ts"), "requested files are missing")

    def test_mixed_coverage_fails_if_one_selected_file_is_below_threshold(self):
        self.write_report({"src/a.ts": [1], "src/b.ts": [0]})
        result = self.read_report()
        self.assertEqual(result.returncode, 1)
        self.assertIn("PASS 100.0% src/a.ts", result.stdout)
        self.assertIn("FAIL 0.0% src/b.ts", result.stdout)

    def test_rounding_to_threshold_does_not_turn_failure_into_pass(self):
        self.write_report({"src/a.ts": [1] * 1999 + [0] * 501})
        result = self.read_report()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL 80.0% src/a.ts (1999/2500 statements)", result.stdout)

    def test_decimal_float_boundary_and_endpoint_thresholds(self):
        for threshold, hits, status in [
            ("80.01", [1] * 4 + [0], 1),
            ("0", [0], 0),
            ("100.0", [1], 0),
            ("58", [1] * 29 + [0] * 21, 0),
            ("80.0000000000000000001", [1] * 4 + [0], 1),
        ]:
            with self.subTest(threshold=threshold):
                self.write_report({"src/a.ts": hits})
                result = self.read_report(threshold)
                self.assertEqual(result.returncode, status, result.stdout + result.stderr)

    def test_invalid_thresholds_are_rejected_with_usage(self):
        for threshold in ["-1", "100.1", "101", "NaN", "Infinity", "80; touch injected", ""]:
            with self.subTest(threshold=threshold):
                result = self.read_report(threshold)
                self.assert_error(result, "threshold must be")
                self.assertIn("Usage:", result.stderr)
                self.assertFalse((self.root / "injected").exists())

    def test_malformed_json_is_explained(self):
        self.fixture.write_text("{broken json")
        self.assert_error(self.read_report(), "coverage report validation failed")

    def test_empty_or_wrong_json_root_is_rejected(self):
        for report in [{}, [], None, "text", 42]:
            with self.subTest(report=report):
                self.fixture.write_text(json.dumps(report))
                self.assert_error(self.read_report(), "non-empty Istanbul file map")

    def test_missing_or_invalid_statement_counters_are_rejected(self):
        for counter in [None, [], "invalid"]:
            with self.subTest(counter=counter):
                entry = self.entry("src/a.ts", [1])
                entry["s"] = counter
                self.fixture.write_text(json.dumps({entry["path"]: entry}))
                self.assert_error(self.read_report(), "s must be an object")
        entry = self.entry("src/a.ts", [1])
        del entry["s"]
        self.fixture.write_text(json.dumps({entry["path"]: entry}))
        self.assert_error(self.read_report(), "s must be an object")

    def test_invalid_hit_counts_are_rejected(self):
        for hit in [-1, 0.5, "1", True, None, 2**53]:
            with self.subTest(hit=hit):
                self.write_report({"src/a.ts": [hit]})
                self.assert_error(self.read_report("0"), "non-negative integer hit counts")

    def test_statement_map_must_match_counter_ids(self):
        for statement_map in [None, {}, {"1": {}}]:
            with self.subTest(statement_map=statement_map):
                entry = self.entry("src/a.ts", [1])
                entry["statementMap"] = statement_map
                self.fixture.write_text(json.dumps({entry["path"]: entry}))
                self.assert_error(self.read_report(), "statementMap and s do not match")

    def test_path_mismatch_and_duplicate_normalized_paths_are_rejected(self):
        entry = self.entry("src/a.ts", [1])
        self.fixture.write_text(json.dumps({str(self.root / "src/b.ts"): entry}))
        self.assert_error(self.read_report(), "file path mismatch")
        self.fixture.write_text(json.dumps({entry["path"]: entry, str(self.root) + "/./src/a.ts": entry}))
        self.assert_error(self.read_report(), "duplicate normalized file path")

    def test_non_statement_hit_counts_are_validated_if_present(self):
        for key, counters in [("f", {"0": -1}), ("b", {"0": [1, -1]}), ("b", {"0": 1})]:
            with self.subTest(key=key, counters=counters):
                entry = self.entry("src/a.ts", [1])
                entry[key] = counters
                self.fixture.write_text(json.dumps({entry["path"]: entry}))
                self.assert_error(self.read_report(), "coverage report validation failed")

    def test_zero_statements_are_na_alongside_measurable_files(self):
        self.write_report({"src/a.ts": [1], "src/types.ts": []})
        result = self.read_report()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("N/A src/types.ts (no executable statements)", result.stdout)
        self.assertNotIn("PASS 100.0% src/types.ts", result.stdout)

    def test_only_zero_statement_targets_cannot_pass(self):
        self.write_report({"src/a.ts": [1], "src/types.ts": []})
        result = self.read_report("80", "src/types.ts")
        self.assert_error(result, "no statements to evaluate")
        self.assertIn("N/A src/types.ts", result.stdout)
        self.write_report({"src/types.ts": []})
        self.assert_error(self.read_report("0"), "no statements to evaluate")


if __name__ == "__main__":
    unittest.main()
