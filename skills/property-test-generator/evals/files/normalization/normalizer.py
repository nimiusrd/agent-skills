"""Unicode空白で区切られた単語をASCII空白1個で結合する。
単語の内容・大小文字・順序を保持し、空文字・空白だけなら空文字を返す。
入力は文字列のみ。前後の空白は除去する。
"""


def normalize_words(text):
    return " ".join(text.split())
