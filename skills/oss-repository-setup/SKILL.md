---
name: oss-repository-setup
license: MIT
description: 公開OSSをGitHubに新規作成するとき、小さく始められるようにルールセット・Immutable Releases・Issue／PRの初期設定を整える。「公開リポジトリを作って初期設定して」「新しいOSSのGitHub設定を整えて」などに使用する。作成直後の設定や中断した初期設定の再開も対象とし、既存OSS全体の設定監査、通常のIssue対応・PR作成・リリース発行には使用しない。
---

# OSS Repository Setup

公開OSSを新しく作る際に、最小限の設定で開発を始められるようにする。ブランチ保護とリリースの不変性を基本にし、レビュー条件・必須チェック・テンプレート・文書・自動化は必要になった時点で追加する。すべてを揃えることを開始条件にしない。

## 依頼の範囲

- 作成と初期設定を依頼された場合は、所有者・名前・公開範囲を確定し、リポジトリ作成から設定まで進める。既に与えられた作成・適用の許可を取り直さない。
- 作成済みの新規リポジトリの初期設定を依頼された場合は、そのリポジトリを使う。別のリポジトリを作成したり、既存の非公開リポジトリを公開に切り替えたりしない。
- 初期設定の方針・手順だけを求められた場合は、標準と例外を説明する。設定の確認だけを求められた場合は読み取りにとどめる。
- ユーザー指定とリポジトリ固有の方針を優先する。個別項目だけの依頼を全設定の変更に広げず、既存OSSの一括移行・監査には拡張しない。

## 設定するタイミング

| タイミング | 設定するもの |
| --- | --- |
| リポジトリ作成直後 | マージコミット、headブランチ自動削除、Issues有効、Discussions無効、Immutable Releases |
| 初期コミットと既定ブランチの作成後 | PR必須、Force push・削除禁止 |

CIの有無にかかわらず初期設定を完了させ、必須チェックの追加を後続の必須作業にしない。公開用workflowがまだなくてもImmutable Releasesは先に有効にできる。今後作る公開手順を不変Releaseに対応させる。

## 標準設定

### デフォルトブランチ

既定ブランチを対象に、次のbranch rulesetをActiveで適用する。ブランチ名を`main`に決め打ちしない。全ブランチを保護して作業ブランチの更新・削除まで妨げない。

新規rulesetには同梱の[default-branch-ruleset.json](assets/default-branch-ruleset.json)を使う。JSONによる適用方法は後述の「RulesetのJSON」を参照する。

| 項目 | 標準 |
| --- | --- |
| PR経由の変更 | 必須。管理者の変更も含める |
| レビュー承認 | 必須にしない（承認数0人）。Code ownerの承認・最後のpushへの承認も要求しない |
| 必須チェック | 設定しない。CIがあっても初期設定では必須化しない |
| マージ前のブランチ最新化 | 要求しない |
| レビューコメントの解決 | 必須にしない |
| Force push・ブランチ削除 | 禁止 |
| Linear history | 必須にしない。マージコミットを許可する |
| Bypass | 新規設定では登録しない |
| 署名付きコミット・Merge queue | 共通の必須条件にはしない |

PRは必須とし、初期設定ではレビュー承認・レビューコメントの解決・チェックの成功をマージ条件にしない。これらの条件は必要になった時点で追加する。

### マージとIssue・PR運用

| 項目 | 標準 |
| --- | --- |
| マージ方法 | マージコミットを有効にし、squash merge・rebase mergeは無効にする |
| マージ後のheadブランチ | 自動削除を有効にする |
| Issues | 有効。不具合・作業・改善候補を記録する |
| Issue作成 | すぐ終わる修正では不要。PRだけで完結してよい |
| PR本文 | 変更の目的と確認結果を簡潔に残す |
| Issueテンプレート | 初期設定では省略。必要に応じて追加する |
| PRテンプレート | 任意。必須化しない |
| Discussions | 初期設定では無効。必要に応じて有効にする |
| CONTRIBUTING・CODEOWNERS | 初期設定では省略。運用に必要になったら追加する |
| 放置Issueの自動クローズ | 初期設定には含めない |

