# 家計管理アプリ ユーザビリティ改善 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** App.jsx に8つのUI改善を加えて、家計管理アプリのユーザビリティを向上させる

**Architecture:** 変更はすべて `finance_web/src/App.jsx` 1ファイル内で完結。データ構造・localStorage キー・外部依存は変更しない。UIと入力処理のみを改善する。

**Tech Stack:** React 18, Vite, localStorage（テストなし・ブラウザで手動確認）

---

## ファイル構成

| 変更 | ファイル |
|------|---------|
| 修正 | `finance_web/src/App.jsx` |
| 参照 | `finance_web/docs/superpowers/specs/2026-05-07-usability-improvements-design.md` |

開発サーバー起動コマンド（作業前に起動しておく）:
```bash
cd /home/kenta_kamijyo/finance_web && npm run dev
```

---

## Task 1: parseAmount ヘルパー追加 + INIT_FX を空配列に

**Files:**
- Modify: `finance_web/src/App.jsx`

- [ ] **Step 1: dev サーバーを起動**

```bash
cd /home/kenta_kamijyo/finance_web && npm run dev
```

ブラウザで `http://localhost:5173` を開く（ポートは異なる場合あり）。

- [ ] **Step 2: INIT_FX を空配列に変更**

`App.jsx` の以下の行を探す（166行目付近）:

```js
const INIT_FX = [
  {id:1,name:"家賃",category:"家賃",amount:80000},
  {id:2,name:"電気",category:"その他固定費",amount:8000},
  {id:3,name:"水道",category:"その他固定費",amount:3000},
  {id:4,name:"スマホ",category:"通信費",amount:5000},
  {id:5,name:"光回線",category:"通信費",amount:4000},
];
```

以下に置き換える:

```js
const INIT_FX = [];
```

- [ ] **Step 3: parseAmount ヘルパー関数を追加**

`yen` 関数の定義行（142行目付近）の直前に追加:

```js
// カンマ区切りで入力された金額（例: "1,000,000"）を数値に変換するヘルパー
function parseAmount(v) {
  return Number(String(v).replace(/,/g, ""));
}
```

- [ ] **Step 4: addTx の Number() を parseAmount() に置き換え**

`addTx` 関数（447行目付近）の:

```js
function addTx(){const a=Number(txF.amt);if(!a||a<=0){
```

を以下に置き換える:

```js
function addTx(){const a=parseAmount(txF.amt);if(!a||a<=0){
```

- [ ] **Step 5: addInc の Number() を parseAmount() に置き換え**

`addInc` 関数（448行目付近）の:

```js
function addInc(){const a=Number(incF.amt);if(!a||a<=0){
```

を以下に置き換える:

```js
function addInc(){const a=parseAmount(incF.amt);if(!a||a<=0){
```

- [ ] **Step 6: addFx の Number() を parseAmount() に置き換え**

`addFx` 関数（449行目付近）の:

```js
function addFx(){const a=Number(fxF.amt);if(!fxF.name||!a){
```

を以下に置き換える:

```js
function addFx(){const a=parseAmount(fxF.amt);if(!fxF.name||!a){
```

- [ ] **Step 7: LoanSection.save の Number() を parseAmount() に置き換え**

`LoanSection` 関数内の `save` 関数（328行目付近）:

```js
function save(){const rem=Number(f.rem);if(!f.name||isNaN(rem)){showT("名称と残債を入力","error");return;}const d={name:f.name,rate:Number(f.rate),remaining:rem,monthly:Number(f.mo),principal:Number(f.prin||0),
```

を以下に置き換える:

```js
function save(){const rem=parseAmount(f.rem);if(!f.name||isNaN(rem)){showT("名称と残債を入力","error");return;}const d={name:f.name,rate:parseAmount(f.rate),remaining:rem,monthly:parseAmount(f.mo),principal:parseAmount(f.prin||0),
```

- [ ] **Step 8: LoanSection.pay の Number() を parseAmount() に置き換え**

`LoanSection` 内の `pay` 関数（329行目付近）:

```js
function pay(id){const k=pfx+id;const loan=arr.find(l=>l.id===id);if(!loan)return;const p=Number(pays[k])||loan.monthly;
```

を以下に置き換える:

```js
function pay(id){const k=pfx+id;const loan=arr.find(l=>l.id===id);if(!loan)return;const p=parseAmount(pays[k])||loan.monthly;
```

