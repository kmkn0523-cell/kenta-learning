// ────────── 固定費1行コンポーネント ──────────
// 固定費リストの1件分。通常表示 ↔ 編集フォームを切り替える

import { useState } from "react";
import { parseYenAmount, formatYen, FIXED_EXPENSE_CATEGORIES, FIXED_EXPENSE_CATEGORY_ICONS } from "../utils/format";
import { STYLE_CARD, STYLE_BUTTON_PRIMARY, STYLE_BUTTON_OUTLINE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_HINT } from "../utils/styles";
import { Input, Select } from "./ui";

// 固定費1件分のデータ型
interface FxItem {
  id: string;
  name: string;
  category: string;
  amount: number | string;
}
// このコンポーネントが受け取る props の型
interface FxRowProps {
  item: FxItem;
  onSave: (item: FxItem) => void;
  onDelete: () => void;
  onMoveUp: (() => void) | null;
  onMoveDown: (() => void) | null;
}

export default function FxRow({item,onSave,onDelete,onMoveUp,onMoveDown}: FxRowProps) {
  const [ed, setEd] = useState(false); // 編集モードかどうか
  const [d, setD] = useState<{name:string;cat:string;amt:string}>({name:"",cat:"",amt:""});      // 編集中のフォーム値

  // 編集モード：フォームを表示する
  if (ed) return (
    <div style={STYLE_CARD}>
      <div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:12}}>
        <Input value={d.name} onChange={e=>setD(x=>({...x,name:e.target.value}))} placeholder="項目名"/>
        <Select value={d.cat} onChange={e=>setD(x=>({...x,cat:e.target.value}))} options={FIXED_EXPENSE_CATEGORIES} icons={FIXED_EXPENSE_CATEGORY_ICONS}/>
        <Input money type="number" value={d.amt} onChange={e=>setD(x=>({...x,amt:e.target.value}))} placeholder="月額（円）"/>
      </div>
      <div style={{display:"flex",gap:10}}>
        <button onClick={()=>{const a=parseYenAmount(d.amt);if(!d.name||!a)return;onSave({...item,name:d.name,category:d.cat,amount:a});setEd(false);}} style={STYLE_BUTTON_PRIMARY}>保存</button>
        <button onClick={()=>setEd(false)} style={{...STYLE_BUTTON_OUTLINE,minHeight:44,padding:"11px 18px"}}>キャンセル</button>
      </div>
    </div>
  );

  // 通常表示：項目名・カテゴリ・金額を並べて表示
  return (
    <div style={{...STYLE_CARD}}>
      <div style={{display:"flex",alignItems:"center",gap:12,marginBottom:10}}>
        {/* カテゴリ絵文字アイコン */}
        <div style={{width:40,height:40,borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",fontSize:16,background:"rgba(255,255,255,0.06)",color:COLOR_TEXT_SECONDARY,flexShrink:0}}>{FIXED_EXPENSE_CATEGORY_ICONS[item.category]||"📌"}</div>
        <div style={{flex:1,minWidth:0}}>
          <div style={{fontSize:13,fontWeight:600}}>{item.name}</div>
          <div style={{fontSize:11,color:COLOR_TEXT_SECONDARY}}>{item.category}</div>
        </div>
        <div style={{fontFamily:"monospace",fontSize:14,fontWeight:700,flexShrink:0}}>{formatYen(item.amount)}<span style={{fontSize:10,color:COLOR_TEXT_HINT}}>/月</span></div>
      </div>
      <div style={{display:"flex",gap:8}}>
        {/* 編集ボタン：クリックで編集フォームを開く */}
        <button onClick={()=>{setD({name:item.name,cat:item.category,amt:String(item.amount)});setEd(true);}} style={{...STYLE_BUTTON_OUTLINE,flex:1,textAlign:"center"}}>編集</button>
        <button onClick={onDelete} style={{...STYLE_BUTTON_OUTLINE,flex:1,textAlign:"center"}}>削除</button>
        {/* 上下移動ボタン：渡されていない時は無効表示 */}
        <button onClick={onMoveUp} disabled={!onMoveUp} style={{...STYLE_BUTTON_OUTLINE,opacity:onMoveUp?1:0.35,padding:"8px 16px"}}>↑</button>
        <button onClick={onMoveDown} disabled={!onMoveDown} style={{...STYLE_BUTTON_OUTLINE,opacity:onMoveDown?1:0.35,padding:"8px 16px"}}>↓</button>
      </div>
    </div>
  );
}
