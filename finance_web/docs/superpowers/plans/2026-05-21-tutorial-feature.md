# チュートリアル機能 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 初回起動時に6ページのスライド式モーダルでアプリの使い方を案内し、設定画面からいつでも再表示できるチュートリアル機能を追加する。

**Architecture:** `TutorialModal.tsx` を新規作成し、App.tsx で `showTutorial` state を管理・初回自動表示する。SettingsView には「使い方を見る」ボタンを追加して再表示できるようにする。`localStorage["kk_tutorial_done"]` で表示済み判定を行う。

**Tech Stack:** React 18、TypeScript、Vitest + @testing-library/react（既存）

---

## ファイル構成

| ファイル | 変更種別 | 担当 |
|---------|---------|------|
| `src/components/TutorialModal.tsx` | 新規作成 | モーダル本体・6ページコンテンツ |
| `src/test/components/TutorialModal.test.tsx` | 新規作成 | TutorialModal のユニットテスト |
| `src/App.tsx` | 修正（3箇所） | showTutorial state / JSX追加 / SettingsView props追加 |
| `src/views/SettingsView.tsx` | 修正（2箇所） | onOpenTutorial prop追加 / ボタン追加 |

---

## Task 1: TutorialModal コンポーネントをテスト駆動で作成

**Files:**
- Create: `src/components/TutorialModal.tsx`
- Create: `src/test/components/TutorialModal.test.tsx`

### Step 1: テストファイルを作成する

- [ ] `src/test/components/TutorialModal.test.tsx` を以下の内容で作成する

```tsx
// ────────── TutorialModal コンポーネントのテスト ──────────
import { render, screen, fireEvent } from "@testing-library/react";
import TutorialModal from "../../components/TutorialModal";

const noop = () => {};

describe("TutorialModal（非表示状態）", () => {
  it("open=false のとき何も表示されない", () => {
    const { container } = render(<TutorialModal open={false} onClose={noop} />);
    expect(container.firstChild).toBeNull();
  });
});

describe("TutorialModal（表示状態）", () => {
  it("open=true のとき最初のページ（ようこそ！）が表示される", () => {
    render(<TutorialModal open={true} onClose={noop} />);
    expect(screen.getByText("ようこそ！")).toBeInTheDocument();
  });

  it("最初は「次へ」ボタンが表示される", () => {
    render(<TutorialModal open={true} onClose={noop} />);
    expect(screen.getByText("次へ")).toBeInTheDocument();
  });

  it("「次へ」を5回クリックすると「はじめる」ボタンが表示される", () => {
    render(<TutorialModal open={true} onClose={noop} />);
    const nextBtn = () => screen.getByText("次へ");
    fireEvent.click(nextBtn()); // page 1
    fireEvent.click(nextBtn()); // page 2
    fireEvent.click(nextBtn()); // page 3
    fireEvent.click(nextBtn()); // page 4
    fireEvent.click(nextBtn()); // page 5（最終）
    expect(screen.getByText("はじめる")).toBeInTheDocument();
  });

  it("「はじめる」クリックで onClose が呼ばれる", () => {
    const onClose = vi.fn();
    render(<TutorialModal open={true} onClose={onClose} />);
    // 最終ページまで進む
    for (let i = 0; i < 5; i++) fireEvent.click(screen.getByText("次へ"));
    fireEvent.click(screen.getByText("はじめる"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("✕ボタンクリックで onClose が呼ばれる", () => {
    const onClose = vi.fn();
    render(<TutorialModal open={true} onClose={onClose} />);
    fireEvent.click(screen.getByLabelText("閉じる"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("open が false → true になるとページが 0 にリセットされる", () => {
    const { rerender } = render(<TutorialModal open={true} onClose={noop} />);
    // ページを2まで進める
    fireEvent.click(screen.getByText("次へ"));
    fireEvent.click(screen.getByText("次へ"));
    // 一度閉じて再度開く
    rerender(<TutorialModal open={false} onClose={noop} />);
    rerender(<TutorialModal open={true} onClose={noop} />);
    // ページ0の内容（ようこそ！）が再表示される
    expect(screen.getByText("ようこそ！")).toBeInTheDocument();
  });
});
```

### Step 2: テストが失敗することを確認する

- [ ] 以下のコマンドを実行する（TutorialModal がまだ存在しないのでエラーになる）

