// ────────── 月選択ナビゲーション ──────────
// 「‹ 2026年5月 ›」のような月切り替えバー
// 今月以外を表示している時は「今月」ボタンも出る
import { MONTH_LABELS } from "../utils/format";
import { STYLE_BUTTON_OUTLINE } from "../utils/styles";

interface MonthNavProps {
  selectedYear: number;
  selectedMonth: number;
  onChange: (year: number, month: number) => void;
}

export default function MonthNav({ selectedYear, selectedMonth, onChange }: MonthNavProps) {
  // 今日の年月を取得して「今月かどうか」を判定する
  const today = new Date();
  const isCur = selectedMonth === today.getMonth() && selectedYear === today.getFullYear();

  // 前の月へ（1月→前年12月）
  function prev() {
    if (selectedMonth === 0) onChange(selectedYear - 1, 11);
    else onChange(selectedYear, selectedMonth - 1);
  }

  // 次の月へ（12月→翌年1月）
  function next() {
    if (selectedMonth === 11) onChange(selectedYear + 1, 0);
    else onChange(selectedYear, selectedMonth + 1);
  }

  return (
    <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:18}}>
      <button onClick={prev} style={{...STYLE_BUTTON_OUTLINE,width:44,height:44,padding:0,borderRadius:"50%",fontSize:20,display:"flex",alignItems:"center",justifyContent:"center"}}>‹</button>
      <span style={{flex:1,textAlign:"center",fontSize:15,fontWeight:600}}>{selectedYear}年 {MONTH_LABELS[selectedMonth]}</span>
      <button onClick={next} style={{...STYLE_BUTTON_OUTLINE,width:44,height:44,padding:0,borderRadius:"50%",fontSize:20,display:"flex",alignItems:"center",justifyContent:"center"}}>›</button>
      {/* 今月以外を見ている時だけ「今月」ボタンを表示する */}
      {!isCur && <button onClick={()=>onChange(today.getFullYear(),today.getMonth())} style={{...STYLE_BUTTON_OUTLINE,fontSize:12,padding:"6px 12px",minHeight:30}}>今月</button>}
    </div>
  );
}
