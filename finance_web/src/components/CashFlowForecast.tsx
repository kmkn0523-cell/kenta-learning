// ────────── 将来キャッシュフロー予測チャート ──────────
// 過去3か月の平均値と確定固定費から、6か月先の収入・支出・手残りを棒グラフで表示する

import { useMemo, CSSProperties } from "react";
import {
  BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { ForecastMonth } from "../utils/cashFlowForecast";
import { formatYen } from "../utils/format";
import {
  COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_TEXT_PRIMARY,
  COLOR_TEXT_HINT, COLOR_TEXT_SECONDARY, COLOR_BORDER, STYLE_CARD, FONT_NUM,
} from "../utils/styles";

// ── スタイル定数 ──────────────────────────────────────────

const STYLE_HEADER: CSSProperties = {
  display: "flex", alignItems: "center", justifyContent: "space-between",
  marginBottom: 4,
};

const STYLE_TITLE: CSSProperties = {
  fontSize: 11, letterSpacing: "2px", color: "#22d3ee",
  textTransform: "uppercase", fontWeight: 600,
};

const STYLE_NOTE: CSSProperties = {
  fontSize: 10, color: COLOR_TEXT_HINT, marginBottom: 12, lineHeight: 1.5,
};

// ── ツールチップ ──────────────────────────────────────────

// recharts のカスタムツールチップが受け取る props の型
interface TooltipProps {
  active?: boolean;
  payload?: { dataKey: string; name: string; value: number; color: string }[];
  label?: string;
}

function CustomTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload?.length) return null;

  // income と expense を payload から取り出す
  const incEntry = payload.find(p => p.dataKey === "income");
  const expEntry = payload.find(p => p.dataKey === "expense");
  const inc = incEntry?.value ?? 0;
  const exp = expEntry?.value ?? 0;
  const net = inc - exp;

  return (
    <div style={{
      background: "#0b1220", border: `1px solid ${COLOR_BORDER}`,
      borderRadius: 10, padding: "10px 14px", fontSize: 12,
    }}>
      {/* 月ラベル */}
      <div style={{ color: COLOR_TEXT_PRIMARY, fontWeight: 700, marginBottom: 6 }}>{label}</div>
      {/* 収入 */}
      <div style={{ color: COLOR_POSITIVE, fontFamily: FONT_NUM }}>
        収入　{formatYen(inc)}
      </div>
      {/* 支出 */}
      <div style={{ color: COLOR_NEGATIVE, fontFamily: FONT_NUM }}>
        支出　{formatYen(exp)}
      </div>
      {/* 手残り */}
      <div style={{ color: net >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE, fontFamily: FONT_NUM, fontWeight: 700, marginTop: 4 }}>
        手残り　{net >= 0 ? "+" : ""}{formatYen(net)}
      </div>
    </div>
  );
}

// ── メインコンポーネント ──────────────────────────────────

interface CashFlowForecastProps {
  // buildCashFlowForecast で生成した予測データ
  forecast: ForecastMonth[];
}

export default function CashFlowForecast({ forecast }: CashFlowForecastProps) {
  // recharts に渡すデータ（income / expense を正の値で持たせ、視覚的に並べる）
  const chartData = useMemo(
    () => forecast.map(f => ({
      label: f.label,
      income: f.income,
      expense: f.expense,
      net: f.net,
    })),
    [forecast]
  );

  // 手残りの最小値（Y軸の下限を少し広げるために使う）
  const minNet = useMemo(
    () => Math.min(...forecast.map(f => f.net), 0),
    [forecast]
  );

  // Y軸の最大値（収入と支出どちらが大きくても収まるように）
  const yMax = useMemo(
    () => Math.max(...forecast.map(f => Math.max(f.income, f.expense)), 1) * 1.1,
    [forecast]
  );

  return (
    <div style={{ ...STYLE_CARD }}>
      {/* タイトル行 */}
      <div style={STYLE_HEADER}>
        <span style={STYLE_TITLE}>6か月先の収支予測</span>
      </div>

      {/* 注記：推定の根拠を1行で説明 */}
      <div style={STYLE_NOTE}>
        収入・変動費は過去3か月平均／固定費・ローンは登録済み確定値
      </div>

      {/* 棒グラフ本体 */}
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={chartData} barCategoryGap="30%" barGap={3}
          margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>

          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" vertical={false} />

          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: COLOR_TEXT_HINT }}
            axisLine={false}
            tickLine={false}
          />

          {/* 左軸：金額（万円単位） */}
          <YAxis
            tickFormatter={v => `${Math.round(v / 10000)}万`}
            tick={{ fontSize: 10, fill: COLOR_TEXT_HINT, fontFamily: FONT_NUM }}
            axisLine={false}
            tickLine={false}
            domain={[0, yMax]}
            width={40}
          />

          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />

          {/* 0円ラインを細く引く（手残りがマイナスになるとき視覚的に分かりやすい） */}
          <ReferenceLine y={0} stroke="rgba(148,163,184,0.3)" strokeDasharray="4 2" />

          {/* 収入バー（緑） */}
          <Bar dataKey="income" name="収入" fill={COLOR_POSITIVE}
            fillOpacity={0.85} radius={[4, 4, 0, 0]} />

          {/* 支出バー（赤） */}
          <Bar dataKey="expense" name="支出" fill={COLOR_NEGATIVE}
            fillOpacity={0.75} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>

      {/* 月ごとの手残りを数値で一覧表示 */}
      <div style={{ display: "flex", gap: 4, marginTop: 10, justifyContent: "space-between" }}>
        {forecast.map(f => (
          <div key={f.yearMonth} style={{ flex: 1, textAlign: "center" }}>
            <div style={{
              fontSize: 10, fontFamily: FONT_NUM, fontWeight: 700,
              color: f.net >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE,
            }}>
              {f.net >= 0 ? "+" : ""}{formatYen(f.net)}
            </div>
            <div style={{ fontSize: 9, color: COLOR_TEXT_HINT, marginTop: 1 }}>
              {f.label}手残
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
