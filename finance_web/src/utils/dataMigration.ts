import { Tx, Income, FixedExpense, Loan } from "../types";

export function coerceAmountToNumber(value: unknown): number {
  if (typeof value === "number") return value;
  if (typeof value === "string") {
    const cleaned = value.replace(/[^\d.-]/g, "");
    return cleaned === "" ? 0 : Number(cleaned);
  }
  return 0;
}

export function migrateTransactions(items: any[]): Tx[] {
  if (!Array.isArray(items)) return [];
  return items.map(item => {
    const memo = item.memo ?? item.note ?? "";
    const { note, ...rest } = item;
    return { ...rest, amount: coerceAmountToNumber(item.amount), memo };
  });
}

export function migrateIncomes(items: any[]): Income[] {
  if (!Array.isArray(items)) return [];
  return items.map(item => ({ ...item, amount: coerceAmountToNumber(item.amount) }));
}

export function migrateFixedExpenses(items: any[]): FixedExpense[] {
  if (!Array.isArray(items)) return [];
  return items.map(item => ({ ...item, amount: coerceAmountToNumber(item.amount) }));
}

export function migrateLoans(items: any[]): Loan[] {
  if (!Array.isArray(items)) return [];
  return items.map(item => ({
    ...item,
    rate: coerceAmountToNumber(item.rate),
    remaining: coerceAmountToNumber(item.remaining),
    monthly: coerceAmountToNumber(item.monthly),
    principal: coerceAmountToNumber(item.principal),
  }));
}

// ────────── 同期用：レコードに updatedAt を補完する ──────────
// 設計書 docs/finance_web_sync_design_v2.md §3。
// 複数端末同期では各レコードの「最終更新時刻」を比べて新しい方を採用するため、
// 同期を始める前から localStorage にある既存データには updatedAt が無い。
// この関数で初回に一度だけ補完する。既に updatedAt があるレコードは触らない（冪等）ので、
// 毎回の読み込みで呼んでも時刻がリセットされない。
export function backfillUpdatedAt<T extends object>(
  items: T[],
  timestamp: string
): (T & { updatedAt: string })[] {
  if (!Array.isArray(items)) return [];
  return items.map(item => {
    const existing = (item as { updatedAt?: string }).updatedAt;
    // 既に時刻があればそのまま、無ければ timestamp を足した新オブジェクトを返す
    return existing
      ? (item as T & { updatedAt: string })
      : { ...item, updatedAt: timestamp };
  });
}
