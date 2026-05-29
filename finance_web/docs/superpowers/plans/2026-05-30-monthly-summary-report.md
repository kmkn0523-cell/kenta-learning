# 月次サマリーレポート機能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** finance_web に「サマリー」タブを新設し、選択月の収入・支出・貯蓄率・カテゴリ内訳と前月比を1画面に表示して PNG / CSV で書き出せるようにする。

**Architecture:** 案A（専用ビュー＋App.tsxで集計）。集計値は `App.tsx` で計算し、表示専用の `SummaryView` に props で渡す。稼働中の `DashboardView` には手を入れない。画像化は `html2canvas`、CSV は既存の `downloadFile` を再利用する。

**Tech Stack:** React 18 + TypeScript + Vite、vitest（純粋関数テスト）、html2canvas（新規・DOM→PNG）。

設計書: `docs/superpowers/specs/2026-05-30-monthly-summary-report-design.md`

---

## ファイル構成

| ファイル | 区分 | 責務 |
|---|---|---|
| `src/types.ts` | 変更 | `SummaryStats` 型を追記 |
| `src/utils/summaryExport.ts` | 新規 | 集計純粋関数（`computeSavingRate` / `buildSummaryCsv`）＋書き出し（`exportSummaryCsv` / `exportSummaryImage`） |
| `src/utils/summaryExport.test.ts` | 新規 | 上記純粋関数の vitest テスト |
| `src/views/SummaryView.tsx` | 新規 | サマリー表示と書き出しボタン（表示専用） |
| `src/App.tsx` | 変更 | 前月集計・カテゴリ内訳を算出し `SummaryView` を lazy レンダー＋タブ追加 |

---

### Task 1: `SummaryStats` 型を追加

**Files:**
- Modify: `src/types.ts`（末尾 132行目 `}` の後ろに追記）

- [ ] **Step 1: 型を追記**

`src/types.ts` の末尾（`DlgData` の閉じ括弧の後）に以下を追記する。

```ts
// 月次サマリー1画面分の集計値の形
export interface SummaryStats {
  income: number;     // 収入合計（円）
  expense: number;    // 支出合計（変動＋固定＋ローン返済。ダッシュボードの totalBurden と同じ定義）
  net: number;        // 手残り（収入合計 − 支出合計）
  savingRate: number; // 貯蓄率（%。小数第1位まで）
}
```

- [ ] **Step 2: 型チェック**

Run: `cd finance_web && npx tsc --noEmit`
Expected: エラーなし（exit 0）

- [ ] **Step 3: Commit**

```bash
cd finance_web && git add src/types.ts && git commit -m "feat: add SummaryStats type for monthly summary"
```

---

### Task 2: `computeSavingRate` 純粋関数（TDD）

貯蓄率 = 手残り(net) ÷ 収入合計 × 100。収入0は0%。小数第1位まで。

**Files:**
- Create: `src/utils/summaryExport.test.ts`
- Create: `src/utils/summaryExport.ts`

- [ ] **Step 1: 失敗するテストを書く**

`src/utils/summaryExport.test.ts` を新規作成する。

```ts
// ──────── 月次サマリー書き出しユーティリティのテスト ────────
import { describe, it, expect } from "vitest";
import { computeSavingRate } from "./summaryExport";

describe("computeSavingRate", () => {
  it("収入30万・手残り6万なら貯蓄率20%", () => {
    expect(computeSavingRate(60000, 300000)).toBe(20);
  });

  it("小数は第1位に丸める（33.33→33.3）", () => {
    // 手残り100000 / 収入300000 = 0.3333... → 33.3
    expect(computeSavingRate(100000, 300000)).toBe(33.3);
  });

  it("収入0のときは0%（ゼロ除算しない）", () => {
    expect(computeSavingRate(0, 0)).toBe(0);
  });

  it("手残りがマイナスでも計算する", () => {
    // 手残り-30000 / 収入300000 = -0.1 → -10
    expect(computeSavingRate(-30000, 300000)).toBe(-10);
  });
});
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `cd finance_web && npx vitest run src/utils/summaryExport.test.ts`
Expected: FAIL（`computeSavingRate` が存在しない／import 解決できない）

- [ ] **Step 3: 最小実装を書く**

`src/utils/summaryExport.ts` を新規作成する。

```ts
// ──────── 月次サマリー書き出しユーティリティ ────────
// 集計の純粋関数と、CSV / PNG の書き出し処理をまとめる

