// ────────── 取引の絞り込み・並び替え（Income/Tx 両方で使える汎用版） ──────────
import { Tx } from "../types";

// フィルター条件をまとめた型
export interface TransactionFilter {
  text?: string;         // メモ・カテゴリのキーワード検索
  categories?: string[]; // カテゴリ名の配列（空の場合は全件）
  dateFrom?: string;     // 開始日（YYYY-MM-DD）
  dateTo?: string;       // 終了日（YYYY-MM-DD）
  amountMin?: number;    // 金額の下限
  amountMax?: number;    // 金額の上限
  sortBy?: "date" | "amount"; // 並び替えの基準
  sortDir?: "asc" | "desc";   // 昇順 or 降順
}

// date/category/amount/memoを持つ任意の型に使える汎用フィルター関数
export function filterAndSortItems<T extends { date: string; category: string; amount: number; memo?: string }>(
  items: T[],
  filter: TransactionFilter
): T[] {
  // テキスト検索用に小文字化しておく
  const text = filter.text?.toLowerCase().trim();

  let result = items.filter(item => {
    // キーワード検索：メモかカテゴリに含まれているか確認
    if (text) {
      const memoMatch = (item.memo || "").toLowerCase().includes(text);
      const categoryMatch = item.category.toLowerCase().includes(text);
      if (!memoMatch && !categoryMatch) return false;
    }
    // カテゴリフィルター：指定カテゴリに含まれているか確認
    if (filter.categories && filter.categories.length > 0) {
      if (!filter.categories.includes(item.category)) return false;
    }
    // 日付フィルター：開始日より前はスキップ
    if (filter.dateFrom && item.date < filter.dateFrom) return false;
    // 日付フィルター：終了日より後はスキップ
    if (filter.dateTo && item.date > filter.dateTo) return false;
    // 金額フィルター：下限より小さいものはスキップ
    if (filter.amountMin !== undefined && item.amount < filter.amountMin) return false;
    // 金額フィルター：上限より大きいものはスキップ
    if (filter.amountMax !== undefined && item.amount > filter.amountMax) return false;
    return true;
  });

  // 並び替え処理
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

// Tx専用の薄いラッパー（既存の呼び出し元との互換性のために残す）
export function filterAndSortTransactions(items: Tx[], filter: TransactionFilter): Tx[] {
  return filterAndSortItems(items, filter);
}
