#!/usr/bin/env bash
set -euo pipefail

# Detect repository stack: node | python | rust | unknown
# Rules:
# - node    : package.json
# - python  : pyproject.toml OR requirements.txt
# - rust    : Cargo.toml
# - multiple hits => unknown (force explicit stack selection)

ROOT="${1:-.}"

find_hit() {
  local pattern="$1"
  if [ -e "$ROOT/$pattern" ]; then
    return 0
  fi
  return 1
}

hits=()
find_hit "package.json" && hits+=("node")
find_hit "pyproject.toml" && hits+=("python")
find_hit "requirements.txt" && hits+=("python")
find_hit "Cargo.toml" && hits+=("rust")

if [ "${#hits[@]}" -gt 1 ]; then
  # normalize by unique values
  uniq_hits=()
  for h in "${hits[@]}"; do
    if [[ ! " ${uniq_hits[*]} " =~ " $h " ]]; then
      uniq_hits+=("$h")
    fi
  done
  hits=("${uniq_hits[@]}")
fi

if [ "${#hits[@]}" -eq 1 ]; then
  echo "${hits[0]}"
else
  echo "unknown"
fi