```
cd /home/kenta_kamijyo/finance_web && npm test -- --reporter=verbose src/test/components/TutorialModal.test.tsx
```

期待される出力：`Cannot find module '../../components/TutorialModal'` のエラー

### Step 3: TutorialModal.tsx を実装する

- [ ] `src/components/TutorialModal.tsx` を以下の内容で作成する

```tsx
// ────────── チュートリアルモーダル ──────────
// 初回起動時に6ページのスライドでアプリの使い方を案内するモーダル
// open=false の時は何も描画しない

import { useState, useEffect } from "react";
import { STYLE_BUTTON_PRIMARY } from "../utils/styles";

// 各ページの内容（アイコン・タイトル・説明文）
const PAGES = [
  {
    icon: "💰",
    title: "ようこそ！",
    desc: "このアプリは収入・支出・ローン・貯金目標をまとめて管理できる家計管理ツールです。データはすべてこの端末に暗号化保存されます。",
  },
  {
    icon: "💰",
    title: "収入タブ",
    desc: "給与・副業・ボーナスなどの収入を登録します。カテゴリごとに分類でき、月ごとの合計が自動集計されます。",
  },
  {
    icon: "📌",
    title: "固定費タブ",
    desc: "家賃・保険・サブスクなど毎月決まって出ていく費用を登録します。年払いも月割りで自動換算されます。",
  },
  {
    icon: "💸",
    title: "支出タブ",
    desc: "食費・交通費など変動する日々の出費を記録します。カテゴリ別に集計・グラフ表示されます。",
  },
  {
    icon: "🏦",
    title: "ローンタブ",
    desc: "住宅ローン・カーローンなどを登録し、返済シミュレーションができます。繰り上げ返済の効果も試算できます。",
  },
  {
    icon: "⚙️",
    title: "設定タブ",
    desc: "カテゴリの追加・編集・並び替えができます。データのバックアップ（JSON書き出し）と復元もここから行えます。",
  },
];

// このコンポーネントが受け取る props の型
interface TutorialModalProps {
  open: boolean;      // true = 表示、false = 非表示
  onClose: () => void; // 閉じる時に呼ばれる関数
}

export default function TutorialModal({ open, onClose }: TutorialModalProps) {
  // 現在表示中のページ番号（0〜5）
  const [page, setPage] = useState(0);

  // open が true になるたびに最初のページに戻す
  useEffect(() => {
    if (open) setPage(0);
  }, [open]);

  // open=false の時は何も描画しない
  if (!open) return null;

  const current = PAGES[page];         // 今表示するページのデータ
  const isLast = page === PAGES.length - 1; // 最終ページかどうか

  return (
    // 背景オーバーレイ（タップしても閉じない → 誤操作防止）
    <div style={{
      position: "fixed",
      inset: 0,
      background: "rgba(0,0,0,0.72)",
      zIndex: 300,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 20,
    }}>
      {/* モーダル本体 */}
      <div style={{
        background: "rgba(15,23,42,0.98)",
        border: "1px solid rgba(148,163,184,0.16)",
        borderRadius: 22,
        padding: "28px 24px 24px",
        width: "100%",
        maxWidth: 340,
        backdropFilter: "blur(20px)",
        position: "relative",
        textAlign: "center",
      }}>
        {/* ✕ 閉じるボタン（右上） */}
        <button
          aria-label="閉じる"
          onClick={onClose}
          style={{
            position: "absolute",
            top: 14,
            right: 14,
            background: "none",
            border: "none",
            color: "rgba(255,255,255,0.4)",
            fontSize: 20,
            cursor: "pointer",
            lineHeight: 1,
            padding: 4,
            fontFamily: "inherit",
          }}
        >
          ✕
        </button>

        {/* ページアイコン（大） */}
        <div style={{ fontSize: 52, marginBottom: 16, lineHeight: 1 }}>
          {current.icon}
        </div>

        {/* タイトル */}
        <div style={{
          fontSize: 18,
          fontWeight: 700,
          color: "#f5f5f7",
          marginBottom: 12,
        }}>
          {current.title}
        </div>

        {/* 説明文 */}
        <div style={{
          fontSize: 13,
          color: "#9a9aa3",
          lineHeight: 1.7,
          marginBottom: 24,
          minHeight: 60,  // 高さを揃えてモーダルがガタつかないようにする
        }}>
          {current.desc}
        </div>

        {/* ページドット（●○○…） */}
        <div style={{
          display: "flex",
          justifyContent: "center",
          gap: 6,
          marginBottom: 20,
        }}>
          {PAGES.map((_, i) => (
            <div
              key={i}
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                // 現在ページは明るい色、それ以外は暗い色
                background: i === page ? "#818cf8" : "rgba(255,255,255,0.2)",
                transition: "background 0.2s ease",
              }}
            />
          ))}
        </div>

        {/* 次へ / はじめる ボタン */}
        <button
          onClick={() => {
            if (isLast) {
              onClose(); // 最終ページは閉じる
            } else {
              setPage(p => p + 1); // 次のページへ
            }
          }}
          style={{
            ...STYLE_BUTTON_PRIMARY,
            width: "100%",
            // 最終ページは緑色にして「完了感」を出す
            background: isLast ? "#34d399" : undefined,
            color: isLast ? "#0a0a0c" : undefined,
          }}
        >
          {isLast ? "はじめる" : "次へ"}
        </button>
      </div>
    </div>
  );
}
```

