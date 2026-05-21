// ────────── 家計診断カード ──────────
// 「貯蓄率」「返済比率」「緊急資金」「収支バランス」の4指標を自動判定して、
// A〜Eの総合評価とアドバイスを表示する
// 数値で自分の家計が客観的に分かるのでマネタイズ訴求にも効く

import { useMemo } from "react";
import { formatYen } from "../utils/format";
import {
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_SECONDARY,
  COLOR_TEXT_HINT,
  COLOR_BORDER,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
  COLOR_ACCENT,
  STYLE_CARD,
} from "../utils/styles";

interface HealthCheckCardProps {
  // ダッシュボードから受け取る集計値
  totalIncome: number;
  totalBurden: number;          // 支出合計（変動＋固定＋ローン返済）
  totalLoanRepayment: number;   // ローン返済額
  net: number;                  // 手残り
  // 口座残高合計（緊急資金チェックに使う）
  totalSavings: number;
}

// 個別指標の判定結果
interface Metric {
  label: string;
  icon: string;
  value: string;       // 数字を文字列で（例 "23%"）
  score: number;       // 0〜100点
  level: "good" | "ok" | "bad";
  hint: string;        // アドバイス文言
}

export default function HealthCheckCard({
  totalIncome,
  totalBurden,
  totalLoanRepayment,
  net,
  totalSavings,
}: HealthCheckCardProps) {

  // 4指標を個別に判定
  const metrics: Metric[] = useMemo(() => {
    const list: Metric[] = [];

    // ① 貯蓄率：(収入 - 支出) ÷ 収入。一般的に20%以上が理想、10%以上で平均的、それ未満は要改善
    const savingRate = totalIncome > 0 ? (net / totalIncome) * 100 : 0;
    list.push({
      label: "貯蓄率",
      icon: "💰",
      value: totalIncome > 0 ? `${Math.round(savingRate)}%` : "—",
      score: totalIncome > 0 ? Math.max(0, Math.min(100, savingRate * 4)) : 50,
      level: savingRate >= 20 ? "good" : savingRate >= 10 ? "ok" : "bad",
      hint: savingRate >= 20
        ? "理想的なペースで貯蓄できています"
        : savingRate >= 10
          ? "平均的。20%超を目指すとさらに安心"
          : savingRate >= 0
            ? "貯蓄率10%以上を目指しましょう"
            : "支出が収入を上回っています",
    });

    // ② 返済比率：ローン返済 ÷ 収入。25%以下が安全、35%超は危険水域（金融機関の融資審査基準）
    const repayRate = totalIncome > 0 ? (totalLoanRepayment / totalIncome) * 100 : 0;
    if (totalLoanRepayment > 0) {
      list.push({
        label: "返済比率",
        icon: "🏦",
        value: `${Math.round(repayRate)}%`,
        score: Math.max(0, Math.min(100, 100 - repayRate * 2.5)),
        level: repayRate <= 25 ? "good" : repayRate <= 35 ? "ok" : "bad",
        hint: repayRate <= 25
          ? "健全な返済比率です"
          : repayRate <= 35
            ? "やや高め。新規借入は慎重に"
            : "危険水域。借換や繰り上げ返済を検討",
      });
    }

    // ③ 緊急資金：口座残高が月支出の何ヶ月分か。3〜6ヶ月分が推奨（FP業界の定石）
    const monthsCovered = totalBurden > 0 ? totalSavings / totalBurden : 0;
    list.push({
      label: "緊急資金",
      icon: "🛟",
      value: totalBurden > 0 ? `${monthsCovered.toFixed(1)}ヶ月分` : "—",
      score: Math.max(0, Math.min(100, monthsCovered * 16.67)),  // 6ヶ月で100点
      level: monthsCovered >= 6 ? "good" : monthsCovered >= 3 ? "ok" : "bad",
      hint: monthsCovered >= 6
        ? "失業や病気にも備えられます"
        : monthsCovered >= 3
          ? "もう少し増やすとより安心"
          : "月支出3〜6ヶ月分の貯金を目標に",
    });

    // ④ 収支バランス：単月の手残りがプラスかマイナスか
    list.push({
      label: "収支バランス",
      icon: "⚖️",
      value: net >= 0 ? "プラス" : "マイナス",
      score: net >= 0 ? (totalIncome > 0 ? Math.min(100, 60 + (net / totalIncome) * 200) : 60) : 20,
      level: net > 0 ? "good" : net === 0 ? "ok" : "bad",
      hint: net > 0
        ? "今月の家計は黒字です"
        : net === 0
          ? "プラスマイナスゼロ。貯蓄のため少し節約を"
          : "赤字です。固定費の見直しを検討",
    });

    return list;
  }, [totalIncome, totalBurden, totalLoanRepayment, net, totalSavings]);

  // 総合スコア＝各指標の平均
  const totalScore = metrics.reduce((s, m) => s + m.score, 0) / metrics.length;
  // A〜E評価に変換（90+: A、75+: B、60+: C、40+: D、未満: E）
  const grade =
    totalScore >= 90 ? "A" :
    totalScore >= 75 ? "B" :
    totalScore >= 60 ? "C" :
    totalScore >= 40 ? "D" : "E";
  const gradeColor =
    grade === "A" ? COLOR_POSITIVE :
    grade === "B" ? COLOR_POSITIVE :
    grade === "C" ? COLOR_ACCENT :
    grade === "D" ? "#facc15" : COLOR_NEGATIVE;
  const gradeMessage =
    grade === "A" ? "理想的な家計です。この調子を維持しましょう"
    : grade === "B" ? "良好な家計です。さらなる改善で資産形成を加速"
    : grade === "C" ? "標準的な家計。少しずつ改善できる余地があります"
    : grade === "D" ? "見直しが必要です。固定費・返済比率に注目を"
    : "要対策。専門家への相談も検討してください";

  // 色マッピング
  const levelColor = (lv: "good" | "ok" | "bad") =>
    lv === "good" ? COLOR_POSITIVE : lv === "ok" ? COLOR_ACCENT : COLOR_NEGATIVE;

  // データが何も無いとき（収入0かつ口座0）は非表示
  if (totalIncome === 0 && totalSavings === 0 && totalBurden === 0) return null;

  return (
    <div style={{ ...STYLE_CARD, background: `linear-gradient(135deg,rgba(15,23,42,0.95) 0%,${gradeColor}10 100%)`, border: `1px solid ${gradeColor}33` }}>
      {/* ヘッダー：診断ラベル＋総合評価 */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
        <div>
          <div style={{ fontSize: 10, color: COLOR_TEXT_HINT, letterSpacing: "1.5px", textTransform: "uppercase", marginBottom: 4 }}>
            🩺 家計診断
          </div>
          <div style={{ fontSize: 13, color: COLOR_TEXT_SECONDARY, lineHeight: 1.5 }}>{gradeMessage}</div>
        </div>
        <div style={{ textAlign: "center", flexShrink: 0, marginLeft: 12 }}>
          <div style={{ fontFamily: "monospace", fontSize: 48, fontWeight: 700, color: gradeColor, lineHeight: 1, letterSpacing: "-2px" }}>
            {grade}
          </div>
          <div style={{ fontSize: 9, color: COLOR_TEXT_HINT, fontFamily: "monospace", marginTop: 2 }}>
            {Math.round(totalScore)}/100
          </div>
        </div>
      </div>

      {/* 4指標の一覧 */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {metrics.map(m => {
          const c = levelColor(m.level);
          return (
            <div key={m.label} style={{ background: "rgba(255,255,255,0.02)", borderRadius: 10, padding: "10px 12px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 4 }}>
                <span style={{ fontSize: 12, color: COLOR_TEXT_PRIMARY, fontWeight: 600 }}>
                  {m.icon} {m.label}
                </span>
                <span style={{ fontFamily: "monospace", fontSize: 14, fontWeight: 700, color: c }}>
                  {m.value}
                </span>
              </div>
              {/* スコアバー */}
              <div style={{ height: 3, background: "rgba(255,255,255,0.06)", borderRadius: 2, overflow: "hidden", marginBottom: 4 }}>
                <div style={{ height: "100%", width: `${m.score}%`, background: c, borderRadius: 2, transition: "width 0.4s ease" }} />
              </div>
              <div style={{ fontSize: 10, color: COLOR_TEXT_HINT, lineHeight: 1.4 }}>{m.hint}</div>
            </div>
          );
        })}
      </div>

      {/* 説明書き */}
      <div style={{ fontSize: 10, color: COLOR_TEXT_HINT, marginTop: 10, lineHeight: 1.5 }}>
        ※ 一般的な家計の目安に基づく簡易診断です。家族構成・地域により異なる場合があります。
      </div>
    </div>
  );
}
