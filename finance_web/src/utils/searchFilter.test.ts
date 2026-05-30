// ────────── 横断検索の純粋関数テスト ──────────
import { describe, it, expect } from "vitest";
import { Tx, Income } from "../types";
import {
  filterTransactions,
  normalizeToResults,
  summarizeResults,
  emptyCriteria,
  SearchCriteria,
} from "./searchFilter";

// テスト用の変動支出データ（4件）
const txs: Tx[] = [
  { id: "t1", date: "2026-05-18", category: "食費", amount: 1200, memo: "ランチ", accountId: "wallet" },
  { id: "t2", date: "2026-05-10", category: "食費", amount: 5000, memo: "外食ディナー", accountId: "bank" },
  { id: "t3", date: "2026-04-30", category: "日用品", amount: 800, memo: "洗剤", accountId: "wallet" },
  { id: "t4", date: "2026-05-25", category: "趣味", amount: 30000, memo: "ゲーム機", accountId: "card" },
];

// テスト用の収入データ（2件）
const incomes: Income[] = [
  { id: "i1", date: "2026-05-15", category: "給与", amount: 250000, memo: "5月給与", accountId: "bank" },
  { id: "i2", date: "2026-05-20", category: "副業", amount: 30000, memo: "ライティング", accountId: "bank" },
];

// 条件を一部だけ上書きしたSearchCriteriaを作るヘルパー
function criteria(over: Partial<SearchCriteria>): SearchCriteria {
  return { ...emptyCriteria(), ...over };
}

// IDの配列に変換するヘルパー（結果の確認に使う）
function ids(items: { id: string }[]): string[] {
  return items.map((item) => item.id);
}

describe("normalizeToResults", () => {
  it("TxとIncomeを6件に正規化し、金額は絶対値になる", () => {
    const result = normalizeToResults(txs, incomes);
    expect(result).toHaveLength(6);
    expect(result.every((item) => item.amount > 0)).toBe(true);
  });

  it("マイナス金額も絶対値に直す", () => {
    const result = normalizeToResults([{ id: "x", date: "2026-05-01", category: "食費", amount: -500, memo: "", accountId: "wallet" }], []);
    expect(result[0].amount).toBe(500);
  });
});

describe("filterTransactions", () => {
  it("条件なしなら全件（6件）", () => {
    expect(filterTransactions(txs, incomes, emptyCriteria())).toHaveLength(6);
  });

  it("キーワード：メモに部分一致", () => {
    const r = filterTransactions(txs, incomes, criteria({ keyword: "ディナー" }));
    expect(ids(r)).toEqual(["t2"]);
  });

  it("キーワード：カテゴリに部分一致", () => {
    const r = filterTransactions(txs, incomes, criteria({ keyword: "食費" }));
    expect(ids(r).sort()).toEqual(["t1", "t2"]);
  });

  it("キーワード：大文字小文字を無視（英字）", () => {
    const r = filterTransactions(
      [{ id: "e1", date: "2026-05-01", category: "Food", amount: 100, memo: "", accountId: "wallet" }],
      [],
      criteria({ keyword: "food" })
    );
    expect(ids(r)).toEqual(["e1"]);
  });

  it("種別：収入だけ（2件）", () => {
    const r = filterTransactions(txs, incomes, criteria({ kind: "income" }));
    expect(ids(r).sort()).toEqual(["i1", "i2"]);
  });

  it("種別：支出だけ（4件）", () => {
    const r = filterTransactions(txs, incomes, criteria({ kind: "expense" }));
    expect(r).toHaveLength(4);
  });

  it("カテゴリ：単一指定", () => {
    const r = filterTransactions(txs, incomes, criteria({ categories: ["趣味"] }));
    expect(ids(r)).toEqual(["t4"]);
  });

  it("カテゴリ：複数指定", () => {
    const r = filterTransactions(txs, incomes, criteria({ categories: ["趣味", "給与"] }));
    expect(ids(r).sort()).toEqual(["i1", "t4"]);
  });

  it("期間：開始日のみ（境界含む）", () => {
    const r = filterTransactions(txs, incomes, criteria({ dateFrom: "2026-05-18", kind: "expense" }));
    expect(ids(r).sort()).toEqual(["t1", "t4"]);
  });

  it("期間：終了日のみ（境界含む）", () => {
    const r = filterTransactions(txs, incomes, criteria({ dateTo: "2026-04-30", kind: "expense" }));
    expect(ids(r)).toEqual(["t3"]);
  });

  it("期間：両方指定", () => {
    const r = filterTransactions(txs, incomes, criteria({ dateFrom: "2026-05-01", dateTo: "2026-05-20", kind: "expense" }));
    expect(ids(r).sort()).toEqual(["t1", "t2"]);
  });

  it("金額：下限（境界含む）", () => {
    const r = filterTransactions(txs, incomes, criteria({ amountMin: 5000, kind: "expense" }));
    expect(ids(r).sort()).toEqual(["t2", "t4"]);
  });

  it("金額：上限（境界含む）", () => {
    const r = filterTransactions(txs, incomes, criteria({ amountMax: 1200, kind: "expense" }));
    expect(ids(r).sort()).toEqual(["t1", "t3"]);
  });

  it("金額：両方指定", () => {
    const r = filterTransactions(txs, incomes, criteria({ amountMin: 1000, amountMax: 6000, kind: "expense" }));
    expect(ids(r).sort()).toEqual(["t1", "t2"]);
  });

  it("口座：一致のみ", () => {
    const r = filterTransactions(txs, incomes, criteria({ accountId: "wallet" }));
    expect(ids(r).sort()).toEqual(["t1", "t3"]);
  });

  it("AND結合：食費＋05/01以降＋2000円以上 → t2のみ", () => {
    const r = filterTransactions(txs, incomes, criteria({ keyword: "食費", dateFrom: "2026-05-01", amountMin: 2000 }));
    expect(ids(r)).toEqual(["t2"]);
  });

  it("並び替え：既定は日付の新しい順", () => {
    const r = filterTransactions(txs, incomes, criteria({ kind: "expense" }));
    expect(ids(r)).toEqual(["t4", "t1", "t2", "t3"]);
  });

  it("並び替え：金額の大きい順", () => {
    const r = filterTransactions(txs, incomes, criteria({ sort: "amountDesc" }));
    expect(r[0].id).toBe("i1"); // 250000が先頭
  });

  it("0件：該当なし（from>to）", () => {
    const r = filterTransactions(txs, incomes, criteria({ dateFrom: "2026-12-01", dateTo: "2026-01-01" }));
    expect(r).toHaveLength(0);
  });
});

describe("summarizeResults", () => {
  it("収入計・支出計・差引・件数を正しく計算する", () => {
    const all = filterTransactions(txs, incomes, emptyCriteria());
    const s = summarizeResults(all);
    expect(s.count).toBe(6);
    expect(s.incomeTotal).toBe(280000);
    expect(s.expenseTotal).toBe(37000);
    expect(s.net).toBe(243000);
  });

  it("空配列なら全て0", () => {
    const s = summarizeResults([]);
    expect(s).toEqual({ count: 0, incomeTotal: 0, expenseTotal: 0, net: 0 });
  });
});
