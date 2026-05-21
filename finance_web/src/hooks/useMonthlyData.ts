// ────────── 月別データ集計フック ──────────
// 選択中の年月に該当する取引・収入と、各種合計値をまとめて返す
import { useMemo } from "react";
import { Tx, Income, FixedExpense, Loan } from "../types";

interface MonthlyDataArgs {
  transactions: Tx[];
  incomes: Income[];
  fixedExpenses: FixedExpense[];
  // ローン・キャッシング・銀行ローンを合算した配列を渡す
  loans: Loan[];
  selectedYear: number;
  selectedMonth: number; // 0-11
}

export function useMonthlyData(args: MonthlyDataArgs) {
  const { transactions, incomes, fixedExpenses, loans, selectedYear, selectedMonth } = args;

  // "2026-05" 形式の年月文字列（フィルタリングのキーになる）
  const monthString = useMemo(
    () => `${selectedYear}-${String(selectedMonth + 1).padStart(2, "0")}`,
    [selectedYear, selectedMonth]
  );

  // 選択月の変動支出だけを抽出する
  const monthlyTransactions = useMemo(
    () => transactions.filter(tx => tx.date && tx.date.startsWith(monthString)),
    [transactions, monthString]
  );

  // 選択月の収入だけを抽出する
  const monthlyIncomes = useMemo(
    () => incomes.filter(i => i.date && i.date.startsWith(monthString)),
    [incomes, monthString]
  );

  // 変動支出の合計（選択月の取引を全部足す）
  const totalVariableExpense = useMemo(
    () => monthlyTransactions.reduce((s, t) => s + t.amount, 0),
    [monthlyTransactions]
  );

  // 固定費の合計（active が false の項目は一時停止扱いで除外）
  // active が未設定(undefined)の場合は有効とみなす
  const totalFixedExpense = useMemo(
    () => fixedExpenses.filter(f => f.active !== false).reduce((s, f) => s + f.amount, 0),
    [fixedExpenses]
  );

  // ローン返済合計（全ローン種別を足す）
  const totalLoanRepayment = useMemo(
    () => loans.reduce((s, l) => s + (l.monthly || 0), 0),
    [loans]
  );

  // 収入合計
  const totalIncome = useMemo(
    () => monthlyIncomes.reduce((s, i) => s + i.amount, 0),
    [monthlyIncomes]
  );

  // 支出合計（変動費 + 固定費 + ローン返済）
  const totalBurden = useMemo(
    () => totalVariableExpense + totalFixedExpense + totalLoanRepayment,
    [totalVariableExpense, totalFixedExpense, totalLoanRepayment]
  );

  // 収支（収入 - 支出合計）
  const net = useMemo(
    () => totalIncome - totalBurden,
    [totalIncome, totalBurden]
  );

  return {
    monthString,
    monthlyTransactions,
    monthlyIncomes,
    totalVariableExpense,
    totalFixedExpense,
    totalLoanRepayment,
    totalIncome,
    totalBurden,
    net,
  };
}
