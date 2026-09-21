"""amount は正の int のみ。更新成功後に通知し、通知失敗は伝播する。"""


def deposit(balance, amount, save, notify):
    if type(amount) is not int or amount <= 0:
        raise ValueError("positive integer required")
    updated = balance + amount
    save(updated)
    notify("deposit", updated)
    return updated


def withdraw(balance, amount, save, notify):
    if type(amount) is not int or amount <= 0:
        raise ValueError("positive integer required")
    if amount > balance:
        raise ValueError("insufficient funds")
    updated = balance - amount
    save(updated)
    notify("withdraw", updated)
    return updated