初期設定では維持する項目を少なくする。ユーザーが必要としているテンプレート・文書・機能は依頼に合わせて整える。既存のテンプレートや文書は保持し、既存のDiscussionsに投稿がある場合は利用実態を踏まえて扱う。

設定作業の一環としてIssue・PR・コメントを投稿したり、既存Issue・PRをクローズ・マージしたりしない。これらは別途依頼されたときに行う。

### リリース

- 新規リポジトリでは将来の初回Releaseから保護するため、Immutable Releasesを初期設定で有効にする。
- 公開はDraft作成 → 配布物の添付・検証 → Publishの順にする。配布物がなければ添付工程は不要。
- 公開後に配布内容を修正するときは新しいバージョンを発行し、確定版タグ（例：`v1.2.3`）を移動・再利用しない。
- 不変になるのはタグと添付アセット。タイトルとリリースノートは編集できる。有効化前の既存リリースには遡及しない。
- GitHub Releasesを使わないと明示された場合は「対象外」としてよい。新規リポジトリにリリース履歴や公開用workflowがないことは、有効化を見送る理由にしない。
- GitHub Actionsの配布で`v1`等の追従タグを使う場合、確定版の不変Releaseと、Releaseに紐づけない更新可能な追従タグを分ける。タグのrulesetで両方を一律に更新禁止にしない。

## 初期設定の進め方

1. **作成先・対象を確定する。** GitHubのhost、所有者、リポジトリ名、公開範囲、作成済みかどうかを依頼・remote・認証情報から確認する。不足する必須情報だけを質問する。作成済みなら公開状態と管理権限を確認する。
2. **作成または再開する。** 作成も依頼されていれば、同名リポジトリの有無を確認して公開リポジトリを作る。応答不明時に重複作成を試みない。既存リポジトリが見つかった場合は今回の対象か確認し、初期設定の続きに進む。利用可能なGitHub API・コネクタ・`gh`を優先し、未対応項目は公式仕様とUIを確認する。
3. **初期化の状態を確認する。** 初期コミットと既定ブランチ、設定値、継承ルール、公開手順の有無を取得し、今回適用する差分をまとめる。空のリポジトリでは、初期ファイルの投入をブランチ保護より先に行う。作成から初期設定までの依頼なら、空のままにする指定がない限り、README等の最小限の初期コミットで既定ブランチを作ってよい。手元の既存ソース一式の公開は依頼範囲を確認してから行う。空のままを指定された場合は、ブランチ保護を初期化後の作業として残す。ライセンスはユーザー指定・既存LICENSEに従い、任意のライセンスを選んで追加しない。
4. **作成直後の設定を適用する。** 上記のタイミング表に沿って、マージ方法、Issues等の機能、リリース設定を適用する。テンプレート等から公開用workflowを引き継いだ場合は、Immutable Releasesとの互換性も確認する。
5. **ブランチを保護する。** 既定ブランチの存在を確認し、PR必須・Force push禁止・削除禁止のbranch rulesetを適用する。レビュー承認・コメント解決・必須チェック・最新化要求は追加しない。bot等による既定ブランチへの直接pushがある場合はPR経由にできるか調べ、動作維持のためだけに広いbypassを追加しない。
6. **再取得して検証する。** APIの書き込み成功だけで完了とせず、設定値と既定ブランチに実際に適用されるルールを確認する。権限不足・API非対応・取得失敗は未確認として扱う。解消できない項目だけを止め、適用済み設定と後続作業を区別して報告する。

