// ────────── カテゴリ別月次推移グラフ ──────────
// 過去6ヶ月分の変動支出を、上位5カテゴリ + その他に分けた積み上げ棒グラフで表示する
// MonthlyChart（収支全体）と並べて、どのカテゴリにいくら使ったかを月次で追えるようにする目的

import { useMemo } from "react";
import {
  BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { formatYen } from "../utils/format";
import { COLOR_TEXT_PRIMARY, COLOR_TEXT_HINT, COLOR_BORDER, STYLE_CARD } from "../utils/styles";

// 1件の変動支出データ型（必要な3フィールドだけ参照）
interface TxEntry {
  date?: string;
  amount?: number | string;
  category?: string;
}

// このコンポーネントが受け取る props
interface CategoryTrendChartProps {
  tx: TxEntry[];
  // カテゴリ別のアイコン（凡例の絵文字に使う・任意）
  icons?: Record<string, string>;
}

// 上位カテゴリに割り当てる色パレット（6色：top5 + その他）
const PALETTE = ["#22d3ee", "#fb7185", "#facc15", "#a78bfa", "#34d399", "#94a3b8"];

// カスタムツールチップの props 型
interface TooltipProps {
  active?: boolean;
  payload?: { dataKey: string; name: string; value: number; color: string }[];
  label?: string;
  icons?: Record<string, string>;
}

// モジュールスコープに定義（コンポーネント内に置くと毎レンダーで再生成されてしまう）
function CustomTooltip({ active, payload, label, icons }: TooltipProps) {
  if (!active || !payload?.length) return null;
  const total = payload.reduce((s, p) => s + (Number(p.value) || 0), 0);
  return (
    <div style={{ background: "#18181f", border: `1px solid ${COLOR_BORDER}`, borderRadius: 10, padding: "10px 14px", fontSize: 12 }}>
      <div style={{ color: COLOR_TEXT_PRIMARY, fontWeight: 700, marginBottom: 6 }}>{label}（計 {formatYen(total)}）</div>
      {payload
        .filter(p => Number(p.value) > 0)
        .sort((a, b) => Number(b.value) - Number(a.value))
        .map(p => (
          <div key={p.dataKey} style={{ color: p.color, fontFamily: "monospace" }}>
            {icons?.[p.name] || ""} {p.name}: {formatYen(Number(p.value))}
          </div>
        ))}
    </div>
  );
}

export default function CategoryTrendChart({ tx, icons }: CategoryTrendChartProps) {
  // 過去6ヶ月分のデータをカテゴリ別に集計する
  const { data, categories } = useMemo(() => {
    const now = new Date();
    // カテゴリ別の6ヶ月合計（上位を決めるため）
    const totalsByCat: Record<string, number> = {};
    // 月ごとのカテゴリ別合計（チャート描画用）
    const monthlyByCat: Array<{ label: string; byCat: Record<string, number> }> = [];

    for (let i = 5; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const ms = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
      const label = `${d.getMonth() + 1}月`;
      const byCat: Record<string, number> = {};
      tx.filter(t => t.date?.startsWith(ms)).forEach(t => {
        // カテゴリ未設定の支出は「未分類」にまとめる
        const cat = t.category || "未分類";
        const amt = Number(t.amount || 0);
        byCat[cat] = (byCat[cat] || 0) + amt;
        totalsByCat[cat] = (totalsByCat[cat] || 0) + amt;
      });
      monthlyByCat.push({ label, byCat });
    }

    // 6ヶ月合計の多い順に並べて上位5カテゴリを取り出す
    const sorted = Object.entries(totalsByCat).sort((a, b) => b[1] - a[1]);
    const top = sorted.slice(0, 5).map(([cat]) => cat);
    const hasOther = sorted.length > 5;
    const cats = hasOther ? [...top, "その他"] : top;

    // recharts のデータ配列を組み立てる：各行 = 月、列 = カテゴリ
    const chartData = monthlyByCat.map(({ label, byCat }) => {
      const row: Record<string, string | number> = { label };
      top.forEach(cat => { row[cat] = byCat[cat] || 0; });
      if (hasOther) {
        row["その他"] = Object.entries(byCat)
          .filter(([cat]) => !top.includes(cat))
          .reduce((s, [, v]) => s + v, 0);
      }
      return row;
    });

    return { data: chartData, categories: cats };
  }, [tx]);

  // データが1件もない（全カテゴリ0円）なら非表示
  const hasData = categories.length > 0 && data.some(d => categories.some(c => Number(d[c] || 0) > 0));
  if (!hasData) return null;

  return (
    <div style={STYLE_CARD}>
      <div style={{ fontSize: 10, color: COLOR_TEXT_HINT, textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: 14 }}>
        カテゴリ別 月次推移（過去6ヶ月）
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} barCategoryGap="25%">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: COLOR_TEXT_HINT, fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis
            tickFormatter={v => v >= 10000 ? (v / 10000).toFixed(0) + "万" : String(v)}
            tick={{ fill: COLOR_TEXT_HINT, fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={36}
          />
          <Tooltip content={<CustomTooltip icons={icons} />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 11, color: COLOR_TEXT_HINT, paddingTop: 8 }}
            formatter={(v: string) => `${icons?.[v] || ""} ${v}`}
          />
          {/* 上位カテゴリ＋その他を積み上げで表示。stackId を揃えると recharts が同じ柱に積む */}
          {categories.map((cat, idx) => (
            <Bar
              key={cat}
              dataKey={cat}
              stackId="cat"
              fill={PALETTE[idx % PALETTE.length]}
              // 一番上のセグメントだけ角丸にする（recharts では Bar 単位で半径指定）
              radius={idx === categories.length - 1 ? [3, 3, 0, 0] : [0, 0, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
