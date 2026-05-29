// ────────── 月次サマリー書き出しユーティリティのテスト ──────────
// 純粋関数（計算だけする関数）の動きをvitestで確かめる
// 画像書き出しは canvas が必要なので、ここではテストしない（手動で確認する）

import { describe, it, expect } from "vitest";
import { computeSavingRate } from "./summaryExport";

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
