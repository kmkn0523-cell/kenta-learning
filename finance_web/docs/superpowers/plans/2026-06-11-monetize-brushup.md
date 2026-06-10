# finance_web 収益ファースト・ブラッシュアップ (v1.6.0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 壊れたアフィリエイトリンクを修正し、診断連動の広告配置・シェア導線・PNG透かしを追加して「SNSで紹介投稿を出せる状態」にする。

**Architecture:** 広告データと選定ロジックを `src/utils/affiliates.ts` に一元化し、バナーUIを `src/components/AffiliateBanner.tsx` として独立させる。表示箇所（ローンタブ・家計診断・月次レポート）はこの2ファイルを参照するだけにする。シェア機能は自己完結コンポーネント `ShareCard`、透かしは `summaryExport.ts` 内の純関数 `appendWatermark` として追加する。

**Tech Stack:** Vite + React 18 + TypeScript + vitest + @testing-library/react（すべて導入済み・新規ライブラリなし）

**前提:**
- 作業ディレクトリ: `/home/kenta_kamijyo/finance_web`
- テスト実行: `npx vitest run`（既存126件が全パスの状態から開始）
- デプロイは `npx vercel --prod`（**ユーザー承認後のみ**・GitHub経由ではない）
- コミットは リポジトリルート `/home/kenta_kamijyo` で行う（finance_web はモノレポの1ディレクトリ）
- 各コミット末尾に `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` を付ける

**設計書:** `finance_web/docs/superpowers/specs/2026-06-11-monetize-brushup-design.md`

---

## File Structure

**Create:**
| ファイル | 責務 |
|---|---|
| `src/utils/affiliates.ts` | 広告データ（承認済み4件）・型・選定ロジック `selectAffiliateOffer` の一元管理 |
| `src/components/AffiliateBanner.tsx` | バナー1枚のUI＋ローンタブ用 `AffiliateSection`（LoanViewから移設） |
| `src/components/ShareCard.tsx` | 「友達に教える」カード（Web Share API＋クリップボードフォールバック） |
| `src/test/utils/affiliates.test.ts` | 選定ロジックのテスト |
| `src/test/components/AffiliateBanner.test.tsx` | バナーのテスト |
| `src/test/components/HealthCheckCard.test.tsx` | 診断カード内の提案枠テスト |
| `src/test/components/MonthlyReportModal.test.tsx` | レポートモーダル内の提案枠テスト |
| `src/test/components/ShareCard.test.tsx` | シェアカードのテスト |
| `docs/sns_launch_posts.md` | SNS紹介投稿文の下書き（finance_web/docs/ 配下） |

**Modify:**
| ファイル | 変更内容 |
|---|---|
| `src/views/LoanView.tsx` | `AFFILIATE` 定数・`AffiliateBanner`・`AffiliateSection` を削除し新コンポーネントを使用 |
| `src/components/HealthCheckCard.tsx` | 最下部に「あなたへの提案」枠 |
| `src/components/MonthlyReportModal.tsx` | 最下部に提案枠＋ `hasAccounts` prop 追加 |
| `src/App.tsx` | `MonthlyReportModal` に `hasAccounts` を渡す |
| `src/views/SettingsView.tsx` | `ShareCard` 追加・バージョン表記を `__APP_VERSION__` に・アプリ名を BYB に |
| `src/components/PasswordGate.tsx` | フッターのバージョンを `__APP_VERSION__` に |
| `src/utils/summaryExport.ts` | PNG書き出しに透かし帯を追加 |
| `src/utils/summaryExport.test.ts` | 透かしのフォールバックテスト追加（既存ファイルに追記・utils直下にある既存テスト） |
| `vite.config.js` | `define` で `__APP_VERSION__` を注入 |
| `src/vite-env.d.ts` | `__APP_VERSION__` の型宣言 |
| `package.json` | `version` を `1.6.0` に |

---

### Task 1: 広告データと選定ロジック（`affiliates.ts`）

**Files:**
- Create: `src/utils/affiliates.ts`
- Test: `src/test/utils/affiliates.test.ts`

- [ ] **Step 1: Write the failing test**

`src/test/utils/affiliates.test.ts` を新規作成:

```typescript
// ────────── affiliates.ts（広告データ・選定ロジック）のテスト ──────────
import {
  APPROVED_OFFERS,
  OFFERS_BY_LOAN_TAB,
  getOfferById,
  selectAffiliateOffer,
} from "../../utils/affiliates";

describe("APPROVED_OFFERS（承認済み広告データ）", () => {
  it("承認済みは4件だけ（審査待ちプレースホルダーを含まない）", () => {
    expect(APPROVED_OFFERS).toHaveLength(4);
  });

  it("全件が実際のA8リンク（px.a8.netドメイン）でPLACEHOLDERを含まない", () => {
    for (const offer of APPROVED_OFFERS) {
      expect(offer.href).toContain("px.a8.net");
      expect(offer.href).not.toContain("PLACEHOLDER");
    }
  });
});

describe("getOfferById", () => {
  it("存在するIDならオファーを返す", () => {
    expect(getOfferById("dmm_stock")?.title).toBe("DMM 株");
  });

  it("存在しないIDなら undefined を返す", () => {
    expect(getOfferById("unknown_id")).toBeUndefined();
  });
});

describe("OFFERS_BY_LOAN_TAB（ローンタブ別の表示リスト）", () => {
  it("全タブのIDが承認済みオファーに解決できる", () => {
    for (const ids of Object.values(OFFERS_BY_LOAN_TAB)) {
      for (const id of ids) {
        expect(getOfferById(id)).toBeDefined();
      }
    }
  });
});

describe("selectAffiliateOffer（診断連動の選定ロジック）", () => {
  it("2月は確定申告オファー（マネーフォワード）を返す", () => {
    const offer = selectAffiliateOffer({ savingRate: 0, hasAccounts: false, month: 2 });
    expect(offer?.id).toBe("moneyforward");
  });

  it("3月も確定申告オファーを返す（投資条件を満たしていても申告期を優先）", () => {
    const offer = selectAffiliateOffer({ savingRate: 50, hasAccounts: true, month: 3 });
    expect(offer?.id).toBe("moneyforward");
  });

  it("貯蓄率20%以上かつ口座ありなら投資オファー（DMM株）を返す", () => {
    const offer = selectAffiliateOffer({ savingRate: 20, hasAccounts: true, month: 6 });
    expect(offer?.id).toBe("dmm_stock");
  });

  it("貯蓄率20%未満なら null（無理に出さない）", () => {
    expect(selectAffiliateOffer({ savingRate: 19.9, hasAccounts: true, month: 6 })).toBeNull();
  });

  it("口座未登録なら投資オファーは出さず null", () => {
    expect(selectAffiliateOffer({ savingRate: 30, hasAccounts: false, month: 6 })).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/test/utils/affiliates.test.ts`
