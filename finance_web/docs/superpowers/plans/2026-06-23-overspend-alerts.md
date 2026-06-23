# 使いすぎアラート（フォアグラウンド通知）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 予算に対する当月のカテゴリ別支出が80%/100%を超えたら、フォアグラウンドのブラウザ通知でユーザーに知らせる。

**Architecture:** 純粋な判定関数（`evaluateOverspend`）で「鳴らすべきアラート＋更新後ログ」を算出し、薄いフック（`useOverspendAlerts`）が当月支出の変化を監視して既存 `useNotification` で通知。設定UIは予算セクションと設定タブの両方に置く。すべて端末ローカル保存・同期対象外。

**Tech Stack:** React 18 + TypeScript, Vite, vitest, Web Notification API（既存 `src/hooks/useNotification.ts`）。

## Global Constraints

- 各行に初心者向け日本語コメントを付ける（既存コードと同じ密度）。
- 変数名・関数名は略さない分かりやすい英単語。
- E2E暗号化を壊さない：サーバ送信・サーバ判定は一切しない（純クライアント機能）。
- `SYNC_KEYS`（`src/utils/syncState.ts`）には追加しない（端末ローカルのみ）。
- 予算は `Record<string, number>`（`src/types.ts` の `Budget`）。支出カテゴリは `EXPENSE_CATEGORIES`（`src/utils/format.ts`）。
- テストは `npx vitest run` で実行。型は `npx tsc --noEmit` で確認。
- 既存コードの無関係な箇所は変更しない。

---

### Task 1: 判定の純粋関数 `evaluateOverspend` / `pruneLog`

**Files:**
- Create: `src/utils/overspendAlerts.ts`
- Test: `src/utils/overspendAlerts.test.ts`

**Interfaces:**
- Consumes: なし（純粋関数）。
- Produces:
  - `interface OverspendAlert { category: string; level: 80 | 100; spent: number; budget: number; ratio: number }`
  - `type NotifyLog = Record<string, string[]>`
  - `evaluateOverspend(actual: Record<string, number>, budget: Record<string, number>, log: NotifyLog, month: string): { alerts: OverspendAlert[]; nextLog: NotifyLog }`
  - `pruneLog(log: NotifyLog, month: string): NotifyLog`

- [ ] **Step 1: Write the failing test**

`src/utils/overspendAlerts.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { evaluateOverspend, pruneLog } from "./overspendAlerts";

const M = "2026-06";

describe("evaluateOverspend", () => {
  it("80%未満は鳴らない", () => {
    const { alerts } = evaluateOverspend({ 食費: 7900 }, { 食費: 10000 }, {}, M);
    expect(alerts).toEqual([]);
  });

  it("80%以上で level=80 を鳴らす", () => {
    const { alerts, nextLog } = evaluateOverspend({ 食費: 8000 }, { 食費: 10000 }, {}, M);
    expect(alerts).toEqual([{ category: "食費", level: 80, spent: 8000, budget: 10000, ratio: 0.8 }]);
    expect(nextLog[M]).toContain("食費|80");
  });

  it("100%以上で level=100。80%も同時にログ済みにして二重通知しない", () => {
    const { alerts, nextLog } = evaluateOverspend({ 食費: 12000 }, { 食費: 10000 }, {}, M);
    expect(alerts).toEqual([{ category: "食費", level: 100, spent: 12000, budget: 10000, ratio: 1.2 }]);
    expect(nextLog[M]).toContain("食費|100");
    expect(nextLog[M]).toContain("食費|80");
  });

  it("同月同レベルは重複して鳴らさない", () => {
    const log = { [M]: ["食費|80"] };
    const { alerts } = evaluateOverspend({ 食費: 8500 }, { 食費: 10000 }, log, M);
    expect(alerts).toEqual([]);
  });

  it("予算未設定(0)のカテゴリは対象外", () => {
    const { alerts } = evaluateOverspend({ 食費: 9999 }, { 食費: 0 }, {}, M);
    expect(alerts).toEqual([]);
  });

  it("月が変わればまた鳴る", () => {
    const log = { "2026-05": ["食費|80"] };
    const { alerts } = evaluateOverspend({ 食費: 8000 }, { 食費: 10000 }, log, "2026-06");
    expect(alerts).toHaveLength(1);
  });
});

describe("pruneLog", () => {
  it("当月以外のログを消す", () => {
    const log = { "2026-05": ["食費|80"], "2026-06": ["住居|100"] };
    expect(pruneLog(log, "2026-06")).toEqual({ "2026-06": ["住居|100"] });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/utils/overspendAlerts.test.ts`
