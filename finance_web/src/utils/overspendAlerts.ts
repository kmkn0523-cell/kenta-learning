// ────────── 使いすぎアラートの判定（純粋関数・React非依存） ──────────
// 当月のカテゴリ別支出と予算を比べ、80%/100%を新たに超えたカテゴリを返す。
// 同じ月・同じカテゴリ・同じ段階は一度しか鳴らさない（通知ログで抑制）。

// 通知1件分の情報
export interface OverspendAlert {
  category: string;   // 例: "食費"
  level: 80 | 100;    // 段階（80%注意 / 100%オーバー）
  spent: number;      // 当月の支出
  budget: number;     // 予算
  ratio: number;      // spent / budget（例: 0.85）
}

// 通知ログ: 月("YYYY-MM") -> ["食費|80","食費|100", ...]
export type NotifyLog = Record<string, string[]>;

// その段階を既に通知済みかを表すキー
function logKey(category: string, level: 80 | 100): string {
  return `${category}|${level}`;
}

// 当月の状況から「新たに鳴らすべきアラート」と「更新後ログ」を返す
export function evaluateOverspend(
  actual: Record<string, number>,
  budget: Record<string, number>,
  log: NotifyLog,
  month: string
): { alerts: OverspendAlert[]; nextLog: NotifyLog } {
  // 当月のログ配列（無ければ空）をコピーして使う
  const monthLog = new Set(log[month] ?? []);
  const alerts: OverspendAlert[] = [];

  // 予算が設定されているカテゴリだけを見る
  for (const category of Object.keys(budget)) {
    const budgetAmount = Number(budget[category] || 0);
    if (budgetAmount <= 0) continue;               // 予算未設定は対象外（ゼロ除算も防ぐ）
    const spent = Number(actual[category] || 0);
    const ratio = spent / budgetAmount;

    if (ratio >= 1.0 && !monthLog.has(logKey(category, 100))) {
      // 100%超え：まだ100%通知をしていなければ鳴らす
      alerts.push({ category, level: 100, spent, budget: budgetAmount, ratio });
      monthLog.add(logKey(category, 100));
      monthLog.add(logKey(category, 80)); // 80%も済み扱いにして二重通知を防ぐ
    } else if (ratio >= 0.8 && !monthLog.has(logKey(category, 80))) {
      // 80%超え：まだ80%通知をしていなければ鳴らす
      alerts.push({ category, level: 80, spent, budget: budgetAmount, ratio });
      monthLog.add(logKey(category, 80));
    }
  }

  const nextLog: NotifyLog = { ...log, [month]: Array.from(monthLog) };
  return { alerts, nextLog };
}

// 当月以外の古いログを落とす（肥大化防止）
export function pruneLog(log: NotifyLog, month: string): NotifyLog {
  return month in log ? { [month]: log[month] } : {};
}
