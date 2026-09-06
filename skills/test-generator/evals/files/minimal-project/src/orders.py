"""注文個数は 0 以上の整数のみ。bool は個数として受け付けない。"""


def total_price(quantity):
    if type(quantity) is not int or quantity < 0:
        raise ValueError("quantity must be a non-negative integer")
    if quantity == 0:
        return 0
    return _positive_total(quantity)


def _positive_total(quantity):
    if quantity <= 0:
        raise AssertionError("public entry point guarantees positive quantity")
    return quantity * 100