- [ ] **Step 9: 口座残高保存の Number() を parseAmount() に置き換え**

収入タブ内の口座保存処理（510行目付近）:

```js
const b=Number(accF.balance);
if(!accF.name||isNaN(b)){showT("口座名と残高を入力","error");return;}
```

を以下に置き換える:

```js
const b=parseAmount(accF.balance);
if(!accF.name||isNaN(b)){showT("口座名と残高を入力","error");return;}
```

- [ ] **Step 10: ブラウザで動作確認**

- 固定費タブを開き、デフォルトの固定費が消えていること（空のリスト）を確認
- 支出タブで金額欄に「1,000,000」と入力して「追加」→ ¥1,000,000 として登録されること確認
- ローンタブで残債欄に「500,000」と入力しても正しく保存されること確認

- [ ] **Step 11: コミット**

```bash
cd /home/kenta_kamijyo/finance_web
git add src/App.jsx
git commit -m "feat: カンマ区切り金額入力対応・固定費初期データをリセット"
```

---

## Task 2: 口座残高をダッシュボードに移動

**Files:**
- Modify: `finance_web/src/App.jsx`

- [ ] **Step 1: 収入タブから口座残高カードの JSX を切り取る**

`tab==="inc"` セクション（479行目付近）の先頭にある口座残高カード全体を削除する。

以下のブロックを丸ごと削除（`{/* 口座残高カード */}` から `</div>` まで）:

```jsx
{/* 口座残高カード */}
<div style={CARD}>
  <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
    <div style={{fontSize:10,color:T3,textTransform:"uppercase",letterSpacing:"1.5px"}}>口座残高</div>
    <button onClick={()=>{setAccF({name:"",balance:""});setEditAccId(null);setShowAccF(v=>!v);}} style={{...OS,fontSize:12,padding:"5px 12px",minHeight:32}}>{showAccF?"閉じる":"＋ 追加"}</button>
  </div>
  {accounts.length===0&&!showAccF&&<div style={{textAlign:"center",padding:"18px 0",color:T3,fontSize:13}}>🏦 口座を追加してください</div>}
  {accounts.map(acc=>(
    <div key={acc.id} style={{display:"flex",alignItems:"center",gap:10,padding:"10px 0",borderBottom:`1px solid ${BD}`}}>
      <div style={{flex:1,minWidth:0}}>
        <div style={{fontSize:13,fontWeight:600}}>{acc.name}</div>
        {acc.updatedAt&&<div style={{fontSize:10,color:T3,marginTop:2}}>{acc.updatedAt} 更新</div>}
      </div>
      <div style={{fontFamily:"monospace",fontSize:15,fontWeight:700,color:POS}}>{yen(acc.balance)}</div>
      <button onClick={()=>{setAccF({name:acc.name,balance:String(acc.balance)});setEditAccId(acc.id);setShowAccF(true);}} style={{...OS,fontSize:12,padding:"5px 10px",minHeight:32}}>編集</button>
      <button onClick={()=>ask("口座を削除しますか？","",()=>{setAccounts(p=>p.filter(a=>a.id!==acc.id));showT("削除しました","error");})} style={{...OS,fontSize:12,padding:"5px 10px",minHeight:32}}>削除</button>
    </div>
  ))}
  {accounts.length>0&&<div style={{display:"flex",justifyContent:"space-between",alignItems:"center",paddingTop:10}}>
    <span style={{fontSize:11,color:T3}}>合計残高</span>
    <span style={{fontFamily:"monospace",fontSize:16,fontWeight:700,color:POS}}>{yen(accounts.reduce((s,a)=>s+Number(a.balance||0),0))}</span>
  </div>}
  {showAccF&&<div style={{marginTop:12,paddingTop:12,borderTop:`1px solid ${BD}`}}>
    <div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:10}}>
      <Inp value={accF.name} onChange={e=>setAccF(f=>({...f,name:e.target.value}))} placeholder="口座名（例: 三井住友・楽天銀行）"/>
      <Inp type="number" value={accF.balance} onChange={e=>setAccF(f=>({...f,balance:e.target.value}))} placeholder="現在の残高（円）"/>
    </div>
    <div style={{display:"flex",gap:10}}>
      <button onClick={()=>{
        const b=parseAmount(accF.balance);
        if(!accF.name||isNaN(b)){showT("口座名と残高を入力","error");return;}
        const updated=ts;
        if(editAccId){setAccounts(p=>p.map(a=>a.id===editAccId?{...a,name:accF.name,balance:b,updatedAt:updated}:a));}
        else{setAccounts(p=>[...p,{id:Date.now(),name:accF.name,balance:b,updatedAt:updated}]);}
        setShowAccF(false);setEditAccId(null);setAccF({name:"",balance:""});showT("保存しました");
      }} style={BS}>保存</button>
      <button onClick={()=>{setShowAccF(false);setEditAccId(null);}} style={{...OS,minHeight:44,padding:"11px 18px"}}>キャンセル</button>
    </div>
  </div>}
</div>
```

