// ────────── タブ切替バー ──────────
// 「🏧 消費者金融 | 🏛 銀行 | 🏦 住宅ローン」のような横並びタブ切替
import { CSSProperties } from "react";
import { COLOR_TEXT_HINT, COLOR_BORDER } from "../utils/styles";

// ── スタイル定数 ──────────────────────────────────────────

// タブボタンの静的スタイル（background・color は選択状態で動的切り替え）
const STYLE_SB_TAB_BASE: CSSProperties = {
  flex: 1, border: "none", borderRadius: 9, padding: "9px 4px",
  cursor: "pointer", fontSize: 12, fontWeight: 500, fontFamily: "inherit",
};

// ─────────────────────────────────────────────────────────

interface StatBlockProps {
  // タブの一覧：[キー, 表示ラベル] の組み合わせを並べた配列
  tabs: [string, string][];
  // 現在選択中のタブのキー
  v: string;
  // タブをクリックした時に呼ばれる関数（引数はタブのキー）
  on: (k: string) => void;
}

export default function StatBlock({ tabs, v, on }: StatBlockProps) {
  return (
    <div style={{display:"flex",background:"rgba(255,255,255,0.04)",border:`1px solid ${COLOR_BORDER}`,borderRadius:12,padding:4,marginBottom:16}}>
      {tabs.map(([k, l]) => (
        <button type="button"
          key={k}
          onClick={() => on(k)}
          style={{...STYLE_SB_TAB_BASE,background:v===k?"rgba(255,255,255,0.1)":"none",color:v===k?"#fff":COLOR_TEXT_HINT}}
        >
          {l}
        </button>
      ))}
    </div>
  );
}
