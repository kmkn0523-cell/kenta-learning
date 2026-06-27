// ────────── 予算超過警告バナー ──────────
// ダッシュボードの上部に表示する小さなバナー
// 予算が設定されているカテゴリのうち、消化率 80% 以上のものを上位3件まで強調表示する
// 100%超 = 赤（警告）、80〜100% = 黄（注意）

import { useMemo } from "react";
import { formatYen, EXPENSE_CATEGORY_ICONS } from "../utils/format";
import {
  COLOR_TEXT_HINT,
  COLOR_TEXT_SECONDARY,
  COLOR_BORDER,
  COLOR_NEGATIVE,
  COLOR_ACCENT,
  COLOR_TEXT_PRIMARY,
FONT_NUM } from "../utils/styles";

interface BudgetAlertBannerProps {
  // カテゴリ別月予算（{ 食費: 30000, ... }）
  budget: Record<string, number>;
  // 今月のカテゴリ別実績（[カテゴリ名, 金額] の配列・降順）
  expByCat: [string, number][];
  // 今月閲覧中か（今月以外は予算アラートを出さない）
  isCurrentMonth: boolean;
}

interface AlertRow {
  cat: string;
  actual: number;
  budget: number;
  ratio: number;
  level: "warn" | "danger"; // 80%超=warn、100%超=danger
}

export default function BudgetAlertBanner({ budget, expByCat, isCurrentMonth }: BudgetAlertBannerProps) {
  // 予算超過の候補を計算（80%以上のもの・消化率の高い順）
  const alerts: AlertRow[] = useMemo(() => {
    if (!isCurrentMonth) return [];
    const actualByCat: Record<string, number> = Object.fromEntries(expByCat);
    return Object.entries(budget)
      .filter(([, b]) => Number(b) > 0)
      .map(([cat, b]) => {
        const actual = Number(actualByCat[cat] || 0);
        const ratio = actual / Number(b);
        return { cat, actual, budget: Number(b), ratio };
      })
      .filter(r => r.ratio >= 0.8)
      .sort((a, b) => b.ratio - a.ratio)
      .slice(0, 3)
      .map(r => ({ ...r, level: r.ratio >= 1 ? "danger" as const : "warn" as const }));
  }, [budget, expByCat, isCurrentMonth]);

  if (alerts.length === 0) return null;

  // バナー全体の色は最も深刻なレベルに合わせる
  const overallDanger = alerts.some(a => a.level === "danger");
  const accent = overallDanger ? COLOR_NEGATIVE : COLOR_ACCENT;
  const bgTint = overallDanger ? "rgba(248,113,113,0.06)" : "rgba(34,211,238,0.05)";

  return (
    <div style={{
      background: bgTint,
      border: `1px solid ${accent}44`,
      borderRadius: 14,
      padding: "12px 14px",
      marginBottom: 14,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
        <span style={{ fontSize: 14 }}>{overallDanger ? "⚠️" : "📊"}</span>
        <span style={{ fontSize: 12, fontWeight: 700, color: accent, letterSpacing: "1px", textTransform: "uppercase" }}>
          {overallDanger ? "予算超過アラート" : "予算消化注意"}
        </span>
      </div>
      {alerts.map(({ cat, actual, budget: b, ratio, level }) => {
        const lineColor = level === "danger" ? COLOR_NEGATIVE : COLOR_ACCENT;
        return (
          <div key={cat} style={{ marginBottom: 6 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 12, marginBottom: 3 }}>
              <span style={{ color: COLOR_TEXT_PRIMARY }}>
                {EXPENSE_CATEGORY_ICONS[cat] || ""} {cat}
              </span>
              <span style={{ fontFamily: FONT_NUM, color: lineColor, fontWeight: 600 }}>
                {Math.round(ratio * 100)}%
              </span>
            </div>
            {/* 消化バー：100%を超えても見やすいよう100%でクリップ */}
            <div style={{ height: 4, background: "rgba(255,255,255,0.06)", borderRadius: 2, overflow: "hidden", marginBottom: 3 }}>
              <div style={{
                height: "100%",
                width: `${Math.min(100, ratio * 100)}%`,
                background: lineColor,
                borderRadius: 2,
                transition: "width 0.4s ease",
              }}/>
            </div>
            <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, fontFamily: FONT_NUM }}>
              {formatYen(actual)} / {formatYen(b)}
              {ratio > 1 && (
                <span style={{ marginLeft: 6, color: COLOR_NEGATIVE }}>
                  超過 +{formatYen(actual - b)}
                </span>
              )}
            </div>
          </div>
        );
      })}
      <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginTop: 4, lineHeight: 1.5 }}>
        {overallDanger
          ? "支出タブで該当カテゴリを見直しましょう"
          : "残りの日数に注意して使い方を調整しましょう"}
      </div>
    </div>
  );
}
