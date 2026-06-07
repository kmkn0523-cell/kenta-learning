// ────────── スタイル定数まとめ ──────────
// アプリ全体で繰り返し使う色・スタイルをひとまとめにしたファイル

// 背景色・文字色の定数
export const COLOR_BACKGROUND = "#070b14";        // ページの背景（ダークネイビー）
export const COLOR_TEXT_PRIMARY = "#f0f4ff";      // メインの文字色（クールホワイト）
export const COLOR_TEXT_SECONDARY = "#94a3b8";    // サブの文字色（スレートグレー）
export const COLOR_TEXT_HINT = "#7c8aa0";         // ヒント・補足テキストの色（背景#070b14で約5.6:1。WCAG AA 4.5:1をクリア）
export const COLOR_BORDER = "rgba(148,163,184,0.12)"; // ボーダー色（青みがかった透明）
export const COLOR_BORDER_GLOW = "rgba(34,211,238,0.18)"; // シアン寄りの微光ボーダー（ヘッダー・アクセント用）
export const COLOR_ACCENT = "#22d3ee";            // アクセントカラー（フィンテックサイアン）
export const COLOR_POSITIVE = "#10b981";          // プラス・収入を示す緑（エメラルド）
export const COLOR_NEGATIVE = "#f43f5e";          // マイナス・支出を示す赤（ローズ）
export const COLOR_SURFACE = "rgba(15,23,42,0.95)"; // フィルターパネルなどの表面色（ダークネイビー半透明）

// カードのスタイル（グラスモーフィズム：すりガラス効果でカードに奥行きを出す）
export const STYLE_CARD = {
  background:"rgba(15,23,42,0.7)",              // カード背景：やや透明なダークネイビー
  backdropFilter:"blur(20px)",                  // すりガラス効果：カードの後ろを20pxぼかす
  border:"1px solid rgba(148,163,184,0.18)",    // ボーダー：薄いグレーのふち線（不透明度0.18）
  borderRadius:18,                              // 角丸：18pxの丸み
  padding:20,                                   // 内側の余白：全方向20px
  marginBottom:14,                              // 下の外側余白：カード同士の間隔
  boxShadow:"0 4px 24px rgba(0,0,0,0.3),0 1px 0 rgba(255,255,255,0.04) inset", // 影：下向きの黒い影＋上側にうっすら白い光（立体感を出す）
};

// 入力欄（input/select）の共通スタイル（backdropFilter:blur(8px) でうっすらガラス感を追加）
export const STYLE_INPUT = {
  background:"rgba(148,163,184,0.06)",  // 入力欄の背景：ごく薄いグレーで存在感を出す
  backdropFilter:"blur(8px)",           // すりガラス効果：入力欄の後ろを8pxぼかす
  border:`1px solid ${COLOR_BORDER}`,   // ボーダー：薄いグレーのふち線
  borderRadius:12,                      // 角丸：12pxの丸み
  padding:"12px 14px",                  // 内側の余白：上下12px・左右14px
  color:COLOR_TEXT_PRIMARY,             // 文字色：メインの白色
  fontSize:16,                          // 文字サイズ：16px
  width:"100%",                         // 横幅：親要素いっぱいに広げる
  fontFamily:"inherit",                 // フォント：親要素と同じフォントを使う
  minHeight:46,                         // 最低の高さ：46px（タップしやすいサイズ）
  boxSizing:"border-box" as const,      // ボックスサイズの計算方法：paddingを含めたサイズにする
};

// プライマリボタン（保存・追加など）の共通スタイル（boxShadow でシアンのグロー光を追加）
export const STYLE_BUTTON_PRIMARY = {
  border:"none",                        // ボーダーなし：ボタン枠を消す
  borderRadius:12,                      // 角丸：12pxの丸み
  padding:"13px 0",                     // 内側の余白：上下13px・左右0px
  cursor:"pointer",                     // カーソル：ポインタ（クリックできる印）
  fontSize:15,                          // 文字サイズ：15px
  fontWeight:700,                       // 文字の太さ：太字
  background:COLOR_ACCENT,             // ボタン背景：シアン（アクセントカラー）
  color:"#070b14",                      // 文字色：ダークネイビー（背景と対比させる）
  width:"100%",                         // 横幅：親要素いっぱいに広げる
  fontFamily:"inherit",                 // フォント：親要素と同じフォントを使う
  minHeight:46,                         // 最低の高さ：46px（タップしやすいサイズ）
  boxShadow:"0 0 20px rgba(34,211,238,0.3),0 0 40px rgba(34,211,238,0.1)", // シアンのグロー光：近くに濃い光・遠くに薄い光
};

// セカンダリボタン（キャンセル・編集など）の共通スタイル
export const STYLE_BUTTON_OUTLINE = {background:"transparent",border:`1px solid ${COLOR_BORDER}`,borderRadius:12,padding:"9px 16px",cursor:"pointer",fontSize:13,color:COLOR_TEXT_SECONDARY,fontFamily:"inherit",minHeight:40};
