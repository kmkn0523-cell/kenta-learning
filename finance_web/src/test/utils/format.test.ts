// ────────── format.ts のユニットテスト ──────────
// parseYenAmount・formatAmount・formatYen の3つの関数をテストする

import { parseYenAmount, formatAmount, formatYen } from "../../utils/format";

// parseYenAmount のテスト：いろんな形式の文字列を数値に変換できるか確認する
describe("parseYenAmount", () => {
  it("カンマなし数値文字列をそのまま変換できる", () => {
    expect(parseYenAmount("1000")).toBe(1000);
  });

  it("カンマ区切り文字列のカンマを除去して変換できる", () => {
    expect(parseYenAmount("1,000,000")).toBe(1000000);
  });

  it("数値型をそのまま受け取れる", () => {
    expect(parseYenAmount(5000)).toBe(5000);
  });

  it("空文字列は 0 になる", () => {
    expect(parseYenAmount("")).toBe(0);
  });

  it("0 を渡すと 0 が返る", () => {
    expect(parseYenAmount(0)).toBe(0);
  });
});

// formatAmount のテスト：数値を「1,000」形式に整形できるか確認する
describe("formatAmount", () => {
  it("1000 を '1,000' に変換できる", () => {
    expect(formatAmount(1000)).toBe("1,000");
  });

  it("文字列の数値も整形できる", () => {
    expect(formatAmount("5000")).toBe("5,000");
  });

  it("空文字列は空文字列のまま返る", () => {
    expect(formatAmount("")).toBe("");
  });

  it("null は空文字列を返す", () => {
    expect(formatAmount(null)).toBe("");
  });

  it("undefined は空文字列を返す", () => {
    expect(formatAmount(undefined)).toBe("");
  });
});

// formatYen のテスト：数値を「¥1,000」形式に変換できるか確認する
describe("formatYen", () => {
  it("整数を円マーク付きカンマ形式に変換できる", () => {
    expect(formatYen(1000)).toBe("¥1,000");
  });

  it("0 は '¥0' になる", () => {
    expect(formatYen(0)).toBe("¥0");
  });

  it("文字列の数値も変換できる", () => {
    expect(formatYen("3000")).toBe("¥3,000");
  });

  it("大きな数字も正しく変換できる", () => {
    expect(formatYen(1000000)).toBe("¥1,000,000");
  });
});
