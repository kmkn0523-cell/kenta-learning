# Finance Web UX Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** finance_web 家計管理アプリの保守性・型安全性・ユーザビリティを 3 フェーズで段階的に改善する（リネーム＋型強化＋エラーハンドリング → コンポーネント分割＋メモ化 → PWA／振替／検索／カテゴリカスタマイズ）。

**Architecture:** 既存の React 18 + TypeScript + Vite 構成・PasswordGate + AES-GCM の暗号化永続化スキームはそのまま維持し、内部実装のみ段階的にリファクタリングする。Phase 1 は識別子と型と例外処理だけを触る純粋な「整理」、Phase 2 は God Component (`App.tsx` 430 行) を views/hooks/utils に分割、Phase 3 は新機能 (PWA・振替・検索・カテゴリ) を任意項目で追加。既存 localStorage データはマイグレーションで自動変換。

**Tech Stack:** React 18.3.1, TypeScript, Vite 5.4.1, Vitest 4.1.6, @testing-library/react 16.3.2, @testing-library/user-event 14.6.1, jsdom 29.1.1, recharts 3.8.1, Web Crypto API (PBKDF2 + AES-GCM), vite-plugin-pwa (Phase 3 で追加・要承認)

---

## 全体ルール

- **TDD 厳守**: 新機能・バグ修正は「失敗するテスト → 実装 → テスト通過 → コミット」の順。リネームは「ベースラインで全テスト緑 → リネーム → 全テスト緑」で安全網にする。
- **コミット粒度**: タスク単位で 1 コミット。タスク内で複数ファイルを触っても 1 コミットにまとめる。
- **コメント**: 初心者向け日本語コメント（各行レベル）を維持。既存スタイルに合わせる。
- **既存機能を壊さない**: 関係ない部分には触らない。リネーム以外の動作変更を混入させない。
- **エラーハンドリング**: 空 catch は禁止。最低でも `console.warn("[location] description", { key, error })`、ユーザー影響時は Toast 通知。
- **作業ディレクトリ**: 全ての相対パスは `/home/kenta_kamijyo/finance_web/` を基準。
- **テスト実行**: 各タスク末で `cd /home/kenta_kamijyo/finance_web && npm test -- --run` を実行（CI モード）。
- **npm install は要承認**: 新ライブラリインストールは CLAUDE.md ルール通り事前承認を取る。

---

## Phase 1: リネーム＋型強化＋エラーハンドリング

**目的:** コードの可読性と型安全性を上げる。動作は一切変えない。

**Phase 1 完了条件:**
- 既存テストが全て pass
- 旧名称（BG/T/T2/AC/POS/NEG/MLS/ECATS/yen/mInt/tInt/Inp/Sel/tx/fx/lo/cf/bl/inc/a1〜a9 など）が grep でヒットしない
- `git grep -nE "catch\s*\([_a-zA-Z]+\)\s*\{\s*\}"` で空 catch がゼロ
- types.ts の `amount` 型が `number` のみになっている
- `useState(null)` のように型推論で `null` になっている箇所がゼロ

---

### Task 1.1: ベースライン確認

**Files:**
- Read: `package.json`
- Run: `npm test -- --run`

- [ ] **Step 1: 現状のテストが全て通ることを確認**

Run:
```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run
```
Expected: 全テスト pass（既存: TxRow/LoanCard/FxRow/format/loanCalc）。1 件でも fail があれば**そこを先に直してから**次タスクへ進む（リネームで起こったエラーか元からあったかを区別できなくなるため）。

- [ ] **Step 2: 旧名称の出現箇所を grep で記録**

Run:
```bash
cd /home/kenta_kamijyo/finance_web && git grep -nE '\b(BG|T2|T3|BD|AC|POS|NEG|MLS|ECATS|FCATS|ICATS|EICO|FICO|IICO|mInt|tInt|cDate|Inp|Sel|PwInput|Dlg|yen|parseAmount)\b' src
```
Expected: 出現リストが返る（後でリネーム漏れがないか比較するための基準）。出力をコピーして手元のメモに保存しておく。

- [ ] **Step 3: 状態保存（コミットは不要、ただし作業前に clean を確認）**

Run:
```bash
cd /home/kenta_kamijyo/finance_web && git status
```
Expected: `nothing to commit, working tree clean` または直前の変更が全てステージ済み。dirty な変更が残っていれば先に commit するかユーザーに確認する。

---

### Task 1.2: styles.ts の識別子リネーム

**Files:**
- Modify: `src/utils/styles.ts`
- Modify: `src/components/ui.tsx`
- Modify: `src/components/PasswordGate.tsx` (該当箇所のみ)
- Modify: 全ての `src/**/*.tsx` で `BG/T/T2/T3/BD/AC/POS/NEG/CARD/IS/BS/OS` を import している箇所

- [ ] **Step 1: styles.ts の export 名を全置換**

`src/utils/styles.ts` を以下に書き換え:

```ts
// ────────── スタイル定数まとめ ──────────
// アプリ全体で繰り返し使う色・スタイルをひとまとめにしたファイル

// 背景色・文字色の定数
export const COLOR_BACKGROUND = "#070b14";        // ページの背景（ダークネイビー）
export const COLOR_TEXT_PRIMARY = "#f0f4ff";      // メインの文字色（クールホワイト）
export const COLOR_TEXT_SECONDARY = "#94a3b8";    // サブの文字色（スレートグレー）
export const COLOR_TEXT_HINT = "#475569";         // ヒント・補足テキストの色（暗めスレート）
export const COLOR_BORDER = "rgba(148,163,184,0.12)"; // ボーダー色（青みがかった透明）
export const COLOR_ACCENT = "#22d3ee";            // アクセントカラー（フィンテックサイアン）
export const COLOR_POSITIVE = "#10b981";          // プラス・収入を示す緑（エメラルド）
export const COLOR_NEGATIVE = "#f43f5e";          // マイナス・支出を示す赤（ローズ）

// カードのスタイル（情報をまとめるブロックの外見）
export const STYLE_CARD = {background:"rgba(15,23,42,0.9)",border:`1px solid ${COLOR_BORDER}`,borderRadius:18,padding:20,marginBottom:14};

// 入力欄（input/select）の共通スタイル
export const STYLE_INPUT = {background:"rgba(148,163,184,0.06)",border:`1px solid ${COLOR_BORDER}`,borderRadius:12,padding:"12px 14px",color:COLOR_TEXT_PRIMARY,fontSize:16,outline:"none",width:"100%",fontFamily:"inherit",minHeight:46,boxSizing:"border-box"};

// プライマリボタン（保存・追加など）の共通スタイル
export const STYLE_BUTTON_PRIMARY = {border:"none",borderRadius:12,padding:"13px 0",cursor:"pointer",fontSize:15,fontWeight:700,background:COLOR_ACCENT,color:"#070b14",width:"100%",fontFamily:"inherit",minHeight:46};

// セカンダリボタン（キャンセル・編集など）の共通スタイル
export const STYLE_BUTTON_OUTLINE = {background:"transparent",border:`1px solid ${COLOR_BORDER}`,borderRadius:12,padding:"9px 16px",cursor:"pointer",fontSize:13,color:COLOR_TEXT_SECONDARY,fontFamily:"inherit",minHeight:40};
```

- [ ] **Step 2: 利用側を一括置換（grep で漏れがないか確認）**

Run:
```bash
cd /home/kenta_kamijyo/finance_web && git grep -lE '\b(BG|T2|T3|BD|AC|POS|NEG|CARD|IS|BS|OS)\b' src
```

各ファイルで以下の対応で `Edit` の `replace_all: true` を使う（文字列単位で `T` のような短い名は誤マッチに注意。必ず **import 行の名前** と **参照箇所のスペル境界** を明示する文脈で置換すること。例: `, T,` → `, COLOR_TEXT_PRIMARY,`、`color:T` → `color:COLOR_TEXT_PRIMARY`）:

| 旧 | 新 |
|---|---|
| `BG` | `COLOR_BACKGROUND` |
| `T` (注: 単独使用箇所のみ) | `COLOR_TEXT_PRIMARY` |
| `T2` | `COLOR_TEXT_SECONDARY` |
| `T3` | `COLOR_TEXT_HINT` |
| `BD` | `COLOR_BORDER` |
| `AC` | `COLOR_ACCENT` |
| `POS` | `COLOR_POSITIVE` |
| `NEG` | `COLOR_NEGATIVE` |
| `CARD` | `STYLE_CARD` |
| `IS` | `STYLE_INPUT` |
| `BS` | `STYLE_BUTTON_PRIMARY` |
| `OS` | `STYLE_BUTTON_OUTLINE` |

**注意:** `T` は React の `T` ジェネリック等と衝突しうる。必ず `from "../utils/styles"` の import 行を起点に追跡してから置換する。手順:
1. import 文を見つける: `import { ..., T, ... } from "../utils/styles"`
2. import 文を新名称に書き換える
3. tsc で「`T` is undefined」エラーが出る箇所を **その場で** `COLOR_TEXT_PRIMARY` に置換

- [ ] **Step 3: テスト実行**

Run:
```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run
```
Expected: 全テスト pass。

- [ ] **Step 4: 型チェック実行**

Run:
```bash
cd /home/kenta_kamijyo/finance_web && npx tsc --noEmit
```
Expected: エラー 0 件。

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/utils/styles.ts src/components src/views 2>/dev/null; git add -u src; git commit -m "refactor(styles): rename style constants to full descriptive names"
```

---

### Task 1.3: format.ts の識別子リネーム

**Files:**
- Modify: `src/utils/format.ts`
- Modify: 利用側全て（`src/App.tsx`, `src/components/*.tsx`, `src/test/utils/format.test.ts`）

- [ ] **Step 1: format.ts を書き換え**

```ts
// ────────── 文字列・数値フォーマットまとめ ──────────

// 文字列の amount から数字以外を除去して整数化
export function parseYenAmount(text: string | number): number {
  if (typeof text === "number") return text;
  const cleaned = String(text).replace(/[^\d]/g, "");
  return cleaned === "" ? 0 : Number(cleaned);
}

// 入力中の amount を 3 桁カンマ付きで整形（例: "12345" → "12,345"）
export function formatAmount(value: string | number): string {
  const num = parseYenAmount(value);
  return num === 0 && (value === "" || value === null || value === undefined)
    ? ""
    : num.toLocaleString("ja-JP");
}

// 金額を「¥1,234」形式で表示
export function formatYen(value: number): string {
  return "¥" + Math.round(value).toLocaleString("ja-JP");
}

// 月のラベル（チャート等で使う）
export const MONTH_LABELS = ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"];

// 変動費カテゴリの一覧
export const EXPENSE_CATEGORIES = ["食費","交通","娯楽","衣服","美容","医療","交際","教育","その他"];

// 固定費カテゴリの一覧
export const FIXED_EXPENSE_CATEGORIES = ["家賃","通信","保険","サブスク","光熱","その他"];

// 収入カテゴリの一覧
export const INCOME_CATEGORIES = ["給与","副業","賞与","投資","その他"];

// 変動費カテゴリの絵文字
export const EXPENSE_CATEGORY_ICONS: Record<string, string> = {"食費":"🍱","交通":"🚃","娯楽":"🎮","衣服":"👕","美容":"💄","医療":"🏥","交際":"🍻","教育":"📚","その他":"📦"};

// 固定費カテゴリの絵文字
export const FIXED_EXPENSE_CATEGORY_ICONS: Record<string, string> = {"家賃":"🏠","通信":"📱","保険":"🛡️","サブスク":"🔄","光熱":"💡","その他":"📦"};

// 収入カテゴリの絵文字
export const INCOME_CATEGORY_ICONS: Record<string, string> = {"給与":"💼","副業":"💻","賞与":"🎉","投資":"📈","その他":"💰"};
```

**移行用エイリアス（リネーム期間中の安全網）:** 一旦は古い名前の export も残さない。一度に置換し切る方が漏れに気付きやすいため。

- [ ] **Step 2: 利用側を置換**

| 旧 | 新 |
|---|---|
| `yen` | `formatYen` |
| `parseAmount` | `parseYenAmount` |
| `MLS` | `MONTH_LABELS` |
| `ECATS` | `EXPENSE_CATEGORIES` |
| `FCATS` | `FIXED_EXPENSE_CATEGORIES` |
| `ICATS` | `INCOME_CATEGORIES` |
| `EICO` | `EXPENSE_CATEGORY_ICONS` |
| `FICO` | `FIXED_EXPENSE_CATEGORY_ICONS` |
| `IICO` | `INCOME_CATEGORY_ICONS` |

各ファイルで import 文をまず書き換え、TS エラーで参照箇所を順に直す。

- [ ] **Step 3: format.test.ts を新 API に追従**

`src/test/utils/format.test.ts` の関数名・定数名も新名称に置換。

- [ ] **Step 4: テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
Expected: 全 pass・エラー 0。

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add -u src && git commit -m "refactor(format): rename format helpers and category constants"
```

---

### Task 1.4: loanCalc.ts の識別子リネーム

**Files:**
- Modify: `src/utils/loanCalc.ts`
- Modify: 利用側（`src/components/LoanSection.tsx`, `src/App.tsx`, `src/test/utils/loanCalc.test.ts`）

- [ ] **Step 1: loanCalc.ts を書き換え**

```ts
// ────────── ローン計算ユーティリティ ──────────

// 月利息を計算（残高 × 年利 ÷ 12）
export function calculateMonthlyInterest(remaining: number, annualRate: number): number {
  return Math.floor(remaining * (annualRate / 100) / 12);
}

// 総支払利息（雑な見積もり）= 月利息 × 月数
export function calculateTotalInterest(remaining: number, annualRate: number, months: number): number {
  return calculateMonthlyInterest(remaining, annualRate) * months;
}

// 完済予定日（今月から months ヶ月後）
export function calculateCompletionDate(months: number): string {
  const date = new Date();
  date.setMonth(date.getMonth() + months);
  return `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, "0")}`;
}

// 利率テーブル等（既存の定義をそのままコピー）
export const RATE_TABLES = { /* 既存内容を維持。Bash で sed --range して該当行をそのまま残す */ };
export const BRANDS_CF = [/* 既存 */];
export const BRANDS_BL = [/* 既存 */];
export const FREE = "free";

