import { describe, it, expect } from "vitest";
import { evaluateOverspend, pruneLog } from "./overspendAlerts";

const M = "2026-06";

describe("evaluateOverspend", () => {
  it("80%未満は鳴らない", () => {
    const { alerts } = evaluateOverspend({ 食費: 7900 }, { 食費: 10000 }, {}, M);
    expect(alerts).toEqual([]);
  });

  it("80%以上で level=80 を鳴らす", () => {
    const { alerts, nextLog } = evaluateOverspend({ 食費: 8000 }, { 食費: 10000 }, {}, M);
    expect(alerts).toEqual([{ category: "食費", level: 80, spent: 8000, budget: 10000, ratio: 0.8 }]);
    expect(nextLog[M]).toContain("食費|80");
  });

  it("100%以上で level=100。80%も同時にログ済みにして二重通知しない", () => {
    const { alerts, nextLog } = evaluateOverspend({ 食費: 12000 }, { 食費: 10000 }, {}, M);
    expect(alerts).toEqual([{ category: "食費", level: 100, spent: 12000, budget: 10000, ratio: 1.2 }]);
    expect(nextLog[M]).toContain("食費|100");
    expect(nextLog[M]).toContain("食費|80");
  });

  it("同月同レベルは重複して鳴らさない", () => {
    const log = { [M]: ["食費|80"] };
    const { alerts } = evaluateOverspend({ 食費: 8500 }, { 食費: 10000 }, log, M);
    expect(alerts).toEqual([]);
  });

  it("予算未設定(0)のカテゴリは対象外", () => {
    const { alerts } = evaluateOverspend({ 食費: 9999 }, { 食費: 0 }, {}, M);
    expect(alerts).toEqual([]);
  });

  it("月が変わればまた鳴る", () => {
    const log = { "2026-05": ["食費|80"] };
    const { alerts } = evaluateOverspend({ 食費: 8000 }, { 食費: 10000 }, log, "2026-06");
    expect(alerts).toHaveLength(1);
  });
});

describe("pruneLog", () => {
  it("当月以外のログを消す", () => {
    const log = { "2026-05": ["食費|80"], "2026-06": ["住居|100"] };
    expect(pruneLog(log, "2026-06")).toEqual({ "2026-06": ["住居|100"] });
  });
});
