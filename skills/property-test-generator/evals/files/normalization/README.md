# 実行環境

Python 3.10 以上と Hypothesis を使用する。`requirements.txt` の依存を評価用の隔離環境に導入し、`python -m unittest discover -s tests -v` で実行する。製品コードと既存テストは変更せず、新しいテストファイルを追加する。