Expected: FAIL（`../../utils/affiliates` が存在しないため import エラー）

- [ ] **Step 3: Write minimal implementation**

`src/utils/affiliates.ts` を新規作成:

```typescript
// ────────── アフィリエイト広告の一元管理 ──────────
// 広告リンク・表示文言・「どの文脈で出すか」をこのファイルにまとめる
// 審査が通ったら APPROVED_OFFERS に1件追加するだけで画面に反映される

// 広告1件の形
export interface AffiliateOffer {
  id: string;       // プログラム識別子（例: "dmm_stock"）
  tag: string;      // 小さく出すジャンルラベル（例: "日本株・米国株・NISA"）
  title: string;    // サービス名
  desc: string;     // 短い説明文
  cta: string;      // ボタンのテキスト
  href: string;     // アフィリエイトリンクURL
  context: "invest" | "tax" | "loan"; // どの文脈で出してよいか
}

// ── 承認済み広告（2026/05/17 A8.net広告リンクから取得）──
export const APPROVED_OFFERS: AffiliateOffer[] = [
  {
    id: "fujitomi_fx",
    tag: "FX自動売買",
    title: "シストレセレクト365（フジトミ証券）",
    desc: "ローン返済と並行して資産を増やしたい方に。FX自動売買で24時間稼働",
    cta: "詳しく見る →",
    href: "https://px.a8.net/svt/ejp?a8mat=4B3SMZ+EPVT6A+34QW+BWVTE",
    context: "invest",
  },
  {
    id: "dmm_tossy",
    tag: "株・FX・先物をアプリひとつで",
    title: "TOSSY（DMM証券）",
    desc: "あらゆる取引がアプリひとつで完結。初心者でも使いやすいUI",
    cta: "口座開設（無料）→",
    href: "https://px.a8.net/svt/ejp?a8mat=4B3SMZ+EOOXYQ+1WP2+1HLNLE",
    context: "invest",
  },
  {
    id: "dmm_stock",
    tag: "日本株・米国株・NISA",
    title: "DMM 株",
    desc: "手数料業界最安水準。NISA口座対応・米国株も1株から購入可能",
    cta: "口座開設（無料）→",
    href: "https://px.a8.net/svt/ejp?a8mat=4B3SMZ+EO3ICY+1WP2+15QHIA",
    context: "invest",
  },
  {
    id: "moneyforward",
    tag: "確定申告・家計管理",
    title: "マネーフォワード クラウド確定申告",
    desc: "自動化で80%以上の時間削減。銀行・カード連携でラクラク申告",
    cta: "無料で試す →",
    href: "https://px.a8.net/svt/ejp?a8mat=4B3RV6+8OKLDE+4JGQ+BYT9E",
    context: "tax",
  },
];

// ── 審査待ち（A8.net審査通過後に上の配列へ移動する）──
// promise_visa: プロミスVISAカード（報酬10,000円）tag:"消費者金融 → カード借り換え" context:"loan"
// smbc_nl:      三井住友カード(NL)（報酬12,000円）tag:"年会費無料・高還元" context:"loan"
// epos:         エポスカード（報酬7,000円）tag:"年会費無料・優待豊富" context:"loan"
// recruit:      リクルートカード（報酬4,800円）tag:"高還元・Pontaポイント" context:"loan"
// tokyu:        TOKYU CARD ClubQ JMB（報酬4,135円）tag:"東急線ユーザー向け" context:"loan"

// IDからオファーを探す（見つからなければ undefined）
export function getOfferById(id: string): AffiliateOffer | undefined {
  return APPROVED_OFFERS.find(offer => offer.id === id);
}

// ローンタブ（cf=消費者金融 / bl=銀行・リボ / lo=住宅・車）ごとに出す広告のID一覧
export const OFFERS_BY_LOAN_TAB: Record<"cf" | "bl" | "lo", string[]> = {
  cf: ["moneyforward"],
  bl: ["dmm_stock", "dmm_tossy"],
  lo: ["fujitomi_fx", "moneyforward"],
};

// 診断連動の選定に使う入力値の形
export interface OfferSelectionContext {
  savingRate: number;   // 貯蓄率（%）
  hasAccounts: boolean; // 口座が1件以上登録されているか
  month: number;        // 今の月（1〜12）
}

// 家計の状態に合った広告を最大1件選ぶ（合うものがなければ null）
// ルールは上から順に判定して最初にマッチしたものだけ返す
export function selectAffiliateOffer(ctx: OfferSelectionContext): AffiliateOffer | null {
  // ① 確定申告期（2〜3月）→ 確定申告ツール
  if (ctx.month === 2 || ctx.month === 3) {
    return getOfferById("moneyforward") ?? null;
  }
  // ② 貯蓄率が理想水準（20%以上）で口座管理もしている → 余剰資金の投資提案
  if (ctx.savingRate >= 20 && ctx.hasAccounts) {
    return getOfferById("dmm_stock") ?? null;
  }
  // ③ 合う提案がなければ何も出さない（無理に出すと信頼を失う）
  return null;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/test/utils/affiliates.test.ts`
