#!/usr/bin/env bash
# テスト対象になり得る変更ソースを、リポジトリルート相対パスで出力する。
# Usage: detect-changes.sh [--null] [base-branch]
# 既定は 1 行 1 パス。改行を含むパスを扱う場合は --null を使用する。
set -euo pipefail

null_output=false
if [ "${1:-}" = '--null' ]; then
  null_output=true
  shift
fi
if [ "$#" -gt 1 ]; then
  printf 'Usage: detect-changes.sh [--null] [base-branch]\n' >&2
  exit 2
fi

repo_root=$(git rev-parse --show-toplevel) || exit 1
cd "$repo_root"

if [ "$#" -eq 1 ]; then
  base=$1
else
  # feature 自身を tracking する upstream は比較元にしない。
  base=$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null) || base=''
  if [ -z "$base" ]; then
    for candidate in refs/heads/main refs/heads/master refs/remotes/origin/main refs/remotes/origin/master; do
      if git rev-parse --verify --quiet "$candidate^{commit}" >/dev/null; then
        base=$candidate
        break
      fi
    done
  fi
  if [ -z "$base" ]; then
    printf 'detect-changes: 比較元が見つかりません。base-branch を明示してください。\n' >&2
    exit 1
  fi
fi

base_commit=$(git rev-parse --verify --end-of-options "$base^{commit}") || {
  printf 'detect-changes: 比較元を解決できません: %s\n' "$base" >&2
  exit 1
}
merge_base=$(git merge-base "$base_commit" HEAD) || {
  printf 'detect-changes: HEAD と比較元の共通祖先を取得できません: %s\n' "$base" >&2
  exit 1
}

changes=$(mktemp "${TMPDIR:-/tmp}/detect-changes.XXXXXX")
trap 'rm -f "$changes"' EXIT

# process substitution 内の失敗を見落とさないよう、列挙完了後に読み取る。
if ! git diff --name-only -z --diff-filter=ACMR "$merge_base" HEAD -- >"$changes" ||
  ! git diff --name-only -z --diff-filter=ACMR -- >>"$changes" ||
  ! git diff --name-only -z --diff-filter=ACMR --cached -- >>"$changes" ||
  ! git ls-files --others --exclude-standard -z -- >>"$changes"; then
  printf 'detect-changes: 変更ファイルの列挙に失敗しました。\n' >&2
  exit 1
fi

# macOS 標準 Bash 3.2 でも利用できる indexed array を使う。
seen=()
seen_count=0
while IFS= read -r -d '' path; do
  [ -f "$path" ] || continue
  case "/$path/" in
    */node_modules/*|*/dist/*|*/build/*|*/target/*|*/coverage/*|*/generated/*|*/.git/*|*/.next/*|*/.nuxt/*|*/__tests__/*|*/__mocks__/*|*/test/*|*/tests/*)
      continue ;;
  esac
  case "$path" in
    config/*|configs/*|.storybook/*)
      continue ;;
  esac
  case "${path##*/}" in
    *.test.*|*.spec.*|*.config.*|*.generated.*|*.d.ts|*.d.tsx)
      continue ;;
  esac
  case "$path" in
    *.ts|*.tsx|*.js|*.jsx|*.rs) ;;
    *) continue ;;
  esac

  duplicate=false
  for ((i = 0; i < seen_count; i++)); do
    if [ "${seen[$i]}" = "$path" ]; then
      duplicate=true
      break
    fi
  done
  if "$duplicate"; then continue; fi
  seen[$seen_count]=$path
  seen_count=$((seen_count + 1))
  if "$null_output"; then
    printf '%s\0' "$path"
  else
    printf '%s\n' "$path"
  fi
done <"$changes"
