# 電卓テンキー入力（金額欄）設計書

- 作成日: 2026-06-27
- 対象: finance_web (BYB)
- 種別: 機能追加（UX）

## 1. 目的

家計簿で最頻の操作である「金額入力」を、四則演算つきの電卓テンキーで楽にする。
レシート合算（`1,250 + 980 + 450`）や割り勘（`3000 ÷ 3`）をアプリ内で完結させる。

## 2. 確定した要件（brainstormingで合意）

| 論点 | 決定 |
| --- | --- |
| 起動方式 | 金額欄の右端に🧮ボタンを置き、押したときだけ電卓ボトムシートを開く。**OSキーボード（iOSフリック入力）は今まで通り併用**できる |
| スコープ | `money` 付き `Input` 全部（支出・収入・固定費の月額・ローン残債/返済額・貯金目標・口座残高・予算）。金利(%)など非金額欄には出さない |
| 確定の流れ | シート上部に式と結果を常時表示。`=` は途中計算用。**「確定」ボタンで結果を金額欄に入れてシートを閉じる**。背景タップ/×/Escは確定せず閉じる |
| 計算方式 | **電卓式（逐次計算）**。押した順に計算する（`1,250 + 980 × 2` →「(1,250+980)×2 = 4,460」）。数学の優先順位（×÷を先に）は採らない |
| 数値 | 円は整数。割り算で小数が出ても**確定時に四捨五入**して整数化。計算中のディスプレイは小数も表示 |

## 3. 採用アプローチ

**案A: 共通 `Input` コンポーネント（`src/components/ui.tsx`）に内蔵**

`money` 付き `Input` が自動で🧮ボタンと電卓シートを持つ。呼び出し側（約12箇所）は変更不要。

- 不採用案B（新 `MoneyInput` で全箇所置換）: 差分が大きい
- 不採用案C（グローバル単一シート＋Context）: 今回のスコープを超える複雑さ。将来「UIヘルパのContext化」と一緒に寄せる方が自然

## 4. ファイル構成

```
src/utils/calculator.ts            ← 電卓の計算ロジック（純粋関数・テスト対象）
src/components/CalculatorSheet.tsx ← ボトムシートUI（テンキー＋演算子＋ディスプレイ＋確定）
src/components/ui.tsx の Input      ← money時に🧮ボタンを追加（最小改修）
src/test/calculator.test.ts        ← ロジックの単体テスト
src/test/CalculatorSheet.test.tsx  ← シートの操作テスト
```

ロジックをUIから切り離し、計算だけを単体テストできる構造にする。

## 5. 計算ロジック（`calculator.ts`）

### 状態モデル

```
type Operator = "+" | "-" | "*" | "/";
interface CalcState {
  acc: number | null;     // 累積値（確定済みの左辺）
  pending: Operator | null; // 押された演算子
  current: string;        // 入力中の数字文字列（"123" や "12.5"）
  error: boolean;         // ÷0 などのエラー中か
}
```

### 操作（純粋関数 `reduce(state, action)` で実装）

- `digit(n)`: 入力中の数字に1桁追加（桁あふれ=12桁超は無視）
- `dot()`: 小数点を1つだけ追加
- `operator(op)`: `pending` があれば先に `acc = apply(acc, pending, current)` を計算してから、新しい `pending` をセット。`current` を空に
- `equals()`: `acc = apply(acc, pending, current)`、`pending = null`、`current` を結果に。**`=` 直後に数字を押したら新しい計算として `current` を作り直す**（結果に追記しない）
- `backspace()`: 入力中の数字を1文字消す
- `clear()`: 全リセット
- `apply(a, op, b)`: 四則演算。`/` で `b === 0` なら `error = true`

### ディスプレイ用の導出値（純粋関数）

- `formatExpression(state)`: 「`1,250 + 980`」のような式文字列
- `currentResult(state)`: 今の計算結果（数値）。エラー中は null
- `confirmValue(state)`: 確定時に金額欄へ渡す**整数**（`Math.round` で四捨五入）

## 6. データの流れ

```
[金額欄] money付き → 右端に🧮ボタン
   ↓ タップ
[CalculatorSheet] 開く（今の入力値 value を parseYenAmount して初期 current にセット。acc/pending は空。0/空なら current も空）
   ↓ テンキー・演算子で操作（式と結果を上部に常時表示）
[確定] → confirmValue(state) を整数化
       → Input が onChange({ target: { value: formatAmount(整数) } }) を呼ぶ
       → 既存の親stateに、手入力と同じカンマ付き形式で入る
       → シート閉じる
[背景タップ / × / Esc] → onChange を呼ばず閉じる（元の値そのまま）
```

`Input` の `money` 時の `onChange` は既存も `formatAmount` 済みの値を親に渡している。電卓も同じ形式で渡すので、保存・集計ロジック（`parseYenAmount`）は無改修で整合する。

## 7. UI仕様（`CalculatorSheet.tsx`）

```
┌────────────────────┐
│  1,250 + 980          ✕ │ ← 式（上）＋閉じる
│            = 2,230       │ ← 結果（常時表示・tabular-nums）
├────────────────────┤
│  C    ⌫    ÷    ×       │
│  7    8    9    −       │
│  4    5    6    +       │
│  1    2    3            │
│  0    .    =            │
├────────────────────┤
│      確定する（シアン）      │ ← STYLE_BUTTON_PRIMARY
└────────────────────┘
```

- 既存トークンに統一: `COLOR_ACCENT`（シアン）/ `STYLE_BUTTON_PRIMARY` / `STYLE_INPUT` 系のグラスモーフィズム
- 数字は等幅（tabular-nums / monospace）で桁ブレを防ぐ
- ボトムシートは下からスライドイン。`prefers-reduced-motion` で動きを抑制（既存 index.css の対応を流用）
- アクセシビリティ: `role="dialog"` ＋ `aria-modal="true"`、Escで閉じる、各ボタンに `aria-label`、タップ領域 46px 以上

## 8. エラー処理

| ケース | 挙動 |
| --- | --- |
| `÷0` | ディスプレイに「エラー」、確定ボタンを無効化（押せない）。C で復帰 |
| 桁あふれ（整数12桁=兆超え） | それ以上の数字入力を受け付けない |
| 何も計算せず確定 | 初期値のまま反映（実質キャンセル） |
| 結果が負 | そのまま整数で反映（呼び出し側の用途次第。金額欄のバリデーションは既存のまま） |

## 9. テスト計画（vitest）

- `calculator.test.ts`（ロジック）
  - 加減乗除それぞれ / 逐次計算（`1+2×3=9`）/ `=` の連続 / backspace / clear
  - `÷0` でエラー / エラー中は確定値が出ない / C で復帰
  - 小数→確定で四捨五入（`10÷3` → 確定 `3`）
  - 桁あふれガード
- `CalculatorSheet.test.tsx`（UI）
  - 🧮タップでシートが開く / 数字入力→確定で金額欄に値が入る / 背景タップで値が変わらない
- 既存285テストを壊さない（`money` 以外の `Input` は従来通り素の `<input>` を返す）

## 10. スコープ外（やらないこと）

- メモリ機能（M+/M-/MR）、％ボタン、括弧、履歴
- 通貨単位の切り替え（円固定）
- 計算履歴の保存
- Context化（案C）は別タスクとして将来対応