Expected: PASS（11 tests）

- [ ] **Step 5: Commit**

```bash
cd /home/kenta_kamijyo
git add finance_web/src/utils/affiliates.ts finance_web/src/test/utils/affiliates.test.ts
git commit -m "feat(finance_web): 広告データと診断連動の選定ロジックを一元化

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: バナーUIコンポーネント（`AffiliateBanner.tsx`）

**Files:**
- Create: `src/components/AffiliateBanner.tsx`
- Test: `src/test/components/AffiliateBanner.test.tsx`

- [ ] **Step 1: Write the failing test**

`src/test/components/AffiliateBanner.test.tsx` を新規作成:

```tsx
// ────────── AffiliateBanner コンポーネントのテスト ──────────
import { render, screen } from "@testing-library/react";
import AffiliateBanner, { AffiliateSection } from "../../components/AffiliateBanner";
import { APPROVED_OFFERS } from "../../utils/affiliates";

describe("AffiliateBanner（広告バナー1枚）", () => {
  const offer = APPROVED_OFFERS[0];

  it("PRラベル・タイトル・説明文が表示される", () => {
    render(<AffiliateBanner offer={offer} />);
    expect(screen.getByText("PR")).toBeInTheDocument();
    expect(screen.getByText(offer.title)).toBeInTheDocument();
    expect(screen.getByText(offer.desc)).toBeInTheDocument();
  });

  it("リンクに rel=sponsored と正しいURLが付いている", () => {
    render(<AffiliateBanner offer={offer} />);
    const link = screen.getByRole("link");
    expect(link.getAttribute("rel")).toContain("sponsored");
    expect(link).toHaveAttribute("href", offer.href);
    expect(link).toHaveAttribute("target", "_blank");
  });
});

