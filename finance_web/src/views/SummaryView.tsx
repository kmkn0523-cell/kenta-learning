// ────────── 月次サマリータブのビューコンポーネント ──────────
// その月の「収入・支出・手残り・貯蓄率・カテゴリ内訳・前月比」を1画面にまとめて表示する
// さらに画面の内容をPNG画像やCSVファイルとして書き出せる
// このファイルは「表示」専用。集計（計算）は App.tsx 側で行い、結果を props で受け取る

import React, { useRef, CSSProperties } from "react";
import { useUI } from "../contexts/UIHelpersContext";
import { SummaryStats } from "../types";
import { formatYen } from "../utils/format";
import { exportSummaryCsv, exportSummaryImage } from "../utils/summaryExport";
import {
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_SECONDARY,
  COLOR_TEXT_HINT,
  COLOR_ACCENT,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
} from "../utils/styles";

// このコンポーネントが親から受け取る値の形（型）
interface SummaryViewProps {
  monthLabel: string;                                          // 表示する月のラベル（例:「2026年5月」）
  current: SummaryStats;                                       // 当月の集計値
  previous: SummaryStats | null;                              // 前月の集計値（無ければ null）
  categoryBreakdown: { category: string; amount: number }[]; // カテゴリ別の支出（金額の大きい順に並んでいる前提）
  // showT は useUI()（UIHelpersContext）から取得する
}

// レポートカード（白枠の囲み）の共通スタイル
const STYLE_REPORT_CARD: CSSProperties = {
  background: "rgba(15,23,42,0.98)",            // カード背景：濃いダークネイビー（画像化したときも見やすい）
  border: "1px solid rgba(148,163,184,0.16)",  // ボーダー：薄いグレーのふち線
  borderRadius: 22,                             // 角丸：22pxの丸み
  padding: "24px 20px",                         // 内側の余白：上下24px・左右20px
  marginBottom: 16,                             // 下の外側余白：カード同士の間隔
};

// 指標を1行（ラベル＋金額＋前月比）で並べるための行スタイル
const STYLE_STAT_ROW: CSSProperties = {
  display: "flex",                  // 横並びにする
  justifyContent: "space-between",  // 左にラベル・右に値を寄せる
  alignItems: "baseline",           // 文字の下端をそろえる
  padding: "10px 0",                // 上下に少し余白を空ける
};

// 書き出しボタンの共通スタイル
const STYLE_ACTION_BUTTON: CSSProperties = {
  flex: 1,                                       // 横幅を均等に分け合う
  border: "1px solid rgba(148,163,184,0.24)",   // ボーダー：薄いグレーのふち線
  borderRadius: 14,                              // 角丸：14pxの丸み
  padding: "13px 0",                             // 内側の余白：上下13px
  cursor: "pointer",                             // カーソル：ポインタ（押せる印）
  fontSize: 14,                                  // 文字サイズ：14px
  fontWeight: 600,                               // 文字の太さ：やや太字
  background: "rgba(148,163,184,0.06)",          // 背景：ごく薄いグレー
  color: COLOR_TEXT_PRIMARY,                     // 文字色：メインの白色
  fontFamily: "inherit",                         // フォント：親と同じ
  minHeight: 46,                                 // 最低の高さ：46px（押しやすいサイズ）
};

// 前月比のバッジ（小さな差分表示）。当月値と前月値の差を計算して色付きで表示する
// unit が "yen" なら金額（¥）、"pt" なら貯蓄率のポイント差として表示する
function DiffBadge({ currentValue, previousValue, unit }: {
  currentValue: number;
  previousValue: number | null | undefined;
  unit: "yen" | "pt";
}) {
  // 前月の値が無いときは前月比を出さない（何も表示しない）
  if (previousValue === null || previousValue === undefined) return null;

  // 差分 ＝ 当月 − 前月
  const diff = currentValue - previousValue;

  // 差が0なら「±0」をグレーで表示する
  if (diff === 0) {
    return <span style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginLeft: 8 }}>±0</span>;
  }

  // プラスなら上向き矢印＋緑、マイナスなら下向き矢印＋赤
  const isUp = diff > 0;
  const arrow = isUp ? "↑" : "↓";
  const color = isUp ? COLOR_POSITIVE : COLOR_NEGATIVE;

  // 表示する数字部分を作る。マイナス記号は見やすい全角ダッシュ（−）を使う
  let amountText: string;
  if (unit === "yen") {
    // 金額：絶対値をカンマ区切りにして「円」を付ける
    const absText = Math.abs(diff).toLocaleString("ja-JP");
    amountText = `${isUp ? "+" : "−"}${absText}円`;
  } else {
    // 貯蓄率：小数第1位まで（pt＝ポイント）
    const absText = Math.abs(diff).toFixed(1);
    amountText = `${isUp ? "+" : "−"}${absText}pt`;
  }

  return (
    <span style={{ fontSize: 12, color, marginLeft: 8, fontWeight: 600 }}>
      {arrow}{amountText}
    </span>
  );
}

