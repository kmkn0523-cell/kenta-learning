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
