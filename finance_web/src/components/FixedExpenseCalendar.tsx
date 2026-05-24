// ────────── 固定費カレンダーコンポーネント ──────────
// 今月の固定費引落日を日付順に並べて一覧表示する
// 「今月あといくら引き落とされるか」を把握しやすくする

import { useMemo } from "react";
import { FixedExpense } from "../types";
import { formatYen } from "../utils/format";
import {
  STYLE_CARD,
  COLOR_TEXT_HINT,
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_SECONDARY,
  COLOR_BORDER,
  COLOR_NEGATIVE,
} from "../utils/styles";

interface FixedExpenseCalendarProps {
  fixedExpenses: FixedExpense[];
}

// "1日" → 1, "15日" → 15, "未設定" → null のように数値に変換する
function parsePayDay(payDay: string): number | null {
  const m = payDay.match(/^(\d+)日$/);
  return m ? Number(m[1]) : null;
}

export default function FixedExpenseCalendar({ fixedExpenses }: FixedExpenseCalendarProps) {
  const today = new Date();
  const todayDay = today.getDate(); // 今日の日付（1〜31）

  // アクティブな固定費だけ対象（active が明示的に false のものは除外）
  const active = fixedExpenses.filter(f => f.active !== false);

  // 引落日が設定されている固定費を日付順に並べる
  const sorted = useMemo(() => {
    return active
      .map(f => ({ ...f, day: parsePayDay(f.payDay || "") }))
      .filter(f => f.day !== null)                      // 「未設定」は除外
      .sort((a, b) => a.day - b.day);                  // 日付昇順
  }, [active]);

  // 引落日未設定の固定費
  const noDay = active.filter(f => parsePayDay(f.payDay || "") === null);

  // 表示するデータがなければカード非表示
  if (active.length === 0) return null;

  // 今日以降に残っている引落総額（今日分を含む）
  const remaining = sorted
    .filter(f => f.day >= todayDay)
    .reduce((s, f) => s + Number(f.amount || 0), 0);

  // 今月の固定費合計
  const monthTotal = active.reduce((s, f) => s + Number(f.amount || 0), 0);

  return (
    <div style={STYLE_CARD}>
      {/* ヘッダー */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
        <div style={{ fontSize: 10, color: COLOR_TEXT_HINT, textTransform: "uppercase", letterSpacing: "1.5px" }}>
          引落カレンダー
        </div>
        {/* 残り引落額 */}
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 9, color: COLOR_TEXT_HINT, marginBottom: 2 }}>今月残り</div>
          <div style={{ fontFamily: "monospace", fontSize: 14, fontWeight: 700, color: remaining > 0 ? COLOR_NEGATIVE : COLOR_TEXT_HINT }}>
            {formatYen(remaining)}
          </div>
        </div>
      </div>

      {/* 日付順の引落一覧 */}
      {sorted.map(f => {
        const isPast   = f.day < todayDay;  // 引落済み（今日より前）
        const isToday  = f.day === todayDay; // 今日引き落とし

        return (
          <div
            key={f.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "8px 0",
              borderBottom: `1px solid rgba(255,255,255,0.04)`,
              opacity: isPast ? 0.4 : 1,          // 引落済みはグレーアウト
            }}
          >
            {/* 日付バッジ */}
            <div style={{
              minWidth: 36, height: 36,
              borderRadius: 8,
              background: isToday
                ? "rgba(251,191,36,0.18)"          // 今日は黄色背景
                : isPast
                  ? "rgba(255,255,255,0.05)"        // 引落済みは薄い背景
                  : "rgba(255,255,255,0.08)",        // 未来は通常背景
              border: isToday ? "1px solid rgba(251,191,36,0.5)" : "none",
              display: "flex",
              flexDirection: "column" as const,
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}>
              <span style={{
                fontSize: 14,
                fontWeight: 700,
                lineHeight: 1,
                color: isToday ? "#fbbf24" : isPast ? COLOR_TEXT_HINT : COLOR_TEXT_PRIMARY,
              }}>
                {f.day}
              </span>
              <span style={{ fontSize: 8, color: COLOR_TEXT_HINT, lineHeight: 1, marginTop: 1 }}>日</span>
            </div>

            {/* 名前・カテゴリ */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: 13,
                fontWeight: 600,
                color: isPast ? COLOR_TEXT_HINT : COLOR_TEXT_PRIMARY,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap" as const,
              }}>
                {isPast && "✓ "}{f.name}
              </div>
              <div style={{ fontSize: 10, color: COLOR_TEXT_HINT, marginTop: 1 }}>
                {f.category}
              </div>
            </div>

            {/* 金額 */}
            <div style={{
              fontFamily: "monospace",
              fontSize: 13,
              fontWeight: 700,
              color: isPast ? COLOR_TEXT_HINT : COLOR_NEGATIVE,
              flexShrink: 0,
            }}>
              {formatYen(Number(f.amount || 0))}
            </div>

            {/* 今日バッジ */}
            {isToday && (
              <span style={{
                fontSize: 9, background: "rgba(251,191,36,0.2)", color: "#fbbf24",
                borderRadius: 4, padding: "2px 6px", fontWeight: 700, flexShrink: 0,
              }}>今日</span>
            )}
          </div>
        );
      })}

      {/* 引落日未設定の固定費（まとめて表示） */}
      {noDay.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <div style={{ fontSize: 10, color: COLOR_TEXT_HINT, marginBottom: 6 }}>引落日未設定</div>
          {noDay.map(f => (
            <div key={f.id} style={{
              display: "flex", justifyContent: "space-between",
              padding: "5px 0", fontSize: 12, color: COLOR_TEXT_SECONDARY,
              borderBottom: `1px solid rgba(255,255,255,0.03)`,
            }}>
              <span>{f.name}</span>
              <span style={{ fontFamily: "monospace" }}>{formatYen(Number(f.amount || 0))}</span>
            </div>
          ))}
        </div>
      )}

      {/* 月合計フッター */}
      <div style={{
        display: "flex", justifyContent: "space-between",
        borderTop: `1px solid ${COLOR_BORDER}`,
        paddingTop: 10, marginTop: 10, fontSize: 12,
      }}>
        <span style={{ color: COLOR_TEXT_HINT }}>月合計</span>
        <span style={{ fontFamily: "monospace", fontWeight: 700, color: COLOR_TEXT_PRIMARY }}>
          {formatYen(monthTotal)}
        </span>
      </div>
    </div>
  );
}