- [ ] **Step 2: ダッシュボードの既存の口座表示カードを置き換える**

`tab==="dash"` セクション内の以下の表示専用カード（469行目付近）:

```jsx
{accounts.length>0&&<div style={{...CARD,marginBottom:12}}><div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}><div><div style={{fontSize:10,color:T3,marginBottom:3}}>口座残高合計</div><div style={{fontFamily:"monospace",fontSize:22,fontWeight:700,color:POS}}>{yen(accounts.reduce((s,a)=>s+Number(a.balance||0),0))}</div></div><div style={{textAlign:"right"}}>{accounts.map(a=><div key={a.id} style={{fontSize:11,color:T2,marginBottom:2}}>{a.name} <span style={{fontFamily:"monospace",fontWeight:600}}>{yen(a.balance)}</span></div>)}</div></div></div>}
```

を、Step 1 で切り取った完全な口座残高カード（編集・追加機能付き）に置き換える。
ただし空の状態のガイダンス文を改善版に変更する:

```jsx
<div style={CARD}>
  <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
    <div style={{fontSize:10,color:T3,textTransform:"uppercase",letterSpacing:"1.5px"}}>口座残高</div>
    <button onClick={()=>{setAccF({name:"",balance:""});setEditAccId(null);setShowAccF(v=>!v);}} style={{...OS,fontSize:12,padding:"5px 12px",minHeight:32}}>{showAccF?"閉じる":"＋ 追加"}</button>
  </div>
  {accounts.length===0&&!showAccF&&<div style={{textAlign:"center",padding:"18px 0",color:T3,fontSize:13}}>🏦 口座を追加すると残高合計が確認できます</div>}
  {accounts.map(acc=>(
    <div key={acc.id} style={{display:"flex",alignItems:"center",gap:10,padding:"10px 0",borderBottom:`1px solid ${BD}`}}>
      <div style={{flex:1,minWidth:0}}>
        <div style={{fontSize:13,fontWeight:600}}>{acc.name}</div>
        {acc.updatedAt&&<div style={{fontSize:10,color:T3,marginTop:2}}>{acc.updatedAt} 更新</div>}
      </div>
      <div style={{fontFamily:"monospace",fontSize:15,fontWeight:700,color:POS}}>{yen(acc.balance)}</div>
      <button onClick={()=>{setAccF({name:acc.name,balance:String(acc.balance)});setEditAccId(acc.id);setShowAccF(true);}} style={{...OS,fontSize:12,padding:"5px 10px",minHeight:32}}>編集</button>
      <button onClick={()=>ask("口座を削除しますか？","",()=>{setAccounts(p=>p.filter(a=>a.id!==acc.id));showT("削除しました","error");})} style={{...OS,fontSize:12,padding:"5px 10px",minHeight:32}}>削除</button>
    </div>
  ))}
  {accounts.length>0&&<div style={{display:"flex",justifyContent:"space-between",alignItems:"center",paddingTop:10}}>
    <span style={{fontSize:11,color:T3}}>合計残高</span>
    <span style={{fontFamily:"monospace",fontSize:16,fontWeight:700,color:POS}}>{yen(accounts.reduce((s,a)=>s+Number(a.balance||0),0))}</span>
  </div>}
  {showAccF&&<div style={{marginTop:12,paddingTop:12,borderTop:`1px solid ${BD}`}}>
    <div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:10}}>
      <Inp value={accF.name} onChange={e=>setAccF(f=>({...f,name:e.target.value}))} placeholder="口座名（例: 三井住友・楽天銀行）"/>
      <Inp type="number" value={accF.balance} onChange={e=>setAccF(f=>({...f,balance:e.target.value}))} placeholder="現在の残高（円）"/>
    </div>
    <div style={{display:"flex",gap:10}}>
      <button onClick={()=>{
        const b=parseAmount(accF.balance);
        if(!accF.name||isNaN(b)){showT("口座名と残高を入力","error");return;}
        const updated=ts;
        if(editAccId){setAccounts(p=>p.map(a=>a.id===editAccId?{...a,name:accF.name,balance:b,updatedAt:updated}:a));}
        else{setAccounts(p=>[...p,{id:Date.now(),name:accF.name,balance:b,updatedAt:updated}]);}
        setShowAccF(false);setEditAccId(null);setAccF({name:"",balance:""});showT("保存しました");
      }} style={BS}>保存</button>
      <button onClick={()=>{setShowAccF(false);setEditAccId(null);}} style={{...OS,minHeight:44,padding:"11px 18px"}}>キャンセル</button>
    </div>
  </div>}
</div>
```