Expected: FAIL（`overspendAlerts` から import 不可）。

- [ ] **Step 3: Write minimal implementation**

`src/utils/overspendAlerts.ts`:

```ts
// ────────── 使いすぎアラートの判定（純粋関数・React非依存） ──────────
// 当月のカテゴリ別支出と予算を比べ、80%/100%を新たに超えたカテゴリを返す。
// 同じ月・同じカテゴリ・同じ段階は一度しか鳴らさない（通知ログで抑制）。

// 通知1件分の情報
export interface OverspendAlert {
  category: string;   // 例: "食費"
  level: 80 | 100;    // 段階（80%注意 / 100%オーバー）
  spent: number;      // 当月の支出
  budget: number;     // 予算
  ratio: number;      // spent / budget（例: 0.85）
}

// 通知ログ: 月("YYYY-MM") -> ["食費|80","食費|100", ...]
export type NotifyLog = Record<string, string[]>;

// その段階を既に通知済みかを表すキー
function logKey(category: string, level: 80 | 100): string {
  return `${category}|${level}`;
}

// 当月の状況から「新たに鳴らすべきアラート」と「更新後ログ」を返す
export function evaluateOverspend(
  actual: Record<string, number>,
  budget: Record<string, number>,
  log: NotifyLog,
  month: string
): { alerts: OverspendAlert[]; nextLog: NotifyLog } {
  // 当月のログ配列（無ければ空）をコピーして使う
  const monthLog = new Set(log[month] ?? []);
  const alerts: OverspendAlert[] = [];

  // 予算が設定されているカテゴリだけを見る
  for (const category of Object.keys(budget)) {
    const budgetAmount = Number(budget[category] || 0);
    if (budgetAmount <= 0) continue;               // 予算未設定は対象外（ゼロ除算も防ぐ）
    const spent = Number(actual[category] || 0);
    const ratio = spent / budgetAmount;

    if (ratio >= 1.0 && !monthLog.has(logKey(category, 100))) {
      // 100%超え：まだ100%通知をしていなければ鳴らす
      alerts.push({ category, level: 100, spent, budget: budgetAmount, ratio });
      monthLog.add(logKey(category, 100));
      monthLog.add(logKey(category, 80)); // 80%も済み扱いにして二重通知を防ぐ
    } else if (ratio >= 0.8 && !monthLog.has(logKey(category, 80))) {
      // 80%超え：まだ80%通知をしていなければ鳴らす
      alerts.push({ category, level: 80, spent, budget: budgetAmount, ratio });
      monthLog.add(logKey(category, 80));
    }
  }

  const nextLog: NotifyLog = { ...log, [month]: Array.from(monthLog) };
  return { alerts, nextLog };
}

// 当月以外の古いログを落とす（肥大化防止）
export function pruneLog(log: NotifyLog, month: string): NotifyLog {
  return month in log ? { [month]: log[month] } : {};
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/utils/overspendAlerts.test.ts`
Expected: PASS（7 tests）。

- [ ] **Step 5: Commit**

```bash
git add src/utils/overspendAlerts.ts src/utils/overspendAlerts.test.ts
git commit -m "feat(finance_web): 使いすぎアラートの判定純粋関数を追加"
```

---

### Task 2: フック `useOverspendAlerts` と App.tsx 配線

**Files:**
- Create: `src/hooks/useOverspendAlerts.ts`
- Modify: `src/App.tsx`（当月カテゴリ別支出の memo / enabled の永続化 / フック呼び出し）

