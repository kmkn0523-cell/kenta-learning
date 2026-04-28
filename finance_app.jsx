import { useState, useEffect, useMemo, useCallback, useRef } from "react";

// ────────── ストレージ ──────────
const mem = {};
function usePersist(key, init) {
  const [val, setVal] = useState(() => mem[key] !== undefined ? mem[key] : init);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    let alive = true;
    (async () => {
      if (window.storage) {
        try {
          const r = await window.storage.get(key);
          if (alive && r && r.value) {
            const p = JSON.parse(r.value);
            mem[key] = p;
            setVal(p);
          }
        } catch (_) {}
      }
      if (alive) setReady(true);
    })();
    return () => { alive = false; };
  }, [key]);
  const set = useCallback((u) => {
    setVal(prev => {
      const next = typeof u === "function" ? u(prev) : u;
      mem[key] = next;
      if (window.storage) window.storage.set(key, JSON.stringify(next)).catch(() => {});
      return next;
    });
  }, [key]);
  return [val, set, ready];
}

// ────────── ユーティリティ ──────────
const yen = n => "¥" + Number(n).toLocaleString("ja-JP");
const MLS = ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"];
const ECATS = ["食費","住居","交通","光熱費","娯楽","医療","衣服","通信費","その他"];
const FCATS = ["家賃","サブスク","保険","通信費","駐車場","その他固定費"];
const ICATS = ["給与","副業","ボーナス","臨時収入","その他収入"];
const EICO = {"食費":"🍽️","住居":"🏠","交通":"🚃","光熱費":"💡","娯楽":"🎮","医療":"💊","衣服":"👕","通信費":"📱","その他":"📦"};
const FICO = {"家賃":"🏠","サブスク":"🎬","保険":"🛡️","通信費":"📱","駐車場":"🅿️","その他固定費":"📌"};
const IICO = {"給与":"💼","副業":"💻","ボーナス":"🎁","臨時収入":"✨","その他収入":"💰"};

function calcMonthlyInt(rem, rate) {
  return Math.round(Number(rem) * (Number(rate) / 100 / 12));
}
function calcTotalInt(rem, rate, mo) {
  const r = Number(rate) / 100 / 12;
  const m = Number(mo);
  const rv = Number(rem);
  if (!rv || !m) return null;
  if (r === 0) return { interest: 0, months: Math.ceil(rv / m) };
  if (m <= rv * r) return null;
  const months = Math.ceil(-Math.log(1 - (rv * r) / m) / Math.log(1 + r));
  return { interest: Math.round(m * months - rv), months };
}
function completionDate(months) {
  if (!months) return null;
  const d = new Date();
  d.setMonth(d.getMonth() + months);
  return { y: d.getFullYear(), m: d.getMonth() + 1 };
}

// ────────── 初期データ ──────────
const INIT_FX = [
  { id:1, name:"家賃", category:"家賃", amount:69000 },
  { id:2, name:"国民健康保険", category:"その他固定費", amount:35400 },
  { id:3, name:"電気", category:"その他固定費", amount:13000 },
  { id:4, name:"docomo携帯", category:"通信費", amount:8073 },
  { id:5, name:"水道", category:"その他固定費", amount:3900 },
  { id:6, name:"ahamo光", category:"通信費", amount:3630 },
  { id:7, name:"amex", category:"サブスク", amount:1100 },
  { id:8, name:"uber", category:"サブスク", amount:498 },
];
const INIT_CF = [
  { id:101, name:"アイフル", rate:18, remaining:99000, monthly:4000 },
  { id:102, name:"アコム", rate:18, remaining:900530, monthly:30000 },
  { id:103, name:"レイク", rate:18, remaining:213052, monthly:12000 },
];
const INIT_BL = [
  { id:201, name:"三井住友カード リボ", rate:15, remaining:609385, monthly:30000 },
  { id:202, name:"セブンカード リボ", rate:15, remaining:100000, monthly:4000 },
  { id:203, name:"みんなの銀行 Loan", rate:4.96, remaining:300000, monthly:1241 },
];
const INIT_LO = [
  { id:1, name:"アプラス（ショッピングローン）", principal:1130000, remaining:1130000, rate:0, monthly:18800 },
];

// ────────── スタイル定数 ──────────
const BG = "#0a0a0c";
const T = "#f5f5f7";
const T2 = "#9a9aa3";
const T3 = "#5a5a63";
const BD = "rgba(255,255,255,0.08)";
const AC = "#818cf8";
const POS = "#34d399";
const NEG = "#f87171";
const CARD = { background:"rgba(255,255,255,0.03)", border:`1px solid ${BD}`, borderRadius:14, padding:16, marginBottom:12 };
const INP_S = { background:"rgba(255,255,255,0.05)", border:`1px solid ${BD}`, borderRadius:10, padding:"11px 13px", color:T, fontSize:15, outline:"none", width:"100%", fontFamily:"inherit", minHeight:44, boxSizing:"border-box" };
const BTN_S = { border:"none", borderRadius:10, padding:"12px 0", cursor:"pointer", fontSize:14, fontWeight:700, background:AC, color:"#0a0a0c", width:"100%", fontFamily:"inherit", minHeight:44 };
const OUTL_S = { background:"transparent", border:`1px solid ${BD}`, borderRadius:10, padding:"8px 14px", cursor:"pointer", fontSize:13, color:T2, fontFamily:"inherit", minHeight:40 };

// ────────── 共通コンポーネント ──────────
function Inp({ value, onChange, type, placeholder, style }) {
  return (
    <input
      type={type || "text"}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      style={{ ...INP_S, ...style }}
      inputMode={type === "number" ? "decimal" : undefined}
    />
  );
}

function Sel({ value, onChange, options, icons }) {
  return (
    <select value={value} onChange={onChange} style={{ ...INP_S, cursor:"pointer" }}>
      {options.map(o => (
        <option key={o} value={o}>{icons ? icons[o] + " " : ""}{o}</option>
      ))}
    </select>
  );
}

function StatBox({ label, value, color }) {
  return (
    <div style={{ background:"rgba(255,255,255,0.03)", border:`1px solid ${BD}`, borderRadius:12, padding:"11px 8px", textAlign:"center" }}>
      <div style={{ fontSize:9, color:T3, marginBottom:4, letterSpacing:"0.5px" }}>{label}</div>
      <div style={{ fontSize:13, fontWeight:700, fontFamily:"monospace", color:color || T }}>{value}</div>
    </div>
  );
}