// 貯蓄率を計算する（手残り ÷ 収入合計 × 100、小数第1位まで）
// 収入合計が0以下のときは0を返してゼロ除算を防ぐ
export function computeSavingRate(net: number, income: number): number {
  if (income <= 0) return 0;
  // 100倍した値をさらに10倍して四捨五入し、10で割ることで小数第1位に丸める
  return Math.round((net / income) * 100 * 10) / 10;
}
```

- [ ] **Step 4: テストが通ることを確認**

Run: `cd finance_web && npx vitest run src/utils/summaryExport.test.ts`
Expected: PASS（4件）

- [ ] **Step 5: Commit**

```bash
cd finance_web && git add src/utils/summaryExport.ts src/utils/summaryExport.test.ts && git commit -m "feat: add computeSavingRate pure function with tests"
```

---

### Task 3: `buildSummaryCsv` 純粋関数（TDD）

縦持ちCSVを返す。前月が `null` なら2列（`項目,金額`）、前月ありなら3列（`項目,当月,前月`）。基本指標の後に空行を挟んでカテゴリ内訳（`カテゴリ,金額`）を並べる。末尾は改行で終わる。

**Files:**
- Modify: `src/utils/summaryExport.test.ts`
- Modify: `src/utils/summaryExport.ts`

- [ ] **Step 1: 失敗するテストを追記**

`src/utils/summaryExport.test.ts` の先頭 import に `buildSummaryCsv` を追加する。

```ts
import { computeSavingRate, buildSummaryCsv } from "./summaryExport";
```

同ファイル末尾に以下の `describe` を追記する。

```ts
import type { SummaryStats } from "../types";

describe("buildSummaryCsv", () => {
  const current: SummaryStats = { income: 300000, expense: 240000, net: 60000, savingRate: 20 };

  it("前月がnullなら2列ヘッダーで基本指標とカテゴリを並べる", () => {
    const csv = buildSummaryCsv(
      "2026年5月",
      current,
      null,
      [{ category: "食費", amount: 50000 }, { category: "交通費", amount: 12000 }],
    );
    const expected =
      "項目,金額\n" +
      "収入合計,300000\n" +
      "支出合計,240000\n" +
      "手残り,60000\n" +
      "貯蓄率,20%\n" +
      "\n" +
      "カテゴリ,金額\n" +
      "食費,50000\n" +
      "交通費,12000\n";
    expect(csv).toBe(expected);
  });

  it("前月ありなら3列ヘッダーで当月・前月を並べる", () => {
    const previous: SummaryStats = { income: 280000, expense: 250000, net: 30000, savingRate: 10.7 };
    const csv = buildSummaryCsv("2026年5月", current, previous, []);
    const expected =
      "項目,当月,前月\n" +
      "収入合計,300000,280000\n" +
      "支出合計,240000,250000\n" +
      "手残り,60000,30000\n" +
      "貯蓄率,20%,10.7%\n";
    expect(csv).toBe(expected);
  });

  it("カンマを含むカテゴリ名はダブルクォートで囲む", () => {
    const csv = buildSummaryCsv(
      "2026年5月",
      current,
      null,
      [{ category: "外食,カフェ", amount: 8000 }],
    );
    expect(csv).toContain('"外食,カフェ",8000\n');
  });
});
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `cd finance_web && npx vitest run src/utils/summaryExport.test.ts`
Expected: FAIL（`buildSummaryCsv` が存在しない）

- [ ] **Step 3: 最小実装を追記**

`src/utils/summaryExport.ts` の先頭に型 import を追加する。

