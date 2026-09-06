"""一時リポジトリで既存資産保持・コマンド実行・失敗時の不変性を検証。"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/apply_devcontainer.sh"
spec = importlib.util.spec_from_file_location("bootstrap", SCRIPT.with_suffix(".py"))
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dev = self.root / ".devcontainer"

    def run_apply(self, *args, success=True, env=None):
        result = subprocess.run(["/bin/bash", str(SCRIPT), "--stack", "node", *args], cwd=self.root, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def existing(self, data):
        self.dev.mkdir()
        (self.dev / "devcontainer.json").write_text(json.dumps(data))
        (self.dev / "postCreate.sh").write_text("user script\n")
        (self.dev / "Dockerfile").write_text("FROM user-image\n")

    def read(self):
        return json.loads((self.dev / "devcontainer.json").read_text())

    def snapshot(self):
        return {str(p.relative_to(self.dev)): p.read_bytes() for p in self.dev.rglob("*") if p.is_file()}

    def test_safe_preserves_settings_features_scripts_env_and_repeats(self):
        self.existing({"image": "user-image", "customizations": {"vscode": {"settings": {"editor.formatOnSave": False}}}, "features": {"ghcr.io/devcontainers/features/git:1": {"version": "2.0"}}, "remoteEnv": {"PACKAGE_MANAGER": "yarn"}, "postCreateCommand": "echo old"})
        self.run_apply("--include-tools", "true")
        data = self.read()
        self.assertFalse(data["customizations"]["vscode"]["settings"]["editor.formatOnSave"])
        self.assertEqual(data["features"]["ghcr.io/devcontainers/features/git:1"], {"version": "2.0"})
        self.assertEqual(data["remoteEnv"]["PACKAGE_MANAGER"], "yarn")
        self.assertEqual((self.dev / "postCreate.sh").read_text(), "user script\n")
        self.assertEqual((self.dev / "Dockerfile").read_text(), "FROM user-image\n")
        before = self.snapshot()
        self.run_apply("--include-tools", "true")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(len(list(self.root.glob(".devcontainer.bak-*"))), 2)

    def test_array_arguments_execute_exactly_once_and_bootstrap_runs(self):
        expected = ["space value", "$(touch bad)", "a'b", "x;y", ""]
        self.existing({"postCreateCommand": [sys.executable, "-c", "import json,sys;open('args.json','w').write(json.dumps(sys.argv[1:]))", *expected]})
        self.run_apply()
        self.run_apply()
        result = subprocess.run(["/bin/sh", "-c", self.read()["postCreateCommand"]], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((self.root / "args.json").read_text()), expected)
        self.assertFalse((self.root / "bad").exists())
        self.assertEqual(result.stdout.count("[postCreate] start"), 1)

    def test_string_failure_does_not_run_bootstrap(self):
        self.existing({"postCreateCommand": "false # trailing comment"})
        self.run_apply()
        result = subprocess.run(["/bin/sh", "-c", self.read()["postCreateCommand"]], cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("[postCreate]", result.stdout)

    def test_object_commands_unchanged(self):
        original = {"first": "echo a", "second": ["printf", "%s", "b c"]}
        self.existing({"postCreateCommand": original})
        self.run_apply()
        self.run_apply()
        result = self.read()["postCreateCommand"]
        self.assertEqual({key: result[key] for key in original}, original)
        self.assertEqual(len(result), 3)

    def test_tools_in_new_safe_and_overwrite(self):
        for mode in ("safe", "overwrite"):
            with self.subTest(mode=mode):
                if self.dev.exists():
                    shutil.rmtree(self.dev)
                self.run_apply("--mode", mode, "--include-tools", "true", "--package-manager", "pnpm")
                self.assertEqual(len(self.read()["features"]), 2)
                self.assertEqual(self.read()["remoteEnv"]["PACKAGE_MANAGER"], "pnpm")

    def test_jsonc_fails_before_changing_existing_files(self):
        self.existing({})
        (self.dev / "devcontainer.json").write_text('{// comment\n"image":"old",}')
        before = self.snapshot()
        self.run_apply(success=False)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(list(self.root.glob(".devcontainer.bak-*")), [])

    def test_conflicting_managed_script_and_invalid_type_leave_existing_unchanged(self):
        self.existing({"postCreateCommand": 42})
        before = self.snapshot()
        self.run_apply(success=False)
        self.assertEqual(self.snapshot(), before)
        (self.dev / "devcontainer.json").write_text('{}')
        (self.dev / bootstrap.SCRIPT_NAME).write_text('user data')
        before = self.snapshot()
        self.run_apply(success=False)
        self.assertEqual(self.snapshot(), before)

    def test_python3_without_python_or_jq(self):
        bindir = self.root / "bin"
        bindir.mkdir()
        for name, target in (("python3", sys.executable), ("dirname", shutil.which("dirname"))):
            (bindir / name).symlink_to(target)
        self.run_apply(env={**os.environ, "PATH": str(bindir)})
        self.assertTrue((self.dev / "devcontainer.json").exists())

    def test_image_tag_applies_to_image_and_dockerfile(self):
        self.run_apply("--image-tag", "22")
        self.assertTrue(self.read()["image"].endswith(":22"))
        self.assertIn(":22", (self.dev / "Dockerfile").read_text())
        before = self.snapshot()
        self.run_apply("--image-tag", "24", success=False)
        self.assertEqual(self.snapshot(), before)

    def test_ci_failure_rolls_back_devcontainer(self):
        self.existing({"image": "old"})
        before = self.snapshot()
        args = type("Args", (), dict(stack="node", mode="safe", package_manager=None, include_tools="true", add_ci="true", image_tag=None))()
        replace = os.replace
        def fail_ci(src, dst):
            if str(dst).endswith("devcontainer-bootstrap.yml"):
                raise OSError("simulated CI failure")
            return replace(src, dst)
        with patch.object(bootstrap.os, "replace", side_effect=fail_ci):
            with self.assertRaises(OSError):
                bootstrap.apply(args, self.root)
        self.assertEqual(self.snapshot(), before)

    def test_existing_ci_safe_retained_overwrite_backed_up(self):
        workflow = self.root / ".github/workflows/devcontainer-bootstrap.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text("user workflow")
        self.run_apply("--add-ci", "true")
        self.assertEqual(workflow.read_text(), "user workflow")
        self.run_apply("--mode", "overwrite", "--add-ci", "true")
        self.assertIn("name: DevContainer Bootstrap", workflow.read_text())
        backups = list(workflow.parent.glob("*.bak-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "user workflow")


if __name__ == "__main__":
    unittest.main()
