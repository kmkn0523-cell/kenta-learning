// ────────── 口座残高計算 ──────────
// 初期残高 + 入金 - 出金 - 振替送金 + 振替受取
import { Account, Tx, Income, Transfer } from "../types";

export function calculateAccountBalance(
  account: Account,
  transactions: Tx[],
  incomes: Income[],
  transfers: Transfer[]
): number {
  // この口座に紐付いた支出を合計
  const expenses = transactions
    .filter(t => t.accountId === account.id)
    .reduce((sum, t) => sum + t.amount, 0);
  // この口座に紐付いた収入を合計
  const income = incomes
    .filter(i => i.accountId === account.id)
    .reduce((sum, i) => sum + i.amount, 0);
  // この口座から外への振替
  const transferOut = transfers
    .filter(t => t.fromAccountId === account.id)
    .reduce((sum, t) => sum + t.amount, 0);
  // この口座への振替受取
  const transferIn = transfers
    .filter(t => t.toAccountId === account.id)
    .reduce((sum, t) => sum + t.amount, 0);
  return account.balance + income - expenses - transferOut + transferIn;
}
