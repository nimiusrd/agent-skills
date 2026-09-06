# fast-check パターンリファレンス

TypeScript/JavaScript 向け。Vitest/Jest と組み合わせて使用。以下は fast-check v4 系の API を前提とする。既存プロジェクトでは導入版の型定義を優先し、これらの例のためだけに更新しない。

## 基本構造

```typescript
import fc from "fast-check";

it("プロパティ名", () => {
  fc.assert(
    fc.property(arbitrary1, arbitrary2, (val1, val2) => {
      // arrange / act / assert
      expect(result).toBe(expected);
    })
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
- `fc.string({ unit: 'grapheme', maxLength: 100 })` — Unicode書記素の文字列（長さはunit数）
- `fc.constant(v)` — 固定値
- `fc.constantFrom(v1, v2, ...)` — 列挙値から選択

### コレクション
- `fc.array(arb, { minLength, maxLength })` — 配列
- `fc.uniqueArray(arb, { minLength, maxLength })` — 重複なし配列
- `fc.tuple(arb1, arb2, ...)` — タプル
- `fc.record({ key: arb, ... })` — オブジェクト
- `fc.dictionary(keyArb, valueArb)` — 辞書

### 合成
- `fc.oneof(arb1, arb2, ...)` — いずれか1つ
- `fc.option(arb)` — `T | null`
- `fc.oneof({ weight: 2, arbitrary: arb1 }, { weight: 1, arbitrary: arb2 })` — 重み付き選択

### 変換
- `.map(fn)` — 値変換（縮小は元のArbitraryに委譲）
- `.filter(pred)` — フィルタ（棄却率に注意、過剰な棄却は生成方法を見直す）
- `.chain(fn)` — 依存値生成（前の値に基づくArbitraryを返す）

### エッジケースの生成
```typescript
fc.integer({ min: 0, max: 100 })
// 追加の境界を oneof + constant で候補に含める。
// 各実行で必ず選ばれる保証はないため、必須ケースは通常のテストにもする。
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

失敗出力の `seed`、`path`、縮小反例、使用した fast-check の版と実行コマンドを残す。同じプロパティ・生成器・版で `fc.assert(property, { seed: 実際のseed, path: "実際のpath" })` として再実行する。再現用の固定値は通常のランダム探索に戻す際に外す。非同期なら `fc.asyncProperty` と `await fc.assert(...)` を使う。

公式資料: [文字列](https://fast-check.dev/docs/core-blocks/arbitraries/primitives/string/)、[重み付き選択](https://fast-check.dev/docs/core-blocks/arbitraries/combiners/any/)、[実行設定](https://fast-check.dev/docs/configuration/)

## ファイル命名

`*.property.test.ts` を推奨（プロジェクト慣例に従う）。