**Interfaces:**
- Consumes: Task 1 の `evaluateOverspend`, `pruneLog`, `NotifyLog`, `OverspendAlert`。`useNotification`（既存）の `notify`, `permission`。
- Produces:
  - `interface UseOverspendAlertsDeps { enabled: boolean; permission: NotificationPermission | "unsupported"; actualByCategory: Record<string, number>; budget: Record<string, number>; notify: (title: string, body?: string) => void; ready: boolean }`
  - `useOverspendAlerts(deps: UseOverspendAlertsDeps): void`

- [ ] **Step 1: フックを作成**

`src/hooks/useOverspendAlerts.ts`:

```ts
// ────────── 使いすぎアラート・フック ──────────
// 当月のカテゴリ別支出が変わるたびに判定し、新たに閾値を超えたら通知する。
// 判定ロジックは純粋関数(evaluateOverspend)に委ね、ここは「監視→通知→保存」だけ担う。
import { useEffect } from "react";
import { evaluateOverspend, pruneLog, type NotifyLog, type OverspendAlert } from "../utils/overspendAlerts";
import { formatYen } from "../utils/format";

// localStorage に通知ログを置くキー（端末ローカル・同期しない）
const LS_LOG = "kk_notify_overspend_log";

export interface UseOverspendAlertsDeps {
  enabled: boolean;                                    // 設定スイッチ
  permission: NotificationPermission | "unsupported"; // 通知許可状態
  actualByCategory: Record<string, number>;           // 当月のカテゴリ別支出
  budget: Record<string, number>;                     // カテゴリ別予算
  notify: (title: string, body?: string) => void;     // 通知関数（useNotification由来）
  ready: boolean;                                      // データ読込完了フラグ
}

// localStorage から通知ログを安全に読む
function readLog(): NotifyLog {
  try {
    const raw = localStorage.getItem(LS_LOG);
    return raw ? (JSON.parse(raw) as NotifyLog) : {};
  } catch {
    return {};
  }
}

// 1件のアラートを通知文言にする
function alertToMessage(a: OverspendAlert): { title: string; body: string } {
  const pct = Math.round(a.ratio * 100);
  if (a.level === 100) {
    const over = a.spent - a.budget;
    return {
      title: `🚨 ${a.category}が予算オーバー`,
      body: `今月 ${formatYen(a.spent)} / ${formatYen(a.budget)}（${formatYen(over)}超過）`,
    };
  }
  return {
    title: `⚠️ ${a.category}が予算の${pct}%`,
    body: `今月 ${formatYen(a.spent)} / ${formatYen(a.budget)}`,
  };
}

export function useOverspendAlerts(deps: UseOverspendAlertsDeps): void {
  const { enabled, permission, actualByCategory, budget, notify, ready } = deps;

  // 当月支出が変わるたび（＝支出記録時）と初回（＝アプリ起動時）に判定する
  useEffect(() => {
    if (!ready || !enabled || permission !== "granted") return;

    // 当月("YYYY-MM")を求める
    const now = new Date();
    const month = now.getFullYear() + "-" + String(now.getMonth() + 1).padStart(2, "0");

    // 既存ログを当月だけに掃除してから判定
    const log = pruneLog(readLog(), month);
    const { alerts, nextLog } = evaluateOverspend(actualByCategory, budget, log, month);

    if (alerts.length === 1) {
      // 1件：具体的に通知
      const { title, body } = alertToMessage(alerts[0]);
      notify(title, body);
    } else if (alerts.length > 1) {
      // 複数：連発を避けて1件に集約
      const over = alerts.filter(a => a.level === 100).length;
      const summary = over > 0
        ? `${alerts.length}件のカテゴリが予算に近づく/超えています`
        : `${alerts.length}件のカテゴリが予算に近づいています`;
      notify("⚠️ 予算アラート", summary);
    }

    // 鳴らした分を記録（次回以降の二重通知を防ぐ）
    if (alerts.length > 0) {
      try {
        localStorage.setItem(LS_LOG, JSON.stringify(nextLog));
      } catch {
        // 保存失敗は致命的でないので無視
      }
    }
    // actualByCategory / budget / enabled / permission / ready の変化で再評価
  }, [ready, enabled, permission, actualByCategory, budget, notify]);
}
```

