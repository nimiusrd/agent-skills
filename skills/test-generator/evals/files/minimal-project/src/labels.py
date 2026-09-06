"""表示名の仕様: 前後の空白を除去し、None と空白だけの名前は「未設定」にする。"""


def display_name(name):
    if name is None:
        return "未設定"
    return name.strip() or "未設定"
