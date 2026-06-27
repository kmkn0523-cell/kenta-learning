// ────────── 電卓ボトムシート ──────────
// 金額欄の🧮ボタンから開く。テンキーと四則演算で計算し、「確定」で金額欄へ値を返す
import { useReducer, useEffect, CSSProperties } from "react";
import { initCalc, calcReducer, currentResult, confirmValue, formatExpression, formatResult, Operator } from "../utils/calculator";
import { COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BORDER, COLOR_NEGATIVE, STYLE_BUTTON_PRIMARY } from "../utils/styles";

interface CalculatorSheetProps {
  open: boolean;                       // 開いているか
  initialValue: string | number;       // 金額欄の今の値
  onConfirm: (value: number) => void;  // 確定したとき呼ぶ（整数を渡す）
  onClose: () => void;                  // 確定せず閉じるとき呼ぶ
}

// ボタン1個の見た目（数字・演算子で色を少し変える）
const STYLE_KEY_BASE: CSSProperties = {
  border: `1px solid ${COLOR_BORDER}`,
  borderRadius: 12,
  background: "rgba(148,163,184,0.06)",
  color: COLOR_TEXT_PRIMARY,
  fontSize: 20,
  fontWeight: 600,
  fontFamily: "inherit",
  minHeight: 52,
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

// 演算子ボタンの表示記号と読み上げラベル
const OP_KEYS: Record<Operator, { label: string; aria: string }> = {
  "/": { label: "÷", aria: "わる" },
  "*": { label: "×", aria: "かける" },
  "-": { label: "−", aria: "ひく" },
  "+": { label: "＋", aria: "たす" },
};

export default function CalculatorSheet({ open, initialValue, onConfirm, onClose }: CalculatorSheetProps) {
  // open するたびに金額欄の今の値で初期化し直す
  const [state, dispatch] = useReducer(calcReducer, initialValue, initCalc);

  // open かつ initialValue が変わったら current を作り直す（clearしてから初期値の数字を流し込む）
  useEffect(() => {
    if (!open) return;
    dispatch({ type: "clear" });
    const digits = String(initialValue).replace(/[^\d]/g, "");
    for (const d of digits) dispatch({ type: "digit", d });
  }, [open, initialValue]);

  // Escキーで閉じる
  useEffect(() => {
    if (!open) return;
    const onKey = (e: globalThis.KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const result = currentResult(state);
  const canConfirm = !state.error && result !== null;

  // 数字ボタンを作る
  const digitKey = (d: string) => (
    <button key={d} type="button" aria-label={d} onClick={() => dispatch({ type: "digit", d })} style={STYLE_KEY_BASE}>{d}</button>
  );
  // 演算子ボタンを作る
  const opKey = (op: Operator) => (
    <button key={op} type="button" aria-label={OP_KEYS[op].aria} onClick={() => dispatch({ type: "operator", op })}
      style={{ ...STYLE_KEY_BASE, color: COLOR_ACCENT, fontWeight: 700 }}>{OP_KEYS[op].label}</button>
  );

  return (
    <div data-testid="calc-overlay" onClick={onClose}
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 300, display: "flex", alignItems: "flex-end", justifyContent: "center" }}>
      <div className="calc-sheet" onClick={e => e.stopPropagation()} role="dialog" aria-modal="true" aria-label="電卓"
        style={{ width: "100%", maxWidth: 420, background: "rgba(15,23,42,0.98)", backdropFilter: "blur(20px)", borderTopLeftRadius: 22, borderTopRightRadius: 22, border: `1px solid ${COLOR_BORDER}`, padding: 16, boxSizing: "border-box" }}>

        {/* ── ディスプレイ（上段=式 / 下段=結果。常時表示） ── */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
          <button type="button" aria-label="閉じる" onClick={onClose} style={{ background: "none", border: "none", color: COLOR_TEXT_SECONDARY, fontSize: 20, cursor: "pointer", padding: 4 }}>✕</button>
          <div style={{ flex: 1, textAlign: "right", overflow: "hidden" }}>
            <div style={{ fontSize: 13, color: COLOR_TEXT_SECONDARY, minHeight: 18, fontFamily: FONT_NUM, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {formatExpression(state)}
            </div>
            <div style={{ fontSize: 30, fontWeight: 700, color: state.error ? COLOR_NEGATIVE : COLOR_TEXT_PRIMARY, fontFamily: FONT_NUM, fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {state.error ? "エラー" : formatResult(result ?? 0)}
            </div>
          </div>
        </div>

        {/* ── テンキー（4列） ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, marginTop: 10 }}>
          <button type="button" aria-label="クリア" onClick={() => dispatch({ type: "clear" })} style={{ ...STYLE_KEY_BASE, color: COLOR_NEGATIVE }}>C</button>
          <button type="button" aria-label="1文字消す" onClick={() => dispatch({ type: "backspace" })} style={STYLE_KEY_BASE}>⌫</button>
          {opKey("/")}
          {opKey("*")}
          {["7", "8", "9"].map(digitKey)}{opKey("-")}
          {["4", "5", "6"].map(digitKey)}{opKey("+")}
          {["1", "2", "3"].map(digitKey)}
          <button type="button" aria-label="イコール" onClick={() => dispatch({ type: "equals" })} style={{ ...STYLE_KEY_BASE, gridRow: "span 2", color: COLOR_ACCENT, fontWeight: 700 }}>=</button>
          {/* 0 は横2マス（最下段の空きを埋めてiOS電卓と同じ並びにする） */}
          <button type="button" aria-label="0" onClick={() => dispatch({ type: "digit", d: "0" })} style={{ ...STYLE_KEY_BASE, gridColumn: "span 2" }}>0</button>
          <button type="button" aria-label="小数点" onClick={() => dispatch({ type: "dot" })} style={STYLE_KEY_BASE}>.</button>
        </div>

        {/* ── 確定ボタン ── */}
        <button type="button" aria-label="確定する" disabled={!canConfirm}
          onClick={() => { onConfirm(confirmValue(state)); onClose(); }}
          style={{ ...STYLE_BUTTON_PRIMARY, marginTop: 12, opacity: canConfirm ? 1 : 0.4, cursor: canConfirm ? "pointer" : "not-allowed" }}>
          確定する
        </button>
      </div>
    </div>
  );
}