describe("AffiliateSection（ローンタブ用のまとまり）", () => {
  it("blタブでは承認済みの投資系2件（DMM株・TOSSY）が表示される", () => {
    render(<AffiliateSection tab="bl" />);
    expect(screen.getByText("DMM 株")).toBeInTheDocument();
    expect(screen.getByText("TOSSY（DMM証券）")).toBeInTheDocument();
  });

  it("cfタブでは審査待ちのプロミスVISAは表示されない", () => {
    render(<AffiliateSection tab="cf" />);
    expect(screen.queryByText("プロミスVISAカード")).not.toBeInTheDocument();
    expect(screen.getByText("マネーフォワード クラウド確定申告")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/test/components/AffiliateBanner.test.tsx`
Expected: FAIL（`../../components/AffiliateBanner` が存在しない）

- [ ] **Step 3: Write minimal implementation**

`src/components/AffiliateBanner.tsx` を新規作成（見た目は現行LoanViewのバナーを踏襲）:

```tsx
// ────────── アフィリエイトバナー ──────────
// 広告1枚のカードUIと、ローンタブ用のセクションをまとめたファイル
// 広告データ本体は utils/affiliates.ts が持つ。ここは「表示」だけを担当する

import { CSSProperties } from "react";
import { AffiliateOffer, OFFERS_BY_LOAN_TAB, getOfferById } from "../utils/affiliates";
import { COLOR_TEXT_HINT, COLOR_TEXT_SECONDARY, COLOR_TEXT_PRIMARY, COLOR_ACCENT } from "../utils/styles";

// ── スタイル定数 ──────────────────────────────────────────

// バナーのカード外枠
const STYLE_AFFIL_CARD: CSSProperties = {
  background: "rgba(15,23,42,0.85)",
  border: "1px solid rgba(34,211,238,0.2)",
  borderRadius: 14,
  padding: "14px 16px",
  marginBottom: 10,
  display: "flex",
  alignItems: "center",
  gap: 12,
  cursor: "pointer",
  transition: "border-color 0.15s",
};

// CTAボタン（右端の申し込みボタン風テキスト）
const STYLE_AFFIL_CTA: CSSProperties = {
  flexShrink: 0,
  background: COLOR_ACCENT,
  color: "#070b14",
  borderRadius: 10,
  padding: "8px 12px",
  fontSize: 12,
  fontWeight: 700,
  whiteSpace: "nowrap",
};

// ─────────────────────────────────────────────────────────

// 広告バナー1枚を描画するコンポーネント
export default function AffiliateBanner({ offer }: { offer: AffiliateOffer }) {
  return (
    <a
      href={offer.href}
      target="_blank"
      rel="noopener noreferrer sponsored"
      style={{ textDecoration: "none", display: "block" }}
    >
      <div style={STYLE_AFFIL_CARD}>
        {/* 左：テキスト情報 */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* 広告タグ + ジャンルラベル */}
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
            <span style={{ fontSize: 12, background: "rgba(34,211,238,0.15)", color: COLOR_ACCENT, borderRadius: 4, padding: "1px 6px", letterSpacing: "0.5px" }}>PR</span>
            <span style={{ fontSize: 12, color: COLOR_TEXT_HINT }}>{offer.tag}</span>
          </div>
          {/* サービス名 */}
          <div style={{ fontSize: 13, fontWeight: 700, color: COLOR_TEXT_PRIMARY, marginBottom: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{offer.title}</div>
          {/* 説明文 */}
          <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY }}>{offer.desc}</div>
        </div>
        {/* 右：CTAボタン */}
        <div style={STYLE_AFFIL_CTA}>{offer.cta}</div>
      </div>
    </a>
  );
}

// ローンタブ（cf/bl/lo）内のアフィリエイトセクション全体
// 承認済みの広告だけが OFFERS_BY_LOAN_TAB に載っているので、ここでは並べるだけ
export function AffiliateSection({ tab }: { tab: "cf" | "bl" | "lo" }) {
  // タブに対応する広告ID一覧を実データに変換する（存在しないIDは無視）
  const offers = OFFERS_BY_LOAN_TAB[tab]
    .map(getOfferById)
    .filter((offer): offer is AffiliateOffer => offer !== undefined);

  // 表示できる広告が1件もなければセクションごと出さない
  if (offers.length === 0) return null;

  return (
    <div style={{ marginTop: 16, marginBottom: 4 }}>
      {/* 区切りラベル */}
      <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, textTransform: "uppercase", letterSpacing: "2px", marginBottom: 10 }}>
        💳 おすすめ金融サービス
      </div>
      {offers.map(offer => (
        <AffiliateBanner key={offer.id} offer={offer} />
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/test/components/AffiliateBanner.test.tsx`
Expected: PASS（4 tests）

- [ ] **Step 5: Commit**

```bash
cd /home/kenta_kamijyo
git add finance_web/src/components/AffiliateBanner.tsx finance_web/src/test/components/AffiliateBanner.test.tsx
git commit -m "feat(finance_web): 広告バナーUIを独立コンポーネント化

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: LoanView を新コンポーネントへ移行（壊れリンク修正の本体）

**Files:**
- Modify: `src/views/LoanView.tsx`

- [ ] **Step 1: 旧コードを削除して新コンポーネントを使う**

`src/views/LoanView.tsx` の以下を変更:

1. **import 変更**（5〜12行目付近）: `CSSProperties` の import から `CSSProperties` を外し（`STYLE_LOAN_INTEREST_ALERT` で使うので残す）、新コンポーネントの import を追加:

```tsx
import React, { CSSProperties } from "react";
import { Loan } from "../types";
import { formatYen } from "../utils/format";
import { calculateMonthlyInterest, calculateTotalInterest, calculateCompletionDate, BRANDS_CF, BRANDS_BL } from "../utils/loanCalc";
import { COLOR_TEXT_HINT, COLOR_TEXT_SECONDARY, COLOR_TEXT_PRIMARY, COLOR_ACCENT, COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_BORDER, STYLE_CARD } from "../utils/styles";
import { StatLabel } from "../components/ui";
import LoanSection from "../components/LoanSection";
import StatBlock from "../components/StatBlock";
import { AffiliateSection } from "../components/AffiliateBanner";
```

2. **削除**: 14〜28行目の `AFFILIATE` 定数ブロック全体（`// ────────── A8.netアフィリエイトリンク ──────────` から `};` まで）

3. **削除**: 32〜56行目のスタイル定数 `STYLE_AFFIL_CARD` と `STYLE_AFFIL_CTA`（`STYLE_LOAN_INTEREST_ALERT` は**残す**）

4. **削除**: 72〜205行目の `function AffiliateBanner(...)` と `function AffiliateSection(...)` の定義全体

5. **残す**: `<AffiliateSection tab="cf" />` などの3箇所の呼び出しはそのまま（import 先が変わるだけ）

- [ ] **Step 2: 型チェックとテストで回帰がないことを確認**

Run: `npx tsc --noEmit && npx vitest run`
Expected: 型エラーなし・全テストPASS（この時点で 126 + 15 = 141 tests）

- [ ] **Step 3: Commit**

```bash
cd /home/kenta_kamijyo
git add finance_web/src/views/LoanView.tsx
git commit -m "fix(finance_web): 審査待ちプレースホルダー広告5件を非表示化

LoanViewの広告定義を utils/affiliates.ts に移行。
壊れたリンク（PROMISE_VISA_PLACEHOLDER等）が本番に出ていた問題を解消。

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: 家計診断カードに「あなたへの提案」枠

**Files:**
- Modify: `src/components/HealthCheckCard.tsx`
- Test: `src/test/components/HealthCheckCard.test.tsx`

- [ ] **Step 1: Write the failing test**

`src/test/components/HealthCheckCard.test.tsx` を新規作成:

```tsx
// ────────── HealthCheckCard（家計診断カード）のテスト ──────────
// 診断結果に連動した「あなたへの提案」枠の表示・非表示を確認する
import { render, screen } from "@testing-library/react";
import { vi, beforeEach, afterEach } from "vitest";
import HealthCheckCard from "../../components/HealthCheckCard";

describe("HealthCheckCard 提案枠（診断連動広告）", () => {
  beforeEach(() => {
    // 月の判定を固定するため日付を 2026-06-15（申告期ではない月）に固定する
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-15T12:00:00"));
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("貯蓄率20%以上かつ口座ありのとき投資系の提案が表示される", () => {
    // 収入30万・支出20万 → 貯蓄率 33%
    render(
      <HealthCheckCard
        totalIncome={300000}
        totalBurden={200000}
        totalLoanRepayment={0}
        totalFixedExpense={100000}
        net={100000}
        totalSavings={1000000}
        hasAccounts={true}
      />
    );
    expect(screen.getByText("あなたへの提案")).toBeInTheDocument();
    expect(screen.getByText("DMM 株")).toBeInTheDocument();
    expect(screen.getByText("PR")).toBeInTheDocument();
  });

  it("貯蓄率が低いとき提案枠は表示されない", () => {
    // 収入30万・支出29万 → 貯蓄率 3.3%
    render(
      <HealthCheckCard
        totalIncome={300000}
        totalBurden={290000}
        totalLoanRepayment={0}
        totalFixedExpense={100000}
        net={10000}
        totalSavings={100000}
        hasAccounts={true}
      />
    );
    expect(screen.queryByText("あなたへの提案")).not.toBeInTheDocument();
  });

  it("口座未登録のとき投資提案は表示されない", () => {
    render(
      <HealthCheckCard
        totalIncome={300000}
        totalBurden={200000}
        totalLoanRepayment={0}
        totalFixedExpense={100000}
        net={100000}
        totalSavings={0}
        hasAccounts={false}
      />
    );
    expect(screen.queryByText("あなたへの提案")).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/test/components/HealthCheckCard.test.tsx`
Expected: FAIL（「あなたへの提案」がまだ存在しない）

- [ ] **Step 3: Write minimal implementation**

`src/components/HealthCheckCard.tsx` に2箇所追加:

1. import に追加（既存 import 群の下）:

```tsx
import { selectAffiliateOffer } from "../utils/affiliates";
import AffiliateBanner from "./AffiliateBanner";
```

2. 「改善アクション」セクションの**直後**・「説明書き」の**直前**（`{/* 説明書き */}` コメントの前）に挿入:

```tsx
      {/* ────────── あなたへの提案（診断連動・最大1枠） ──────────
          家計の状態に合うサービスがある時だけ表示する。合わなければ何も出さない */}
      {(() => {
        // 現在の貯蓄率と口座の有無から、文脈に合う広告を最大1件選ぶ
        const offer = selectAffiliateOffer({
          savingRate: curSavingRate ?? 0,
          hasAccounts,
          month: new Date().getMonth() + 1,
        });
        if (!offer) return null;
        return (
          <div style={{ marginTop: 12 }}>
            <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, letterSpacing: "1px", marginBottom: 8 }}>
              💡 あなたへの提案
            </div>
            <AffiliateBanner offer={offer} />
          </div>
        );
      })()}
```

注意: `curSavingRate` は同コンポーネント内 152行目付近で定義済み（`totalIncome > 0 ? (net / totalIncome) * 100 : null`）。`hasAccounts` は props で受け取り済み。

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/test/components/HealthCheckCard.test.tsx`
Expected: PASS（3 tests）

- [ ] **Step 5: Commit**

```bash
cd /home/kenta_kamijyo
git add finance_web/src/components/HealthCheckCard.tsx finance_web/src/test/components/HealthCheckCard.test.tsx
git commit -m "feat(finance_web): 家計診断カードに診断連動の提案枠を追加

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: 月次レポートモーダルに提案枠

**Files:**
- Modify: `src/components/MonthlyReportModal.tsx`
- Modify: `src/App.tsx:337-346`（`<MonthlyReportModal>` 呼び出し）
- Test: `src/test/components/MonthlyReportModal.test.tsx`

- [ ] **Step 1: Write the failing test**

`src/test/components/MonthlyReportModal.test.tsx` を新規作成:

```tsx
// ────────── MonthlyReportModal（月次レポート）のテスト ──────────
import { render, screen } from "@testing-library/react";
import { vi, beforeEach, afterEach } from "vitest";
import MonthlyReportModal from "../../components/MonthlyReportModal";

const noop = () => {};

describe("MonthlyReportModal", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-15T12:00:00"));
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("open=false のとき何も表示されない", () => {
    const { container } = render(
      <MonthlyReportModal open={false} onClose={noop} year={2026} month={5}
        income={300000} expense={200000} topCats={[]} overBudget={[]} hasAccounts={true} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("収支サマリー（黒字バッジ）が表示される", () => {
    render(
      <MonthlyReportModal open={true} onClose={noop} year={2026} month={5}
        income={300000} expense={200000} topCats={[]} overBudget={[]} hasAccounts={true} />
    );
    expect(screen.getByText("2026年5月の振り返り")).toBeInTheDocument();
  });

  it("貯蓄率20%以上かつ口座ありなら提案バナーが表示される", () => {
    // 収入30万・支出20万 → 貯蓄率 33%
    render(
      <MonthlyReportModal open={true} onClose={noop} year={2026} month={5}
        income={300000} expense={200000} topCats={[]} overBudget={[]} hasAccounts={true} />
    );
    expect(screen.getByText("DMM 株")).toBeInTheDocument();
  });

  it("赤字（貯蓄率マイナス）のとき提案バナーは表示されない", () => {
    render(
      <MonthlyReportModal open={true} onClose={noop} year={2026} month={5}
        income={200000} expense={300000} topCats={[]} overBudget={[]} hasAccounts={true} />
    );
    expect(screen.queryByText("DMM 株")).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/test/components/MonthlyReportModal.test.tsx`
Expected: FAIL（`hasAccounts` prop が型に存在しない・バナー未実装）

- [ ] **Step 3: Write minimal implementation**

`src/components/MonthlyReportModal.tsx` を3箇所変更:

1. import に追加:

```tsx
import { selectAffiliateOffer } from "../utils/affiliates";
import AffiliateBanner from "./AffiliateBanner";
```

2. props 型（`MonthlyReportProps`）に追加:

```tsx
  // 口座が1件以上登録されているか（提案枠の表示判定に使う）
  hasAccounts: boolean;
```

関数の引数分割代入にも `hasAccounts,` を追加:

```tsx
export default function MonthlyReportModal({
  open, onClose, year, month, income, expense, topCats, overBudget, hasAccounts,
}: MonthlyReportProps) {
```

3. 「閉じるボタン」の**直前**に挿入:

```tsx
        {/* ── あなたへの提案（前月の家計状態に連動・最大1枠） ── */}
        {(() => {
          // 前月の貯蓄率（収入0なら0%として扱う）
          const savingRate = income > 0 ? (net / income) * 100 : 0;
          const offer = selectAffiliateOffer({
            savingRate,
            hasAccounts,
            month: new Date().getMonth() + 1,
          });
          if (!offer) return null;
          return (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, letterSpacing: "1px", marginBottom: 8 }}>
                💡 あなたへの提案
              </div>
              <AffiliateBanner offer={offer} />
            </div>
          );
        })()}
```

4. `src/App.tsx` の `<MonthlyReportModal>` 呼び出し（337-346行目）に1行追加:

```tsx
    <MonthlyReportModal
      open={showMonthlyReport}
      onClose={() => setShowMonthlyReport(false)}
      year={reportData.year}
      month={reportData.month}
      income={reportData.income}
      expense={reportData.expense}
      topCats={reportData.topCats}
      overBudget={reportData.overBudget}
      hasAccounts={accounts.length > 0}
    />
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/test/components/MonthlyReportModal.test.tsx && npx tsc --noEmit`
Expected: PASS（4 tests）・型エラーなし

- [ ] **Step 5: Commit**

```bash
cd /home/kenta_kamijyo
git add finance_web/src/components/MonthlyReportModal.tsx finance_web/src/App.tsx finance_web/src/test/components/MonthlyReportModal.test.tsx
git commit -m "feat(finance_web): 月次レポートに診断連動の提案枠を追加

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: 「友達に教える」シェアカード

**Files:**
- Create: `src/components/ShareCard.tsx`
- Modify: `src/views/SettingsView.tsx`（使い方カードとアプリ情報カードの間）
- Test: `src/test/components/ShareCard.test.tsx`

- [ ] **Step 1: Write the failing test**

`src/test/components/ShareCard.test.tsx` を新規作成:

```tsx
// ────────── ShareCard（友達に教えるカード）のテスト ──────────
// jsdom には navigator.share / navigator.clipboard が無いので、
// defineProperty で一時的にモックを生やしてテストする
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, afterEach } from "vitest";
import ShareCard, { SHARE_URL } from "../../components/ShareCard";

// テストで生やしたモックを毎回掃除する
afterEach(() => {
  // @ts-expect-error テスト用に生やしたものを消す
  delete navigator.share;
});

describe("ShareCard", () => {
  it("シェアボタンが表示される", () => {
    render(<ShareCard />);
    expect(screen.getByText("📣 友達に教える")).toBeInTheDocument();
  });

  it("navigator.share がある環境ではシェアシートを開く", async () => {
    const shareMock = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "share", { value: shareMock, configurable: true, writable: true });
    render(<ShareCard />);
    fireEvent.click(screen.getByText("📣 友達に教える"));
    await waitFor(() => expect(shareMock).toHaveBeenCalledTimes(1));
    // シェア内容にアプリURLが含まれている
    expect(shareMock.mock.calls[0][0].url).toBe(SHARE_URL);
  });

  it("navigator.share が無い環境ではURLをクリップボードにコピーする", async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: writeTextMock }, configurable: true, writable: true,
    });
    render(<ShareCard />);
    fireEvent.click(screen.getByText("📣 友達に教える"));
    // コピー成功のフィードバックがボタンに出る
    await waitFor(() => expect(screen.getByText("✓ リンクをコピーしました")).toBeInTheDocument());
    expect(writeTextMock.mock.calls[0][0]).toContain(SHARE_URL);
  });

  it("クリップボードへのコピーに失敗したらエラーメッセージを出す", async () => {
    const writeTextMock = vi.fn().mockRejectedValue(new Error("denied"));
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: writeTextMock }, configurable: true, writable: true,
    });
    render(<ShareCard />);
    fireEvent.click(screen.getByText("📣 友達に教える"));
    await waitFor(() => expect(screen.getByText(/コピーできませんでした/)).toBeInTheDocument());
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/test/components/ShareCard.test.tsx`
Expected: FAIL（`../../components/ShareCard` が存在しない）

- [ ] **Step 3: Write minimal implementation**

`src/components/ShareCard.tsx` を新規作成:

```tsx
// ────────── 「友達に教える」シェアカード ──────────
// 設定タブに置く、アプリ自体を広めてもらうためのカード
// スマホ: ネイティブのシェアシート（navigator.share）
// PC等: クリップボードにURLをコピーしてボタンの文言でフィードバック

import { useState } from "react";
import { STYLE_CARD, STYLE_BUTTON_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_NEGATIVE } from "../utils/styles";

// シェアで送る内容（OGP・index.html の説明文とトーンを合わせる）
const SHARE_TITLE = "BYB — Before You Broke";
const SHARE_TEXT = "収支を入力するだけ。グラフで家計が一目でわかる無料の家計簿アプリ";
export const SHARE_URL = "https://financeweb-nine.vercel.app";

export default function ShareCard() {
  // ボタンのフィードバック状態（"" = 通常 / copied = コピー成功 / error = 失敗）
  const [feedback, setFeedback] = useState<"" | "copied" | "error">("");

  async function share() {
    // スマホなどシェアシートが使える環境
    if (typeof navigator.share === "function") {
      try {
        await navigator.share({ title: SHARE_TITLE, text: SHARE_TEXT, url: SHARE_URL });
      } catch (_) {
        // ユーザーがシェアをキャンセルした場合もここに来る（正常系なので何もしない）
      }
      return;
    }
    // PC等：クリップボードにコピーする
    try {
      await navigator.clipboard.writeText(`${SHARE_TEXT} ${SHARE_URL}`);
      setFeedback("copied");
    } catch (_) {
      setFeedback("error");
    }
    // 2秒後にボタンを元の表示に戻す
    setTimeout(() => setFeedback(""), 2000);
  }

  return (
    <div style={{ ...STYLE_CARD, marginTop: 16 }}>
      <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: 10 }}>
        友達に教える
      </div>
      <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, lineHeight: 1.7, marginBottom: 12 }}>
        BYBが役に立ったら、家族や友達にもシェアしてもらえると嬉しいです。
      </div>
      <button type="button" onClick={share} style={{ ...STYLE_BUTTON_PRIMARY, width: "100%" }}>
        {feedback === "copied" ? "✓ リンクをコピーしました" : "📣 友達に教える"}
      </button>
      {/* コピー失敗時だけ表示するエラーメッセージ（URLを直接見せて手動コピーできるように） */}
      {feedback === "error" && (
        <div style={{ fontSize: 12, color: COLOR_NEGATIVE, marginTop: 8, textAlign: "center", lineHeight: 1.6 }}>
          コピーできませんでした。このURLを直接共有してください：<br />
          {SHARE_URL}
        </div>
      )}
    </div>
  );
}
```

`src/views/SettingsView.tsx` に組み込み:

1. import 追加: `import ShareCard from "../components/ShareCard";`
2. 「使い方カード」（`📖 使い方を見る` のカード）の閉じ `</div>` 直後・「アプリ情報カード」コメントの直前に挿入:

```tsx
      {/* ────────── 友達に教えるカード ────────── */}
      <ShareCard />
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/test/components/ShareCard.test.tsx && npx tsc --noEmit`
Expected: PASS（4 tests）・型エラーなし

- [ ] **Step 5: Commit**

```bash
cd /home/kenta_kamijyo
git add finance_web/src/components/ShareCard.tsx finance_web/src/views/SettingsView.tsx finance_web/src/test/components/ShareCard.test.tsx
git commit -m "feat(finance_web): 設定タブに「友達に教える」シェアカードを追加

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: サマリーPNGに透かし帯

**Files:**
- Modify: `src/utils/summaryExport.ts`
- Test: `src/utils/summaryExport.test.ts`（既存ファイルに追記）

- [ ] **Step 1: Write the failing test**

`src/utils/summaryExport.test.ts` の末尾に追記:

```typescript
// ────────── appendWatermark（PNG透かし帯）のテスト ──────────
import { appendWatermark, WATERMARK_TEXT } from "./summaryExport";

describe("appendWatermark", () => {
  it("透かし文言にアプリ名とURLが含まれている", () => {
    expect(WATERMARK_TEXT).toContain("BYB");
    expect(WATERMARK_TEXT).toContain("financeweb-nine.vercel.app");
  });

  it("2Dコンテキストが使えない環境（jsdom）では元のcanvasをそのまま返す", () => {
    // jsdom の canvas.getContext は null を返すのでフォールバック分岐が通る
    const canvas = document.createElement("canvas");
    canvas.width = 100;
    canvas.height = 50;
    expect(appendWatermark(canvas)).toBe(canvas);
  });
});
```

注意: 既存ファイル先頭に `import` 群があるので、追記する `import` はファイル先頭の既存 import の下にまとめる（`appendWatermark, WATERMARK_TEXT` を既存の `from "./summaryExport"` の import に統合してもよい）。

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/utils/summaryExport.test.ts`
Expected: FAIL（`appendWatermark` が export されていない）

- [ ] **Step 3: Write minimal implementation**

`src/utils/summaryExport.ts` に追加（`exportSummaryImage` の直前）:

```typescript
// 透かしに入れる文言（シェアされた画像からアプリにたどり着けるようにする）
export const WATERMARK_TEXT = "BYB — financeweb-nine.vercel.app";

// PNG画像の下に透かし帯（アプリ名＋URL）を追加した新しいcanvasを返す
// 2Dコンテキストが取れない環境では透かしなしの元canvasをそのまま返す
export function appendWatermark(source: HTMLCanvasElement): HTMLCanvasElement {
  const FOOTER_HEIGHT = 56; // 帯の高さ（scale:2 で出力されるので実質28px相当）
  const output = document.createElement("canvas");
  output.width = source.width;
  output.height = source.height + FOOTER_HEIGHT;
  const context = output.getContext("2d");
  if (!context) return source;

  // 背景をアプリの背景色で塗ってから、元の画像を上に重ねる
  context.fillStyle = "#0a0a0c";
  context.fillRect(0, 0, output.width, output.height);
  context.drawImage(source, 0, 0);

  // 帯の中央に小さくアプリ名とURLを描く
  context.font = "22px monospace";
  context.fillStyle = "#9a9aa3";
  context.textAlign = "center";
  context.fillText(WATERMARK_TEXT, output.width / 2, source.height + 36);
  return output;
}
```

`exportSummaryImage` 内の1行を変更:

変更前:
```typescript
  const canvas = await html2canvas(node, { backgroundColor: "#0a0a0c", scale: 2 });
```

変更後:
```typescript
  // 画像化してから下部に透かし帯（アプリ名＋URL）を追加する
  const canvas = appendWatermark(await html2canvas(node, { backgroundColor: "#0a0a0c", scale: 2 }));
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/utils/summaryExport.test.ts`
Expected: PASS（既存テスト＋新規2件）

- [ ] **Step 5: Commit**

```bash
cd /home/kenta_kamijyo
git add finance_web/src/utils/summaryExport.ts finance_web/src/utils/summaryExport.test.ts
git commit -m "feat(finance_web): サマリーPNG書き出しにアプリURL透かしを追加

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 8: バージョン表記の一元化（1.6.0）

**Files:**
- Modify: `package.json`（version）
- Modify: `vite.config.js`（define 追加）
- Modify: `src/vite-env.d.ts`（型宣言）
- Modify: `src/components/PasswordGate.tsx:235`（フッター）
- Modify: `src/views/SettingsView.tsx:634-638`（アプリ情報カード）

- [ ] **Step 1: package.json の version を 1.6.0 に**

```json
  "version": "1.6.0",
```

- [ ] **Step 2: vite.config.js に define を追加**

ファイル先頭の import に追加:

```js
import { readFileSync } from "node:fs";

// package.json の version をビルド時に読み込んで __APP_VERSION__ として全コードに注入する
const packageJson = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf-8"));
```

`defineConfig({...})` の中（`plugins` と同じ階層）に追加:

```js
  // __APP_VERSION__ という名前で package.json のバージョン文字列を使えるようにする
  define: {
    __APP_VERSION__: JSON.stringify(packageJson.version),
  },
```

- [ ] **Step 3: src/vite-env.d.ts に型宣言を追加**

末尾に追記:

```typescript
// vite.config.js の define で注入されるアプリバージョン（package.json の version と常に一致）
declare const __APP_VERSION__: string;
```

- [ ] **Step 4: PasswordGate.tsx のフッターを連動化**

変更前（235行目付近）:
```tsx
          v1.2.2 / © 2026 kmkn0523<br/>
```

変更後:
```tsx
          v{__APP_VERSION__} / © 2026 kmkn0523<br/>
```

- [ ] **Step 5: SettingsView.tsx のアプリ情報カードを連動化**

変更前（634行目付近）:
```tsx
            <span style={{ color: COLOR_TEXT_PRIMARY }}>家計管理アプリ</span>
```
変更後（アプリ名を正式名称に統一）:
```tsx
            <span style={{ color: COLOR_TEXT_PRIMARY }}>BYB — Before You Broke</span>
```

変更前（638行目付近）:
```tsx
            <span style={{ color: COLOR_TEXT_PRIMARY, fontFamily: "monospace" }}>v1.5.0</span>
```
変更後:
```tsx
            <span style={{ color: COLOR_TEXT_PRIMARY, fontFamily: "monospace" }}>v{__APP_VERSION__}</span>
```

- [ ] **Step 6: 型チェック・全テスト・ビルドで検証**

Run: `npx tsc --noEmit && npx vitest run && npm run build`
Expected: 型エラーなし・全テストPASS・ビルド成功（`__APP_VERSION__` が "1.6.0" に置換される）

- [ ] **Step 7: Commit**

```bash
cd /home/kenta_kamijyo
git add finance_web/package.json finance_web/vite.config.js finance_web/src/vite-env.d.ts finance_web/src/components/PasswordGate.tsx finance_web/src/views/SettingsView.tsx
git commit -m "chore(finance_web): v1.6.0・バージョン表記をpackage.jsonと自動連動化

3箇所バラバラだったバージョン表記（1.2.2/1.2.2/1.5.0）を
viteのdefineで一元化。今後はpackage.jsonを上げるだけで全画面に反映。

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 9: SNS紹介投稿文の下書き

**Files:**
- Create: `docs/sns_launch_posts.md`（finance_web/docs/ 配下）

- [ ] **Step 1: 投稿文ファイルを作成**

`docs/sns_launch_posts.md` を新規作成:

```markdown
# BYB SNS紹介投稿 下書き

作成日: 2026-06-11
対象: Threads（@RoninWords ではなく個人 or skin とは別文脈で）・X
投稿は**手動**で行う。skin/ronin の自動投稿JSONには入れない。

---

## 事前準備：スクリーンショット3枚

デモデータ（収入30万・支出いくつか・口座1つ・ローン1つ程度）を入れた状態で撮影する。

1. **概要タブ**：収入サマリーカード＋今月のペースが見える状態
2. **家計診断**：A〜B評価が出ている状態（診断カードを開いた画面）
3. **月次サマリー**：🧾タブの収支・貯蓄率・カテゴリ内訳

> 撮影時の注意：実データではなくデモデータで撮る（金額が写るため）

---

## Threads パターン1（共感フック型）

\`\`\`
家計簿アプリ、何度も挫折した人へ。

挫折の原因って「銀行連携の設定が面倒」「広告だらけ」「データをクラウドに預けるのが不安」のどれかじゃないですか。

それが嫌で、自分で作りました。

・口座連携なし。収支を入力するだけ
・データは端末の中だけ。外部送信ゼロ
・貯蓄率や返済比率からA〜Eの家計診断

無料・登録不要でブラウザからすぐ使えます👇
https://financeweb-nine.vercel.app
\`\`\`

## Threads パターン2（機能訴求型）

\`\`\`
無料の家計簿アプリ「BYB」を公開しています。

📊 収支・固定費・ローンを一画面で管理
🩺 貯蓄率・返済比率からA〜E評価の家計診断
🎯 貯金目標と繰り上げ返済シミュレーション
🔒 データは端末内で暗号化（クラウドに送らない）

インストール不要。ブラウザで開いて、ホーム画面に追加すればアプリになります。
https://financeweb-nine.vercel.app
\`\`\`

## X パターン（短文）

\`\`\`
家計簿アプリBYB、無料公開中。

・口座連携なし、登録なし
・データは端末内だけで暗号化
・収支を入れるだけでA〜E家計診断

https://financeweb-nine.vercel.app
\`\`\`

---

## 投稿のコツ

- スクショは1〜3枚添付（1枚目に概要タブ＝一番見栄えがする画面）
- 投稿時間は20〜22時台（家計を見直す時間帯）
- 反応があったリプには「どんな機能が欲しいか」を聞き返す（次の開発ネタになる）
```

注意: 上記コードブロック内の `\`\`\`` は実ファイルでは ``` をそのまま書く。

- [ ] **Step 2: Commit**

```bash
cd /home/kenta_kamijyo
git add finance_web/docs/sns_launch_posts.md
git commit -m "docs(finance_web): SNS紹介投稿の下書きを追加

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 10: 最終検証

**Files:** なし（検証のみ）

- [ ] **Step 1: 全テスト実行**

Run: `npx vitest run`
Expected: 全件PASS（既存126件＋新規約28件 ≈ 154件）

- [ ] **Step 2: 型チェック＋本番ビルド**

Run: `npx tsc --noEmit && npm run build`
Expected: エラーなし・`dist/` 生成成功

- [ ] **Step 3: ローカルで目視確認（preview）**

Run: `npm run preview` を起動し、ユーザーに以下の確認を依頼:
- ローンタブ：壊れたバナー（プロミス等5件）が消え、承認済みのみ表示
- 設定タブ：「友達に教える」カード・バージョン v1.6.0 表記
- 初回LP（シークレットウィンドウで）：フッターが v1.6.0
- サマリータブ：PNG書き出しで画像下部に透かし

- [ ] **Step 4: TODO.md 更新（リリース内容を反映）**

`/home/kenta_kamijyo/TODO.md` の finance_web セクションに v1.6.0 の完了項目を追記し、`SNS（Threads / X）でアプリを紹介する投稿を出す` の前提が整ったことをメモ。

- [ ] **Step 5: デプロイ（ユーザー承認後のみ）**

ユーザーのOKが出たら:
Run: `cd /home/kenta_kamijyo/finance_web && npx vercel --prod`
Expected: デプロイ成功・本番URLで Step 3 と同じ項目を再確認

---

## 設計書からの変更点（実装前調査による）

1. 設計③の「ログイン画面に機能ハイライト追加」→ **初回LPは実装済みだった**ため取りやめ。代わりにバージョン表記3箇所バラバラ問題の解消（Task 8）に変更（設計書も修正済み）
2. シェアのフィードバックはトースト（showT）ではなく**ボタン文言の切り替え**で実装 — SettingsView の props に showT が無く、props 追加なしで自己完結させる方が変更範囲が小さいため
```
