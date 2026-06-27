# 電卓テンキー入力（金額欄）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `money` 付き金額欄に四則演算つきの電卓ボトムシートを追加し、レシート合算や割り勘をアプリ内で完結させる。

**Architecture:** 計算ロジックを純粋関数（`calculator.ts`）に分離し、ボトムシートUI（`CalculatorSheet.tsx`）がそれを使う。共通 `Input`（`ui.tsx`）が `money` のとき自動で🧮ボタンとシートを持つので、呼び出し側（約12箇所）は無改修。

**Tech Stack:** React 18 / TypeScript / vitest + @testing-library/react / 既存スタイル定数（`utils/styles.ts`）

## Global Constraints

- 円は整数。割り算で小数が出ても**確定時に `Math.round` で四捨五入**して整数化（仕様 §2）
- 計算方式は**電卓式（逐次計算）**。`1,250 + 980 × 2` →「(1,250+980)×2 = 4,460」（×÷優先はしない）
- 桁あふれガード: 整数部 12 桁（兆未満）まで
- `money` 以外の `Input`（type=date 等）は**従来通り素の `<input>`** を返す（後方互換）
- 既存 285 テストを壊さない。`tsc` 0 エラー・`vite build` 緑を維持
- 既存スタイル定数を使う（`COLOR_ACCENT` / `STYLE_BUTTON_PRIMARY` / `COLOR_BORDER` 等）。新規の色直書きを増やさない
- vitest は `globals: true`（`describe/it/expect` は import 不要）。`vi` は `vitest` から、`render/screen/fireEvent` は `@testing-library/react` から import
- 仕上げに `package.json` の version を `1.6.9` → `1.7.0` に上げる（finance_web は変更時にバージョンを上げる方針）

## File Structure

```
src/utils/calculator.ts            ← 新規: 電卓の状態・計算（純粋関数のみ。Reactに依存しない）
src/components/CalculatorSheet.tsx ← 新規: ボトムシートUI（default export, open/onClose）
src/components/ui.tsx              ← 改修: Input が money時に🧮ボタン＋シートを持つ
src/index.css                     ← 改修: ボトムシートのスライドイン（reduced-motion対応）
src/test/utils/calculator.test.ts ← 新規: ロジックの単体テスト
src/test/components/CalculatorSheet.test.tsx ← 新規: シートの操作テスト
src/test/components/Input.calculator.test.tsx ← 新規: Input統合テスト
package.json                      ← 改修: version 1.7.0
```

---

### Task 1: 電卓の計算ロジック `calculator.ts`

純粋関数だけで状態機械を実装する。React に依存しないので単体テストしやすい。

**Files:**
- Create: `src/utils/calculator.ts`
- Test: `src/test/utils/calculator.test.ts`

**Interfaces:**
- Consumes: `parseYenAmount` from `src/utils/format.ts`
- Produces:
  - `type Operator = "+" | "-" | "*" | "/"`
  - `interface CalcState { current: string; previous: number | null; operation: Operator | null; overwrite: boolean; error: boolean }`
  - `type CalcAction = { type: "digit"; d: string } | { type: "dot" } | { type: "operator"; op: Operator } | { type: "equals" } | { type: "clear" } | { type: "backspace" }`
  - `initCalc(initial: string | number): CalcState`
  - `calcReducer(state: CalcState, action: CalcAction): CalcState`
  - `currentResult(state: CalcState): number | null`（エラー中は null）
  - `confirmValue(state: CalcState): number`（確定用の整数）
  - `formatExpression(state: CalcState): string`（上段の式表示）
  - `formatResult(n: number): string`（結果のカンマ表示・小数最大4桁）

- [ ] **Step 1: 失敗するテストを書く**

`src/test/utils/calculator.test.ts`:

