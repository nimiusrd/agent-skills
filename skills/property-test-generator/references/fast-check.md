# fast-check パターンリファレンス

TypeScript/JavaScript 向け。Vitest/Jest と組み合わせて使用。

## 基本構造

```typescript
import fc from "fast-check";

it("プロパティ名", () => {
  fc.assert(
    fc.property(arbitrary1, arbitrary2, (val1, val2) => {
      // arrange / act / assert
      expect(result).toBe(expected);
    }),
    { seed: 42 } // 再現用（オプション）
  );
});
```

## Arbitrary 一覧

### プリミティブ
- `fc.integer({ min, max })` — 整数
- `fc.nat()` — 自然数（0以上）
- `fc.float({ noDefaultInfinity: true, noNaN: true, min, max })` — 浮動小数点
- `fc.boolean()` — boolean
- `fc.string({ minLength, maxLength })` — 文字列
- `fc.unicodeString()` — Unicode文字列
- `fc.constant(v)` — 固定値
- `fc.constantFrom(v1, v2, ...)` — 列挙値から選択

### コレクション
- `fc.array(arb, { minLength, maxLength })` — 配列
- `fc.uniqueArray(arb, { minLength, maxLength })` — 重複なし配列
- `fc.set(arb)` — （非推奨、`uniqueArray`推奨）
- `fc.tuple(arb1, arb2, ...)` — タプル
- `fc.record({ key: arb, ... })` — オブジェクト
- `fc.dictionary(keyArb, valueArb)` — 辞書

### 合成
- `fc.oneof(arb1, arb2, ...)` — いずれか1つ
- `fc.option(arb)` — `T | null`
- `fc.frequency({ weight, arbitrary }, ...)` — 重み付き選択

### 変換（縮小を損なわない順に推奨）
- `.map(fn)` — 値変換（縮小は元のArbitraryに委譲）
- `.filter(pred)` — フィルタ（棄却率に注意、10%未満を目標）
- `.chain(fn)` — 依存値生成（前の値に基づくArbitraryを返す）

### エッジケース強制
```typescript
fc.integer({ min: 0, max: 100 })
// fast-check は自動で 0, 1, MAX 付近を優先生成する
// 追加のエッジケースは oneof + constant で明示：
fc.oneof(
  fc.constant(0),
  fc.constant(Number.MAX_SAFE_INTEGER),
  fc.integer({ min: 1, max: 1000 })
)
```

## プロパティパターン

### Round-trip（往復）
```typescript
fc.property(inputArb, (input) => {
  expect(decode(encode(input))).toEqual(input);
});
```

### Idempotence（冪等）
```typescript
fc.property(inputArb, (input) => {
  const once = normalize(input);
  expect(normalize(once)).toEqual(once);
});
```

### 不変条件
```typescript
fc.property(listArb, (list) => {
  expect(sort(list).length).toBe(list.length);
});
```

### Metamorphic（入力変形）
```typescript
fc.property(fc.array(fc.integer()), (arr) => {
  const sorted = sort(arr);
  const reversed = sort([...arr].reverse());
  expect(sorted).toEqual(reversed);
});
```

### 参照モデル
```typescript
fc.property(inputArb, (input) => {
  expect(optimizedImpl(input)).toEqual(naiveImpl(input));
});
```

## 失敗時の再現

```typescript
// 失敗出力例:
// Property failed after 23 tests
// Seed: 1234567890
// Counterexample: [42, "hello"]

// 再現:
fc.assert(fc.property(...), { seed: 1234567890 });
```

## ファイル命名

`*.property.test.ts` を推奨（プロジェクト慣例に従う）。
