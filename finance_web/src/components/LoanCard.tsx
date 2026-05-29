// ────────── ローン1件カードコンポーネント ──────────
// ローン・借入1件分の情報表示と、手動/自動返済モードの切替・反映ボタンを提供する

import { useState, CSSProperties } from "react";
import { calculateMonthlyInterest, calculateTotalInterest, calculateCompletionDate } from "../utils/loanCalc";
import { formatYen, formatAmount } from "../utils/format";
import { STYLE_CARD, STYLE_BUTTON_PRIMARY, STYLE_BUTTON_OUTLINE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_HINT, COLOR_BORDER, COLOR_ACCENT, COLOR_POSITIVE, COLOR_NEGATIVE } from "../utils/styles";
import { Input, StatLabel } from "./ui";
import PrepaymentSimulator from "./PrepaymentSimulator";

// ── スタイル定数 ──────────────────────────────────────────

// 完済バッジ（✓ 完済）
const STYLE_LOAN_COMPLETE_BADGE: CSSProperties = {
  fontSize: 12, fontWeight: 700, color: COLOR_POSITIVE,
  background: "rgba(52,211,153,0.1)", borderRadius: 5,
  padding: "2px 8px", display: "inline-block", marginBottom: 4,
};

// 手動↔自動トグルスライダー本体の静的スタイル（background は isAuto で動的に変わる）
const STYLE_LOAN_TOGGLE_BASE: CSSProperties = {
  width: 44, height: 24, borderRadius: 12,
  position: "relative", cursor: "pointer",
  transition: "background 0.2s", flexShrink: 0,
};

// トグルスライダー内の丸ノブの静的スタイル（left は isAuto で動的に変わる）
const STYLE_LOAN_TOGGLE_KNOB: CSSProperties = {
  position: "absolute", top: 3,
  width: 18, height: 18, borderRadius: "50%",
  background: "white", transition: "left 0.2s",
};

// 完済予定日ボックス
const STYLE_LOAN_COMPLETION_BOX: CSSProperties = {
  background: "rgba(255,255,255,0.03)", border: `1px solid ${COLOR_BORDER}`,
  borderRadius: 12, padding: "12px 14px", marginBottom: 10,
  display: "flex", justifyContent: "space-between", alignItems: "center",
};

// ─────────────────────────────────────────────────────────

// ローン1件分のデータ型
interface LoanItem {
  id: string;
  name: string;
  rate: number;
  remaining: number;
  monthly: number;
  principal?: number;
  payDay?: string;
  autoMode?: boolean;
  lastAutoPaid?: string;
}
// このコンポーネントが受け取る props の型
interface LoanCardProps {
  loan: LoanItem;
  onEdit: () => void;
  onDelete: () => void;
  payVal: string;
  onPayChange: (v: string) => void;
  onPaySubmit: () => void;
  onToggleAuto: () => void;
}

