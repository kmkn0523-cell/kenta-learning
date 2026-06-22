// ────────── サブスク棚卸し（年間コスト集計） ──────────
// 登録済みの繰り返し支出（サブスク・ジム代等）を「年間いくらか」で見える化し、
// 解約判断を促すための集計を行う純粋関数。UIから切り離してテストしやすくする
import { RecurringExpense } from "../types";

// 棚卸し一覧の1行分
export interface SubscriptionItem {
  id: string;
  name: string;
  category: string;
  monthly: number;   // 月額（円）
  annual: number;    // 年額（円） = 月額 × 12
  active: boolean;    // 稼働中か（false は停止中＝集計対象外）
  sharePct: number;   // 稼働中の年額合計に占める割合（%・停止中は0）
}

// 棚卸し全体のサマリー
export interface SubscriptionSummary {
  items: SubscriptionItem[];     // 稼働中→年額降順、停止中→末尾に年額降順
  activeCount: number;           // 稼働中の件数
  pausedCount: number;           // 停止中の件数
  monthlyTotal: number;          // 稼働中の月額合計（円）
  annualTotal: number;           // 稼働中の年額合計（円）= 月額合計 × 12
  pausedMonthlySaved: number;    // 停止中の月額合計（円）＝止めて節約できている額
}

// 繰り返し支出の配列から棚卸しサマリーを作る
export function buildSubscriptionSummary(recurringExpenses: RecurringExpense[]): SubscriptionSummary {
  // 配列でなければ空のサマリーを返す（壊れたデータでも落ちないように）
  if (!Array.isArray(recurringExpenses)) {
    return { items: [], activeCount: 0, pausedCount: 0, monthlyTotal: 0, annualTotal: 0, pausedMonthlySaved: 0 };
  }

  // active が明示的に false のものだけ停止中扱い（未設定は稼働中とみなす）
  const monthlyTotal = recurringExpenses
    .filter(r => r.active !== false)
    .reduce((sum, r) => sum + (Number(r.amount) || 0), 0);
  const annualTotal = monthlyTotal * 12;

  // 停止中の月額合計（止めて節約できている額）
  const pausedMonthlySaved = recurringExpenses
    .filter(r => r.active === false)
    .reduce((sum, r) => sum + (Number(r.amount) || 0), 0);

  // 各行を組み立てる
  const items: SubscriptionItem[] = recurringExpenses.map(r => {
    const monthly = Number(r.amount) || 0;
    const active = r.active !== false;
    return {
      id: r.id,
      name: r.name,
      category: r.category,
      monthly,
      annual: monthly * 12,
      active,
      // 割合は稼働中のみ計算（停止中は0）。年額合計0なら0%
      sharePct: active && annualTotal > 0 ? Math.round((monthly * 12 / annualTotal) * 100) : 0,
    };
  });

  // 稼働中を先に・それぞれ年額の高い順に並べる（大きい固定費を上に出して解約判断を促す）
  items.sort((a, b) => {
    if (a.active !== b.active) return a.active ? -1 : 1;
    return b.annual - a.annual;
  });

  return {
    items,
    activeCount: recurringExpenses.filter(r => r.active !== false).length,
    pausedCount: recurringExpenses.filter(r => r.active === false).length,
    monthlyTotal,
    annualTotal,
    pausedMonthlySaved,
  };
}