```ts
import type { SummaryStats } from "../types";
```

同ファイルの `computeSavingRate` の下に以下を追記する。

```ts
// CSVの1セルを安全な文字列にする（カンマ・改行・ダブルクォートを含む場合は囲む）
// RFC4180準拠：セル内のダブルクォートは2個重ねでエスケープする
function csvCell(value: string): string {
  if (/[",\n]/.test(value)) {
    return '"' + value.replace(/"/g, '""') + '"';
  }
  return value;
}

// 月次サマリーを縦持ちCSV文字列にする（純粋関数）
// previous が null なら2列、あれば3列で前月値も並べる。末尾は改行で終わる
export function buildSummaryCsv(
  monthLabel: string,
  current: SummaryStats,
  previous: SummaryStats | null,
  categoryBreakdown: { category: string; amount: number }[],
): string {
  void monthLabel; // ファイル名生成側で使う。CSV本文では今は未使用だが引数として保持する
  const lines: string[] = [];

  if (previous) {
    // 3列ヘッダー（当月・前月）
    lines.push("項目,当月,前月");
    lines.push(`収入合計,${current.income},${previous.income}`);
    lines.push(`支出合計,${current.expense},${previous.expense}`);
    lines.push(`手残り,${current.net},${previous.net}`);
    lines.push(`貯蓄率,${current.savingRate}%,${previous.savingRate}%`);
  } else {
    // 2列ヘッダー（当月のみ）
    lines.push("項目,金額");
    lines.push(`収入合計,${current.income}`);
    lines.push(`支出合計,${current.expense}`);
    lines.push(`手残り,${current.net}`);
    lines.push(`貯蓄率,${current.savingRate}%`);
  }

  // カテゴリ内訳がある場合は空行を挟んで別ブロックとして並べる
  if (categoryBreakdown.length > 0) {
    lines.push(""); // 空行で区切る
    lines.push("カテゴリ,金額");
    for (const row of categoryBreakdown) {
      lines.push(`${csvCell(row.category)},${row.amount}`);
    }
  }

  // 各行を改行でつなぎ、末尾にも改行を付ける
  return lines.join("\n") + "\n";
}
```

- [ ] **Step 4: テストが通ることを確認**

Run: `cd finance_web && npx vitest run src/utils/summaryExport.test.ts`
Expected: PASS（computeSavingRate 4件＋buildSummaryCsv 3件）

- [ ] **Step 5: Commit**

```bash
cd finance_web && git add src/utils/summaryExport.ts src/utils/summaryExport.test.ts && git commit -m "feat: add buildSummaryCsv pure function with tests"
```

---

### Task 4: html2canvas をインストール（要ユーザー承認）

**Files:** `package.json` / `package-lock.json`（npm が更新）

- [ ] **Step 1: ユーザー承認を得る**

CLAUDE.md「新しいライブラリのインストールは事前確認」に従い、実行前にユーザーへ確認する。承認が出るまで次に進まない。

- [ ] **Step 2: インストール**

Run: `cd finance_web && npm install html2canvas`
Expected: 追加され `package-lock.json` が更新される（exit 0）

- [ ] **Step 3: 解決確認**

Run: `cd finance_web && node -e "require.resolve('html2canvas'); console.log('ok')"`
Expected: `ok`（html2canvas は型定義を同梱するため `@types` は不要）

- [ ] **Step 4: Commit**

```bash
cd finance_web && git add package.json package-lock.json && git commit -m "chore: add html2canvas for summary image export"
```

---

### Task 5: 書き出し関数 `exportSummaryCsv` / `exportSummaryImage` を追加

CSV は既存 `downloadFile` を再利用。画像は `html2canvas` → `canvas.toBlob` → URL 経由でダウンロード。

**Files:**
- Modify: `src/utils/summaryExport.ts`

- [ ] **Step 1: import を追記**

`src/utils/summaryExport.ts` の import 群に以下を追加する。

```ts
import html2canvas from "html2canvas";
import { downloadFile } from "./dataExport";
```

