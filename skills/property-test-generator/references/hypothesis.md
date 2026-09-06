# hypothesis パターンリファレンス

Python 向け。pytest と組み合わせて使用。既存の導入版・設定を確認して適用する。

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
- `st.text(alphabet=..., min_size=0, max_size=100)` — 文字列
- `st.binary(min_size=0, max_size=100)` — バイト列
- `st.just(v)` — 固定値
- `st.sampled_from([v1, v2, ...])` — 列挙値から選択
- `st.none()` — None

### コレクション
- `st.lists(element, min_size=0, max_size=100)` — リスト
- `st.tuples(st1, st2, ...)` — タプル
- `st.dictionaries(keys, values, min_size=0, max_size=100)` — 辞書
- `st.fixed_dictionaries({ key: st, ... })` — 固定キー辞書
- `st.frozensets(element, min_size=0, max_size=100)` — frozenset

### 合成
- `st.one_of(st1, st2, ...)` — いずれか1つ
- `st.from_type(T)` — 型アノテーションから自動生成
- `st.builds(cls, arg1=st1, ...)` — コンストラクタ呼び出し

### 変換
- `.map(fn)` — 値変換
- `.filter(pred)` — フィルタ（棄却率に注意）
- `.flatmap(fn)` — 依存値生成

### エッジケースの生成
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

必要に応じて `@settings(print_blob=True)` を使い、失敗時に出力された `@reproduce_failure(実際のversion, 実際のblob)` を一時的に追加して再実行する。blob は版をまたいだ互換性が保証されないので、架空の値や別バージョンの例をコピーしない。

縮小された入力を継続して検証するには `@example(...)` や通常の回帰テストにする。通常の失敗で seed が必ず表示されるとは限らない。記録済み seed を使う場合は pytest の `--hypothesis-seed` を利用できる。

試行回数・deadline・database は既存設定を優先する。タイムアウトや永続化を理由なく無効にしない。必須の境界は `@example` で指定する。

公式資料: [失敗の再実行](https://hypothesis.readthedocs.io/en/latest/tutorial/replaying-failures.html)、[pytest連携](https://hypothesis.readthedocs.io/en/latest/reference/integrations.html)

## ファイル命名

`test_*_property.py` または `*_property_test.py` を推奨（プロジェクト慣例に従う）。
