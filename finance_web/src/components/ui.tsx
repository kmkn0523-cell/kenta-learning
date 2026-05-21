// ────────── 共通UIコンポーネント ──────────
// アプリ全体で使い回す小さな部品をまとめたファイル

import { useState, ChangeEvent, CSSProperties, KeyboardEvent, forwardRef } from "react";
import { formatAmount, formatYen } from "../utils/format";
import { COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_HINT, COLOR_BORDER, COLOR_ACCENT, COLOR_POSITIVE, COLOR_NEGATIVE, STYLE_INPUT, STYLE_BUTTON_PRIMARY, STYLE_BUTTON_OUTLINE } from "../utils/styles";

// 目アイコン付きパスワード入力欄（👁️ボタンで文字を見せたり隠したりできる）
interface PasswordInputProps {
  value: string;
  onChange: (v: string) => void;
  onEnter?: () => void;
  placeholder?: string;
  err?: boolean;
}
export function PasswordInput({ value, onChange, onEnter, placeholder, err }: PasswordInputProps) {
  const [show, setShow] = useState(true);
  // エラーがある時は枠を赤くする
  const border = err ? "#f87171" : "rgba(255,255,255,0.08)";

  return (
    <div style={{position:"relative",marginBottom:12}}>
      <input
        type="text"             // 常にtext型→iOSフリック入力が使える
        inputMode="text"        // スマホでテキストキーボードを使う
        autoComplete="off"      // オートコンプリートを無効化
        value={value}           // Reactが値を管理するcontrolled input
        onChange={e => onChange(e.target.value)}  // 入力のたびに親に値を渡す
        onKeyDown={(e: KeyboardEvent<HTMLInputElement>) => e.key === "Enter" && onEnter && onEnter()}
        placeholder={show ? placeholder : ""}
        style={{
          background:"rgba(255,255,255,0.05)",
          border:`1px solid ${border}`,
          borderRadius:10,
          padding:"13px 44px 13px 16px",
          // 非表示モードのとき文字色を透明にする（inputは動作し続けるがテキストが見えない）
          color: show ? "#f5f5f7" : "transparent",
          caretColor:"#f5f5f7", // カーソルは常に表示
          fontSize:16,
          outline:"none",
          width:"100%",
          boxSizing:"border-box",
          fontFamily:"inherit",
          textAlign:"center",
          letterSpacing:"0.2em",
        }}
      />
      {/* 非表示モード時のオーバーレイ：•を文字数分だけ表示（クリックはinputに通す） */}
      {!show && value.length > 0 && (
        <div style={{
          position:"absolute",
          top:0, left:0, right:44, bottom:0,
          display:"flex",
          alignItems:"center",
          justifyContent:"center",
          pointerEvents:"none",  // タップがinputに届くように透過させる
          fontSize:20,
          color:"#f5f5f7",
          letterSpacing:"0.15em",
          overflow:"hidden",
          userSelect:"none",
        }}>
          {"•".repeat(value.length)}
        </div>
      )}
      {/* 非表示モードでvalue空のときだけplaceholderを代替表示 */}
      {!show && value.length === 0 && placeholder && (
        <div style={{
          position:"absolute",
          top:0, left:0, right:44, bottom:0,
          display:"flex",
          alignItems:"center",
          justifyContent:"center",
          pointerEvents:"none",
          fontSize:16,
          color:"rgba(255,255,255,0.25)",
          overflow:"hidden",
          userSelect:"none",
        }}>
          {placeholder}
        </div>
      )}
      {/* 👁️ボタン：クリックするたびに表示/非表示が切り替わる */}
      <button onClick={() => setShow(s => !s)} style={{position:"absolute",right:12,top:"50%",transform:"translateY(-50%)",background:"none",border:"none",cursor:"pointer",fontSize:18,padding:4,color:"#9a9aa3"}}>
        {show ? "🙈" : "👁️"}
      </button>
    </div>
  );
}

