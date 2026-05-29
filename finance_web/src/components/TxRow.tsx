// ────────── 収支1行コンポーネント ──────────
// 変動支出・収入リストの1件分。通常表示 ↔ 編集フォームを切り替える

import { useState, CSSProperties } from "react";
import { parseYenAmount, formatYen } from "../utils/format";
import { STYLE_CARD, STYLE_BUTTON_PRIMARY, STYLE_BUTTON_OUTLINE, COLOR_TEXT_HINT, COLOR_POSITIVE, COLOR_NEGATIVE } from "../utils/styles";
import { Input, Select } from "./ui";

// ── スタイル定数 ──────────────────────────────────────────

// カテゴリアイコン丸の静的スタイル（background・color は種別で動的切り替え）
const STYLE_TR_ICON_BASE: CSSProperties = {
  width: 40, height: 40, borderRadius: "50%",
  display: "flex", alignItems: "center", justifyContent: "center",
  fontSize: 16, flexShrink: 0,
};

// ─────────────────────────────────────────────────────────

// 収支1件分のデータ型（memo は任意）
interface TxItem {
  id: string;
  date: string;
  category: string;
  amount: number;
  memo?: string;
}
// このコンポーネントが受け取る props の型
interface TxRowProps {
  item: TxItem;
  onSave: (item: TxItem) => void;
  onDelete: () => void;
  cats: string[];
  ico: Record<string, string>;
  isInc?: boolean;
}

// cats: カテゴリ一覧配列, ico: カテゴリ→絵文字マップ, isInc: 収入かどうか（false=支出）
export default function TxRow({item,onSave,onDelete,cats,ico,isInc}: TxRowProps) {
  const [ed, setEd] = useState(false); // 編集モードかどうか
  const [d, setD] = useState<{cat:string;amt:string;date:string;memo:string}>({cat:"",amt:"",date:"",memo:""});      // 編集中のフォーム値

  // 収入は緑・支出は赤で背景と文字色を変える
  const bg  = isInc ? "rgba(52,211,153,0.12)" : "rgba(248,113,113,0.12)";
  const col = isInc ? COLOR_POSITIVE : COLOR_NEGATIVE;

  // 編集モード：フォームを表示する
  if (ed) return (
    <div style={STYLE_CARD}>
      <div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:12}}>
        <Select value={d.cat} onChange={e=>setD(x=>({...x,cat:e.target.value}))} options={cats} icons={ico}/>
        <Input money type="number" value={d.amt} onChange={e=>setD(x=>({...x,amt:e.target.value}))} placeholder="金額（円）"/>
        <Input type="date" value={d.date} onChange={e=>setD(x=>({...x,date:e.target.value}))}/>
        <Input value={d.memo||""} onChange={e=>setD(x=>({...x,memo:e.target.value}))} placeholder="メモ（任意）"/>
      </div>
      <div style={{display:"flex",gap:10}}>
        <button type="button" onClick={()=>{const a=parseYenAmount(d.amt);if(!a)return;onSave({...item,category:d.cat,amount:a,date:d.date,memo:d.memo||""});setEd(false);}} style={STYLE_BUTTON_PRIMARY}>保存</button>
        <button type="button" onClick={()=>setEd(false)} style={{...STYLE_BUTTON_OUTLINE,minHeight:44,padding:"11px 18px"}}>キャンセル</button>
      </div>
    </div>
  );

  // 通常表示：カテゴリアイコン・メモ・日付・金額を横並びに表示
  return (
    <div style={{display:"flex",alignItems:"center",gap:12,...STYLE_CARD}}>
      {/* カテゴリ絵文字（収入は緑背景・支出は赤背景の丸） */}
      <div style={{ ...STYLE_TR_ICON_BASE, background: bg, color: col }}>{ico[item.category]||"●"}</div>
      <div style={{flex:1,minWidth:0}}>
        <div style={{fontSize:13,fontWeight:600}}>{item.category} <span style={{fontSize:12,color:COLOR_TEXT_HINT}}>{item.memo}</span></div>
        <div style={{fontSize:12,color:COLOR_TEXT_HINT,marginTop:2}}>{item.date}</div>
      </div>
      {/* 収入は「+」、支出は「-」を頭につけて金額を表示 */}
      <div style={{fontFamily:"monospace",fontSize:14,fontWeight:700,color:col}}>{isInc?"+":"-"}{formatYen(item.amount)}</div>
      <button type="button" onClick={()=>{setD({cat:item.category,amt:String(item.amount),date:item.date,memo:item.memo||""});setEd(true);}} style={STYLE_BUTTON_OUTLINE}>編集</button>
      <button type="button" onClick={onDelete} style={STYLE_BUTTON_OUTLINE}>削除</button>
    </div>
  );
}