function BarRow({ label, value, max, color, icon }) {
  return (
    <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:9 }}>
      <div style={{ fontSize:11, color, width:78, display:"flex", alignItems:"center", gap:4, overflow:"hidden", flexShrink:0 }}>
        {icon && <span>{icon}</span>}
        <span style={{ overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{label}</span>
      </div>
      <div style={{ flex:1, height:6, background:"rgba(255,255,255,0.06)", borderRadius:3, overflow:"hidden" }}>
        <div style={{ height:"100%", borderRadius:3, background:color, opacity:0.8, width:Math.min(100, (value / (max || 1)) * 100) + "%" }} />
      </div>
      <div style={{ fontSize:11, color:T2, width:82, textAlign:"right", fontFamily:"monospace", flexShrink:0 }}>{yen(value)}</div>
    </div>
  );
}

function Toast({ data }) {
  if (!data) return null;
  const cl = data.type === "error" ? NEG : data.type === "info" ? T2 : POS;
  return (
    <div style={{ position:"fixed", top:14, left:"50%", transform:"translateX(-50%)", zIndex:999, padding:"9px 18px", borderRadius:20, fontSize:13, fontWeight:600, whiteSpace:"nowrap", pointerEvents:"none", color:cl, background:"rgba(10,10,14,0.92)", border:`1px solid ${cl}44` }}>
      {data.msg}
    </div>
  );
}

function ConfirmDlg({ data, onOk, onCancel }) {
  if (!data) return null;
  return (
    <div onClick={onCancel} style={{ position:"fixed", inset:0, background:"rgba(0,0,0,0.72)", zIndex:200, display:"flex", alignItems:"center", justifyContent:"center", padding:20 }}>
      <div onClick={e => e.stopPropagation()} style={{ background:"#18181f", border:`1px solid ${BD}`, borderRadius:20, padding:24, width:"100%", maxWidth:340 }}>
        <div style={{ fontSize:15, fontWeight:600, marginBottom:8 }}>{data.title}</div>
        <div style={{ fontSize:13, color:T2, marginBottom:20 }}>{data.msg || "この操作は元に戻せません。"}</div>
        <div style={{ display:"flex", gap:10 }}>
          <button onClick={onCancel} style={{ ...OUTL_S, flex:1, minHeight:44, padding:12 }}>キャンセル</button>
          <button onClick={onOk} style={{ ...BTN_S, flex:1, background:NEG }}>削除する</button>
        </div>
      </div>
    </div>
  );
}

function MonthNav({ year, month, onPrev, onNext, onToday, isCurrent }) {
  return (
    <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:18 }}>
      <button onClick={onPrev} style={{ ...OUTL_S, width:44, height:44, padding:0, borderRadius:"50%", fontSize:20, display:"flex", alignItems:"center", justifyContent:"center" }}>‹</button>
      <span style={{ flex:1, textAlign:"center", fontSize:15, fontWeight:600 }}>{year}年 {MLS[month]}</span>
      <button onClick={onNext} style={{ ...OUTL_S, width:44, height:44, padding:0, borderRadius:"50%", fontSize:20, display:"flex", alignItems:"center", justifyContent:"center" }}>›</button>
      {!isCurrent && <button onClick={onToday} style={{ ...OUTL_S, fontSize:11, padding:"6px 12px", minHeight:30 }}>今月</button>}
    </div>
  );
}

function SubTabs({ tabs, value, onChange }) {
  return (
    <div style={{ display:"flex", background:"rgba(255,255,255,0.04)", border:`1px solid ${BD}`, borderRadius:12, padding:4, marginBottom:16 }}>
      {tabs.map(([k, l]) => (
        <button key={k} onClick={() => onChange(k)} style={{ flex:1, border:"none", borderRadius:9, padding:"9px 4px", cursor:"pointer", fontSize:12, fontWeight:500, fontFamily:"inherit", background:value === k ? "rgba(255,255,255,0.1)" : "none", color:value === k ? "#fff" : T3 }}>
          {l}
        </button>
      ))}
    </div>
  );
}

// ────────── 固定費行（編集対応）──────────
function FxRow({ item, onSave, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({});

  function startEdit() {
    setDraft({ name:item.name, cat:item.category, amt:String(item.amount), note:item.note || "" });
    setEditing(true);
  }
  function save() {
    const a = Number(draft.amt);
    if (!draft.name || !a) return;
    onSave({ ...item, name:draft.name, category:draft.cat, amount:a, note:draft.note });
    setEditing(false);
  }

  if (editing) {
    return (
      <div style={{ ...CARD }}>
        <div style={{ display:"flex", flexDirection:"column", gap:10, marginBottom:12 }}>
          <Inp value={draft.name} onChange={e => setDraft(d => ({ ...d, name:e.target.value }))} placeholder="項目名" />
          <Sel value={draft.cat} onChange={e => setDraft(d => ({ ...d, cat:e.target.value }))} options={FCATS} icons={FICO} />
          <Inp type="number" value={draft.amt} onChange={e => setDraft(d => ({ ...d, amt:e.target.value }))} placeholder="月額（円）" />
          <Inp value={draft.note} onChange={e => setDraft(d => ({ ...d, note:e.target.value }))} placeholder="メモ（任意）" />
        </div>
        <div style={{ display:"flex", gap:10 }}>
          <button onClick={save} style={BTN_S}>保存</button>
          <button onClick={() => setEditing(false)} style={{ ...OUTL_S, minHeight:44, padding:"11px 18px" }}>キャンセル</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display:"flex", alignItems:"center", gap:12, ...CARD }}>
      <div style={{ width:40, height:40, borderRadius:"50%", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16, background:"rgba(255,255,255,0.06)", color:T2, flexShrink:0 }}>{FICO[item.category] || "📌"}</div>
      <div style={{ flex:1, minWidth:0 }}>
        <div style={{ fontSize:13, fontWeight:600 }}>{item.name}</div>
        <div style={{ fontSize:11, color:T2 }}>{item.category}</div>
      </div>
      <div style={{ fontFamily:"monospace", fontSize:14, fontWeight:700 }}>{yen(item.amount)}<span style={{ fontSize:10, color:T3 }}>/月</span></div>
      <button onClick={startEdit} style={OUTL_S}>編集</button>
      <button onClick={onDelete} style={OUTL_S}>削除</button>
    </div>
  );
}