// 汎用テキスト/数値入力欄
// money=true を渡すと、数字以外を弾いて3桁カンマ付き表示に整形する
interface InputProps {
  value: string | number;
  onChange: (e: { target: { value: string } }) => void;
  type?: string;
  placeholder?: string;
  style?: CSSProperties;
  money?: boolean;
}
export const Input = forwardRef<HTMLInputElement, InputProps>(({value, onChange, type, placeholder, style, money}, ref) => {
  // money の時は画面に出す値をカンマ付きに整える
  const display = money ? formatAmount(value) : value;
  // money の時は入力イベントを横取りして数字だけ抜き出し→整形してから onChange へ渡す
  const handle = money ? (e: ChangeEvent<HTMLInputElement>) => onChange({target:{value:formatAmount(e.target.value)}}) : onChange;
  return <input ref={ref} type={type==="number"||money?"text":type||"text"} value={display} onChange={handle as any} placeholder={placeholder} style={{...STYLE_INPUT,...style}} inputMode={type==="number"||money?"numeric":type==="date"?undefined:"text"}/>;
});
Input.displayName = "Input";

// セレクトボックス（プルダウン）
// options に文字列の配列、icons に {カテゴリ名: 絵文字} のオブジェクトを渡す
interface SelectProps {
  value: string;
  onChange: (e: ChangeEvent<HTMLSelectElement>) => void;
  options: string[];
  icons?: Record<string, string>;
}
export const Select = ({value, onChange, options, icons}: SelectProps) =>
  <select value={value} onChange={onChange} style={{...STYLE_INPUT,cursor:"pointer"}}>
    {options.map(o=><option key={o} value={o}>{icons?icons[o]+" ":""}{o}</option>)}
  </select>;

// 統計ラベルカード（残債・月返済など1つの数値を見やすく表示する小パーツ）
interface StatLabelProps {
  label: string;
  value: string;
  color?: string;
}
export const StatLabel = ({label, value, color}: StatLabelProps) =>
  <div style={{
    background:"rgba(15,23,42,0.6)",        // カード背景：やや透明なダークネイビー
    backdropFilter:"blur(12px)",            // すりガラス効果：後ろを12pxぼかす
    border:"1px solid rgba(148,163,184,0.16)", // ボーダー：薄いグレーのふち（不透明度0.16）
    borderRadius:14,                        // 角の丸み
    padding:"14px 8px",                     // 内側の余白
    textAlign:"center",                     // テキストを中央揃え
    boxShadow:"0 2px 12px rgba(0,0,0,0.2)", // 影：カードに奥行きを出す
  }}>
    <div style={{fontSize:9,color:COLOR_TEXT_HINT,marginBottom:6,letterSpacing:"1px",textTransform:"uppercase"}}>{label}</div>
    <div style={{fontSize:14,fontWeight:700,fontFamily:"monospace",color:color||COLOR_TEXT_PRIMARY,letterSpacing:"-0.5px"}}>{value}</div>
  </div>;

