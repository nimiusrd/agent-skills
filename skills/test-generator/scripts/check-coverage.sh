#!/usr/bin/env bash
# Run tests with coverage and report per-file coverage for specified files.
# Usage: check-coverage.sh <threshold> [file1 file2 ...]
# If no files specified, reports all. Exit 0 if all files meet threshold, 1 otherwise.
set -euo pipefail

THRESHOLD="${1:-80}"
if ! [[ "$THRESHOLD" =~ ^([0-9]{1,2}([.][0-9]+)?|100([.]0+)?)$ ]]; then
  echo "ERROR: threshold must be a number between 0 and 100."
  exit 1
fi
shift || true
TARGET_FILES=("$@")

detect_runner() {
  if [ -f "vitest.config.ts" ] || [ -f "vitest.config.js" ] || \
     ([ -f "vite.config.ts" ] && grep -q "test" vite.config.ts 2>/dev/null); then
    echo "vitest"
  elif [ -f "Cargo.toml" ]; then
    echo "cargo"
  else
    echo "unknown"
  fi
}

RUNNER=$(detect_runner)

case "$RUNNER" in
  vitest)
    if [ -x "./node_modules/.bin/vitest" ]; then
      VITEST_BIN="./node_modules/.bin/vitest"
    elif command -v vitest >/dev/null 2>&1; then
      VITEST_BIN="$(command -v vitest)"
    else
      echo "ERROR: vitest executable not found."
      echo "Install project dependencies and retry."
      exit 1
    fi

    "$VITEST_BIN" run --coverage >/dev/null 2>&1 || true
    COV_FILE="coverage/coverage-final.json"
    if [ ! -f "$COV_FILE" ]; then
      echo "ERROR: Coverage file not found at $COV_FILE"
      echo "Ensure @vitest/coverage-v8 or @vitest/coverage-istanbul is installed."
      exit 1
    fi
    echo "=== Coverage Report ==="
    echo ""
    THRESHOLD="$THRESHOLD" node -e '
      const path = require("path");
      const [covFile, ...targets] = process.argv.slice(1);
      const threshold = Number(process.env.THRESHOLD);
      const cov = require(path.resolve(covFile));
      let allPass = true;
      for (const [file, data] of Object.entries(cov)) {
        const rel = file.replace(process.cwd() + "/", "");
        if (targets.length > 0 && !targets.some(t => rel.includes(t))) continue;
        const s = data.s || {};
        const total = Object.keys(s).length;
        const covered = Object.values(s).filter(v => v > 0).length;
        const pct = total > 0 ? ((covered / total) * 100).toFixed(1) : "100.0";
        const status = Number(pct) >= threshold ? "PASS" : "FAIL";
        if (status === "FAIL") allPass = false;
        console.log(status + " " + pct + "% " + rel);
      }
      process.exit(allPass ? 0 : 1);
    ' "$COV_FILE" "${TARGET_FILES[@]}" 2>/dev/null
    ;;
  cargo)
    echo "Rust coverage requires cargo-llvm-cov. Run:"
    echo "  cargo llvm-cov --json | cargo llvm-cov report"
    echo "See AGENTS.md for project-specific Rust coverage commands."
    exit 1
    ;;
  *)
    echo "ERROR: Could not detect test runner."
    echo "Supported: vitest, cargo"
    exit 1
    ;;
esac