```ts
// ────────── calculator.ts のユニットテスト ──────────
// 電卓の状態機械（純粋関数）を一通り検証する
import { initCalc, calcReducer, currentResult, confirmValue, formatExpression, formatResult, CalcState, CalcAction } from "../../utils/calculator";

// アクションを順番に適用していくヘルパー（テストを読みやすくするため）
function run(start: CalcState, ...actions: CalcAction[]): CalcState {
  return actions.reduce((s, a) => calcReducer(s, a), start);
}
// "1250" → [{digit:"1"},{digit:"2"},...] に変換するヘルパー
const digits = (str: string): CalcAction[] => str.split("").map(d => ({ type: "digit", d }));

describe("initCalc", () => {
  it("空・0 のときは current が空", () => {
    expect(initCalc("").current).toBe("");
    expect(initCalc(0).current).toBe("");
  });
  it("既存値はそのまま current に入る（カンマは除去）", () => {
    expect(initCalc("1,000").current).toBe("1000");
    expect(initCalc(2500).current).toBe("2500");
  });
});

describe("calcReducer: 基本の四則演算", () => {
  it("足し算 1250 + 980 = 2230", () => {
    const s = run(initCalc(""), ...digits("1250"), { type: "operator", op: "+" }, ...digits("980"), { type: "equals" });
    expect(confirmValue(s)).toBe(2230);
  });
  it("引き算 1000 - 200 = 800", () => {
    const s = run(initCalc(""), ...digits("1000"), { type: "operator", op: "-" }, ...digits("200"), { type: "equals" });
    expect(confirmValue(s)).toBe(800);
  });
  it("掛け算 12 × 3 = 36", () => {
    const s = run(initCalc(""), ...digits("12"), { type: "operator", op: "*" }, ...digits("3"), { type: "equals" });
    expect(confirmValue(s)).toBe(36);
  });
});

describe("calcReducer: 逐次計算（電卓式）", () => {
  it("1 + 2 × 3 は (1+2)×3 = 9（数学の優先順位ではない）", () => {
    const s = run(initCalc(""), ...digits("1"), { type: "operator", op: "+" }, ...digits("2"), { type: "operator", op: "*" }, ...digits("3"), { type: "equals" });
    expect(confirmValue(s)).toBe(9);
  });
  it("演算子の連続入力は最後の演算子で上書き 5 +（×に変更）2 = 10", () => {
    const s = run(initCalc(""), ...digits("5"), { type: "operator", op: "+" }, { type: "operator", op: "*" }, ...digits("2"), { type: "equals" });
    expect(confirmValue(s)).toBe(10);
  });
});

describe("calcReducer: 既存値からの継続", () => {
  it("初期値1000を開いて +500 = 1500", () => {
    const s = run(initCalc("1000"), { type: "operator", op: "+" }, ...digits("500"), { type: "equals" });
    expect(confirmValue(s)).toBe(1500);
  });
  it("初期値があっても数字を先に押すと打ち直しになる（9 → 9）", () => {
    const s = run(initCalc("1000"), ...digits("9"));
    expect(confirmValue(s)).toBe(9);
  });
});

describe("currentResult: 結果の常時プレビュー", () => {
  it("980 を入力中（演算子の右辺）に結果が更新される 1250 + 980 → 2230", () => {
    const s = run(initCalc(""), ...digits("1250"), { type: "operator", op: "+" }, ...digits("980"));
    expect(currentResult(s)).toBe(2230);
  });
  it("数字だけ入力中はその数字自身", () => {
    const s = run(initCalc(""), ...digits("42"));
    expect(currentResult(s)).toBe(42);
  });
});

describe("calcReducer: ÷0 エラー", () => {
  it("10 ÷ 0 はエラーになり、結果は null", () => {
    const s = run(initCalc(""), ...digits("10"), { type: "operator", op: "/" }, ...digits("0"), { type: "equals" });
    expect(s.error).toBe(true);
    expect(currentResult(s)).toBeNull();
  });
  it("clear でエラーから復帰する", () => {
    const s = run(initCalc(""), ...digits("10"), { type: "operator", op: "/" }, ...digits("0"), { type: "equals" }, { type: "clear" });
    expect(s.error).toBe(false);
    expect(confirmValue(s)).toBe(0);
  });
});

describe("confirmValue: 小数は四捨五入で整数化", () => {
  it("10 ÷ 3 = 3.333... → 確定で 3", () => {
    const s = run(initCalc(""), ...digits("10"), { type: "operator", op: "/" }, ...digits("3"), { type: "equals" });
    expect(confirmValue(s)).toBe(3);
  });
  it("5 ÷ 2 = 2.5 → 確定で 3（四捨五入）", () => {
    const s = run(initCalc(""), ...digits("5"), { type: "operator", op: "/" }, ...digits("2"), { type: "equals" });
    expect(confirmValue(s)).toBe(3);
  });
});

describe("桁あふれガード", () => {
  it("整数13桁目は受け付けない（12桁で止まる）", () => {
    const s = run(initCalc(""), ...digits("12345678901234"));
    expect(s.current.replace(/[^\d]/g, "").length).toBe(12);
  });
});

describe("backspace と小数点", () => {
  it("backspace で1文字消える", () => {
    const s = run(initCalc(""), ...digits("123"), { type: "backspace" });
    expect(s.current).toBe("12");
  });
  it("小数点は1つしか入らない", () => {
    const s = run(initCalc(""), ...digits("1"), { type: "dot" }, { type: "dot" }, ...digits("5"));
    expect(s.current).toBe("1.5");
  });
});

describe("formatExpression / formatResult", () => {
  it("式が「1,250 ＋ 980」のように出る", () => {
    const s = run(initCalc(""), ...digits("1250"), { type: "operator", op: "+" }, ...digits("980"));
    expect(formatExpression(s)).toBe("1,250 ＋ 980");
  });
  it("formatResult はカンマ区切り、小数は最大4桁", () => {
    expect(formatResult(2230)).toBe("2,230");
    expect(formatResult(3.3333333)).toBe("3.3333");
  });
});
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `cd finance_web && npx vitest run src/test/utils/calculator.test.ts`
Expected: FAIL（`Cannot find module '../../utils/calculator'`）

- [ ] **Step 3: 最小実装を書く**

`src/utils/calculator.ts`:

```ts
// ────────── 電卓の計算ロジック（純粋関数のみ） ──────────
// Reactに依存しないので、この1ファイルだけで単体テストできる
import { parseYenAmount } from "./format";

