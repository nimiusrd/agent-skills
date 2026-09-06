---
name: devcontainer-bootstrap
license: MIT
description: "Node・Python・Rust リポジトリへの Dev Container 導入・更新を支援する。スタック判定、テンプレート生成、既存設定を優先する安全マージ、任意の開発ツールと CI 追加に使用する。"
---

# devcontainer-bootstrap

## ワークフロー
1. リポジトリルートと既存 `.devcontainer/`、バージョン指定ファイルを確認する。
2. `scripts/detect_stack.sh <repo>` で `node|python|rust|unknown` を判定する。複数スタックや未対応構成では、目的に合うスタックを選び `--stack` を指定する。判断材料が不足する場合だけユーザーに確認する。
3. 新規作成・overwrite では下記の方針でイメージタグを選び、`--image-tag` に渡す。既存設定の safe 更新は image/build と Dockerfile を保持する。
4. 対象リポジトリを作業ディレクトリとして `scripts/apply_devcontainer.sh` を実行する。Python 3.8 以上が必要（`python3` を優先、無ければ Python 3 の `python`）。jq は不要。
5. 差分、バックアップ先、手動調整が必要な点を報告する。Docker が利用可能なら、依頼の範囲に応じてビルド・起動を確認し、生成のみか実行まで検証したかを区別する。

## 実行オプション
- `--stack auto|node|python|rust`（既定 `auto`）
- `--package-manager npm|pnpm|yarn`（Node 用）。未指定なら safe では既存 `remoteEnv.PACKAGE_MANAGER` を保持し、それ以外は `npm`。明示指定は既存値を更新する。
- `--mode safe|overwrite`（既定 `safe`）
  - safe: extensions を重複なく追加し、settings/features は既存値を優先して不足分を補完する。既存 image/build、Dockerfile、`postCreate.sh` は保持する。
  - overwrite: `devcontainer.json` と Dockerfile、専用 bootstrap スクリプトをテンプレートで置換する。その他の既存ファイルは保持する。
- `--include-tools true|false`（既定 `false`）。true は全モードで git / github-cli feature を補完する。false は既存 feature を削除しない。
- `--add-ci true|false`（既定 `false`）。true は `.github/workflows/devcontainer-bootstrap.yml` を生成する。safe は既存 workflow を保持、overwrite はバックアップ後に置換する。
- `--image-tag <tag>`: 新規作成・overwrite 用の確認済み固定タグ。JSON の image と生成 Dockerfile の FROM に反映する。`latest` は不可。既存設定を持つ safe 更新で指定すると、変更前に停止する。

```bash
# 対象リポジトリで実行。スクリプトパスはインストール先に置き換える。
bash /path/to/devcontainer-bootstrap/scripts/apply_devcontainer.sh --mode safe
bash /path/to/devcontainer-bootstrap/scripts/apply_devcontainer.sh --stack node --package-manager pnpm --image-tag 22 --mode overwrite --include-tools true --add-ci true
```

## イメージタグの選択
スクリプトはプロジェクトのバージョン指定を自動解釈しない。エージェントが次の情報を読んで、制約に合うタグがレジストリに存在することを確認し、`--image-tag` に渡す。

- Node: `.nvmrc` → `.node-version` → `package.json` の `engines.node`。範囲・LTS エイリアスは互換な固定タグに解決する。[Node タグ一覧](https://mcr.microsoft.com/v2/devcontainers/typescript-node/tags/list)
- Python: `.python-version` → `pyproject.toml` の `requires-python` / Poetry の Python 制約。互換な major.minor タグを選ぶ。[Python タグ一覧](https://mcr.microsoft.com/v2/devcontainers/python/tags/list)
- Rust: `rust-toolchain.toml` / `rust-toolchain`、`Cargo.toml` の `rust-version` を確認する。[Rust タグ一覧](https://mcr.microsoft.com/v2/devcontainers/rust/tags/list)

指定がなければ適切な安定版を確認する。確認できなければその制限を報告する。スクリプト単体でタグを省略した場合はバンドル値（Node 24 / Python 3.14 / Rust 1）を使うため、これを最新・プロジェクト互換と断定しない。

## 安全更新と postCreate
- 更新内容を一時領域で構成・検証してから、既存 `.devcontainer/` を `.devcontainer.bak-<一意ID>/` にバックアップして反映する。通常の反映エラーでは元のディレクトリへ戻す。強制終了・電源断時はバックアップから復元する。
- 既存 `devcontainer.json` は strict JSON のみ対応。JSONC（コメント・末尾カンマ）や更新対象の symlink は、既存ファイルを変えずに停止する。JSONC を無断で変換せず、必要な項目だけを直接編集してコメントを保持する。
- 共通処理は `.devcontainer/bootstrap-postCreate.sh` に配置する。safe で同名ファイルに異なる内容がある場合は上書きせず停止する。
- 文字列コマンドの後に成功時だけ bootstrap を実行する。配列は argv として各引数を shell quote して同様に合成する。既存オブジェクトは各値を保持し、`devcontainer-bootstrap` キーを追加する。この形式では各処理は並列実行になるため、既存処理が依存インストールなどで競合する場合は順序を確認して個別に構成する。
- 同じオプションで再適用してもコマンドや拡張を重複追加しない。bootstrap の依存導入はベストエフォートであり、成功ログだけで依存導入の成功を判断しない。

モード選択・復旧の詳細は [docs/decision-guide.md](docs/decision-guide.md) を参照。回帰検証は `python3 -m unittest discover -s /path/to/devcontainer-bootstrap/tests -v`。
