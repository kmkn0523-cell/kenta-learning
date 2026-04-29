import { useState, useEffect, useMemo, useCallback, useRef } from "react";

const mem = {};
function usePersist(key, init) {
  const [val, setVal] = useState(() => mem[key] !== undefined ? mem[key] : init);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    let alive = true;
    (async () => {
      if (window.storage) try {
        const r = await window.storage.get(key);
        if (alive && r?.value) { const p = JSON.parse(r.value); mem[key] = p; setVal(p); }
      } catch (_) {}
      if (alive) setReady(true);
    })();
    return () => { alive = false; };
  }, [key]);
  const set = useCallback((u) => setVal(prev => {
    const next = typeof u === "function" ? u(prev) : u;
    mem[key] = next;
    if (window.storage) window.storage.set(key, JSON.stringify(next)).catch(() => {});
    return next;
  }), [key]);
  return [val, set, ready];
}

const yen = n => "¥" + Number(n).toLocaleString("ja-JP");
const MLS = ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"];
const ECATS = ["食費","住居","交通","光熱費","娯楽","医療","衣服","通信費","その他"];
const FCATS = ["家賃","サブスク","保険","通信費","駐車場","その他固定費"];
const ICATS = ["給与","副業","ボーナス","臨時収入","その他収入"];
const EICO = {"食費":"🍽️","住居":"🏠","交通":"🚃","光熱費":"💡","娯楽":"🎮","医療":"💊","衣服":"👕","通信費":"📱","その他":"📦"};
const FICO = {"家賃":"🏠","サブスク":"🎬","保険":"🛡️","通信費":"📱","駐車場":"🅿️","その他固定費":"📌"};
const IICO = {"給与":"💼","副業":"💻","ボーナス":"🎁","臨時収入":"✨","その他収入":"💰"};

function mInt(rem, rate) { return Math.round(Number(rem) * (Number(rate) / 100 / 12)); }
function tInt(rem, rate, mo) {
  const r = Number(rate)/100/12, m = Number(mo), rv = Number(rem);
  if (!rv || !m) return null;
  if (r === 0) return { interest: 0, months: Math.ceil(rv/m) };
  if (m <= rv*r) return null;
  const months = Math.ceil(-Math.log(1-(rv*r)/m) / Math.log(1+r));
  return { interest: Math.round(m*months-rv), months };
}
function cDate(months) {
  if (!months) return null;
  const d = new Date(); d.setMonth(d.getMonth() + months);
  return { y: d.getFullYear(), m: d.getMonth()+1 };
}

const INIT_FX = [
  {id:1,name:"家賃",category:"家賃",amount:69000},
  {id:2,name:"国民健康保険",category:"その他固定費",amount:35400},
  {id:3,name:"電気",category:"その他固定費",amount:13000},
  {id:4,name:"docomo携帯",category:"通信費",amount:8073},
  {id:5,name:"水道",category:"その他固定費",amount:3900},
  {id:6,name:"ahamo光",category:"通信費",amount:3630},
  {id:7,name:"amex",category:"サブスク",amount:1100},
  {id:8,name:"uber",category:"サブスク",amount:498},
];
const INIT_CF = [
  {id:101,name:"アイフル",rate:18,remaining:99000,monthly:4000},
  {id:102,name:"アコム",rate:18,remaining:900530,monthly:30000},
  {id:103,name:"レイク",rate:18,remaining:213052,monthly:12000},
];
const INIT_BL = [
  {id:201,name:"三井住友カード リボ",rate:15,remaining:609385,monthly:30000},
  {id:202,name:"セブンカード リボ",rate:15,remaining:100000,monthly:4000},
  {id:203,name:"みんなの銀行 Loan",rate:4.96,remaining:300000,monthly:1241},
];
const INIT_LO = [{id:1,name:"アプラス（ショッピングローン）",principal:1130000,remaining:1130000,rate:0,monthly:18800}];

const BG="#0a0a0c",T="#f5f5f7",T2="#9a9aa3",T3="#5a5a63",BD="rgba(255,255,255,0.08)",AC="#818cf8",POS="#34d399",NEG="#f87171";
const CARD={background:"rgba(255,255,255,0.03)",border:`1px solid ${BD}`,borderRadius:14,padding:16,marginBottom:12};
const IS={background:"rgba(255,255,255,0.05)",border:`1px solid ${BD}`,borderRadius:10,padding:"11px 13px",color:T,fontSize:15,outline:"none",width:"100%",fontFamily:"inherit",minHeight:44,boxSizing:"border-box"};
const BS={border:"none",borderRadius:10,padding:"12px 0",cursor:"pointer",fontSize:14,fontWeight:700,background:AC,color:"#0a0a0c",width:"100%",fontFamily:"inherit",minHeight:44};
const OS={background:"transparent",border:`1px solid ${BD}`,borderRadius:10,padding:"8px 14px",cursor:"pointer",fontSize:13,color:T2,fontFamily:"inherit",minHeight:40};

