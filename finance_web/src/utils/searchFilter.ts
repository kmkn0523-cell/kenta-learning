// ────────── 横断検索（収入Income＋変動支出Tx をまたいで絞り込む） ──────────
// 画面やlocalStorageに依存しない「計算だけ」の純粋関数を集めたファイル
import { Tx, Income } from "../types";
// 既存の汎用フィルター関数を再利用する（キーワード/カテゴリ/期間/金額/並び替え）
import { filterAndSortItems } from "./filterTransactions";

// 検索条件をまとめた型（メモリ上だけで使う・保存はしない）
export interface SearchCriteria {
  keyword: string;                          // メモ・カテゴリのキーワード
  kind: "all" | "income" | "expense";       // 種別（全部 / 収入 / 支出）
  categories: string[];                     // カテゴリ名の配列（空なら全件）
  dateFrom: string;                         // 開始日 "YYYY-MM-DD"（空なら下限なし）
  dateTo: string;                           // 終了日 "YYYY-MM-DD"（空なら上限なし）
  amountMin: number | null;                 // 金額の下限（nullなら下限なし）
  amountMax: number | null;                 // 金額の上限（nullなら上限なし）
  accountId: string;                        // 口座ID（空なら全口座）
  sort: "dateDesc" | "amountDesc";          // 並び替え（日付の新しい順 / 金額の大きい順）
}

// 検索結果1件の形（Tx と Income を同じ形にそろえたもの）
export interface SearchResultItem {
  id: string;                  // 元データのID
  kind: "income" | "expense";  // 収入か支出か
  date: string;                // 日付 "YYYY-MM-DD"
  category: string;            // カテゴリ名
  amount: number;              // 常に正の絶対値（符号は kind で表す）
  memo: string;                // メモ
  accountId?: string;          // 紐づく口座ID（任意）
}

// 検索結果の集計値の形
export interface SearchSummary {
  count: number;          // 件数
  incomeTotal: number;    // 収入の合計
  expenseTotal: number;   // 支出の合計
  net: number;            // 差引（収入合計 − 支出合計）
}

// 何も絞り込んでいない初期状態の検索条件を返す
export function emptyCriteria(): SearchCriteria {
  return {
    keyword: "",          // キーワードは空
    kind: "all",          // 種別は全部
    categories: [],       // カテゴリ指定なし
    dateFrom: "",         // 開始日なし
    dateTo: "",           // 終了日なし
    amountMin: null,      // 下限なし
    amountMax: null,      // 上限なし
    accountId: "",        // 全口座
    sort: "dateDesc",     // 既定は日付の新しい順
  };
}

// Tx と Income を「同じ形（SearchResultItem）」にそろえる
export function normalizeToResults(transactions: Tx[], incomes: Income[]): SearchResultItem[] {
  // 変動支出は kind="expense"、金額は絶対値にする
  const expenseItems: SearchResultItem[] = transactions.map((tx) => ({
    id: tx.id,
    kind: "expense",
    date: tx.date,
    category: tx.category,
    amount: Math.abs(tx.amount),  // マイナスで入っていても正に直す
    memo: tx.memo,
    accountId: tx.accountId,
  }));
  // 収入は kind="income"、金額は絶対値にする
  const incomeItems: SearchResultItem[] = incomes.map((income) => ({
    id: income.id,
    kind: "income",
    date: income.date,
    category: income.category,
    amount: Math.abs(income.amount),
    memo: income.memo,
    accountId: income.accountId,
  }));
  // 2つを1つの配列にまとめて返す
  return [...expenseItems, ...incomeItems];
}

// 検索条件にあう取引だけを絞り込んで並び替える（横断検索の本体）
export function filterTransactions(
  transactions: Tx[],
  incomes: Income[],
  criteria: SearchCriteria
): SearchResultItem[] {
  // まず Tx と Income を同じ形にそろえる
  let items = normalizeToResults(transactions, incomes);

  // 種別で絞り込む（"all" のときは絞り込まない）
  if (criteria.kind !== "all") {
    items = items.filter((item) => item.kind === criteria.kind);
  }

  // 口座で絞り込む（空のときは全口座）
  if (criteria.accountId) {
    items = items.filter((item) => item.accountId === criteria.accountId);
  }

  // 残りの共通条件（キーワード/カテゴリ/期間/金額/並び替え）は既存の汎用関数に任せる
  return filterAndSortItems(items, {
    text: criteria.keyword,                                   // キーワード
    categories: criteria.categories,                         // カテゴリ配列
    dateFrom: criteria.dateFrom || undefined,               // 空文字は「指定なし」に変換
    dateTo: criteria.dateTo || undefined,                   // 空文字は「指定なし」に変換
    amountMin: criteria.amountMin ?? undefined,             // null は「指定なし」に変換
    amountMax: criteria.amountMax ?? undefined,             // null は「指定なし」に変換
    sortBy: criteria.sort === "amountDesc" ? "amount" : "date", // 並び替えの基準
    sortDir: "desc",                                        // 検索では常に降順（新しい順 / 大きい順）
  });
}

// 検索結果から集計値（件数・収入計・支出計・差引）を計算する
export function summarizeResults(results: SearchResultItem[]): SearchSummary {
  // 収入だけ合計する
  const incomeTotal = results
    .filter((item) => item.kind === "income")
    .reduce((sum, item) => sum + item.amount, 0);
  // 支出だけ合計する
  const expenseTotal = results
    .filter((item) => item.kind === "expense")
    .reduce((sum, item) => sum + item.amount, 0);
  // 集計結果をまとめて返す
  return {
    count: results.length,            // 件数
    incomeTotal,                      // 収入の合計
    expenseTotal,                     // 支出の合計
    net: incomeTotal - expenseTotal,  // 差引
  };
}