- [ ] **Step 3: ブラウザで動作確認**

- 概要タブを開き、口座残高カードが表示されること（「＋ 追加」ボタン付き）を確認
- 口座を追加・編集・削除できること確認
- 収入タブを開き、口座残高カードが表示されないこと確認

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web
git add src/App.jsx
git commit -m "feat: 口座残高カードを収入タブからダッシュボードへ移動"
```

---

## Task 3: 支出フォームを折りたたみ式に変更

**Files:**
- Modify: `finance_web/src/App.jsx`

- [ ] **Step 1: showTxForm state を追加**

App コンポーネント内の state 宣言部分（369行目付近）に追加:

現在の:
```js
const [showFx,setShowFx]=useState(false),[ltab,setLtab]=useState("cf");
```

を以下に変更:

```js
const [showFx,setShowFx]=useState(false),[showTxForm,setShowTxForm]=useState(false),[ltab,setLtab]=useState("cf");
```

- [ ] **Step 2: 支出タブのフォームを折りたたみ式に変更**

`tab==="exp"` セクション（530行目付近）の最初の `<div style={CARD}>` から `<button onClick={addTx} style={BS}>追加</button></div>` までの入力フォームブロックを以下に置き換える。

削除対象（現状のフォーム）:

```jsx
<div style={CARD}><div style={{fontSize:10,color:T3,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:14}}>変動支出を入力</div><div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:12}}><Sel value={txF.cat} onChange={e=>setTxF(f=>({...f,cat:e.target.value}))} options={ECATS} icons={EICO}/><Inp type="number" value={txF.amt} onChange={e=>setTxF(f=>({...f,amt:e.target.value}))} placeholder="金額（円）"/><Inp type="date" value={txF.date} onChange={e=>setTxF(f=>({...f,date:e.target.value}))}/><Inp value={txF.note} onChange={e=>setTxF(f=>({...f,note:e.target.value}))} placeholder="メモ（任意）"/></div><button onClick={addTx} style={BS}>追加</button></div>
```

置き換え後:

```jsx
{!showTxForm
  ? <button onClick={()=>setShowTxForm(true)} style={{...BS,marginBottom:12}}>＋ 支出を追加</button>
  : <div style={CARD}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:14}}>
        <div style={{fontSize:10,color:T3,textTransform:"uppercase",letterSpacing:"1.5px"}}>変動支出を入力</div>
        <button onClick={()=>setShowTxForm(false)} style={{...OS,fontSize:12,padding:"4px 10px",minHeight:30}}>✕ 閉じる</button>
      </div>
      <div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:12}}>
        <Sel value={txF.cat} onChange={e=>setTxF(f=>({...f,cat:e.target.value}))} options={ECATS} icons={EICO}/>
        <Inp type="number" value={txF.amt} onChange={e=>setTxF(f=>({...f,amt:e.target.value}))} placeholder="金額（円）"/>
        <Inp type="date" value={txF.date} onChange={e=>setTxF(f=>({...f,date:e.target.value}))}/>
        <Inp value={txF.note} onChange={e=>setTxF(f=>({...f,note:e.target.value}))} placeholder="メモ（任意）"/>
      </div>
      <button onClick={addTx} style={BS}>追加</button>
    </div>
}
```

- [ ] **Step 3: ブラウザで動作確認**

- 支出タブを開いたとき「＋ 支出を追加」ボタンだけが表示されること確認
- ボタンタップでフォームが展開されること確認
- 支出を追加後、フォームが開いたままであること確認
- 「✕ 閉じる」ボタンでフォームが閉じること確認
- 閉じた後、支出リストがすぐ見えること確認

- [ ] **Step 4: コミット**

```bash
cd /home/kenta_kamijyo/finance_web
git add src/App.jsx
git commit -m "feat: 支出入力フォームを折りたたみ式に変更"
```

---

## Task 4: 収入タブに検索・フィルタ＋CSV出力を追加

**Files:**
- Modify: `finance_web/src/App.jsx`

- [ ] **Step 1: 収入用の検索 state を追加**

App コンポーネントの state 宣言部（370行目付近）:

```js
const [pays,setPays]=useState({}),[sq,setSq]=useState(""),[fcat,setFcat]=useState("");
```

を以下に変更:

```js
const [pays,setPays]=useState({}),[sq,setSq]=useState(""),[fcat,setFcat]=useState(""),[incSq,setIncSq]=useState(""),[incFcat,setIncFcat]=useState("");
```

- [ ] **Step 2: fInc（フィルタ済み収入リスト）を useMemo で追加**

既存の `fTx` の `useMemo` 定義（389行目付近）の直後に追加:

```js
const fInc=useMemo(()=>{let l=mInc;if(incFcat)l=l.filter(i=>i.category===incFcat);if(incSq.trim()){const q=incSq.toLowerCase();l=l.filter(i=>(i.note||"").toLowerCase().includes(q)||String(i.amount).includes(q));}return l;},[mInc,incFcat,incSq]);
```

- [ ] **Step 3: exportIncCSV 関数を追加**

既存の `exportCSV` 関数（437行目付近）の直後に追加:

```js
function exportIncCSV(){
  const rows=[["日付","カテゴリ","金額","メモ"],...[...mInc].sort((a,b)=>b.date.localeCompare(a.date)).map(i=>[i.date,i.category,i.amount,i.note||""])];
  const csv=rows.map(r=>r.map(v=>`"${String(v).replace(/"/g,'""')}"`).join(",")).join("\n");
  const blob=new Blob(["﻿"+csv],{type:"text/csv;charset=utf-8;"});
  const url=URL.createObjectURL(blob);
  const a=document.createElement("a");
  a.href=url;a.download=`収入_${sy}年${MLS[sm]}.csv`;a.click();
  URL.revokeObjectURL(url);
  showT("CSVを保存しました");
}
```

- [ ] **Step 4: 収入タブのリスト表示部分を更新**

`tab==="inc"` セクションの `<MN/>` の直後にある収入リスト部分:

```jsx
{mInc.length===0?<div style={{textAlign:"center",padding:"44px 0",color:T3}}><div style={{fontSize:36,marginBottom:10}}>💰</div>この月の収入データがありません</div>
:[...mInc].sort((a,b)=>b.date.localeCompare(a.date)).map(i=><TxRow key={i.id} item={i} cats={ICATS} ico={IICO} isInc onSave={u=>{setInc(p=>p.map(x=>x.id===u.id?u:x));showT("更新しました");}} onDelete={()=>ask("収入を削除しますか？","",()=>{setInc(p=>p.filter(x=>x.id!==i.id));showT("削除しました","error");})}/>)}
```

を以下に置き換える:

```jsx
{mInc.length>0&&<button onClick={exportIncCSV} style={{...OS,width:"100%",marginBottom:10,fontSize:12}}>📥 CSV出力</button>}
{mInc.length>0&&<div style={{marginBottom:12}}><Inp value={incSq} onChange={e=>setIncSq(e.target.value)} placeholder="🔍 検索..." style={{marginBottom:8}}/><div style={{display:"flex",flexWrap:"wrap",gap:6}}>{["",...ICATS.filter(c=>mInc.some(i=>i.category===c))].map(c=><button key={c} onClick={()=>setIncFcat(incFcat===c&&c?"":c)} style={{...OS,borderRadius:20,padding:"6px 12px",fontSize:12,...(incFcat===c?{background:T,borderColor:T,color:BG,fontWeight:700}:{})}}>{c?IICO[c]+" "+c:"すべて"}</button>)}</div></div>}
{mInc.length===0
  ?<div style={{textAlign:"center",padding:"44px 0",color:T3}}><div style={{fontSize:36,marginBottom:10}}>💰</div><div>この月の収入データがありません</div><div style={{fontSize:12,marginTop:8}}>上のフォームから収入を入力してみましょう</div></div>
  :fInc.length===0?<div style={{textAlign:"center",padding:"44px 0",color:T3}}>🔍 該当なし</div>
  :[...fInc].sort((a,b)=>b.date.localeCompare(a.date)).map(i=><TxRow key={i.id} item={i} cats={ICATS} ico={IICO} isInc onSave={u=>{setInc(p=>p.map(x=>x.id===u.id?u:x));showT("更新しました");}} onDelete={()=>ask("収入を削除しますか？","",()=>{setInc(p=>p.filter(x=>x.id!==i.id));showT("削除しました","error");})}/>)}
