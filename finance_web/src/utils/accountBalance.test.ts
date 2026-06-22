// ────────── 口座残高計算のテスト ──────────
// 初期残高 + 入金 - 出金 - 振替送金 + 振替受取 が正しいか確認する
import { describe, it, expect } from "vitest";
import { calculateAccountBalance } from "./accountBalance";
import { Account, Tx, Income, Transfer } from "../types";

// テスト用の口座（2つ：財布と銀行）
const wallet: Account = { id: "wallet", name: "財布", balance: 10000 };
const bank: Account = { id: "bank", name: "銀行", balance: 100000 };

// 財布から3000円使い、銀行に副業収入5000円
const transactions: Tx[] = [
  { id: "t1", date: "2026-06-01", category: "食費", amount: 3000, memo: "", accountId: "wallet" },
  { id: "t2", date: "2026-06-02", category: "趣味", amount: 1000, memo: "", accountId: "bank" },
  { id: "t3", date: "2026-06-03", category: "食費", amount: 500, memo: "", /* 口座未指定 */ },
];
const incomes: Income[] = [
  { id: "i1", date: "2026-06-05", category: "給与", amount: 200000, memo: "", accountId: "bank" },
  { id: "i2", date: "2026-06-06", category: "副業", amount: 5000, memo: "", /* 口座未指定 */ },
];
// 銀行 → 財布 に20000円振替
const transfers: Transfer[] = [
  { id: "tr1", date: "2026-06-07", fromAccountId: "bank", toAccountId: "wallet", amount: 20000 },
];

describe("calculateAccountBalance（口座残高の集計）", () => {
  it("財布：初期1万 - 支出3千 + 振替受取2万 = 27000", () => {
    // 財布に紐づく収入は無い・支出は3000・振替受取20000
    expect(calculateAccountBalance(wallet, transactions, incomes, transfers)).toBe(27000);
  });

  it("銀行：初期10万 + 給与20万 - 支出1千 - 振替送金2万 = 279000", () => {
    expect(calculateAccountBalance(bank, transactions, incomes, transfers)).toBe(279000);
  });

  it("口座未指定の取引・収入は残高に影響しない", () => {
    // どの口座にも紐づかない t3(500) と i2(5000) は集計対象外
    const total =
      calculateAccountBalance(wallet, transactions, incomes, transfers) +
      calculateAccountBalance(bank, transactions, incomes, transfers);
    // 27000 + 279000 = 306000（未指定分は含まれない）
    expect(total).toBe(306000);
  });

  it("取引も振替も無ければ初期残高そのまま", () => {
    expect(calculateAccountBalance(wallet, [], [], [])).toBe(10000);
  });

  it("残高がマイナスになるケースも計算する", () => {
    const empty: Account = { id: "x", name: "空", balance: 0 };
    const spend: Tx[] = [{ id: "s1", date: "2026-06-01", category: "食費", amount: 5000, memo: "", accountId: "x" }];
    expect(calculateAccountBalance(empty, spend, [], [])).toBe(-5000);
  });
});
