import { describe, it, expect } from "vitest";
import { transactionsToCsv, exportAsJson } from "../../utils/dataExport";

describe("transactionsToCsv", () => {
  it("ヘッダー行を含む CSV を返す", () => {
    const csv = transactionsToCsv([]);
    expect(csv).toBe("date,category,amount,memo\n");
  });

  it("取引行を正しく出力する", () => {
    const csv = transactionsToCsv([
      { id: "1", date: "2026-05-01", category: "食費", amount: 1500, memo: "ランチ" }
    ]);
    expect(csv).toContain("2026-05-01,食費,1500,ランチ");
  });

  it("memo にカンマが含まれていたらクオートする", () => {
    const csv = transactionsToCsv([
      { id: "1", date: "2026-05-01", category: "食費", amount: 1500, memo: "a,b,c" }
    ]);
    expect(csv).toContain('"a,b,c"');
  });

  it("memo にダブルクオートが含まれていたらエスケープする", () => {
    const csv = transactionsToCsv([
      { id: "1", date: "2026-05-01", category: "食費", amount: 1500, memo: 'say "hi"' }
    ]);
    expect(csv).toContain('"say ""hi"""');
  });
});

describe("exportAsJson", () => {
  it("整形済み JSON 文字列を返す", () => {
    const json = exportAsJson({ foo: "bar" });
    expect(json).toBe('{\n  "foo": "bar"\n}');
  });
});