const Inp=({value,onChange,type,placeholder,style})=><input type={type||"text"} value={value} onChange={onChange} placeholder={placeholder} style={{...IS,...style}} inputMode={type==="number"?"decimal":undefined}/>;
const Sel=({value,onChange,options,icons})=><select value={value} onChange={onChange} style={{...IS,cursor:"pointer"}}>{options.map(o=><option key={o} value={o}>{icons?icons[o]+" ":""}{o}</option>)}</select>;
const Stat=({label,value,color})=><div style={{background:"rgba(255,255,255,0.03)",border:`1px solid ${BD}`,borderRadius:12,padding:"11px 8px",textAlign:"center"}}><div style={{fontSize:9,color:T3,marginBottom:4,letterSpacing:"0.5px"}}>{label}</div><div style={{fontSize:13,fontWeight:700,fontFamily:"monospace",color:color||T}}>{value}</div></div>;
const Bar=({label,value,max,color,icon})=><div style={{display:"flex",alignItems:"center",gap:10,marginBottom:9}}><div style={{fontSize:11,color,width:78,display:"flex",alignItems:"center",gap:4,overflow:"hidden",flexShrink:0}}>{icon&&<span>{icon}</span>}<span style={{overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{label}</span></div><div style={{flex:1,height:6,background:"rgba(255,255,255,0.06)",borderRadius:3,overflow:"hidden"}}><div style={{height:"100%",borderRadius:3,background:color,opacity:0.8,width:Math.min(100,(value/(max||1))*100)+"%"}}/></div><div style={{fontSize:11,color:T2,width:82,textAlign:"right",fontFamily:"monospace",flexShrink:0}}>{yen(value)}</div></div>;
function Toast({data}){ if(!data) return null; const cl=data.type==="error"?NEG:data.type==="info"?T2:POS; return <div style={{position:"fixed",top:14,left:"50%",transform:"translateX(-50%)",zIndex:999,padding:"9px 18px",borderRadius:20,fontSize:13,fontWeight:600,whiteSpace:"nowrap",pointerEvents:"none",color:cl,background:"rgba(10,10,14,0.92)",border:`1px solid ${cl}44`}}>{data.msg}</div>; }
function Dlg({data,onOk,onCancel}){ if(!data) return null; return <div onClick={onCancel} style={{position:"fixed",inset:0,background:"rgba(0,0,0,0.72)",zIndex:200,display:"flex",alignItems:"center",justifyContent:"center",padding:20}}><div onClick={e=>e.stopPropagation()} style={{background:"#18181f",border:`1px solid ${BD}`,borderRadius:20,padding:24,width:"100%",maxWidth:340}}><div style={{fontSize:15,fontWeight:600,marginBottom:8}}>{data.title}</div><div style={{fontSize:13,color:T2,marginBottom:20}}>{data.msg||"この操作は元に戻せません。"}</div><div style={{display:"flex",gap:10}}><button onClick={onCancel} style={{...OS,flex:1,minHeight:44,padding:12}}>キャンセル</button><button onClick={onOk} style={{...BS,flex:1,background:NEG}}>削除する</button></div></div></div>; }

function FxRow({item,onSave,onDelete}){
  const [ed,setEd]=useState(false);
  const [d,setD]=useState({});
  if(ed) return <div style={CARD}><div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:12}}><Inp value={d.name} onChange={e=>setD(x=>({...x,name:e.target.value}))} placeholder="項目名"/><Sel value={d.cat} onChange={e=>setD(x=>({...x,cat:e.target.value}))} options={FCATS} icons={FICO}/><Inp type="number" value={d.amt} onChange={e=>setD(x=>({...x,amt:e.target.value}))} placeholder="月額（円）"/></div><div style={{display:"flex",gap:10}}><button onClick={()=>{const a=Number(d.amt);if(!d.name||!a)return;onSave({...item,name:d.name,category:d.cat,amount:a});setEd(false);}} style={BS}>保存</button><button onClick={()=>setEd(false)} style={{...OS,minHeight:44,padding:"11px 18px"}}>キャンセル</button></div></div>;
  return <div style={{display:"flex",alignItems:"center",gap:12,...CARD}}><div style={{width:40,height:40,borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",fontSize:16,background:"rgba(255,255,255,0.06)",color:T2,flexShrink:0}}>{FICO[item.category]||"📌"}</div><div style={{flex:1,minWidth:0}}><div style={{fontSize:13,fontWeight:600}}>{item.name}</div><div style={{fontSize:11,color:T2}}>{item.category}</div></div><div style={{fontFamily:"monospace",fontSize:14,fontWeight:700}}>{yen(item.amount)}<span style={{fontSize:10,color:T3}}>/月</span></div><button onClick={()=>{setD({name:item.name,cat:item.category,amt:String(item.amount)});setEd(true);}} style={OS}>編集</button><button onClick={onDelete} style={OS}>削除</button></div>;
}

function TxRow({item,onSave,onDelete,cats,ico,isInc}){
  const [ed,setEd]=useState(false);
  const [d,setD]=useState({});
  const bg=isInc?"rgba(52,211,153,0.12)":"rgba(248,113,113,0.12)";
  const col=isInc?POS:NEG;
  if(ed) return <div style={CARD}><div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:12}}><Sel value={d.cat} onChange={e=>setD(x=>({...x,cat:e.target.value}))} options={cats} icons={ico}/><Inp type="number" value={d.amt} onChange={e=>setD(x=>({...x,amt:e.target.value}))} placeholder="金額（円）"/><Inp type="date" value={d.date} onChange={e=>setD(x=>({...x,date:e.target.value}))}/><Inp value={d.note||""} onChange={e=>setD(x=>({...x,note:e.target.value}))} placeholder="メモ（任意）"/></div><div style={{display:"flex",gap:10}}><button onClick={()=>{const a=Number(d.amt);if(!a)return;onSave({...item,category:d.cat,amount:a,date:d.date,note:d.note||""});setEd(false);}} style={BS}>保存</button><button onClick={()=>setEd(false)} style={{...OS,minHeight:44,padding:"11px 18px"}}>キャンセル</button></div></div>;
  return <div style={{display:"flex",alignItems:"center",gap:12,...CARD}}><div style={{width:40,height:40,borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",fontSize:16,background:bg,color:col,flexShrink:0}}>{ico[item.category]||"●"}</div><div style={{flex:1,minWidth:0}}><div style={{fontSize:13,fontWeight:600}}>{item.category} <span style={{fontSize:11,color:T3}}>{item.note}</span></div><div style={{fontSize:11,color:T3,marginTop:2}}>{item.date}</div></div><div style={{fontFamily:"monospace",fontSize:14,fontWeight:700,color:col}}>{isInc?"+":"-"}{yen(item.amount)}</div><button onClick={()=>{setD({cat:item.category,amt:String(item.amount),date:item.date,note:item.note||""});setEd(true);}} style={OS}>編集</button><button onClick={onDelete} style={OS}>削除</button></div>;
}

function LoanCard({loan,onEdit,onDelete,payVal,onPayChange,onPaySubmit}){
  const ti=tInt(loan.remaining,loan.rate,loan.monthly),comp=ti?cDate(ti.months):null;
  const paid=Number(loan.remaining)===0,mi=mInt(loan.remaining,loan.rate);
  const insuf=!paid&&loan.monthly>0&&loan.monthly<=mi&&loan.rate>0;
  return <div style={{...CARD,opacity:paid?0.75:1}}>
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:12}}>
      <div style={{flex:1,minWidth:0}}>{paid&&<div style={{fontSize:10,fontWeight:700,color:POS,background:"rgba(52,211,153,0.1)",borderRadius:5,padding:"2px 8px",display:"inline-block",marginBottom:4}}>✓ 完済</div>}<div style={{fontSize:15,fontWeight:700}}>{loan.name}</div>    <div style={{fontSize:11,color:T3,marginTop:2}}>金利 <span style={{fontFamily:"monospace",color:T,fontWeight:700}}>{loan.rate}%</span>{loan.payDay&&loan.payDay!=="未設定"&&<span style={{marginLeft:8}}>毎月<span style={{fontFamily:"monospace",color:T2,fontWeight:600}}>{loan.payDay}</span>引落</span>}</div></div>
      <div style={{display:"flex",gap:8,flexShrink:0}}><button onClick={onEdit} style={OS}>編集</button><button onClick={onDelete} style={OS}>削除</button></div>
    </div>
    {insuf&&<div style={{background:"rgba(248,113,113,0.06)",border:"1px solid rgba(248,113,113,0.3)",borderRadius:10,padding:"10px 14px",marginBottom:10,fontSize:12,color:NEG}}>⚠️ 月返済({yen(loan.monthly)})が月利息({yen(mi)})を下回っています</div>}
    {!paid&&comp&&<div style={{background:"rgba(255,255,255,0.03)",border:`1px solid ${BD}`,borderRadius:12,padding:"12px 14px",marginBottom:10,display:"flex",justifyContent:"space-between",alignItems:"center"}}><div><div style={{fontSize:10,color:T3,marginBottom:3}}>完済予定</div><span style={{fontFamily:"monospace",fontSize:20,fontWeight:700}}>{comp.y}年{comp.m}月</span><span style={{fontSize:11,color:T2,marginLeft:8}}>あと{ti.months}ヶ月</span></div><span style={{fontSize:26}}>🏁</span></div>}
    {!paid&&ti&&ti.interest>0&&<div style={{background:"rgba(248,113,113,0.06)",border:"1px solid rgba(248,113,113,0.2)",borderRadius:10,padding:"10px 14px",marginBottom:10,color:NEG,fontSize:12}}>💸 総利息 <span style={{fontFamily:"monospace",fontSize:16,fontWeight:700}}>{yen(ti.interest)}</span></div>}
    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8,marginBottom:12}}><Stat label="残債" value={yen(loan.remaining)} color={paid?POS:T}/><Stat label="月返済額" value={yen(loan.monthly)}/><Stat label="今月の利息" value={yen(mi)} color={NEG}/><Stat label="利息割合" value={loan.remaining>0&&loan.monthly>0?((mi/loan.monthly)*100).toFixed(0)+"%":"—"} color={NEG}/></div>
    {!paid&&<div style={{background:"rgba(255,255,255,0.03)",borderRadius:10,padding:10}}><div style={{fontSize:11,color:T3,marginBottom:8}}>今月の返済額を反映</div><div style={{display:"flex",gap:8}}><Inp type="number" value={payVal} onChange={e=>onPayChange(e.target.value)} placeholder={String(loan.monthly||"")} style={{textAlign:"right"}}/><button onClick={onPaySubmit} style={{...BS,width:"auto",padding:"11px 16px",whiteSpace:"nowrap"}}>反映</button></div></div>}
  </div>;
}