// 横棒グラフ1行（カテゴリ別支出などを視覚化する）
interface ProgressBarProps {
  label: string;
  value: number;
  max: number;
  color: string; // グラデーション固定のため未使用（呼び出し元との型互換のため残している）
  icon?: string;
}
export const ProgressBar = ({label, value, max, color, icon}: ProgressBarProps) =>
  <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:11}}>
    <div style={{fontSize:11,color:COLOR_TEXT_SECONDARY,width:80,display:"flex",alignItems:"center",gap:4,overflow:"hidden",flexShrink:0}}>
      {icon&&<span>{icon}</span>}
      <span style={{overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{label}</span>
    </div>
    <div style={{flex:1,height:8,background:"rgba(148,163,184,0.08)",borderRadius:4,overflow:"hidden"}}>
      <div style={{
        height:"100%",                                            // バーの高さを親に合わせる
        borderRadius:4,                                           // 角の丸み
        background:`linear-gradient(90deg,#22d3ee,#38bdf8)`,    // シアン→水色のグラデーション（color引数は使わない）
        width:Math.min(100,(value/(max||1))*100)+"%",            // 値に応じた幅（最大100%）
        transition:"width 0.4s ease",                            // 幅が変わるとき0.4秒でアニメーション
      }}/>
    </div>
    <div style={{fontSize:11,color:COLOR_TEXT_SECONDARY,width:82,textAlign:"right",fontFamily:"monospace",flexShrink:0}}>{formatYen(value)}</div>
  </div>;

// 一時的な通知バナー（保存・エラーなどのメッセージを画面上部に一瞬表示する）
// data が null の時は何も表示しない
// action を渡すと「元に戻す」などのボタンを横に並べて表示できる
interface ToastData {
  msg: string;
  type?: "success" | "error" | "info";
  action?: { label: string; onClick: () => void };
}
export function Toast({data}: { data: ToastData | null }) {
  if (!data) return null;
  const cl = data.type==="error" ? COLOR_NEGATIVE : data.type==="info" ? COLOR_TEXT_SECONDARY : COLOR_POSITIVE;
  // action があるときだけタップを受け付ける（誤タップでフォーム操作を邪魔しないため）
  const pe = data.action ? "auto" : "none";
  return (
    <div style={{position:"fixed",top:16,left:"50%",transform:"translateX(-50%)",zIndex:999,padding:"10px 20px",borderRadius:24,fontSize:13,fontWeight:600,whiteSpace:"nowrap",pointerEvents:pe as any,color:cl,background:"rgba(7,11,20,0.95)",border:`1px solid ${cl}55`,backdropFilter:"blur(12px)",boxShadow:`0 4px 24px ${cl}22`,display:"flex",alignItems:"center",gap:10}}>
      <span>{data.msg}</span>
      {data.action && (
        <button
          onClick={data.action.onClick}
          style={{background:"rgba(255,255,255,0.08)",border:`1px solid ${cl}66`,color:cl,fontSize:12,fontWeight:700,padding:"4px 10px",borderRadius:14,cursor:"pointer",fontFamily:"inherit"}}
        >
          {data.action.label}
        </button>
      )}
    </div>
  );
}

// 削除確認ダイアログ（背景タップ or キャンセルボタンで閉じる）
// data が null の時は何も表示しない
interface ConfirmDialogData {
  title: string;
  msg?: string;
  onOk: () => void;
}
export function ConfirmDialog({data, onOk, onCancel}: { data: ConfirmDialogData | null; onOk: () => void; onCancel: () => void }) {
  if (!data) return null;
  return (
    <div onClick={onCancel} style={{position:"fixed",inset:0,background:"rgba(0,0,0,0.72)",zIndex:200,display:"flex",alignItems:"center",justifyContent:"center",padding:20}}>
      <div onClick={e=>e.stopPropagation()} style={{background:"rgba(15,23,42,0.98)",border:`1px solid ${COLOR_BORDER}`,borderRadius:22,padding:24,width:"100%",maxWidth:340,backdropFilter:"blur(20px)"}}>
        <div style={{fontSize:15,fontWeight:600,marginBottom:8}}>{data.title}</div>
        <div style={{fontSize:13,color:COLOR_TEXT_SECONDARY,marginBottom:20}}>{data.msg||"この操作は元に戻せません。"}</div>
        <div style={{display:"flex",gap:10}}>
          <button onClick={onCancel} style={{...STYLE_BUTTON_OUTLINE,flex:1,minHeight:44,padding:12}}>キャンセル</button>
          <button onClick={onOk} style={{...STYLE_BUTTON_PRIMARY,flex:1,background:COLOR_NEGATIVE}}>削除する</button>
        </div>
      </div>
    </div>
  );
}
