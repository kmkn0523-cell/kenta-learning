import { describe, it, expect } from "vitest";
import { calculateAccountBalance } from "../../utils/accountBalance";
import { Account, Tx, Income, Transfer } from "../../types";

const baseAccount: Account = { id: "a", name: "メイン", balance: 10000 };

describe("calculateAccountBalance", () => {
  it("初期残高だけのときはその値を返す", () => {
    expect(calculateAccountBalance(baseAccount, [], [], [])).toBe(10000);
  });

  it("収入で残高が増える", () => {
    const incomes: Income[] = [{ id: "i1", date: "2026-05-01", category: "給与", amount: 5000, memo: "", accountId: "a" }];
    expect(calculateAccountBalance(baseAccount, [], incomes, [])).toBe(15000);
  });

  it("支出で残高が減る", () => {
    const transactions: Tx[] = [{ id: "t1", date: "2026-05-01", category: "食費", amount: 3000, memo: "", accountId: "a" }];
    expect(calculateAccountBalance(baseAccount, transactions, [], [])).toBe(7000);
  });

  it("振替送金で残高が減る", () => {
    const transfers: Transfer[] = [{ id: "tr1", date: "2026-05-01", fromAccountId: "a", toAccountId: "b", amount: 2000 }];
    expect(calculateAccountBalance(baseAccount, [], [], transfers)).toBe(8000);
  });

  it("振替受取で残高が増える", () => {
    const transfers: Transfer[] = [{ id: "tr1", date: "2026-05-01", fromAccountId: "b", toAccountId: "a", amount: 2000 }];
    expect(calculateAccountBalance(baseAccount, [], [], transfers)).toBe(12000);
  });

  it("accountId が一致しない取引は無視する", () => {
    const transactions: Tx[] = [{ id: "t1", date: "2026-05-01", category: "食費", amount: 3000, memo: "", accountId: "other" }];
    expect(calculateAccountBalance(baseAccount, transactions, [], [])).toBe(10000);
  });

  it("accountId が未指定の取引は無視する（紐付けされていない）", () => {
    const transactions: Tx[] = [{ id: "t1", date: "2026-05-01", category: "食費", amount: 3000, memo: "" }];
    expect(calculateAccountBalance(baseAccount, transactions, [], [])).toBe(10000);
  });
});