- [ ] **Step 2: 書き出し関数を追記**

`src/utils/summaryExport.ts` の末尾に以下を追記する。

```ts
// 月次サマリーをCSVファイルとして保存する（ファイル名例: サマリー_2026年5月.csv）
export function exportSummaryCsv(
  monthLabel: string,
  current: SummaryStats,
  previous: SummaryStats | null,
  categoryBreakdown: { category: string; amount: number }[],
): void {
  const csv = buildSummaryCsv(monthLabel, current, previous, categoryBreakdown);
  downloadFile(`サマリー_${monthLabel}.csv`, csv, "text/csv;charset=utf-8");
}

// 指定したDOM要素をPNG画像にして保存する（ファイル名例: サマリー_2026年5月.png）
// html2canvas でDOMを描画 → Blob化 → 一時URLを作ってダウンロードリンクをクリックする
export async function exportSummaryImage(node: HTMLElement, fileName: string): Promise<void> {
  // 背景色をアプリの暗い背景に合わせ、scale:2 で高解像度にする
  const canvas = await html2canvas(node, { backgroundColor: "#0a0a0c", scale: 2 });

  // canvas を Blob（画像データのかたまり）に変換する。toBlob はコールバック式なので Promise で包む
  const blob = await new Promise<Blob | null>((resolve) => {
    canvas.toBlob((b) => resolve(b), "image/png");
  });
  if (!blob) {
    throw new Error("画像の生成に失敗しました");
  }

  // Blob から一時URLを作り、見えないリンクを作ってクリックしてダウンロードさせる
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  // 使い終わった一時URLは解放してメモリリークを防ぐ
  URL.revokeObjectURL(url);
}
```

- [ ] **Step 3: 型チェック＋既存テスト維持**

Run: `cd finance_web && npx tsc --noEmit && npx vitest run src/utils/summaryExport.test.ts`
Expected: 型エラーなし、テストPASS（7件）

- [ ] **Step 4: Commit**

```bash
cd finance_web && git add src/utils/summaryExport.ts && git commit -m "feat: add CSV/PNG export functions for monthly summary"
```

---

### Task 6: `SummaryView.tsx` を作成

表示専用。`useRef` で画像化対象のDOMを掴み、前月比は `DiffBadge` で表示する。

**Files:**
- Create: `src/views/SummaryView.tsx`

- [ ] **Step 1: 既存のスタイル定数・format 関数を確認**

Run: `cd finance_web && grep -n "export const STYLE_\|export const COLOR_" src/utils/styles.ts && grep -n "export function formatYen\|export const MONTH_LABELS" src/utils/format.ts`
Expected: 実在する定数名・関数名を把握する。`STYLE_BUTTON_PRIMARY` が無ければボタンは下記コード内のインラインスタイルをそのまま使う（このTaskのコードはTutorialModal同様 `STYLE_BUTTON_PRIMARY` を import するが、grep で存在しない場合は import 行を削除しインラインの `background:"#818cf8"` 等で代替する）。`formatYen` が無ければ `toLocaleString()` で代替する。

- [ ] **Step 2: コンポーネントを作成**

`src/views/SummaryView.tsx` を新規作成する。