export function findRate(brand: string, amount: number): number {
  // 既存の実装をそのまま維持
  // 実装中身は既存ファイル lines 77-83 をコピーすること
}
```

**実装手順:**
1. 既存 `src/utils/loanCalc.ts` を Read で開き、`mInt/tInt/cDate` 以外の `RATE_TABLES/BRANDS_CF/BRANDS_BL/FREE/findRate` の中身をそのまま保持
2. 関数名のみ Edit で置換: `mInt` → `calculateMonthlyInterest`, `tInt` → `calculateTotalInterest`, `cDate` → `calculateCompletionDate`

- [ ] **Step 2: 利用側の置換**

```bash
cd /home/kenta_kamijyo/finance_web && git grep -lE '\b(mInt|tInt|cDate)\b' src
```

各ファイルで Edit + replace_all を使い `mInt` → `calculateMonthlyInterest` 等に。

- [ ] **Step 3: loanCalc.test.ts の追従**

`src/test/utils/loanCalc.test.ts` の関数呼び出しも新名称に置換。

- [ ] **Step 4: テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
Expected: 全 pass・エラー 0。

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add -u src && git commit -m "refactor(loan): rename loan calc helpers to descriptive names"
```

---

### Task 1.5: ui.tsx の識別子リネーム

**Files:**
- Modify: `src/components/ui.tsx`
- Modify: 利用側（`src/App.tsx`, `src/components/*.tsx`, `src/test/components/*.tsx`）

- [ ] **Step 1: ui.tsx の export 名を変更**

| 旧 | 新 | 注意 |
|---|---|---|
| `PwInput` | `PasswordInput` | |
| `Inp` | `Input` | |
| `Sel` | `Select` | |
| `Stat` | `StatLabel` | |
| `Bar` | `ProgressBar` | recharts の `Bar` と衝突回避 |
| `Toast` | `Toast` | 変更なし |
| `Dlg` | `ConfirmDialog` | |

`src/components/ui.tsx` の `export function PwInput` → `export function PasswordInput` 等を Edit で書き換える。Props 型名も追従:
- `PwInputProps` → `PasswordInputProps`
- `InpProps` → `InputProps`
- `SelProps` → `SelectProps`
- `StatProps` → `StatLabelProps`
- `BarProps` → `ProgressBarProps`
- `DlgData` → `ConfirmDialogData`

- [ ] **Step 2: 利用側の置換**

```bash
cd /home/kenta_kamijyo/finance_web && git grep -lE '\b(PwInput|Inp|Sel|Stat|Bar|Dlg|InpProps|SelProps|StatProps|BarProps|DlgData|PwInputProps)\b' src
```

`Bar` は recharts の import と衝突しないよう **import 元** を必ず確認してから置換すること（recharts 由来は触らない）。

App.tsx の `<Stat label=` → `<StatLabel label=`、`<Bar` (ui 由来) → `<ProgressBar` 等。