### Step 4: テストが通ることを確認する

- [ ] 以下のコマンドを実行する

```
cd /home/kenta_kamijyo/finance_web && npm test -- --reporter=verbose src/test/components/TutorialModal.test.tsx
```

期待される出力：
```
✓ TutorialModal（非表示状態） > open=false のとき何も表示されない
✓ TutorialModal（表示状態） > open=true のとき最初のページ（ようこそ！）が表示される
✓ TutorialModal（表示状態） > 最初は「次へ」ボタンが表示される
✓ TutorialModal（表示状態） > 「次へ」を5回クリックすると「はじめる」ボタンが表示される
✓ TutorialModal（表示状態） > 「はじめる」クリックで onClose が呼ばれる
✓ TutorialModal（表示状態） > ✕ボタンクリックで onClose が呼ばれる
✓ TutorialModal（表示状態） > open が false → true になるとページが 0 にリセットされる

Test Files  1 passed
Tests  7 passed
```

### Step 5: コミットする

- [ ] 以下のコマンドを実行する

```
cd /home/kenta_kamijyo && git add finance_web/src/components/TutorialModal.tsx finance_web/src/test/components/TutorialModal.test.tsx
git commit -m "feat: TutorialModal コンポーネントを追加（6ページスライド式）"
```

---

## Task 2: App.tsx に showTutorial state と TutorialModal を追加する

**Files:**
- Modify: `src/App.tsx`

### Step 1: App.tsx の現在の状態を確認する

- [ ] `src/App.tsx` の以下の3箇所を確認する
  - `import` 行（1〜35行目付近）
  - `AppInner` 内の `useState` 群（45〜63行目付近）
  - `SettingsView` の JSX（265〜275行目付近）

### Step 2: import に TutorialModal を追加する

- [ ] `src/App.tsx` の import セクション末尾（`const SettingsView = lazy(...)` の直後）に以下を追記する

```tsx
// TutorialModal は初回表示に使うため即時ロード（lazy にしない）
import TutorialModal from "./components/TutorialModal";
```

既存コード（変更前）：
```tsx
const SettingsView = lazy(() => import("./views/SettingsView"));
```

変更後：
```tsx
const SettingsView = lazy(() => import("./views/SettingsView"));
// TutorialModal は初回表示に使うため即時ロード（lazy にしない）
import TutorialModal from "./components/TutorialModal";
```

※ import は必ず他の import と同じ階層（ファイル先頭）に記述すること。TypeScript の import 文はトップレベルにしか書けないため、`AppInner` 関数の外に置く。実際には `const SettingsView = lazy(...)` の前ではなく、ファイル先頭の import ブロックに追加するほうが正しい。以下のように修正する：

`src/App.tsx` の行 34 付近（`const SettingsView = lazy(...)` の1行前）の import ブロック末尾に追記する：

変更前の import ブロック末尾：
```tsx
import DashboardView from "./views/DashboardView";
// それ以外のビューは初回ロードを軽くするためタブを開いた時に動的ロード（コード分割）
const IncomeView = lazy(() => import("./views/IncomeView"));
const FixedExpenseView = lazy(() => import("./views/FixedExpenseView"));
const ExpenseView = lazy(() => import("./views/ExpenseView"));
const LoanView = lazy(() => import("./views/LoanView"));
const SettingsView = lazy(() => import("./views/SettingsView"));
```

