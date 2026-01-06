#!/usr/bin/env bash
set -euo pipefail

echo "[postCreate] start"

PM="${PACKAGE_MANAGER:-npm}"

if [[ -f "package.json" ]]; then
  echo "[postCreate] node detected (package.json)"
  case "$PM" in
    pnpm) (pnpm install || true) ;;
    yarn) (yarn install || true) ;;
    npm) (npm install || true) ;;
  esac
fi

if [[ -f "pyproject.toml" || -f "requirements.txt" ]]; then
  echo "[postCreate] python detected (pyproject.toml/requirements.txt)"
  python -m pip install --upgrade pip setuptools wheel || true
  if [[ -f "requirements.txt" ]]; then
    python -m pip install -r requirements.txt || true
  fi
  if [[ -f "pyproject.toml" && ! -f "requirements.txt" ]]; then
    # best-effort editable install
    python -m pip install -e . || true
  fi
fi

if [[ -f "Cargo.toml" ]]; then
  echo "[postCreate] rust detected (Cargo.toml)"
  cargo fetch || true
fi

echo "[postCreate] done"
