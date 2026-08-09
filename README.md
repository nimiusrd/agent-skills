# agent-skills

AI コーディングエージェント向けスキルコレクション。

## 前提条件

- GitHub CLI 2.90.0 以降
- GitHub CLI の認証（`gh auth login`）

`gh skill` はPublic Previewです。仕様は将来変更される可能性があります。

## インストール

`gh skill` はGitHub CLIのスキル管理コマンドです。`gh skills` という複数形のエイリアスも利用できます。

すべてのスキルをCodexのユーザースコープへインストールする場合:

```bash
gh skill install nimiusrd/agent-skills --all --agent codex --scope user
```

特定のスキルだけをインストールする場合:

```bash
gh skill install nimiusrd/agent-skills cleanup-package-json --agent codex --scope user
gh skill install nimiusrd/agent-skills commit-and-pr --agent codex --scope user
gh skill install nimiusrd/agent-skills devcontainer-bootstrap --agent codex --scope user
gh skill install nimiusrd/agent-skills property-test-generator --agent codex --scope user
gh skill install nimiusrd/agent-skills refactoring --agent codex --scope user
gh skill install nimiusrd/agent-skills test-generator --agent codex --scope user
```

`codex` は対象エージェントに合わせて変更できます（例: `claude-code`, `cursor`, `github-copilot`）。プロジェクト単位で管理する場合は `--scope project` を指定してください。

## 確認・更新

```bash
# インストール済みスキルを一覧表示
gh skill list

# 更新の有無だけ確認
gh skill update --dry-run

# すべてのスキルを更新
gh skill update --all

# インストール前に内容をプレビュー
gh skill preview nimiusrd/agent-skills refactoring
```

## 公開

公開前に、Agent Skills仕様への適合性を検証します。

```bash
gh skill publish --dry-run
```

検証に成功したら、SemVer形式のタグを指定してGitHub Releaseを作成します。

```bash
gh skill publish --tag v1.0.0
```

## 含まれるスキル

| スキル | 説明 |
|--------|------|
| [cleanup-package-json](skills/cleanup-package-json/) | package.json のスクリプト整理・未使用依存削除・ロックファイル再生成 |
| [commit-and-pr](skills/commit-and-pr/) | 変更をコミットして GitHub Pull Request を作成する一括ワークフロー |
| [devcontainer-bootstrap](skills/devcontainer-bootstrap/) | Dev Container を最短で導入/更新するブートストラップ（node/python/rust 対応） |
| [property-test-generator](skills/property-test-generator/) | プロパティベーステストを設計・生成（fast-check / hypothesis / proptest 対応） |
| [refactoring](skills/refactoring/) | 外部仕様を変えずにコードの内部構造を改善するリファクタリング支援 |
| [test-generator](skills/test-generator/) | 変更ファイルに対するテストを自動生成し、カバレッジ 80%+ を目指す |
