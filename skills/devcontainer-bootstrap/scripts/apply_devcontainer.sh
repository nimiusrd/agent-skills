#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 全モードを同じ実装で処理する。対象を書き換える前に実行環境を確認。
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1 && python -c 'import sys; sys.exit(sys.version_info < (3, 8))'; then
  PYTHON_BIN="$(command -v python)"
else
  echo 'ERROR: Python 3.8 以上が必要です（python3 または python）。' >&2
  exit 1
fi
"$PYTHON_BIN" -c 'import sys; sys.exit("ERROR: Python 3.8 以上が必要です") if sys.version_info < (3, 8) else None'
exec "$PYTHON_BIN" "${SCRIPT_DIR}/apply_devcontainer.py" "$@"
