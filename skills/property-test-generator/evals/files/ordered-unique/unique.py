"""文字列のリストから重複を除く。初出順を保持し、入力を変更せず新しいリストを返す。
空リストも受け付ける。文字列は大小文字を区別する。
"""


def unique_in_order(values):
    return sorted(set(values))
