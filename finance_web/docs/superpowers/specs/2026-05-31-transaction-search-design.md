# 横断検索タブ「🔍 検索」 設計書

- 日付: 2026-05-31
- 対象: `finance_web`（BYB / Vite + React + TypeScript PWA）
- アプローチ: A（土台を軽く整えてから、価値の高い新機能を1つ）

## 1. 目的と背景

家計簿アプリ `finance_web` には現在、収入・固定費・支出・ローンがそれぞれ別タブに分かれており、
「特定のキーワード」「特定の期間」「特定の金額帯」の取引を**タブをまたいで一覧する手段がない**。
本機能は、収入(Income)と変動支出(Tx)を**横断的に検索・絞り込み・集計**する新タブを追加する。

副次目的として、絞り込みのロジックを**純粋関数**（画面やlocalStorageに依存しない計算だけの関数）に
切り出し、ユニットテストで品質を担保する。これが「土台を整える」部分にあたる。

## 2. スコープ

### やること
- 8番目のタブ「🔍 検索」を**遅延ロード**（lazy）で追加する
- 検索対象は **変動支出(Tx) と 収入(Income)** の2種類
- 絞り込み条件: キーワード / 種別 / カテゴリ(複数) / 期間 / 金額帯 / 口座 / 並び替え
- 結果は **サマリー（件数・収入計・支出計・差引）＋ 一覧** で表示
- 絞り込みは**純粋関数 `filterTransactions()`** に切り出し、ユニットテストを付ける

### やらないこと（YAGNI）
- 検索結果からの編集・削除（v1では表示のみ）
- 新しい localStorage キーの追加（永続データは増やさない）
- 固定費(FixedExpense)・ローン(Loan)の検索対象化（v1では対象外）
- recharts のチャンク分割や `@types/react` v19不一致の修正（本件と無関係なので別件）

## 3. データ

新しく**永続化するデータはない**。既存の `Tx` / `Income` をそのまま読む。

- `Tx`: `{ id, date:"YYYY-MM-DD", category, amount, memo, accountId? }`
- `Income`: `{ id, date:"YYYY-MM-DD", category, amount, memo, accountId? }`

検索処理の内部だけで使う型を新設する（メモリ上のみ・永続化しない）:

```ts
export interface SearchCriteria {
  keyword: string;
  kind: "all" | "income" | "expense";
  categories: string[];
  dateFrom: string;      // "YYYY-MM-DD"（空なら下限なし）
  dateTo: string;        // "YYYY-MM-DD"（空なら上限なし）
  amountMin: number | null;
  amountMax: number | null;
  accountId: string;     // 空なら全口座
  sort: "dateDesc" | "amountDesc";
}

export interface SearchResultItem {
  id: string;
  kind: "income" | "expense";
  date: string;
  category: string;
  amount: number;        // 常に正の絶対値。符号は kind で表す
  memo: string;
  accountId?: string;
}

export interface SearchSummary {
  count: number;
  incomeTotal: number;
  expenseTotal: number;
  net: number;           // incomeTotal − expenseTotal
}
```

## 4. コンポーネント構成

- `src/utils/searchFilter.ts`（新規）— 純粋関数と型。`filterTransactions()` / `summarizeResults()` / `normalizeToResults()` / `emptyCriteria()`
- `src/utils/searchFilter.test.ts`（新規）— 上記のユニットテスト
- `src/views/SearchView.tsx`（新規）— 検索タブ本体。状態を持ち、純粋関数を呼んで描画
- `src/components/SearchFilters.tsx`（新規）— 絞り込み条件の入力UI（制御コンポーネント）
- `src/components/SearchResultRow.tsx`（新規）— 結果1件の表示
- `src/App.tsx`（既存・最小変更）— タブ配列に `["search","🔍","検索"]` 追加、`SearchView` を lazy import、表示分岐に枝を追加

## 5. データフロー

```
App.tsx（transactions / incomes / accounts / categories を保持）
  └─ SearchView（criteria を useState で保持）
       ├─ SearchFilters（criteria を編集 → onChange で SearchView に返す）
       ├─ useMemo: filterTransactions(transactions, incomes, criteria) → results
       ├─ useMemo: summarizeResults(results) → summary
       └─ results.map → SearchResultRow
```

## 6. 絞り込みロジック（filterTransactions）

1. `Tx` を `kind:"expense"`、`Income` を `kind:"income"` に正規化（`amount` は絶対値）
2. 種別: `kind !== "all"` なら種別一致のみ
3. キーワード: 空でなければ memo か category に部分一致（小文字化して比較）
4. カテゴリ: 配列が空でなければ含まれるもののみ
5. 期間: `"YYYY-MM-DD"` の文字列比較で from/to を境界含めて判定
6. 金額: min/max を境界含めて判定
7. 口座: 空でなければ accountId 一致のみ
8. 並び替え: `dateDesc`（日付の新しい順）または `amountDesc`（金額の大きい順）

すべての条件は **AND** で重ねる。

## 7. エラーハンドリング

- 該当0件 → 空配列を返し、画面は空状態メッセージを表示（クラッシュさせない）
- `from > to` のような矛盾した期間 → 結果0件として扱う（例外を投げない）
- カテゴリ/口座が削除済みで結果に残る場合 → 名前が引けなければ省略表示
- 金額入力は数値のみ・負数を弾く（UI側でバリデーション）

## 8. テスト方針

`searchFilter.test.ts` で純粋関数を網羅的にテストする（UIテストは書かない）:
- キーワード（メモ/カテゴリ/大小無視/部分一致/空で全件）
- 種別（all/income/expense）
- カテゴリ（単一/複数/空で全件）
- 期間（開始のみ/終了のみ/両方/境界）
- 金額（min/max/両方/境界）
- 口座（一致/空で全件）
- AND結合・並び替え（dateDesc/amountDesc）・サマリー計算・0件

## 9. UI仕様

- 上部: サマリーバー（件数・収入計・支出計・差引を色分け表示）
- 中部: `SearchFilters`（キーワード入力、種別3択、カテゴリチップ、期間＋クイック選択、金額min-max、口座選択、並び替え切替）
- 下部: 結果一覧（`SearchResultRow` を並べる。収入=緑/支出=赤のバッジ）
- 既存のダークテーマ・グラスモーフィズムに合わせる

## 10. 受け入れ条件

- [ ] 「🔍 検索」タブが表示され、開くと全件（収入＋支出）が新しい順で出る
- [ ] キーワード・種別・カテゴリ・期間・金額・口座で正しく絞り込める
- [ ] 複数条件を重ねると AND で絞り込まれる
- [ ] サマリーが結果に連動して正しく計算される
- [ ] 並び替え（日付順/金額順）が効く
- [ ] 0件のとき空状態メッセージが出てクラッシュしない
- [ ] `npm run test` が全件パス（既存103件＋新規）
- [ ] `npm run build` と `tsc --noEmit` が成功する
