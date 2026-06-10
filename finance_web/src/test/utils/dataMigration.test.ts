import { describe, it, expect } from "vitest";
import { coerceAmountToNumber, migrateTransactions } from "../../utils/dataMigration";

describe("coerceAmountToNumber", () => {
  it("数値はそのまま返す", () => {
    expect(coerceAmountToNumber(1000)).toBe(1000);
  });
  it("カンマ付き文字列を数値化する", () => {
    expect(coerceAmountToNumber("1,234")).toBe(1234);
  });
  it("空文字は 0 にする", () => {
    expect(coerceAmountToNumber("")).toBe(0);
  });
  it("undefined は 0 にする", () => {
    expect(coerceAmountToNumber(undefined)).toBe(0);
  });
});

describe("migrateTransactions", () => {
  it("amount が文字列の取引を数値化する", () => {
    const input = [{ id: "1", date: "2026-05-01", category: "食費", amount: "1,500", memo: "" }];
    const result = migrateTransactions(input as any);
    expect(result[0].amount).toBe(1500);
  });
  it("note フィールドを memo にリネームする", () => {
    const input = [{ id: "1", date: "2026-05-01", category: "食費", amount: 100, note: "ランチ" }];
    const result = migrateTransactions(input as any);
    expect(result[0].memo).toBe("ランチ");
    expect((result[0] as any).note).toBeUndefined();
  });
});
