#!/usr/bin/env bash
# Detect changed source files that may need tests.
# Usage: detect-changes.sh [base-branch]
# Outputs one file path per line.
set -euo pipefail

BASE="${1:-$(git rev-parse --abbrev-ref HEAD@{upstream} 2>/dev/null | sed 's|/.*||' || echo main)}"

# Merge-base so we only see branch-specific changes
MERGE_BASE=$(git merge-base "$BASE" HEAD 2>/dev/null || echo "$BASE")

# Collect changed/added files (staged + unstaged + untracked new files)
{
  git diff --name-only --diff-filter=ACMR "$MERGE_BASE" HEAD 2>/dev/null
  git diff --name-only --diff-filter=ACMR 2>/dev/null
  git diff --name-only --diff-filter=ACMR --cached 2>/dev/null
} | sort -u | while IFS= read -r f; do
  # Skip if file no longer exists
  [ -f "$f" ] || continue
  # Skip test files themselves
  [[ "$f" =~ \.(test|spec)\.(ts|tsx|js|jsx|rs)$ ]] && continue
  # Skip config, assets, styles, markdown, lock files
  [[ "$f" =~ \.(css|scss|less|svg|png|jpg|gif|ico|md|json|lock|toml|yaml|yml)$ ]] && continue
  # Skip common non-testable paths
  [[ "$f" =~ (node_modules|dist|build|target|\.git|__mocks__|test/setup) ]] && continue
  # Keep only source files
  [[ "$f" =~ \.(ts|tsx|js|jsx|rs)$ ]] && printf '%s\n' "$f"
done
