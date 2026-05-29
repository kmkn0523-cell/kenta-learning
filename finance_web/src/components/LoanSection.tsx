// ────────── ローンタブ全体コンポーネント ──────────
// 消費者金融・銀行ローン・個人ローン3タブで共通して使われるローン管理セクション

import { useState, useRef } from "react";
import { parseYenAmount, formatYen } from "../utils/format";
import { findRate, FREE, calculateMonthlyInterest, calculateTotalInterest } from "../utils/loanCalc";
import { STYLE_CARD, STYLE_BUTTON_PRIMARY, STYLE_BUTTON_OUTLINE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_HINT, COLOR_BORDER, COLOR_ACCENT, COLOR_NEGATIVE } from "../utils/styles";
import { newId } from "../utils/crypto";
import { Input, Select, StatLabel } from "./ui";
import LoanCard from "./LoanCard";

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
interface LoanSectionProps {
  arr: LoanItem[];
  setArr: (fn: (p: LoanItem[]) => LoanItem[]) => void;
  pfx: string;
  pays: Record<string, string>;
  setPays: (fn: (p: Record<string, string>) => Record<string, string>) => void;
  showPrincipal: boolean;
  onDelete: (id: string, setArr: (fn: (p: LoanItem[]) => LoanItem[]) => void) => void;
  showT: (msg: string, type?: string) => void;
  brands?: string[];
}

