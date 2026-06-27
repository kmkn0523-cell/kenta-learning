// ────────── 将来キャッシュフロー予測ユーティリティ ──────────
// 過去の収支履歴と確定している固定費・ローンから、
// 数か月先の収入・支出・手残りを推定して返す純粋関数

import { Tx, Income, FixedExpense, Loan } from "../types";

// 予測1か月分のデータの形
export interface ForecastMonth {
  label: string;      // 短縮月ラベル（例: "8月"）
  yearMonth: string;  // "YYYY-MM" 形式（例: "2026-08"）
  income: number;     // 推定収入（円）
  expense: number;    // 推定支出（固定＋変動、円）
  net: number;        // 推定手残り（収入 - 支出、円）
}

// 予測に必要な入力データの型
interface ForecastArgs {
  transactions: Tx[];          // 変動支出の履歴
  incomes: Income[];           // 収入の履歴
  fixedExpenses: FixedExpense[]; // 固定費一覧
  loans: Loan[];               // ローン一覧
  today: string;               // 基準日 "YYYY-MM-DD"（これより先を予測する）
  monthsAhead?: number;        // 何か月先まで予測するか（デフォルト: 6）
  lookbackMonths?: number;     // 平均の計算に使う過去月数（デフォルト: 3）
}

// "YYYY-MM" 文字列を [年, 月(1-12)] に変換するヘルパー
function parseYearMonth(ym: string): [number, number] {
  const [y, m] = ym.split("-").map(Number);
  return [y, m];
}

// 基準年月から N か月ずらした "YYYY-MM" 文字列を返す
// offset が負なら過去、正なら未来
function shiftMonth(baseYM: string, offset: number): string {
  const [y, m] = parseYearMonth(baseYM);
  // 月を 0-indexed にしてから足し算し、再び 1-indexed に戻す
  const totalMonths = (y * 12 + (m - 1)) + offset;
  const newY = Math.floor(totalMonths / 12);
  const newM = (totalMonths % 12) + 1;
  return `${newY}-${String(newM).padStart(2, "0")}`;
}

/**
 * 将来N月分のキャッシュフロー予測を返す
 *
 * 推定ロジック:
 *   収入   = 過去 lookbackMonths 月の収入合計の平均
 *   変動費 = 過去 lookbackMonths 月の変動支出合計の平均
 *   固定費 = 現在登録されている固定費合計（active かつ autoTrack=false）
 *   ローン = 現在登録されているローン返済額合計
 *   手残り = 収入 - (変動費 + 固定費 + ローン)
 */
export function buildCashFlowForecast({
  transactions,
  incomes,
  fixedExpenses,
  loans,
  today,
  monthsAhead = 6,
  lookbackMonths = 3,
}: ForecastArgs): ForecastMonth[] {
  // 基準年月（today の年月）
  const baseYM = today.substring(0, 7); // "YYYY-MM"

  // ── 確定支出（毎月必ず出ていく金額）を計算 ──────────
  // active=false で停止中・autoTrack=true で変動支出に転記済みの固定費は除外
  const fixedCost = fixedExpenses
    .filter(f => f.active !== false && !f.autoTrack)
    .reduce((sum, f) => sum + (f.amount || 0), 0);

  // ローン返済合計
  const loanCost = loans.reduce((sum, l) => sum + (l.monthly || 0), 0);

  // 毎月確実に出ていく金額
  const certainExpense = fixedCost + loanCost;

  // ── 過去 N 月の平均収入と平均変動費を計算 ──────────
  // 過去月のキー一覧（baseYM の 1か月前 〜 lookbackMonths か月前）
  const pastYMs: string[] = [];
  for (let i = 1; i <= lookbackMonths; i++) {
    pastYMs.push(shiftMonth(baseYM, -i));
  }

  // 過去月の収入合計の平均（履歴ゼロなら 0）
  const totalPastIncome = pastYMs.reduce((sum, ym) => {
    return sum + incomes
      .filter(inc => inc.date.startsWith(ym))
      .reduce((s, inc) => s + (inc.amount || 0), 0);
  }, 0);
  const avgIncome = pastYMs.length > 0 ? totalPastIncome / pastYMs.length : 0;

  // 過去月の変動支出合計の平均（履歴ゼロなら 0）
  const totalPastVariable = pastYMs.reduce((sum, ym) => {
    return sum + transactions
      .filter(tx => tx.date.startsWith(ym))
      .reduce((s, tx) => s + (tx.amount || 0), 0);
  }, 0);
  const avgVariable = pastYMs.length > 0 ? totalPastVariable / pastYMs.length : 0;

  // ── 将来 N 月分の予測を生成 ──────────
  const result: ForecastMonth[] = [];
  for (let i = 1; i <= monthsAhead; i++) {
    const yearMonth = shiftMonth(baseYM, i);
    const [, mo] = parseYearMonth(yearMonth);

    const estimatedExpense = Math.round(certainExpense + avgVariable);
    const estimatedIncome = Math.round(avgIncome);
    const estimatedNet = estimatedIncome - estimatedExpense;

    result.push({
      label: `${mo}月`,
      yearMonth,
      income: estimatedIncome,
      expense: estimatedExpense,
      net: estimatedNet,
    });
  }

  return result;
}
