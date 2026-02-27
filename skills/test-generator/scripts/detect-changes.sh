#!/usr/bin/env bash
# Detect changed source files that may need tests.
# Usage: detect-changes.sh [base-branch]
# Outputs one file path per line.
set -euo pipefail

BASE="${1:-$(git rev-parse --abbrev-ref HEAD@{upstream} 2>/dev/null | sed 's|/.*||' || echo main)}"

# Merge-base so we only see branch-specific changes
MERGE_BASE=$(git merge-base "$BASE" HEAD 2>/dev/null || echo "$BASE")

# Collect changed/added files (staged + unstaged + untracked new files)
declare -A seen
while IFS= read -r -d '' f; do
  [ -n "$f" ] || continue
  [ -f "$f" ] || continue

  if [ -n "${seen[$f]+x}" ]; then
    continue
  fi
  seen["$f"]=1

  case "$f" in
    *.test.ts|*.spec.ts|*.test.tsx|*.spec.tsx|*.test.js|*.spec.js|*.test.jsx|*.spec.jsx|*.test.rs|*.spec.rs)
      continue
      ;;
  esac

  case "$f" in
    *.css|*.scss|*.less|*.svg|*.png|*.jpg|*.gif|*.ico|*.md|*.json|*.lock|*.toml|*.yaml|*.yml)
      continue
      ;;
  esac

  case "$f" in
    *node_modules*|*dist*|*build*|*target*|*.git*|*__mocks__*|*test/setup*)
      continue
      ;;
  esac

  case "$f" in
    *.ts|*.tsx|*.js|*.jsx|*.rs)
      printf '%s\n' "$f"
      ;;
  esac
done < <(
  git diff --name-only -z --diff-filter=ACMR "$MERGE_BASE" HEAD 2>/dev/null || true
  git diff --name-only -z --diff-filter=ACMR 2>/dev/null || true
  git diff --name-only -z --diff-filter=ACMR --cached 2>/dev/null || true
)
