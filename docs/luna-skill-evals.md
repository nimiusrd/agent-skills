# Luna に対するスキル必要性の追加評価

現在の対象は4スキル。進め方の規約を検討する `incremental-refactoring` に加え、必要と判断した `property-test-generator`、`commit-and-pr`、`codex-review-loop` も再検証する。初回の成功・失敗だけで要否を決めず、未検証の失敗経路や、実際に観測した誤判断の再発を比較する。

この文書は現存する評価ケースと入力 fixture の実行手順を記載する。fixture のテスト成功や JSON 構文確認を、Luna が評価ケースに合格した結果として扱わない。

## 削除済みスキルの評価履歴

`maintain-package-json` と `devcontainer-bootstrap` は、Luna の追加比較後に削除した。削除前のケース・fixture・採点手順は [評価時点のソース](https://github.com/nimiusrd/agent-skills/tree/9e56837ddc6e39986218eabd15ca7dd365a3064f) に残る。両スキルの5ケースを各条件3回ずつ比較し、スキルなしでは全15実行が全項目を満たした。スキルありでは既存bootstrapの保持条件に1回違反した。Docker起動と外部依存の実調査は対象外。

`refactoring` は候補の永続化と差分の拡大防止を目的として `incremental-refactoring` に再構成した。

## 追加ケース

| スキル / ID | 検証する振る舞い |
|---|---|
| incremental-refactoring / 8 | 重複削減時に、保存→通知の順序・回数・例外伝播を保持する |
| incremental-refactoring / 9 | 正常系1件の成功と副作用・拒否経路の検証不足を区別する |
| property-test-generator / 1 | 正常実装で成功し、単語の意味を壊す4種の誤実装を追加生成テストだけで検出する |
| property-test-generator / 2 | 初出順違反をHypothesisで発見し、縮小反例を再実行して不具合を報告する |
| commit-and-pr / 1 | クリーンなツリーでも未公開コミットを公開し、既存PRのbaseを保持する |
| commit-and-pr / 2 | 作成応答が不明でも同じPRを再利用し、fork所有者の異なる同名ブランチを区別する |
| commit-and-pr / 3 | squash済みの親の境界で子だけを再配置し、lease拒否後の他者更新を守る |
| codex-review-loop / 8 | 現HEADへの依頼がある状態で明示された待機期限に達したら、再依頼せず終了する |
| codex-review-loop / 9 | 投稿時刻だけでは最新HEADとレビューの対応を確定しない |

## 比較条件

1. `gpt-5.6-luna` の同じ reasoning effort・ツール・実行環境で、スキルあり / なしを比較する。各ケース・条件ごとに新しいエージェントと独立した一時コピーを使う。
2. 各 `evals.json` の追加ケースの `prompt` を両条件に同じ文面で渡す。相対パスはそのスキルを基準に解決する。fixture は隠しファイルも含めディレクトリ全体をコピーする。
3. あり側だけ該当 `SKILL.md` と付属資料・スクリプトを利用できる。実行用のスキルコピーから `evals/` を除き、本文中の評価ケースへのリンクも除く。両条件とも `evals.json`、期待事項、採点資料（この文書を含む）、他ケース・他条件の結果を参照禁止とし、なし側にはスキル本文も渡さない。実行担当には対象ケースの prompt と入力 fixture だけを渡し、あり側にはさらに上述のスキルコピーを渡す。入力 fixture とその公開仕様・テストは両条件で同じにする。
4. 各条件3回を目安に独立反復する。モデル、reasoning effort、Node/npm/Python の版、実行コマンド、差分、終了コード、未実施項目を保存する。生成物・ログ・採点は入力 fixture に書き込まない。
5. 外部サービスへの投稿は行わない。依存 fixture は架空のローカルパッケージなのでレジストリに照会しない。Docker 起動や実タグ照会はこのセットの対象外。提供タグ一覧を実際のレジストリ確認結果として報告しない。

## 採点

各ケースの `expectations` を成果物と実行結果で採点する。スキル独自の記録形式や中止ログの有無を、スキルなしの能力不足として数えない。

- **incremental-refactoring / 8**: 既存テストを変更せず前後で実行し、実際に重複を減らした差分も確認する。テストが成功しただけで変更がなければ未達。
- **incremental-refactoring / 9**: 基本評価は未検証範囲の正しい報告、テスト変更禁止、変更した場合の動作保持。候補への状態・再開条件の保存は運用規約として別欄で採点する。なし側が動作を保持して変更できた場合、中止しなかったことだけで失敗にしない。変更した成果物は別コピーで `side-effects/tests/test_account.py` を使い動作保持を検証できる。この追加検証用テストを実行担当に渡したり、入力 fixture に追加したりしない。
- **property-test-generator / 1**: Hypothesis入りの同じ隔離環境を両条件へ提供する。未導入なら先に環境を整備するか環境ブロックとして記録し、モデルの失敗と混同しない。評価担当が `python skills/property-test-generator/evals/check_normalization_mutations.py <成果物のfixtureディレクトリ>` を実行する。このスクリプトは候補の製品コード・既存テストの保持を確認し、一時コピーで追加ファイルだけを実行する。既存の例示テストで誤実装を検出できても、生成テストの検出力の証拠にはしない。正常系の0件実行、タイムアウト、import等のエラーを成功やmutation検出として数えない。スクリプト自体は実行担当へ渡さない。出力とテストを読み、Hypothesisを実際に使っていることと仕様に基づく生成も別途確認する。
- **property-test-generator / 2**: fixtureは意図的に初出順を破る製品不具合を含み、既存テストでは通る。生成テストで失敗することが正しい成果。反例の特定の文字列や最小長は要求しない。実際の縮小出力と再実行の証拠を確認し、手書き反例だけを縮小成功とは扱わない。製品修正や期待値の緩和は不合格。
- **commit-and-pr**: すべて模擬状態で次の行動を採点する。コマンドの完全一致や特定ツールの利用を要求せず、base保持・重複防止・親境界の利用・lease拒否時の保護を確認する。実操作の成功を検証したとは報告しない。
- **codex-review-loop / 8–9**: 明示された期限を使い、スキル独自の30分既定値を知らないことでは不合格にしない。ケース8は初回に曖昧だった「現HEADの依頼済み」を明記した回帰ケース。ケース9は正規投稿者でもHEAD対応が不明な条件を検証する。

両条件で同じ成果を得られるケース、スキルありだけ成功するケース、両方失敗するケースを分ける。単発の成功や、独自ルールへの準拠だけでスキル全体の要否を決めない。時間・トークンは取得できた実測値だけを併記する。

## fixture の事前確認

リポジトリルートから実行する。npm install は fixture を一時コピーしてから行い、元の入力に `node_modules` を残さない。

```sh
(cd skills/incremental-refactoring/evals/files/side-effects && python3 -m unittest discover -s tests -v)
(cd skills/incremental-refactoring/evals/files/uncovered-effects && python3 -m unittest discover -s tests -v)
```

PBT fixture は Python 3.10 以上の隔離環境に同梱 `requirements.txt` を導入し、各 fixture のディレクトリで `python -m unittest discover -s tests -v` を実行する。元の例示テストはいずれも成功する。Hypothesis 6.168.0 / sortedcontainers 2.4.0 に固定し、両条件で同じ環境を使う。依存導入は実行担当へ課題を渡す前に行う。

これらは入力・補助コードの健全性確認であり、Luna の行動評価とは別の検証である。

## incremental-refactoring の運用評価

ID 10は候補の永続化と一単位への差分限定、ID 11は大きな候補の分割、ID 12は会話履歴なしでの既存台帳の照合を評価する。次セッションへの引き継ぎは、生成された候補台帳と成果物だけを新しい実行担当に渡して確認する。現行規約に合わせてID 1–3・6・9を更新した。旧規約の停止・ログ形式を基本能力の合否へ流用しない。追加・更新したケースは実行結果ではなく評価定義である。
