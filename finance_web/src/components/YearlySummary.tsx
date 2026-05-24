// ────────── 年間サマリーコンポーネント ──────────
// 選択した年の1〜12月を一覧で表示し、
// 各月の収入・支出・手残りを確認できるカード

import { useMemo } from "react";
import { Tx, Income, FixedExpense, Loan } from "../types";
import { formatYen } from "../utils/format";
import {
  COLOR_TEXT_HINT,
  COLOR_TEXT_SECONDARY,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
  COLOR_TEXT_PRIMARY,
  COLOR_BORDER,
  STYLE_CARD,
  STYLE_BUTTON_OUTLINE,
} from "../utils/styles";

// このコンポーネントが受け取る props の型
interface YearlySummaryProps {
  // 集計対象の年
  selectedYear: number;
  // 前年に移動するコールバック
  onPrevYear: () => void;
  // 翌年に移動するコールバック
  onNextYear: () => void;
  // 変動支出の全履歴
  transactions: Tx[];
  // 収入の全履歴
  incomes: Income[];
  // 固定費の一覧（月ごとに一定額として加算）
  fixedExpenses: FixedExpense[];
  // ローン一覧（月ごとの返済額を加算）
  loans: Loan[];
  // ある月を選択したときの月次ビューに移動するコールバック
  onSelectMonth: (month: number) => void;
}

