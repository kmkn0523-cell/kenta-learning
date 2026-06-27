// ────────── 曜日別支出コンポーネント ──────────
// 選択中の月の支出を月〜日の7曜日に分けて集計し、
// どの曜日に使いがちかを一目で確認できるカード

import { useMemo, CSSProperties } from "react";
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
interface DayOfWeekBreakdownProps {
  // 表示中の月の支出一覧（日付フィルタ済み）
  mTx: TxEntry[];
}

// ── スタイル定数 ──────────────────────────────────────────

// 曜日バッジ（丸型）の静的スタイル（background は支出有無・最大曜日で動的切り替え）
const STYLE_DOW_BADGE_BASE: CSSProperties = {
  width: 26, height: 26, borderRadius: "50%",
  display: "flex", alignItems: "center", justifyContent: "center",
  flexShrink: 0,
};

// ─────────────────────────────────────────────────────────

// 曜日の定義：getDay() が返す 0=日〜6=土 に対応する日本語ラベル
// 月曜始まり（月火水木金土日）で表示する
const DAY_ORDER = [1, 2, 3, 4, 5, 6, 0] as const; // 月〜土、日
const DAY_LABELS: Record<number, string> = {
  0: "日", 1: "月", 2: "火", 3: "水", 4: "木", 5: "金", 6: "土",
};
// 土曜・日曜は色を変えて週末感を出す
const DAY_COLOR: Record<number, string | null> = {
  0: "#f87171",  // 日：赤
  1: null,       // 月：デフォルト
  2: null,
  3: null,
  4: null,
  5: null,
  6: "#60a5fa",  // 土：青
};

export default function DayOfWeekBreakdown({ mTx }: DayOfWeekBreakdownProps) {

  // 曜日ごとの支出合計と件数を集計する
  const dayStats = useMemo(() => {
    // dayNum(0〜6) → {total, count} を初期化
    const stats: Record<number, { total: number; count: number }> = {};
    for (let d = 0; d <= 6; d++) stats[d] = { total: 0, count: 0 };

    mTx.forEach(t => {
      if (!t.date) return;
      // "YYYY-MM-DD" を Date に変換して曜日を取得（例："2026-05-24" → 6=土）
      const dt = new Date(t.date + "T00:00:00"); // ローカルタイムで解釈させる
      const dow = dt.getDay(); // 0=日, 1=月 ... 6=土
      stats[dow].total += Number(t.amount || 0);
      stats[dow].count++;
    });

    return stats;
  }, [mTx]);

  // 月〜日の順に並べた配列（表示用）
  const rows = DAY_ORDER.map(d => ({
    dow: d,
    label: DAY_LABELS[d],
    total: dayStats[d].total,
    count: dayStats[d].count,
  }));

  // 全曜日の合計支出
  const grandTotal = rows.reduce((s, r) => s + r.total, 0);

  // 支出ゼロなら非表示
  if (grandTotal === 0) return null;

  // 最も支出の多い曜日（ハイライト用）
  const maxTotal = Math.max(...rows.map(r => r.total));

  // 1曜日あたりの平均支出（参考表示用）
  const activeDays = rows.filter(r => r.count > 0).length;
  const avgPerActiveDay = activeDays > 0 ? Math.round(grandTotal / activeDays) : 0;

  return (
    <div style={STYLE_CARD}>
      {/* ヘッダー */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
        <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, textTransform: "uppercase", letterSpacing: "1.5px" }}>
          曜日別支出
        </div>
        {/* 1曜日平均を右に小さく表示 */}
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginBottom: 1 }}>使った曜日の平均</div>
          <div style={{ fontFamily: FONT_NUM, fontSize: 12, color: COLOR_TEXT_SECONDARY }}>
            {formatYen(avgPerActiveDay)}
          </div>
        </div>
      </div>

      {/* 曜日ごとの行 */}
      {rows.map(r => {
        // バー幅：最も高い曜日を100%として相対比率で計算
        const barWidth = maxTotal > 0 ? (r.total / maxTotal) * 100 : 0;
        // 最大支出曜日は赤、他は緑（週末は別途色分けあり）
        const isMax = r.total === maxTotal && r.total > 0;
        const weekendColor = DAY_COLOR[r.dow]; // 土=青, 日=赤, 平日=null
        // ラベルの色優先順：最大支出=赤 > 土=青 > 日=赤 > デフォルト
        const labelColor = isMax
          ? COLOR_NEGATIVE
          : weekendColor ?? COLOR_TEXT_PRIMARY;
        const barColor = isMax
          ? COLOR_NEGATIVE
          : weekendColor ?? COLOR_POSITIVE;

        return (
          <div key={r.dow} style={{ marginBottom: 10 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              {/* 曜日バッジ（丸型） */}
              <div style={{
                ...STYLE_DOW_BADGE_BASE,
                background: r.total > 0
                  ? (isMax ? "rgba(248,113,113,0.15)" : "rgba(255,255,255,0.06)")
                  : "rgba(255,255,255,0.03)",
              }}>
                <span style={{
                  fontSize: 12,
                  fontWeight: 700,
                  color: r.total > 0 ? labelColor : COLOR_TEXT_HINT,
                }}>
                  {r.label}
                </span>
              </div>

              {/* プログレスバー */}
              <div style={{ flex: 1, height: 4, background: "rgba(255,255,255,0.07)", borderRadius: 2, overflow: "hidden" }}>
                {r.total > 0 && (
                  <div style={{
                    height: "100%",
                    width: barWidth + "%",
                    background: barColor,
                    borderRadius: 2,
                    transition: "width 0.4s ease",
                    opacity: isMax ? 1 : 0.65,
                  }}/>
                )}
              </div>

              {/* 金額と件数 */}
              <div style={{ textAlign: "right", flexShrink: 0, minWidth: 72 }}>
                {r.total > 0 ? (
                  <>
                    <span style={{
                      fontFamily: FONT_NUM, fontSize: 12, fontWeight: 700,
                      color: isMax ? COLOR_NEGATIVE : COLOR_TEXT_SECONDARY,
                    }}>
                      {formatYen(r.total)}
                    </span>
                    {/* 件数を小さく右端に */}
                    <span style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginLeft: 4 }}>
                      {r.count}件
                    </span>
                  </>
                ) : (
                  <span style={{ fontSize: 12, color: "rgba(255,255,255,0.15)" }}>−</span>
                )}
              </div>
            </div>
          </div>
        );
      })}

      {/* 月合計フッター */}
      <div style={{
        display: "flex", justifyContent: "space-between",
        borderTop: `1px solid ${COLOR_BORDER}`,
        paddingTop: 10, marginTop: 4, fontSize: 12,
      }}>
        <span style={{ color: COLOR_TEXT_HINT }}>月計</span>
        <span style={{ fontFamily: FONT_NUM, fontWeight: 700, color: COLOR_TEXT_PRIMARY }}>
          {formatYen(grandTotal)}
        </span>
      </div>
    </div>
  );
}