初期設定の再実行では、既存rulesetのIDと内容を確認して更新し、同名rulesetを重複作成しない。既に設定済みなら変更不要とする。テンプレートや組織から引き継いだ設定は無関係な部分を保持し、強い保護を標準との差だけで緩和しない。組織ルールや旧branch protectionも重なって効くため、ローカルな設定値だけで有効な保護を判断しない。

### RulesetのJSON

[assets/default-branch-ruleset.json](assets/default-branch-ruleset.json)は、PR必須・Force push禁止・削除禁止だけを設定する共通の雛形。対象に`~DEFAULT_BRANCH`を使い、リポジトリ名・ブランチ名・作成済みrulesetのIDを埋め込まない。承認は0人、コメント解決は不要とし、必須チェック・Linear history・bypassは追加しない。

- **JSONの準備だけを依頼された場合:** 雛形を指定の保存先にコピーし、必要な差分だけを調整して渡す。GitHubには適用しない。
- **初期設定の適用を依頼された場合:** 新規rulesetにはこのJSONを入力としてAPIで適用する。UIで設定する場合も同じJSONをインポートできる。
- **既存rulesetを更新する場合:** 雛形をそのまま上書きせず、現状のルールや対象条件を保持した更新用JSONを作り、対象IDへ適用する。

UIでは対象リポジトリのSettingsからRulesetsを開き、New ruleset → Import a rulesetでJSONを選び、内容を確認してCreateする。APIでは次のように作成する。各変数には確認済みのhost、`owner/repo`、JSONの絶対パスを設定する。

```bash
gh api --hostname "$github_host" --method POST \
  "repos/$target_repo/rulesets" \
  --input "$ruleset_json"
```

更新には`PUT repos/{owner}/{repo}/rulesets/{ruleset_id}`を使う。作成前の一覧取得・更新前の詳細取得・適用後の再取得を行い、重複や意図しない上書きを防ぐ。

このJSONが扱うのはブランチのrulesetだけ。マージコミットの有効化、headブランチ自動削除、Issues、Discussions、Immutable Releasesは別のリポジトリ設定として適用する。JSONをリポジトリに保存しただけでは設定は反映されない。

### Immutable Releasesを有効にする前の条件

- Release公開後にバイナリをアップロードするworkflowや、公開アセットを差し替える処理がないか確認する。
- 複数ジョブで配布物を作る場合も、すべてのアップロードと検証が完了してからPublishする構成にする。
- 互換性のない公開手順が稼働中なら、手順の修正が反映されるまで有効化を保留する。検証目的で実際のReleaseを公開したり、既存Release・タグ・配布物を変更したりしない。

## 成果のまとめ方

対象ごとに、適用済み・変更不要・対象外・未適用・未確認を区別して簡潔に報告する。ローカル変更とGitHubに反映済みの変更も区別する。例外には理由を添え、必要なら後で取り組む作業を示す。

作成したリポジトリのURLと、初期設定の結果を返す。後続作業がある場合は「既定ブランチ作成後に保護」など、有効化の条件を添える。設定ファイルを保存するだけではGitHubへ反映されないことを明確にする。省略したレビュー条件・必須チェック・任意のテンプレート・文書・自動化を、未完了の必須作業として列挙しない。

## 公式仕様の参照先

適用時は利用中のGitHub host・プランに対応する最新仕様と、実際に利用できるAPIを確認する。以下は仕様を確認する起点であり、標準方針そのものはこのスキルで定める。

- [Rulesetsのルール](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [Rulesets REST API](https://docs.github.com/en/rest/repos/rules)
- [RulesetのJSONインポート](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository#importing-a-ruleset)
- [リポジトリ設定REST API](https://docs.github.com/en/rest/repos/repos)
- [Immutable Releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
- [リリースの不変性の有効化](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes)
- [GitHub Actionsの不変Releaseと追従タグ](https://docs.github.com/en/actions/how-tos/create-and-publish-actions/using-immutable-releases-and-tags-to-manage-your-actions-releases)