```tsx
// ────────── 月次サマリービュー ──────────
// 選択月の収入・支出・貯蓄率・カテゴリ内訳と前月比を1画面に表示し、
// PNG画像 / CSV で書き出せるようにする。集計はしない（App.tsxから props で受け取る表示専用）
import { useRef, CSSProperties } from "react";
import { SummaryStats } from "../types";
import { formatYen } from "../utils/format";
import { exportSummaryCsv, exportSummaryImage } from "../utils/summaryExport";

// ── スタイル定数 ──────────────────────────────────────────

// レポート全体を囲むカード（この範囲を画像化する）
const STYLE_REPORT_CARD: CSSProperties = {
  background: "rgba(15,23,42,0.98)",
  border: "1px solid rgba(148,163,184,0.16)",
  borderRadius: 22,
  padding: "24px 20px",
  marginBottom: 16,
};

// 指標1行（ラベル左・金額右）
const STYLE_STAT_ROW: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "baseline",
  padding: "10px 0",
  borderBottom: "1px solid rgba(148,163,184,0.12)",
};

// ボタン共通
const STYLE_ACTION_BUTTON: CSSProperties = {
  flex: 1,
  padding: "12px 0",
  borderRadius: 12,
  border: "none",
  fontSize: 14,
  fontWeight: 700,
  cursor: "pointer",
  fontFamily: "inherit",
  color: "#0a0a0c",
};

// ─────────────────────────────────────────────────────────

// 前月比バッジ：差を ↑+5,000円（緑）/ ↓-2,000円（赤）/ ±0（グレー）で表す
// pt=true のときは「円」ではなく「pt」を単位にする（貯蓄率用）
function DiffBadge({ diff, pt }: { diff: number; pt?: boolean }) {
  // 差が0なら ±0 をグレーで表示
  if (diff === 0) {
    return <span style={{ fontSize: 12, color: "#9a9aa3" }}>±0</span>;
  }
  const isUp = diff > 0;                                  // プラスかどうか
  const arrow = isUp ? "↑" : "↓";                          // 上下の矢印
  const color = isUp ? "#34d399" : "#f87171";             // 緑 or 赤
  const sign = isUp ? "+" : "−";                           // 符号（マイナスは全角ダッシュで見やすく）
  const absValue = Math.abs(diff);                         // 絶対値
  // pt なら小数第1位付きの数値、円なら3桁区切り
  const body = pt ? `${absValue.toFixed(1)}pt` : `${absValue.toLocaleString()}円`;
  return (
    <span style={{ fontSize: 12, color, fontWeight: 700 }}>
      {arrow}{sign}{body}
    </span>
  );
}

// このコンポーネントが受け取る props の型
interface SummaryViewProps {
  monthLabel: string;                                            // 例 "2026年5月"
  current: SummaryStats;                                          // 当月の集計値
  previous: SummaryStats | null;                                  // 前月の集計値（なければ null）
  categoryBreakdown: { category: string; amount: number }[];      // カテゴリ内訳（降順）
  showT: (msg: string, type?: string) => void;                    // トースト表示
}

export default function SummaryView({
  monthLabel,
  current,
  previous,
  categoryBreakdown,
  showT,
}: SummaryViewProps) {
  // 画像化する対象のDOMを掴むための参照
  const reportRef = useRef<HTMLDivElement>(null);

  // 「画像で保存」ボタン：レポートカードをPNG化する
  async function handleSaveImage() {
    if (!reportRef.current) return;
    try {
      await exportSummaryImage(reportRef.current, `サマリー_${monthLabel}.png`);
      showT("画像を保存しました");
    } catch {
      // html2canvas が失敗した場合はエラートーストを出す
      showT("画像の保存に失敗しました", "error");
    }
  }

  // 「CSVで保存」ボタン：集計値を縦持ちCSVにして保存する
  function handleSaveCsv() {
    exportSummaryCsv(monthLabel, current, previous, categoryBreakdown);
    showT("CSVを保存しました");
  }

  return (
    <div>
      {/* ここから下（reportRef）が画像化される範囲 */}
      <div ref={reportRef} style={STYLE_REPORT_CARD}>
        {/* 見出し（対象月） */}
        <div style={{ fontSize: 18, fontWeight: 700, color: "#f5f5f7", marginBottom: 16 }}>
          {monthLabel} のサマリー
        </div>

        {/* 基本指標 */}
        <div style={STYLE_STAT_ROW}>
          <span style={{ fontSize: 14, color: "#9a9aa3" }}>収入合計</span>
          <span style={{ textAlign: "right" }}>
            <span style={{ fontSize: 16, fontWeight: 700, color: "#f5f5f7" }}>{formatYen(current.income)}</span>
            {previous && <span style={{ marginLeft: 8 }}><DiffBadge diff={current.income - previous.income} /></span>}
          </span>
        </div>

        <div style={STYLE_STAT_ROW}>
          <span style={{ fontSize: 14, color: "#9a9aa3" }}>支出合計</span>
          <span style={{ textAlign: "right" }}>
            <span style={{ fontSize: 16, fontWeight: 700, color: "#f5f5f7" }}>{formatYen(current.expense)}</span>
            {previous && <span style={{ marginLeft: 8 }}><DiffBadge diff={current.expense - previous.expense} /></span>}
          </span>
        </div>

        <div style={STYLE_STAT_ROW}>
          <span style={{ fontSize: 14, color: "#9a9aa3" }}>手残り</span>
          <span style={{ fontSize: 16, fontWeight: 700, color: current.net >= 0 ? "#34d399" : "#f87171" }}>
            {formatYen(current.net)}
          </span>
        </div>

        <div style={{ ...STYLE_STAT_ROW, borderBottom: "none" }}>
          <span style={{ fontSize: 14, color: "#9a9aa3" }}>貯蓄率</span>
          <span style={{ textAlign: "right" }}>
            <span style={{ fontSize: 16, fontWeight: 700, color: "#f5f5f7" }}>{current.savingRate}%</span>
            {previous && <span style={{ marginLeft: 8 }}><DiffBadge diff={Math.round((current.savingRate - previous.savingRate) * 10) / 10} pt /></span>}
          </span>
        </div>

        {/* カテゴリ内訳 */}
        <div style={{ fontSize: 14, fontWeight: 700, color: "#f5f5f7", margin: "20px 0 8px" }}>
          カテゴリ内訳
        </div>
        {categoryBreakdown.length === 0 ? (
          <div style={{ fontSize: 13, color: "#9a9aa3", padding: "8px 0" }}>支出がありません</div>
        ) : (
          categoryBreakdown.map((row) => (
            <div key={row.category} style={STYLE_STAT_ROW}>
              <span style={{ fontSize: 14, color: "#9a9aa3" }}>{row.category}</span>
              <span style={{ fontSize: 15, fontWeight: 600, color: "#f5f5f7" }}>{formatYen(row.amount)}</span>
            </div>
          ))
        )}
      </div>

      {/* 書き出しボタン（画像化範囲の外に置く） */}
      <div style={{ display: "flex", gap: 12 }}>
        <button type="button" onClick={handleSaveImage} style={{ ...STYLE_ACTION_BUTTON, background: "#818cf8" }}>
          画像で保存
        </button>
        <button type="button" onClick={handleSaveCsv} style={{ ...STYLE_ACTION_BUTTON, background: "#34d399" }}>
          CSVで保存
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 型チェック**

Run: `cd finance_web && npx tsc --noEmit`
Expected: 型エラーなし（`formatYen` の有無は Step 1 で確認済み。無い場合は `toLocaleString()` ベースに置換済みのこと）

- [ ] **Step 4: Commit**

```bash
cd finance_web && git add src/views/SummaryView.tsx && git commit -m "feat: add SummaryView component"
```

---

### Task 7: App.tsx に統合（タブ追加・集計受け渡し）

前月集計を `useMonthlyData` の前月引数呼び出しで作り、カテゴリ内訳を変換して `SummaryView` に渡す。

**Files:**
- Modify: `src/App.tsx`（lazy import 群 `:81-85` / `useMonthlyData` 周辺 `:144-161` / レンダー `:339-468` / タブ配列 `:471`）

- [ ] **Step 1: 統合前に現状を再確認**

Run: `cd finance_web && grep -n "lazy(() => import\|useMonthlyData\|const prevMs\|const expByCat\|tab===\"set\"\|\\[\"dash\"" src/App.tsx`
Expected: lazy import 群・`useMonthlyData` 呼び出し・`prevMs` / `expByCat` 定義・`tab==="set"` レンダー・タブ配列の正確な行番号を把握する。以降の編集はこの結果に合わせて適用する。

- [ ] **Step 2: lazy import と純粋関数 import を追加**

既存の lazy import 群（`SettingsView` の隣）に追加する。

```tsx
const SummaryView = lazy(() => import("./views/SummaryView"));
```

ファイル冒頭の import 群（既存の utils import の近く）に追加する。

```tsx
import { computeSavingRate } from "./utils/summaryExport";
```

- [ ] **Step 3: 前月集計・当月集計・カテゴリ内訳を算出**

`useMonthlyData` 当月呼び出しと `prevMs` 定義の後ろに以下を追加する。`useMonthlyData` を前月の年・月で再度呼び、支出定義を当月とそろえる。

```tsx
// 前月の「年」と「月インデックス(0-11)」を prevMs（"YYYY-MM"）から取り出す
const prevYearNum = Number(prevMs.slice(0, 4));        // 例 "2026-04" → 2026
const prevMonthIdx = Number(prevMs.slice(5, 7)) - 1;   // 例 "2026-04" → 3（4月＝index3）

