// ────────── 月次推移グラフコンポーネント ──────────
// 過去3/6/12ヶ月の収入・支出（変動＋固定）を棒グラフで表示する
// 右上のボタンで表示期間を切り替えられる

import { useMemo, useState, CSSProperties } from "react";
import {
  BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { formatYen } from "../utils/format";
import { COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_TEXT_PRIMARY, COLOR_TEXT_HINT, COLOR_BORDER, STYLE_CARD } from "../utils/styles";

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

// モジュールスコープに定義（コンポーネント内に置くと毎レンダーで再生成されてしまう）
function CustomTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background:"#0b1220", border:`1px solid ${COLOR_BORDER}`, borderRadius:10, padding:"10px 14px", fontSize:12 }}>
      <div style={{ color:COLOR_TEXT_PRIMARY, fontWeight:700, marginBottom:6 }}>{label}</div>
      {payload.map(p => (
        <div key={p.dataKey} style={{ color:p.color, fontFamily:FONT_NUM }}>
          {p.name}: {formatYen(p.value)}
        </div>
      ))}
    </div>
  );
}

// ── スタイル定数 ──────────────────────────────────────────

// 期間切り替えボタンの静的スタイル（background・border・color・fontWeight は選択状態で動的切り替え）
const STYLE_MC_RANGE_BTN_BASE: CSSProperties = {
  borderRadius: 6, fontSize: 12,
  padding: "3px 9px", cursor: "pointer",
  fontFamily: "inherit",
  transition: "background 0.15s, border-color 0.15s, color 0.15s, font-weight 0.15s",
};

// ─────────────────────────────────────────────────────────

// 表示期間の選択肢（ヶ月）
const RANGE_OPTIONS = [3, 6, 12] as const;
type RangeOption = typeof RANGE_OPTIONS[number];

// tx: 変動支出の全履歴配列, inc: 収入の全履歴配列, tFx: 今月の固定費合計（毎月一定と仮定）
export default function MonthlyChart({ tx, inc, tFx }: MonthlyChartProps) {
  // 表示する月数（3/6/12ヶ月。デフォルトは6ヶ月）
  const [range, setRange] = useState<RangeOption>(6);

  // 選択した期間分のデータを集計する（今月含む）
  const data = useMemo(() => {
    const now = new Date();
    const months = [];
    // range=6 なら i=5〜0（6ヶ月）、range=3 なら i=2〜0（3ヶ月）
    for (let i = range - 1; i >= 0; i--) {
      // i が大きいほど古い月になるようにループ
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const y = d.getFullYear();
      const m = d.getMonth() + 1;
      const ms = y + "-" + String(m).padStart(2, "0"); // 例: "2026-05"
      const label = m + "月"; // グラフのX軸ラベル（12ヶ月表示では年もつける）
      // 12ヶ月表示では「5月」だけでは1年前と今年が区別できないので年を追加
      const displayLabel = range === 12 ? `${String(y).slice(2)}/${m}月` : label;

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

      months.push({ label: displayLabel, income, variable, fixed: tFx, total, net });
    }
    return months;
  }, [tx, inc, tFx, range]);

  return (
    <div style={STYLE_CARD}>
      {/* ── ヘッダー：タイトル＋期間切り替えボタン ── */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:14 }}>
        <div style={{ fontSize:12, color:COLOR_TEXT_HINT, textTransform:"uppercase", letterSpacing:"1.5px" }}>
          月次推移
        </div>
        {/* 3ヶ月・6ヶ月・12ヶ月のトグルボタン */}
        <div style={{ display:"flex", gap:4 }}>
          {RANGE_OPTIONS.map(r => (
            <button type="button"
              key={r}
              onClick={() => setRange(r)}
              style={{
                ...STYLE_MC_RANGE_BTN_BASE,
                background: range === r ? "rgba(34,211,238,0.15)" : "rgba(255,255,255,0.04)",
                border: `1px solid ${range === r ? "rgba(34,211,238,0.4)" : "rgba(255,255,255,0.1)"}`,
                color: range === r ? "#22d3ee" : COLOR_TEXT_HINT,
                fontWeight: range === r ? 700 : 400,
              }}
            >
              {r}ヶ月
            </button>
          ))}
        </div>
      </div>

      {/* recharts の棒グラフ。収入（緑）と支出（赤）を並べて表示 */}
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} barCategoryGap="30%" barGap={4}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false}/>
          {/* X軸：月ラベル（12ヶ月表示は文字が多いので少し小さく） */}
          <XAxis
            dataKey="label"
            tick={{ fill:COLOR_TEXT_HINT, fontSize: range === 12 ? 9 : 11 }}
            axisLine={false}
            tickLine={false}
          />
          {/* Y軸：万円単位で短縮表示 */}
          <YAxis
            tickFormatter={v => v >= 10000 ? (v / 10000).toFixed(0) + "万" : String(v)}
            tick={{ fill:COLOR_TEXT_HINT, fontSize:12 }}
            axisLine={false}
            tickLine={false}
            width={36}
          />
          <Tooltip content={<CustomTooltip />}/>
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize:12, color:COLOR_TEXT_HINT, paddingTop:8 }}
          />
          {/* 収入バー（緑） */}
          <Bar dataKey="income" name="収入" fill={COLOR_POSITIVE} radius={[3, 3, 0, 0]}/>
          {/* 支出合計バー（赤） */}
          <Bar dataKey="total" name="支出合計" fill={COLOR_NEGATIVE} radius={[3, 3, 0, 0]}/>
        </BarChart>
      </ResponsiveContainer>

      {/* 各月の手残りを一覧で表示（棒グラフだけでは分かりにくいため補足） */}
      <div style={{ marginTop:14, borderTop:`1px solid rgba(255,255,255,0.06)`, paddingTop:12 }}>
        <div style={{ fontSize:12, color:COLOR_TEXT_HINT, marginBottom:8, letterSpacing:"0.5px" }}>手残り推移</div>
        {data.map(d => (
          <div
            key={d.label}
            style={{ display:"flex", justifyContent:"space-between", padding:"4px 0", borderBottom:`1px solid rgba(255,255,255,0.04)`, fontSize:12 }}
          >
            <span style={{ color:COLOR_TEXT_HINT }}>{d.label}</span>
            <span style={{ fontFamily:FONT_NUM, fontWeight:700, color: d.net >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE }}>
              {d.net >= 0 ? "+" : ""}{formatYen(d.net)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
