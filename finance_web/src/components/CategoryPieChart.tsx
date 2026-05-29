// ────────── カテゴリ別支出 円グラフ ──────────
// 選択中の月の変動支出を、カテゴリ別の割合（ドーナツグラフ）で可視化する
// 「どこに一番使っているか」をひと目でわかるようにする目的

import { useMemo } from "react";
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { formatYen } from "../utils/format";
import {
  COLOR_TEXT_HINT, COLOR_BORDER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, STYLE_CARD,
} from "../utils/styles";

// 色パレット（8色。カテゴリが多い場合はループして再利用）
const PALETTE = [
  "#22d3ee", "#fb7185", "#facc15", "#a78bfa",
  "#34d399", "#fb923c", "#60a5fa", "#94a3b8",
];

// 1件の変動支出データ型（必要なフィールドだけ参照）
interface TxEntry {
  date?: string;
  amount?: number | string;
  category?: string;
}

// このコンポーネントが受け取る props
interface CategoryPieChartProps {
  tx: TxEntry[];
  selectedYear: number;
  selectedMonth: number;  // 0〜11（JavaScriptのDate.getMonth()と同じ）
  icons?: Record<string, string>;  // カテゴリ名→絵文字のマップ（任意）
}

// カスタムツールチップの props 型
interface TooltipProps {
  active?: boolean;
  payload?: { name: string; value: number; payload: { name: string; value: number; pct: number } }[];
  icons?: Record<string, string>;
}

// モジュールスコープに定義（コンポーネント内に置くと毎レンダーで再生成されてしまう）
function CustomTooltip({ active, payload, icons }: TooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: "#18181f",
      border: `1px solid ${COLOR_BORDER}`,
      borderRadius: 10,
      padding: "10px 14px",
      fontSize: 12,
    }}>
      <div style={{ color: COLOR_TEXT_PRIMARY, fontWeight: 700, marginBottom: 4 }}>
        {icons?.[d.name] || ""} {d.name}
      </div>
      <div style={{ fontFamily: "monospace", color: "#22d3ee" }}>
        {formatYen(d.value)}
        <span style={{ color: COLOR_TEXT_HINT, marginLeft: 6 }}>({d.pct}%)</span>
      </div>
    </div>
  );
}

export default function CategoryPieChart({ tx, selectedYear, selectedMonth, icons }: CategoryPieChartProps) {
  // 選択月のカテゴリ別合計を計算する
  const data = useMemo(() => {
    // 例: "2026-05"（選択中の月の文字列プレフィックス）
    const ms = `${selectedYear}-${String(selectedMonth + 1).padStart(2, "0")}`;
    const byCat: Record<string, number> = {};

    // 選択月のデータだけを絞り込んでカテゴリ別に合計する
    tx.filter(t => t.date?.startsWith(ms)).forEach(t => {
      const cat = t.category || "未分類";
      byCat[cat] = (byCat[cat] || 0) + Number(t.amount || 0);
    });

    // 全カテゴリの合計金額（割合計算に使う）
    const total = Object.values(byCat).reduce((s, v) => s + v, 0);

    // 金額の多い順に並べて返す
    return Object.entries(byCat)
      .sort((a, b) => b[1] - a[1])
      .map(([name, value]) => ({
        name,
        value,
        // パーセント（四捨五入・合計が0なら0%）
        pct: total > 0 ? Math.round((value / total) * 100) : 0,
      }));
  }, [tx, selectedYear, selectedMonth]);

  // データがなければ何も表示しない（支出が0件の月）
  if (data.length === 0) return null;

  return (
    <div style={STYLE_CARD}>
      {/* タイトル：何月のグラフかわかるように月を表示 */}
      <div style={{
        fontSize: 12,
        color: COLOR_TEXT_HINT,
        textTransform: "uppercase",
        letterSpacing: "1.5px",
        marginBottom: 14,
      }}>
        カテゴリ別 支出割合（{selectedMonth + 1}月）
      </div>

      {/* ドーナツ型の円グラフ（innerRadius を設定するとドーナツになる） */}
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={55}   // 穴の半径（ドーナツの内側）
            outerRadius={90}   // 円の外半径
            paddingAngle={2}   // 各スライス間の隙間
            dataKey="value"
          >
            {/* 各スライスにパレットの色を割り当てる */}
            {data.map((_, idx) => (
              <Cell key={idx} fill={PALETTE[idx % PALETTE.length]} />
            ))}
          </Pie>
          {/* ホバーツールチップ */}
          <Tooltip content={<CustomTooltip icons={icons} />} />
          {/* 凡例（絵文字アイコン付き） */}
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 12, color: COLOR_TEXT_HINT, paddingTop: 8 }}
            formatter={(v: string) => `${icons?.[v] || ""} ${v}`}
          />
        </PieChart>
      </ResponsiveContainer>

      {/* グラフ下部：上位5カテゴリを金額・割合付きでリスト表示（グラフだけでは読みにくいため補足） */}
      <div style={{ marginTop: 10, borderTop: `1px solid rgba(255,255,255,0.06)`, paddingTop: 10 }}>
        {data.slice(0, 5).map((d, idx) => (
          <div
            key={d.name}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "5px 0",
              borderBottom: `1px solid rgba(255,255,255,0.04)`,
              fontSize: 12,
            }}
          >
            {/* カラードット + カテゴリ名 */}
            <span style={{ display: "flex", alignItems: "center", gap: 7 }}>
              <span style={{
                width: 8, height: 8, borderRadius: "50%",
                background: PALETTE[idx % PALETTE.length],
                display: "inline-block", flexShrink: 0,
              }}/>
              <span style={{ color: COLOR_TEXT_SECONDARY }}>
                {icons?.[d.name] || ""} {d.name}
              </span>
            </span>
            {/* 金額 + パーセント */}
            <span>
              <span style={{ fontFamily: "monospace", fontWeight: 700 }}>{formatYen(d.value)}</span>
              <span style={{ color: COLOR_TEXT_HINT, fontSize: 12, marginLeft: 5 }}>({d.pct}%)</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
