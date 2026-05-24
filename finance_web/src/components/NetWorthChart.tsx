// ────────── 純資産（累積手残り）推移グラフ ──────────
// 過去12ヶ月の月次「収入 − 支出」を積み上げた累積グラフを表示する
// MonthlyChart とは別に、「貯まっているかどうか」が一目でわかる折れ線グラフ

import { useMemo } from "react";
import {
  LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { formatYen } from "../utils/format";
import {
  COLOR_ACCENT,
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_HINT,
  COLOR_BORDER,
  STYLE_CARD,
} from "../utils/styles";

// このコンポーネントが受け取る props の型
interface NetWorthChartProps {
  // 変動支出の全履歴（期間フィルターはこのコンポーネント内でかける）
  tx: { date?: string; amount?: number | string }[];
  // 収入の全履歴
  inc: { date?: string; amount?: number | string }[];
  // 固定費の月額合計（全期間共通として使う近似値）
  tFx: number;
}

// カスタムツールチップの props 型
interface TooltipProps {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
}

// ツールチップ：グラフの棒にホバーしたときに表示される吹き出し
function CustomTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload?.length) return null;
  const value = payload[0].value;
  const isPositive = value >= 0;
  return (
    <div style={{
      background: "rgba(7,11,20,0.97)",
      border: `1px solid ${COLOR_BORDER}`,
      borderRadius: 10,
      padding: "10px 14px",
      fontSize: 13,
    }}>
      {/* 月ラベル（例: "5月"） */}
      <div style={{ color: COLOR_TEXT_HINT, marginBottom: 4 }}>{label}</div>
      {/* 累積手残り金額（プラスなら水色、マイナスなら赤） */}
      <div style={{ color: isPositive ? COLOR_ACCENT : "#f87171", fontWeight: 700, fontFamily: "monospace" }}>
        {isPositive ? "+" : ""}{formatYen(value)}
      </div>
    </div>
  );
}

export default function NetWorthChart({ tx, inc, tFx }: NetWorthChartProps) {
  // 過去12ヶ月分の「月」文字列一覧を生成する（例: ["2025-6", ..., "2026-5"]）
  const months = useMemo(() => {
    const now = new Date();
    // 12ヶ月前から今月まで順番に並べる
    return Array.from({ length: 12 }, (_, i) => {
      const d = new Date(now.getFullYear(), now.getMonth() - 11 + i, 1);
      return {
        // グラフのキーとして使う文字列（例: "2026-05"）
        key: d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0"),
        // X軸ラベルとして表示する短い文字列（例: "5月"）
        label: String(d.getMonth() + 1) + "月",
      };
    });
  }, []);

  // 月ごとの「収入 − 支出」を計算し、累積値を積み上げる
  const chartData = useMemo(() => {
    let cumulative = 0;
    return months.map(({ key, label }) => {
      // その月の変動支出合計
      const varExp = tx
        .filter(t => typeof t.date === "string" && t.date.startsWith(key))
        .reduce((s, t) => s + Number(t.amount || 0), 0);

      // その月の収入合計
      const income = inc
        .filter(i => typeof i.date === "string" && i.date.startsWith(key))
        .reduce((s, i) => s + Number(i.amount || 0), 0);

      // 月次手残り = 収入 − 変動支出 − 固定費
      const monthly = income - varExp - tFx;

      // 累積値を足していく（最初から今月まで積み上げた純資産変化）
      cumulative += monthly;

      return {
        label,
        // 表示する値：累積の純資産変化額
        cumulative,
        // 当月だけの手残りをツールチップで補足表示する場合に使う
        monthly,
      };
    });
  }, [months, tx, inc, tFx]);

  return (
    <div style={STYLE_CARD}>
      {/* セクションタイトル */}
      <div style={{
        fontSize: 10,
        color: COLOR_TEXT_HINT,
        textTransform: "uppercase",
        letterSpacing: "1.5px",
        marginBottom: 16,
      }}>
        📈 累積手残り推移（過去12ヶ月）
      </div>

      {/* recharts の折れ線グラフ */}
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={chartData} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
          {/* グリッド線（薄く表示） */}
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(148,163,184,0.1)"
            vertical={false}
          />
          {/* X軸：月ラベル */}
          <XAxis
            dataKey="label"
            tick={{ fontSize: 10, fill: COLOR_TEXT_HINT }}
            axisLine={false}
            tickLine={false}
          />
          {/* Y軸：金額（万円単位で短縮表示） */}
          <YAxis
            tickFormatter={v => `${(v / 10000).toFixed(0)}万`}
            tick={{ fontSize: 10, fill: COLOR_TEXT_HINT }}
            axisLine={false}
            tickLine={false}
            width={36}
          />
          {/* ツールチップ */}
          <Tooltip content={<CustomTooltip />} />
          {/* ゼロ基準線（プラス・マイナスの境界） */}
          <ReferenceLine y={0} stroke="rgba(148,163,184,0.3)" strokeDasharray="4 4" />
          {/* 累積手残りの折れ線 */}
          <Line
            type="monotone"
            dataKey="cumulative"
            stroke={COLOR_ACCENT}
            strokeWidth={2}
            dot={{ fill: COLOR_ACCENT, r: 3, strokeWidth: 0 }}
            activeDot={{ r: 5, fill: COLOR_ACCENT }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* 注釈：最新月の累積値をサマリー表示 */}
      {chartData.length > 0 && (() => {
        const latest = chartData[chartData.length - 1];
        const isPositive = latest.cumulative >= 0;
        return (
          <div style={{
            marginTop: 14,
            paddingTop: 12,
            borderTop: "1px solid rgba(255,255,255,0.06)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}>
            <span style={{ fontSize: 12, color: COLOR_TEXT_HINT }}>
              直近12ヶ月の累積
            </span>
            <span style={{
              fontSize: 15,
              fontWeight: 700,
              fontFamily: "monospace",
              color: isPositive ? COLOR_ACCENT : "#f87171",
            }}>
              {isPositive ? "+" : ""}{formatYen(latest.cumulative)}
            </span>
          </div>
        );
      })()}
    </div>
  );
}
