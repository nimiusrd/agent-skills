# agent-skills

AI コーディングエージェント向けスキルコレクション。

## インストール

```bash
npx skills add nimiusrd/agent-skills
```

特定のスキルだけをインストールする場合:

```bash
npx skills add nimiusrd/agent-skills --skill commit-and-pr
npx skills add nimiusrd/agent-skills --skill devcontainer-bootstrap
npx skills add nimiusrd/agent-skills --skill property-test-generator
npx skills add nimiusrd/agent-skills --skill refactoring
npx skills add nimiusrd/agent-skills --skill test-generator
```

特定のエージェントに対してインストールする場合:

```bash
npx skills add nimiusrd/agent-skills -a cursor
npx skills add nimiusrd/agent-skills -a claude-code
```

詳しくは [skills.sh](https://skills.sh/) を参照。

## 含まれるスキル

| スキル | 説明 |
|--------|------|
| [commit-and-pr](skills/commit-and-pr/) | 変更をコミットして GitHub Pull Request を作成する一括ワークフロー |
| [devcontainer-bootstrap](skills/devcontainer-bootstrap/) | Dev Container を最短で導入/更新するブートストラップ（node/python/rust 対応） |
| [property-test-generator](skills/property-test-generator/) | プロパティベーステストを設計・生成（fast-check / hypothesis / proptest 対応） |
| [refactoring](skills/refactoring/) | 外部仕様を変えずにコードの内部構造を改善するリファクタリング支援 |
| [test-generator](skills/test-generator/) | 変更ファイルに対するテストを自動生成し、カバレッジ 80%+ を目指す |
