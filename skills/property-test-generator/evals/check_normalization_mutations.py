"""評価担当用。追加されたHypothesisテストだけの誤実装検出力を調べる。

実行担当には渡さない。候補のfixtureディレクトリを引数に指定する。
Hypothesisを導入したPythonで実行する。入力は変更せず、一時コピーで検証する。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

MUTATIONS = {
    "constant": 'return ""',
    "lowercase": 'return " ".join(text.split()).lower()',
    "reverse": 'return " ".join(reversed(text.split()))',
    "ascii_space_only": 'return " ".join(word for word in text.split(" ") if word)',
}


def run_tests(project, pattern):
    try:
        result = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-v"],
            cwd=project, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60,
        )
        match = re.search(r"Ran (\d+) tests?", result.stdout)
        return {"exit_code": result.returncode, "tests_run": int(match[1]) if match else 0, "output": result.stdout}
    except subprocess.TimeoutExpired:
        return {"exit_code": None, "tests_run": 0, "output": "timeout after 60 seconds"}


def check(project):
    original = Path(__file__).parent / "files" / "normalization"
    for name in ("normalizer.py", "tests/test_normalizer.py"):
        if (project / name).read_bytes() != (original / name).read_bytes():
            raise ValueError(f"製品コードまたは既存テストが変更されています: {name}")
    if not (project / "tests/test_properties_normalizer.py").is_file():
        raise ValueError("tests/test_properties_normalizer.py がありません")
    results = {}
    for name, body in [("baseline", None), *MUTATIONS.items()]:
        with tempfile.TemporaryDirectory(prefix="pbt-mutation-") as temp:
            target = Path(temp) / "project"
            shutil.copytree(project, target, ignore=shutil.ignore_patterns("__pycache__", ".hypothesis", ".venv"))
            if body is not None:
                (target / "normalizer.py").write_text("def normalize_words(text):\n    " + body + "\n")
            result = run_tests(target, "test_properties_normalizer.py")
            result["passed"] = result["tests_run"] > 0 and (
                result["exit_code"] == 0 if body is None else
                result["exit_code"] == 1 and re.search(r"FAILED \(failures=[1-9]\d*\)", result["output"]) is not None
            )
            results[name] = result
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    results = check(args.project.resolve())
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(value["passed"] for value in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