- [ ] **Step 3: テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
Expected: 全 pass・エラー 0。

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add -u src && git commit -m "refactor(ui): rename UI primitives to descriptive names"
```

---

### Task 1.6: App.tsx の state 変数リネーム

**Files:**
- Modify: `src/App.tsx`

- [ ] **Step 1: 単純な state 変数を置換**

`src/App.tsx` で以下を **import がない単独 word 境界** で置換。Edit に `replace_all: true` を使うが、必ず変数宣言行から始めて一気に置き換える（部分置換だと TS エラーが残り続けて発見しにくい）。

| 旧 | 新 |
|---|---|
| `tx` (state) | `transactions` |
| `setTx` | `setTransactions` |
| `fx` (state) | `fixedExpenses` |
| `setFx` | `setFixedExpenses` |
| `lo` (state) | `loans` |
| `setLo` | `setLoans` |
| `cf` (state) | `cashFlow` |
| `setCf` | `setCashFlow` |
| `bl` (state) | `balance` |
| `setBl` | `setBalance` |
| `inc` (state) | `incomes` |
| `setInc` | `setIncomes` |
| `sm` | `selectedMonth` |
| `setSm` | `setSelectedMonth` |
| `sy` | `selectedYear` |
| `setSy` | `setSelectedYear` |
| `ms` | `monthString` |
| `mTx` | `monthlyTransactions` |
| `mInc` | `monthlyIncomes` |
| `tVar` | `totalVariableExpense` |
| `tFx` | `totalFixedExpense` |
| `tRep` | `totalLoanRepayment` |
| `tInc` | `totalIncome` |
| `tBur` | `totalBurden` |
| `MN` (component) | `MonthNav` |
| `ST` (component) | `StatBlock` |

**手順 (1 変数ずつ慎重に):**
1. Edit (`replace_all: true`) で `const [tx,` → `const [transactions,`
2. Edit (`replace_all: true`) で `setTx(` → `setTransactions(`
3. tsc 通過まで使用箇所を順次直す
4. 次の変数へ

- [ ] **Step 2: テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
Expected: 全 pass・エラー 0。

- [ ] **Step 3: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add -u src && git commit -m "refactor(App): rename state variables to descriptive names"
```

---

### Task 1.7: App.tsx の口座 a1〜a9 → account_0..account_8

**Files:**
- Modify: `src/App.tsx`

- [ ] **Step 1: account ごとの ready フラグと state を 1:1 で置換**

`a1` → `account_0`, `a2` → `account_1`, ..., `a9` → `account_8` の対応。**1-indexed → 0-indexed** に変更する点に注意（JS 配列に合わせる）。

App.tsx に `const [a1, setA1, a1Ready] = usePersist(...)` のようなパターンが 9 個並んでいるはず。各ペアを以下のように置換:

```ts
const [account_0, setAccount_0, account_0Ready] = usePersist<Account>("kk_account_0", { id: "account_0", name: "メイン口座", balance: 0 });
const [account_1, setAccount_1, account_1Ready] = usePersist<Account>("kk_account_1", { id: "account_1", name: "貯金", balance: 0 });
// ...
const [account_8, setAccount_8, account_8Ready] = usePersist<Account>("kk_account_8", { id: "account_8", name: "予備 8", balance: 0 });
```

**重要:** localStorage キーも `kk_a1` → `kk_account_0` に変える場合は **既存データを失う**。既存ユーザーのデータを守るため、**キーは旧名称 `kk_a1` のまま維持** する（TS 内の変数名だけリネーム）。

```ts
// JS 変数名は account_0 だが localStorage キーは "kk_a1" のまま
const [account_0, setAccount_0, account_0Ready] = usePersist<Account>("kk_a1", { id: "account_0", name: "...", balance: 0 });
```

- [ ] **Step 2: 利用側 (forms/handlers) も全て新名称に**

`a1.balance` → `account_0.balance`、`setA1(...)` → `setAccount_0(...)`。

- [ ] **Step 3: テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
Expected: 全 pass・エラー 0。

- [ ] **Step 4: ブラウザで動作確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm run dev
```
ブラウザで開き、口座 1〜9 の残高が **以前と同じ値** で表示されることを目視確認。問題なければ Ctrl+C で停止。

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add -u src && git commit -m "refactor(App): rename account state variables a1-a9 to account_0..account_8 (localStorage keys unchanged)"
```

---

### Task 1.8: crypto.ts の関数に型注釈

**Files:**
- Modify: `src/utils/crypto.ts`
- Test: 既存 import 側の TS チェックで検証

- [ ] **Step 1: 各関数のシグネチャを明示**

```ts
// 旧形式の簡易ハッシュ（後方互換のため残す）
export function simpleHash(input: string): string {
  // 既存実装をそのまま
}

// 旧形式判定（8 桁 hex かどうか）
export function isLegacyHash(hash: string): boolean {
  return /^[0-9a-f]{8}$/.test(hash);
}

// PBKDF2 で新形式ハッシュを作る
export async function makeNewHash(password: string): Promise<string> {
  // 既存実装
}

// 新形式ハッシュを検証
export async function verifyNewHash(password: string, savedHash: string): Promise<boolean> {
  // 既存実装
}

// AES-GCM 用の暗号化鍵をパスワードから派生
export async function deriveEncryptionKey(password: string, salt: Uint8Array): Promise<CryptoKey> {
  // 既存実装
}

// 暗号化用ソルトを localStorage から取得 or 新規作成
export function getOrCreateEncSalt(): Uint8Array {
  // 既存実装
}
```

**手順:** 既存ファイルを Read し、各 `export function`/`export async function` 行を Edit で型付き宣言に書き換えるだけ。中身（関数 body）は触らない。

- [ ] **Step 2: 型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npx tsc --noEmit
```
Expected: エラー 0。**特に注意:** 既存 caller (`PasswordGate.tsx`) で型不整合が出ないか確認。

- [ ] **Step 3: テスト**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run
```
Expected: 全 pass。

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add -u src && git commit -m "refactor(crypto): add explicit type annotations to crypto functions"
```

---

### Task 1.9: PasswordGate.tsx の useState 型注釈

**Files:**
- Modify: `src/components/PasswordGate.tsx`

- [ ] **Step 1: 各 useState に明示的なジェネリック**

PasswordGate.tsx を Edit で以下のように修正:

```ts
const [ok, setOk] = useState<boolean>(() => sessionStorage.getItem("ff_auth") === "1");
const [savedHash, setSavedHash] = useState<string>(() => { try { return localStorage.getItem("kk_pw_hash") || ""; } catch(_){ return ""; } });
const [pw, setPw] = useState<string>("");
const [pw2, setPw2] = useState<string>("");
const [err, setErr] = useState<string>("");
const [showReset, setShowReset] = useState<boolean>(false);
const [busy, setBusy] = useState<boolean>(false);
const [cryptoKey, setCryptoKey] = useState<CryptoKey | null>(null);  // ← ここが最重要
const [failCount, setFailCount] = useState<number>(() => Number(sessionStorage.getItem("ff_fail") || "0"));
const [lockUntil, setLockUntil] = useState<number>(() => Number(sessionStorage.getItem("ff_lock") || "0"));
```

- [ ] **Step 2: showErr 関数も型付け**

```ts
function showErr(msg: string): void { setErr(msg); setTimeout(()=>setErr(""),2000); }
```

- [ ] **Step 3: 型チェック＋テスト**

```bash
cd /home/kenta_kamijyo/finance_web && npx tsc --noEmit && npm test -- --run
```
Expected: 全 pass・エラー 0。

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add -u src && git commit -m "refactor(PasswordGate): add explicit useState type annotations"
```

---

### Task 1.10: BudgetSection の actual/draft 型付け

**Files:**
- Read: `src/components/BudgetSection.tsx`
- Modify: `src/components/BudgetSection.tsx`

- [ ] **Step 1: 型注釈を追加**

BudgetSection 内の `actual` (集計済み実績値) と `draft` (フォーム編集中の値) に明示的型:

```ts
const actual: Record<string, number> = useMemo(() => {
  // 既存集計ロジック
}, [/* 既存依存 */]);

const [draft, setDraft] = useState<Record<string, string>>({});
```

**`actual` は集計結果 (数値合計)** → `Record<string, number>`
**`draft` はフォーム入力中の文字列** → `Record<string, string>`

- [ ] **Step 2: 型チェック＋テスト**

```bash
cd /home/kenta_kamijyo/finance_web && npx tsc --noEmit && npm test -- --run
```
Expected: 全 pass・エラー 0。

- [ ] **Step 3: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add -u src && git commit -m "refactor(BudgetSection): type actual and draft state"
```

---

### Task 1.11: amount: number | string → number

**Files:**
- Modify: `src/types.ts`
- Modify: `src/App.tsx` (form handlers)
- Modify: `src/components/LoanSection.tsx`, `src/components/TxRow.tsx`, `src/components/FxRow.tsx`, `src/components/LoanCard.tsx`
- Modify: `src/hooks/usePersist.ts` (マイグレーション用 helper を追加)
- Test: `src/test/utils/dataMigration.test.ts` (新規)

- [ ] **Step 1: マイグレーション helper のテストを書いて失敗させる**

`src/utils/dataMigration.ts` 新規作成予定。先にテストを書く:

`src/test/utils/dataMigration.test.ts`:
```ts
import { describe, it, expect } from "vitest";
import { coerceAmountToNumber, migrateTransactions } from "../../utils/dataMigration";

describe("coerceAmountToNumber", () => {
  it("数値はそのまま返す", () => {
    expect(coerceAmountToNumber(1000)).toBe(1000);
  });
  it("カンマ付き文字列を数値化する", () => {
    expect(coerceAmountToNumber("1,234")).toBe(1234);
  });
  it("空文字は 0 にする", () => {
    expect(coerceAmountToNumber("")).toBe(0);
  });
  it("undefined は 0 にする", () => {
    expect(coerceAmountToNumber(undefined)).toBe(0);
  });
});

describe("migrateTransactions", () => {
  it("amount が文字列の取引を数値化する", () => {
    const input = [{ id: "1", date: "2026-05-01", category: "食費", amount: "1,500", memo: "" }];
    const result = migrateTransactions(input as any);
    expect(result[0].amount).toBe(1500);
  });
  it("note フィールドを memo にリネームする", () => {
    const input = [{ id: "1", date: "2026-05-01", category: "食費", amount: 100, note: "ランチ" }];
    const result = migrateTransactions(input as any);
    expect(result[0].memo).toBe("ランチ");
    expect((result[0] as any).note).toBeUndefined();
  });
});
```

- [ ] **Step 2: テストを実行して失敗を確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run src/test/utils/dataMigration.test.ts
```
Expected: FAIL with "Cannot find module" (まだ実装していない)。

- [ ] **Step 3: dataMigration.ts を実装**

`src/utils/dataMigration.ts`:
```ts
// ────────── 既存データのマイグレーション ──────────
// 古い形式 (amount: string, note フィールド) を新形式 (amount: number, memo) に変換

import { Tx, Income, FixedExpense, Loan } from "../types";

// 文字列または数値の amount を必ず数値にする
export function coerceAmountToNumber(value: unknown): number {
  if (typeof value === "number") return value;
  if (typeof value === "string") {
    const cleaned = value.replace(/[^\d.-]/g, "");
    return cleaned === "" ? 0 : Number(cleaned);
  }
  return 0;
}

// 取引一覧をマイグレート (amount を数値化、note → memo)
export function migrateTransactions(items: any[]): Tx[] {
  if (!Array.isArray(items)) return [];
  return items.map(item => {
    const memo = item.memo ?? item.note ?? "";
    const { note, ...rest } = item;
    return {
      ...rest,
      amount: coerceAmountToNumber(item.amount),
      memo,
    };
  });
}

// 収入一覧をマイグレート
export function migrateIncomes(items: any[]): Income[] {
  if (!Array.isArray(items)) return [];
  return items.map(item => ({ ...item, amount: coerceAmountToNumber(item.amount) }));
}

// 固定費一覧をマイグレート
export function migrateFixedExpenses(items: any[]): FixedExpense[] {
  if (!Array.isArray(items)) return [];
  return items.map(item => ({ ...item, amount: coerceAmountToNumber(item.amount) }));
}

// ローン一覧をマイグレート（rate/remaining/monthly/principal も数値化）
export function migrateLoans(items: any[]): Loan[] {
  if (!Array.isArray(items)) return [];
  return items.map(item => ({
    ...item,
    rate: coerceAmountToNumber(item.rate),
    remaining: coerceAmountToNumber(item.remaining),
    monthly: coerceAmountToNumber(item.monthly),
    principal: coerceAmountToNumber(item.principal),
  }));
}
```

- [ ] **Step 4: テスト通過を確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run src/test/utils/dataMigration.test.ts
```
Expected: PASS。

- [ ] **Step 5: types.ts の amount を number に**

`src/types.ts` を以下に書き換え:
```ts
export interface Tx {
  id: string;
  date: string;
  category: string;
  amount: number;
  memo: string;
  accountId?: string; // Phase 3 で使うので予約 (任意項目)
}

export interface FixedExpense {
  id: string;
  category: string;
  amount: number;
  payDay: number;
  active: boolean;
}

export interface Loan {
  id: string;
  name: string;
  brand?: string;
  principal: number;
  remaining: number;
  rate: number;
  monthly: number;
  startDate?: string;
}

export interface Income {
  id: string;
  date: string;
  category: string;
  amount: number;
  memo: string;
  accountId?: string;
}

export interface Account {
  id: string;
  name: string;
  balance: number;
}

export type Budget = Record<string, number>;

export interface ToastData {
  msg: string;
  type?: "success" | "error" | "info";
}

export interface DlgData {
  title: string;
  msg?: string;
  onOk: () => void;
}
```

- [ ] **Step 6: App.tsx の usePersist でマイグレーションを噛ます**

App.tsx で `usePersist` を呼ぶ箇所のうち取引・収入・固定費・ローンに、初回読み込み後にマイグレーションを 1 回だけかける `useEffect` を追加（または usePersist にマイグレーション関数を渡せるように拡張）。

最小変更: App.tsx の AppInner 関数の冒頭付近に追加:
```ts
import { migrateTransactions, migrateIncomes, migrateFixedExpenses, migrateLoans } from "./utils/dataMigration";

// ────── マイグレーション（初回 1 回だけ） ──────
const migratedRef = useRef(false);
useEffect(() => {
  if (migratedRef.current) return;
  if (!txReady || !incReady || !fxReady || !loReady) return;
  migratedRef.current = true;
  setTransactions(prev => migrateTransactions(prev as any));
  setIncomes(prev => migrateIncomes(prev as any));
  setFixedExpenses(prev => migrateFixedExpenses(prev as any));
  setLoans(prev => migrateLoans(prev as any));
}, [txReady, incReady, fxReady, loReady]);
```

- [ ] **Step 7: フォームハンドラを number ベースに**

addTx/addInc/addFx/loan add などで `amount: parseYenAmount(form.amount)` のように数値化してから state を更新する。例:

```ts
function addTx() {
  if (!txF.category || !txF.amount) return;
  setTransactions(prev => [
    { id: crypto.randomUUID(), date: monthString + "-01", category: txF.category, amount: parseYenAmount(txF.amount), memo: txF.memo || "" },
    ...prev,
  ]);
  setTxF({ category: "", amount: "", memo: "" });
}
```

- [ ] **Step 8: TxRow/FxRow/LoanCard の amount 表示も number 前提に**

各コンポーネントで `Number(amount)` のような防御コードを `amount` 直接参照に変える。`yen(amount)` → `formatYen(amount)`。

- [ ] **Step 9: 全テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
Expected: 全 pass・エラー 0。

- [ ] **Step 10: ブラウザ動作確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm run dev
```
- 既存の取引・収入・固定費・ローンが**数値として正しく表示**されることを確認
- 新規取引を追加して問題なく保存・表示できることを確認
- メモが「note」だった旧データが「memo」として表示されることを確認

- [ ] **Step 11: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/types.ts src/utils/dataMigration.ts src/test/utils/dataMigration.test.ts && git add -u src && git commit -m "refactor(types): tighten amount to number with localStorage migration"
```

---

### Task 1.12: memo vs note フィールド統一

**Files:**
- Modify: `src/App.tsx` (note → memo)
- Modify: `src/components/TxRow.tsx`

- [ ] **Step 1: App.tsx で note を memo に統一**

`src/App.tsx` 内の取引フォーム関連 state (`txF`) と addTx 関数で `note` フィールドを使っている場合、全て `memo` に置換:

| 旧 | 新 |
|---|---|
| `txF.note` | `txF.memo` |
| `note: ""` (txF 初期値) | `memo: ""` |
| `setTxF({...txF, note: e.target.value})` | `setTxF({...txF, memo: e.target.value})` |
| `note: txF.note` (addTx 内) | `memo: txF.memo` |

**マイグレーション層 (Task 1.11) が既存データの `note` を `memo` に変換するので**、ここでは新規入力側だけ揃える。

- [ ] **Step 2: TxRow.tsx の参照確認**

`src/components/TxRow.tsx` で `tx.note` を参照している箇所があれば `tx.memo` に置換。

- [ ] **Step 3: テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
Expected: 全 pass・エラー 0。

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add -u src && git commit -m "refactor: unify transaction memo field (was inconsistently note/memo)"
```

---

### Task 1.13: 空 catch を console.warn に置換

**Files:**
- Modify: `src/hooks/usePersist.ts` (lines 33, 42, 49, 56, 71)
- Modify: `src/utils/crypto.ts` (lines 70, 91, 94)
- Modify: `src/components/PasswordGate.tsx` (lines 21, 62, 117)
- Modify: `src/components/LoanSection.tsx` (空 catch があれば)
- Modify: `src/App.tsx` (もし空 catch が残っていれば)

- [ ] **Step 1: usePersist.ts の各 catch にログ出力を追加**

`src/hooks/usePersist.ts` で `catch(_){}` を以下のように修正:

```ts
// 例: localStorage read エラー
try {
  const raw = localStorage.getItem(key);
  if (raw) { /* ... */ }
} catch (error) {
  console.warn("[usePersist] localStorage read failed", { key, error });
}

// 例: 暗号化エラー
try {
  // 暗号化処理
} catch (error) {
  console.warn("[usePersist] encrypt failed", { key, error });
}
```

5 箇所全てに `key` と `error` を含めた `console.warn` を入れる。**動作変更はしない**（再 throw もしない）。

- [ ] **Step 2: crypto.ts の各 catch も同様に**

```ts
} catch (error) {
  console.warn("[crypto] simpleHash failed", { error });
}
```

- [ ] **Step 3: PasswordGate.tsx の各 catch も同様に**

```ts
// line 21: localStorage read in init state
useState(() => {
  try { return localStorage.getItem("kk_pw_hash") || ""; }
  catch (error) { console.warn("[PasswordGate] init read failed", { error }); return ""; }
});

// line 62: hash upgrade
try { /* ... */ }
catch (error) { console.warn("[PasswordGate] hash upgrade failed", { error }); }

// line 117: localStorage write
try { localStorage.setItem("kk_pw_hash", h); }
catch (error) { console.warn("[PasswordGate] save hash failed", { error }); }
```

ユーザー影響がある場合は Toast を出すが、これらはバックグラウンドのキャッシュ操作なので Toast は不要。

- [ ] **Step 4: 残りの空 catch を grep で確認**

```bash
cd /home/kenta_kamijyo/finance_web && git grep -nE 'catch\s*\([_a-zA-Z]+\)\s*\{\s*\}' src
```
Expected: ヒット 0 件。残っていれば該当箇所にも `console.warn` を追加。

- [ ] **Step 5: テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
Expected: 全 pass・エラー 0。

- [ ] **Step 6: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add -u src && git commit -m "refactor: replace empty catch blocks with console.warn for visibility"
```

---

### Task 1.14: Phase 1 完了確認

- [ ] **Step 1: 旧名称が残っていないか最終チェック**

```bash
cd /home/kenta_kamijyo/finance_web && git grep -nE '\b(BG|T2|T3|BD|AC|POS|NEG|CARD|IS|BS|OS|MLS|ECATS|FCATS|ICATS|EICO|FICO|IICO|mInt|tInt|cDate|Inp|Sel|PwInput|Dlg|yen)\b' src
```
Expected: ヒット 0 件（recharts の `Bar` import が残るのは正しい）。

- [ ] **Step 2: 空 catch が残っていないか確認**

```bash
cd /home/kenta_kamijyo/finance_web && git grep -nE 'catch\s*\([_a-zA-Z]+\)\s*\{\s*\}' src
```
Expected: ヒット 0 件。

- [ ] **Step 3: amount の string 残骸が残っていないか確認**

```bash
cd /home/kenta_kamijyo/finance_web && git grep -nE 'amount:\s*number\s*\|\s*string' src
```
Expected: ヒット 0 件。

- [ ] **Step 4: 全テスト＋型チェック＋本番ビルド**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run build
```
Expected: 全 pass・エラー 0・build 成功。

- [ ] **Step 5: ブラウザで完全動作確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm run dev
```
- パスワードログイン → 既存データが見える
- 取引・収入・固定費・ローン・口座が**以前と同じ値**で表示される
- 新規追加が動く
- 削除が動く
- 月選択が動く
- データエクスポートが動く

問題なければ Phase 1 完了。

---

## Phase 2: コンポーネント分割＋メモ化＋カスタムフック

**目的:** 430 行の App.tsx を 100 行以下に分割。再レンダリングコストを useMemo で削減。usePersist の mem バグを修正。

**Phase 2 完了条件:**
- App.tsx が 100 行以下
- 各 view (Dashboard/Income/FixedExpense/Expense/Loan) が独立ファイル
- 派生値が useMemo でメモ化されている
- usePersist の mem バグテストが pass

---

### Task 2.1: usePersist の mem バグ修正（TDD）

**Files:**
- Modify: `src/hooks/usePersist.ts`
- Test: `src/test/hooks/usePersist.test.ts` (新規)

- [ ] **Step 1: 失敗するテストを書く**

`src/test/hooks/usePersist.test.ts`:
```ts
import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePersist } from "../../hooks/usePersist";

describe("usePersist mem isolation", () => {
  it("異なるキーのフックが互いに干渉しない", async () => {
    // フック A をマウント
    const { result: a } = renderHook(() => usePersist<string>("test_a", "initialA"));
    // フック B をマウント
    const { result: b } = renderHook(() => usePersist<string>("test_b", "initialB"));

    // A を更新
    act(() => {
      a.current[1]("updatedA");
    });

    // B の値が A に汚染されていないことを確認
    expect(a.current[0]).toBe("updatedA");
    expect(b.current[0]).toBe("initialB");
  });

  it("同じキーで再マウントしても前回の mem は残らない", async () => {
    const { unmount } = renderHook(() => usePersist<string>("test_c", "first"));
    unmount();

    // 別の初期値で再マウント
    const { result } = renderHook(() => usePersist<string>("test_c", "second"));

    // localStorage に保存されていなければ second が初期値として使われる
    // (mem ではなく localStorage または初期値が真実)
    expect(["first", "second"]).toContain(result.current[0]);
  });
});
```

- [ ] **Step 2: テスト実行して失敗確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run src/test/hooks/usePersist.test.ts
```
Expected: いずれかのテストが FAIL（モジュールレベル `mem` が他キーと共有されているため）。

- [ ] **Step 3: usePersist を useRef ベースに修正**

`src/hooks/usePersist.ts` を以下のように変更:

```ts
// ────────── localStorage 永続化フック ──────────
// AES-GCM 暗号化付きで state を localStorage と同期させる
import { useEffect, useRef, useState, useContext } from "react";
import CryptoKeyContext from "../contexts/CryptoKeyContext";
import { /* 既存の暗号 helper */ } from "../utils/crypto";

export function usePersist<T>(key: string, init: T): [T, (updater: T | ((prev: T) => T)) => void, boolean] {
  const cryptoKey = useContext(CryptoKeyContext);
  const [value, setValue] = useState<T>(init);
  const [ready, setReady] = useState<boolean>(false);

  // mem は **このフック呼び出しごと** に独立した参照を持つ
  const memRef = useRef<T | null>(null);

  // 読み込み
  useEffect(() => {
    if (!cryptoKey) return;
    let cancelled = false;
    (async () => {
      try {
        const raw = localStorage.getItem(key);
        if (raw) {
          // 復号
          const decrypted = await decrypt(raw, cryptoKey);
          if (!cancelled) {
            setValue(decrypted as T);
            memRef.current = decrypted as T;
          }
        }
      } catch (error) {
        console.warn("[usePersist] read failed", { key, error });
      } finally {
        if (!cancelled) setReady(true);
      }
    })();
    return () => { cancelled = true; };
  }, [cryptoKey, key]);

  // 書き込み
  const updateValue = (updater: T | ((prev: T) => T)) => {
    setValue(prev => {
      const next = typeof updater === "function" ? (updater as (p: T) => T)(prev) : updater;
      memRef.current = next;
      if (cryptoKey) {
        encrypt(next, cryptoKey)
          .then(ciphertext => {
            try { localStorage.setItem(key, ciphertext); }
            catch (error) { console.warn("[usePersist] write failed", { key, error }); }
          })
          .catch(error => { console.warn("[usePersist] encrypt failed", { key, error }); });
      }
      return next;
    });
  };

  return [value, updateValue, ready];
}
```

**重要:** 既存の暗号化ロジック (`encrypt`/`decrypt` の中身) はそのまま流用する。**変えるのは `let mem` (モジュールレベル) → `useRef` (フックインスタンスごと) の部分だけ**。

- [ ] **Step 4: テスト通過を確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run src/test/hooks/usePersist.test.ts
```
Expected: 全 pass。

- [ ] **Step 5: 全テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
Expected: 全 pass・エラー 0。

- [ ] **Step 6: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/test/hooks/usePersist.test.ts && git add -u src && git commit -m "fix(usePersist): isolate mem per hook instance via useRef"
```

---

### Task 2.2: 派生値の useMemo メモ化

**Files:**
- Modify: `src/App.tsx`

- [ ] **Step 1: 既存の useMemo されていない計算を特定**

App.tsx の以下の派生値が `useMemo` でラップされていないはず:
- `totalLoanRepayment`
- `totalIncome`
- `totalBurden`
- `net` (収支)

- [ ] **Step 2: useMemo でラップ**

```ts
const totalLoanRepayment = useMemo(
  () => loans.reduce((sum, l) => sum + (l.monthly || 0), 0),
  [loans]
);

const totalIncome = useMemo(
  () => monthlyIncomes.reduce((sum, i) => sum + i.amount, 0),
  [monthlyIncomes]
);

const totalBurden = useMemo(
  () => totalVariableExpense + totalFixedExpense + totalLoanRepayment,
  [totalVariableExpense, totalFixedExpense, totalLoanRepayment]
);

const net = useMemo(
  () => totalIncome - totalBurden,
  [totalIncome, totalBurden]
);
```

- [ ] **Step 3: テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
Expected: 全 pass・エラー 0。

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add -u src && git commit -m "perf(App): memoize totalLoanRepayment/totalIncome/totalBurden/net"
```

---

### Task 2.3: MonthNav を別ファイルに切り出す

**Files:**
- Create: `src/components/MonthNav.tsx`
- Modify: `src/App.tsx`

- [ ] **Step 1: MonthNav.tsx を作成**

```tsx
// ────────── 月選択ナビゲーション ──────────
// 「← 2026年5月 →」のような月切り替えバー
import { MONTH_LABELS } from "../utils/format";
import { COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BORDER } from "../utils/styles";

interface MonthNavProps {
  selectedYear: number;
  selectedMonth: number;
  onChange: (year: number, month: number) => void;
}

export default function MonthNav({ selectedYear, selectedMonth, onChange }: MonthNavProps) {
  // 前の月へ
  function prev() {
    if (selectedMonth === 0) onChange(selectedYear - 1, 11);
    else onChange(selectedYear, selectedMonth - 1);
  }
  // 次の月へ
  function next() {
    if (selectedMonth === 11) onChange(selectedYear + 1, 0);
    else onChange(selectedYear, selectedMonth + 1);
  }
  return (
    <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"12px 16px",border:`1px solid ${COLOR_BORDER}`,borderRadius:14,marginBottom:14}}>
      <button onClick={prev} aria-label="前の月" style={{background:"transparent",border:"none",color:COLOR_TEXT_SECONDARY,cursor:"pointer",fontSize:18,padding:4}}>←</button>
      <div style={{fontSize:15,fontWeight:600,color:COLOR_TEXT_PRIMARY}}>{selectedYear}年 {MONTH_LABELS[selectedMonth]}</div>
      <button onClick={next} aria-label="次の月" style={{background:"transparent",border:"none",color:COLOR_TEXT_SECONDARY,cursor:"pointer",fontSize:18,padding:4}}>→</button>
    </div>
  );
}
```

**実装手順:**
1. App.tsx の `function MN(...)` または `const MN = ...` の中身を Read で確認
2. **既存の実装の見た目をそのまま保つ** ように MonthNav.tsx に移植（color/padding 値は既存値を維持）
3. props 経由で受け取るように変える (props を介さず親 state を直接参照していた箇所を引数化)

- [ ] **Step 2: App.tsx で MonthNav を import して使用**

```tsx
import MonthNav from "./components/MonthNav";

// 使用箇所:
<MonthNav
  selectedYear={selectedYear}
  selectedMonth={selectedMonth}
  onChange={(year, month) => { setSelectedYear(year); setSelectedMonth(month); }}
/>
```

- [ ] **Step 3: App.tsx 内の旧 MN 定義と参照を全削除**

- [ ] **Step 4: テスト＋型チェック＋ブラウザ確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
ブラウザでも月切替が動くことを確認:
```bash
cd /home/kenta_kamijyo/finance_web && npm run dev
```

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/components/MonthNav.tsx && git add -u src && git commit -m "refactor(App): extract MonthNav to its own component file"
```

---

### Task 2.4: StatBlock を別ファイルに切り出す

**Files:**
- Create: `src/components/StatBlock.tsx`
- Modify: `src/App.tsx`

- [ ] **Step 1: StatBlock.tsx を作成**

```tsx
// ────────── 集計ブロック ──────────
// 「収入 ¥12,345」のような数値カード
import { ReactNode } from "react";
import { COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BORDER, STYLE_CARD } from "../utils/styles";
import { formatYen } from "../utils/format";

interface StatBlockProps {
  label: string;
  amount: number;
  color?: string;
  icon?: ReactNode;
}

export default function StatBlock({ label, amount, color, icon }: StatBlockProps) {
  return (
    <div style={{...STYLE_CARD, flex:1, marginBottom:0}}>
      <div style={{fontSize:11,color:COLOR_TEXT_SECONDARY,marginBottom:6,display:"flex",alignItems:"center",gap:6}}>
        {icon}{label}
      </div>
      <div style={{fontSize:18,fontWeight:700,color:color || COLOR_TEXT_PRIMARY,fontFamily:"monospace"}}>
        {formatYen(amount)}
      </div>
    </div>
  );
}
```

**実装手順:** App.tsx の既存 ST コンポーネントの見た目を踏襲。props 名 (`label`, `amount`, `color`, `icon`) で受け取る。

- [ ] **Step 2: App.tsx で使用**

```tsx
import StatBlock from "./components/StatBlock";
// 既存 ST 呼び出し箇所を全て <StatBlock ... /> に置換
```

- [ ] **Step 3: App.tsx 内の旧 ST 定義を削除**

- [ ] **Step 4: テスト＋型チェック＋ブラウザ確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run dev
```

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/components/StatBlock.tsx && git add -u src && git commit -m "refactor(App): extract StatBlock to its own component file"
```

---

### Task 2.5: dataExport.ts ユーティリティ（TDD）

**Files:**
- Create: `src/utils/dataExport.ts`
- Test: `src/test/utils/dataExport.test.ts`

- [ ] **Step 1: 失敗するテストを書く**

`src/test/utils/dataExport.test.ts`:
```ts
import { describe, it, expect } from "vitest";
import { transactionsToCsv, exportAsJson } from "../../utils/dataExport";

describe("transactionsToCsv", () => {
  it("ヘッダー行を含む CSV を返す", () => {
    const csv = transactionsToCsv([]);
    expect(csv).toBe("date,category,amount,memo\n");
  });

  it("取引行を正しく出力する", () => {
    const csv = transactionsToCsv([
      { id: "1", date: "2026-05-01", category: "食費", amount: 1500, memo: "ランチ" }
    ]);
    expect(csv).toContain("2026-05-01,食費,1500,ランチ");
  });

  it("memo にカンマが含まれていたらクオートする", () => {
    const csv = transactionsToCsv([
      { id: "1", date: "2026-05-01", category: "食費", amount: 1500, memo: "a,b,c" }
    ]);
    expect(csv).toContain('"a,b,c"');
  });

  it("memo にダブルクオートが含まれていたらエスケープする", () => {
    const csv = transactionsToCsv([
      { id: "1", date: "2026-05-01", category: "食費", amount: 1500, memo: 'say "hi"' }
    ]);
    expect(csv).toContain('"say ""hi"""');
  });
});

describe("exportAsJson", () => {
  it("整形済み JSON 文字列を返す", () => {
    const json = exportAsJson({ foo: "bar" });
    expect(json).toBe('{\n  "foo": "bar"\n}');
  });
});
```

- [ ] **Step 2: テストを実行して失敗確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run src/test/utils/dataExport.test.ts
```
Expected: FAIL with "Cannot find module"。

- [ ] **Step 3: dataExport.ts を実装**

`src/utils/dataExport.ts`:
```ts
// ────────── データ出力ユーティリティ ──────────
// CSV/JSON エクスポートとファイルダウンロード
import { Tx } from "../types";

// CSV 用の 1 セルをクオートする (RFC 4180 準拠)
function csvCell(value: string | number): string {
  const str = String(value);
  const needsQuote = /[",\n]/.test(str);
  if (!needsQuote) return str;
  return '"' + str.replace(/"/g, '""') + '"';
}

// 取引一覧を CSV 文字列に変換
export function transactionsToCsv(transactions: Tx[]): string {
  const header = "date,category,amount,memo\n";
  const rows = transactions
    .map(tx => [tx.date, tx.category, tx.amount, tx.memo || ""].map(csvCell).join(","))
    .join("\n");
  return header + (rows ? rows + "\n" : "");
}

// オブジェクトを整形済み JSON 文字列に変換
export function exportAsJson(data: object): string {
  return JSON.stringify(data, null, 2);
}

// ブラウザでファイルとしてダウンロードさせる
export function downloadFile(filename: string, content: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
```

- [ ] **Step 4: テスト通過を確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run src/test/utils/dataExport.test.ts
```
Expected: 全 pass。

- [ ] **Step 5: App.tsx の exportCSV/exportIncCSV/exportBackup から該当処理を新ユーティリティに置換**

App.tsx の `exportCSV` 関数を以下のように書き換え:

```ts
import { transactionsToCsv, exportAsJson, downloadFile } from "./utils/dataExport";

function exportCSV() {
  const csv = transactionsToCsv(monthlyTransactions);
  downloadFile(`transactions-${monthString}.csv`, csv, "text/csv;charset=utf-8");
}

function exportBackup() {
  const data = { transactions, fixedExpenses, loans, incomes, /* 他必要なもの */ };
  const json = exportAsJson(data);
  downloadFile(`finance-backup-${new Date().toISOString().slice(0,10)}.json`, json, "application/json");
}
```

収入用 CSV (`exportIncCSV`) は別関数のままにするか、`transactionsToCsv` を流用するか選ぶ（共通化したいなら `incomesToCsv` を追加実装）。

- [ ] **Step 6: 全テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
Expected: 全 pass・エラー 0。

- [ ] **Step 7: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/utils/dataExport.ts src/test/utils/dataExport.test.ts && git add -u src && git commit -m "refactor(export): extract CSV/JSON export utilities with tests"
```

---

### Task 2.6: useMonthlyData カスタムフック

**Files:**
- Create: `src/hooks/useMonthlyData.ts`
- Modify: `src/App.tsx`

- [ ] **Step 1: useMonthlyData を実装**

```ts
// ────────── 月別データ集計フック ──────────
// 選択中の年月に該当する取引・収入と、各種合計値をまとめて返す
import { useMemo } from "react";
import { Tx, Income, FixedExpense, Loan } from "../types";

interface MonthlyDataArgs {
  transactions: Tx[];
  incomes: Income[];
  fixedExpenses: FixedExpense[];
  loans: Loan[];
  selectedYear: number;
  selectedMonth: number; // 0-11
}

export function useMonthlyData(args: MonthlyDataArgs) {
  const { transactions, incomes, fixedExpenses, loans, selectedYear, selectedMonth } = args;
  // "2026-05" 形式
  const monthString = useMemo(
    () => `${selectedYear}-${String(selectedMonth + 1).padStart(2, "0")}`,
    [selectedYear, selectedMonth]
  );
  const monthlyTransactions = useMemo(
    () => transactions.filter(tx => tx.date && tx.date.startsWith(monthString)),
    [transactions, monthString]
  );
  const monthlyIncomes = useMemo(
    () => incomes.filter(i => i.date && i.date.startsWith(monthString)),
    [incomes, monthString]
  );
  const totalVariableExpense = useMemo(
    () => monthlyTransactions.reduce((s, t) => s + t.amount, 0),
    [monthlyTransactions]
  );
  const totalFixedExpense = useMemo(
    () => fixedExpenses.filter(f => f.active).reduce((s, f) => s + f.amount, 0),
    [fixedExpenses]
  );
  const totalLoanRepayment = useMemo(
    () => loans.reduce((s, l) => s + (l.monthly || 0), 0),
    [loans]
  );
  const totalIncome = useMemo(
    () => monthlyIncomes.reduce((s, i) => s + i.amount, 0),
    [monthlyIncomes]
  );
  const totalBurden = useMemo(
    () => totalVariableExpense + totalFixedExpense + totalLoanRepayment,
    [totalVariableExpense, totalFixedExpense, totalLoanRepayment]
  );
  const net = useMemo(
    () => totalIncome - totalBurden,
    [totalIncome, totalBurden]
  );
  return {
    monthString,
    monthlyTransactions,
    monthlyIncomes,
    totalVariableExpense,
    totalFixedExpense,
    totalLoanRepayment,
    totalIncome,
    totalBurden,
    net,
  };
}
```

- [ ] **Step 2: App.tsx で useMonthlyData を呼び出す**

App.tsx の monthString/monthlyTransactions などの既存 useMemo を全削除し、以下に置換:

```tsx
import { useMonthlyData } from "./hooks/useMonthlyData";

const monthly = useMonthlyData({
  transactions, incomes, fixedExpenses, loans, selectedYear, selectedMonth
});
// 以後 monthly.monthString, monthly.totalIncome などで参照
```

利用側の参照箇所 (`monthString` → `monthly.monthString` 等) を全て修正。

- [ ] **Step 3: テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
Expected: 全 pass・エラー 0。

- [ ] **Step 4: ブラウザ確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm run dev
```
ダッシュボードの数値が以前と一致することを目視確認。

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/hooks/useMonthlyData.ts && git add -u src && git commit -m "refactor(App): extract monthly aggregation to useMonthlyData hook"
```

---

### Task 2.7: useAutoPayment カスタムフック

**Files:**
- Create: `src/hooks/useAutoPayment.ts`
- Modify: `src/App.tsx`

- [ ] **Step 1: useAutoPayment を実装**

App.tsx の自動支払い useEffect (lines 76-143 周辺) のロジックをそのまま移植:

```ts
// ────────── 毎月の自動支払い処理 ──────────
// 月初に固定費・ローン返済を自動で取引/CF に反映する
import { useEffect, useRef } from "react";
import { FixedExpense, Loan, Tx } from "../types";

interface UseAutoPaymentArgs {
  fixedExpenses: FixedExpense[];
  loans: Loan[];
  transactions: Tx[];
  setTransactions: (updater: Tx[] | ((p: Tx[]) => Tx[])) => void;
  // ... 既存の引数を維持
  ready: boolean; // 全ての usePersist が ready になった時点で起動
}

export function useAutoPayment(args: UseAutoPaymentArgs) {
  const lastAutoRunDate = useRef<string | null>(null);
  useEffect(() => {
    if (!args.ready) return;
    const today = new Date();
    const dateKey = today.toISOString().slice(0, 10);
    if (lastAutoRunDate.current === dateKey) return;
    lastAutoRunDate.current = dateKey;
    // ────── 既存の自動支払いロジックをここに移植 ──────
    // 既存 App.tsx lines 76-143 の処理本体をそのままコピー
  }, [args.ready, /* 既存の依存配列 */]);
}
```

**実装手順:**
1. 既存 App.tsx の useEffect 内ロジックを **そのまま** コピー
2. setTransactions/setCashFlow 等の依存を引数として受け取れるよう props 化
3. 動作変更は禁止（あくまで「移動」のみ）

- [ ] **Step 2: App.tsx で呼び出す**

```ts
import { useAutoPayment } from "./hooks/useAutoPayment";

useAutoPayment({
  fixedExpenses, loans, transactions, setTransactions,
  /* 既存の依存全部 */,
  ready: txReady && fxReady && loReady && /* etc */,
});
```

App.tsx 内の旧 useEffect は削除。

- [ ] **Step 3: テスト＋型チェック＋ブラウザ確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run dev
```
月またぎで自動取引が走るかは目視で確認しにくいので、`console.log` を一時的に入れて確認 → 完了後に削除（**コミット前に削除**）。

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/hooks/useAutoPayment.ts && git add -u src && git commit -m "refactor(App): extract auto-payment logic to useAutoPayment hook"
```

---

### Task 2.8: useDataExport カスタムフック

**Files:**
- Create: `src/hooks/useDataExport.ts`
- Modify: `src/App.tsx`

- [ ] **Step 1: useDataExport を実装**

```ts
// ────────── データ出力フック ──────────
// CSV/JSON エクスポートとバックアップインポートをまとめる
import { useCallback } from "react";
import { Tx, Income, FixedExpense, Loan, Account, Budget } from "../types";
import { transactionsToCsv, exportAsJson, downloadFile } from "../utils/dataExport";

interface BackupData {
  transactions: Tx[];
  fixedExpenses: FixedExpense[];
  loans: Loan[];
  incomes: Income[];
  accounts?: Account[];
  budget?: Budget;
  exportedAt: string;
}

interface UseDataExportArgs {
  transactions: Tx[];
  monthlyTransactions: Tx[];
  monthlyIncomes: Income[];
  fixedExpenses: FixedExpense[];
  loans: Loan[];
  incomes: Income[];
}

export function useDataExport(args: UseDataExportArgs) {
  const exportMonthlyCsv = useCallback((monthLabel: string) => {
    const csv = transactionsToCsv(args.monthlyTransactions);
    downloadFile(`transactions-${monthLabel}.csv`, csv, "text/csv;charset=utf-8");
  }, [args.monthlyTransactions]);

  const exportMonthlyIncomeCsv = useCallback((monthLabel: string) => {
    // incomesToCsv が無ければここで簡易実装
    const header = "date,category,amount,memo\n";
    const rows = args.monthlyIncomes
      .map(i => `${i.date},${i.category},${i.amount},${(i.memo || "").replace(/[",\n]/g, "_")}`)
      .join("\n");
    downloadFile(`incomes-${monthLabel}.csv`, header + rows + "\n", "text/csv;charset=utf-8");
  }, [args.monthlyIncomes]);

  const exportBackup = useCallback(() => {
    const backup: BackupData = {
      transactions: args.transactions,
      fixedExpenses: args.fixedExpenses,
      loans: args.loans,
      incomes: args.incomes,
      exportedAt: new Date().toISOString(),
    };
    downloadFile(
      `finance-backup-${new Date().toISOString().slice(0, 10)}.json`,
      exportAsJson(backup),
      "application/json"
    );
  }, [args]);

  return { exportMonthlyCsv, exportMonthlyIncomeCsv, exportBackup };
}
```

**注意:** インポート (`importBackup`) は state setter を多数受け取るためフック化が複雑。当面は App.tsx に残しておくか、別フックに分けてもよい。

- [ ] **Step 2: App.tsx で使用**

```ts
import { useDataExport } from "./hooks/useDataExport";

const dataExport = useDataExport({
  transactions, monthlyTransactions: monthly.monthlyTransactions,
  monthlyIncomes: monthly.monthlyIncomes, fixedExpenses, loans, incomes,
});

// 既存 exportCSV/exportBackup を dataExport.exportMonthlyCsv 等に置換
```

- [ ] **Step 3: テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
Expected: 全 pass・エラー 0。

- [ ] **Step 4: ブラウザでエクスポート動作確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm run dev
```
- 月次 CSV エクスポートが動く
- バックアップ JSON エクスポートが動く
- インポート（残した側）が動く

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/hooks/useDataExport.ts && git add -u src && git commit -m "refactor(App): extract data export to useDataExport hook"
```

---

### Task 2.9: DashboardView を切り出す

**Files:**
- Create: `src/views/DashboardView.tsx`
- Modify: `src/App.tsx`

- [ ] **Step 1: DashboardView.tsx を作成**

```tsx
// ────────── ダッシュボード画面 ──────────
// 月次サマリー・グラフ・収入支出の集計を表示する
import { Tx, Income, FixedExpense, Loan, Account } from "../types";
import StatBlock from "../components/StatBlock";
import { ProgressBar } from "../components/ui";
import { COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, STYLE_CARD } from "../utils/styles";
import { EXPENSE_CATEGORIES, EXPENSE_CATEGORY_ICONS } from "../utils/format";

interface DashboardViewProps {
  monthlyTransactions: Tx[];
  monthlyIncomes: Income[];
  totalVariableExpense: number;
  totalFixedExpense: number;
  totalLoanRepayment: number;
  totalIncome: number;
  totalBurden: number;
  net: number;
  // 必要な他の props
}

export default function DashboardView(props: DashboardViewProps) {
  // ────── App.tsx 既存の dash タブの中身をそのまま移植 ──────
  // <StatBlock label="収入" amount={props.totalIncome} color={COLOR_POSITIVE} />
  // <ProgressBar ... />
  // など
  return (
    <div>
      {/* 既存 dash タブの JSX を全部コピー */}
    </div>
  );
}
```

**実装手順:**
1. App.tsx の `tab === "dash"` の中身 (JSX) を Read で確認
2. それを DashboardView.tsx に **そのまま** コピー
3. 親 state を参照していた箇所を props 経由に変える

- [ ] **Step 2: App.tsx で DashboardView を使用**

```tsx
{tab === "dash" && (
  <DashboardView
    monthlyTransactions={monthly.monthlyTransactions}
    monthlyIncomes={monthly.monthlyIncomes}
    totalVariableExpense={monthly.totalVariableExpense}
    totalFixedExpense={monthly.totalFixedExpense}
    totalLoanRepayment={monthly.totalLoanRepayment}
    totalIncome={monthly.totalIncome}
    totalBurden={monthly.totalBurden}
    net={monthly.net}
  />
)}
```

旧 dash タブ JSX は App.tsx から削除。

- [ ] **Step 3: テスト＋型チェック＋ブラウザ確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run dev
```
ダッシュボードの**見た目と数値が以前と完全一致**することを確認。

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/views/DashboardView.tsx && git add -u src && git commit -m "refactor(App): extract dashboard tab to DashboardView"
```

---

### Task 2.10: IncomeView を切り出す

**Files:**
- Create: `src/views/IncomeView.tsx`
- Modify: `src/App.tsx`

- [ ] **Step 1: IncomeView.tsx を作成**

```tsx
// ────────── 収入入力・履歴画面 ──────────
import { Income } from "../types";
import { Input, Select } from "../components/ui";
import { INCOME_CATEGORIES, INCOME_CATEGORY_ICONS, parseYenAmount } from "../utils/format";

interface IncomeViewProps {
  incomes: Income[];
  monthlyIncomes: Income[];
  monthString: string;
  setIncomes: (updater: Income[] | ((p: Income[]) => Income[])) => void;
  // 既存の formIncome state を内包するか、props で受けるかは設計判断
}

export default function IncomeView(props: IncomeViewProps) {
  // App.tsx 既存の inc タブ JSX を移植
  return <div>{/* ... */}</div>;
}
```

App.tsx の `tab === "inc"` 内容を移植。フォーム state (`incF`) は当面 props で受けるか、IncomeView 内に閉じ込めるか — **内に閉じ込める方が App.tsx を薄くできるので推奨**。

- [ ] **Step 2: App.tsx で使用**

- [ ] **Step 3: テスト＋型チェック＋ブラウザ確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run dev
```

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/views/IncomeView.tsx && git add -u src && git commit -m "refactor(App): extract income tab to IncomeView"
```

---

### Task 2.11: FixedExpenseView を切り出す

**Files:**
- Create: `src/views/FixedExpenseView.tsx`
- Modify: `src/App.tsx`

- [ ] **Step 1: FixedExpenseView.tsx を作成**

App.tsx の `tab === "fix"` 内容を移植。同様にフォーム state を view 内に閉じ込める。

```tsx
// ────────── 固定費画面 ──────────
import { FixedExpense } from "../types";
// 既存 fix タブ JSX 全コピー
```

- [ ] **Step 2: App.tsx で使用**

- [ ] **Step 3: テスト＋型チェック＋ブラウザ確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run dev
```

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/views/FixedExpenseView.tsx && git add -u src && git commit -m "refactor(App): extract fixed expense tab to FixedExpenseView"
```

---

### Task 2.12: ExpenseView を切り出す

**Files:**
- Create: `src/views/ExpenseView.tsx`
- Modify: `src/App.tsx`

- [ ] **Step 1: ExpenseView.tsx を作成**

App.tsx の `tab === "exp"` 内容を移植。

```tsx
// ────────── 変動費（取引）画面 ──────────
import { Tx } from "../types";
// 既存 exp タブ JSX 全コピー
```

**重要:** Phase 3 で検索 UI を載せる土台になるので、後で props を追加しやすい構造にしておく（フィルタ・並び替え state を内包する形）。

- [ ] **Step 2: App.tsx で使用**

- [ ] **Step 3: テスト＋型チェック＋ブラウザ確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run dev
```

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/views/ExpenseView.tsx && git add -u src && git commit -m "refactor(App): extract expense tab to ExpenseView"
```

---

### Task 2.13: LoanView を切り出す

**Files:**
- Create: `src/views/LoanView.tsx`
- Modify: `src/App.tsx`

- [ ] **Step 1: LoanView.tsx を作成**

App.tsx の `tab === "loan"` 内容を移植（既存の LoanSection コンポーネントはそのまま使う）。

```tsx
// ────────── ローン画面 ──────────
import { Loan } from "../types";
import LoanSection from "../components/LoanSection";
// 既存 loan タブ JSX 全コピー
```

- [ ] **Step 2: App.tsx で使用**

- [ ] **Step 3: テスト＋型チェック＋ブラウザ確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run dev
```

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/views/LoanView.tsx && git add -u src && git commit -m "refactor(App): extract loan tab to LoanView"
```

---

### Task 2.14: Phase 2 完了確認

- [ ] **Step 1: App.tsx の行数を確認**

```bash
cd /home/kenta_kamijyo/finance_web && wc -l src/App.tsx
```
Expected: 100 行以下。それ以上ならさらに分割を検討。

- [ ] **Step 2: 各 view が独立ファイルになっていることを確認**

```bash
cd /home/kenta_kamijyo/finance_web && ls src/views/
```
Expected: `DashboardView.tsx IncomeView.tsx FixedExpenseView.tsx ExpenseView.tsx LoanView.tsx`

- [ ] **Step 3: 全テスト＋型チェック＋ビルド**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run build
```
Expected: 全 pass・エラー 0・build 成功。

- [ ] **Step 4: ブラウザで全タブ動作確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm run dev
```
- ダッシュボード切替・月切替・収入入力・固定費入力・変動費入力・ローン入力・エクスポート全てが Phase 1 と同じ挙動

問題なければ Phase 2 完了。

---

## Phase 3: PWA + 振替 + 検索 + カテゴリカスタマイズ

**目的:** ホーム画面追加、振替、検索／絞り込み、カテゴリカスタマイズの 4 機能を追加。既存データはそのまま、新機能は任意項目。

**Phase 3 完了条件:**
- ホーム画面追加が動作（PWA 化）
- 振替で残高が正しく増減
- 検索で目的の取引が見つかる
- カテゴリのカスタマイズと取引データ整合性確保

---

### Task 3.1: vite-plugin-pwa インストール（要承認）

**Files:**
- Modify: `package.json`
- Modify: `package-lock.json`

- [ ] **Step 1: ユーザーに承認を求める**

CLAUDE.md の「新しいライブラリのインストール」ルールに従い、エージェントは以下のメッセージをユーザーに送信し、明示承認を得る:

```
Phase 3 で vite-plugin-pwa を導入したい。
コマンド: cd /home/kenta_kamijyo/finance_web && npm install --save-dev vite-plugin-pwa workbox-window
追加サイズ: 約 1.5 MB (devDependencies)。
承認していい？
```

承認待ち。承認が取れたら Step 2 へ。**承認なしでは npm install を実行しない**。

- [ ] **Step 2: インストール実行**

```bash
cd /home/kenta_kamijyo/finance_web && npm install --save-dev vite-plugin-pwa workbox-window
```
Expected: エラーなくインストール完了。

- [ ] **Step 3: package.json に追加されたことを確認**

```bash
cd /home/kenta_kamijyo/finance_web && grep -E '(vite-plugin-pwa|workbox-window)' package.json
```
Expected: 両方が devDependencies に存在。

- [ ] **Step 4: テストが引き続き通ることを確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run
```
Expected: 全 pass。

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add package.json package-lock.json && git commit -m "chore: install vite-plugin-pwa and workbox-window for PWA support"
```

---

### Task 3.2: vite.config.ts に PWA 設定

**Files:**
- Modify: `vite.config.ts`

- [ ] **Step 1: VitePWA プラグインを追加**

```ts
// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg", "apple-touch-icon.png"],
      manifest: {
        name: "家計管理",
        short_name: "家計",
        description: "家計簿アプリ（PWA）",
        theme_color: "#070b14",
        background_color: "#070b14",
        display: "standalone",
        orientation: "portrait",
        scope: "/",
        start_url: "/",
        icons: [
          { src: "pwa-192x192.png", sizes: "192x192", type: "image/png" },
          { src: "pwa-512x512.png", sizes: "512x512", type: "image/png" },
          { src: "pwa-512x512.png", sizes: "512x512", type: "image/png", purpose: "any maskable" },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,png,svg,woff2}"],
        navigateFallback: "/index.html",
      },
    }),
  ],
});
```

既存の他プラグイン設定があれば残す。

- [ ] **Step 2: ビルド確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm run build
```
Expected: ビルド成功。`dist/sw.js`・`dist/manifest.webmanifest` が生成される。

