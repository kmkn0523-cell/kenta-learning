// ────────── スタイル定数まとめ ──────────
// アプリ全体で繰り返し使う色・スタイルをひとまとめにしたファイル

// 背景色・文字色の定数
export const COLOR_BACKGROUND = "#070b14";        // ページの背景（ダークネイビー）
export const COLOR_TEXT_PRIMARY = "#f0f4ff";      // メインの文字色（クールホワイト）
export const COLOR_TEXT_SECONDARY = "#94a3b8";    // サブの文字色（スレートグレー）
export const COLOR_TEXT_HINT = "#475569";         // ヒント・補足テキストの色（暗めスレート）
export const COLOR_BORDER = "rgba(148,163,184,0.12)"; // ボーダー色（青みがかった透明）
export const COLOR_BORDER_GLOW = "rgba(34,211,238,0.18)"; // シアン寄りの微光ボーダー（ヘッダー・アクセント用）
export const COLOR_ACCENT = "#22d3ee";            // アクセントカラー（フィンテックサイアン）
export const COLOR_POSITIVE = "#10b981";          // プラス・収入を示す緑（エメラルド）
export const COLOR_NEGATIVE = "#f43f5e";          // マイナス・支出を示す赤（ローズ）
export const COLOR_SURFACE = "rgba(15,23,42,0.95)"; // フィルターパネルなどの表面色（ダークネイビー半透明）

// カードのスタイル（グラスモーフィズム：すりガラス効果でカードに奥行きを出す）
export const STYLE_CARD = {background:"rgba(15,23,42,0.7)",backdropFilter:"blur(20px)",border:"1px solid rgba(148,163,184,0.18)",borderRadius:18,padding:20,marginBottom:14,boxShadow:"0 4px 24px rgba(0,0,0,0.3),0 1px 0 rgba(255,255,255,0.04) inset"};

// 入力欄（input/select）の共通スタイル（すりガラス効果を追加）
export const STYLE_INPUT = {background:"rgba(148,163,184,0.06)",backdropFilter:"blur(8px)",border:`1px solid ${COLOR_BORDER}`,borderRadius:12,padding:"12px 14px",color:COLOR_TEXT_PRIMARY,fontSize:16,outline:"none",width:"100%",fontFamily:"inherit",minHeight:46,boxSizing:"border-box" as const};

// プライマリボタン（保存・追加など）の共通スタイル（シアングローを追加）
export const STYLE_BUTTON_PRIMARY = {border:"none",borderRadius:12,padding:"13px 0",cursor:"pointer",fontSize:15,fontWeight:700,background:COLOR_ACCENT,color:"#070b14",width:"100%",fontFamily:"inherit",minHeight:46,boxShadow:"0 0 20px rgba(34,211,238,0.3),0 0 40px rgba(34,211,238,0.1)"};

// セカンダリボタン（キャンセル・編集など）の共通スタイル
export const STYLE_BUTTON_OUTLINE = {background:"transparent",border:`1px solid ${COLOR_BORDER}`,borderRadius:12,padding:"9px 16px",cursor:"pointer",fontSize:13,color:COLOR_TEXT_SECONDARY,fontFamily:"inherit",minHeight:40};
