// ────────── 文字列・数値フォーマットまとめ ──────────

// 文字列の amount から数字以外を除去して整数化
export function parseYenAmount(text: string | number): number {
  if (typeof text === "number") return text;
  const cleaned = String(text).replace(/[^\d]/g, "");
  return cleaned === "" ? 0 : Number(cleaned);
}

// 入力中の amount を 3 桁カンマ付きで整形（例: "12345" → "12,345"）
export function formatAmount(value: string | number | undefined | null): string {
  const digits = String(value ?? "").replace(/[^\d]/g, "");
  if (!digits) return "";
  return Number(digits).toLocaleString("ja-JP");
}

// 金額を「¥1,234」形式で表示
export function formatYen(value: number | string): string {
  return "¥" + Number(value).toLocaleString("ja-JP");
}

// 月のラベル（チャート等で使う）
export const MONTH_LABELS = ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"];

// 変動費カテゴリの一覧
export const EXPENSE_CATEGORIES = ["食費","住居","交通","光熱費","娯楽","医療","衣服","通信費","その他"];

// 固定費カテゴリの一覧
export const FIXED_EXPENSE_CATEGORIES = ["家賃","サブスク","保険","通信費","駐車場","その他固定費"];

// 収入カテゴリの一覧
export const INCOME_CATEGORIES = ["給与","副業","ボーナス","臨時収入","その他収入"];

// 変動費カテゴリの絵文字
export const EXPENSE_CATEGORY_ICONS: Record<string, string> = {"食費":"🍽️","住居":"🏠","交通":"🚃","光熱費":"💡","娯楽":"🎮","医療":"💊","衣服":"👕","通信費":"📱","その他":"📦"};

// 固定費カテゴリの絵文字
export const FIXED_EXPENSE_CATEGORY_ICONS: Record<string, string> = {"家賃":"🏠","サブスク":"🎬","保険":"🛡️","通信費":"📱","駐車場":"🅿️","その他固定費":"📌"};

// 収入カテゴリの絵文字
export const INCOME_CATEGORY_ICONS: Record<string, string> = {"給与":"💼","副業":"💻","ボーナス":"🎁","臨時収入":"✨","その他収入":"💰"};