- [ ] **Step 3: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add vite.config.ts && git commit -m "feat(pwa): configure VitePWA plugin with manifest and service worker"
```

---

### Task 3.3: PWA アイコン画像を追加

**Files:**
- Create: `public/pwa-192x192.png`
- Create: `public/pwa-512x512.png`
- Create: `public/apple-touch-icon.png` (180x180)

- [ ] **Step 1: アイコン画像を生成**

既存 favicon を元にアイコンを作成。手段の選択肢:
- 既存の `public/favicon.svg` から ImageMagick で生成
- もしくはユーザーに既存ロゴ画像を提供してもらう

```bash
cd /home/kenta_kamijyo/finance_web && ls public
```
Expected: `favicon.svg` or similar が見える。

ImageMagick が使えるなら:
```bash
cd /home/kenta_kamijyo/finance_web && which convert
```
- 使えれば: `convert public/favicon.svg -resize 192x192 public/pwa-192x192.png` 等で生成
- 使えなければ: ユーザーに画像ファイルを用意してもらうよう依頼。当面は **placeholder** として favicon を流用する形でも PWA は動く

- [ ] **Step 2: 仮対応として SVG を流用**

ImageMagick が無い場合: manifest の icons を SVG ベースに変更:
```ts
icons: [
  { src: "favicon.svg", sizes: "any", type: "image/svg+xml", purpose: "any maskable" },
],
```

- [ ] **Step 3: ビルド確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm run build
```
Expected: ビルド成功。

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add public/ vite.config.ts && git commit -m "feat(pwa): add PWA icon assets"
```

---

### Task 3.4: index.html に iOS apple-touch-icon

**Files:**
- Modify: `index.html`

- [ ] **Step 1: head に link を追加**

```html
<head>
  <!-- 既存タグ -->
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="家計">
  <meta name="theme-color" content="#070b14">