// 使える演算子の種類
export type Operator = "+" | "-" | "*" | "/";

// 電卓の状態（current=今表示・入力中の数字 / previous=演算子の左辺 / operation=押された演算子 /
//  overwrite=次に数字を押したら current を上書きするか / error=÷0などのエラー中か）
export interface CalcState {
  current: string;
  previous: number | null;
  operation: Operator | null;
  overwrite: boolean;
  error: boolean;
}

// 電卓に対する操作（ボタン1つ＝1アクション）
export type CalcAction =
  | { type: "digit"; d: string }
  | { type: "dot" }
  | { type: "operator"; op: Operator }
  | { type: "equals" }
  | { type: "clear" }
  | { type: "backspace" };

// 整数部の最大桁数（兆の手前まで）
export const MAX_INT_DIGITS = 12;

// 演算子の記号（画面表示用。マイナスは見やすい全角マイナス）
const OP_SYMBOL: Record<Operator, string> = { "+": "＋", "-": "−", "*": "×", "/": "÷" };

// まっさらな状態を作る（clear と初期化で共用）
function emptyState(): CalcState {
  return { current: "", previous: null, operation: null, overwrite: true, error: false };
}

// 初期状態を作る（金額欄の今の値を current に入れる。0や空なら空にする）
export function initCalc(initial: string | number): CalcState {
  const n = parseYenAmount(initial); // 数字以外を除いた整数
  return { ...emptyState(), current: n === 0 ? "" : String(n) };
}

// 実際の四則演算。÷0 のときだけ null を返す（呼び出し側でエラー化する）
function apply(a: number, op: Operator, b: number): number | null {
  switch (op) {
    case "+": return a + b;
    case "-": return a - b;
    case "*": return a * b;
    case "/": return b === 0 ? null : a / b;
  }
}

// エラー状態を作る共通処理
function toError(): CalcState {
  return { ...emptyState(), error: true };
}

