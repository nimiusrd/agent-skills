# テスト手順

プロジェクトルートで Python 3 の標準ライブラリを使う。依存追加は不要。

- 全体テスト: `python3 -m unittest discover -s tests -v`
- 注文テスト: `python3 -m unittest discover -s tests -p test_orders.py -v`
- 表示名テスト: `python3 -m unittest discover -s tests -p test_labels.py -v`
- 行カバレッジ: `python3 -m trace --count --summary --missing --coverdir <今回専用の一時出力先> --module unittest discover -s tests -v`

一時出力先は実行ごとに新しく作成する。測定コマンド自体の終了コードを確認し、出力された `src.orders.cover` と `src.labels.cover` の実行回数付き行・未実行行から対象の実行行数と未実行行数を確認する。標準出力の率は整数丸めされるので閾値判定には使わない。`trace` は行カバレッジだけを測定するため、分岐カバレッジは未計測と報告する。

`reports/previous-coverage.json` は過去の測定記録で、今回の実行との対応はない。
