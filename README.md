# agent-skills

AI コーディングエージェント向けスキルコレクション。

## インストール

```bash
npx skills add nimiusrd/agent-skills
```

特定のスキルだけをインストールする場合:

```bash
npx skills add nimiusrd/agent-skills --skill devcontainer-bootstrap
npx skills add nimiusrd/agent-skills --skill test-generator
npx skills add nimiusrd/agent-skills --skill property-test-generator
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
| [devcontainer-bootstrap](skills/devcontainer-bootstrap/) | Dev Container を最短で導入/更新するブートストラップ（node/python/rust 対応） |
| [test-generator](skills/test-generator/) | 変更ファイルに対するテストを自動生成し、カバレッジ 80%+ を目指す |
| [property-test-generator](skills/property-test-generator/) | プロパティベーステストを設計・生成（fast-check / hypothesis / proptest 対応） |
