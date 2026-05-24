// ────────── 月次レポートモーダル ──────────
// 月が変わった最初のアクセス時に自動表示される「前月振り返り」サマリーモーダル
// open=false の時は何も描画しない

import { formatYen } from "../utils/format";
import {
  STYLE_BUTTON_PRIMARY,
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_HINT,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
  COLOR_BORDER,
} from "../utils/styles";

// このコンポーネントが受け取るpropsの型
interface MonthlyReportProps {
  open: boolean;
  onClose: () => void;
  // 前月の年・月（例: year=2026, month=4 → 「4月」と表示）
  year: number;
  month: number;
  // 前月の収入合計（円）
  income: number;
  // 前月の支出合計（変動＋固定費の合計）
  expense: number;
  // 前月のカテゴリ別支出 top3（[カテゴリ名, 金額] の配列）
  topCats: [string, number][];
  // 予算超過したカテゴリ（[カテゴリ名, 超過額] の配列）
  overBudget: [string, number][];
}

export default function MonthlyReportModal({
  open, onClose, year, month, income, expense, topCats, overBudget,
}: MonthlyReportProps) {
  // open=false なら何も描画しない（DOMに残さない）
  if (!open) return null;

  // 手残り（収入 - 支出）
  const net = income - expense;
  // 黒字かどうか（true=黒字, false=赤字）
  const isBlack = net >= 0;

  return (
    // 背景オーバーレイ（タップして閉じることもできる）
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 200,
        background: "rgba(0,0,0,0.75)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px 16px",
      }}
    >
      {/* モーダル本体（クリックが背景に伝わらないように止める） */}
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: "#0f1520",
          border: `1px solid ${COLOR_BORDER}`,
          borderRadius: 18,
          padding: "28px 24px",
          width: "100%",
          maxWidth: 440,
          maxHeight: "80vh",
          overflowY: "auto",
        }}
      >
        {/* ── ヘッダー：カレンダーアイコン＋タイトル ── */}
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <div style={{ fontSize: 38, marginBottom: 8 }}>📅</div>
          <div style={{ fontSize: 11, color: COLOR_TEXT_HINT, letterSpacing: "2px", textTransform: "uppercase", marginBottom: 4 }}>
            Monthly Report
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, color: COLOR_TEXT_PRIMARY }}>
            {year}年{month}月の振り返り
          </div>
        </div>

        {/* ── 収支サマリー：3列グリッドで収入・支出・手残りを表示 ── */}
        <div style={{
          background: "rgba(255,255,255,0.04)",
          borderRadius: 12,
          padding: "16px 20px",
          marginBottom: 16,
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: 12,
          textAlign: "center",
        }}>
          {/* 収入 */}
          <div>
            <div style={{ fontSize: 10, color: COLOR_TEXT_HINT, marginBottom: 6, letterSpacing: "0.5px" }}>収入</div>
            <div style={{ fontFamily: "monospace", fontSize: 13, fontWeight: 700, color: COLOR_POSITIVE, lineHeight: 1.3 }}>
              {formatYen(income)}
            </div>
          </div>
          {/* 支出 */}
          <div>
            <div style={{ fontSize: 10, color: COLOR_TEXT_HINT, marginBottom: 6, letterSpacing: "0.5px" }}>支出</div>
            <div style={{ fontFamily: "monospace", fontSize: 13, fontWeight: 700, color: COLOR_NEGATIVE, lineHeight: 1.3 }}>
              {formatYen(expense)}
            </div>
          </div>
          {/* 手残り */}
          <div>
            <div style={{ fontSize: 10, color: COLOR_TEXT_HINT, marginBottom: 6, letterSpacing: "0.5px" }}>手残り</div>
            <div style={{ fontFamily: "monospace", fontSize: 13, fontWeight: 700, color: isBlack ? COLOR_POSITIVE : COLOR_NEGATIVE, lineHeight: 1.3 }}>
              {net >= 0 ? "+" : ""}{formatYen(net)}
            </div>
          </div>
        </div>

        {/* ── 結果バッジ（黒字 or 赤字） ── */}
        <div style={{ textAlign: "center", marginBottom: 20 }}>
          <span style={{
            display: "inline-block",
            padding: "6px 18px",
            borderRadius: 999,
            fontSize: 13,
            fontWeight: 700,
            background: isBlack ? "rgba(34,197,94,0.12)" : "rgba(244,63,94,0.12)",
            color: isBlack ? COLOR_POSITIVE : COLOR_NEGATIVE,
            border: `1px solid ${isBlack ? "rgba(34,197,94,0.25)" : "rgba(244,63,94,0.25)"}`,
          }}>
            {isBlack
              ? `🎉 ${formatYen(net)} の黒字でした`
              : `⚠️ ${formatYen(-net)} の赤字でした`}
          </span>
        </div>

        {/* ── 変動支出 TOP3 ── */}
        {topCats.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 11, color: COLOR_TEXT_HINT, letterSpacing: "1px", textTransform: "uppercase", marginBottom: 10 }}>
              変動支出 TOP {topCats.length}
            </div>
            {topCats.map(([cat, amt], i) => (
              <div
                key={cat}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "8px 0",
                  borderBottom: "1px solid rgba(255,255,255,0.05)",
                }}
              >
                {/* 順位番号＋カテゴリ名 */}
                <span style={{ fontSize: 13, color: COLOR_TEXT_PRIMARY }}>
                  <span style={{ color: COLOR_TEXT_HINT, marginRight: 8, fontFamily: "monospace" }}>
                    {i + 1}.
                  </span>
                  {cat}
                </span>
                {/* 金額（赤系で表示） */}
                <span style={{ fontFamily: "monospace", fontSize: 13, fontWeight: 600, color: COLOR_NEGATIVE }}>
                  {formatYen(amt)}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* ── 予算超過アラート（超過があった時だけ表示） ── */}
        {overBudget.length > 0 && (
          <div style={{
            background: "rgba(244,63,94,0.06)",
            border: "1px solid rgba(244,63,94,0.2)",
            borderRadius: 10,
            padding: "12px 16px",
            marginBottom: 20,
          }}>
            {/* バナータイトル */}
            <div style={{ fontSize: 11, color: COLOR_NEGATIVE, fontWeight: 600, marginBottom: 8, letterSpacing: "0.5px" }}>
              🚨 先月の予算超過カテゴリ
            </div>
            {/* 超過カテゴリ一覧 */}
            {overBudget.map(([cat, over]) => (
              <div key={cat} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
                <span style={{ color: COLOR_TEXT_PRIMARY }}>{cat}</span>
                <span style={{ fontFamily: "monospace", color: COLOR_NEGATIVE, fontWeight: 600 }}>
                  {formatYen(over)} 超過
                </span>
              </div>
            ))}
          </div>
        )}

        {/* ── 閉じるボタン ── */}
        <button onClick={onClose} style={{ ...STYLE_BUTTON_PRIMARY, width: "100%" }}>
          今月もがんばろう 💪
        </button>
      </div>
    </div>
  );
}
