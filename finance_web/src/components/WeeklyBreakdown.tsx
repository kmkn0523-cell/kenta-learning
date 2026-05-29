// ────────── 週別支出内訳コンポーネント ──────────
// 選択中の月の支出を第1〜4週に分けて集計し、
// どの週に使いすぎているかを一目で確認できるカード

import { useMemo } from "react";
import { formatYen } from "../utils/format";
import {
  STYLE_CARD,
  COLOR_TEXT_HINT,
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_SECONDARY,
  COLOR_BORDER,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
} from "../utils/styles";

// 支出1件のデータ型（date と amount だけ使う）
interface TxEntry {
  date?: string;
  amount?: number | string;
}

// このコンポーネントが受け取る props の型
interface WeeklyBreakdownProps {
  // 表示中の月の支出一覧（日付フィルタ済み）
  mTx: TxEntry[];
  // 選択中の年（週の日付範囲計算に使う）
  selectedYear: number;
  // 選択中の月（0〜11）
  selectedMonth: number;
}

// 週の定義：第1〜4週の開始日と終了日（1〜31の日数）
const WEEKS = [
  { label: "第1週", from: 1,  to: 7  },
  { label: "第2週", from: 8,  to: 14 },
  { label: "第3週", from: 15, to: 21 },
  { label: "第4週", from: 22, to: 31 }, // 月末まで（月によって日数が変わる）
] as const;

export default function WeeklyBreakdown({ mTx, selectedYear, selectedMonth }: WeeklyBreakdownProps) {

  // 各週の支出合計と日付範囲を計算する
  const weeks = useMemo(() => {
    // その月の最終日（例：2月なら28か29）
    const lastDay = new Date(selectedYear, selectedMonth + 1, 0).getDate();

    return WEEKS.map(w => {
      // 第4週の終了日は月末に合わせる
      const actualTo = Math.min(w.to, lastDay);
      // "2026-05-08" 〜 "2026-05-14" のような表示用文字列
      const mm = String(selectedMonth + 1).padStart(2, "0");
      const fromStr = `${String(w.from).padStart(2, "0")}`;
      const toStr   = `${String(actualTo).padStart(2, "0")}`;
      const rangeLabel = `${fromStr}〜${toStr}日`;

      // その週に含まれる日付（"YYYY-MM-DD" 形式）を使って支出を絞り込む
      const prefix = `${selectedYear}-${mm}-`;
      const total = mTx
        .filter(t => {
          if (!t.date?.startsWith(prefix)) return false;
          const day = Number(t.date.slice(8, 10)); // "2026-05-08" → 8
          return day >= w.from && day <= actualTo;
        })
        .reduce((s, t) => s + Number(t.amount || 0), 0);

      return { label: w.label, rangeLabel, total, from: w.from, to: actualTo };
    });
  }, [mTx, selectedYear, selectedMonth]);

  // 全週合計（バーの幅計算に使う）
  const grandTotal = weeks.reduce((s, w) => s + w.total, 0);

  // 最も支出が多い週（ハイライト用）
  const maxTotal = Math.max(...weeks.map(w => w.total));

  // 支出がある週が1件もなければカード自体を表示しない
  if (grandTotal === 0) return null;

  // 今日が選択中の月かどうかを確認（今週ハイライト用）
  const today = new Date();
  const isCurMonth = today.getFullYear() === selectedYear && today.getMonth() === selectedMonth;
  const todayDay = today.getDate();

  return (
    <div style={STYLE_CARD}>
      {/* ヘッダー */}
      <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: 14 }}>
        週別支出
      </div>

      {/* 週ごとの行 */}
      {weeks.map(w => {
        // バーの幅：最も高い週を100%として相対比率で計算
        const barWidth = maxTotal > 0 ? (w.total / maxTotal) * 100 : 0;

        // 今週かどうか（今月表示中 かつ 今日がその週の範囲内）
        const isThisWeek = isCurMonth && todayDay >= w.from && todayDay <= w.to;

        // 最も支出が多い週を赤っぽく、最も少ない週を緑っぽく
        const isMax = w.total === maxTotal && w.total > 0;
        const barColor = isMax ? COLOR_NEGATIVE : COLOR_POSITIVE;

        return (
          <div key={w.label} style={{ marginBottom: 12 }}>
            {/* ラベル行：週名・日付範囲・金額 */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 12, marginBottom: 5 }}>
              {/* 左側：週ラベルと日付範囲 */}
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ color: isThisWeek ? "#22d3ee" : COLOR_TEXT_PRIMARY, fontWeight: isThisWeek ? 700 : 500 }}>
                  {w.label}
                </span>
                {/* 今週バッジ */}
                {isThisWeek && (
                  <span style={{
                    fontSize: 8, background: "rgba(34,211,238,0.2)", color: "#22d3ee",
                    borderRadius: 3, padding: "1px 4px", fontWeight: 700,
                  }}>今週</span>
                )}
                <span style={{ fontSize: 12, color: COLOR_TEXT_HINT }}>{w.rangeLabel}</span>
              </div>
              {/* 右側：金額 */}
              <span style={{ fontFamily: "monospace", fontWeight: 700, color: isMax ? COLOR_NEGATIVE : COLOR_TEXT_SECONDARY }}>
                {w.total > 0 ? formatYen(w.total) : "−"}
              </span>
            </div>

            {/* プログレスバー */}
            {w.total > 0 && (
              <div style={{ height: 4, background: "rgba(255,255,255,0.07)", borderRadius: 2, overflow: "hidden" }}>
                <div style={{
                  height: "100%",
                  width: barWidth + "%",
                  background: barColor,
                  borderRadius: 2,
                  transition: "width 0.4s ease",
                  opacity: isMax ? 1 : 0.65,
                }}/>
              </div>
            )}
          </div>
        );
      })}

      {/* 合計行 */}
      <div style={{
        display: "flex", justifyContent: "space-between",
        borderTop: `1px solid ${COLOR_BORDER}`, paddingTop: 10, marginTop: 4,
        fontSize: 12,
      }}>
        <span style={{ color: COLOR_TEXT_HINT }}>月計</span>
        <span style={{ fontFamily: "monospace", fontWeight: 700, color: COLOR_TEXT_PRIMARY }}>
          {formatYen(grandTotal)}
        </span>
      </div>
    </div>
  );
}
