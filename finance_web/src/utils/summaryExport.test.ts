// ────────── 月次サマリー書き出しユーティリティのテスト ──────────
// 純粋関数（計算だけする関数）の動きをvitestで確かめる
// 画像書き出しは canvas が必要なので、ここではテストしない（手動で確認する）

import { describe, it, expect } from "vitest";
import { computeSavingRate, buildSummaryCsv, appendWatermark, WATERMARK_TEXT } from "./summaryExport";
import type { SummaryStats } from "../types";

describe("appendWatermark", () => {
  it("透かし文言にアプリ名とURLが含まれている", () => {
    expect(WATERMARK_TEXT).toContain("BYB");
    expect(WATERMARK_TEXT).toContain("financeweb-nine.vercel.app");
  });

  it("2Dコンテキストが使えない環境（jsdom）では元のcanvasをそのまま返す", () => {
    // jsdom の canvas.getContext は null を返すのでフォールバック分岐が通る
    const canvas = document.createElement("canvas");
    canvas.width = 100;
    canvas.height = 50;
    expect(appendWatermark(canvas)).toBe(canvas);
  });
});

describe("computeSavingRate", () => {
  it("手残り60000円・収入300000円なら貯蓄率は20%", () => {
    expect(computeSavingRate(60000, 300000)).toBe(20);
  });

  it("割り切れない時は小数第1位まで（手残り100000・収入300000なら33.3%）", () => {
    expect(computeSavingRate(100000, 300000)).toBe(33.3);
  });

  it("収入が0円のときはゼロ除算を避けて0%にする", () => {
    expect(computeSavingRate(0, 0)).toBe(0);
  });

  it("手残りがマイナス（赤字）なら貯蓄率もマイナスになる", () => {
    expect(computeSavingRate(-30000, 300000)).toBe(-10);
  });
});

describe("buildSummaryCsv", () => {
  // 当月の集計値（テスト全体で使い回す基本データ）
  const current: SummaryStats = { income: 300000, expense: 240000, net: 60000, savingRate: 20 };

  it("前月がnullなら2列ヘッダーで基本指標とカテゴリを並べる", () => {
    const csv = buildSummaryCsv(
      "2026年5月",
      current,
      null,
      [{ category: "食費", amount: 50000 }, { category: "交通費", amount: 12000 }],
    );
    const expected =
      "項目,金額\n" +
      "収入合計,300000\n" +
      "支出合計,240000\n" +
      "手残り,60000\n" +
      "貯蓄率,20%\n" +
      "\n" +
      "カテゴリ,金額\n" +
      "食費,50000\n" +
      "交通費,12000\n";
    expect(csv).toBe(expected);
  });

  it("前月ありなら3列ヘッダーで当月・前月を並べる", () => {
    const previous: SummaryStats = { income: 280000, expense: 250000, net: 30000, savingRate: 10.7 };
    const csv = buildSummaryCsv("2026年5月", current, previous, []);
    const expected =
      "項目,当月,前月\n" +
      "収入合計,300000,280000\n" +
      "支出合計,240000,250000\n" +
      "手残り,60000,30000\n" +
      "貯蓄率,20%,10.7%\n";
    expect(csv).toBe(expected);
  });

  it("カンマを含むカテゴリ名はダブルクォートで囲む", () => {
    const csv = buildSummaryCsv(
      "2026年5月",
      current,
      null,
      [{ category: "外食,カフェ", amount: 8000 }],
    );
    expect(csv).toContain('"外食,カフェ",8000\n');
  });
});