変更後：
```tsx
import DashboardView from "./views/DashboardView";
// TutorialModal は初回表示に使うため即時ロード（lazy にしない）
import TutorialModal from "./components/TutorialModal";
// それ以外のビューは初回ロードを軽くするためタブを開いた時に動的ロード（コード分割）
const IncomeView = lazy(() => import("./views/IncomeView"));
const FixedExpenseView = lazy(() => import("./views/FixedExpenseView"));
const ExpenseView = lazy(() => import("./views/ExpenseView"));
const LoanView = lazy(() => import("./views/LoanView"));
const SettingsView = lazy(() => import("./views/SettingsView"));
```

### Step 3: AppInner に showTutorial state を追加する

- [ ] `AppInner` 関数内の `useState` 群（`const [tab,setTab]=...` の行の直後）に以下を追加する

変更前（`src/App.tsx` の 45 行目付近）：
```tsx
const [tab,setTab]=useState("dash"),[selectedMonth,setSelectedMonth]=useState(today.getMonth()),[selectedYear,setSelectedYear]=useState(today.getFullYear());
```

変更後：
```tsx
const [tab,setTab]=useState("dash"),[selectedMonth,setSelectedMonth]=useState(today.getMonth()),[selectedYear,setSelectedYear]=useState(today.getFullYear());
  // チュートリアル表示フラグ：localStorage に "kk_tutorial_done"="1" がなければ初回表示する
  const [showTutorial, setShowTutorial] = useState(() => localStorage.getItem("kk_tutorial_done") !== "1");
  // チュートリアルを閉じる：localStorage にフラグを立てて表示しないようにする
  function handleCloseTutorial() {
    localStorage.setItem("kk_tutorial_done", "1");
    setShowTutorial(false);
  }
```

### Step 4: JSX に TutorialModal を追加する

- [ ] `<Toast data={toast}/>` の直後（`src/App.tsx` の 149 行目付近）に `<TutorialModal>` を追加する

変更前：
```tsx
    <Toast data={toast}/>
    <ConfirmDialog data={dlg} onOk={()=>{dlg?.onOk();setDlg(null);}} onCancel={()=>setDlg(null)}/>
```

変更後：
```tsx
    <Toast data={toast}/>
    <ConfirmDialog data={dlg} onOk={()=>{dlg?.onOk();setDlg(null);}} onCancel={()=>setDlg(null)}/>
    {/* チュートリアルモーダル：初回自動表示・設定画面からも再表示できる */}
    <TutorialModal open={showTutorial} onClose={handleCloseTutorial}/>
```

### Step 5: SettingsView の JSX に onOpenTutorial を渡す

- [ ] `tab==="set"` の SettingsView JSX（265〜275 行目付近）に `onOpenTutorial` を追加する

変更前：
```tsx
      {tab==="set"&&<SettingsView
        categoryConfig={categoryConfig}
        setCategoryConfig={setCategoryConfig}
        transactions={transactions}
        setTransactions={setTransactions}
        incomes={incomes}
        setIncomes={setIncomes}
        fixedExpenses={fixedExpenses}
        setFixedExpenses={setFixedExpenses}
        onReset={()=>{}}
      />}
```

変更後：
```tsx
      {tab==="set"&&<SettingsView
        categoryConfig={categoryConfig}
        setCategoryConfig={setCategoryConfig}
        transactions={transactions}
        setTransactions={setTransactions}
        incomes={incomes}
        setIncomes={setIncomes}
        fixedExpenses={fixedExpenses}
        setFixedExpenses={setFixedExpenses}
        onReset={()=>{}}
        onOpenTutorial={() => setShowTutorial(true)}
      />}
```

### Step 6: ビルドエラーがないことを確認する

- [ ] 以下のコマンドを実行する（TypeScript 型チェック）

```
cd /home/kenta_kamijyo/finance_web && npm run build 2>&1 | tail -20
```

期待される出力：
```
✓ built in ...
```

エラーが出た場合は TypeScript の型エラーメッセージを確認して修正する。

### Step 7: コミットする

- [ ] 以下のコマンドを実行する

