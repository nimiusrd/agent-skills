# DevContainer Bootstrap Decision Guide

## 判定ルール
- **node**: `package.json`
- **python**: `pyproject.toml` または `requirements.txt`
- **rust**: `Cargo.toml`
- **その他/複数命中**: `unknown` とする → `--stack` を明示（自動選択しない）

## safe / overwrite の使い分け
- **safe**（推奨デフォルト）
  - 既存 `.devcontainer/` があれば **必ず** `.devcontainer.bak-<timestamp>/` にバックアップ
  - `devcontainer.json` は extensions/settings/features/postCreateCommand をマージ（`jq` 無しでも postCreate だけは確実に追加）
  - 既存 Dockerfile は保持し、テンプレートは補完用途で追加のみ
  - 既存の GitHub Actions がある場合、workflow はバックアップしてスキップ（壊さない）
- **overwrite**
  - テンプレートの `devcontainer.json` と `Dockerfile` をそのまま配置
  - `.devcontainer/` はバックアップ後に置換
  - workflow も置換（バックアップを残す）

## バックアップ方針
- `.devcontainer/` が存在する場合は必ず `cp -a` で `.devcontainer.bak-<timestamp>/` を作成してから更新
- workflow 既存時は `<file>.bak-<timestamp>` を作成
- バックアップ先をログで必ず報告

## よくある罠と対処
- **Docker Desktop / デーモン未起動**: devcontainer build で失敗する。Docker を起動して再実行。
- **postCreate が遅い/失敗する**: ログを確認し、必要なら `postCreate.sh` 内の install コマンドを短縮。失敗しても非致命（スクリプトは `|| true`）。
- **複数スタック混在 / go.mod のみ**: detect は `unknown` を返す。必ず `--stack` を明示して実行（例: node+rust 混在など）。
- **VS Code 拡張が足りない**: `customizations.vscode.extensions` に追加。safe ならマージで壊れにくい。
- **features 競合**: safe はオブジェクトマージ。上書きされたくない場合は手動で確認し、バックアップから比較する。
- **CI が不要**: `--add-ci false`（default）。既存 workflow を守りたい場合は safe を選択。

## VS Code 向け設定の場所
- 推奨設定・拡張は `customizations.vscode` に置く（参考: [Supporting tools](https://containers.dev/supporting#visual-studio-code)）。
- stack 別テンプレートに最小設定を含めている。safe モードでは既存設定をマージし、`postCreateCommand` に `.devcontainer/postCreate.sh` を追加するだけで済む。

## Node イメージタグの選び方
- ベースは `mcr.microsoft.com/devcontainers/typescript-node` を使用。
- **latest は避ける**。安定タグとしてメジャー番号タグ（例: `24`）を選択する。
- 新しい LTS に上げる場合はテンプレートの `image` をメジャー番号タグへ更新し、CI が通ることを確認する。
