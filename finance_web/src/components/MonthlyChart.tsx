// ────────── 月次推移グラフコンポーネント ──────────
// 過去6ヶ月の収入・支出（変動＋固定）を棒グラフで表示する

import { useMemo } from "react";
import {
  BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { formatYen } from "../utils/format";
import { COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_TEXT_HINT, COLOR_BORDER, STYLE_CARD } from "../utils/styles";

// 収支1件のデータ型（date と amount だけ使う）
interface TxEntry {
  date?: string;
  amount?: number | string;
}

// このコンポーネントが受け取る props の型
interface MonthlyChartProps {
  tx: TxEntry[];
  inc: TxEntry[];
  tFx: number;
}

// カスタムツールチップの props 型
interface TooltipProps {
  active?: boolean;
  payload?: { dataKey: string; name: string; value: number; color: string }[];
  label?: string;
}

// tx: 変動支出の全履歴配列, inc: 収入の全履歴配列, tFx: 今月の固定費合計（毎月一定と仮定）
export default function MonthlyChart({ tx, inc, tFx }: MonthlyChartProps) {
  // 過去6ヶ月分のデータを集計する（今月含む）
  const data = useMemo(() => {
    const now = new Date();
    const months = [];
    for (let i = 5; i >= 0; i--) {
      // i=5 が6ヶ月前、i=0 が今月になるようにループ
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const y = d.getFullYear();
      const m = d.getMonth() + 1;
      const ms = y + "-" + String(m).padStart(2, "0"); // 例: "2026-05"
      const label = m + "月"; // グラフのX軸ラベル

      // その月の収入合計
      const income = inc
        .filter(x => x.date?.startsWith(ms))
        .reduce((s, x) => s + Number(x.amount || 0), 0);

      // その月の変動支出合計
      const variable = tx
        .filter(x => x.date?.startsWith(ms))
        .reduce((s, x) => s + Number(x.amount || 0), 0);

      // 固定費は毎月同じ金額と仮定してそのまま足す
      const total = variable + tFx;
      const net = income - total; // 手残り（プラスなら黒字・マイナスなら赤字）

      months.push({ label, income, variable, fixed: tFx, total, net });
    }
    return months;
  }, [tx, inc, tFx]);

  // カスタムツールチップ：ホバー時に円単位で金額を表示する
  const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={{ background:"#18181f", border:`1px solid ${COLOR_BORDER}`, borderRadius:10, padding:"10px 14px", fontSize:12 }}>
        <div style={{ color:COLOR_TEXT_PRIMARY, fontWeight:700, marginBottom:6 }}>{label}</div>
        {payload.map(p => (
          <div key={p.dataKey} style={{ color:p.color, fontFamily:"monospace" }}>
            {p.name}: {formatYen(p.value)}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={STYLE_CARD}>
      <div style={{ fontSize:10, color:COLOR_TEXT_HINT, textTransform:"uppercase", letterSpacing:"1.5px", marginBottom:14 }}>
        月次推移（過去6ヶ月）
      </div>

      {/* recharts の棒グラフ。収入（緑）と支出（赤）を並べて表示 */}
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} barCategoryGap="30%" barGap={4}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false}/>
          {/* X軸：月ラベル */}
          <XAxis
            dataKey="label"
            tick={{ fill:COLOR_TEXT_HINT, fontSize:11 }}
            axisLine={false}
            tickLine={false}
          />
          {/* Y軸：万円単位で短縮表示 */}
          <YAxis
            tickFormatter={v => v >= 10000 ? (v / 10000).toFixed(0) + "万" : String(v)}
            tick={{ fill:COLOR_TEXT_HINT, fontSize:10 }}
            axisLine={false}
            tickLine={false}
            width={36}
          />
          <Tooltip content={<CustomTooltip />}/>
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize:11, color:COLOR_TEXT_HINT, paddingTop:8 }}
          />
          {/* 収入バー（緑） */}
          <Bar dataKey="income" name="収入" fill={COLOR_POSITIVE} radius={[3, 3, 0, 0]}/>
          {/* 支出合計バー（赤） */}
          <Bar dataKey="total" name="支出合計" fill={COLOR_NEGATIVE} radius={[3, 3, 0, 0]}/>
        </BarChart>
      </ResponsiveContainer>

      {/* 各月の手残りを一覧で表示（棒グラフだけでは分かりにくいため補足） */}
      <div style={{ marginTop:14, borderTop:`1px solid rgba(255,255,255,0.06)`, paddingTop:12 }}>
        <div style={{ fontSize:10, color:COLOR_TEXT_HINT, marginBottom:8, letterSpacing:"0.5px" }}>手残り推移</div>
        {data.map(d => (
          <div
            key={d.label}
            style={{ display:"flex", justifyContent:"space-between", padding:"4px 0", borderBottom:`1px solid rgba(255,255,255,0.04)`, fontSize:12 }}
          >
            <span style={{ color:COLOR_TEXT_HINT }}>{d.label}</span>
            <span style={{ fontFamily:"monospace", fontWeight:700, color: d.net >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE }}>
              {d.net >= 0 ? "+" : ""}{formatYen(d.net)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
