# 実装計画：横断検索タブ「🔍 検索」

対象設計書: `docs/superpowers/specs/2026-05-31-transaction-search-design.md`
作成日: 2026-05-31 / 状態: 実装完了

## 目的
収入(Income)と変動支出(Tx)をまたいで、キーワード・種別・カテゴリ・期間・金額帯・口座で
絞り込み、集計（件数/収入計/支出計/差引）しながら一覧確認できる読み取り専用タブを追加する。

## 設計方針
- 純粋関数のコア（`searchFilter.ts`）をTDDで先に固め、UIは薄く乗せる
- 既存の汎用フィルタ `filterAndSortItems<T>()`（`filterTransactions.ts`）を再利用しDRYを保つ
  - `null`→`undefined` を `?? undefined` で橋渡し
  - `sort:"dateDesc"|"amountDesc"` を `{sortBy, sortDir}` に変換して委譲
- 画面は表示専用（編集は各タブで行う）

## 成果物
| ファイル | 役割 |
|---|---|
| `src/utils/searchFilter.ts` | 純粋関数コア（正規化・絞り込み・集計） |
| `src/utils/searchFilter.test.ts` | コアのユニットテスト（23件） |
| `src/components/SearchResultRow.tsx` | 結果1件の表示行（読み取り専用） |
| `src/components/SearchFilters.tsx` | 絞り込み条件の入力UI（制御コンポーネント） |
| `src/views/SearchView.tsx` | 検索画面本体（状態保持・集計・一覧） |
| `src/App.tsx` | lazy import・`tab==="search"` 分岐・ナビ配列に「🔍 検索」追加 |

## 実装ステップ（実施済み）
1. `searchFilter.ts` の型と純粋関数をTDDで実装（23テスト緑）
2. 表示部品 `SearchResultRow` / 入力部品 `SearchFilters` を作成
3. 画面本体 `SearchView` を作成（サマリーバー＋条件フォーム＋結果一覧＋空状態）
4. `App.tsx` に3点統合（lazy import / tab分岐 / ナビ配列）
5. 検証：`tsc --noEmit` エラーなし、`npm run test` 126 passed、`npm run build` 成功

## 検証結果
- 型チェック: エラーなし
- テスト: 13ファイル / 126件 passed
- ビルド: 成功（precache 23→25エントリ、検索系チャンク追加）

## 非対象（YAGNI）
- 検索条件の永続化（タブを離れるとリセット）
- 固定費(fixedExpenses)・ローンの検索対象化
- 検索結果からの直接編集
