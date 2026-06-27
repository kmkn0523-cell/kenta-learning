// ────────── サブスク棚卸しカード ──────────
// 登録済みの定期支出を「年間いくらか」で見える化し、解約判断を促すカード。
// 月額だと小さく見える出費も、年額（×12）にすると規模が実感できる
import { useMemo } from "react";
import { RecurringExpense } from "../types";
import { buildSubscriptionSummary } from "../utils/subscriptionSummary";
import { formatYen } from "../utils/format";
import {
  COLOR_TEXT_HINT, COLOR_TEXT_SECONDARY, COLOR_TEXT_PRIMARY,
  COLOR_ACCENT, COLOR_NEGATIVE, COLOR_POSITIVE, COLOR_BORDER, STYLE_CARD,
FONT_NUM } from "../utils/styles";

// このカードが受け取る props
interface SubscriptionInventoryProps {
  recurringExpenses: RecurringExpense[];
  icons?: Record<string, string>; // カテゴリ名→絵文字のマップ（任意）
}

export default function SubscriptionInventory({ recurringExpenses, icons }: SubscriptionInventoryProps) {
  // 集計は純粋関数に任せる（再計算は recurringExpenses が変わった時だけ）
  const summary = useMemo(() => buildSubscriptionSummary(recurringExpenses), [recurringExpenses]);

  // 1件も登録が無ければカード自体を出さない
  if (summary.items.length === 0) return null;

  return (
    <div style={STYLE_CARD}>
      {/* ── 見出し ── */}
      <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: 12 }}>
        🗂 サブスク棚卸し
      </div>

      {/* ── 年間合計（一番目立たせる）＋月額の内訳 ── */}
      <div style={{ marginBottom: 4 }}>
        <span style={{ fontSize: 11, color: COLOR_TEXT_HINT, letterSpacing: "0.5px" }}>稼働中サブスクの年間コスト</span>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 14 }}>
        <span style={{ fontFamily: FONT_NUM, fontSize: 26, fontWeight: 700, color: COLOR_NEGATIVE, letterSpacing: "-0.5px" }}>
          {formatYen(summary.annualTotal)}
        </span>
        <span style={{ fontSize: 12, color: COLOR_TEXT_HINT }}>
          /年（{formatYen(summary.monthlyTotal)}/月 × 12）
        </span>
      </div>

      {/* ── 解約判断を促す一言 ── */}
      <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, lineHeight: 1.7, marginBottom: 14 }}>
        年額の大きい順に並んでいます。「本当に年間{summary.annualTotal >= 10000 ? `${Math.round(summary.annualTotal / 10000)}万円` : formatYen(summary.annualTotal)}分の価値があるか」で見直してみましょう。
      </div>

      {/* ── 各サブスクの一覧（稼働中→年額降順、停止中は末尾に淡色で） ── */}
      <div>
        {summary.items.map(item => (
          <div
            key={item.id}
            style={{
              padding: "9px 0",
              borderBottom: `1px solid rgba(255,255,255,0.04)`,
              opacity: item.active ? 1 : 0.45, // 停止中は淡く
            }}
          >
            {/* 名前・カテゴリ と 年額 */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
              <span style={{ fontSize: 13, color: item.active ? COLOR_TEXT_PRIMARY : COLOR_TEXT_HINT, fontWeight: 600 }}>
                {!item.active && "⏸ "}{icons?.[item.category] || ""} {item.name}
              </span>
              <span style={{ fontFamily: FONT_NUM, fontWeight: 700, color: item.active ? COLOR_TEXT_PRIMARY : COLOR_TEXT_HINT, whiteSpace: "nowrap" }}>
                {formatYen(item.annual)}<span style={{ fontSize: 11, color: COLOR_TEXT_HINT }}>/年</span>
              </span>
            </div>
            {/* 月額・割合の補足行 */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 4, fontSize: 11, color: COLOR_TEXT_HINT }}>
              <span>{formatYen(item.monthly)}/月{item.active && item.sharePct > 0 ? ` ・ 全体の${item.sharePct}%` : ""}</span>
            </div>
            {/* 稼働中だけ割合バーを出す（一番太いものが最大の固定費） */}
            {item.active && summary.annualTotal > 0 && (
              <div style={{ height: 4, background: "rgba(255,255,255,0.05)", borderRadius: 2, marginTop: 6, overflow: "hidden" }}>
                <div style={{ width: `${item.sharePct}%`, height: "100%", background: COLOR_ACCENT, borderRadius: 2 }} />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* ── 停止中があれば「節約できている額」を緑で表示 ── */}
      {summary.pausedCount > 0 && (
        <div style={{ marginTop: 12, paddingTop: 10, borderTop: `1px solid ${COLOR_BORDER}`, fontSize: 12, color: COLOR_POSITIVE }}>
          ⏸ 停止中{summary.pausedCount}件で {formatYen(summary.pausedMonthlySaved * 12)}/年 を節約中
        </div>
      )}
    </div>
  );
}
