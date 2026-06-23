# 使いすぎアラート（フォアグラウンド通知）設計書

作成日: 2026-06-23
対象アプリ: finance_web（BYB — Before You Broke）

## 目的

予算に対して支出が増えてきた時、ユーザーが「使いすぎる前に気づける」ようにする。
アプリ名のコンセプト（Before You Broke）に直結する継続率施策。

## 前提と制約

- データは E2E 暗号化（サーバは中身を読めない）。よって「予算の何%か」をサーバで判定できない。
  → サーバ起点のプッシュ（閉じている間に鳴らす）は採用しない。
- 既存資産: `src/hooks/useNotification.ts`（Web Notification API・フォアグラウンドのみ）、
  `src/components/BudgetSection.tsx`（80%超のアプリ内警告UI）、予算 `kk_budget: Record<string, number>`。

## 確定した仕様

| 項目 | 決定 |
|---|---|
| 方式 | フォアグラウンド通知（既存 `useNotification` を活用、E2E維持） |
| 閾値 | 2段階：80%「注意」／100%「オーバー」 |
| 対象 | カテゴリ別のみ（予算が設定済み＝0より大きいカテゴリ） |
| 頻度 | 各カテゴリ × 各段階、当月1回ずつ（翌月リセット） |
| タイミング | 支出記録時／アプリ起動時（＝当月のカテゴリ別支出が変わった時） |
| 基準月 | 常に「実際の今月」。画面で閲覧中の月タブとは無関係 |
| UI | 予算セクション内＋設定タブ（⚙️）の両方 |
| 保存 | すべて端末ローカル・**同期しない**（通知は端末ごとの事情のため） |

## アーキテクチャ

### 1. 純粋な判定関数（React非依存）

新規ファイル `src/utils/overspendAlerts.ts`

```ts
// 1件のアラート
export interface OverspendAlert {
  category: string;   // 例: "食費"
  level: 80 | 100;    // 段階
  spent: number;      // 当月の支出
  budget: number;     // 予算
  ratio: number;      // spent / budget（0.85 など）
}

// 通知ログ: 月 -> ["食費|80","食費|100", ...]
export type NotifyLog = Record<string, string[]>;

// 当月の状況から「新たに鳴らすべきアラート」と「更新後ログ」を返す純粋関数。
// actual: { カテゴリ: 当月支出 } / budget: { カテゴリ: 予算 } / month: "YYYY-MM"
export function evaluateOverspend(
  actual: Record<string, number>,
  budget: Record<string, number>,
  log: NotifyLog,
  month: string
): { alerts: OverspendAlert[]; nextLog: NotifyLog };

// 古い月のログを落とす（当月のみ残す）
export function pruneLog(log: NotifyLog, month: string): NotifyLog;
```

判定ルール:
- 予算 `budget[cat] > 0` のカテゴリのみ対象。
- `ratio = spent / budget`。`ratio >= 1.0` なら level=100、`ratio >= 0.8` なら level=80。
- 同月・同カテゴリ・同レベルが既に `log[month]` に有れば鳴らさない（重複防止）。
- 100%に達した時、その月にまだ80%通知をしていなくても、**100%だけ**鳴らせばよい
  （80%もログに記録済み扱いにして二重通知を防ぐ）。
- 戻り値 `nextLog` には今回鳴らしたものを追記。

### 2. フック

新規ファイル `src/hooks/useOverspendAlerts.ts`

入力（依存）:
- `enabled: boolean`（設定スイッチ）
- `actualByCategory: Record<string, number>`（当月のカテゴリ別支出）
- `budget: Record<string, number>`
- `notify(title, body)`（`useNotification` 由来）
- `permission`（granted の時だけ実際に通知）

挙動:
- `enabled && permission === "granted"` の時のみ動作。
- `actualByCategory` が変わるたび（＝支出記録時）と初回マウント時（＝アプリ起動時）に
  `evaluateOverspend` を実行。
- 返ったアラートを通知:
  - 1件 → カテゴリ別の具体的な通知。
  - 2件以上（起動時に複数該当など）→ 連発を避けて1件に集約
    （例: 「3件のカテゴリが予算に近づいています／超えています」）。
- `nextLog` を `pruneLog` して localStorage に保存。
- localStorage キー: `kk_notify_overspend_log`。

### 3. 設定UI（共通部品）

新規ファイル `src/components/OverspendNotifySettings.tsx`

- 「使いすぎ通知」オン/オフスイッチ（`kk_notify_overspend_enabled`）。
- 未許可なら「通知を許可」ボタン → `requestPermission()`。
- 状態表示: 許可済み／拒否（ブラウザ設定から変更する旨の案内）／非対応。
- 予算セクション（`BudgetSection.tsx`）と設定タブ（`App.tsx` の `tab==="set"`）の両方で使う。

### 4. 当月カテゴリ別支出の算出

- 「実際の今月」（`new Date()` の年月）で変動支出トランザクションをカテゴリ集計する memo を
  `App.tsx` に用意（既存の月別集計ロジックを踏襲。閲覧中の selectedMonth とは別に当月固定で計算）。
- これを `useOverspendAlerts` に渡す。

## データフロー

```
取引追加 / アプリ起動
  → 当月カテゴリ別支出(memo) 変化
  → useOverspendAlerts effect
  → evaluateOverspend(actual, budget, log, month)
  → 新規アラートを notify()（1件=個別 / 複数=集約）
  → nextLog を pruneして localStorage 保存
```

## 永続化キー（すべて端末ローカル・同期対象外）

| キー | 内容 | 既定 |
|---|---|---|
| `kk_notify_overspend_enabled` | 通知オン/オフ | `false` |
| `kk_notify_overspend_log` | `{ "YYYY-MM": ["cat|level", ...] }` | `{}` |

`SYNC_KEYS`（`syncState.ts`）には追加しない。

## エラー・エッジケース

- 予算0/未設定カテゴリは対象外。`budget>0` ガードでゼロ除算なし。
- `notify()` は非対応・未許可なら何もしない（既存仕様）。
- 予算を後から下げても、同月の同レベルは再通知しない（ログで抑制）。
- 月替わり: ログは月キーで管理し、`pruneLog` で古い月を削除。
- 初回オン時に既に複数カテゴリ超過 → 集約通知1件で連発を防ぐ。

## テスト（TDD）

`src/utils/overspendAlerts.test.ts`（純粋関数を中心に）:
- 80%境界（79%→鳴らない／80%→鳴る）
- 100%境界（100%で level=100、80%は同時にログ済み化して二重通知しない）
- 同月同レベルの重複防止
- 月またぎでリセット（翌月は再び鳴る）
- 予算未設定カテゴリは除外
- `pruneLog` が当月以外を消す

## 非対象（YAGNI）

- 閉じている間のプッシュ（Web Push基盤）— E2Eと矛盾するため対象外。
- 通知%のユーザー設定 — 当面は80/100固定。
- 月の総予算アラート — カテゴリ別のみ。
- 通知のスケジュール送信 / 定期実行。
