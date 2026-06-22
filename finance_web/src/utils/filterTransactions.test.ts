// ────────── 取引の絞り込み・並び替えのテスト ──────────
// キーワード・カテゴリ・日付・金額のフィルターと、日付/金額の並び替えを確認する
import { describe, it, expect } from "vitest";
import { filterAndSortItems, filterAndSortTransactions } from "./filterTransactions";
import { Tx } from "../types";

// テスト用の変動支出データ（4件）
const txs: Tx[] = [
  { id: "t1", date: "2026-05-18", category: "食費", amount: 1200, memo: "ランチ" },
  { id: "t2", date: "2026-05-10", category: "食費", amount: 5000, memo: "外食ディナー" },
  { id: "t3", date: "2026-04-30", category: "日用品", amount: 800, memo: "洗剤" },
  { id: "t4", date: "2026-05-25", category: "趣味", amount: 30000, memo: "ゲーム機" },
];

// 結果のIDだけ取り出すヘルパー
const ids = (items: { id: string }[]) => items.map((i) => i.id);

describe("filterAndSortItems（絞り込み）", () => {
  it("条件なしなら全件返す", () => {
    expect(filterAndSortItems(txs, {}).length).toBe(4);
  });

  it("キーワードはメモにマッチする（大文字小文字を無視）", () => {
    expect(ids(filterAndSortItems(txs, { text: "ランチ" }))).toEqual(["t1"]);
  });

  it("キーワードはカテゴリにもマッチする", () => {
    expect(ids(filterAndSortItems(txs, { text: "食費" }))).toEqual(["t1", "t2"]);
  });

  it("カテゴリフィルターで絞り込む", () => {
    expect(ids(filterAndSortItems(txs, { categories: ["趣味", "日用品"] }))).toEqual(["t3", "t4"]);
  });

  it("カテゴリ配列が空なら全件（絞り込まない）", () => {
    expect(filterAndSortItems(txs, { categories: [] }).length).toBe(4);
  });

  it("日付の範囲で絞り込む（境界を含む）", () => {
    const result = filterAndSortItems(txs, { dateFrom: "2026-05-10", dateTo: "2026-05-18" });
    expect(ids(result).sort()).toEqual(["t1", "t2"]);
  });

  it("金額の下限・上限で絞り込む", () => {
    expect(ids(filterAndSortItems(txs, { amountMin: 1000, amountMax: 6000 })).sort()).toEqual(["t1", "t2"]);
  });

  it("複数条件はAND（すべて満たすもの）", () => {
    // 食費 かつ 2000円以上 → t2のみ
    expect(ids(filterAndSortItems(txs, { categories: ["食費"], amountMin: 2000 }))).toEqual(["t2"]);
  });
});

describe("filterAndSortItems（並び替え）", () => {
  it("日付の降順（新しい順）", () => {
    expect(ids(filterAndSortItems(txs, { sortBy: "date", sortDir: "desc" }))).toEqual(["t4", "t1", "t2", "t3"]);
  });

  it("日付の昇順（古い順）", () => {
    expect(ids(filterAndSortItems(txs, { sortBy: "date", sortDir: "asc" }))).toEqual(["t3", "t2", "t1", "t4"]);
  });

  it("金額の降順（高い順）", () => {
    expect(ids(filterAndSortItems(txs, { sortBy: "amount", sortDir: "desc" }))).toEqual(["t4", "t2", "t1", "t3"]);
  });

  it("金額の昇順（安い順）", () => {
    expect(ids(filterAndSortItems(txs, { sortBy: "amount", sortDir: "asc" }))).toEqual(["t3", "t1", "t2", "t4"]);
  });

  it("元の配列を破壊しない（非破壊ソート）", () => {
    const before = ids(txs);
    filterAndSortItems(txs, { sortBy: "amount", sortDir: "desc" });
    expect(ids(txs)).toEqual(before);
  });
});

describe("filterAndSortTransactions（Tx専用ラッパー）", () => {
  it("filterAndSortItems と同じ結果を返す", () => {
    expect(ids(filterAndSortTransactions(txs, { categories: ["趣味"] }))).toEqual(["t4"]);
  });
});