// ────────── 【改善①】支出行（編集対応）──────────
function ExpRow({ item, onSave, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({});

  function startEdit() {
    setDraft({ cat:item.category, amt:String(item.amount), date:item.date, note:item.note || "" });
    setEditing(true);
  }
  function save() {
    const a = Number(draft.amt);
    if (!a) return;
    onSave({ ...item, category:draft.cat, amount:a, date:draft.date, note:draft.note });
    setEditing(false);
  }

  if (editing) {
    return (
      <div style={CARD}>
        <div style={{ display:"flex", flexDirection:"column", gap:10, marginBottom:12 }}>
          <Sel value={draft.cat} onChange={e => setDraft(d => ({ ...d, cat:e.target.value }))} options={ECATS} icons={EICO} />
          <Inp type="number" value={draft.amt} onChange={e => setDraft(d => ({ ...d, amt:e.target.value }))} placeholder="金額（円）" />
          <Inp type="date" value={draft.date} onChange={e => setDraft(d => ({ ...d, date:e.target.value }))} />
          <Inp value={draft.note} onChange={e => setDraft(d => ({ ...d, note:e.target.value }))} placeholder="メモ（任意）" />
        </div>
        <div style={{ display:"flex", gap:10 }}>
          <button onClick={save} style={BTN_S}>保存</button>
          <button onClick={() => setEditing(false)} style={{ ...OUTL_S, minHeight:44, padding:"11px 18px" }}>キャンセル</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display:"flex", alignItems:"center", gap:12, ...CARD }}>
      <div style={{ width:40, height:40, borderRadius:"50%", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16, background:"rgba(248,113,113,0.12)", color:NEG, flexShrink:0 }}>{EICO[item.category] || "↓"}</div>
      <div style={{ flex:1, minWidth:0 }}>
        <div style={{ fontSize:13, fontWeight:600 }}>{item.category} <span style={{ fontSize:11, color:T3 }}>{item.note}</span></div>
        <div style={{ fontSize:11, color:T3, marginTop:2 }}>{item.date}</div>
      </div>
      <div style={{ fontFamily:"monospace", fontSize:14, fontWeight:700, color:NEG }}>-{yen(item.amount)}</div>
      <button onClick={startEdit} style={OUTL_S}>編集</button>
      <button onClick={onDelete} style={OUTL_S}>削除</button>
    </div>
  );
}

// ────────── 【改善①】収入行（編集対応）──────────
function IncRow({ item, onSave, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({});

  function startEdit() {
    setDraft({ cat:item.category, amt:String(item.amount), date:item.date, note:item.note || "" });
    setEditing(true);
  }
  function save() {
    const a = Number(draft.amt);
    if (!a) return;
    onSave({ ...item, category:draft.cat, amount:a, date:draft.date, note:draft.note });
    setEditing(false);
  }

  if (editing) {
    return (
      <div style={CARD}>
        <div style={{ display:"flex", flexDirection:"column", gap:10, marginBottom:12 }}>
          <Sel value={draft.cat} onChange={e => setDraft(d => ({ ...d, cat:e.target.value }))} options={ICATS} icons={IICO} />
          <Inp type="number" value={draft.amt} onChange={e => setDraft(d => ({ ...d, amt:e.target.value }))} placeholder="金額（円）" />
          <Inp type="date" value={draft.date} onChange={e => setDraft(d => ({ ...d, date:e.target.value }))} />
          <Inp value={draft.note} onChange={e => setDraft(d => ({ ...d, note:e.target.value }))} placeholder="メモ（任意）" />
        </div>
        <div style={{ display:"flex", gap:10 }}>
          <button onClick={save} style={BTN_S}>保存</button>
          <button onClick={() => setEditing(false)} style={{ ...OUTL_S, minHeight:44, padding:"11px 18px" }}>キャンセル</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display:"flex", alignItems:"center", gap:12, ...CARD }}>
      <div style={{ width:40, height:40, borderRadius:"50%", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16, background:"rgba(52,211,153,0.12)", color:POS, flexShrink:0 }}>{IICO[item.category] || "↑"}</div>
      <div style={{ flex:1, minWidth:0 }}>
        <div style={{ fontSize:13, fontWeight:600 }}>{item.category} <span style={{ fontSize:11, color:T3 }}>{item.note}</span></div>
        <div style={{ fontSize:11, color:T3, marginTop:2 }}>{item.date}</div>
      </div>
      <div style={{ fontFamily:"monospace", fontSize:14, fontWeight:700, color:POS }}>+{yen(item.amount)}</div>
      <button onClick={startEdit} style={OUTL_S}>編集</button>
      <button onClick={onDelete} style={OUTL_S}>削除</button>
    </div>
  );
}

