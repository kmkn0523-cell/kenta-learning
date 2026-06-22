// ────────── ローン計算ロジックのテスト ──────────
// お金の計算（金利・完済月数・完済予定日・金利テーブル）が正しいか確認する
import { describe, it, expect, vi, afterEach } from "vitest";
import {
  calculateMonthlyInterest,
  calculateTotalInterest,
  calculateCompletionDate,
  findRate,
} from "./loanCalc";

describe("calculateMonthlyInterest（今月の利息額）", () => {
  it("残債×年利/12 を四捨五入して返す", () => {
    // 100万円・年利12% → 月利1% → 10000円
    expect(calculateMonthlyInterest(1000000, 12)).toBe(10000);
    // 100万円・年利18% → 月利1.5% → 15000円
    expect(calculateMonthlyInterest(1000000, 18)).toBe(15000);
  });

  it("文字列で渡しても数値として計算する", () => {
    expect(calculateMonthlyInterest("1000000", "12")).toBe(10000);
  });

  it("端数は四捨五入される", () => {
    // 33333 × 18% / 12 = 499.995 → 500
    expect(calculateMonthlyInterest(33333, 18)).toBe(500);
  });

  it("残債0なら0", () => {
    expect(calculateMonthlyInterest(0, 18)).toBe(0);
  });
});

describe("calculateTotalInterest（完済までの月数と総利息）", () => {
  it("残債か返済額が0なら null", () => {
    expect(calculateTotalInterest(0, 12, 10000)).toBeNull();
    expect(calculateTotalInterest(100000, 12, 0)).toBeNull();
  });

  it("金利0%なら利息0・月数は残債÷返済額の切り上げ", () => {
    // 12万円を毎月1万円返済（金利なし）→ 12ヶ月・利息0
    expect(calculateTotalInterest(120000, 0, 10000)).toEqual({ interest: 0, months: 12 });
  });

  it("金利0%で割り切れない場合は月数を切り上げる", () => {
    // 12.5万円を毎月1万円 → 13ヶ月
    expect(calculateTotalInterest(125000, 0, 10000)).toEqual({ interest: 0, months: 13 });
  });

  it("毎月の返済額が利息以下なら完済不能で null", () => {
    // 100万円・年利18% → 月利息15000円。返済1万円では永遠に終わらない
    expect(calculateTotalInterest(1000000, 18, 10000)).toBeNull();
  });

  it("通常ケースで月数と総利息を計算する", () => {
    // 10万円・年利12%・毎月1万円返済 → 11ヶ月・総利息10000円
    expect(calculateTotalInterest(100000, 12, 10000)).toEqual({ interest: 10000, months: 11 });
  });

  it("文字列で渡しても計算できる", () => {
    expect(calculateTotalInterest("120000", "0", "10000")).toEqual({ interest: 0, months: 12 });
  });
});

describe("calculateCompletionDate（完済予定の年月）", () => {
  afterEach(() => {
    // 時刻のモックを毎回解除する
    vi.useRealTimers();
  });

  it("months が null/undefined/0 なら null", () => {
    expect(calculateCompletionDate(null)).toBeNull();
    expect(calculateCompletionDate(undefined)).toBeNull();
    expect(calculateCompletionDate(0)).toBeNull();
  });

  it("現在から指定月数後の年月を返す", () => {
    // 現在を 2026年1月15日 に固定する
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 0, 15));
    // 12ヶ月後 → 2027年1月
    expect(calculateCompletionDate(12)).toEqual({ y: 2027, m: 1 });
    // 2ヶ月後 → 2026年3月
    expect(calculateCompletionDate(2)).toEqual({ y: 2026, m: 3 });
  });

  it("年をまたぐ計算も正しい", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 10, 15)); // 2026年11月
    // 3ヶ月後 → 2027年2月
    expect(calculateCompletionDate(3)).toEqual({ y: 2027, m: 2 });
  });
});

describe("findRate（借入額とブランドから金利を自動判定）", () => {
  it("テーブルに無いブランドは null", () => {
    expect(findRate("存在しない銀行", 500000)).toBeNull();
  });

  it("借入額0は null（金利を勝手に書き換えない）", () => {
    expect(findRate("アコム", 0)).toBeNull();
  });

  it("借入額帯に応じた金利を返す（アコム）", () => {
    // 100万円以下 → 18.0%
    expect(findRate("アコム", 500000)).toBe(18.0);
    // 100万円ちょうど → 18.0%（上限は以下判定）
    expect(findRate("アコム", 1000000)).toBe(18.0);
    // 300万円以下 → 15.0%
    expect(findRate("アコム", 1500000)).toBe(15.0);
  });

  it("最高額帯（Infinity）の金利を返す", () => {
    // アコムの最後の帯は 7.7%
    expect(findRate("アコム", 9000000)).toBe(7.7);
  });

  it("文字列の金額でも判定できる", () => {
    expect(findRate("アコム", "500000")).toBe(18.0);
  });
});
