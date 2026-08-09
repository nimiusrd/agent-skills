# agent-skills

AI コーディングエージェントの作業を再利用可能な手順としてまとめた、Agent Skills のコレクションです。

パッケージ整理、テスト生成、リファクタリング、Dev Container の導入、Pull Request の作成まで、日常的な開発作業に使えるスキルを収録しています。

## クイックスタート

### 前提条件

- GitHub CLI 2.90.0 以降
- GitHub CLI で認証済みであること（`gh auth login`）

すべてのスキルを、現在のプロジェクトで使うエージェントのプロジェクトスコープへインストールします。コマンドは対象プロジェクトのルートで実行してください。
`AGENT_NAME` は `gh skill install -h` で確認した値に置き換えてください。

```bash
gh skill install nimiusrd/agent-skills --all --agent AGENT_NAME --scope project
```

インストール後は、利用するエージェント上で次のように依頼できます。

```text
このブランチの変更にテストを追加して
```

## 収録スキル

| スキル | 用途 | 依頼例 |
|---|---|---|
| [cleanup-package-json](skills/cleanup-package-json/SKILL.md) | `package.json` のスクリプト整理、未使用依存の削除、ロックファイルの再生成 | 「package.json を整理して」 |
| [commit-and-pr](skills/commit-and-pr/SKILL.md) | 変更内容の確認、コミット、プッシュ、Pull Request 作成 | 「変更をコミットして PR を作って」 |
| [devcontainer-bootstrap](skills/devcontainer-bootstrap/SKILL.md) | Node.js、Python、Rust 向け Dev Container の導入・安全な更新 | 「このリポジトリに Dev Container を導入して」 |
| [property-test-generator](skills/property-test-generator/SKILL.md) | fast-check、Hypothesis、proptest を使ったプロパティベーステストの設計・生成 | 「変更した関数にプロパティテストを追加して」 |
| [refactoring](skills/refactoring/SKILL.md) | 外部仕様を維持したまま内部構造を改善 | 「このコードを振る舞いを変えずにリファクタリングして」 |
| [test-generator](skills/test-generator/SKILL.md) | 変更ファイルへのテスト追加とカバレッジ確認 | 「このブランチの変更をテストして」 |

各スキルの詳しい動作、制約、対応ツールは、それぞれの `SKILL.md` を参照してください。

## インストール方法

### 特定のスキルだけをインストールする

リポジトリ名の後にスキル名を指定します。

```bash
gh skill install nimiusrd/agent-skills refactoring --agent AGENT_NAME --scope project
```

ほかのスキルを指定する場合は、`refactoring` を収録スキルの名前に置き換えてください。

## ローカルのスキルをインストールして検証する

作成中のスキルは、GitHub に公開する前に `--from-local` で対象プロジェクトへインストールして動作を確認できます。ローカルインストールではファイルがコピーされるため、`SKILL.md` を修正した場合は再インストールしてください。

### 1. スキルの仕様を検証する

スキルのソースリポジトリで、Agent Skills 仕様への適合性を確認します。

```bash
cd /path/to/agent-skills
gh skill publish --dry-run
```

### 2. 作成中のスキルを対象プロジェクトへ入れる

対象プロジェクトのルートで、ローカルリポジトリのパスを指定します。

```bash
cd /path/to/target-project

# 1つのスキルだけをインストール
gh skill install /path/to/agent-skills refactoring \
  --from-local --agent AGENT_NAME --scope project

# すべてのスキルをインストールする場合
gh skill install /path/to/agent-skills \
  --from-local --all --agent AGENT_NAME --scope project
```

### 3. インストール結果を確認して実際に使う

```bash
# プロジェクトスコープの対象エージェントのスキルを一覧表示
gh skill list --agent AGENT_NAME --scope project
```

対象プロジェクトでエージェントを起動し、スキルが想定どおり適用される依頼を実行します。

```text
このプロジェクトの package.json を整理して
```

修正を反映して再確認する場合は、`--force` を付けて同じコマンドを再実行します。

```bash
gh skill install /path/to/agent-skills refactoring \
  --from-local --agent AGENT_NAME --scope project --force
```

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

## 開発

各スキルは `skills/<skill-name>/SKILL.md` を起点に構成されています。必要に応じて、スクリプト、テンプレート、リファレンス、評価ケースを同じディレクトリ内へ配置します。

変更後は、Agent Skills 仕様への適合性を検証してください。

```bash
gh skill publish --dry-run
```

この検証は、`main` ブランチへの push と Pull Request でも GitHub Actions により実行されます。

## 公開

検証に成功したら、SemVer 形式のタグを指定して GitHub Release を作成します。

```bash
gh skill publish --tag v1.0.0
```

## ライセンス

[MIT License](LICENSE)