</head>
```

- [ ] **Step 2: ビルド＋ブラウザ動作確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm run build && npm run preview
```
ブラウザで `http://localhost:4173` を開き、DevTools → Application → Manifest を確認。Service Worker が登録されているはず。

- [ ] **Step 3: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add index.html && git commit -m "feat(pwa): add iOS apple-touch-icon and meta tags"
```

---

### Task 3.5: types.ts に Transfer 型と accountId

**Files:**
- Modify: `src/types.ts`

- [ ] **Step 1: Transfer 型を追加し、Tx/Income に accountId? を追加**

Tx と Income には既に Task 1.11 で `accountId?: string` を入れている。新たに Transfer:

```ts
export interface Transfer {
  id: string;
  date: string;           // "2026-05-15"
  fromAccountId: string;
  toAccountId: string;
  amount: number;
  memo?: string;
}
```

- [ ] **Step 2: 型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npx tsc --noEmit
```
Expected: エラー 0。

- [ ] **Step 3: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/types.ts && git commit -m "feat(types): add Transfer interface for account transfers"
```

---

### Task 3.6: 振替の残高計算ロジック（TDD）

**Files:**
- Create: `src/utils/accountBalance.ts`
- Test: `src/test/utils/accountBalance.test.ts`

- [ ] **Step 1: 失敗するテストを書く**

`src/test/utils/accountBalance.test.ts`:
```ts
import { describe, it, expect } from "vitest";
import { calculateAccountBalance } from "../../utils/accountBalance";
import { Account, Tx, Income, Transfer } from "../../types";

