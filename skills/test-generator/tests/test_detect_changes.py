"""変更ソース列挙 CLI の回帰テスト（Python 標準ライブラリのみ）。"""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "detect-changes.sh"
BASH = os.environ.get("TEST_BASH", "/bin/bash")
GIT = shutil.which("git")


class DetectChangesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="detect-changes-test-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.env = os.environ.copy()
        self.env.update({
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
        })
        self.git("init", "--quiet", "--initial-branch=main")
        self.write("src/existing.ts", "export const value = 1;\n")
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "baseline")
        self.git("checkout", "--quiet", "-b", "feature")

    def git(self, *args):
        return subprocess.run(
            [GIT, *args], cwd=self.repo, env=self.env, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def write(self, name, content="export const value = 1;\n"):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def detect(self, *args, cwd=None, env=None):
        return subprocess.run(
            [BASH, str(SCRIPT), *args], cwd=cwd or self.repo,
            env=env or self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def paths(self, *args):
        result = self.detect("--null", *args)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        return [os.fsdecode(path) for path in result.stdout.split(b"\0") if path]

    def test_committed_staged_unstaged_untracked_and_deduplication(self):
        self.write("src/committed.ts")
        self.write("src/existing.ts", "export const value = 2;\n")
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "feature changes")
        self.write("src/staged.tsx")
        self.write("src/existing.ts", "export const value = 3;\n")
        self.git("add", ".")
        self.write("src/existing.ts", "export const value = 4;\n")
        self.write("src/untracked.jsx")
        self.assertCountEqual(self.paths(), [
            "src/committed.ts", "src/existing.ts", "src/staged.tsx", "src/untracked.jsx",
        ])

    def test_default_ignores_feature_tracking_branch(self):
        self.write("src/committed.ts")
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "feature changes")
        self.git("remote", "add", "origin", str(self.repo / "unused-remote"))
        self.git("update-ref", "refs/remotes/origin/feature", "HEAD")
        self.git("config", "branch.feature.remote", "origin")
        self.git("config", "branch.feature.merge", "refs/heads/feature")
        self.assertEqual(self.paths(), ["src/committed.ts"])

    def test_origin_head_has_priority_and_explicit_base_overrides_it(self):
        self.write("src/committed.ts")
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "feature changes")
        self.git("update-ref", "refs/remotes/origin/trunk", "HEAD")
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
        self.assertEqual(self.paths(), [])
        self.assertEqual(self.paths("main"), ["src/committed.ts"])

    def test_empty_tree_produces_no_output(self):
        result = self.detect()
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(result.stdout, b"")

    def test_invalid_ref_fails_without_partial_output(self):
        self.write("src/untracked.ts")
        result = self.detect("does-not-exist")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"does-not-exist", result.stderr)

    def test_not_a_repository_fails_with_diagnostic(self):
        with tempfile.TemporaryDirectory() as outside:
            result = self.detect(cwd=outside)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr)

    def test_failed_file_enumeration_is_not_silently_ignored(self):
        self.write("src/untracked.ts")
        bindir = self.repo / "fake-bin"
        bindir.mkdir()
        fake_git = bindir / "git"
        fake_git.write_text(
            '#!/bin/sh\n'
            'if [ "$1" = "$FAIL_GIT_COMMAND" ]; then echo "fixture git failure" >&2; exit 17; fi\n'
            'exec "$REAL_GIT" "$@"\n'
        )
        fake_git.chmod(0o755)
        env = {**self.env, "PATH": str(bindir) + os.pathsep + self.env["PATH"], "REAL_GIT": GIT}
        for command in ["diff", "ls-files"]:
            with self.subTest(command=command):
                result = self.detect(env={**env, "FAIL_GIT_COMMAND": command})
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, b"")
                self.assertIn(b"fixture git failure", result.stderr)

    def test_paths_with_spaces_and_newlines_and_repository_relative_output(self):
        names = ["src/a space.ts", "src/a\nnewline.jsx", "src/[pattern].tsx"]
        for name in names:
            self.write(name)
        self.assertCountEqual(self.paths(), names)
        result = self.detect("--null", cwd=self.repo / "src")
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertCountEqual([os.fsdecode(p) for p in result.stdout.split(b"\0") if p], names)

    def test_filters_components_and_test_config_generated_names(self):
        sources = [
            "src/builder.ts", "src/targeting.tsx", "src/distribution.jsx", "src/config/runtime.ts",
            "src/building/index.rs", "src/testimonial.js", "src/widget.tsx",
            "src/api.config.data/runtime.ts",
        ]
        excluded = [
            "node_modules/pkg/a.ts", "dist/a.js", "build/a.ts", "target/a.rs", "coverage/a.ts",
            "src/generated/a.ts", "src/__tests__/a.ts", "src/__mocks__/a.ts", "test/setup.ts",
            "tests/helper.ts", "src/a.property.test.ts", "src/a.spec.jsx", "src/a.test.tsx",
            "vite.config.ts", "eslint.config.js", "config/build.ts", "configs/tool.ts",
            ".storybook/main.ts", "src/a.generated.ts", "src/types.d.ts", "docs/readme.md",
        ]
        for name in sources + excluded:
            self.write(name)
        self.assertCountEqual(self.paths(), sources)

    def test_ignored_and_deleted_files_are_not_reported(self):
        self.write(".gitignore", "ignored/\n")
        self.write("ignored/a.ts")
        (self.repo / "src/existing.ts").unlink()
        self.git("add", "-u")
        self.assertEqual(self.paths(), [])

    def test_default_line_output_preserves_spaces(self):
        self.write("src/a space.ts")
        result = self.detect("main")
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(result.stdout, b"src/a space.ts\n")

    def test_master_fallback_and_missing_default_base(self):
        self.git("branch", "-m", "main", "master")
        self.write("src/untracked.ts")
        self.assertEqual(self.paths(), ["src/untracked.ts"])
        self.git("branch", "-D", "master")
        result = self.detect()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr)
        self.assertEqual(self.paths("HEAD"), ["src/untracked.ts"])

    def test_unrelated_base_fails_instead_of_comparing_unrelated_trees(self):
        self.git("checkout", "--quiet", "--orphan", "unrelated")
        self.git("commit", "--quiet", "-m", "independent root")
        self.git("checkout", "--quiet", "feature")
        result = self.detect("unrelated")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"unrelated", result.stderr)


if __name__ == "__main__":
    unittest.main()