```
cd /home/kenta_kamijyo && git add finance_web/src/App.tsx
git commit -m "feat: App.tsx にチュートリアル表示制御を追加"
```

---

## Task 3: SettingsView に「使い方を見る」ボタンを追加する

**Files:**
- Modify: `src/views/SettingsView.tsx`

### Step 1: SettingsView の Props 型を更新する

- [ ] `src/views/SettingsView.tsx` の `SettingsViewProps` interface に `onOpenTutorial` を追加する

変更前（18〜29 行目付近）：
```tsx
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
```

変更後：
```tsx
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
  onOpenTutorial: () => void;  // チュートリアルモーダルを開く関数
}
```

### Step 2: 「使い方を見る」カードを追加する

- [ ] `src/views/SettingsView.tsx` のアプリ情報カード（300 行目付近）の直前に「使い方を見る」カードを挿入する

変更前（アプリ情報カードの直前）：
```tsx
      {/* ────────── アプリ情報カード（バージョン・制作者・著作権） ────────── */}
      <div style={{ ...STYLE_CARD, marginTop: 16 }}>
```

変更後：
```tsx
      {/* ────────── 使い方を見るボタン ────────── */}
      <div style={{ ...STYLE_CARD, marginTop: 16 }}>
        <button
          onClick={props.onOpenTutorial}
          style={{ ...STYLE_BUTTON_OUTLINE, width: "100%" }}
        >
          📖 使い方を見る
        </button>
      </div>

      {/* ────────── アプリ情報カード（バージョン・制作者・著作権） ────────── */}
      <div style={{ ...STYLE_CARD, marginTop: 16 }}>
```

### Step 3: ビルドエラーがないことを確認する

- [ ] 以下のコマンドを実行する

```
cd /home/kenta_kamijyo/finance_web && npm run build 2>&1 | tail -20
```

期待される出力：
```
✓ built in ...
```

### Step 4: 全テストが通ることを確認する

- [ ] 以下のコマンドを実行する

```
cd /home/kenta_kamijyo/finance_web && npm test 2>&1 | tail -20
```

期待される出力：
```
Test Files  X passed
Tests  XX passed
```

失敗があれば内容を確認して修正する。

### Step 5: コミットする

- [ ] 以下のコマンドを実行する

```
cd /home/kenta_kamijyo && git add finance_web/src/views/SettingsView.tsx
git commit -m "feat: SettingsView に「使い方を見る」ボタンを追加"
```

---

## Task 4: 動作確認 & 本番デプロイ

**Files:**（変更なし・確認のみ）

### Step 1: ローカルで動作確認する

- [ ] 以下のコマンドでローカルサーバーを起動する

```
cd /home/kenta_kamijyo/finance_web && npm run dev
```

ブラウザで `http://localhost:5173` を開き、以下を確認する：
1. 初回アクセス → チュートリアルモーダルが自動表示される
2. 「次へ」×5 → 「はじめる」に変わる
3. 「はじめる」クリック → モーダルが閉じる
4. 再読み込み → モーダルが表示されない
5. ⚙️設定タブ → 「📖 使い方を見る」ボタンがある
6. ボタンクリック → モーダルが page 0 から再表示される
7. ✕ボタンで閉じられる

確認が取れたら Ctrl+C でサーバーを止める。

### Step 2: 本番デプロイする

- [ ] 以下のコマンドを実行する

```
cd /home/kenta_kamijyo/finance_web && npx vercel --prod
```

期待される出力：
```
✅  Production: https://financeweb-nine.vercel.app [XX s]
```

### Step 3: 本番で動作確認する

- [ ] `https://financeweb-nine.vercel.app` を開いて以下を確認する：
  - チュートリアルが表示される（初回アクセス時 or 別ブラウザで確認）
  - 設定タブの「使い方を見る」ボタンが機能する

### Step 4: git push する

- [ ] 以下のコマンドを実行する

```
cd /home/kenta_kamijyo && git push origin main
```

---

## チェックリスト（完了条件）

- [ ] `npm test` が全テスト PASS
- [ ] `npm run build` がエラーなし
- [ ] 初回アクセスでチュートリアルが自動表示される
- [ ] `kk_tutorial_done="1"` セット後に再読み込みしてもモーダルが出ない
- [ ] 設定タブの「使い方を見る」でいつでも再表示できる
- [ ] 本番（vercel.app）で正常動作することを確認した