// arr/setArr: ローン一覧の state
// pfx: localStorage キーのプレフィックス（'cf_'/'bl_'/'lo_' など）
// pays/setPays: 手動返済入力欄の値を管理する state
// showPrincipal: 借入元本入力欄を出すか
// onDelete: 削除確認ダイアログを開く関数
// showT: トースト通知を表示する関数
// brands: ブランドプリセット一覧（lo タブには渡さない）
export default function LoanSection({arr,setArr,pfx,pays,setPays,showPrincipal,onDelete,showT,brands}: LoanSectionProps) {
  // brands が渡された時だけ「ブランドを選ぶ」UIを出す
  const brandOpts = brands ? [FREE, ...brands] : null;
  const initF = () => ({name:"",prin:"",rem:"",rate:"",mo:"",brand:brandOpts?FREE:""});

  const [showF, setShowF] = useState(false);                     // フォーム表示フラグ
  const edId              = useRef<string | null>(null);          // 編集中のローンID（新規時は null・JSXで使わないためref）
  const [f, setF]         = useState<{name:string;prin:string;rem:string;rate:string;mo:string;brand:string;payDay?:string}>(initF);   // フォームの入力値

  // 金利の注意書きポップアップ：初回のブランド選択時に自動で出す。一度見たら再表示しない
  const [showDisc, setShowDisc] = useState(false);

  // ブランドを選んだ時：名称をブランド名にコピー、残債を元に金利を自動で入れる
  function pickBrand(b) {
    setF(x => {
      const isFree = b === FREE;
      const r = isFree ? null : findRate(b, x.rem);
      return {...x, brand:b, name: isFree?"":b, rate: r==null ? x.rate : String(r)};
    });
    // 実ブランドを選んだ初回だけ注意書きポップアップを出す
    if (b !== FREE) { try { if (!localStorage.getItem("kk_rate_disc_seen")) setShowDisc(true); } catch(error){ console.warn("[LoanSection] localStorage read failed", error); } }
  }

  function closeDisc() { try { localStorage.setItem("kk_rate_disc_seen","1"); } catch(error){ console.warn("[LoanSection] localStorage write failed", error); } setShowDisc(false); }

  // 残債を変更した時：ブランド選択中なら金利テーブルを引き直して自動更新
  function changeRem(v) {
    setF(x => {
      const next = {...x, rem:v};
      if (x.brand && x.brand !== FREE) {
        const r = findRate(x.brand, v);
        if (r != null) next.rate = String(r);
      }
      return next;
    });
  }

  // ローンを保存する（新規追加 or 既存更新）
  function save() {
    const rem = parseYenAmount(f.rem);
    if (!f.name || isNaN(rem)) { showT("名称と残債を入力","error"); return; }
    const d = {name:f.name,rate:parseYenAmount(f.rate),remaining:rem,monthly:parseYenAmount(f.mo),principal:parseYenAmount(f.prin||0),payDay:f.payDay||"未設定"};
    if (edId.current) setArr(p => p.map(l => l.id===edId.current ? {...d,id:edId.current!,lastAutoPaid:l.lastAutoPaid} : l));
    else              setArr(p => [...p, {...d, id:newId()}]);
    edId.current = null; setShowF(false); setF(initF()); showT("保存しました");
  }

  // 手動返済を残債に反映する
  function pay(id) {
    const k = pfx + id;
    const loan = arr.find(l => l.id === id);
    if (!loan) return;
    const p = parseYenAmount(pays[k]) || loan.monthly;
    if (!p) return;
    const nr = Math.max(0, loan.remaining - p);
    setArr(prev => prev.map(l => l.id===id ? {...l, remaining:nr} : l));
    setPays(pp => ({...pp, [k]:""}));
    showT(nr===0 ? "🎉 完済！" : "返済を反映しました", nr===0 ? "success" : "info");
  }

  // 全ローンの合計を出すヘルパー
  const sumOf = k => arr.reduce((s,l) => s + Number(l[k]||0), 0);

  return (
    <div>
      {/* サマリー統計グリッド：総残債・月次返済・今月の利息・支払総利息 */}
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8,marginBottom:14}}>
        <StatLabel label="総残債"    value={formatYen(sumOf("remaining"))}/>
        <StatLabel label="月次返済"  value={formatYen(sumOf("monthly"))}/>
        <StatLabel label="今月の利息" value={formatYen(arr.reduce((s,l)=>s+calculateMonthlyInterest(l.remaining,l.rate),0))} color={COLOR_NEGATIVE}/>
        <StatLabel label="支払総利息" value={formatYen(arr.reduce((s,l)=>{const r=calculateTotalInterest(l.remaining,l.rate,l.monthly);return r?s+r.interest:s;},0))} color={COLOR_NEGATIVE}/>
      </div>

      {/* ローン一覧 */}
      {arr.map(loan =>
        <LoanCard
          key={loan.id}
          loan={loan}
          onEdit={() => {
            // 編集開始：フォームに既存値をセット
            const isPreset = brands && brands.includes(loan.name);
            setF({name:loan.name,prin:String(loan.principal||""),rem:String(loan.remaining),rate:String(loan.rate),mo:String(loan.monthly),payDay:loan.payDay||"未設定",brand:isPreset?loan.name:(brandOpts?FREE:"")});
            edId.current = loan.id; setShowF(true);
          }}
          onDelete={() => onDelete(loan.id, setArr)}
          payVal={pays[pfx+loan.id] || String(loan.monthly||"")}
          onPayChange={v => setPays(p => ({...p, [pfx+loan.id]:v}))}
          onPaySubmit={() => pay(loan.id)}
          onToggleAuto={() => setArr(p => p.map(l => l.id===loan.id ? {...l, autoMode:!l.autoMode} : l))}
        />
      )}

      {/* 追加ボタン：フォームが閉じている時だけ表示 */}
      {!showF && <button onClick={()=>{setShowF(true);edId.current=null;setF(initF());}} style={{...STYLE_BUTTON_PRIMARY,marginTop:4}}>＋ 追加</button>}

      {/* 入力フォーム */}
      {showF && <div style={STYLE_CARD}>
        <div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:12}}>
          {/* ブランドプリセット選択（branches が渡された時だけ表示） */}
          {brandOpts && <div>
            <div style={{fontSize:12,color:COLOR_TEXT_HINT,marginBottom:6,letterSpacing:"0.5px",display:"flex",alignItems:"center",gap:6}}>
              <span>ブランドを選ぶと、借入額に応じた金利を自動で入れます</span>
              <button type="button" onClick={()=>setShowDisc(true)} style={{background:"none",border:"none",color:COLOR_ACCENT,cursor:"pointer",padding:0,fontSize:13,lineHeight:1}} aria-label="金利の注意">ⓘ</button>
            </div>
            <Select value={f.brand||FREE} onChange={e=>pickBrand(e.target.value)} options={brandOpts}/>
          </div>}
          {/* 自由入力の名称欄（brandOpts なし、または FREE を選んでいる時に表示） */}
          {(!brandOpts || f.brand===FREE) && <Input value={f.name} onChange={e=>setF(x=>({...x,name:e.target.value}))} placeholder="名称"/>}
          {/* 借入元本（lo タブで showPrincipal=true の時のみ） */}
          {showPrincipal && <Input money type="number" value={f.prin||""} onChange={e=>setF(x=>({...x,prin:e.target.value}))} placeholder="借入元本（円）"/>}
          <Input money type="number" value={f.rem} onChange={e=>changeRem(e.target.value)} placeholder="残債（円）"/>
          <Input type="number" value={f.rate} onChange={e=>setF(x=>({...x,rate:e.target.value}))} placeholder={f.brand&&f.brand!==FREE?`金利（%）※${f.brand}の目安を自動セット中`:"金利（%）"}/>
          <Input money type="number" value={f.mo} onChange={e=>setF(x=>({...x,mo:e.target.value}))} placeholder="月返済額（円）"/>
          <Select value={f.payDay||"未設定"} onChange={e=>setF(x=>({...x,payDay:e.target.value}))} options={["未設定",...Array.from({length:31},(_,i)=>String(i+1)+"日")]}/>
        </div>
        <div style={{display:"flex",gap:10}}>
          <button onClick={save} style={STYLE_BUTTON_PRIMARY}>保存</button>
          <button onClick={()=>{setShowF(false);edId.current=null;}} style={{...STYLE_BUTTON_OUTLINE,minHeight:44,padding:"11px 18px"}}>キャンセル</button>
        </div>
      </div>}

      {/* 金利の注意書きポップアップ：背景タップ・「わかった」で閉じる */}
      {showDisc && <div onClick={closeDisc} style={{position:"fixed",inset:0,background:"rgba(0,0,0,0.72)",zIndex:300,display:"flex",alignItems:"center",justifyContent:"center",padding:20}}>
        <div onClick={e=>e.stopPropagation()} style={{background:"#18181f",border:`1px solid ${COLOR_BORDER}`,borderRadius:20,padding:24,width:"100%",maxWidth:340}}>
          <div style={{fontSize:28,marginBottom:8,textAlign:"center"}}>⚠️</div>
          <div style={{fontSize:15,fontWeight:700,marginBottom:10,textAlign:"center"}}>金利の自動入力について</div>
          <div style={{fontSize:13,color:COLOR_TEXT_SECONDARY,lineHeight:1.7,marginBottom:20}}>金利テーブルの値は<span style={{color:COLOR_TEXT_PRIMARY,fontWeight:700}}>各社の公表する最高金利の目安</span>です。実際の契約金利は審査結果で変わるため、契約書の金利と違う場合は<span style={{color:COLOR_TEXT_PRIMARY,fontWeight:700}}>金利欄を手で書き換えて</span>ください。</div>
          <button onClick={closeDisc} style={STYLE_BUTTON_PRIMARY}>わかった</button>
        </div>
      </div>}
    </div>
  );
}
