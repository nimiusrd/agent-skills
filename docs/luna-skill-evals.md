# Luna に対するスキル必要性の追加評価

対象は `test-generator` を除く6スキル。初回比較で不要候補だった3件に加え、必要と判断した `property-test-generator`、`commit-and-pr`、`codex-review-loop` も再検証する。初回の成功・失敗だけで要否を決めず、未検証の失敗経路や、実際に観測した誤判断の再発を比較する。

この変更は評価ケースと入力 fixture の追加。fixture のテスト成功や JSON 構文確認を、Luna が評価ケースに合格した結果として扱わない。

## 追加ケース

| スキル / ID | 検証する振る舞い |
|---|---|
| refactoring / 8 | 重複削減時に、保存→通知の順序・回数・例外伝播を保持する |
| refactoring / 9 | 正常系1件の成功と副作用・拒否経路の検証不足を区別する |
| maintain-package-json / 4 | npm の pre/post フック、引数、失敗時の停止、CI の入口を保持する |
| maintain-package-json / 5 | Node と peer の制約を満たす更新だけを選び、同じ出力でも非互換な最新版は見送る |
| devcontainer-bootstrap / 1 | JSONC のコメントと既存設定を保持して指定 feature だけを追加する |
| devcontainer-bootstrap / 2 | 共通 bootstrap と同名のチーム独自スクリプトを上書きしない |
| devcontainer-bootstrap / 3 | プロジェクトの Python 制約から固定タグを選び、生成設定間で整合させる |
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

- **refactoring / 8**: 既存テストを変更せず前後で実行し、実際に重複を減らした差分も確認する。テストが成功しただけで変更がなければ未達。
- **refactoring / 9**: 基本評価は未検証範囲の正しい報告、テスト変更禁止、変更した場合の動作保持。スキルの Gate B による「ソースを変えず停止」と「中止ログ」は別欄の運用方針として採点する。なし側が動作を保持して変更できた場合、中止しなかったことだけで失敗にしない。変更した成果物は別コピーで `side-effects/tests/test_account.py` を使い動作保持を検証できる。この追加検証用テストを実行担当に渡したり、入力 fixture に追加したりしない。
- **maintain-package-json / 4**: `npm test` が成功すること。テストは正常実行に加え pre/build の各失敗時、空白・セミコロンを含む引数を検証する。呼ばれている入口を残し、整理不要と根拠付きで判断する結果も合格にできる。
- **maintain-package-json / 5**: manifest・lock・配布物の実バージョンと engines/peer を確認する。隔離した成果物に対して `npm ci --offline --ignore-scripts` と `npm test` を行う。ホストが Node 20/22 でなければ engine 警告があり得る。ホストでの実行成功はサポート対象版での検証成功を意味しない。`engine-strict` が有効など環境都合で実行不能なら環境ブロックを記録し、制約を緩和しない。
- **devcontainer-bootstrap / 1**: 元のコメント、値、配列を保持した差分であることを確認する。`json.loads` で JSONC を読めないことを fixture 不良とみなさない。
- **devcontainer-bootstrap / 2**: 競合で無変更終了した場合も、別名で安全に共存させた場合も成果で採点する。スクリプト固有の停止方法だけを必須にしない。
- **devcontainer-bootstrap / 3**: image または使用する Dockerfile の FROM を確認し、使用しない Dockerfile も生成したなら矛盾がないことを確認する。
- **property-test-generator / 1**: Hypothesis入りの同じ隔離環境を両条件へ提供する。未導入なら先に環境を整備するか環境ブロックとして記録し、モデルの失敗と混同しない。評価担当が `python skills/property-test-generator/evals/check_normalization_mutations.py <成果物のfixtureディレクトリ>` を実行する。このスクリプトは候補の製品コード・既存テストの保持を確認し、一時コピーで追加ファイルだけを実行する。既存の例示テストで誤実装を検出できても、生成テストの検出力の証拠にはしない。正常系の0件実行、タイムアウト、import等のエラーを成功やmutation検出として数えない。スクリプト自体は実行担当へ渡さない。出力とテストを読み、Hypothesisを実際に使っていることと仕様に基づく生成も別途確認する。
- **property-test-generator / 2**: fixtureは意図的に初出順を破る製品不具合を含み、既存テストでは通る。生成テストで失敗することが正しい成果。反例の特定の文字列や最小長は要求しない。実際の縮小出力と再実行の証拠を確認し、手書き反例だけを縮小成功とは扱わない。製品修正や期待値の緩和は不合格。
- **commit-and-pr**: すべて模擬状態で次の行動を採点する。コマンドの完全一致や特定ツールの利用を要求せず、base保持・重複防止・親境界の利用・lease拒否時の保護を確認する。実操作の成功を検証したとは報告しない。
- **codex-review-loop / 8–9**: 明示された期限を使い、スキル独自の30分既定値を知らないことでは不合格にしない。ケース8は初回に曖昧だった「現HEADの依頼済み」を明記した回帰ケース。ケース9は正規投稿者でもHEAD対応が不明な条件を検証する。

両条件で同じ成果を得られるケース、スキルありだけ成功するケース、両方失敗するケースを分ける。単発の成功や、独自ルールへの準拠だけでスキル全体の要否を決めない。時間・トークンは取得できた実測値だけを併記する。

## fixture の事前確認

リポジトリルートから実行する。npm install は fixture を一時コピーしてから行い、元の入力に `node_modules` を残さない。

```sh
(cd skills/refactoring/evals/files/side-effects && python3 -m unittest discover -s tests -v)
(cd skills/refactoring/evals/files/uncovered-effects && python3 -m unittest discover -s tests -v)
(cd skills/maintain-package-json/evals/files/lifecycle-scripts && npm test)
python3 -m unittest discover -s skills/devcontainer-bootstrap/tests -v
```

PBT fixture は Python 3.10 以上の隔離環境に同梱 `requirements.txt` を導入し、各 fixture のディレクトリで `python -m unittest discover -s tests -v` を実行する。元の例示テストはいずれも成功する。Hypothesis 6.168.0 / sortedcontainers 2.4.0 に固定し、両条件で同じ環境を使う。依存導入は実行担当へ課題を渡す前に行う。

これらは入力・補助コードの健全性確認であり、Luna の行動評価とは別の検証である。
