// ────────── 月次レポートモーダル ──────────
// 月が変わった最初のアクセス時に自動表示される「前月振り返り」サマリーモーダル
// open=false の時は何も描画しない

import { CSSProperties } from "react";
import { formatYen } from "../utils/format";
import { selectAffiliateOffer } from "../utils/affiliates";
import AffiliateBanner from "./AffiliateBanner";
import {
  STYLE_BUTTON_PRIMARY,
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_HINT,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
  COLOR_BORDER,
} from "../utils/styles";

// ── スタイル定数 ──────────────────────────────────────────

// 背景オーバーレイ（タップして閉じるエリア）
const STYLE_REPORT_OVERLAY: CSSProperties = {
  position: "fixed",
  inset: 0,
  zIndex: 200,
  background: "rgba(0,0,0,0.75)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "20px 16px",
};

// モーダル本体カード
const STYLE_REPORT_MODAL: CSSProperties = {
  background: "#0f1520",
  border: `1px solid ${COLOR_BORDER}`,
  borderRadius: 18,
  padding: "28px 24px",
  width: "100%",
  maxWidth: 440,
  maxHeight: "80vh",
  overflowY: "auto",
};

// 収支サマリーグリッド（収入・支出・手残りの3列）
const STYLE_REPORT_SUMMARY_GRID: CSSProperties = {
  background: "rgba(255,255,255,0.04)",
  borderRadius: 12,
  padding: "16px 20px",
  marginBottom: 16,
  display: "grid",
  gridTemplateColumns: "1fr 1fr 1fr",
  gap: 12,
  textAlign: "center",
};

// 結果バッジの静的スタイル（background・color・border は isBlack で動的に変わる）
const STYLE_REPORT_BADGE_BASE: CSSProperties = {
  display: "inline-block",
  padding: "6px 18px",
  borderRadius: 999,
  fontSize: 13,
  fontWeight: 700,
};

// ─────────────────────────────────────────────────────────

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
  // 口座が1件以上登録されているか（提案枠の表示判定に使う）
  hasAccounts: boolean;
}

export default function MonthlyReportModal({
  open, onClose, year, month, income, expense, topCats, overBudget, hasAccounts,
}: MonthlyReportProps) {
  // open=false なら何も描画しない（DOMに残さない）
  if (!open) return null;

  // 手残り（収入 - 支出）
  const net = income - expense;
  // 黒字かどうか（true=黒字, false=赤字）
  const isBlack = net >= 0;

  return (
    // 背景オーバーレイ（タップして閉じることもできる）
    <div onClick={onClose} style={STYLE_REPORT_OVERLAY}>
      {/* モーダル本体（クリックが背景に伝わらないように止める） */}
      <div onClick={e => e.stopPropagation()} style={STYLE_REPORT_MODAL}>
        {/* ── ヘッダー：カレンダーアイコン＋タイトル ── */}
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <div style={{ fontSize: 38, marginBottom: 8 }}>📅</div>
          <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, letterSpacing: "2px", textTransform: "uppercase", marginBottom: 4 }}>
            Monthly Report
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, color: COLOR_TEXT_PRIMARY }}>
            {year}年{month}月の振り返り
          </div>
        </div>

        {/* ── 収支サマリー：3列グリッドで収入・支出・手残りを表示 ── */}
        <div style={STYLE_REPORT_SUMMARY_GRID}>
          {/* 収入 */}
          <div>
            <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginBottom: 6, letterSpacing: "0.5px" }}>収入</div>
            <div style={{ fontFamily: "monospace", fontSize: 13, fontWeight: 700, color: COLOR_POSITIVE, lineHeight: 1.3 }}>
              {formatYen(income)}
            </div>
          </div>
          {/* 支出 */}
          <div>
            <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginBottom: 6, letterSpacing: "0.5px" }}>支出</div>
            <div style={{ fontFamily: "monospace", fontSize: 13, fontWeight: 700, color: COLOR_NEGATIVE, lineHeight: 1.3 }}>
              {formatYen(expense)}
            </div>
          </div>
          {/* 手残り */}
          <div>
            <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginBottom: 6, letterSpacing: "0.5px" }}>手残り</div>
            <div style={{ fontFamily: "monospace", fontSize: 13, fontWeight: 700, color: isBlack ? COLOR_POSITIVE : COLOR_NEGATIVE, lineHeight: 1.3 }}>
              {net >= 0 ? "+" : ""}{formatYen(net)}
            </div>
          </div>
        </div>

        {/* ── 結果バッジ（黒字 or 赤字） ── */}
        <div style={{ textAlign: "center", marginBottom: 20 }}>
          <span style={{
            ...STYLE_REPORT_BADGE_BASE,
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
            <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, letterSpacing: "1px", textTransform: "uppercase", marginBottom: 10 }}>
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
                <span style={{ fontSize: 13, color: COLOR_TEXT_PRIMARY }}>
                  <span style={{ color: COLOR_TEXT_HINT, marginRight: 8, fontFamily: "monospace" }}>
                    {i + 1}.
                  </span>
                  {cat}
                </span>
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
            <div style={{ fontSize: 12, color: COLOR_NEGATIVE, fontWeight: 600, marginBottom: 8, letterSpacing: "0.5px" }}>
              🚨 先月の予算超過カテゴリ
            </div>
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

        {/* ── あなたへの提案（前月の家計状態に連動・最大1枠） ── */}
        {(() => {
          // 前月の貯蓄率（収入0なら0%として扱う）
          const savingRate = income > 0 ? (net / income) * 100 : 0;
          const offer = selectAffiliateOffer({
            savingRate,
            hasAccounts,
            month: new Date().getMonth() + 1,
          });
          if (!offer) return null;
          return (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, letterSpacing: "1px", marginBottom: 8 }}>
                💡 あなたへの提案
              </div>
              <AffiliateBanner offer={offer} />
            </div>
          );
        })()}

        {/* ── 閉じるボタン ── */}
        <button type="button" onClick={onClose} style={{ ...STYLE_BUTTON_PRIMARY, width: "100%" }}>
          今月もがんばろう 💪
        </button>
      </div>
    </div>
  );
}
