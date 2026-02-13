# proptest パターンリファレンス

Rust 向け。`cargo test` で実行。

## セットアップ

```toml
# Cargo.toml
[dev-dependencies]
proptest = "1"
```

## 基本構造

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn property_name(val in 0..100i32) {
        // arrange / act / assert
        prop_assert_eq!(result, expected);
    }
}
```

## Strategy 一覧

### プリミティブ
- `any::<i32>()` — 任意の整数（型推論）
- `0..100i32` — 範囲（Range は自動で Strategy）
- `Just(v)` — 固定値
- `prop_oneof![st1, st2, ...]` — いずれか1つ
- `"[a-z]{1,10}"` — 正規表現から文字列生成
- `any::<bool>()` — boolean
- `any::<f64>().prop_filter("finite", |v| v.is_finite())` — フィルタ付き

### コレクション
- `prop::collection::vec(element, size_range)` — Vec
- `prop::collection::hash_set(element, size_range)` — HashSet
- `prop::collection::hash_map(key, value, size_range)` — HashMap
- `prop::collection::btree_set(element, size_range)` — BTreeSet

### 合成
- `(st1, st2, st3)` — タプル（自動で Strategy）
- `prop_oneof![st1, st2]` — いずれか1つ
- `prop::sample::select(vec![v1, v2, ...])` — スライスから選択

### 変換
- `.prop_map(|v| transform(v))` — 値変換
- `.prop_filter("reason", |v| predicate(v))` — フィルタ（理由文字列必須）
- `.prop_flat_map(|v| dependent_strategy(v))` — 依存値生成

### Enum / 構造体の生成
```rust
#[derive(Debug, Clone)]
enum Op { Add, Sub, Mul }

fn op_strategy() -> impl Strategy<Value = Op> {
    prop_oneof![
        Just(Op::Add),
        Just(Op::Sub),
        Just(Op::Mul),
    ]
}

fn record_strategy() -> impl Strategy<Value = Record> {
    (any::<String>(), 0..1000u32).prop_map(|(name, value)| Record { name, value })
}
```

### エッジケース強制
```rust
prop_oneof![
    Just(0i32),
    Just(i32::MIN),
    Just(i32::MAX),
    -1000..1000i32,
]
```

## プロパティパターン

### Round-trip（往復）
```rust
proptest! {
    #[test]
    fn roundtrip(input in input_strategy()) {
        let encoded = encode(&input);
        let decoded = decode(&encoded).unwrap();
        prop_assert_eq!(decoded, input);
    }
}
```

### Idempotence（冪等）
```rust
proptest! {
    #[test]
    fn idempotent(input in input_strategy()) {
        let once = normalize(&input);
        let twice = normalize(&once);
        prop_assert_eq!(once, twice);
    }
}
```

### 不変条件
```rust
proptest! {
    #[test]
    fn sort_preserves_length(mut v in prop::collection::vec(any::<i32>(), 0..100)) {
        let len = v.len();
        v.sort();
        prop_assert_eq!(v.len(), len);
    }
}
```

### Metamorphic（入力変形）
```rust
proptest! {
    #[test]
    fn sort_order_independent(v in prop::collection::vec(any::<i32>(), 0..100)) {
        let mut a = v.clone();
        let mut b = v.into_iter().rev().collect::<Vec<_>>();
        a.sort();
        b.sort();
        prop_assert_eq!(a, b);
    }
}
```

### 参照モデル
```rust
proptest! {
    #[test]
    fn matches_reference(input in input_strategy()) {
        prop_assert_eq!(optimized(&input), naive(&input));
    }
}
```

## 失敗時の再現

```rust
// 失敗出力例:
// thread 'test' panicked at 'Test failed: minimal failing input: val = 42'
// proptest persistence file: proptest-regressions/module_name.txt

// proptest は自動で proptest-regressions/ に失敗ケースを保存する。
// 再実行時に自動で回帰テストとして実行される。
// 手動で設定ファイルから seed を指定することも可能：

// proptest.toml (プロジェクトルート)
// [default]
// cases = 256
```

## 設定

```rust
proptest! {
    #![proptest_config(ProptestConfig::with_cases(500))]

    #[test]
    fn heavy_test(input in input_strategy()) {
        // ...
    }
}
```

## ファイル配置

テストはモジュール内 `#[cfg(test)] mod tests` に記述するか、
`tests/` ディレクトリに統合テストとして配置する（プロジェクト慣例に従う）。
