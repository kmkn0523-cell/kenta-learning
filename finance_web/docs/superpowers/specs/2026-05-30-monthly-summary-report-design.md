# 月次サマリーレポート機能 設計書

作成日: 2026-05-30
対象: finance_web（家計簿PWA「BYB」）

## 目的

その月の家計を1画面にまとめて振り返れる「月次サマリー」を新タブとして追加する。
収入・支出・貯蓄率・カテゴリ内訳に加え前月比を表示し、PNG画像とCSVで書き出せるようにする。

## スコープ

### 含めるもの（必須）
- 収入合計
- 支出合計（変動＋固定＋ローン返済。ダッシュボードの `totalBurden` と同じ定義）
- 手残り（net = 収入合計 − 支出合計）
- 貯蓄率
- カテゴリ内訳（支出カテゴリ別の金額リスト・降順）
- 前月比（収入・支出・貯蓄率を前月と比較）
- PNG画像書き出し
- CSV書き出し

### 含めないもの（今回見送り）
- カテゴリ内訳の円グラフ表示（金額リストのみ）
- 上位支出3件
- 予算達成状況

## 計算定義

- 貯蓄率 = 手残り(net) ÷ 収入合計 × 100。収入合計が0のときは 0%。小数第1位まで表示。
- 前月比 = 当月値 − 前月値。プラスは `↑+5,000円`（緑）、マイナスは `↓-2,000円`（赤）、同額は `±0`（グレー）。
  貯蓄率の前月比は `↑+3.2pt` のようにポイント差で表示。
- カテゴリ内訳 = 当月の変動支出をカテゴリ名でグルーピングし金額合計、降順ソート。

## アーキテクチャ（案A: 専用ビュー＋Appで集計）

集計値は `App.tsx` 側で計算して表示専用の `SummaryView` に props で渡す。
稼働中の `DashboardView` には手を入れない。

```
App.tsx
 ├─ 当月集計（既存の totalIncome / totalBurden / net を流用）
 ├─ 前月集計（前月の収入合計・支出合計・貯蓄率を新たに算出）
 ├─ カテゴリ内訳（当月 transactions をカテゴリ別集計）
 └─ <SummaryView ...props /> （lazy + Suspense）
        ├─ レポート本体DOM（ref で掴む）
        ├─ 「画像で保存」ボタン → summaryExport.exportSummaryImage(ref)
        └─ 「CSVで保存」ボタン → summaryExport.exportSummaryCsv(集計値)
```

## コンポーネント・モジュール

### 新規: `src/views/SummaryView.tsx`
- 役割: 月次サマリーの表示と書き出しボタン。表示専用、集計はしない。
- props:
  - `monthLabel: string`（例 "2026年5月"）
  - `current: SummaryStats`（当月の集計値）
  - `previous: SummaryStats | null`（前月の集計値。データなしは null）
  - `categoryBreakdown: { category: string; amount: number }[]`（降順）
  - `showT: (msg: string, type?: string) => void`（トースト用）
- 依存: `utils/summaryExport`、`utils/format`（formatYen）、`utils/styles`

### 新規: `src/utils/summaryExport.ts`
- `buildSummaryCsv(monthLabel, current, previous, categoryBreakdown): string`
  - `項目,金額` の縦持ちCSV文字列を返す（純粋関数・テスト対象）
- `exportSummaryCsv(...)`: 上記を `downloadFile`（既存）で保存
- `exportSummaryImage(node: HTMLElement, fileName: string): Promise<void>`
  - `html2canvas(node)` → `canvas.toBlob` → URL 経由で PNG ダウンロード

### 新規: 型 `SummaryStats`（`src/types.ts` に追記）
```ts
export interface SummaryStats {
  income: number;     // 収入合計
  expense: number;    // 支出合計（変動＋固定＋返済）
  net: number;        // 手残り
  savingRate: number; // 貯蓄率（%）
}
```

### 変更: `src/App.tsx`（最小限）
- タブ定数に「サマリー」を追加
- `SummaryView` を `lazy` インポートし `Suspense` でレンダー
- 前月集計とカテゴリ内訳を `useMemo` で算出して渡す
- 関係ない既存処理は変更しない

### 変更: タブバー（ナビ）
- 「サマリー」タブ項目を1つ追加（アイコン例 📊）

## データフロー

1. ユーザーが「サマリー」タブを選択
2. App が選択月の `transactions` / `incomes` / 固定費 / ローンから当月・前月の集計を算出
3. `SummaryView` が props を受け取り表示
4. 「画像で保存」→ レポートDOMを `html2canvas` で PNG 化して保存
5. 「CSVで保存」→ 集計値を縦持ちCSVにして保存

## エラーハンドリング

- 収入合計0での貯蓄率は 0%（ゼロ除算を回避）
- 前月データが無い場合は前月比を非表示（`previous` が null）
- `html2canvas` 失敗時は try/catch でトースト「画像の保存に失敗しました」
- カテゴリ内訳が空（支出0）の場合は「支出がありません」表示

## テスト（vitest）

`src/utils/summaryExport.test.ts`
- `buildSummaryCsv` が正しい縦持ちCSVを返す
- 収入0のとき貯蓄率0%でゼロ除算しない

集計ロジック（前月比・カテゴリ内訳）を純粋関数に切り出してテスト可能にする。
（画像書き出しは jsdom で canvas が動かないため自動テスト対象外。手動確認とする）

## 新規ライブラリ

- `html2canvas`（DOM→画像化）。実装着手時に `npm install` の承認を得る。

## 既存資産の再利用

- `utils/format.ts` の `formatYen` / `MONTH_LABELS`
- `utils/dataExport.ts` の `downloadFile`
- `utils/styles.ts` のスタイル定数
- ダッシュボードの集計定義（`totalIncome` / `totalBurden` / `net`）と整合させる