function LoanSection({arr,setArr,pfx,pays,setPays,showPrincipal,onDelete,showT}){
  const [showF,setShowF]=useState(false),[edId,setEdId]=useState(null),[f,setF]=useState({name:"",prin:"",rem:"",rate:"",mo:""});
  function save(){const rem=Number(f.rem);if(!f.name||isNaN(rem)){showT("名称と残債を入力","error");return;}const d={name:f.name,rate:Number(f.rate),remaining:rem,monthly:Number(f.mo),principal:Number(f.prin||0),payDay:f.payDay||"未設定"};  if(edId)setArr(p=>p.map(l=>l.id===edId?{...d,id:edId,lastAutoPaid:l.lastAutoPaid}:l));else setArr(p=>[...p,{...d,id:Date.now()}]);setEdId(null);setShowF(false);setF({name:"",prin:"",rem:"",rate:"",mo:""});showT("保存しました");}
  function pay(id){const k=pfx+id,p=Number(pays[k]);if(!p)return;const loan=arr.find(l=>l.id===id);if(!loan)return;const nr=Math.max(0,loan.remaining-p);setArr(prev=>prev.map(l=>l.id===id?{...l,remaining:nr}:l));setPays(pp=>({...pp,[k]:""}));showT(nr===0?"🎉 完済！":"返済を反映しました",nr===0?"success":"info");}
  const sumOf=k=>arr.reduce((s,l)=>s+Number(l[k]||0),0);
  return <div>
    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8,marginBottom:14}}><Stat label="総残債" value={yen(sumOf("remaining"))}/><Stat label="月次返済" value={yen(sumOf("monthly"))}/><Stat label="今月の利息" value={yen(arr.reduce((s,l)=>s+mInt(l.remaining,l.rate),0))} color={NEG}/><Stat label="支払総利息" value={yen(arr.reduce((s,l)=>{const r=tInt(l.remaining,l.rate,l.monthly);return r?s+r.interest:s;},0))} color={NEG}/></div>
    {arr.map(loan=><LoanCard key={loan.id} loan={loan} onEdit={()=>{          setF({name:loan.name,prin:String(loan.principal||""),rem:String(loan.remaining),rate:String(loan.rate),mo:String(loan.monthly),payDay:loan.payDay||"未設定"});setEdId(loan.id);setShowF(true);}} onDelete={()=>onDelete(loan.id,setArr)} payVal={pays[pfx+loan.id]||""} onPayChange={v=>setPays(p=>({...p,[pfx+loan.id]:v}))} onPaySubmit={()=>pay(loan.id)}/>)}
    {!showF&&<button onClick={()=>{setShowF(true);setEdId(null);setF({name:"",prin:"",rem:"",rate:"",mo:""});}} style={{...BS,marginTop:4}}>＋ 追加</button>}
    {showF&&<div style={CARD}><div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:12}}><Inp value={f.name} onChange={e=>setF(x=>({...x,name:e.target.value}))} placeholder="名称"/>{showPrincipal&&<Inp type="number" value={f.prin||""} onChange={e=>setF(x=>({...x,prin:e.target.value}))} placeholder="借入元本（円）"/>}<Inp type="number" value={f.rem} onChange={e=>setF(x=>({...x,rem:e.target.value}))} placeholder="残債（円）"/><Inp type="number" value={f.rate} onChange={e=>setF(x=>({...x,rate:e.target.value}))} placeholder="金利（%）"/>        <Inp type="number" value={f.mo} onChange={e=>setF(x=>({...x,mo:e.target.value}))} placeholder="月返済額（円）"/>
        <Sel value={f.payDay||"未設定"} onChange={e=>setF(x=>({...x,payDay:e.target.value}))} options={["未設定",...Array.from({length:31},(_,i)=>String(i+1)+"日")]} /></div><div style={{display:"flex",gap:10}}><button onClick={save} style={BS}>保存</button><button onClick={()=>{setShowF(false);setEdId(null);}} style={{...OS,minHeight:44,padding:"11px 18px"}}>キャンセル</button></div></div>}
  </div>;
}