- [ ] **Step 2: `formatYen` の存在を確認**

Run: `grep -n "export function formatYen\|export const formatYen" src/utils/format.ts`
Expected: 1件ヒット。もし関数名が異なる場合（例 `formatCurrency`）は、その正しい名前に Step 1 の import と呼び出しを置き換える。

- [ ] **Step 3: App.tsx に当月カテゴリ別支出の memo を追加**

`src/App.tsx` の `expByCat` 定義（210行目付近）の直後に追加する：

```tsx
  // 当月（実際の今月）のカテゴリ別変動支出。閲覧中の月タブとは無関係に常に今月を見る。
  const currentMonthExpByCategory = useMemo(() => {
    const thisMonth = today.getFullYear() + "-" + String(today.getMonth() + 1).padStart(2, "0");
    const map: Record<string, number> = {};
    transactions.forEach(t => {
      // t.date は "YYYY-MM-DD"。先頭7文字が当月なら集計する
      if (t.category && typeof t.date === "string" && t.date.slice(0, 7) === thisMonth) {
        map[t.category] = (map[t.category] || 0) + Number(t.amount || 0);
      }
    });
    return map;
  }, [transactions]);
```

- [ ] **Step 4: App.tsx に enabled の永続化とフック呼び出しを追加**

`src/App.tsx` の `useNotification` 利用箇所（133行目付近 `const { permission: notifPermission, requestPermission, notify } = useNotification();`）の直後に追加：

```tsx
  // 使いすぎ通知のオン/オフ（端末ローカル・同期しない）
  const [overspendNotifyEnabled, setOverspendNotifyEnabled] = usePersist("kk_notify_overspend_enabled", false);
```

さらに `currentMonthExpByCategory` を定義した後（Step 3 の直後）に追加：

```tsx
  // 当月の使いすぎを監視して通知する
  useOverspendAlerts({
    enabled: overspendNotifyEnabled,
    permission: notifPermission,
    actualByCategory: currentMonthExpByCategory,
    budget,
    notify,
    ready: allOk,
  });
```

import を `src/App.tsx` の先頭付近（他の hooks import の近く）に追加：

```tsx
import { useOverspendAlerts } from "./hooks/useOverspendAlerts";
```

- [ ] **Step 5: 型チェックとテスト**

Run: `npx tsc --noEmit && npx vitest run`
Expected: 型エラー無し、既存テスト全合格（Task 1 の7件含む）。

- [ ] **Step 6: Commit**

```bash
git add src/hooks/useOverspendAlerts.ts src/App.tsx
git commit -m "feat(finance_web): 使いすぎアラートのフックとApp配線を追加"
```

---

### Task 3: 設定UI `OverspendNotifySettings` と2箇所への設置・通知アイコン修正

**Files:**
- Create: `src/components/OverspendNotifySettings.tsx`
- Modify: `src/App.tsx`（設定タブに設置・props受け渡し）
- Modify: `src/components/BudgetSection.tsx`（予算セクションに設置）
- Modify: `src/hooks/useNotification.ts`（アイコンパス修正）

**Interfaces:**
- Consumes: `notifPermission`, `requestPermission`（既存 `useNotification`）、`overspendNotifyEnabled`, `setOverspendNotifyEnabled`（Task 2 で App に追加）。
- Produces:
  - `interface OverspendNotifySettingsProps { enabled: boolean; onToggle: (v: boolean) => void; permission: NotificationPermission | "unsupported"; onRequestPermission: () => void }`
  - `export default function OverspendNotifySettings(props): JSX.Element`

- [ ] **Step 1: 通知アイコンのパスを修正**

`src/hooks/useNotification.ts` の49行目を実在するアイコンに直す：

```ts
        icon: "/icons/icon-192.png",
```

（理由: manifest（`vite.config.js`）のアイコンは `/icons/icon-192.png`。`icon-192x192.png` は存在しない。）

- [ ] **Step 2: 設定コンポーネントを作成**

`src/components/OverspendNotifySettings.tsx`:

