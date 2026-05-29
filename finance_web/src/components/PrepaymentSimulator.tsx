// ────────── 繰り上げ返済シミュレーター（モーダル） ──────────
// あるローンに対して「毎月いくら多く払うと、何ヶ月早く完済できて、利息はいくら節約できるか」を試算する
// スライダーで追加月額を動かすとリアルタイムで結果が更新される

import { useState, useMemo } from "react";
import { formatYen } from "../utils/format";
import { calculateTotalInterest, calculateCompletionDate } from "../utils/loanCalc";
import {
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_SECONDARY,
  COLOR_TEXT_HINT,
  COLOR_BORDER,
  COLOR_ACCENT,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
  STYLE_BUTTON_PRIMARY,
  STYLE_BUTTON_OUTLINE,
} from "../utils/styles";

interface LoanItem {
  id: string;
  name: string;
  rate: number;
  remaining: number;
  monthly: number;
}

interface PrepaymentSimulatorProps {
  loan: LoanItem;
  onClose: () => void;
}

// スライダーの追加月額候補（初心者でも理解しやすい区切り）
const EXTRA_STEPS = [0, 1000, 3000, 5000, 10000, 20000, 30000, 50000];

export default function PrepaymentSimulator({ loan, onClose }: PrepaymentSimulatorProps) {
  // 追加で払う月額（スライダーで動かす）
  const [extra, setExtra] = useState(5000);
  // 一括返済額（ボーナス時にまとめて返すシナリオ）
  const [lumpSum, setLumpSum] = useState(0);

  // 現状の試算（追加なし）
  const baseline = useMemo(
    () => calculateTotalInterest(loan.remaining, loan.rate, loan.monthly),
    [loan]
  );

  // 繰り上げ後の試算
  // - 月額を monthly + extra に増やす
  // - lumpSum があれば最初に残債から引いた状態で計算
  const improved = useMemo(() => {
    const adjustedRemaining = Math.max(0, loan.remaining - lumpSum);
    if (adjustedRemaining === 0) {
      // 一括で完済する場合
      return { interest: 0, months: 0 };
    }
    return calculateTotalInterest(adjustedRemaining, loan.rate, loan.monthly + extra);
  }, [loan, extra, lumpSum]);

  // 短縮月数・節約利息
  const monthsSaved = baseline && improved ? Math.max(0, baseline.months - improved.months) : 0;
  // 一括返済分は「利息ではないが」総支払い減として扱う（節約とは別表示）
  const interestSaved = baseline && improved ? Math.max(0, baseline.interest - improved.interest) : 0;
  // 短縮後の完済予定月
  const newCompletion = improved ? calculateCompletionDate(improved.months) : null;
  // ベースライン完済予定月
  const baseCompletion = baseline ? calculateCompletionDate(baseline.months) : null;

  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.72)", zIndex: 200,
      display: "flex", alignItems: "center", justifyContent: "center", padding: 16,
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        background: "rgba(15,23,42,0.98)", border: `1px solid ${COLOR_BORDER}`,
        borderRadius: 22, padding: 20, width: "100%", maxWidth: 420, maxHeight: "90vh",
        overflowY: "auto", backdropFilter: "blur(20px)",
      }}>
        {/* ヘッダー */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
          <div>
            <div style={{ fontSize: 12, color: COLOR_ACCENT, letterSpacing: "1.5px", textTransform: "uppercase", fontWeight: 700, marginBottom: 4 }}>
              💪 繰り上げ返済シミュレーター
            </div>
            <div style={{ fontSize: 15, fontWeight: 700 }}>{loan.name}</div>
            <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginTop: 2 }}>
              金利 {loan.rate}% / 残債 {formatYen(loan.remaining)} / 月額 {formatYen(loan.monthly)}
            </div>
          </div>
          <button type="button" onClick={onClose} style={{ ...STYLE_BUTTON_OUTLINE, padding: "4px 10px", minHeight: 28, fontSize: 12 }}>✕</button>
        </div>

        {/* 月額を増やすスライダー */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
            <span style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY }}>月額を増やす</span>
            <span style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 700, color: COLOR_ACCENT }}>
              +{formatYen(extra)}
            </span>
          </div>
          {/* ボタンで段階的に選べる UI（スライダーよりタップしやすい） */}
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {EXTRA_STEPS.map(amt => (
              <button type="button"
                key={amt}
                onClick={() => setExtra(amt)}
                style={{
                  flex: "1 1 auto",
                  minWidth: 70,
                  padding: "6px 8px",
                  borderRadius: 999,
                  border: `1px solid ${extra === amt ? COLOR_ACCENT : COLOR_BORDER}`,
                  background: extra === amt ? COLOR_ACCENT : "transparent",
                  color: extra === amt ? "#fff" : COLOR_TEXT_PRIMARY,
                  fontSize: 12,
                  fontFamily: "monospace",
                  cursor: "pointer",
                }}
              >
                +{amt === 0 ? "0" : `${(amt / 1000)}k`}
              </button>
            ))}
          </div>
        </div>

        {/* 一括返済（ボーナス時など） */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
            <span style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY }}>ボーナス一括返済</span>
            <span style={{ fontFamily: "monospace", fontSize: 16, fontWeight: 700, color: COLOR_ACCENT }}>
              {lumpSum > 0 ? formatYen(lumpSum) : "なし"}
            </span>
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {[0, 50000, 100000, 200000, 500000].map(amt => (
              <button type="button"
                key={amt}
                onClick={() => setLumpSum(Math.min(amt, loan.remaining))}
                style={{
                  flex: "1 1 auto",
                  minWidth: 60,
                  padding: "6px 8px",
                  borderRadius: 999,
                  border: `1px solid ${lumpSum === amt ? COLOR_ACCENT : COLOR_BORDER}`,
                  background: lumpSum === amt ? COLOR_ACCENT : "transparent",
                  color: lumpSum === amt ? "#fff" : COLOR_TEXT_PRIMARY,
                  fontSize: 12,
                  fontFamily: "monospace",
                  cursor: "pointer",
                }}
              >
                {amt === 0 ? "なし" : `+${amt / 10000}万`}
              </button>
            ))}
          </div>
        </div>

        {/* 比較結果カード */}
        <div style={{
          background: "rgba(34,211,238,0.05)", border: `1px solid ${COLOR_ACCENT}44`,
          borderRadius: 14, padding: 14, marginBottom: 12,
        }}>
          <div style={{ fontSize: 12, color: COLOR_ACCENT, letterSpacing: "1px", textTransform: "uppercase", fontWeight: 700, marginBottom: 10 }}>
            📊 試算結果
          </div>

          {/* 現状 vs 繰り上げ後 を上下に並べて比較 */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {/* 現状 */}
            <div style={{ borderBottom: `1px solid ${COLOR_BORDER}`, paddingBottom: 10 }}>
              <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginBottom: 4 }}>現状のまま</div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <span style={{ fontSize: 13 }}>
                  完済: <span style={{ fontFamily: "monospace", fontWeight: 700 }}>
                    {baseCompletion ? `${baseCompletion.y}年${baseCompletion.m}月` : "—"}
                  </span>
                  <span style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginLeft: 6 }}>
                    ({baseline?.months || 0}ヶ月)
                  </span>
                </span>
                <span style={{ fontSize: 12, color: COLOR_NEGATIVE, fontFamily: "monospace", fontWeight: 700 }}>
                  利息 {formatYen(baseline?.interest || 0)}
                </span>
              </div>
            </div>

            {/* 繰り上げ後 */}
            <div>
              <div style={{ fontSize: 12, color: COLOR_POSITIVE, fontWeight: 700, marginBottom: 4 }}>繰り上げ後</div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <span style={{ fontSize: 13 }}>
                  完済: <span style={{ fontFamily: "monospace", fontWeight: 700, color: COLOR_POSITIVE }}>
                    {improved && improved.months === 0 ? "今月" : (newCompletion ? `${newCompletion.y}年${newCompletion.m}月` : "—")}
                  </span>
                  <span style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginLeft: 6 }}>
                    ({improved?.months || 0}ヶ月)
                  </span>
                </span>
                <span style={{ fontSize: 12, color: COLOR_POSITIVE, fontFamily: "monospace", fontWeight: 700 }}>
                  利息 {formatYen(improved?.interest || 0)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* ハイライト：節約効果 */}
        {(monthsSaved > 0 || interestSaved > 0) && (
          <div style={{
            background: "rgba(52,211,153,0.08)", border: `1px solid ${COLOR_POSITIVE}55`,
            borderRadius: 14, padding: 14, marginBottom: 12,
          }}>
            <div style={{ fontSize: 12, color: COLOR_POSITIVE, fontWeight: 700, marginBottom: 8 }}>
              ✨ あなたの節約効果
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div>
                <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginBottom: 4 }}>完済が早まる</div>
                <div style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 700, color: COLOR_POSITIVE }}>
                  {monthsSaved}ヶ月
                </div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginBottom: 4 }}>利息を節約</div>
                <div style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 700, color: COLOR_POSITIVE }}>
                  {formatYen(interestSaved)}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 注記 */}
        <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, lineHeight: 1.5, marginBottom: 12 }}>
          ※ 元利均等返済方式での試算。実際の金融機関の計算と数百円ずれる場合があります。
        </div>

        <button type="button" onClick={onClose} style={STYLE_BUTTON_PRIMARY}>閉じる</button>
      </div>
    </div>
  );
}
