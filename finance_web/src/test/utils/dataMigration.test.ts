import { describe, it, expect } from "vitest";
import { coerceAmountToNumber, migrateTransactions, backfillUpdatedAt } from "../../utils/dataMigration";

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

describe("backfillUpdatedAt", () => {
  const STAMP = "2026-06-22T10:00:00.000Z";

  it("updatedAt が無いレコードに補完する", () => {
    const input = [{ id: "1", amount: 100 }];
    const result = backfillUpdatedAt(input, STAMP);
    expect(result[0].updatedAt).toBe(STAMP);
  });

  it("既に updatedAt があるレコードは上書きしない（冪等）", () => {
    const input = [{ id: "1", updatedAt: "2026-01-01T00:00:00.000Z" }];
    const result = backfillUpdatedAt(input, STAMP);
    expect(result[0].updatedAt).toBe("2026-01-01T00:00:00.000Z");
  });

  it("混在配列でも欠けている分だけ補完する", () => {
    const input = [
      { id: "1" },
      { id: "2", updatedAt: "2026-01-01T00:00:00.000Z" },
    ];
    const result = backfillUpdatedAt(input, STAMP);
    expect(result[0].updatedAt).toBe(STAMP);
    expect(result[1].updatedAt).toBe("2026-01-01T00:00:00.000Z");
  });

  it("配列でない入力は空配列を返す", () => {
    expect(backfillUpdatedAt(undefined as any, STAMP)).toEqual([]);
    expect(backfillUpdatedAt(null as any, STAMP)).toEqual([]);
  });

  it("元の配列・要素を破壊しない（新しいオブジェクトを返す）", () => {
    const original = [{ id: "1", amount: 100 }];
    const result = backfillUpdatedAt(original, STAMP);
    expect(original[0]).not.toHaveProperty("updatedAt");
    expect(result[0]).not.toBe(original[0]);
  });
});