// ────────── ローンカード ──────────
function LoanCard({ loan, onEdit, onDelete, payVal, onPayChange, onPaySubmit }) {
  const ti = calcTotalInt(loan.remaining, loan.rate, loan.monthly);
  const comp = ti ? completionDate(ti.months) : null;
  const paid = Number(loan.remaining) === 0;
  const mi = calcMonthlyInt(loan.remaining, loan.rate);
  const insuf = !paid && loan.monthly > 0 && loan.monthly <= mi && loan.rate > 0;

  return (
    <div style={{ ...CARD, opacity: paid ? 0.75 : 1 }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:12 }}>
        <div style={{ flex:1, minWidth:0 }}>
          {paid && (
            <div style={{ fontSize:10, fontWeight:700, color:POS, background:"rgba(52,211,153,0.1)", borderRadius:5, padding:"2px 8px", display:"inline-block", marginBottom:4 }}>✓ 完済</div>
          )}
          <div style={{ fontSize:15, fontWeight:700 }}>{loan.name}</div>
          <div style={{ fontSize:11, color:T3, marginTop:2 }}>金利 <span style={{ fontFamily:"monospace", color:T, fontWeight:700 }}>{loan.rate}%</span></div>
        </div>
        <div style={{ display:"flex", gap:8, flexShrink:0 }}>
          <button onClick={onEdit} style={OUTL_S}>編集</button>
          <button onClick={onDelete} style={OUTL_S}>削除</button>
        </div>
      </div>

      {insuf && (
        <div style={{ background:"rgba(248,113,113,0.06)", border:"1px solid rgba(248,113,113,0.3)", borderRadius:10, padding:"10px 14px", marginBottom:10, fontSize:12, color:NEG }}>
          ⚠️ 月返済({yen(loan.monthly)})が月利息({yen(mi)})を下回っています
        </div>
      )}

      {!paid && comp && (
        <div style={{ background:"rgba(255,255,255,0.03)", border:`1px solid ${BD}`, borderRadius:12, padding:"12px 14px", marginBottom:10, display:"flex", justifyContent:"space-between", alignItems:"center" }}>
          <div>
            <div style={{ fontSize:10, color:T3, marginBottom:3 }}>完済予定</div>
            <span style={{ fontFamily:"monospace", fontSize:20, fontWeight:700 }}>{comp.y}年{comp.m}月</span>
            <span style={{ fontSize:11, color:T2, marginLeft:8 }}>あと{ti.months}ヶ月</span>
          </div>
          <span style={{ fontSize:26 }}>🏁</span>
        </div>
      )}

      {!paid && ti && ti.interest > 0 && (
        <div style={{ background:"rgba(248,113,113,0.06)", border:"1px solid rgba(248,113,113,0.2)", borderRadius:10, padding:"10px 14px", marginBottom:10, color:NEG, fontSize:12 }}>
          💸 総利息 <span style={{ fontFamily:"monospace", fontSize:16, fontWeight:700 }}>{yen(ti.interest)}</span>
        </div>
      )}

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:12 }}>
        <StatBox label="残債" value={yen(loan.remaining)} color={paid ? POS : T} />
        <StatBox label="月返済額" value={yen(loan.monthly)} />
        <StatBox label="今月の利息" value={yen(mi)} color={NEG} />
        <StatBox label="利息割合" value={loan.remaining > 0 && loan.monthly > 0 ? ((mi / loan.monthly) * 100).toFixed(0) + "%" : "—"} color={NEG} />
      </div>

      {!paid && (
        <div style={{ background:"rgba(255,255,255,0.03)", borderRadius:10, padding:10 }}>
          <div style={{ fontSize:11, color:T3, marginBottom:8 }}>今月の返済額を反映</div>
          <div style={{ display:"flex", gap:8 }}>
            <Inp type="number" value={payVal} onChange={e => onPayChange(e.target.value)} placeholder={String(loan.monthly || "")} style={{ textAlign:"right" }} />
            <button onClick={onPaySubmit} style={{ ...BTN_S, width:"auto", padding:"11px 16px", whiteSpace:"nowrap" }}>反映</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ────────── ローンフォーム ──────────
function LoanForm({ form, setForm, onSave, onCancel, showPrincipal }) {
  return (
    <div style={CARD}>
      <div style={{ display:"flex", flexDirection:"column", gap:10, marginBottom:12 }}>
        <Inp value={form.name} onChange={e => setForm(f => ({ ...f, name:e.target.value }))} placeholder="名称" />
        {showPrincipal && <Inp type="number" value={form.prin || ""} onChange={e => setForm(f => ({ ...f, prin:e.target.value }))} placeholder="借入元本（円）" />}
        <Inp type="number" value={form.rem} onChange={e => setForm(f => ({ ...f, rem:e.target.value }))} placeholder="残債（円）" />
        <Inp type="number" value={form.rate} onChange={e => setForm(f => ({ ...f, rate:e.target.value }))} placeholder="金利（%）" />
        <Inp type="number" value={form.mo} onChange={e => setForm(f => ({ ...f, mo:e.target.value }))} placeholder="月返済額（円）" />
      </div>
      <div style={{ display:"flex", gap:10 }}>
        <button onClick={onSave} style={BTN_S}>保存</button>
        <button onClick={onCancel} style={{ ...OUTL_S, minHeight:44, padding:"11px 18px" }}>キャンセル</button>
      </div>
    </div>
  );
}

// ────────── ローンセクション ──────────
function LoanSection({ arr, setArr, pfx, pays, setPays, showPrincipal, onDelete, showT, payHistory, setPayHistory }) {
  const [showF, setShowF] = useState(false);
  const [edId, setEdId] = useState(null);
  const [form, setForm] = useState({ name:"", prin:"", rem:"", rate:"", mo:"" });
  const [showHist, setShowHist] = useState(false);

  const sumR = arr.reduce((s, l) => s + Number(l.remaining || 0), 0);
  const sumM = arr.reduce((s, l) => s + Number(l.monthly || 0), 0);
  const sumMI = arr.reduce((s, l) => s + calcMonthlyInt(l.remaining, l.rate), 0);
  const sumTI = arr.reduce((s, l) => { const r = calcTotalInt(l.remaining, l.rate, l.monthly); return r ? s + r.interest : s; }, 0);

  // このセクションの返済履歴だけ絞り込む
  const sectionHist = payHistory.filter(h => h.pfx === pfx);

  function save() {
    const rem = Number(form.rem);
    if (!form.name || isNaN(rem)) { showT("名称と残債を入力してください", "error"); return; }
    const d = { name:form.name, rate:Number(form.rate), remaining:rem, monthly:Number(form.mo), principal:Number(form.prin || 0) };
    if (edId) setArr(p => p.map(l => l.id === edId ? { ...d, id:edId } : l));
    else setArr(p => [...p, { ...d, id:Date.now() }]);
    setEdId(null); setShowF(false); setForm({ name:"", prin:"", rem:"", rate:"", mo:"" });
    showT("保存しました");
  }

  function startEdit(loan) {
    setForm({ name:loan.name, prin:String(loan.principal || ""), rem:String(loan.remaining), rate:String(loan.rate), mo:String(loan.monthly) });
    setEdId(loan.id);
    setShowF(true);
  }

  // 【改善②】返済時に履歴を記録する
  function payLoan(id) {
    const k = pfx + id;
    const p = Number(pays[k]);
    if (!p) return;
    const loan = arr.find(l => l.id === id);
    if (!loan) return;
    const remainingBefore = loan.remaining;
    const nr = Math.max(0, loan.remaining - p);
    setArr(prev => prev.map(l => l.id === id ? { ...l, remaining:nr } : l));
    setPays(pp => ({ ...pp, [k]:"" }));

    // 返済履歴に追加する
    const record = {
      id: Date.now(),
      pfx,
      loanId: id,
      loanName: loan.name,
      amount: p,
      date: new Date().toISOString().slice(0, 10),
      remainingBefore,
      remainingAfter: nr,
    };
    setPayHistory(prev => [record, ...prev]);

    showT(nr === 0 ? "🎉 完済！" : "返済を反映しました", nr === 0 ? "success" : "info");
  }

  return (
    <div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:14 }}>
        <StatBox label="総残債" value={yen(sumR)} />
        <StatBox label="月次返済" value={yen(sumM)} />
        <StatBox label="今月の利息" value={yen(sumMI)} color={NEG} />
        <StatBox label="支払総利息" value={yen(sumTI)} color={NEG} />
      </div>

      {arr.map(loan => (
        <LoanCard
          key={loan.id}
          loan={loan}
          onEdit={() => startEdit(loan)}
          onDelete={() => onDelete(loan.id, setArr)}
          payVal={pays[pfx + loan.id] || ""}
          onPayChange={v => setPays(p => ({ ...p, [pfx + loan.id]:v }))}
          onPaySubmit={() => payLoan(loan.id)}
        />
      ))}

      {!showF && (
        <button onClick={() => { setShowF(true); setEdId(null); setForm({ name:"", prin:"", rem:"", rate:"", mo:"" }); }} style={{ ...BTN_S, marginTop:4 }}>
          ＋ 追加
        </button>
      )}
      {showF && (
        <LoanForm
          form={form}
          setForm={setForm}
          onSave={save}
          onCancel={() => { setShowF(false); setEdId(null); }}
          showPrincipal={showPrincipal}
        />
      )}

      {/* 【改善②】返済履歴セクション */}
      {sectionHist.length > 0 && (
        <div style={{ marginTop:16 }}>
          <button
            onClick={() => setShowHist(v => !v)}
            style={{ ...OUTL_S, width:"100%", textAlign:"left", padding:"10px 14px", display:"flex", justifyContent:"space-between" }}
          >
            <span>返済履歴（{sectionHist.length}件）</span>
            <span>{showHist ? "▲" : "▼"}</span>
          </button>
          {showHist && (
            <div style={{ marginTop:8 }}>
              {sectionHist.map(h => (
                <div key={h.id} style={{ ...CARD, marginBottom:8, padding:"12px 14px" }}>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:4 }}>
                    <span style={{ fontSize:13, fontWeight:600 }}>{h.loanName}</span>
                    <span style={{ fontFamily:"monospace", fontSize:14, fontWeight:700, color:POS }}>-{yen(h.amount)}</span>
                  </div>
                  <div style={{ display:"flex", justifyContent:"space-between", fontSize:11, color:T3 }}>
                    <span>{h.date}</span>
                    <span>{yen(h.remainingBefore)} → {yen(h.remainingAfter)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ────────── 【改善③】データエクスポート ──────────
function exportAllData(tx, inc, fx, lo, cf, bl, payHistory) {
  const data = {
    exportedAt: new Date().toISOString(),
    transactions: tx,
    income: inc,
    fixedCosts: fx,
    loans: {
      others: lo,
      consumerFinance: cf,
      bankLoans: bl,
    },
    loanPaymentHistory: payHistory,
  };
  const blob = new Blob([JSON.stringify(data, null, 2)], { type:"application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `finance_backup_${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

// ────────── メインアプリ ──────────
export default function App() {
  const today = new Date();
  const todayStr = today.toISOString().slice(0, 10);

  const [tab, setTab] = useState("dash");
  const [sm, setSm] = useState(today.getMonth());
  const [sy, setSy] = useState(today.getFullYear());

  const [tx, setTx, tx_ok] = usePersist("kk_tx", []);
  const [fx, setFx, fx_ok] = usePersist("kk_fx", INIT_FX);
  const [lo, setLo, lo_ok] = usePersist("kk_lo", INIT_LO);
  const [cf, setCf, cf_ok] = usePersist("kk_cf", INIT_CF);
  const [bl, setBl, bl_ok] = usePersist("kk_bl", INIT_BL);
  const [inc, setInc, inc_ok] = usePersist("kk_inc", []);
  // 【改善②】返済履歴の保存
  const [payHistory, setPayHistory, ph_ok] = usePersist("kk_pay_history", []);

  const [txF, setTxF] = useState({ cat:"食費", amt:"", date:todayStr, note:"" });
  const [fxF, setFxF] = useState({ name:"", cat:"家賃", amt:"", note:"" });
  const [incF, setIncF] = useState({ cat:"給与", amt:"", date:todayStr, note:"" });
  const [showFx, setShowFx] = useState(false);
  const [ltab, setLtab] = useState("cf");
  const [pays, setPays] = useState({});
  const [sq, setSq] = useState("");
  const [fcat, setFcat] = useState("");
  const [toast, setToast] = useState(null);
  const [dlg, setDlg] = useState(null);
  const toastRef = useRef(null);

  const allOk = tx_ok && fx_ok && lo_ok && cf_ok && bl_ok && inc_ok && ph_ok;

  const showT = useCallback((msg, type) => {
    if (toastRef.current) clearTimeout(toastRef.current);
    setToast({ msg, type: type || "success" });
    toastRef.current = setTimeout(() => setToast(null), 2200);
  }, []);

  const ask = useCallback((title, msg, onOk) => setDlg({ title, msg, onOk }), []);

  const handleDelete = useCallback((id, setArr) => {
    ask("削除しますか？", "この操作は元に戻せません。", () => {
      setArr(p => p.filter(l => l.id !== id));
      showT("削除しました", "error");
    });
  }, [ask, showT]);

  const ms = sy + "-" + String(sm + 1).padStart(2, "0");
  const mTx = useMemo(() => tx.filter(t => t.date && t.date.startsWith(ms)), [tx, ms]);
  const mInc = useMemo(() => inc.filter(i => i.date && i.date.startsWith(ms)), [inc, ms]);

  const allL = useMemo(() => [...lo, ...cf, ...bl], [lo, cf, bl]);
  const tVar = useMemo(() => mTx.reduce((s, t) => s + Number(t.amount || 0), 0), [mTx]);
  const tFx = useMemo(() => fx.reduce((s, f) => s + Number(f.amount || 0), 0), [fx]);
  const tRep = allL.reduce((s, l) => s + Number(l.monthly || 0), 0);
  const tInc = mInc.reduce((s, i) => s + Number(i.amount || 0), 0);
  const tBur = tVar + tFx + tRep;
  const net = tInc - tBur;

  const expByCat = useMemo(() => {
    const m = {};
    mTx.forEach(t => { if (t.category) m[t.category] = (m[t.category] || 0) + Number(t.amount || 0); });
    return Object.entries(m).sort((a, b) => b[1] - a[1]);
  }, [mTx]);

  const fTx = useMemo(() => {
    let list = mTx;
    if (fcat) list = list.filter(t => t.category === fcat);
    if (sq.trim()) {
      const q = sq.toLowerCase();
      list = list.filter(t => (t.note || "").toLowerCase().includes(q) || String(t.amount).includes(q));
    }
    return list;
  }, [mTx, fcat, sq]);

  function prevM() { if (sm === 0) { setSm(11); setSy(y => y - 1); } else setSm(m => m - 1); }
  function nextM() { if (sm === 11) { setSm(0); setSy(y => y + 1); } else setSm(m => m + 1); }
  function goToday() { setSm(today.getMonth()); setSy(today.getFullYear()); }
  const isCur = sm === today.getMonth() && sy === today.getFullYear();

  function addTx() {
    const a = Number(txF.amt);
    if (!a || a <= 0) { showT("金額を入力してください", "error"); return; }
    setTx(p => [...p, { id:Date.now(), category:txF.cat, amount:a, date:txF.date, note:txF.note }]);
    setTxF(f => ({ ...f, amt:"", note:"" }));
    showT("支出を追加しました");
  }

  function addInc() {
    const a = Number(incF.amt);
    if (!a || a <= 0) { showT("金額を入力してください", "error"); return; }
    setInc(p => [...p, { id:Date.now(), category:incF.cat, amount:a, date:incF.date, note:incF.note }]);
    setIncF(f => ({ ...f, amt:"", note:"" }));
    showT("収入を追加しました");
  }

  function addFx() {
    const a = Number(fxF.amt);
    if (!fxF.name || !a) { showT("項目名と金額を入力してください", "error"); return; }
    setFx(p => [...p, { id:Date.now(), name:fxF.name, category:fxF.cat, amount:a, note:fxF.note }]);
    setFxF({ name:"", cat:"家賃", amt:"", note:"" });
    setShowFx(false);
    showT("固定費を追加しました");
  }

  if (!allOk) {
    return (
      <div style={{ minHeight:"100vh", display:"flex", alignItems:"center", justifyContent:"center", background:BG, flexDirection:"column", gap:12 }}>
        <div style={{ fontSize:36 }}>💰</div>
        <div style={{ color:T2, fontSize:14 }}>読み込み中...</div>
      </div>
    );
  }

  return (
    <div style={{ background:BG, minHeight:"100vh", color:T, fontFamily:'"Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif' }}>
      <Toast data={toast} />
      <ConfirmDlg data={dlg} onOk={() => { dlg?.onOk(); setDlg(null); }} onCancel={() => setDlg(null)} />

      {/* ヘッダー */}
      <div style={{ position:"sticky", top:0, zIndex:50, background:"rgba(6,6,10,0.92)", backdropFilter:"blur(20px)", borderBottom:`1px solid ${BD}`, padding:"0 16px" }}>
        <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"13px 0 11px", maxWidth:520, margin:"0 auto" }}>
          <div>
            <div style={{ fontSize:9, letterSpacing:"2.5px", color:T2, textTransform:"uppercase", marginBottom:3 }}>Family Finance</div>
            <div style={{ fontSize:19, fontWeight:700 }}>家計管理</div>
          </div>
          <div style={{ display:"flex", alignItems:"center", gap:10 }}>
            {/* 【改善③】エクスポートボタン */}
            <button
              onClick={() => { exportAllData(tx, inc, fx, lo, cf, bl, payHistory); showT("エクスポートしました"); }}
              style={{ ...OUTL_S, fontSize:11, padding:"6px 12px", minHeight:34 }}
              title="データをJSONでバックアップ"
            >
              💾 保存
            </button>
            <div style={{ textAlign:"right" }}>
              <div style={{ fontSize:9, color:T3, marginBottom:2 }}>今月の手残り</div>
              <div style={{ fontFamily:"monospace", fontSize:16, fontWeight:700, color:net >= 0 ? POS : NEG }}>{net >= 0 ? "+" : ""}{yen(net)}</div>
            </div>
          </div>
        </div>
      </div>

      {/* コンテンツ */}
      <div style={{ padding:"16px 16px 110px", maxWidth:520, margin:"0 auto" }}>

        {/* ── ダッシュボード ── */}
        {tab === "dash" && (
          <div>
            <MonthNav year={sy} month={sm} onPrev={prevM} onNext={nextM} onToday={goToday} isCurrent={isCur} />

            <div style={CARD}>
              <div style={{ fontSize:10, color:T3, textTransform:"uppercase", letterSpacing:"1.5px", marginBottom:6 }}>今月の収入</div>
              <div style={{ fontFamily:"monospace", fontSize:30, fontWeight:700, marginBottom:10 }}>{yen(tInc)}</div>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                <div style={{ fontSize:12, color:T2 }}>
                  支出合計 <span style={{ fontFamily:"monospace", color:T }}>{yen(tBur)}</span>
                  {tInc > 0 && <span style={{ marginLeft:8, fontSize:11, color:tBur > tInc ? NEG : T2 }}>({Math.round(tBur / tInc * 100)}%)</span>}
                </div>
                <div style={{ fontSize:13, fontWeight:700, color:net >= 0 ? POS : NEG }}>
                  手残り <span style={{ fontFamily:"monospace" }}>{net >= 0 ? "+" : ""}{yen(net)}</span>
                </div>
              </div>
            </div>

            <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:8, marginBottom:12 }}>
              <StatBox label="変動支出" value={yen(tVar)} />
              <StatBox label="固定費" value={yen(tFx)} />
              <StatBox label="返済合計" value={yen(tRep)} />
            </div>

            <div style={CARD}>
              <div style={{ fontSize:10, color:T3, textTransform:"uppercase", letterSpacing:"1.5px", marginBottom:14 }}>月次収支バランス</div>
              <BarRow label="収入" value={tInc} max={Math.max(tInc, tBur) || 1} color={POS} />
              <BarRow label="変動支出" value={tVar} max={Math.max(tInc, tBur) || 1} color={T2} />
              <BarRow label="固定費" value={tFx} max={Math.max(tInc, tBur) || 1} color={T2} />
              <BarRow label="ローン返済" value={tRep} max={Math.max(tInc, tBur) || 1} color={NEG} />
            </div>

            {expByCat.length > 0 && (
              <div style={CARD}>
                <div style={{ fontSize:10, color:T3, textTransform:"uppercase", letterSpacing:"1.5px", marginBottom:14 }}>変動支出 内訳</div>
                {expByCat.map(([cat, amt]) => (
                  <BarRow key={cat} label={cat} value={amt} max={expByCat[0][1] || 1} color={T2} icon={EICO[cat]} />
                ))}
              </div>
            )}

            <div style={CARD}>
              <div style={{ fontSize:10, color:T3, textTransform:"uppercase", letterSpacing:"1.5px", marginBottom:14, display:"flex", justifyContent:"space-between" }}>
                <span>ローン残債一覧</span><span>{allL.length}件</span>
              </div>
              {allL.map(loan => {
                const ti = calcTotalInt(loan.remaining, loan.rate, loan.monthly);
                const comp = ti ? completionDate(ti.months) : null;
                const mi = calcMonthlyInt(loan.remaining, loan.rate);
                return (
                  <div key={loan.id} style={{ paddingBottom:12, marginBottom:12, borderBottom:`1px solid ${BD}` }}>
                    <div style={{ display:"flex", justifyContent:"space-between", marginBottom:5 }}>
                      <span style={{ fontSize:13, fontWeight:600 }}>{loan.name}</span>
                      <span style={{ fontFamily:"monospace", fontSize:14, fontWeight:700 }}>{yen(loan.remaining)}</span>
                    </div>
                    <div style={{ display:"flex", gap:12, fontSize:11, color:T3, flexWrap:"wrap", marginBottom:4 }}>
                      <span>月返済 <span style={{ fontFamily:"monospace", color:T2 }}>{yen(loan.monthly)}</span></span>
                      <span>月利息 <span style={{ fontFamily:"monospace", color:NEG }}>{yen(mi)}</span></span>
                      <span style={{ fontFamily:"monospace" }}>{loan.rate}%</span>
                    </div>
                    {comp && (
                      <div style={{ fontSize:11, color:T3 }}>
                        完済予定 <span style={{ fontFamily:"monospace", color:T, fontWeight:700 }}>{comp.y}年{comp.m}月</span>
                        {ti && <span style={{ marginLeft:8 }}>総利息 <span style={{ fontFamily:"monospace", color:NEG, fontWeight:700 }}>{yen(ti.interest)}</span></span>}
                      </div>
                    )}
                  </div>
                );
              })}
              <div style={{ display:"flex", justifyContent:"space-between" }}>
                <span style={{ fontSize:12, color:T3 }}>全ローン 支払総利息</span>
                <span style={{ fontFamily:"monospace", fontSize:14, fontWeight:700, color:NEG }}>
                  {yen(allL.reduce((s, l) => { const r = calcTotalInt(l.remaining, l.rate, l.monthly); return r ? s + r.interest : s; }, 0))}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* ── 収入 ── */}
        {tab === "inc" && (
          <div>
            <div style={CARD}>
              <div style={{ fontSize:10, color:T3, textTransform:"uppercase", letterSpacing:"1.5px", marginBottom:14 }}>収入を入力</div>
              <div style={{ display:"flex", flexDirection:"column", gap:10, marginBottom:12 }}>
                <Sel value={incF.cat} onChange={e => setIncF(f => ({ ...f, cat:e.target.value }))} options={ICATS} icons={IICO} />
                <Inp type="number" value={incF.amt} onChange={e => setIncF(f => ({ ...f, amt:e.target.value }))} placeholder="金額（円）" />
                <Inp type="date" value={incF.date} onChange={e => setIncF(f => ({ ...f, date:e.target.value }))} />
                <Inp value={incF.note} onChange={e => setIncF(f => ({ ...f, note:e.target.value }))} placeholder="メモ（任意）" />
              </div>
              <button onClick={addInc} style={BTN_S}>追加</button>
            </div>
            <MonthNav year={sy} month={sm} onPrev={prevM} onNext={nextM} onToday={goToday} isCurrent={isCur} />
            {mInc.length === 0
              ? <div style={{ textAlign:"center", padding:"44px 0", color:T3 }}><div style={{ fontSize:36, marginBottom:10 }}>💰</div>この月の収入データがありません</div>
              : [...mInc].sort((a, b) => b.date.localeCompare(a.date)).map(i => (
                /* 【改善①】IncRowコンポーネントで編集対応 */
                <IncRow
                  key={i.id}
                  item={i}
                  onSave={updated => { setInc(p => p.map(x => x.id === updated.id ? updated : x)); showT("更新しました"); }}
                  onDelete={() => ask("収入を削除しますか？", "", () => { setInc(p => p.filter(x => x.id !== i.id)); showT("削除しました", "error"); })}
                />
              ))
            }
          </div>
        )}

        {/* ── 固定費 ── */}
        {tab === "fix" && (
          <div>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:18 }}>
              <div>
                <div style={{ fontSize:10, color:T3, marginBottom:4 }}>毎月の固定費合計</div>
                <div style={{ fontFamily:"monospace", fontSize:26, fontWeight:700 }}>{yen(tFx)}</div>
              </div>
              <div style={{ fontSize:12, color:T3 }}>{fx.length}項目</div>
            </div>
            {fx.map(item => (
              <FxRow key={item.id} item={item}
                onSave={updated => { setFx(p => p.map(f => f.id === updated.id ? updated : f)); showT("更新しました"); }}
                onDelete={() => ask("固定費を削除しますか？", "", () => { setFx(p => p.filter(f => f.id !== item.id)); showT("削除しました", "error"); })}
              />
            ))}
            {showFx ? (
              <div style={CARD}>
                <div style={{ display:"flex", flexDirection:"column", gap:10, marginBottom:12 }}>
                  <Inp value={fxF.name} onChange={e => setFxF(f => ({ ...f, name:e.target.value }))} placeholder="項目名（例: Netflix）" />
                  <Sel value={fxF.cat} onChange={e => setFxF(f => ({ ...f, cat:e.target.value }))} options={FCATS} icons={FICO} />
                  <Inp type="number" value={fxF.amt} onChange={e => setFxF(f => ({ ...f, amt:e.target.value }))} placeholder="月額（円）" />
                </div>
                <div style={{ display:"flex", gap:10 }}>
                  <button onClick={addFx} style={BTN_S}>追加</button>
                  <button onClick={() => setShowFx(false)} style={{ ...OUTL_S, minHeight:44, padding:"11px 18px" }}>キャンセル</button>
                </div>
              </div>
            ) : (
              <button onClick={() => setShowFx(true)} style={{ ...BTN_S, marginTop:8 }}>＋ 固定費を追加</button>
            )}
          </div>
        )}

        {/* ── 支出 ── */}
        {tab === "exp" && (
          <div>
            <div style={CARD}>
              <div style={{ fontSize:10, color:T3, textTransform:"uppercase", letterSpacing:"1.5px", marginBottom:14 }}>変動支出を入力</div>
              <div style={{ display:"flex", flexDirection:"column", gap:10, marginBottom:12 }}>
                <Sel value={txF.cat} onChange={e => setTxF(f => ({ ...f, cat:e.target.value }))} options={ECATS} icons={EICO} />
                <Inp type="number" value={txF.amt} onChange={e => setTxF(f => ({ ...f, amt:e.target.value }))} placeholder="金額（円）" />
                <Inp type="date" value={txF.date} onChange={e => setTxF(f => ({ ...f, date:e.target.value }))} />
                <Inp value={txF.note} onChange={e => setTxF(f => ({ ...f, note:e.target.value }))} placeholder="メモ（任意）" />
              </div>
              <button onClick={addTx} style={BTN_S}>追加</button>
            </div>

            <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:14 }}>
              <button onClick={prevM} style={{ ...OUTL_S, width:44, height:44, padding:0, borderRadius:"50%", fontSize:20, display:"flex", alignItems:"center", justifyContent:"center" }}>‹</button>
              <span style={{ flex:1, textAlign:"center", fontSize:14, fontWeight:600 }}>{sy}年 {MLS[sm]}</span>
              <button onClick={nextM} style={{ ...OUTL_S, width:44, height:44, padding:0, borderRadius:"50%", fontSize:20, display:"flex", alignItems:"center", justifyContent:"center" }}>›</button>
              {!isCur && <button onClick={goToday} style={{ ...OUTL_S, fontSize:11, padding:"6px 12px" }}>今月</button>}
              <span style={{ fontFamily:"monospace", fontSize:14, fontWeight:700 }}>{yen(tVar)}</span>
            </div>

            {mTx.length > 0 && (
              <div style={{ marginBottom:12 }}>
                <Inp value={sq} onChange={e => setSq(e.target.value)} placeholder="🔍 検索..." style={{ marginBottom:8 }} />
                <div style={{ display:"flex", flexWrap:"wrap", gap:6 }}>
                  {["", ...ECATS.filter(c => mTx.some(t => t.category === c))].map(c => (
                    <button key={c} onClick={() => setFcat(fcat === c && c ? "" : c)}
                      style={{ ...OUTL_S, borderRadius:20, padding:"6px 12px", fontSize:12, ...(fcat === c ? { background:T, borderColor:T, color:BG, fontWeight:700 } : {}) }}>
                      {c ? EICO[c] + " " + c : "すべて"}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {mTx.length === 0
              ? <div style={{ textAlign:"center", padding:"44px 0", color:T3 }}><div style={{ fontSize:36, marginBottom:10 }}>💸</div>この月の支出はありません</div>
              : fTx.length === 0
                ? <div style={{ textAlign:"center", padding:"44px 0", color:T3 }}>🔍 該当なし</div>
                : [...fTx].sort((a, b) => b.date.localeCompare(a.date)).map(t => (
                  /* 【改善①】ExpRowコンポーネントで編集対応 */
                  <ExpRow
                    key={t.id}
                    item={t}
                    onSave={updated => { setTx(p => p.map(x => x.id === updated.id ? updated : x)); showT("更新しました"); }}
                    onDelete={() => ask("支出を削除しますか？", "", () => { setTx(p => p.filter(x => x.id !== t.id)); showT("削除しました", "error"); })}
                  />
                ))
            }
          </div>
        )}

        {/* ── ローン ── */}
        {tab === "loan" && (
          <div>
            <div style={CARD}>
              <div style={{ fontSize:10, color:T3, textTransform:"uppercase", letterSpacing:"1.5px", marginBottom:12, display:"flex", justifyContent:"space-between" }}>
                <span>全ローン合計</span><span>{allL.length}件</span>
              </div>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"baseline", marginBottom:10 }}>
                <span style={{ fontSize:10, color:T3 }}>総残債</span>
                <span style={{ fontFamily:"monospace", fontSize:24, fontWeight:700 }}>{yen(allL.reduce((s, l) => s + Number(l.remaining || 0), 0))}</span>
              </div>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:8 }}>
                <StatBox label="月次返済" value={yen(tRep)} />
                <StatBox label="今月の利息" value={yen(allL.reduce((s, l) => s + calcMonthlyInt(l.remaining, l.rate), 0))} color={NEG} />
                <StatBox label="支払総利息" value={yen(allL.reduce((s, l) => { const r = calcTotalInt(l.remaining, l.rate, l.monthly); return r ? s + r.interest : s; }, 0))} color={NEG} />
              </div>
            </div>

            <SubTabs tabs={[["cf","🏧 消費者金融"],["bl","🏛 銀行/リボ"],["lo","🏦 その他"]]} value={ltab} onChange={setLtab} />

            {ltab === "cf" && <LoanSection arr={cf} setArr={setCf} pfx="cf" pays={pays} setPays={setPays} showPrincipal={false} onDelete={handleDelete} showT={showT} payHistory={payHistory} setPayHistory={setPayHistory} />}
            {ltab === "bl" && <LoanSection arr={bl} setArr={setBl} pfx="bl" pays={pays} setPays={setPays} showPrincipal={false} onDelete={handleDelete} showT={showT} payHistory={payHistory} setPayHistory={setPayHistory} />}
            {ltab === "lo" && <LoanSection arr={lo} setArr={setLo} pfx="lo" pays={pays} setPays={setPays} showPrincipal={true} onDelete={handleDelete} showT={showT} payHistory={payHistory} setPayHistory={setPayHistory} />}
          </div>
        )}
      </div>

      {/* ボトムナビ */}
      <nav style={{ position:"fixed", bottom:0, left:0, right:0, background:"rgba(8,8,14,0.94)", backdropFilter:"blur(20px)", borderTop:`1px solid ${BD}`, display:"flex", zIndex:100 }}>
        {[["dash","📊","概要"],["inc","💰","収入"],["fix","📌","固定費"],["exp","💸","支出"],["loan","🏦","ローン"]].map(([key, icon, label]) => (
          <button key={key} onClick={() => setTab(key)} style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", padding:"11px 4px 12px", cursor:"pointer", border:"none", background:"none", color:tab === key ? T : T3, fontSize:10, gap:4, fontFamily:"inherit", minHeight:58 }}>
            <span style={{ fontSize:22, lineHeight:1 }}>{icon}</span>
            <span>{label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