const baseAccount: Account = { id: "a", name: "メイン", balance: 10000 };

describe("calculateAccountBalance", () => {
  it("初期残高だけのときはその値を返す", () => {
    expect(calculateAccountBalance(baseAccount, [], [], [])).toBe(10000);
  });

  it("収入で残高が増える", () => {
    const incomes: Income[] = [{ id: "i1", date: "2026-05-01", category: "給与", amount: 5000, memo: "", accountId: "a" }];
    expect(calculateAccountBalance(baseAccount, [], incomes, [])).toBe(15000);
  });

  it("支出で残高が減る", () => {
    const transactions: Tx[] = [{ id: "t1", date: "2026-05-01", category: "食費", amount: 3000, memo: "", accountId: "a" }];
    expect(calculateAccountBalance(baseAccount, transactions, [], [])).toBe(7000);
  });

  it("振替送金で残高が減る", () => {
    const transfers: Transfer[] = [{ id: "tr1", date: "2026-05-01", fromAccountId: "a", toAccountId: "b", amount: 2000 }];
    expect(calculateAccountBalance(baseAccount, [], [], transfers)).toBe(8000);
  });

  it("振替受取で残高が増える", () => {
    const transfers: Transfer[] = [{ id: "tr1", date: "2026-05-01", fromAccountId: "b", toAccountId: "a", amount: 2000 }];
    expect(calculateAccountBalance(baseAccount, [], [], transfers)).toBe(12000);
  });

  it("accountId が一致しない取引は無視する", () => {
    const transactions: Tx[] = [{ id: "t1", date: "2026-05-01", category: "食費", amount: 3000, memo: "", accountId: "other" }];
    expect(calculateAccountBalance(baseAccount, transactions, [], [])).toBe(10000);
  });

  it("accountId が未指定の取引は無視する（紐付けされていない）", () => {
    const transactions: Tx[] = [{ id: "t1", date: "2026-05-01", category: "食費", amount: 3000, memo: "" }];
    expect(calculateAccountBalance(baseAccount, transactions, [], [])).toBe(10000);
  });
});
```

- [ ] **Step 2: テスト実行＆失敗確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run src/test/utils/accountBalance.test.ts
```
Expected: FAIL with "Cannot find module"。

- [ ] **Step 3: accountBalance.ts を実装**

`src/utils/accountBalance.ts`:
```ts
// ────────── 口座残高計算 ──────────
// 初期残高 + 入金 - 出金 - 振替送金 + 振替受取
import { Account, Tx, Income, Transfer } from "../types";

export function calculateAccountBalance(
  account: Account,
  transactions: Tx[],
  incomes: Income[],
  transfers: Transfer[]
): number {
  // この口座に紐付いた支出を合計
  const expenses = transactions
    .filter(t => t.accountId === account.id)
    .reduce((sum, t) => sum + t.amount, 0);
  // この口座に紐付いた収入を合計
  const income = incomes
    .filter(i => i.accountId === account.id)
    .reduce((sum, i) => sum + i.amount, 0);
  // この口座から外への振替
  const transferOut = transfers
    .filter(t => t.fromAccountId === account.id)
    .reduce((sum, t) => sum + t.amount, 0);
  // この口座への振替受取
  const transferIn = transfers
    .filter(t => t.toAccountId === account.id)
    .reduce((sum, t) => sum + t.amount, 0);
  return account.balance + income - expenses - transferOut + transferIn;
}
```

- [ ] **Step 4: テスト通過を確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run src/test/utils/accountBalance.test.ts
```
Expected: 全 pass。

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/utils/accountBalance.ts src/test/utils/accountBalance.test.ts && git commit -m "feat(account): add balance calculation with transfer support"
```

---

### Task 3.7: App.tsx に transfers state を追加

**Files:**
- Modify: `src/App.tsx`

- [ ] **Step 1: usePersist で transfers を持つ**

App.tsx に追加:
```ts
import { Transfer } from "./types";

const [transfers, setTransfers, transfersReady] = usePersist<Transfer[]>("kk_transfers", []);
```

- [ ] **Step 2: 既存 ready フラグの集約に transfersReady を加える**

```ts
const allReady = txReady && fxReady && loReady && cfReady && blReady && incReady &&
  account_0Ready && /* ... */ && account_8Ready && budgetReady && tplsReady && transfersReady;
```

- [ ] **Step 3: テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```
Expected: 全 pass・エラー 0。

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add -u src && git commit -m "feat(transfers): add transfers persistent state"
```

---

### Task 3.8: 振替フォーム UI

**Files:**
- Create: `src/components/TransferForm.tsx`
- Modify: `src/views/DashboardView.tsx`

- [ ] **Step 1: TransferForm.tsx を実装**

```tsx
// ────────── 振替フォーム ──────────
// 口座間の振替を入力するモーダル
import { useState } from "react";
import { Transfer, Account } from "../types";
import { Input, Select } from "../components/ui";
import { STYLE_CARD, STYLE_BUTTON_PRIMARY, STYLE_BUTTON_OUTLINE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY } from "../utils/styles";
import { parseYenAmount } from "../utils/format";

interface TransferFormProps {
  accounts: Account[];
  onSubmit: (transfer: Transfer) => void;
  onCancel: () => void;
}

export default function TransferForm({ accounts, onSubmit, onCancel }: TransferFormProps) {
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [fromAccountId, setFromAccountId] = useState(accounts[0]?.id || "");
  const [toAccountId, setToAccountId] = useState(accounts[1]?.id || "");
  const [amount, setAmount] = useState("");
  const [memo, setMemo] = useState("");
  const [err, setErr] = useState("");

  function handleSubmit() {
    if (!fromAccountId || !toAccountId) { setErr("口座を選んでください"); return; }
    if (fromAccountId === toAccountId) { setErr("同じ口座への振替はできません"); return; }
    const amountNum = parseYenAmount(amount);
    if (amountNum <= 0) { setErr("金額を入力してください"); return; }
    onSubmit({
      id: crypto.randomUUID(),
      date, fromAccountId, toAccountId, amount: amountNum, memo: memo || undefined,
    });
  }

  return (
    <div onClick={onCancel} style={{position:"fixed",inset:0,background:"rgba(0,0,0,0.72)",zIndex:200,display:"flex",alignItems:"center",justifyContent:"center",padding:20}}>
      <div onClick={e=>e.stopPropagation()} style={{...STYLE_CARD,width:"100%",maxWidth:360}}>
        <div style={{fontSize:16,fontWeight:700,color:COLOR_TEXT_PRIMARY,marginBottom:16}}>口座間の振替</div>
        <div style={{fontSize:12,color:COLOR_TEXT_SECONDARY,marginBottom:4}}>日付</div>
        <Input value={date} onChange={e => setDate(e.target.value)} type="date" />
        <div style={{height:10}} />
        <div style={{fontSize:12,color:COLOR_TEXT_SECONDARY,marginBottom:4}}>送金元</div>
        <Select value={fromAccountId} onChange={e => setFromAccountId(e.target.value)} options={accounts.map(a => a.id)} />
        <div style={{height:10}} />
        <div style={{fontSize:12,color:COLOR_TEXT_SECONDARY,marginBottom:4}}>送金先</div>
        <Select value={toAccountId} onChange={e => setToAccountId(e.target.value)} options={accounts.map(a => a.id)} />
        <div style={{height:10}} />
        <div style={{fontSize:12,color:COLOR_TEXT_SECONDARY,marginBottom:4}}>金額</div>
        <Input value={amount} onChange={e => setAmount(e.target.value)} money placeholder="0" />
        <div style={{height:10}} />
        <div style={{fontSize:12,color:COLOR_TEXT_SECONDARY,marginBottom:4}}>メモ（任意）</div>
        <Input value={memo} onChange={e => setMemo(e.target.value)} placeholder="" />
        {err && <div style={{color:"#f87171",fontSize:13,marginTop:10}}>{err}</div>}
        <div style={{display:"flex",gap:10,marginTop:16}}>
          <button onClick={onCancel} style={{...STYLE_BUTTON_OUTLINE,flex:1}}>キャンセル</button>
          <button onClick={handleSubmit} style={{...STYLE_BUTTON_PRIMARY,flex:1}}>振替する</button>
        </div>
      </div>
    </div>
  );
}
```

**注:** Select の options は accountId の配列を渡しているが、表示名は ID。実際の表示には `accountName` を表示する Select の拡張が必要。当面は accounts[].name を表示する形に Select を拡張するか、TransferForm 内で `<select>` を直接書く。

- [ ] **Step 2: DashboardView に振替ボタン＋モーダルを追加**

```tsx
// DashboardView 内
const [showTransfer, setShowTransfer] = useState(false);
// ボタン: <button onClick={() => setShowTransfer(true)}>口座間振替</button>
// モーダル: {showTransfer && <TransferForm accounts={accounts} onSubmit={...} onCancel={() => setShowTransfer(false)} />}
```

DashboardView の props に accounts と addTransfer コールバックを追加。

- [ ] **Step 3: App.tsx で addTransfer を実装**

```tsx
function addTransfer(transfer: Transfer) {
  setTransfers(prev => [transfer, ...prev]);
  setShowTransfer(false);
}
```

- [ ] **Step 4: 残高表示の更新**

口座残高表示箇所で `calculateAccountBalance` を使うように更新:
```tsx
import { calculateAccountBalance } from "./utils/accountBalance";
const account0Balance = calculateAccountBalance(account_0, transactions, incomes, transfers);
```

- [ ] **Step 5: テスト＋型チェック＋ブラウザ確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run dev
```
- 振替を実行 → 送金元の残高が減り、送金先の残高が増えることを目視確認
- 同じ口座への振替がエラーになることを確認

- [ ] **Step 6: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/components/TransferForm.tsx && git add -u src && git commit -m "feat(transfers): add transfer form UI and wire to balance display"
```