export default function YearlySummary({
  selectedYear,
  onPrevYear,
  onNextYear,
  transactions,
  incomes,
  fixedExpenses,
  loans,
  onSelectMonth,
}: YearlySummaryProps) {

  // 固定費の月合計（毎月同額として扱う）
  const monthlyFixed = useMemo(
    () => fixedExpenses.reduce((s, f) => s + Number(f.amount || 0), 0),
    [fixedExpenses]
  );

  // ローン月返済合計（毎月同額として扱う）
  const monthlyLoan = useMemo(
    () => loans.reduce((s, l) => s + Number(l.monthly || 0), 0),
    [loans]
  );

  // 1月〜12月の集計データを作る
  const rows = useMemo(() => {
    return Array.from({ length: 12 }, (_, i) => {
      const month = i; // 0〜11
      const ms = `${selectedYear}-${String(month + 1).padStart(2, "0")}`; // "2026-01"

      // その月の収入合計
      const incTotal = incomes
        .filter(inc => inc.date?.startsWith(ms))
        .reduce((s, inc) => s + Number(inc.amount || 0), 0);

      // その月の変動支出合計
      const varTotal = transactions
        .filter(t => t.date?.startsWith(ms))
        .reduce((s, t) => s + Number(t.amount || 0), 0);

      // その月の総支出（変動＋固定＋ローン）
      const expTotal = varTotal + monthlyFixed + monthlyLoan;

      // 手残り
      const net = incTotal - expTotal;

      // データがあるかどうか（収入も支出も0の月はグレーアウト）
      const hasData = incTotal > 0 || varTotal > 0;

      return { month, ms, incTotal, varTotal, expTotal, net, hasData };
    });
  }, [selectedYear, transactions, incomes, monthlyFixed, monthlyLoan]);

  // 年間合計を集計
  const yearTotal = useMemo(() => {
    const incTotal = rows.reduce((s, r) => s + r.incTotal, 0);
    const expTotal = rows.reduce((s, r) => s + r.expTotal, 0);
    const net = incTotal - expTotal;
    return { incTotal, expTotal, net };
  }, [rows]);

  // 今月（ハイライト用）
  const today = new Date();
  const curMonth = today.getMonth(); // 0〜11

  return (
    <div style={STYLE_CARD}>
      {/* ────── ヘッダー：タイトル＋年切り替えボタン ────── */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
        <div style={{ fontSize:10, color:COLOR_TEXT_HINT, textTransform:"uppercase", letterSpacing:"1.5px" }}>
          年間サマリー
        </div>
        {/* 前年・翌年の切り替えボタン */}
        <div style={{ display:"flex", alignItems:"center", gap:8 }}>
          <button onClick={onPrevYear} style={{...STYLE_BUTTON_OUTLINE, padding:"4px 10px", fontSize:13, minHeight:28}}>◀</button>
          <span style={{ fontSize:14, fontWeight:700, color:COLOR_TEXT_PRIMARY, minWidth:40, textAlign:"center" }}>
            {selectedYear}
          </span>
          <button onClick={onNextYear} style={{...STYLE_BUTTON_OUTLINE, padding:"4px 10px", fontSize:13, minHeight:28}}>▶</button>
        </div>
      </div>

      {/* ────── カラム見出し ────── */}
      <div style={{
        display:"grid",
        gridTemplateColumns:"48px 1fr 1fr 1fr",
        gap:4, padding:"4px 0 8px",
        borderBottom:`1px solid ${COLOR_BORDER}`,
        marginBottom:4,
      }}>
        <div style={{ fontSize:10, color:COLOR_TEXT_HINT }}>月</div>
        <div style={{ fontSize:10, color:COLOR_TEXT_HINT, textAlign:"right" }}>収入</div>
        <div style={{ fontSize:10, color:COLOR_TEXT_HINT, textAlign:"right" }}>支出</div>
        <div style={{ fontSize:10, color:COLOR_TEXT_HINT, textAlign:"right" }}>手残り</div>
      </div>

      {/* ────── 月ごとの行 ────── */}
      {rows.map(row => {
        const isCur = selectedYear === today.getFullYear() && row.month === curMonth;
        return (
          <div
            key={row.month}
            onClick={() => onSelectMonth(row.month)}
            style={{
              display:"grid",
              gridTemplateColumns:"48px 1fr 1fr 1fr",
              gap:4, padding:"9px 0",
              borderBottom:`1px solid rgba(255,255,255,0.04)`,
              cursor:"pointer",
              background: isCur ? "rgba(34,211,238,0.05)" : "transparent",
              borderRadius: isCur ? 6 : 0,
              transition:"background 0.15s",
            }}
          >
            {/* 月ラベル */}
            <div style={{
              fontSize:13, fontWeight: isCur ? 700 : 500,
              color: isCur ? "#22d3ee" : row.hasData ? COLOR_TEXT_PRIMARY : COLOR_TEXT_HINT,
              display:"flex", alignItems:"center", gap:4,
            }}>
              {row.month + 1}月
              {/* 今月バッジ */}
              {isCur && (
                <span style={{
                  fontSize:8, background:"rgba(34,211,238,0.2)", color:"#22d3ee",
                  borderRadius:3, padding:"1px 4px", fontWeight:700,
                }}>今月</span>
              )}
            </div>
            {/* 収入 */}
            <div style={{
              fontFamily:"monospace", fontSize:12, textAlign:"right",
              color: row.hasData ? COLOR_POSITIVE : COLOR_TEXT_HINT,
            }}>
              {row.incTotal > 0 ? formatYen(row.incTotal) : "−"}
            </div>
            {/* 支出 */}
            <div style={{
              fontFamily:"monospace", fontSize:12, textAlign:"right",
              color: row.hasData ? COLOR_NEGATIVE : COLOR_TEXT_HINT,
            }}>
              {row.expTotal > 0 ? formatYen(row.expTotal) : "−"}
            </div>
            {/* 手残り */}
            <div style={{
              fontFamily:"monospace", fontSize:12, fontWeight:700, textAlign:"right",
              color: !row.hasData ? COLOR_TEXT_HINT : row.net >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE,
            }}>
              {row.hasData
                ? `${row.net >= 0 ? "+" : ""}${formatYen(row.net)}`
                : "−"
              }
            </div>
          </div>
        );
      })}

      {/* ────── 年間合計行 ────── */}
      <div style={{
        display:"grid",
        gridTemplateColumns:"48px 1fr 1fr 1fr",
        gap:4, padding:"10px 0 2px",
        borderTop:`1px solid ${COLOR_BORDER}`,
        marginTop:4,
      }}>
        <div style={{ fontSize:11, fontWeight:700, color:COLOR_TEXT_SECONDARY }}>年計</div>
        <div style={{ fontFamily:"monospace", fontSize:12, fontWeight:700, textAlign:"right", color:COLOR_POSITIVE }}>
          {formatYen(yearTotal.incTotal)}
        </div>
        <div style={{ fontFamily:"monospace", fontSize:12, fontWeight:700, textAlign:"right", color:COLOR_NEGATIVE }}>
          {formatYen(yearTotal.expTotal)}
        </div>
        <div style={{ fontFamily:"monospace", fontSize:12, fontWeight:700, textAlign:"right", color:yearTotal.net >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE }}>
          {yearTotal.net >= 0 ? "+" : ""}{formatYen(yearTotal.net)}
        </div>
      </div>
      {/* タップで月次ビューに飛べるヒント */}
      <div style={{ fontSize:10, color:COLOR_TEXT_HINT, marginTop:10, textAlign:"center" }}>
        月をタップすると月次ビューに切り替わります
      </div>
    </div>
  );
}
