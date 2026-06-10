// ────────── loanCalc.ts のユニットテスト ──────────
// calculateMonthlyInterest・calculateTotalInterest・calculateCompletionDate・findRate の4つの関数をテストする

import { calculateMonthlyInterest, calculateTotalInterest, calculateCompletionDate, findRate } from "../../utils/loanCalc";

// calculateMonthlyInterest のテスト：今月の利息額が正しく計算できるか確認する
describe("calculateMonthlyInterest", () => {
  it("残債100万・年利18%のとき今月の利息は1500円", () => {
    // 1000000 × 0.18 / 12 = 15000 → Math.round で 15000
    expect(calculateMonthlyInterest(1000000, 18)).toBe(15000);
  });

  it("残債0のとき利息は0", () => {
    expect(calculateMonthlyInterest(0, 18)).toBe(0);
  });

  it("金利0のとき利息は0", () => {
    expect(calculateMonthlyInterest(1000000, 0)).toBe(0);
  });

  it("文字列の数値も計算できる", () => {
    // 同じ値を文字列で渡しても同じ結果になる
    expect(calculateMonthlyInterest("500000", "12")).toBe(calculateMonthlyInterest(500000, 12));
  });
});

// calculateTotalInterest のテスト：完済月数と総利息が正しく計算できるか確認する
describe("calculateTotalInterest", () => {
  it("通常ケース：残債100万・年利18%・月返済3万で完済できる", () => {
    const result = calculateTotalInterest(1000000, 18, 30000);
    // 結果が null でないこと、months と interest が数値であることを確認
    expect(result).not.toBeNull();
    expect(typeof result!.months).toBe("number");
    expect(typeof result!.interest).toBe("number");
    expect(result!.months).toBeGreaterThan(0);
    expect(result!.interest).toBeGreaterThan(0);
  });

  it("金利0のとき総利息は0で月数は残債÷月返済の切り上げ", () => {
    const result = calculateTotalInterest(1200000, 0, 100000);
    expect(result).not.toBeNull();
    expect(result!.interest).toBe(0);
    expect(result!.months).toBe(12); // 1200000 ÷ 100000 = 12
  });

  it("残債0のとき null を返す", () => {
    expect(calculateTotalInterest(0, 18, 30000)).toBeNull();
  });

  it("月返済が0のとき null を返す", () => {
    expect(calculateTotalInterest(1000000, 18, 0)).toBeNull();
  });

  it("月返済額が利息以下（永遠に完済できない）のとき null を返す", () => {
    // 残債1億・年利18% → 月利息150万。月返済10万では利息を払えない
    expect(calculateTotalInterest(100000000, 18, 100000)).toBeNull();
  });
});

// calculateCompletionDate のテスト：何ヶ月後の完済予定日が正しく返るか確認する
describe("calculateCompletionDate", () => {
  it("12ヶ月後の年と月が返る", () => {
    const now = new Date();
    const result = calculateCompletionDate(12);
    expect(result).not.toBeNull();
    // 12ヶ月後の年月を期待値として計算する
    const expected = new Date(now.getFullYear(), now.getMonth() + 12, 1);
    expect(result!.y).toBe(expected.getFullYear());
    expect(result!.m).toBe(expected.getMonth() + 1);
  });

  it("null を渡すと null を返す", () => {
    expect(calculateCompletionDate(null)).toBeNull();
  });

  it("undefined を渡すと null を返す", () => {
    expect(calculateCompletionDate(undefined)).toBeNull();
  });

  it("0 を渡すと null を返す（0ヶ月後は無効）", () => {
    expect(calculateCompletionDate(0)).toBeNull();
  });
});

// findRate のテスト：ブランドと金額から金利が正しく取れるか確認する
describe("findRate", () => {
  it("アコム・残債50万（100万以下）→ 18.0% が返る", () => {
    expect(findRate("アコム", 500000)).toBe(18.0);
  });

  it("アコム・残債200万（100万超〜300万以下）→ 15.0% が返る", () => {
    expect(findRate("アコム", 2000000)).toBe(15.0);
  });

  it("テーブルに存在しないブランドは null を返す", () => {
    expect(findRate("存在しない銀行", 1000000)).toBeNull();
  });

  it("金額0のとき null を返す", () => {
    expect(findRate("アコム", 0)).toBeNull();
  });

  it("文字列の金額でも正しく金利を返す", () => {
    // 数値でも文字列でも同じ結果になる
    expect(findRate("プロミス", "500000")).toBe(findRate("プロミス", 500000));
  });
});