---

### Task 3.9: ExpenseView に検索・絞り込み UI（TDD）

**Files:**
- Create: `src/utils/filterTransactions.ts`
- Test: `src/test/utils/filterTransactions.test.ts`
- Modify: `src/views/ExpenseView.tsx`

- [ ] **Step 1: フィルタロジックのテストを書く**

`src/test/utils/filterTransactions.test.ts`:
```ts
import { describe, it, expect } from "vitest";
import { filterAndSortTransactions, TransactionFilter } from "../../utils/filterTransactions";
import { Tx } from "../../types";

const transactions: Tx[] = [
  { id: "1", date: "2026-05-01", category: "食費", amount: 1500, memo: "ランチ" },
  { id: "2", date: "2026-05-10", category: "交通", amount: 500, memo: "電車" },
  { id: "3", date: "2026-05-15", category: "食費", amount: 3000, memo: "ディナー" },
  { id: "4", date: "2026-05-20", category: "娯楽", amount: 2000, memo: "映画" },
];

describe("filterAndSortTransactions", () => {
  it("フィルタなしでは全件返す", () => {
    expect(filterAndSortTransactions(transactions, {}).length).toBe(4);
  });

  it("テキスト検索が memo に部分一致する（大小文字無視）", () => {
    const filter: TransactionFilter = { text: "ランチ" };
    expect(filterAndSortTransactions(transactions, filter).map(t => t.id)).toEqual(["1"]);
  });

  it("テキスト検索が category にも部分一致する", () => {
    const filter: TransactionFilter = { text: "食費" };
    expect(filterAndSortTransactions(transactions, filter).map(t => t.id).sort()).toEqual(["1", "3"]);
  });

  it("カテゴリ複数選択", () => {
    const filter: TransactionFilter = { categories: ["食費", "娯楽"] };
    expect(filterAndSortTransactions(transactions, filter).map(t => t.id).sort()).toEqual(["1", "3", "4"]);
  });

  it("日付範囲フィルタ", () => {
    const filter: TransactionFilter = { dateFrom: "2026-05-05", dateTo: "2026-05-15" };
    expect(filterAndSortTransactions(transactions, filter).map(t => t.id).sort()).toEqual(["2", "3"]);
  });

  it("金額範囲フィルタ", () => {
    const filter: TransactionFilter = { amountMin: 1000, amountMax: 2500 };
    expect(filterAndSortTransactions(transactions, filter).map(t => t.id).sort()).toEqual(["1", "4"]);
  });

  it("金額昇順ソート", () => {
    const filter: TransactionFilter = { sortBy: "amount", sortDir: "asc" };
    expect(filterAndSortTransactions(transactions, filter).map(t => t.amount)).toEqual([500, 1500, 2000, 3000]);
  });

  it("日付降順ソート", () => {
    const filter: TransactionFilter = { sortBy: "date", sortDir: "desc" };
    expect(filterAndSortTransactions(transactions, filter).map(t => t.id)).toEqual(["4", "3", "2", "1"]);
  });

  it("複数条件の組み合わせ", () => {
    const filter: TransactionFilter = {
      text: "食",
      amountMin: 2000,
      sortBy: "amount",
      sortDir: "desc",
    };
    expect(filterAndSortTransactions(transactions, filter).map(t => t.id)).toEqual(["3"]);
  });
});
```

- [ ] **Step 2: テスト実行＆失敗確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run src/test/utils/filterTransactions.test.ts
```
Expected: FAIL with "Cannot find module"。

- [ ] **Step 3: filterTransactions.ts を実装**

`src/utils/filterTransactions.ts`:
```ts
// ────────── 取引の絞り込み・並び替え ──────────
import { Tx } from "../types";

export interface TransactionFilter {
  text?: string;              // memo/category 部分一致（大小文字無視）
  categories?: string[];      // 含めるカテゴリ（OR）
  dateFrom?: string;          // "2026-05-01"
  dateTo?: string;            // "2026-05-31"
  amountMin?: number;
  amountMax?: number;
  sortBy?: "date" | "amount";
  sortDir?: "asc" | "desc";
}

export function filterAndSortTransactions(items: Tx[], filter: TransactionFilter): Tx[] {
  const text = filter.text?.toLowerCase().trim();
  let result = items.filter(tx => {
    if (text) {
      const memoMatch = (tx.memo || "").toLowerCase().includes(text);
      const categoryMatch = tx.category.toLowerCase().includes(text);
      if (!memoMatch && !categoryMatch) return false;
    }
    if (filter.categories && filter.categories.length > 0) {
      if (!filter.categories.includes(tx.category)) return false;
    }
    if (filter.dateFrom && tx.date < filter.dateFrom) return false;
    if (filter.dateTo && tx.date > filter.dateTo) return false;
    if (filter.amountMin !== undefined && tx.amount < filter.amountMin) return false;
    if (filter.amountMax !== undefined && tx.amount > filter.amountMax) return false;
    return true;
  });

  if (filter.sortBy) {
    const dir = filter.sortDir === "asc" ? 1 : -1;
    result = [...result].sort((a, b) => {
      if (filter.sortBy === "date") return dir * a.date.localeCompare(b.date);
      if (filter.sortBy === "amount") return dir * (a.amount - b.amount);
      return 0;
    });
  }
  return result;
}
```

- [ ] **Step 4: テスト通過を確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run src/test/utils/filterTransactions.test.ts
```
Expected: 全 pass。

- [ ] **Step 5: ExpenseView に検索 UI を追加**

`src/views/ExpenseView.tsx` 内に検索 state を追加:
```tsx
import { useState, useMemo } from "react";
import { filterAndSortTransactions, TransactionFilter } from "../utils/filterTransactions";
import { EXPENSE_CATEGORIES } from "../utils/format";

const [searchText, setSearchText] = useState("");
const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
const [dateFrom, setDateFrom] = useState("");
const [dateTo, setDateTo] = useState("");
const [amountMin, setAmountMin] = useState("");
const [amountMax, setAmountMax] = useState("");
const [sortBy, setSortBy] = useState<"date" | "amount">("date");
const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
const [showFilters, setShowFilters] = useState(false);

const filteredTransactions = useMemo(() => {
  return filterAndSortTransactions(props.monthlyTransactions, {
    text: searchText || undefined,
    categories: selectedCategories.length > 0 ? selectedCategories : undefined,
    dateFrom: dateFrom || undefined,
    dateTo: dateTo || undefined,
    amountMin: amountMin ? Number(amountMin) : undefined,
    amountMax: amountMax ? Number(amountMax) : undefined,
    sortBy, sortDir,
  });
}, [props.monthlyTransactions, searchText, selectedCategories, dateFrom, dateTo, amountMin, amountMax, sortBy, sortDir]);
```

UI 要素として:
- テキスト入力欄（メモ・カテゴリ検索）
- 「絞り込み」ボタンでフィルタパネルを開閉
- カテゴリチェックボックスのリスト
- 日付 from/to
- 金額 min/max
- ソート選択 (日付/金額) + asc/desc トグル
- 「クリア」ボタン

既存の `monthlyTransactions` のレンダリングを `filteredTransactions` に差し替え。

- [ ] **Step 6: 全テスト＋型チェック＋ブラウザ確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run dev
```
- テキスト検索で「ランチ」と打って絞り込めることを確認
- カテゴリチェックで絞り込み可
- 日付・金額・ソートも動く

- [ ] **Step 7: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/utils/filterTransactions.ts src/test/utils/filterTransactions.test.ts && git add -u src && git commit -m "feat(expense): add search/filter/sort to ExpenseView"
```

---

### Task 3.10: IncomeView にも検索・絞り込み

**Files:**
- Modify: `src/views/IncomeView.tsx`

- [ ] **Step 1: filterTransactions のロジックを Income にも使えるよう汎用化 (必要なら)**

Income と Tx は構造が同じ（id, date, category, amount, memo, accountId?）なので、`filterAndSortTransactions` を再利用可能。型を緩めたい場合は:

```ts
// filterTransactions.ts を汎用化（オプション）
export function filterAndSortItems<T extends { date: string; category: string; amount: number; memo?: string }>(
  items: T[], filter: TransactionFilter
): T[] { /* 同じロジック */ }

// 既存 filterAndSortTransactions は filterAndSortItems への薄いラッパに
export function filterAndSortTransactions(items: Tx[], filter: TransactionFilter): Tx[] {
  return filterAndSortItems(items, filter);
}
```

- [ ] **Step 2: IncomeView にフィルタ UI を追加**

ExpenseView と同じ UI を Income 向けに複製。カテゴリは `INCOME_CATEGORIES` を使う。

- [ ] **Step 3: テスト＋型チェック＋ブラウザ確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run dev
```

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add -u src && git commit -m "feat(income): add search/filter/sort to IncomeView"
```

---

### Task 3.11: CategoryConfig 型と永続化

**Files:**
- Modify: `src/types.ts`
- Modify: `src/App.tsx`

- [ ] **Step 1: types.ts に CategoryConfig**

```ts
export interface CategoryItem {
  id: string;
  name: string;
  icon: string;
  order: number;
}

export interface CategoryConfig {
  expense: CategoryItem[];
  fixedExpense: CategoryItem[];
  income: CategoryItem[];
}
```

- [ ] **Step 2: 初期値生成 helper**

`src/utils/defaultCategories.ts`:
```ts
import { CategoryConfig } from "../types";
import { EXPENSE_CATEGORIES, FIXED_EXPENSE_CATEGORIES, INCOME_CATEGORIES, EXPENSE_CATEGORY_ICONS, FIXED_EXPENSE_CATEGORY_ICONS, INCOME_CATEGORY_ICONS } from "./format";

export function makeDefaultCategoryConfig(): CategoryConfig {
  return {
    expense: EXPENSE_CATEGORIES.map((name, i) => ({
      id: `exp-${i}`, name, icon: EXPENSE_CATEGORY_ICONS[name] || "📦", order: i
    })),
    fixedExpense: FIXED_EXPENSE_CATEGORIES.map((name, i) => ({
      id: `fix-${i}`, name, icon: FIXED_EXPENSE_CATEGORY_ICONS[name] || "📦", order: i
    })),
    income: INCOME_CATEGORIES.map((name, i) => ({
      id: `inc-${i}`, name, icon: INCOME_CATEGORY_ICONS[name] || "💰", order: i
    })),
  };
}
```

- [ ] **Step 3: App.tsx に usePersist 追加**

```ts
import { CategoryConfig } from "./types";
import { makeDefaultCategoryConfig } from "./utils/defaultCategories";

const [categoryConfig, setCategoryConfig, categoryConfigReady] = usePersist<CategoryConfig>(
  "kk_categories",
  makeDefaultCategoryConfig()
);
```

- [ ] **Step 4: テスト＋型チェック**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit
```

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/utils/defaultCategories.ts && git add -u src && git commit -m "feat(categories): add CategoryConfig persistent state with defaults"
```

---

### Task 3.12: SettingsView でカテゴリ管理

**Files:**
- Create: `src/views/SettingsView.tsx`
- Modify: `src/App.tsx`

- [ ] **Step 1: SettingsView.tsx を作成**

