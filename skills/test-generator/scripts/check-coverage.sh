#!/usr/bin/env bash
# 今回のテスト実行で生成した Istanbul JSON だけを検査する。
# Usage: check-coverage.sh [threshold=80] [files...] [-- command args...]
# 例: check-coverage.sh 80 src/main.ts -- npm run test --
set -euo pipefail

THRESHOLD="${1-80}"
if ! [[ "$THRESHOLD" =~ ^([0-9]{1,2}([.][0-9]+)?|100([.]0+)?)$ ]]; then
  echo "ERROR: threshold must be a number between 0 and 100." >&2
  exit 1
fi
if [ "$#" -gt 0 ]; then
  shift
fi

TARGET_FILES=()
CUSTOM_COMMAND=()
while [ "$#" -gt 0 ]; do
  if [ "$1" = "--" ]; then
    shift
    if [ "$#" -eq 0 ]; then
      echo "ERROR: a command is required after --." >&2
      exit 1
    fi
    CUSTOM_COMMAND=("$@")
    break
  fi
  TARGET_FILES[${#TARGET_FILES[@]}]="$1"
  shift
done

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node is required to validate the coverage report." >&2
  exit 1
fi

if [ "${#CUSTOM_COMMAND[@]}" -gt 0 ]; then
  TEST_COMMAND=("${CUSTOM_COMMAND[@]}")
elif [ -x "./node_modules/.bin/vitest" ]; then
  TEST_COMMAND=("./node_modules/.bin/vitest" run)
elif command -v vitest >/dev/null 2>&1; then
  TEST_COMMAND=("$(command -v vitest)" run)
elif [ -f Cargo.toml ]; then
  echo "ERROR: Rust coverage is not supported by this Istanbul JSON checker." >&2
  echo "Use the project's cargo-llvm-cov coverage command instead." >&2
  exit 1
else
  echo "ERROR: vitest executable not found. Install project dependencies and retry." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COVERAGE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/test-generator-coverage.XXXXXX")"
COVERAGE_FILE="$COVERAGE_DIR/coverage-final.json"
# 成功・失敗のどちらでも今回の生成先を表示し、調査用に保持する。
echo "Coverage report: $COVERAGE_FILE"
# 既存 npm script の --coverage と同じ boolean option を重ねない。
if "${TEST_COMMAND[@]}" --coverage.enabled=true --coverage.reporter=json "--coverage.reportsDirectory=$COVERAGE_DIR"; then
  :
else
  status=$?
  echo "ERROR: test command failed (exit $status); coverage was not evaluated." >&2
  exit "$status"
fi

if [ ! -f "$COVERAGE_FILE" ]; then
  echo "ERROR: this test run did not create $COVERAGE_FILE" >&2
  echo "Check the coverage provider and whether the command forwards Vitest options." >&2
  exit 1
fi

# Bash 3.2 の nounset は空配列の通常展開を拒否するため、未要素時は展開しない。
node "$SCRIPT_DIR/read-coverage.cjs" "$COVERAGE_FILE" "$THRESHOLD" ${TARGET_FILES[@]+"${TARGET_FILES[@]}"}