```

- [ ] **Step 5: ブラウザで動作確認**

- 収入を複数カテゴリで入力しておく（給与・副業など）
- カテゴリフィルタボタンをタップして絞り込めること確認
- テキスト検索で金額やメモで絞り込めること確認
- 「📥 CSV出力」ボタンが表示されCSVがダウンロードできること確認
- データがない月は「上のフォームから収入を入力してみましょう」が表示されること確認

- [ ] **Step 6: コミット**

```bash
cd /home/kenta_kamijyo/finance_web
git add src/App.jsx
git commit -m "feat: 収入タブに検索・フィルタ・CSV出力を追加"
```

---

## Task 5: ローンラベル補足 + 空の状態ガイダンス追加

**Files:**
- Modify: `finance_web/src/App.jsx`

- [ ] **Step 1: ローンタブのサブタブラベルを更新**

`tab==="loan"` セクション内の ST コンポーネント呼び出し（541行目付近）:

```jsx
<ST tabs={[["cf","🏧 消費者金融"],["bl","🏛 銀行/リボ"],["lo","🏦 その他"]]} v={ltab} on={setLtab}/>
```

を以下に変更:

```jsx
<ST tabs={[["cf","🏧 消費者金融"],["bl","🏛 銀行・リボ払い"],["lo","🏦 住宅・車ローン"]]} v={ltab} on={setLtab}/>
```

- [ ] **Step 2: 固定費タブの空の状態にガイダンスを追加**

`tab==="fix"` セクション（525行目付近）の `{fx.map(...)}` の直前に追加:

```jsx
{fx.length===0&&!showFx&&<div style={{textAlign:"center",padding:"32px 0",color:T3}}><div style={{fontSize:36,marginBottom:10}}>📌</div><div>固定費が登録されていません</div><div style={{fontSize:12,marginTop:8}}>家賃・サブスクなど毎月かかる費用を登録しましょう</div></div>}
```

- [ ] **Step 3: 支出タブの空の状態にガイダンスを追加**

`tab==="exp"` セクションの空表示部分（現状）:

```jsx
{mTx.length===0?<div style={{textAlign:"center",padding:"44px 0",color:T3}}><div style={{fontSize:36,marginBottom:10}}>💸</div>この月の支出はありません</div>
```

を以下に変更:

```jsx
{mTx.length===0?<div style={{textAlign:"center",padding:"44px 0",color:T3}}><div style={{fontSize:36,marginBottom:10}}>💸</div><div>この月の支出はありません</div><div style={{fontSize:12,marginTop:8}}>「＋ 支出を追加」から記録してみましょう</div></div>
```

- [ ] **Step 4: ブラウザで動作確認**

- ローンタブのサブタブラベルが「銀行・リボ払い」「住宅・車ローン」に変わっていること確認
- 固定費タブを開き（INIT_FX を空にしたので）ガイダンスが表示されること確認
- 支出が0件の月に移動して、ガイダンス文が表示されること確認

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo/finance_web
git add src/App.jsx
git commit -m "feat: ローンラベル補足・各タブの空状態にガイダンス追加"
```

---

## 最終確認

- [ ] **全タブを一通り操作して、既存機能が壊れていないこと確認**
  - パスワードログイン
  - ダッシュボードの収支計算
  - 固定費の追加・編集・削除・並び替え
  - ローンの追加・返済反映・自動モード
- [ ] **Vercel へ push してデプロイ確認**

```bash
cd /home/kenta_kamijyo/finance_web
git push
```

Vercel が自動デプロイするのを待ち、`https://financeweb-nine.vercel.app` で動作確認。