```tsx
// ────────── 使いすぎ通知 設定UI（共通部品） ──────────
// 予算セクションと設定タブの両方に置く。
//  ・オン/オフスイッチ
//  ・未許可なら「通知を許可」ボタン
//  ・許可状態の表示（拒否・非対応の案内）
import { CSSProperties } from "react";
import {
  STYLE_CARD,
  STYLE_BUTTON_OUTLINE,
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_SECONDARY,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
} from "../utils/styles";

const STYLE_ROW: CSSProperties = { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 };

interface OverspendNotifySettingsProps {
  enabled: boolean;                                    // オン/オフ
  onToggle: (value: boolean) => void;                 // スイッチ変更
  permission: NotificationPermission | "unsupported"; // 通知許可状態
  onRequestPermission: () => void;                    // 「通知を許可」ボタン
}

export default function OverspendNotifySettings(props: OverspendNotifySettingsProps) {
  const { enabled, onToggle, permission, onRequestPermission } = props;
  // 通知が実際に届く状態か（オン かつ 許可済み）
  const active = enabled && permission === "granted";

  return (
    <section style={{ ...STYLE_CARD, marginTop: 16 }}>
      <h3 style={{ fontSize: 15, color: COLOR_TEXT_PRIMARY, margin: "0 0 4px" }}>🔔 使いすぎ通知</h3>
      <p style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, margin: "0 0 14px" }}>
        カテゴリの支出が予算の80%・100%を超えたらお知らせします（このアプリを開いている時／開いた時）。
      </p>

      {/* オン/オフ */}
      <label style={{ ...STYLE_ROW, marginBottom: 12, cursor: "pointer" }}>
        <span style={{ fontSize: 13, color: COLOR_TEXT_PRIMARY }}>使いすぎ通知を受け取る</span>
        <input type="checkbox" checked={enabled} onChange={e => onToggle(e.target.checked)} />
      </label>

      {/* 許可の導線・状態表示 */}
      {permission === "unsupported" ? (
        <p style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, margin: 0 }}>
          お使いのブラウザは通知に対応していません。
        </p>
      ) : permission === "denied" ? (
        <p style={{ fontSize: 12, color: COLOR_NEGATIVE, margin: 0 }}>
          通知がブロックされています。ブラウザの設定から許可してください。
        </p>
      ) : permission === "granted" ? (
        <p style={{ fontSize: 12, color: active ? COLOR_POSITIVE : COLOR_TEXT_SECONDARY, margin: 0 }}>
          {active ? "通知は有効です。" : "通知は許可済みです（スイッチをオンにしてください）。"}
        </p>
      ) : (
        <button type="button" style={{ ...STYLE_BUTTON_OUTLINE, width: "100%" }} onClick={onRequestPermission}>
          通知を許可する
        </button>
      )}
    </section>
  );
}
```

- [ ] **Step 3: 設定タブに設置**

`src/App.tsx` の設定タブ、`CloudSyncSection` を描画している箇所の直後に追加：

```tsx
      {tab==="set"&&<OverspendNotifySettings
        enabled={overspendNotifyEnabled}
        onToggle={setOverspendNotifyEnabled}
        permission={notifPermission}
        onRequestPermission={requestPermission}
      />}
```

import を追加：

```tsx
import OverspendNotifySettings from "./components/OverspendNotifySettings";
```

- [ ] **Step 4: 予算セクションに設置**

まず `BudgetSection` の現在の描画場所と props を確認する：

Run: `grep -rn "BudgetSection" src/ --include=*.tsx`

`src/components/BudgetSection.tsx` に props を1つ足して、コンポーネント末尾（最後の `</...>` の直前）に設置する。
`BudgetSectionProps`（28行目付近）に追記：

```tsx
  // 使いすぎ通知の設定（任意。渡された時だけ表示する）
  notifySettings?: {
    enabled: boolean;
    onToggle: (value: boolean) => void;
    permission: NotificationPermission | "unsupported";
    onRequestPermission: () => void;
  };
```

関数引数の分割代入（39行目付近 `function BudgetSection({ budget, setBudget, mTx, prevMTx = [] }`）に `notifySettings` を追加：