export default function SummaryView({ monthLabel, current, previous, categoryBreakdown }: SummaryViewProps) {
  const { showT } = useUI();
  // 画像化する対象のDOM（レポート部分のまとまり）を覚えておくための入れ物
  const reportRef = useRef<HTMLDivElement>(null);

  // 手残りがプラスなら緑、マイナス（赤字）なら赤で表示する
  const netColor = current.net >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE;

  // 「CSVで保存」ボタンを押したときの処理
  function handleSaveCsv() {
    exportSummaryCsv(monthLabel, current, previous, categoryBreakdown);
    showT("CSVを保存しました");
  }

  // 「画像で保存」ボタンを押したときの処理
  async function handleSaveImage() {
    // 画像化する対象がまだ準備できていなければ何もしない
    if (!reportRef.current) return;
    try {
      await exportSummaryImage(reportRef.current, `サマリー_${monthLabel}.png`);
      showT("画像を保存しました");
    } catch (error) {
      // 画像化に失敗したときはエラー通知を出す
      showT("画像の保存に失敗しました", "error");
    }
  }

  return (
    <div>
      {/* 画面タイトル */}
      <h2 style={{ fontSize: 20, fontWeight: 700, color: COLOR_TEXT_PRIMARY, margin: "4px 0 4px" }}>
        月次サマリー
      </h2>
      <p style={{ fontSize: 13, color: COLOR_TEXT_SECONDARY, margin: "0 0 16px" }}>
        {monthLabel}の収支をまとめて確認できます
      </p>

      {/* ここから下（reportRef）が画像化される範囲 */}
      <div ref={reportRef}>
        {/* 基本指標カード（収入・支出・手残り・貯蓄率） */}
        <div style={STYLE_REPORT_CARD}>
          <div style={{ fontSize: 13, color: COLOR_ACCENT, fontWeight: 600, marginBottom: 4 }}>
            {monthLabel}
          </div>

          {/* 収入合計 */}
          <div style={STYLE_STAT_ROW}>
            <span style={{ fontSize: 14, color: COLOR_TEXT_SECONDARY }}>収入合計</span>
            <span style={{ fontSize: 16, fontWeight: 700, color: COLOR_TEXT_PRIMARY }}>
              {formatYen(current.income)}
              <DiffBadge currentValue={current.income} previousValue={previous?.income} unit="yen" />
            </span>
          </div>

          {/* 支出合計 */}
          <div style={STYLE_STAT_ROW}>
            <span style={{ fontSize: 14, color: COLOR_TEXT_SECONDARY }}>支出合計</span>
            <span style={{ fontSize: 16, fontWeight: 700, color: COLOR_TEXT_PRIMARY }}>
              {formatYen(current.expense)}
              <DiffBadge currentValue={current.expense} previousValue={previous?.expense} unit="yen" />
            </span>
          </div>

          {/* 手残り（収入 − 支出） */}
          <div style={STYLE_STAT_ROW}>
            <span style={{ fontSize: 14, color: COLOR_TEXT_SECONDARY }}>手残り</span>
            <span style={{ fontSize: 18, fontWeight: 800, color: netColor }}>
              {formatYen(current.net)}
              <DiffBadge currentValue={current.net} previousValue={previous?.net} unit="yen" />
            </span>
          </div>

          {/* 貯蓄率（%） */}
          <div style={{ ...STYLE_STAT_ROW, borderTop: "1px solid rgba(148,163,184,0.12)", marginTop: 4 }}>
            <span style={{ fontSize: 14, color: COLOR_TEXT_SECONDARY }}>貯蓄率</span>
            <span style={{ fontSize: 18, fontWeight: 800, color: COLOR_ACCENT }}>
              {current.savingRate}%
              <DiffBadge currentValue={current.savingRate} previousValue={previous?.savingRate} unit="pt" />
            </span>
          </div>
        </div>

        {/* カテゴリ内訳カード */}
        <div style={STYLE_REPORT_CARD}>
          <div style={{ fontSize: 13, color: COLOR_ACCENT, fontWeight: 600, marginBottom: 12 }}>
            カテゴリ内訳
          </div>

          {categoryBreakdown.length === 0 ? (
            // カテゴリ別の支出が無いとき
            <p style={{ fontSize: 13, color: COLOR_TEXT_HINT, margin: 0 }}>支出がありません</p>
          ) : (
            // 金額の大きい順に1行ずつ並べる
            categoryBreakdown.map((row) => (
              <div key={row.category} style={STYLE_STAT_ROW}>
                <span style={{ fontSize: 14, color: COLOR_TEXT_SECONDARY }}>{row.category}</span>
                <span style={{ fontSize: 15, fontWeight: 600, color: COLOR_TEXT_PRIMARY }}>
                  {formatYen(row.amount)}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 書き出しボタン（画像化の範囲の外に置く） */}
      <div style={{ display: "flex", gap: 12, marginTop: 4 }}>
        <button type="button" style={STYLE_ACTION_BUTTON} onClick={handleSaveImage}>
          画像で保存
        </button>
        <button type="button" style={STYLE_ACTION_BUTTON} onClick={handleSaveCsv}>
          CSVで保存
        </button>
      </div>
    </div>
  );
}