export default function App(){
  const today=new Date(),ts=today.toISOString().slice(0,10);
  const [tab,setTab]=useState("dash"),[sm,setSm]=useState(today.getMonth()),[sy,setSy]=useState(today.getFullYear());
  const [tx,setTx,a1]=usePersist("kk_tx",[]);
  const [fx,setFx,a2]=usePersist("kk_fx",INIT_FX);
  const [lo,setLo,a3]=usePersist("kk_lo",INIT_LO);
  const [cf,setCf,a4]=usePersist("kk_cf",INIT_CF);
  const [bl,setBl,a5]=usePersist("kk_bl",INIT_BL);
  const [inc,setInc,a6]=usePersist("kk_inc",[]);
  const [txF,setTxF]=useState({cat:"食費",amt:"",date:ts,note:""});
  const [fxF,setFxF]=useState({name:"",cat:"家賃",amt:"",note:""});
  const [incF,setIncF]=useState({cat:"給与",amt:"",date:ts,note:""});
  const [showFx,setShowFx]=useState(false),[ltab,setLtab]=useState("cf");
  const [pays,setPays]=useState({}),[sq,setSq]=useState(""),[fcat,setFcat]=useState("");
  const [toast,setToast]=useState(null),[dlg,setDlg]=useState(null);
  const tr=useRef(null);
  const showT=useCallback((msg,type)=>{if(tr.current)clearTimeout(tr.current);setToast({msg,type:type||"success"});tr.current=setTimeout(()=>setToast(null),2200);},[]);
  const ask=useCallback((t,m,ok)=>setDlg({title:t,msg:m,onOk:ok}),[]);
  const delItem=useCallback((id,setArr)=>ask("削除しますか？","",()=>{setArr(p=>p.filter(x=>x.id!==id));showT("削除しました","error");}),[ask,showT]);
  const allOk=a1&&a2&&a3&&a4&&a5&&a6;
  const ms=sy+"-"+String(sm+1).padStart(2,"0");
  const mTx=useMemo(()=>tx.filter(t=>t.date?.startsWith(ms)),[tx,ms]);
  const mInc=useMemo(()=>inc.filter(i=>i.date?.startsWith(ms)),[inc,ms]);
  const allL=useMemo(()=>[...lo,...cf,...bl],[lo,cf,bl]);
  const tVar=useMemo(()=>mTx.reduce((s,t)=>s+Number(t.amount||0),0),[mTx]);
  const tFx=useMemo(()=>fx.reduce((s,f)=>s+Number(f.amount||0),0),[fx]);
  const tRep=allL.reduce((s,l)=>s+Number(l.monthly||0),0);
  const tInc=mInc.reduce((s,i)=>s+Number(i.amount||0),0);
  const tBur=tVar+tFx+tRep,net=tInc-tBur;
  const expByCat=useMemo(()=>{const m={};mTx.forEach(t=>{if(t.category)m[t.category]=(m[t.category]||0)+Number(t.amount||0);});return Object.entries(m).sort((a,b)=>b[1]-a[1]);},[mTx]);
  const fTx=useMemo(()=>{let l=mTx;if(fcat)l=l.filter(t=>t.category===fcat);if(sq.trim()){const q=sq.toLowerCase();l=l.filter(t=>(t.note||"").toLowerCase().includes(q)||String(t.amount).includes(q));}return l;},[mTx,fcat,sq]);
  function prevM(){if(sm===0){setSm(11);setSy(y=>y-1);}else setSm(m=>m-1);}
  function nextM(){if(sm===11){setSm(0);setSy(y=>y+1);}else setSm(m=>m+1);}
  const isCur=sm===today.getMonth()&&sy===today.getFullYear();

  // 自動引落処理（セッション起動時に1回だけ実行）
  const autoProcessed = useRef(false);
  useEffect(() => {
    if (!allOk || autoProcessed.current) return;
    autoProcessed.current = true;

    function applyAuto(arr, setArr) {
      let changed = false;
      const updated = arr.map(loan => {
        if (!loan.payDay || loan.payDay === "未設定") return loan;
        const dayNum = parseInt(loan.payDay);
        if (isNaN(dayNum)) return loan;

        // lastAutoPaid が未設定なら先月を初期値にする
        let lastPaid = loan.lastAutoPaid;
        if (!lastPaid) {
          const d = new Date(today.getFullYear(), today.getMonth() - 1, 1);
          lastPaid = d.getFullYear() + "-" + String(d.getMonth()+1).padStart(2,"0");
        }

        let [ly, lm] = lastPaid.split("-").map(Number);
        let remaining = loan.remaining;
        let newLastPaid = lastPaid;

        // lastAutoPaid の翌月から今月まで順番に処理
        while (true) {
          lm++; if (lm > 12) { lm = 1; ly++; }
          if (ly > today.getFullYear() || (ly === today.getFullYear() && lm > today.getMonth()+1)) break;
          // 月末より大きい日付は月末に丸める
          const daysInMonth = new Date(ly, lm, 0).getDate();
          const actualDay = Math.min(dayNum, daysInMonth);
          const payDate = new Date(ly, lm-1, actualDay);
          if (today >= payDate && remaining > 0) {
            remaining = Math.max(0, remaining - loan.monthly);
            newLastPaid = ly + "-" + String(lm).padStart(2,"0");
            changed = true;
          }
        }

        return (newLastPaid !== loan.lastAutoPaid || remaining !== loan.remaining)
          ? { ...loan, remaining, lastAutoPaid: newLastPaid }
          : loan;
      });
      if (changed) setArr(updated);
    }

    applyAuto(lo, setLo);
    applyAuto(cf, setCf);
    applyAuto(bl, setBl);
  }, [allOk]);
  function addTx(){const a=Number(txF.amt);if(!a||a<=0){showT("金額を入力","error");return;}setTx(p=>[...p,{id:Date.now(),category:txF.cat,amount:a,date:txF.date,note:txF.note}]);setTxF(f=>({...f,amt:"",note:""}));showT("追加しました");}
  function addInc(){const a=Number(incF.amt);if(!a||a<=0){showT("金額を入力","error");return;}setInc(p=>[...p,{id:Date.now(),category:incF.cat,amount:a,date:incF.date,note:incF.note}]);setIncF(f=>({...f,amt:"",note:""}));showT("追加しました");}
  function addFx(){const a=Number(fxF.amt);if(!fxF.name||!a){showT("項目名と金額を入力","error");return;}setFx(p=>[...p,{id:Date.now(),name:fxF.name,category:fxF.cat,amount:a,note:fxF.note}]);setFxF({name:"",cat:"家賃",amt:"",note:""});setShowFx(false);showT("追加しました");}
  const MN=()=><div style={{display:"flex",alignItems:"center",gap:10,marginBottom:18}}><button onClick={prevM} style={{...OS,width:44,height:44,padding:0,borderRadius:"50%",fontSize:20,display:"flex",alignItems:"center",justifyContent:"center"}}>‹</button><span style={{flex:1,textAlign:"center",fontSize:15,fontWeight:600}}>{sy}年 {MLS[sm]}</span><button onClick={nextM} style={{...OS,width:44,height:44,padding:0,borderRadius:"50%",fontSize:20,display:"flex",alignItems:"center",justifyContent:"center"}}>›</button>{!isCur&&<button onClick={()=>{setSm(today.getMonth());setSy(today.getFullYear());}} style={{...OS,fontSize:11,padding:"6px 12px",minHeight:30}}>今月</button>}</div>;
  const ST=({tabs,v,on})=><div style={{display:"flex",background:"rgba(255,255,255,0.04)",border:`1px solid ${BD}`,borderRadius:12,padding:4,marginBottom:16}}>{tabs.map(([k,l])=><button key={k} onClick={()=>on(k)} style={{flex:1,border:"none",borderRadius:9,padding:"9px 4px",cursor:"pointer",fontSize:12,fontWeight:500,fontFamily:"inherit",background:v===k?"rgba(255,255,255,0.1)":"none",color:v===k?"#fff":T3}}>{l}</button>)}</div>;

  if(!allOk) return <div style={{minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center",background:BG,flexDirection:"column",gap:12}}><div style={{fontSize:36}}>💰</div><div style={{color:T2,fontSize:14}}>読み込み中...</div></div>;

  return <div style={{background:BG,minHeight:"100vh",color:T,fontFamily:'"Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif'}}>
    <Toast data={toast}/>
    <Dlg data={dlg} onOk={()=>{dlg?.onOk();setDlg(null);}} onCancel={()=>setDlg(null)}/>
    <div style={{position:"sticky",top:0,zIndex:50,background:"rgba(6,6,10,0.92)",backdropFilter:"blur(20px)",borderBottom:`1px solid ${BD}`,padding:"0 16px"}}>
      <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"13px 0 11px",maxWidth:520,margin:"0 auto"}}>
        <div><div style={{fontSize:9,letterSpacing:"2.5px",color:T2,textTransform:"uppercase",marginBottom:3}}>Family Finance</div><div style={{fontSize:19,fontWeight:700}}>家計管理</div></div>
        <div style={{textAlign:"right"}}><div style={{fontSize:9,color:T3,marginBottom:2}}>今月の手残り</div><div style={{fontFamily:"monospace",fontSize:16,fontWeight:700,color:net>=0?POS:NEG}}>{net>=0?"+":""}{yen(net)}</div></div>
      </div>
    </div>
    <div style={{padding:"16px 16px 110px",maxWidth:520,margin:"0 auto"}}>
      {tab==="dash"&&<div>
        <MN/>
        <div style={CARD}><div style={{fontSize:10,color:T3,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:6}}>今月の収入</div><div style={{fontFamily:"monospace",fontSize:30,fontWeight:700,marginBottom:10}}>{yen(tInc)}</div><div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}><div style={{fontSize:12,color:T2}}>支出合計 <span style={{fontFamily:"monospace",color:T}}>{yen(tBur)}</span>{tInc>0&&<span style={{marginLeft:8,fontSize:11,color:tBur>tInc?NEG:T2}}>({Math.round(tBur/tInc*100)}%)</span>}</div><div style={{fontSize:13,fontWeight:700,color:net>=0?POS:NEG}}>手残り <span style={{fontFamily:"monospace"}}>{net>=0?"+":""}{yen(net)}</span></div></div></div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:8,marginBottom:12}}><Stat label="変動支出" value={yen(tVar)}/><Stat label="固定費" value={yen(tFx)}/><Stat label="返済合計" value={yen(tRep)}/><Stat label="今月の利息" value={yen(allL.reduce((s,l)=>s+mInt(l.remaining,l.rate),0))} color={NEG}/></div>
        <div style={CARD}><div style={{fontSize:10,color:T3,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:14}}>月次収支バランス</div><Bar label="収入" value={tInc} max={Math.max(tInc,tBur)||1} color={POS}/><Bar label="変動支出" value={tVar} max={Math.max(tInc,tBur)||1} color={T2}/><Bar label="固定費" value={tFx} max={Math.max(tInc,tBur)||1} color={T2}/><Bar label="ローン返済" value={tRep} max={Math.max(tInc,tBur)||1} color={NEG}/></div>
        {expByCat.length>0&&<div style={CARD}><div style={{fontSize:10,color:T3,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:14}}>変動支出 内訳</div>{expByCat.map(([cat,amt])=><Bar key={cat} label={cat} value={amt} max={expByCat[0][1]||1} color={T2} icon={EICO[cat]}/>)}</div>}
        <div style={CARD}>
          <div style={{fontSize:10,color:T3,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:14,display:"flex",justifyContent:"space-between"}}><span>ローン残債一覧</span><span>{allL.length}件</span></div>
          {allL.map(l=>{const ti=tInt(l.remaining,l.rate,l.monthly),comp=ti?cDate(ti.months):null,mi=mInt(l.remaining,l.rate);return <div key={l.id} style={{paddingBottom:12,marginBottom:12,borderBottom:`1px solid ${BD}`}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:5}}><span style={{fontSize:13,fontWeight:600}}>{l.name}</span><span style={{fontFamily:"monospace",fontSize:14,fontWeight:700}}>{yen(l.remaining)}</span></div><div style={{display:"flex",gap:12,fontSize:11,color:T3,flexWrap:"wrap",marginBottom:4}}><span>月返済 <span style={{fontFamily:"monospace",color:T2}}>{yen(l.monthly)}</span></span><span>月利息 <span style={{fontFamily:"monospace",color:NEG}}>{yen(mi)}</span></span><span style={{fontFamily:"monospace"}}>{l.rate}%</span></div>{comp&&<div style={{fontSize:11,color:T3}}>完済予定 <span style={{fontFamily:"monospace",color:T,fontWeight:700}}>{comp.y}年{comp.m}月</span>{ti&&<span style={{marginLeft:8}}>総利息 <span style={{fontFamily:"monospace",color:NEG,fontWeight:700}}>{yen(ti.interest)}</span></span>}</div>}</div>;})}
          <div style={{display:"flex",justifyContent:"space-between"}}><span style={{fontSize:12,color:T3}}>全ローン 支払総利息</span><span style={{fontFamily:"monospace",fontSize:14,fontWeight:700,color:NEG}}>{yen(allL.reduce((s,l)=>{const r=tInt(l.remaining,l.rate,l.monthly);return r?s+r.interest:s;},0))}</span></div>
        </div>
      </div>}
      {tab==="inc"&&<div>
        <div style={CARD}><div style={{fontSize:10,color:T3,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:14}}>収入を入力</div><div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:12}}><Sel value={incF.cat} onChange={e=>setIncF(f=>({...f,cat:e.target.value}))} options={ICATS} icons={IICO}/><Inp type="number" value={incF.amt} onChange={e=>setIncF(f=>({...f,amt:e.target.value}))} placeholder="金額（円）"/><Inp type="date" value={incF.date} onChange={e=>setIncF(f=>({...f,date:e.target.value}))}/><Inp value={incF.note} onChange={e=>setIncF(f=>({...f,note:e.target.value}))} placeholder="メモ（任意）"/></div><button onClick={addInc} style={BS}>追加</button></div>
        <MN/>
        {mInc.length===0?<div style={{textAlign:"center",padding:"44px 0",color:T3}}><div style={{fontSize:36,marginBottom:10}}>💰</div>この月の収入データがありません</div>
        :[...mInc].sort((a,b)=>b.date.localeCompare(a.date)).map(i=><TxRow key={i.id} item={i} cats={ICATS} ico={IICO} isInc onSave={u=>{setInc(p=>p.map(x=>x.id===u.id?u:x));showT("更新しました");}} onDelete={()=>ask("収入を削除しますか？","",()=>{setInc(p=>p.filter(x=>x.id!==i.id));showT("削除しました","error");})}/>)}
      </div>}
      {tab==="fix"&&<div>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:18}}><div><div style={{fontSize:10,color:T3,marginBottom:4}}>毎月の固定費合計</div><div style={{fontFamily:"monospace",fontSize:26,fontWeight:700}}>{yen(tFx)}</div></div><div style={{fontSize:12,color:T3}}>{fx.length}項目</div></div>
        {fx.map(item=><FxRow key={item.id} item={item} onSave={u=>{setFx(p=>p.map(f=>f.id===u.id?u:f));showT("更新しました");}} onDelete={()=>ask("固定費を削除しますか？","",()=>{setFx(p=>p.filter(f=>f.id!==item.id));showT("削除しました","error");})}/>)}
        {showFx?<div style={CARD}><div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:12}}><Inp value={fxF.name} onChange={e=>setFxF(f=>({...f,name:e.target.value}))} placeholder="項目名（例: Netflix）"/><Sel value={fxF.cat} onChange={e=>setFxF(f=>({...f,cat:e.target.value}))} options={FCATS} icons={FICO}/><Inp type="number" value={fxF.amt} onChange={e=>setFxF(f=>({...f,amt:e.target.value}))} placeholder="月額（円）"/></div><div style={{display:"flex",gap:10}}><button onClick={addFx} style={BS}>追加</button><button onClick={()=>setShowFx(false)} style={{...OS,minHeight:44,padding:"11px 18px"}}>キャンセル</button></div></div>:<button onClick={()=>setShowFx(true)} style={{...BS,marginTop:8}}>＋ 固定費を追加</button>}
      </div>}
      {tab==="exp"&&<div>
        <div style={CARD}><div style={{fontSize:10,color:T3,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:14}}>変動支出を入力</div><div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:12}}><Sel value={txF.cat} onChange={e=>setTxF(f=>({...f,cat:e.target.value}))} options={ECATS} icons={EICO}/><Inp type="number" value={txF.amt} onChange={e=>setTxF(f=>({...f,amt:e.target.value}))} placeholder="金額（円）"/><Inp type="date" value={txF.date} onChange={e=>setTxF(f=>({...f,date:e.target.value}))}/><Inp value={txF.note} onChange={e=>setTxF(f=>({...f,note:e.target.value}))} placeholder="メモ（任意）"/></div><button onClick={addTx} style={BS}>追加</button></div>
        <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:14}}><button onClick={prevM} style={{...OS,width:44,height:44,padding:0,borderRadius:"50%",fontSize:20,display:"flex",alignItems:"center",justifyContent:"center"}}>‹</button><span style={{flex:1,textAlign:"center",fontSize:14,fontWeight:600}}>{sy}年 {MLS[sm]}</span><button onClick={nextM} style={{...OS,width:44,height:44,padding:0,borderRadius:"50%",fontSize:20,display:"flex",alignItems:"center",justifyContent:"center"}}>›</button>{!isCur&&<button onClick={()=>{setSm(today.getMonth());setSy(today.getFullYear());}} style={{...OS,fontSize:11,padding:"6px 12px"}}>今月</button>}<span style={{fontFamily:"monospace",fontSize:14,fontWeight:700}}>{yen(tVar)}</span></div>
        {mTx.length>0&&<div style={{marginBottom:12}}><Inp value={sq} onChange={e=>setSq(e.target.value)} placeholder="🔍 検索..." style={{marginBottom:8}}/><div style={{display:"flex",flexWrap:"wrap",gap:6}}>{["",...ECATS.filter(c=>mTx.some(t=>t.category===c))].map(c=><button key={c} onClick={()=>setFcat(fcat===c&&c?"":c)} style={{...OS,borderRadius:20,padding:"6px 12px",fontSize:12,...(fcat===c?{background:T,borderColor:T,color:BG,fontWeight:700}:{})}}>{c?EICO[c]+" "+c:"すべて"}</button>)}</div></div>}
        {mTx.length===0?<div style={{textAlign:"center",padding:"44px 0",color:T3}}><div style={{fontSize:36,marginBottom:10}}>💸</div>この月の支出はありません</div>:fTx.length===0?<div style={{textAlign:"center",padding:"44px 0",color:T3}}>🔍 該当なし</div>:[...fTx].sort((a,b)=>b.date.localeCompare(a.date)).map(t=><TxRow key={t.id} item={t} cats={ECATS} ico={EICO} onSave={u=>{setTx(p=>p.map(x=>x.id===u.id?u:x));showT("更新しました");}} onDelete={()=>ask("支出を削除しますか？","",()=>{setTx(p=>p.filter(x=>x.id!==t.id));showT("削除しました","error");})}/>)}
      </div>}
      {tab==="loan"&&<div>
        <div style={CARD}><div style={{fontSize:10,color:T3,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:12,display:"flex",justifyContent:"space-between"}}><span>全ローン合計</span><span>{allL.length}件</span></div><div style={{display:"flex",justifyContent:"space-between",alignItems:"baseline",marginBottom:10}}><span style={{fontSize:10,color:T3}}>総残債</span><span style={{fontFamily:"monospace",fontSize:24,fontWeight:700}}>{yen(allL.reduce((s,l)=>s+Number(l.remaining||0),0))}</span></div><div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:8}}><Stat label="月次返済" value={yen(tRep)}/><Stat label="今月の利息" value={yen(allL.reduce((s,l)=>s+mInt(l.remaining,l.rate),0))} color={NEG}/><Stat label="支払総利息" value={yen(allL.reduce((s,l)=>{const r=tInt(l.remaining,l.rate,l.monthly);return r?s+r.interest:s;},0))} color={NEG}/></div></div>
        <ST tabs={[["cf","🏧 消費者金融"],["bl","🏛 銀行/リボ"],["lo","🏦 その他"]]} v={ltab} on={setLtab}/>
        {ltab==="cf"&&<LoanSection arr={cf} setArr={setCf} pfx="cf" pays={pays} setPays={setPays} showPrincipal={false} onDelete={delItem} showT={showT}/>}
        {ltab==="bl"&&<LoanSection arr={bl} setArr={setBl} pfx="bl" pays={pays} setPays={setPays} showPrincipal={false} onDelete={delItem} showT={showT}/>}
        {ltab==="lo"&&<LoanSection arr={lo} setArr={setLo} pfx="lo" pays={pays} setPays={setPays} showPrincipal={true} onDelete={delItem} showT={showT}/>}
      </div>}
    </div>
    <nav style={{position:"fixed",bottom:0,left:0,right:0,background:"rgba(8,8,14,0.94)",backdropFilter:"blur(20px)",borderTop:`1px solid ${BD}`,display:"flex",zIndex:100}}>
      {[["dash","📊","概要"],["inc","💰","収入"],["fix","📌","固定費"],["exp","💸","支出"],["loan","🏦","ローン"]].map(([key,icon,label])=>(
        <button key={key} onClick={()=>setTab(key)} style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",padding:"11px 4px 12px",cursor:"pointer",border:"none",background:"none",color:tab===key?T:T3,fontSize:10,gap:4,fontFamily:"inherit",minHeight:58}}>
          <span style={{fontSize:22,lineHeight:1}}>{icon}</span><span>{label}</span>
        </button>
      ))}
    </nav>
  </div>;
}