```tsx
export default function BudgetSection({ budget, setBudget, mTx, prevMTx = [], notifySettings }: BudgetSectionProps) {
```

ファイル冒頭に import を追加：

```tsx
import OverspendNotifySettings from "./OverspendNotifySettings";
```

`return (...)` の一番外側の閉じタグの直前に挿入：

```tsx
      {notifySettings && (
        <OverspendNotifySettings
          enabled={notifySettings.enabled}
          onToggle={notifySettings.onToggle}
          permission={notifySettings.permission}
          onRequestPermission={notifySettings.onRequestPermission}
        />
      )}
```

そして `BudgetSection` を呼んでいる箇所（Step 4 冒頭の grep で判明した場所）に `notifySettings` を渡す：

```tsx
        notifySettings={{
          enabled: overspendNotifyEnabled,
          onToggle: setOverspendNotifyEnabled,
          permission: notifPermission,
          onRequestPermission: requestPermission,
        }}
```

※ 呼び出し箇所が `App.tsx` 以外（別 View）で `overspendNotifyEnabled` 等を受け取っていない場合は、その View に props を素通しで追加する。最小の変更にとどめる。

- [ ] **Step 5: 型チェック・テスト・ビルド**

Run: `npx tsc --noEmit && npx vitest run && npm run build`
Expected: 型エラー無し、テスト全合格、ビルド成功。

- [ ] **Step 6: Commit**

```bash
git add src/components/OverspendNotifySettings.tsx src/components/BudgetSection.tsx src/App.tsx src/hooks/useNotification.ts
git commit -m "feat(finance_web): 使いすぎ通知の設定UIを予算/設定に追加・通知アイコン修正"
```

---

### Task 4: 本番デプロイ

**Files:** なし（デプロイのみ）

- [ ] **Step 1: 本番デプロイ**

Run: `npx vercel --prod --yes`
Expected: `Aliased: https://financeweb-nine.vercel.app` と `readyState: READY`。

- [ ] **Step 2: フロント疎通確認**

Run: `curl -s -o /dev/null -w "%{http_code}\n" https://financeweb-nine.vercel.app/`
Expected: `200`。

- [ ] **Step 3: 実機での確認（ユーザー作業）**

スマホ/PCで開き、設定タブまたは予算セクションで「使いすぎ通知」をオン→「通知を許可」。予算を設定したカテゴリで支出を80%/100%まで記録し、通知が出ることを確認する。

---

## Self-Review

**Spec coverage:**
- 方式=フォアグラウンド通知 → Task 2（`useNotification` 利用）✓
- 2段階80/100 → Task 1（判定ロジック）✓
- カテゴリ別のみ → Task 1（`budget` のキーを走査）✓
- 月1回ずつ重複防止 → Task 1（`NotifyLog`）＋ Task 2（保存）✓
- タイミング（記録時/起動時） → Task 2（effect の依存に `actualByCategory`、初回マウント実行）✓
- 基準月=実際の今月 → Task 2 Step 3（`today` で当月集計）✓
- UI 2箇所 → Task 3（設定タブ＋予算セクション）✓
- 端末ローカル・非同期 → `kk_notify_overspend_enabled`（usePersist）/ `kk_notify_overspend_log`（直接localStorage）、`SYNC_KEYS` 不変更 ✓
- まとめ通知 → Task 2（alerts.length>1）✓
- テスト（境界/月またぎ/重複/未設定/prune） → Task 1 ✓
- 非対象（Web Push/総予算/％設定） → 計画に含めない ✓

**Placeholder scan:** プレースホルダ無し。すべて実コードを記載。`formatYen` のみ Task 2 Step 2 で名称を確認するガードを設置済み。`BudgetSection` の呼び出し場所は Task 3 Step 4 で grep 確認する手順を明記。

**Type consistency:** `OverspendAlert` / `NotifyLog` は Task 1 で定義し Task 2 で使用。`UseOverspendAlertsDeps` は Task 2 で定義・使用。`OverspendNotifySettingsProps` は Task 3 で定義・両設置箇所で同じ形。`permission` の型は全箇所 `NotificationPermission | "unsupported"` で統一。
