// ────────── サブスク棚卸し集計のテスト ──────────
// 年額計算・稼働/停止の振り分け・並び順・割合が正しいか確認する
import { describe, it, expect } from "vitest";
import { buildSubscriptionSummary } from "./subscriptionSummary";
import { RecurringExpense } from "../types";

// テスト用の繰り返し支出（稼働2件・停止1件）
const subs: RecurringExpense[] = [
  { id: "s1", name: "Netflix", category: "趣味", amount: 1490, payDay: "1日" },
  { id: "s2", name: "ジム", category: "その他", amount: 8000, payDay: "5日", active: true },
  { id: "s3", name: "解約済みサービス", category: "趣味", amount: 500, payDay: "未設定", active: false },
];

describe("buildSubscriptionSummary（サブスク棚卸し）", () => {
  it("稼働中の月額合計と年額合計（×12）を計算する", () => {
    const s = buildSubscriptionSummary(subs);
    // 1490 + 8000 = 9490/月
    expect(s.monthlyTotal).toBe(9490);
    // 9490 × 12 = 113880/年
    expect(s.annualTotal).toBe(113880);
  });

  it("active が未設定のものは稼働中として数える", () => {
    const s = buildSubscriptionSummary(subs);
    // s1(未設定)+s2(true) = 2件稼働、s3(false) = 1件停止
    expect(s.activeCount).toBe(2);
    expect(s.pausedCount).toBe(1);
  });

  it("停止中の月額合計（節約額）を別途集計する", () => {
    expect(buildSubscriptionSummary(subs).pausedMonthlySaved).toBe(500);
  });

  it("各行の年額は月額×12", () => {
    const netflix = buildSubscriptionSummary(subs).items.find(i => i.id === "s1")!;
    expect(netflix.annual).toBe(1490 * 12);
  });

  it("稼働中を先に・年額の高い順に並べる（停止中は末尾）", () => {
    const order = buildSubscriptionSummary(subs).items.map(i => i.id);
    // ジム(8000) → Netflix(1490) → 停止中
    expect(order).toEqual(["s2", "s1", "s3"]);
  });

  it("割合は稼働中の年額合計に対する比率（停止中は0%）", () => {
    const items = buildSubscriptionSummary(subs).items;
    const gym = items.find(i => i.id === "s2")!;
    const paused = items.find(i => i.id === "s3")!;
    // 8000/9490 ≒ 84%
    expect(gym.sharePct).toBe(84);
    expect(paused.sharePct).toBe(0);
  });

  it("空配列なら全て0", () => {
    const s = buildSubscriptionSummary([]);
    expect(s).toEqual({ items: [], activeCount: 0, pausedCount: 0, monthlyTotal: 0, annualTotal: 0, pausedMonthlySaved: 0 });
  });

  it("配列でない値でも落ちずに空サマリーを返す", () => {
    expect(buildSubscriptionSummary(null as any).annualTotal).toBe(0);
  });

  it("金額が文字列でも数値として集計する", () => {
    const s = buildSubscriptionSummary([{ id: "x", name: "test", category: "趣味", amount: "1000" as any, payDay: "1日" }]);
    expect(s.annualTotal).toBe(12000);
  });
});