// 状態＋アクション → 新しい状態（純粋関数）
export function calcReducer(state: CalcState, action: CalcAction): CalcState {
  switch (action.type) {
    case "clear":
      return emptyState();

    case "digit": {
      if (state.error) return state;
      // overwrite中（演算子や=の直後・開いた直後）は新しく打ち直す
      if (state.overwrite) {
        return { ...state, current: action.d, overwrite: false };
      }
      // 桁あふれガード（整数部の数字だけ数える。小数を打ち始めたら制限しない）
      const intLen = state.current.split(".")[0].replace(/[^\d]/g, "").length;
      if (!state.current.includes(".") && intLen >= MAX_INT_DIGITS) return state;
      // 先頭の余分な0を防ぐ（"0" の次は置き換え）
      if (state.current === "0") return { ...state, current: action.d };
      return { ...state, current: state.current + action.d };
    }

    case "dot": {
      if (state.error) return state;
      if (state.overwrite) return { ...state, current: "0.", overwrite: false };
      if (state.current.includes(".")) return state;
      if (state.current === "") return { ...state, current: "0." };
      return { ...state, current: state.current + "." };
    }

    case "operator": {
      if (state.error) return state;
      // まだ左辺が無いとき → current を左辺にして演算子をセット
      if (state.previous === null) {
        const cur = state.current === "" ? 0 : Number(state.current);
        return { ...state, previous: cur, operation: action.op, overwrite: true };
      }
      // 演算子の連打（overwrite中）→ 演算子だけ差し替え
      if (state.overwrite) {
        return { ...state, operation: action.op };
      }
      // 逐次計算：いったん previous と current を計算してから次の演算子へ
      const result = apply(state.previous, state.operation!, Number(state.current));
      if (result === null) return toError();
      return { ...state, previous: result, current: String(result), operation: action.op, overwrite: true };
    }

    case "equals": {
      if (state.error || state.previous === null || state.operation === null) return state;
      const right = state.current === "" ? state.previous : Number(state.current);
      const result = apply(state.previous, state.operation, right);
      if (result === null) return toError();
      return { ...state, current: String(result), previous: null, operation: null, overwrite: true };
    }

    case "backspace": {
      if (state.error) return emptyState();
      if (state.overwrite) return state;
      return { ...state, current: state.current.slice(0, -1) };
    }
  }
}

// いま画面に出すべき計算結果（演算子の右辺を入力中なら途中結果をプレビュー）
export function currentResult(state: CalcState): number | null {
  if (state.error) return null;
  // 左辺・演算子があって右辺を入力中 → 途中結果を出す
  if (state.previous !== null && state.operation && !state.overwrite && state.current !== "") {
    return apply(state.previous, state.operation, Number(state.current));
  }
  if (state.current !== "") return Number(state.current);
  if (state.previous !== null) return state.previous;
  return 0;
}

// 確定ボタンで金額欄へ渡す整数（小数は四捨五入）
export function confirmValue(state: CalcState): number {
  const r = currentResult(state);
  return Math.round(r ?? 0);
}

// 数字文字列をカンマ区切りに（入力中の小数もそのまま見せる）
function formatNumberString(numStr: string): string {
  if (numStr === "") return "";
  const [intPart, decPart] = numStr.split(".");
  const intFmt = Number(intPart || "0").toLocaleString("ja-JP");
  return decPart !== undefined ? `${intFmt}.${decPart}` : intFmt;
}

// 上段に出す式（例: "1,250 ＋ 980"）
export function formatExpression(state: CalcState): string {
  if (state.error) return "エラー";
  if (state.previous === null) return formatNumberString(state.current);
  const left = formatNumberString(String(state.previous));
  const op = state.operation ? ` ${OP_SYMBOL[state.operation]} ` : "";
  const right = state.overwrite ? "" : formatNumberString(state.current);
  return `${left}${op}${right}`.trimEnd();
}

// 結果の表示（カンマ区切り・小数は最大4桁まで）
export function formatResult(n: number): string {
  return n.toLocaleString("ja-JP", { maximumFractionDigits: 4 });
}
```

- [ ] **Step 4: テストが通ることを確認**

Run: `cd finance_web && npx vitest run src/test/utils/calculator.test.ts`
Expected: PASS（全ケース緑）

- [ ] **Step 5: 型チェック**

Run: `cd finance_web && npx tsc --noEmit`
Expected: エラー 0

- [ ] **Step 6: コミット**

```bash
cd finance_web && git add src/utils/calculator.ts src/test/utils/calculator.test.ts && git commit -m "feat(calc): 電卓の計算ロジック（純粋関数）を追加"
```

---

### Task 2: ボトムシートUI `CalculatorSheet.tsx`

Task 1 のロジックを使う表示部分。テンキー・演算子・式/結果ディスプレイ・確定ボタン。

**Files:**
- Create: `src/components/CalculatorSheet.tsx`
- Modify: `src/index.css`（スライドインのkeyframes追加）
- Test: `src/test/components/CalculatorSheet.test.tsx`

**Interfaces:**
- Consumes: `initCalc`, `calcReducer`, `currentResult`, `confirmValue`, `formatExpression`, `formatResult`, `Operator` from `src/utils/calculator.ts`; スタイル定数 from `src/utils/styles.ts`
- Produces: `export default function CalculatorSheet(props: CalculatorSheetProps)` with `interface CalculatorSheetProps { open: boolean; initialValue: string | number; onConfirm: (value: number) => void; onClose: () => void }`

- [ ] **Step 1: 失敗するテストを書く**

`src/test/components/CalculatorSheet.test.tsx`:

```tsx
// ────────── CalculatorSheet（電卓ボトムシート）のテスト ──────────
import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import CalculatorSheet from "../../components/CalculatorSheet";

