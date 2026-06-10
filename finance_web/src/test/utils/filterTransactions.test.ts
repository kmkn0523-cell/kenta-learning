import { describe, it, expect } from "vitest";
import { filterAndSortTransactions, TransactionFilter } from "../../utils/filterTransactions";
import { Tx } from "../../types";

// テスト用のダミーデータ
const items: Tx[] = [
  { id: "1", date: "2026-05-01", category: "食費", amount: 1000, memo: "スーパー" },
  { id: "2", date: "2026-05-10", category: "交通費", amount: 500, memo: "電車" },
  { id: "3", date: "2026-05-20", category: "食費", amount: 3000, memo: "レストラン" },
  { id: "4", date: "2026-04-15", category: "娯楽費", amount: 2000, memo: "映画" },
  { id: "5", date: "2026-05-05", category: "食費", amount: 800, memo: "" },
];

describe("filterAndSortTransactions", () => {
  it("フィルターなしで全件返す", () => {
    expect(filterAndSortTransactions(items, {})).toHaveLength(5);
  });

  it("メモのテキスト検索", () => {
    const result = filterAndSortTransactions(items, { text: "スーパー" });
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("1");
  });

  it("カテゴリのテキスト検索", () => {
    const result = filterAndSortTransactions(items, { text: "交通" });
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("2");
  });

  it("複数カテゴリでフィルター", () => {
    const result = filterAndSortTransactions(items, { categories: ["食費", "娯楽費"] });
    expect(result).toHaveLength(4);
  });

  it("日付範囲でフィルター", () => {
    const result = filterAndSortTransactions(items, { dateFrom: "2026-05-01", dateTo: "2026-05-10" });
    expect(result).toHaveLength(3);
  });

  it("金額範囲でフィルター", () => {
    const result = filterAndSortTransactions(items, { amountMin: 1000, amountMax: 2000 });
    expect(result).toHaveLength(2);
  });

  it("金額昇順でソート", () => {
    const result = filterAndSortTransactions(items, { sortBy: "amount", sortDir: "asc" });
    expect(result[0].amount).toBe(500);
    expect(result[4].amount).toBe(3000);
  });

  it("日付降順でソート", () => {
    const result = filterAndSortTransactions(items, { sortBy: "date", sortDir: "desc" });
    expect(result[0].date).toBe("2026-05-20");
    expect(result[4].date).toBe("2026-04-15");
  });

  it("テキスト検索と日付範囲の組み合わせ", () => {
    // 食費カテゴリ（id=1,3,5）のうち 2026-05-01 以降（3件すべて該当）
    const result = filterAndSortTransactions(items, { text: "食費", dateFrom: "2026-05-01" });
    expect(result).toHaveLength(3);
  });
});