export default function LoanCard({loan,onEdit,onDelete,payVal,onPayChange,onPaySubmit,onToggleAuto}: LoanCardProps) {
  // 繰り上げ返済シミュレーターの表示フラグ
  const [simOpen, setSimOpen] = useState(false);
  // 完済予定月・総利息を計算する
  const ti   = calculateTotalInterest(loan.remaining, loan.rate, loan.monthly);
  const comp = ti ? calculateCompletionDate(ti.months) : null;
  const paid = Number(loan.remaining) === 0; // 残債ゼロ = 完済済み
  const mi   = calculateMonthlyInterest(loan.remaining, loan.rate); // 今月の利息額
  // 元本があれば返済進捗率を計算（cf/bl は principal が無いケースがある）
  const principalNum = Number(loan.principal || 0);
  const progressPct = principalNum > 0 ? Math.min(100, Math.max(0, ((principalNum - loan.remaining) / principalNum) * 100)) : null;
  // 毎月返済額が月利息以下だと永久に完済できない（警告を出す）
  const insuf  = !paid && loan.monthly > 0 && loan.monthly <= mi && loan.rate > 0;
  const isAuto = !!loan.autoMode; // 自動モードかどうか
  const hasPayDay = loan.payDay && loan.payDay !== "未設定"; // 引落日が設定されているか

  return (
    <div style={{...STYLE_CARD,opacity:paid?0.75:1}}>
      {/* ヘッダー：ローン名・金利・編集/削除ボタン */}
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:12}}>
        <div style={{flex:1,minWidth:0}}>
          {paid && <div style={STYLE_LOAN_COMPLETE_BADGE}>✓ 完済</div>}
          <div style={{fontSize:15,fontWeight:700}}>{loan.name}</div>
          <div style={{fontSize:12,color:COLOR_TEXT_HINT,marginTop:2}}>
            金利 <span style={{fontFamily:"monospace",color:COLOR_TEXT_PRIMARY,fontWeight:700}}>{loan.rate}%</span>
            {hasPayDay && <span style={{marginLeft:8}}>毎月<span style={{fontFamily:"monospace",color:COLOR_TEXT_SECONDARY,fontWeight:600}}>{loan.payDay}</span>引落</span>}
          </div>
        </div>
        <div style={{display:"flex",gap:8,flexShrink:0}}>
          <button type="button" onClick={onEdit} style={STYLE_BUTTON_OUTLINE}>編集</button>
          <button type="button" onClick={onDelete} style={STYLE_BUTTON_OUTLINE}>削除</button>
        </div>
      </div>

      {/* 返済モード切替トグル（完済済みは表示しない） */}
      {!paid && <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:12,background:"rgba(255,255,255,0.02)",borderRadius:10,padding:"10px 12px"}}>
        <span style={{fontSize:12,color:COLOR_TEXT_HINT,flex:1}}>返済モード</span>
        <span style={{fontSize:12,color:isAuto?COLOR_TEXT_HINT:COLOR_TEXT_PRIMARY,fontWeight:isAuto?400:700}}>手動</span>
        {/* スライドトグルボタン：クリックで手動↔自動を切り替える */}
        <div onClick={onToggleAuto} style={{...STYLE_LOAN_TOGGLE_BASE,background:isAuto?COLOR_ACCENT:"rgba(255,255,255,0.1)"}}>
          <div style={{...STYLE_LOAN_TOGGLE_KNOB,left:isAuto?23:3}}/>
        </div>
        <span style={{fontSize:12,color:isAuto?COLOR_TEXT_PRIMARY:COLOR_TEXT_HINT,fontWeight:isAuto?700:400}}>自動</span>
      </div>}

      {/* 月返済額が月利息を下回っている場合の警告 */}
      {insuf && <div style={{background:"rgba(248,113,113,0.06)",border:"1px solid rgba(248,113,113,0.3)",borderRadius:10,padding:"10px 14px",marginBottom:10,fontSize:12,color:COLOR_NEGATIVE}}>⚠️ 月返済({formatYen(loan.monthly)})が月利息({formatYen(mi)})を下回っています</div>}

      {/* 自動モードだが引落日未設定の時の警告 */}
      {!paid && isAuto && !hasPayDay && <div style={{background:"rgba(248,113,113,0.06)",border:"1px solid rgba(248,113,113,0.3)",borderRadius:10,padding:"10px 14px",marginBottom:10,fontSize:12,color:COLOR_NEGATIVE}}>⚠️ 自動モードには引落日の設定が必要です（編集から設定してください）</div>}

      {/* 完済予定日 */}
      {!paid && comp && <div style={STYLE_LOAN_COMPLETION_BOX}>
        <div>
          <div style={{fontSize:12,color:COLOR_TEXT_HINT,marginBottom:3}}>完済予定</div>
          <span style={{fontFamily:"monospace",fontSize:20,fontWeight:700}}>{comp.y}年{comp.m}月</span>
          <span style={{fontSize:12,color:COLOR_TEXT_SECONDARY,marginLeft:8}}>あと{ti.months}ヶ月</span>
        </div>
        <span style={{fontSize:26}}>🏁</span>
      </div>}

      {/* 総利息 */}
      {!paid && ti && ti.interest > 0 && <div style={{background:"rgba(248,113,113,0.06)",border:"1px solid rgba(248,113,113,0.2)",borderRadius:10,padding:"10px 14px",marginBottom:10,color:COLOR_NEGATIVE,fontSize:12}}>💸 総利息 <span style={{fontFamily:"monospace",fontSize:16,fontWeight:700}}>{formatYen(ti.interest)}</span></div>}

      {/* 残債・月返済額・今月の利息・利息割合の4つをグリッドで表示 */}
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8,marginBottom:12}}>
        <StatLabel label="残債"     value={formatYen(loan.remaining)} color={paid?COLOR_POSITIVE:COLOR_TEXT_PRIMARY}/>
        <StatLabel label="月返済額" value={formatYen(loan.monthly)}/>
        <StatLabel label="今月の利息" value={formatYen(mi)} color={COLOR_NEGATIVE}/>
        <StatLabel label="利息割合" value={loan.remaining>0&&loan.monthly>0?((mi/loan.monthly)*100).toFixed(0)+"%":"—"} color={COLOR_NEGATIVE}/>
      </div>

      {/* 手動モードの時だけ「今月の返済額を反映」フォームを出す */}
      {!paid && !isAuto && <div style={{background:"rgba(255,255,255,0.03)",borderRadius:10,padding:10}}>
        <div style={{fontSize:12,color:COLOR_TEXT_HINT,marginBottom:8}}>今月の返済額を反映</div>
        <div style={{display:"flex",gap:8}}>
          <Input money type="number" value={payVal} onChange={e=>onPayChange(e.target.value)} placeholder={formatAmount(loan.monthly||"")} style={{textAlign:"right"}}/>
          <button type="button" onClick={onPaySubmit} style={{...STYLE_BUTTON_PRIMARY,width:"auto",padding:"11px 16px",whiteSpace:"nowrap"}}>反映</button>
        </div>
      </div>}

      {/* 自動モード・引落日設定済みの時は説明文を表示 */}
      {!paid && isAuto && hasPayDay && <div style={{background:"rgba(129,140,248,0.06)",border:"1px solid rgba(129,140,248,0.2)",borderRadius:10,padding:"10px 14px",fontSize:12,color:COLOR_ACCENT}}>🔄 毎月{loan.payDay}に自動で残債から引落します</div>}

      {/* 返済進捗バー：元本データがあるローンのみ表示（住宅・車ローン等） */}
      {!paid && progressPct !== null && (
        <div style={{marginTop:12}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"baseline",marginBottom:6}}>
            <span style={{fontSize:12,color:COLOR_TEXT_HINT,letterSpacing:"1px",textTransform:"uppercase"}}>元本の返済進捗</span>
            <span style={{fontFamily:"monospace",fontSize:13,fontWeight:700,color:COLOR_POSITIVE}}>{progressPct.toFixed(1)}%</span>
          </div>
          <div style={{height:6,background:"rgba(255,255,255,0.06)",borderRadius:3,overflow:"hidden"}}>
            <div style={{height:"100%",width:`${progressPct}%`,background:COLOR_POSITIVE,borderRadius:3,transition:"width 0.4s ease"}}/>
          </div>
          <div style={{fontSize:12,color:COLOR_TEXT_HINT,marginTop:4,fontFamily:"monospace"}}>
            {formatYen(principalNum - loan.remaining)} 返済済 / 元本 {formatYen(principalNum)}
          </div>
        </div>
      )}

      {/* 繰り上げ返済シミュレーターボタン（完済済みは出さない） */}
      {!paid && (
        <button type="button"
          onClick={()=>setSimOpen(true)}
          style={{...STYLE_BUTTON_OUTLINE,width:"100%",marginTop:12,fontSize:12,color:COLOR_ACCENT,borderColor:`${COLOR_ACCENT}55`}}
        >
          💪 繰り上げ返済をシミュレート
        </button>
      )}

      {/* シミュレーターモーダル */}
      {simOpen && <PrepaymentSimulator loan={loan} onClose={()=>setSimOpen(false)}/>}
    </div>
  );
}
