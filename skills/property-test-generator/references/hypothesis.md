# hypothesis パターンリファレンス

Python 向け。pytest と組み合わせて使用。

## 基本構造

```python
from hypothesis import given, settings, assume, reproduce_failure
from hypothesis import strategies as st

@given(val=st.integers(min_value=0, max_value=100))
def test_property_name(val):
    result = func(val)
    assert result == expected
```

## Strategy 一覧

### プリミティブ
- `st.integers(min_value, max_value)` — 整数
- `st.floats(min_value, max_value, allow_nan=False, allow_infinity=False)` — 浮動小数点
- `st.booleans()` — boolean
- `st.text(min_size, max_size, alphabet)` — 文字列
- `st.binary(min_size, max_size)` — バイト列
- `st.just(v)` — 固定値
- `st.sampled_from([v1, v2, ...])` — 列挙値から選択
- `st.none()` — None

### コレクション
- `st.lists(element, min_size, max_size)` — リスト
- `st.tuples(st1, st2, ...)` — タプル
- `st.dictionaries(keys, values, min_size, max_size)` — 辞書
- `st.fixed_dictionaries({ key: st, ... })` — 固定キー辞書
- `st.frozensets(element, min_size, max_size)` — frozenset

### 合成
- `st.one_of(st1, st2, ...)` — いずれか1つ
- `st.from_type(T)` — 型アノテーションから自動生成
- `st.builds(cls, arg1=st1, ...)` — コンストラクタ呼び出し

### 変換
- `.map(fn)` — 値変換
- `.filter(pred)` — フィルタ（棄却率に注意）
- `.flatmap(fn)` — 依存値生成

### エッジケース強制
```python
st.one_of(
    st.just(0),
    st.just(float("inf")),
    st.integers(min_value=1, max_value=1000),
)
```

## プロパティパターン

### Round-trip（往復）
```python
@given(data=input_strategy)
def test_roundtrip(data):
    assert decode(encode(data)) == data
```

### Idempotence（冪等）
```python
@given(data=input_strategy)
def test_idempotent(data):
    once = normalize(data)
    assert normalize(once) == once
```

### 不変条件
```python
@given(lst=st.lists(st.integers()))
def test_sort_preserves_length(lst):
    assert len(sorted(lst)) == len(lst)
```

### Metamorphic（入力変形）
```python
@given(lst=st.lists(st.integers()))
def test_sort_invariant_to_input_order(lst):
    assert sorted(lst) == sorted(reversed(lst))
```

### 参照モデル
```python
@given(data=input_strategy)
def test_matches_reference(data):
    assert optimized(data) == naive(data)
```

## 失敗時の再現

```python
# 失敗出力例:
# Falsifying example: test_name(data=42)
# You can reproduce this example by temporarily adding
# @reproduce_failure('6.x', b'AAAB')

@reproduce_failure('6.100.0', b'AAAB')
@given(data=input_strategy)
def test_name(data):
    ...
```

## 設定

```python
@settings(max_examples=200, deadline=None, database=None)
@given(...)
def test_heavy(data):
    ...
```

## ファイル命名

`test_*_property.py` または `*_property_test.py` を推奨（プロジェクト慣例に従う）。