const noop = () => {};

// ボタンを aria-label で押すヘルパー
function press(label: string) {
  fireEvent.click(screen.getByRole("button", { name: label }));
}

describe("CalculatorSheet", () => {
  it("open=false のとき何も表示されない", () => {
    const { container } = render(
      <CalculatorSheet open={false} initialValue="" onConfirm={noop} onClose={noop} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("1250 + 980 を計算して確定すると onConfirm(2230) が呼ばれる", () => {
    const onConfirm = vi.fn();
    render(<CalculatorSheet open={true} initialValue="" onConfirm={onConfirm} onClose={noop} />);
    "1250".split("").forEach(d => press(d));
    press("たす");
    "980".split("").forEach(d => press(d));
    press("確定する");
    expect(onConfirm).toHaveBeenCalledWith(2230);
  });

  it("÷0 のときは確定ボタンが無効", () => {
    render(<CalculatorSheet open={true} initialValue="" onConfirm={noop} onClose={noop} />);
    press("1"); press("0"); press("わる"); press("0"); press("イコール");
    expect(screen.getByRole("button", { name: "確定する" })).toBeDisabled();
  });

  it("背景タップで onClose が呼ばれ、onConfirm は呼ばれない", () => {
    const onConfirm = vi.fn();
    const onClose = vi.fn();
    render(<CalculatorSheet open={true} initialValue="500" onConfirm={onConfirm} onClose={onClose} />);
    fireEvent.click(screen.getByTestId("calc-overlay"));
    expect(onClose).toHaveBeenCalled();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("Escキーで onClose が呼ばれる", () => {
    const onClose = vi.fn();
    render(<CalculatorSheet open={true} initialValue="" onConfirm={noop} onClose={onClose} />);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `cd finance_web && npx vitest run src/test/components/CalculatorSheet.test.tsx`
Expected: FAIL（`Cannot find module '../../components/CalculatorSheet'`）

- [ ] **Step 3: index.css にスライドインを追加**

`src/index.css` の末尾に追記（既存の `prefers-reduced-motion` 方針に合わせ、低減設定では動かさない）:

```css
/* 電卓ボトムシートのスライドイン */
@keyframes calc-sheet-up {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}
.calc-sheet { animation: calc-sheet-up 0.22s ease-out; }
@media (prefers-reduced-motion: reduce) {
  .calc-sheet { animation: none; }
}
```

- [ ] **Step 4: CalculatorSheet を実装**

`src/components/CalculatorSheet.tsx`:

```tsx
// ────────── 電卓ボトムシート ──────────
// 金額欄の🧮ボタンから開く。テンキーと四則演算で計算し、「確定」で金額欄へ値を返す
import { useReducer, useEffect, CSSProperties } from "react";
import { initCalc, calcReducer, currentResult, confirmValue, formatExpression, formatResult, Operator } from "../utils/calculator";
import { COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BORDER, COLOR_NEGATIVE, STYLE_BUTTON_PRIMARY } from "../utils/styles";

interface CalculatorSheetProps {
  open: boolean;                       // 開いているか
  initialValue: string | number;       // 金額欄の今の値
  onConfirm: (value: number) => void;  // 確定したとき呼ぶ（整数を渡す）
  onClose: () => void;                  // 確定せず閉じるとき呼ぶ
}

// ボタン1個の見た目（数字・演算子で色を少し変える）
const STYLE_KEY_BASE: CSSProperties = {
  border: `1px solid ${COLOR_BORDER}`,
  borderRadius: 12,
  background: "rgba(148,163,184,0.06)",
  color: COLOR_TEXT_PRIMARY,
  fontSize: 20,
  fontWeight: 600,
  fontFamily: "inherit",
  minHeight: 52,
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

// 演算子ボタンの表示記号と読み上げラベル
const OP_KEYS: Record<Operator, { label: string; aria: string }> = {
  "/": { label: "÷", aria: "わる" },
  "*": { label: "×", aria: "かける" },
  "-": { label: "−", aria: "ひく" },
  "+": { label: "＋", aria: "たす" },
};

export default function CalculatorSheet({ open, initialValue, onConfirm, onClose }: CalculatorSheetProps) {
  // open するたびに金額欄の今の値で初期化し直す
  const [state, dispatch] = useReducer(calcReducer, initialValue, initCalc);

  // open かつ initialValue が変わったら current を作り直す（clearしてから初期値の数字を流し込む）
  useEffect(() => {
    if (!open) return;
    dispatch({ type: "clear" });
    const digits = String(initialValue).replace(/[^\d]/g, "");
    for (const d of digits) dispatch({ type: "digit", d });
  }, [open, initialValue]);

  // Escキーで閉じる
  useEffect(() => {
    if (!open) return;
    const onKey = (e: globalThis.KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const result = currentResult(state);
  const canConfirm = !state.error && result !== null;

  // 数字ボタンを作る
  const digitKey = (d: string) => (
    <button key={d} type="button" aria-label={d} onClick={() => dispatch({ type: "digit", d })} style={STYLE_KEY_BASE}>{d}</button>
  );
  // 演算子ボタンを作る
  const opKey = (op: Operator) => (
    <button key={op} type="button" aria-label={OP_KEYS[op].aria} onClick={() => dispatch({ type: "operator", op })}
      style={{ ...STYLE_KEY_BASE, color: COLOR_ACCENT, fontWeight: 700 }}>{OP_KEYS[op].label}</button>
  );

  return (
    <div data-testid="calc-overlay" onClick={onClose}
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 300, display: "flex", alignItems: "flex-end", justifyContent: "center" }}>
      <div className="calc-sheet" onClick={e => e.stopPropagation()} role="dialog" aria-modal="true" aria-label="電卓"
        style={{ width: "100%", maxWidth: 420, background: "rgba(15,23,42,0.98)", backdropFilter: "blur(20px)", borderTopLeftRadius: 22, borderTopRightRadius: 22, border: `1px solid ${COLOR_BORDER}`, padding: 16, boxSizing: "border-box" }}>

        {/* ── ディスプレイ（上段=式 / 下段=結果。常時表示） ── */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
          <button type="button" aria-label="閉じる" onClick={onClose} style={{ background: "none", border: "none", color: COLOR_TEXT_SECONDARY, fontSize: 20, cursor: "pointer", padding: 4 }}>✕</button>
          <div style={{ flex: 1, textAlign: "right", overflow: "hidden" }}>
            <div style={{ fontSize: 13, color: COLOR_TEXT_SECONDARY, minHeight: 18, fontFamily: "ui-monospace, monospace", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {formatExpression(state)}
            </div>
            <div style={{ fontSize: 30, fontWeight: 700, color: state.error ? COLOR_NEGATIVE : COLOR_TEXT_PRIMARY, fontFamily: "ui-monospace, monospace", fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {state.error ? "エラー" : formatResult(result ?? 0)}
            </div>
          </div>
        </div>

        {/* ── テンキー（4列） ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, marginTop: 10 }}>
          <button type="button" aria-label="クリア" onClick={() => dispatch({ type: "clear" })} style={{ ...STYLE_KEY_BASE, color: COLOR_NEGATIVE }}>C</button>
          <button type="button" aria-label="1文字消す" onClick={() => dispatch({ type: "backspace" })} style={STYLE_KEY_BASE}>⌫</button>
          {opKey("/")}
          {opKey("*")}
          {["7", "8", "9"].map(digitKey)}{opKey("-")}
          {["4", "5", "6"].map(digitKey)}{opKey("+")}
          {["1", "2", "3"].map(digitKey)}
          <button type="button" aria-label="イコール" onClick={() => dispatch({ type: "equals" })} style={{ ...STYLE_KEY_BASE, gridRow: "span 2", color: COLOR_ACCENT, fontWeight: 700 }}>=</button>
          {digitKey("0")}
          <button type="button" aria-label="小数点" onClick={() => dispatch({ type: "dot" })} style={STYLE_KEY_BASE}>.</button>
        </div>

        {/* ── 確定ボタン ── */}
        <button type="button" aria-label="確定する" disabled={!canConfirm}
          onClick={() => { onConfirm(confirmValue(state)); onClose(); }}
          style={{ ...STYLE_BUTTON_PRIMARY, marginTop: 12, opacity: canConfirm ? 1 : 0.4, cursor: canConfirm ? "pointer" : "not-allowed" }}>
          確定する
        </button>
      </div>
    </div>
  );
}
```

> 補足: `=` ボタンは2行ぶん（`gridRow: "span 2"`）なので、グリッドの並びは「1 2 3 =」「0 . （=が続く）」になる。テンキーが12マス＋演算子で破綻しないことを Step 5 の画面テスト（数字が押せる）で担保する。

- [ ] **Step 5: テストが通ることを確認**

Run: `cd finance_web && npx vitest run src/test/components/CalculatorSheet.test.tsx`
Expected: PASS

- [ ] **Step 6: 型チェック**

Run: `cd finance_web && npx tsc --noEmit`
Expected: エラー 0

- [ ] **Step 7: コミット**

```bash
cd finance_web && git add src/components/CalculatorSheet.tsx src/index.css src/test/components/CalculatorSheet.test.tsx && git commit -m "feat(calc): 電卓ボトムシートUIを追加"
```

---

### Task 3: 共通 `Input` に🧮ボタンを統合

`money` 付き `Input` のときだけ、右端に🧮ボタンと電卓シートを出す。`money` 以外は今まで通り素の `<input>`。

**Files:**
- Modify: `src/components/ui.tsx`（`Input` コンポーネント・import）
- Test: `src/test/components/Input.calculator.test.tsx`

**Interfaces:**
- Consumes: `CalculatorSheet` from `src/components/CalculatorSheet.tsx`; `formatAmount` from `src/utils/format.ts`（既存import）
- Produces: `Input` の公開APIは不変（`value/onChange/type/placeholder/style/money` のまま）。`money` 時に内部で🧮ボタンと確定処理を持つ

- [ ] **Step 1: 失敗するテストを書く**

`src/test/components/Input.calculator.test.tsx`:

```tsx
// ────────── Input の電卓統合テスト ──────────
import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { Input } from "../../components/ui";

function press(label: string) {
  fireEvent.click(screen.getByRole("button", { name: label }));
}

describe("Input + 電卓", () => {
  it("money のとき🧮ボタンが出る", () => {
    render(<Input money value="" onChange={() => {}} placeholder="金額（円）" />);
    expect(screen.getByRole("button", { name: "電卓を開く" })).toBeInTheDocument();
  });

  it("money でないとき🧮ボタンは出ない", () => {
    render(<Input value="" onChange={() => {}} placeholder="メモ" />);
    expect(screen.queryByRole("button", { name: "電卓を開く" })).not.toBeInTheDocument();
  });

  it("🧮→計算→確定で onChange にカンマ整形済みの値が渡る", () => {
    const onChange = vi.fn();
    render(<Input money value="" onChange={onChange} placeholder="金額（円）" />);
    press("電卓を開く");
    "1250".split("").forEach(d => press(d));
    press("たす");
    "980".split("").forEach(d => press(d));
    press("確定する");
    expect(onChange).toHaveBeenCalledWith({ target: { value: "2,230" } });
  });
});
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `cd finance_web && npx vitest run src/test/components/Input.calculator.test.tsx`
Expected: FAIL（🧮ボタンが存在しない）

- [ ] **Step 3: `ui.tsx` の import に `CalculatorSheet` を追加**

`src/components/ui.tsx` の先頭の import 群に1行追加する（既存の `import { useState, useEffect, ChangeEvent, ... } from "react";` はそのまま。`useState` は既に import 済み）:

```tsx
import CalculatorSheet from "./CalculatorSheet";
```

- [ ] **Step 4: `Input` 本体を差し替える**

`src/components/ui.tsx:136-143`（`export const Input = forwardRef(...)` から `Input.displayName = "Input";` まで）を、以下に**まるごと置き換える**:

```tsx
export const Input = forwardRef<HTMLInputElement, InputProps>(({value, onChange, type, placeholder, style, money}, ref) => {
  // フックは必ず関数の先頭で（条件分岐より前で）呼ぶ ← Reactのルール
  const [calcOpen, setCalcOpen] = useState(false);

  // money の時は画面に出す値をカンマ付きに整える
  const display = money ? formatAmount(value) : value;
  // money の時は入力イベントを横取りして数字だけ抜き出し→整形してから onChange へ渡す
  const handle = money ? (e: ChangeEvent<HTMLInputElement>) => onChange({target:{value:formatAmount(e.target.value)}}) : onChange;

  // money でないときは今まで通り素の input を返す（後方互換・🧮なし）
  if (!money) {
    return <input ref={ref} type={type==="number"?"text":type||"text"} value={display} onChange={handle as any} placeholder={placeholder} style={{...STYLE_INPUT,...style}} inputMode={type==="number"?"numeric":type==="date"?undefined:"text"}/>;
  }

  // money のときは input の右に🧮ボタンを重ね、押すと電卓シートを開く
  return (
    <div style={{position:"relative"}}>
      <input ref={ref} type="text" value={display} onChange={handle as any} placeholder={placeholder}
        style={{...STYLE_INPUT, paddingRight:44, ...style}} inputMode="numeric"/>
      {/* 🧮ボタン：押すと電卓ボトムシートを開く（普段のフリック入力はそのまま使える） */}
      <button type="button" aria-label="電卓を開く" onClick={()=>setCalcOpen(true)}
        style={{position:"absolute", right:6, top:"50%", transform:"translateY(-50%)", background:"none", border:"none", cursor:"pointer", fontSize:20, padding:4, lineHeight:1}}>
        🧮
      </button>
      <CalculatorSheet open={calcOpen} initialValue={value}
        onConfirm={(v)=>onChange({target:{value:formatAmount(String(v))}})}
        onClose={()=>setCalcOpen(false)}/>
    </div>
  );
});
Input.displayName = "Input";
```

- [ ] **Step 5: テストが通ることを確認**

Run: `cd finance_web && npx vitest run src/test/components/Input.calculator.test.tsx`
Expected: PASS

- [ ] **Step 6: 既存テスト全体が壊れていないか確認**

Run: `cd finance_web && npx vitest run`
Expected: 既存285＋新規すべて PASS。特に `TxRow.test.tsx` / `FxRow.test.tsx` / `LoanCard.test.tsx`（`money` Input を使う行）が緑であること

- [ ] **Step 7: 型チェック**

Run: `cd finance_web && npx tsc --noEmit`
Expected: エラー 0

- [ ] **Step 8: コミット**

```bash
cd finance_web && git add src/components/ui.tsx src/test/components/Input.calculator.test.tsx && git commit -m "feat(calc): money入力欄に🧮ボタンで電卓を統合"
```

---

### Task 4: バージョン更新と最終検証

**Files:**
- Modify: `package.json`（version）

- [ ] **Step 1: バージョンを上げる**

`package.json:3` の `"version": "1.6.9"` を `"version": "1.7.0"` に変更。

- [ ] **Step 2: 全テスト**

Run: `cd finance_web && npx vitest run`
Expected: 全 PASS

- [ ] **Step 3: 型チェック**

Run: `cd finance_web && npx tsc --noEmit`
Expected: エラー 0

- [ ] **Step 4: 本番ビルド**

Run: `cd finance_web && npx vite build`
Expected: 成功（エラーなし）

- [ ] **Step 5: コミット**

```bash
cd finance_web && git add package.json && git commit -m "chore: v1.7.0（電卓テンキー入力）"
```

---

## デプロイ（実装後・ユーザー操作）

このプランは本番デプロイを含まない。実装完了後、別途：

```
cd finance_web && npx vercel --prod
```

※ 電卓機能はサーバーAPI（同期）に依存しないため、電卓単体では Vercel env の追加は不要。前回リファクタ分を同時に本番反映する場合のみ、別メモにある `SYNC_OPEN_ACCESS=true`（Production）の設定が必要。

## 完了の定義

- 🧮ボタンが全 `money` 金額欄に出る／`money` 以外には出ない
- 四則演算・逐次計算・÷0エラー・四捨五入確定が動く
- 既存285＋新規テストがすべて緑、`tsc` 0、`vite build` 成功
- `package.json` が v1.7.0