```tsx
// ────────── 設定画面（カテゴリ管理） ──────────
import { useState } from "react";
import { CategoryConfig, CategoryItem, Tx, Income, FixedExpense } from "../types";
import { Input } from "../components/ui";
import { STYLE_CARD, STYLE_BUTTON_PRIMARY, STYLE_BUTTON_OUTLINE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_NEGATIVE } from "../utils/styles";
import { makeDefaultCategoryConfig } from "../utils/defaultCategories";

type CategoryKind = "expense" | "fixedExpense" | "income";

interface SettingsViewProps {
  categoryConfig: CategoryConfig;
  setCategoryConfig: (updater: CategoryConfig | ((p: CategoryConfig) => CategoryConfig)) => void;
  transactions: Tx[];
  setTransactions: (updater: Tx[] | ((p: Tx[]) => Tx[])) => void;
  incomes: Income[];
  setIncomes: (updater: Income[] | ((p: Income[]) => Income[])) => void;
  fixedExpenses: FixedExpense[];
  setFixedExpenses: (updater: FixedExpense[] | ((p: FixedExpense[]) => FixedExpense[])) => void;
  onReset: () => void;
}

export default function SettingsView(props: SettingsViewProps) {
  const [kind, setKind] = useState<CategoryKind>("expense");
  const [newName, setNewName] = useState("");
  const [newIcon, setNewIcon] = useState("📦");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editIcon, setEditIcon] = useState("");
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<CategoryItem | null>(null);

  const items: CategoryItem[] = props.categoryConfig[kind].slice().sort((a, b) => a.order - b.order);

  function addCategory() {
    if (!newName.trim()) return;
    const newItem: CategoryItem = {
      id: `${kind}-${Date.now()}-${Math.random().toString(36).slice(2,7)}`,
      name: newName.trim(),
      icon: newIcon || "📦",
      order: items.length,
    };
    props.setCategoryConfig(prev => ({ ...prev, [kind]: [...prev[kind], newItem] }));
    setNewName(""); setNewIcon("📦");
  }

  function saveEdit(item: CategoryItem) {
    const newNameTrimmed = editName.trim();
    if (!newNameTrimmed) return;
    const oldName = item.name;
    // 1. カテゴリ自体を更新
    props.setCategoryConfig(prev => ({
      ...prev,
      [kind]: prev[kind].map(i => i.id === item.id ? { ...i, name: newNameTrimmed, icon: editIcon || i.icon } : i),
    }));
    // 2. 既存取引データの category 名も一括更新（リネームの場合）
    if (newNameTrimmed !== oldName) {
      if (kind === "expense") {
        props.setTransactions(prev => prev.map(t => t.category === oldName ? { ...t, category: newNameTrimmed } : t));
      } else if (kind === "income") {
        props.setIncomes(prev => prev.map(t => t.category === oldName ? { ...t, category: newNameTrimmed } : t));
      } else if (kind === "fixedExpense") {
        props.setFixedExpenses(prev => prev.map(t => t.category === oldName ? { ...t, category: newNameTrimmed } : t));
      }
    }
    setEditingId(null); setEditName(""); setEditIcon("");
  }

  function attemptDelete(item: CategoryItem) {
    // 削除前に使用中チェック
    const inUse = kind === "expense" ? props.transactions.some(t => t.category === item.name)
      : kind === "income" ? props.incomes.some(t => t.category === item.name)
      : props.fixedExpenses.some(t => t.category === item.name);
    if (inUse) {
      alert(`「${item.name}」は既存のデータで使われているため削除できません。先に該当データを別カテゴリに移してください。`);
      return;
    }
    setDeleteTarget(item);
  }

  function confirmDelete() {
    if (!deleteTarget) return;
    props.setCategoryConfig(prev => ({
      ...prev,
      [kind]: prev[kind].filter(i => i.id !== deleteTarget.id),
    }));
    setDeleteTarget(null);
  }

  function moveUp(item: CategoryItem) {
    const sorted = items.slice();
    const idx = sorted.findIndex(i => i.id === item.id);
    if (idx <= 0) return;
    const above = sorted[idx - 1];
    props.setCategoryConfig(prev => ({
      ...prev,
      [kind]: prev[kind].map(i => {
        if (i.id === item.id) return { ...i, order: above.order };
        if (i.id === above.id) return { ...i, order: item.order };
        return i;
      }),
    }));
  }

  function moveDown(item: CategoryItem) {
    const sorted = items.slice();
    const idx = sorted.findIndex(i => i.id === item.id);
    if (idx < 0 || idx >= sorted.length - 1) return;
    const below = sorted[idx + 1];
    props.setCategoryConfig(prev => ({
      ...prev,
      [kind]: prev[kind].map(i => {
        if (i.id === item.id) return { ...i, order: below.order };
        if (i.id === below.id) return { ...i, order: item.order };
        return i;
      }),
    }));
  }

  function resetAll() {
    props.setCategoryConfig(makeDefaultCategoryConfig());
    setShowResetConfirm(false);
  }

  return (
    <div>
      <div style={{...STYLE_CARD}}>
        <div style={{fontSize:15,fontWeight:700,color:COLOR_TEXT_PRIMARY,marginBottom:12}}>カテゴリ管理</div>
        {/* タブ切替 */}
        <div style={{display:"flex",gap:8,marginBottom:14}}>
          {(["expense","fixedExpense","income"] as CategoryKind[]).map(k => (
            <button key={k} onClick={() => setKind(k)} style={{...STYLE_BUTTON_OUTLINE, flex:1, borderColor: kind===k ? COLOR_TEXT_PRIMARY : undefined}}>
              {k === "expense" ? "変動費" : k === "fixedExpense" ? "固定費" : "収入"}
            </button>
          ))}
        </div>
        {/* 追加フォーム */}
        <div style={{display:"flex",gap:8,marginBottom:14}}>
          <input value={newIcon} onChange={e => setNewIcon(e.target.value)} placeholder="📦" style={{width:50,fontSize:18,textAlign:"center"}} />
          <Input value={newName} onChange={e => setNewName(e.target.value)} placeholder="新しいカテゴリ名" />
          <button onClick={addCategory} style={{...STYLE_BUTTON_PRIMARY,width:80}}>追加</button>
        </div>
        {/* 一覧 */}
        {items.map(item => (
          <div key={item.id} style={{display:"flex",alignItems:"center",gap:8,padding:"8px 0",borderBottom:"1px solid rgba(148,163,184,0.08)"}}>
            {editingId === item.id ? (
              <>
                <input value={editIcon} onChange={e => setEditIcon(e.target.value)} style={{width:36,fontSize:18}} />
                <Input value={editName} onChange={e => setEditName(e.target.value)} />
                <button onClick={() => saveEdit(item)} style={{...STYLE_BUTTON_PRIMARY,width:60}}>保存</button>
                <button onClick={() => setEditingId(null)} style={{...STYLE_BUTTON_OUTLINE,width:60}}>取消</button>
              </>
            ) : (
              <>
                <span style={{fontSize:20}}>{item.icon}</span>
                <span style={{flex:1,color:COLOR_TEXT_PRIMARY}}>{item.name}</span>
                <button onClick={() => moveUp(item)} title="上へ" style={{background:"none",border:"none",color:COLOR_TEXT_SECONDARY,cursor:"pointer"}}>↑</button>
                <button onClick={() => moveDown(item)} title="下へ" style={{background:"none",border:"none",color:COLOR_TEXT_SECONDARY,cursor:"pointer"}}>↓</button>
                <button onClick={() => { setEditingId(item.id); setEditName(item.name); setEditIcon(item.icon); }} style={{background:"none",border:"none",color:COLOR_TEXT_SECONDARY,cursor:"pointer"}}>✏️</button>
                <button onClick={() => attemptDelete(item)} style={{background:"none",border:"none",color:COLOR_NEGATIVE,cursor:"pointer"}}>🗑️</button>
              </>
            )}
          </div>
        ))}
        {/* リセット */}
        <button onClick={() => setShowResetConfirm(true)} style={{...STYLE_BUTTON_OUTLINE,marginTop:20,color:COLOR_NEGATIVE}}>カテゴリをデフォルトにリセット</button>
      </div>
      {/* リセット確認 */}
      {showResetConfirm && (
        <div onClick={() => setShowResetConfirm(false)} style={{position:"fixed",inset:0,background:"rgba(0,0,0,0.72)",zIndex:200,display:"flex",alignItems:"center",justifyContent:"center",padding:20}}>
          <div onClick={e=>e.stopPropagation()} style={{...STYLE_CARD,maxWidth:340}}>
            <div style={{fontSize:15,fontWeight:700,color:COLOR_TEXT_PRIMARY,marginBottom:8}}>カテゴリをリセット</div>
            <div style={{fontSize:13,color:COLOR_TEXT_SECONDARY,marginBottom:16}}>カスタマイズが全て削除されデフォルトに戻ります。既存の取引データは保持されます。</div>
            <div style={{display:"flex",gap:10}}>
              <button onClick={() => setShowResetConfirm(false)} style={{...STYLE_BUTTON_OUTLINE,flex:1}}>キャンセル</button>
              <button onClick={resetAll} style={{...STYLE_BUTTON_PRIMARY,flex:1,background:COLOR_NEGATIVE}}>リセット</button>
            </div>
          </div>
        </div>
      )}
      {/* 削除確認 */}
      {deleteTarget && (
        <div onClick={() => setDeleteTarget(null)} style={{position:"fixed",inset:0,background:"rgba(0,0,0,0.72)",zIndex:200,display:"flex",alignItems:"center",justifyContent:"center",padding:20}}>
          <div onClick={e=>e.stopPropagation()} style={{...STYLE_CARD,maxWidth:340}}>
            <div style={{fontSize:15,fontWeight:700,color:COLOR_TEXT_PRIMARY,marginBottom:8}}>カテゴリを削除</div>
            <div style={{fontSize:13,color:COLOR_TEXT_SECONDARY,marginBottom:16}}>「{deleteTarget.name}」を削除します。よろしいですか？</div>
            <div style={{display:"flex",gap:10}}>
              <button onClick={() => setDeleteTarget(null)} style={{...STYLE_BUTTON_OUTLINE,flex:1}}>キャンセル</button>
              <button onClick={confirmDelete} style={{...STYLE_BUTTON_PRIMARY,flex:1,background:COLOR_NEGATIVE}}>削除</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: App.tsx に「設定」タブを追加**

```tsx
// タブ定義に "set" を追加
const tabs = [
  { key: "dash", label: "📊" },
  { key: "inc", label: "💰" },
  { key: "fix", label: "🏠" },
  { key: "exp", label: "🍱" },
  { key: "loan", label: "💳" },
  { key: "set", label: "⚙️" },
];

{tab === "set" && (
  <SettingsView
    categoryConfig={categoryConfig}
    setCategoryConfig={setCategoryConfig}
    transactions={transactions}
    setTransactions={setTransactions}
    incomes={incomes}
    setIncomes={setIncomes}
    fixedExpenses={fixedExpenses}
    setFixedExpenses={setFixedExpenses}
    onReset={() => {}}
  />
)}
```

- [ ] **Step 3: テスト＋型チェック＋ブラウザ確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run dev
```
- 設定タブを開く
- 新しいカテゴリを追加できる
- 既存カテゴリ名を変更すると既存取引も連動して変わる（リネーム反映）
- 使用中カテゴリの削除は拒否される
- 未使用カテゴリの削除は通る
- 並び替えが効く
- リセットでデフォルトに戻る

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add src/views/SettingsView.tsx && git add -u src && git commit -m "feat(settings): add SettingsView for category management"
```

---

### Task 3.13: フォームをカテゴリ動的化

**Files:**
- Modify: `src/views/ExpenseView.tsx`
- Modify: `src/views/IncomeView.tsx`
- Modify: `src/views/FixedExpenseView.tsx`

- [ ] **Step 1: 各 view でハードコードされた CATEGORIES を categoryConfig 経由に置換**

ExpenseView の props に `categoryConfig` を追加し、Select の options を:
```tsx
const expenseCategoryNames = props.categoryConfig.expense
  .slice().sort((a,b) => a.order - b.order).map(c => c.name);

<Select value={form.category} onChange={...} options={expenseCategoryNames} icons={
  Object.fromEntries(props.categoryConfig.expense.map(c => [c.name, c.icon]))
} />
```

同様に IncomeView は `categoryConfig.income`、FixedExpenseView は `categoryConfig.fixedExpense` を参照。

- [ ] **Step 2: 検索 UI のカテゴリチェックボックスも動的化**

ExpenseView の `EXPENSE_CATEGORIES` 参照を `expenseCategoryNames` に置換。

- [ ] **Step 3: App.tsx で categoryConfig を各 view に渡す**

```tsx
<ExpenseView ... categoryConfig={categoryConfig} />
<IncomeView ... categoryConfig={categoryConfig} />
<FixedExpenseView ... categoryConfig={categoryConfig} />
```

- [ ] **Step 4: テスト＋型チェック＋ブラウザ確認**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run dev
```
- 設定画面で新カテゴリ「サウナ」を追加 → 変動費フォームのカテゴリ Select に「サウナ」が現れる
- 既存カテゴリのアイコンを変更 → フォーム・履歴の表示も即時反映される

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo/finance_web && git add -u src && git commit -m "feat(categories): dynamic category lookup in expense/income/fixed forms"
```

---

### Task 3.14: Phase 3 完了確認

- [ ] **Step 1: PWA インストールテスト**

```bash
cd /home/kenta_kamijyo/finance_web && npm run build && npm run preview
```
ブラウザで開き、DevTools → Application:
- Manifest が読み込まれている
- Service Worker が登録されている
- 「ホーム画面に追加」（モバイル）または「アプリをインストール」（デスクトップ Chrome）が表示される

- [ ] **Step 2: 振替動作テスト**

ブラウザで:
- 口座 A → 口座 B に 1000 円振替
- 口座 A の残高が -1000、口座 B の残高が +1000 になることを確認
- 同じ口座への振替がエラーで弾かれることを確認

- [ ] **Step 3: 検索動作テスト**

- 変動費タブで「ランチ」と検索 → 該当だけ表示
- カテゴリチェックで絞り込み
- 日付範囲・金額範囲で絞り込み
- ソート (日付/金額/asc/desc)

- [ ] **Step 4: カテゴリ管理テスト**

- 新カテゴリ追加
- 既存カテゴリのリネーム → 既存取引も新名で表示
- 使用中カテゴリの削除拒否
- 未使用カテゴリの削除
- 並び替え
- リセット

- [ ] **Step 5: 全テスト＋型チェック＋ビルド**

```bash
cd /home/kenta_kamijyo/finance_web && npm test -- --run && npx tsc --noEmit && npm run build
```
Expected: 全 pass・エラー 0・build 成功。

- [ ] **Step 6: 既存データ動作テスト**

Phase 1 開始時から使い続けている既存ユーザーデータが:
- そのまま読み込める
- 過去取引が表示できる
- 過去ローンが表示できる
- 過去固定費が動作する

問題なければ Phase 3 完了。

---

## 自己レビュー

実装計画として、以下を確認した:

**1. スペック網羅:**
- ✅ Phase 1: styles/format/loanCalc/ui/App.tsx の全リネーム (Task 1.2-1.7)
- ✅ Phase 1: 型強化 (Task 1.8-1.11)
- ✅ Phase 1: memo/note 統一 (Task 1.12)
- ✅ Phase 1: 空 catch 全置換 (Task 1.13)
- ✅ Phase 2: usePersist mem バグ修正 (Task 2.1)
- ✅ Phase 2: useMemo メモ化 (Task 2.2, 2.6)
- ✅ Phase 2: MN/ST 外部化 (Task 2.3, 2.4)
- ✅ Phase 2: dataExport 抽出 (Task 2.5)
- ✅ Phase 2: useMonthlyData/useAutoPayment/useDataExport (Task 2.6-2.8)
- ✅ Phase 2: 5 view 分割 (Task 2.9-2.13)
- ✅ Phase 3: PWA (Task 3.1-3.4)
- ✅ Phase 3: 振替 (Task 3.5-3.8)
- ✅ Phase 3: 検索 (Task 3.9-3.10)
- ✅ Phase 3: カテゴリ (Task 3.11-3.13)

**2. プレースホルダ:**
- なし。Bash/Edit ベースで実行可能な具体手順のみ。
- 既存実装の「中身そのまま移植」は明示しており、その箇所は Read で確認する手順を含めている。

**3. 型整合:**
- `parseYenAmount`/`formatYen`/`MONTH_LABELS` 等の名称は全タスクで一貫
- `Transfer`/`CategoryConfig`/`CategoryItem`/`TransactionFilter` の型は Task 3.5/3.11/3.9 で定義し、後続タスクで参照
- `calculateAccountBalance` のシグネチャは Task 3.6 で確定し、Task 3.8 で使用

---

## 実行方法の選択

計画完成。`/home/kenta_kamijyo/finance_web/docs/superpowers/plans/2026-05-15-finance-web-ux-improvements.md` に保存済み。2 つの実行方法から選択する:

**1. Subagent-Driven（推奨）** - タスクごとに新しい subagent を生成し、レビューを挟みながら高速反復。長時間作業を安定して進められる。

**2. Inline Execution** - このセッション内でタスクを順次実行。途中でレビューを挟む。

どちらで進める？