// 前月の集計を当月と同じ useMonthlyData で取得する（支出定義をそろえるため）
const prevData = useMonthlyData(prevYearNum, prevMonthIdx);

// 当月のサマリー集計値（既存の totalIncome / totalBurden / net を SummaryStats に詰める）
const currentSummary = useMemo<SummaryStats>(() => ({
  income: totalIncome,
  expense: totalBurden,
  net: net,
  savingRate: computeSavingRate(net, totalIncome),
}), [totalIncome, totalBurden, net]);

// 前月のサマリー集計値。収入も支出も0なら「前月データなし」とみなして null にする
const previousSummary = useMemo<SummaryStats | null>(() => {
  if (prevData.totalIncome === 0 && prevData.totalBurden === 0) return null;
  return {
    income: prevData.totalIncome,
    expense: prevData.totalBurden,
    net: prevData.net,
    savingRate: computeSavingRate(prevData.net, prevData.totalIncome),
  };
}, [prevData.totalIncome, prevData.totalBurden, prevData.net]);

// カテゴリ内訳（既存の expByCat: [カテゴリ名, 金額][] を {category, amount} の配列に変換）
const categoryBreakdown = useMemo(
  () => expByCat.map(([category, amount]) => ({ category, amount })),
  [expByCat],
);

// 対象月のラベル（例 "2026年5月"）
const summaryMonthLabel = `${selectedYear}年${selectedMonth + 1}月`;
```

> 注意: `SummaryStats` と `useMemo` が未 import の場合は import 行に追加する（`import { SummaryStats } from "./types";` / React の `useMemo`）。Step 1 の grep 結果と既存 import を照合し、既にあれば重複させない。

- [ ] **Step 4: レンダー分岐を追加**

`{tab==="set"&&<SettingsView ... />}` の並びに以下を追加する（Suspense の内側）。

```tsx
{tab === "sum" && (
  <SummaryView
    monthLabel={summaryMonthLabel}
    current={currentSummary}
    previous={previousSummary}
    categoryBreakdown={categoryBreakdown}
    showT={showT}
  />
)}
```

> `showT` の正確な変数名は Step 1 周辺で確認する。トースト表示関数が別名（例 `showToast`）ならそれに合わせる。

- [ ] **Step 5: タブバーに項目を追加**

タブ定義配列（`:471` 付近）に要素を1つ追加する。ダッシュボードが 📊 なので区別のため 🧾 を使う。

```tsx
["sum", "🧾", "サマリー"],
```

挿入位置は `["dash","📊","概要"]` の直後を推奨（概要の隣にサマリー）。

- [ ] **Step 6: 型チェック＋ビルド確認**

Run: `cd finance_web && npx tsc --noEmit && npm run build`
Expected: 型エラーなし、ビルド成功

- [ ] **Step 7: 動作確認（手動）**

Run: `cd finance_web && npm run dev`
ブラウザで「サマリー」タブを開き、(1) 当月の収入・支出・手残り・貯蓄率・カテゴリ内訳が表示される (2) 前月データがあれば前月比バッジが出る (3)「画像で保存」でPNG、「CSVで保存」でCSVがダウンロードされることを確認する。

- [ ] **Step 8: Commit**

```bash
cd finance_web && git add src/App.tsx && git commit -m "feat: integrate SummaryView as summary tab in App"
```

---

### Task 8: 本番デプロイ（任意・要ユーザー確認）

- [ ] **Step 1: デプロイ可否をユーザーに確認**

finance_web は GitHub 経由ではなく `vercel --prod` で直接デプロイする。実行前にユーザーへ確認する。

- [ ] **Step 2: デプロイ**

Run: `cd finance_web && npx vercel --prod`
Expected: デプロイ完了、本番URLが表示される

---

## Self-Review

**1. Spec coverage（設計書の各要件 → 対応タスク）**

| 設計書の要件 | 対応 |
|---|---|
| 収入合計 | Task 1（型）/ Task 7（`totalIncome`）/ Task 6（表示） |
| 支出合計（`totalBurden` 定義） | Task 7（`totalBurden`）/ Task 6 |
| 手残り（net） | Task 7（`net`）/ Task 6 |
| 貯蓄率（収入0は0%・小数第1位） | Task 2（`computeSavingRate`）|
| カテゴリ内訳（降順） | Task 7（`expByCat` 変換）/ Task 6（リスト表示・空時「支出がありません」） |
| 前月比（収入/支出/貯蓄率、↑+円/↓-円/±0、貯蓄率はpt） | Task 6（`DiffBadge`）/ Task 7（前月集計・null判定） |
| PNG書き出し | Task 4（html2canvas）/ Task 5（`exportSummaryImage`）/ Task 6（ボタン・try/catch） |
| CSV書き出し | Task 3（`buildSummaryCsv`）/ Task 5（`exportSummaryCsv`）/ Task 6（ボタン） |
| 新タブ「サマリー」 | Task 7（タブ配列・レンダー分岐） |
| DashboardView 非改変 | 全タスクで DashboardView を触らない |
| ゼロ除算回避 | Task 2 |
| 前月データなしは前月比非表示 | Task 7（`previousSummary` を null）/ Task 6（`previous &&`） |
| html2canvas失敗時トースト | Task 6（catch で `"画像の保存に失敗しました"`） |
| テスト（buildSummaryCsv・ゼロ除算） | Task 2 / Task 3 |
| 既存資産再利用（formatYen / downloadFile / styles） | Task 5（downloadFile）/ Task 6（formatYen・styles） |

含めないもの（円グラフ・上位支出3件・予算達成状況）はどのタスクにも入れていない（YAGNI遵守）。

**2. Placeholder scan**

「TBD」「適切に」「など」等の曖昧表現なし。コードを変える全ステップに実コードを記載。`formatYen` / `STYLE_BUTTON_PRIMARY` / `showT` の名前ゆれは Task 6 Step 1・Task 7 Step 1 の grep で実在確認し、無ければ代替する手順を明記済み。

**3. Type consistency**

- `SummaryStats { income, expense, net, savingRate }`：Task 1 定義 → Task 2/3/5/6/7 で同一フィールド名で使用。
- `computeSavingRate(net, income)`：Task 2 定義（第1引数 net・第2引数 income） → Task 7 で `computeSavingRate(net, totalIncome)` / `computeSavingRate(prevData.net, prevData.totalIncome)` と同順で呼び出し。
- `buildSummaryCsv(monthLabel, current, previous, categoryBreakdown)`：Task 3 定義 → Task 5 `exportSummaryCsv` から同順で呼び出し。
- `categoryBreakdown: { category: string; amount: number }[]`：Task 3/5/6 の型と Task 7 の変換（`{ category, amount }`）が一致。
- `exportSummaryImage(node, fileName)`：Task 5 定義 → Task 6 `handleSaveImage` から `(reportRef.current, ファイル名)` で呼び出し。
- `SummaryView` props（monthLabel/current/previous/categoryBreakdown/showT）：Task 6 定義 → Task 7 レンダーで全て同名で渡す。
