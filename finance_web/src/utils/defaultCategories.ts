// ────────── デフォルトカテゴリ設定の生成 ──────────
// format.ts の定数からアプリ起動時のデフォルト CategoryConfig を作る
import { CategoryConfig } from "../types";
import {
  EXPENSE_CATEGORIES,
  FIXED_EXPENSE_CATEGORIES,
  INCOME_CATEGORIES,
  EXPENSE_CATEGORY_ICONS,
  FIXED_EXPENSE_CATEGORY_ICONS,
  INCOME_CATEGORY_ICONS,
} from "./format";

// format.ts のカテゴリ配列から CategoryItem[] に変換する
export function makeDefaultCategoryConfig(): CategoryConfig {
  return {
    expense: EXPENSE_CATEGORIES.map((name, i) => ({
      id: `exp-${i}`,
      name,
      icon: EXPENSE_CATEGORY_ICONS[name] || "📦",
      order: i,
    })),
    fixedExpense: FIXED_EXPENSE_CATEGORIES.map((name, i) => ({
      id: `fix-${i}`,
      name,
      icon: FIXED_EXPENSE_CATEGORY_ICONS[name] || "📦",
      order: i,
    })),
    income: INCOME_CATEGORIES.map((name, i) => ({
      id: `inc-${i}`,
      name,
      icon: INCOME_CATEGORY_ICONS[name] || "💰",
      order: i,
    })),
  };
}
