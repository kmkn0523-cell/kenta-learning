// ────────── 旧データ形式の変換（マイグレーション）のテスト ──────────
// 文字列金額の数値化・note→memo 統合・各種フィールドの数値化が正しいか確認する
import { describe, it, expect } from "vitest";
import {
  coerceAmountToNumber,
  migrateTransactions,
  migrateIncomes,
  migrateFixedExpenses,
  migrateLoans,
} from "./dataMigration";

describe("coerceAmountToNumber（金額を数値に揃える）", () => {
  it("数値はそのまま返す", () => {
    expect(coerceAmountToNumber(1200)).toBe(1200);
  });

  it("カンマや円記号付きの文字列から数値を取り出す", () => {
    expect(coerceAmountToNumber("1,200円")).toBe(1200);
    expect(coerceAmountToNumber("¥3,000")).toBe(3000);
  });

  it("マイナスや小数も解釈する", () => {
    expect(coerceAmountToNumber("-500")).toBe(-500);
    expect(coerceAmountToNumber("12.5")).toBe(12.5);
  });

  it("空文字や数字を含まない文字列は0", () => {
    expect(coerceAmountToNumber("")).toBe(0);
    expect(coerceAmountToNumber("なし")).toBe(0);
  });

  it("数値でも文字列でもない値は0", () => {
    expect(coerceAmountToNumber(null)).toBe(0);
    expect(coerceAmountToNumber(undefined)).toBe(0);
    expect(coerceAmountToNumber({})).toBe(0);
  });
});

describe("migrateTransactions（変動支出の変換）", () => {
  it("配列でなければ空配列", () => {
    expect(migrateTransactions(null as any)).toEqual([]);
    expect(migrateTransactions(undefined as any)).toEqual([]);
  });

  it("文字列金額を数値化する", () => {
    const result = migrateTransactions([{ id: "1", date: "2026-06-01", category: "食費", amount: "1,000", memo: "" }]);
    expect(result[0].amount).toBe(1000);
  });

  it("旧 note フィールドを memo に移し、note は消す", () => {
    const result = migrateTransactions([{ id: "1", date: "2026-06-01", category: "食費", amount: 500, note: "旧メモ" }]);
    expect(result[0].memo).toBe("旧メモ");
    expect("note" in result[0]).toBe(false);
  });

  it("memo が既にあれば note より memo を優先する", () => {
    const result = migrateTransactions([{ id: "1", date: "2026-06-01", category: "食費", amount: 500, memo: "新", note: "旧" }]);
    expect(result[0].memo).toBe("新");
  });

  it("memo も note も無ければ空文字", () => {
    const result = migrateTransactions([{ id: "1", date: "2026-06-01", category: "食費", amount: 500 }]);
    expect(result[0].memo).toBe("");
  });
});

describe("migrateIncomes / migrateFixedExpenses（収入・固定費の変換）", () => {
  it("収入の金額を数値化する", () => {
    const result = migrateIncomes([{ id: "1", date: "2026-06-01", category: "給与", amount: "250,000", memo: "" }]);
    expect(result[0].amount).toBe(250000);
  });

  it("固定費の金額を数値化する", () => {
    const result = migrateFixedExpenses([{ id: "1", name: "家賃", category: "家賃", amount: "80,000", payDay: "1日" }]);
    expect(result[0].amount).toBe(80000);
  });

  it("配列でなければ空配列", () => {
    expect(migrateIncomes(null as any)).toEqual([]);
    expect(migrateFixedExpenses(undefined as any)).toEqual([]);
  });
});

describe("migrateLoans（ローンの変換）", () => {
  it("rate/remaining/monthly/principal をすべて数値化する", () => {
    const result = migrateLoans([
      { id: "1", name: "アコム", rate: "18.0", remaining: "1,000,000", monthly: "30,000", principal: "1,500,000", payDay: "1日" },
    ]);
    expect(result[0].rate).toBe(18.0);
    expect(result[0].remaining).toBe(1000000);
    expect(result[0].monthly).toBe(30000);
    expect(result[0].principal).toBe(1500000);
  });

  it("配列でなければ空配列", () => {
    expect(migrateLoans(null as any)).toEqual([]);
  });
});
