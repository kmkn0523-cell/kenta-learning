// ────────── アプリ本体 ──────────
// 全タブの状態管理・画面切替・CSV出力・バックアップ機能をまとめた中心ファイル
// UI部品・ユーティリティ・フックはすべて外部ファイルから読み込む

import { useState, useEffect, useMemo, useRef, lazy, Suspense } from "react";
import { usePersist } from "./hooks/usePersist";
import { useMonthlyData } from "./hooks/useMonthlyData";
import { useAutoPayment } from "./hooks/useAutoPayment";
import { useDataExport } from "./hooks/useDataExport";
import { useToast } from "./hooks/useToast";
import { useBackup } from "./hooks/useBackup";
import { newId } from "./utils/crypto";
import { parseYenAmount, formatYen, MONTH_LABELS, EXPENSE_CATEGORIES, FIXED_EXPENSE_CATEGORIES, INCOME_CATEGORIES, EXPENSE_CATEGORY_ICONS, FIXED_EXPENSE_CATEGORY_ICONS, INCOME_CATEGORY_ICONS } from "./utils/format";
import { calculateMonthlyInterest, calculateTotalInterest, calculateCompletionDate, BRANDS_CF, BRANDS_BL } from "./utils/loanCalc";
import { COLOR_BACKGROUND, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_HINT, COLOR_BORDER, COLOR_BORDER_GLOW, COLOR_ACCENT, COLOR_POSITIVE, COLOR_NEGATIVE, STYLE_CARD, STYLE_BUTTON_PRIMARY, STYLE_BUTTON_OUTLINE } from "./utils/styles";
import { migrateTransactions, migrateIncomes, migrateFixedExpenses, migrateLoans } from "./utils/dataMigration";
import { Transfer, CategoryConfig, SavingGoal } from "./types";
import { makeDefaultCategoryConfig } from "./utils/defaultCategories";
import PasswordGate from "./components/PasswordGate";
import { Input, Select, StatLabel, ProgressBar, Toast, ConfirmDialog } from "./components/ui";
import FxRow from "./components/FxRow";
import TxRow from "./components/TxRow";
import LoanSection from "./components/LoanSection";
import MonthlyChart from "./components/MonthlyChart";
import BudgetSection from "./components/BudgetSection";
import MonthNav from "./components/MonthNav";
import StatBlock from "./components/StatBlock";
// DashboardView は初期表示タブなので即時ロード
import DashboardView from "./views/DashboardView";
import TutorialModal from "./components/TutorialModal";
// それ以外のビューは初回ロードを軽くするためタブを開いた時に動的ロード（コード分割）
const IncomeView = lazy(() => import("./views/IncomeView"));
const FixedExpenseView = lazy(() => import("./views/FixedExpenseView"));
const ExpenseView = lazy(() => import("./views/ExpenseView"));
const LoanView = lazy(() => import("./views/LoanView"));
const SettingsView = lazy(() => import("./views/SettingsView"));

// 初期値：何もデータが無い時の空配列（usePersist の第2引数に渡す）
const INIT_FX = [];
const INIT_CF = [];
const INIT_BL = [];
const INIT_LO = [];

function AppInner(){
  const today=new Date(),ts=today.toISOString().slice(0,10);
  const [tab,setTab]=useState("dash"),[selectedMonth,setSelectedMonth]=useState(today.getMonth()),[selectedYear,setSelectedYear]=useState(today.getFullYear());
  const [transactions,setTransactions,txReady]=usePersist("kk_tx",[]);
  const [fixedExpenses,setFixedExpenses,fxReady]=usePersist("kk_fx",INIT_FX);
  const [loans,setLoans,loansReady]=usePersist("kk_lo",INIT_LO);
  const [cashFlow,setCashFlow,cashFlowReady]=usePersist("kk_cf",INIT_CF);
  const [balance,setBalance,balanceReady]=usePersist("kk_bl",INIT_BL);
  const [incomes,setIncomes,incomesReady]=usePersist("kk_inc",[]);
  const [accounts,setAccounts,accountsReady]=usePersist("kk_accounts",[]);
  const [budget,setBudget,budgetReady]=usePersist("kk_budget",{});
  const [tpls,setTpls,tplsReady]=usePersist("kk_tpls",[]);
  const [transfers,setTransfers,transfersReady]=usePersist<Transfer[]>("kk_transfers",[]);
  // カテゴリ設定（ユーザーが追加・編集・削除したカテゴリを永続化）
  const [categoryConfig,setCategoryConfig,categoryConfigReady]=usePersist<CategoryConfig>("kk_categories",makeDefaultCategoryConfig());
  // 貯金目標（単一目標。null＝未設定）
  const [savingGoal,setSavingGoal,savingGoalReady]=usePersist<SavingGoal | null>("kk_savingGoal",null);
  const [txF,setTxF]=useState({cat:"食費",amt:"",date:ts,memo:""});
  const [fxF,setFxF]=useState({name:"",cat:"家賃",amt:"",note:""});
  const [incF,setIncF]=useState({cat:"給与",amt:"",date:ts,memo:""});
  const [showFx,setShowFx]=useState(false),[showTxForm,setShowTxForm]=useState(false),[ltab,setLtab]=useState("cf");
  const [pays,setPays]=useState({});
  const txListRef=useRef<HTMLDivElement | null>(null);
  // バックアップ復元時に「ファイルを選ぶ」ダイアログを開くための隠しinputへの参照
  const fileInputRef=useRef<HTMLInputElement | null>(null);
  // トースト・確認ダイアログ・削除Undo をまとめた共通フック
  const { toast, dlg, setDlg, showT, ask, delItem } = useToast();
  const [accF,setAccF]=useState({name:"",balance:""}),[showAccF,setShowAccF]=useState(false),[editAccId,setEditAccId]=useState<string | null>(null);
  const allOk=txReady&&fxReady&&loansReady&&cashFlowReady&&balanceReady&&incomesReady&&accountsReady&&budgetReady&&tplsReady&&transfersReady&&categoryConfigReady&&savingGoalReady;
  // ローン・キャッシング・銀行ローンをまとめた配列（月別集計フックに渡す）
  const allL=useMemo(()=>[...loans,...cashFlow,...balance],[loans,cashFlow,balance]);
  // 月別データ集計フック：選択月のフィルタ済みリストと各合計値を取得
  const {
    monthString,
    monthlyTransactions,
    monthlyIncomes,
    totalVariableExpense,
    totalFixedExpense,
    totalLoanRepayment,
    totalIncome,
    totalBurden,
    net,
  } = useMonthlyData({ transactions, incomes, fixedExpenses, loans: allL, selectedYear, selectedMonth });
  const expByCat=useMemo(()=>{const m: Record<string,number>={};monthlyTransactions.forEach(t=>{if(t.category)m[t.category]=(m[t.category]||0)+Number(t.amount||0);});return Object.entries(m).sort((a,b)=>b[1]-a[1]);},[monthlyTransactions]);
  // 前月の年月文字列（前月比較カードで使う）
  const prevMs=useMemo(()=>{const pm=selectedMonth===0?11:selectedMonth-1,py=selectedMonth===0?selectedYear-1:selectedYear;return py+"-"+String(pm+1).padStart(2,"0");},[selectedMonth,selectedYear]);
  const prevTVar=useMemo(()=>transactions.filter(t=>t.date?.startsWith(prevMs)).reduce((s,t)=>s+Number(t.amount||0),0),[transactions,prevMs]);
  const prevTInc=useMemo(()=>incomes.filter(i=>i.date?.startsWith(prevMs)).reduce((s,i)=>s+Number(i.amount||0),0),[incomes,prevMs]);
  function prevM(){if(selectedMonth===0){setSelectedMonth(11);setSelectedYear(y=>y-1);}else setSelectedMonth(m=>m-1);}
  function nextM(){if(selectedMonth===11){setSelectedMonth(0);setSelectedYear(y=>y+1);}else setSelectedMonth(m=>m+1);}
  const isCur=selectedMonth===today.getMonth()&&selectedYear===today.getFullYear();

  // ──────── データマイグレーション（旧形式のamount文字列・noteフィールドを修正） ────────
  useEffect(() => {
    if (!allOk) return;
    setTransactions(p => migrateTransactions(p));
    setIncomes(p => migrateIncomes(p));
    setFixedExpenses(p => migrateFixedExpenses(p));
    setLoans(p => migrateLoans(p));
    setCashFlow(p => migrateLoans(p));
    setBalance(p => migrateLoans(p));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allOk]);

  // ──────── 自動引落の実行管理（useAutoPayment フックに移動済み） ────────
  useAutoPayment({ setLoans, setCashFlow, setBalance, ready: allOk });

  // ──────── CSV出力（useDataExport フックに移動済み） ────────
  const { exportMonthlyCsv, exportMonthlyIncomeCsv } = useDataExport({ monthlyTransactions, monthlyIncomes, showT });
  // ────────── バックアップ・復元（useBackup フックに移動済み） ──────────
  const { exportBackup, importBackup } = useBackup({ todayStr: ts, showT, ask });
  // 支出追加：連続入力できるよう、金額・メモのみクリアしてフォームは閉じない（スクロール移動も廃止）
  // 成功時に true を返す→View 側で「金額入力欄に再フォーカス」できる
  function addTx(){
    const a=parseYenAmount(txF.amt);
    if(!a||a<=0){showT("金額を入力","error");return false;}
    setTransactions(p=>[...p,{id:newId(),category:txF.cat,amount:a,date:txF.date,memo:txF.memo}]);
    setTxF(f=>({...f,amt:"",memo:""}));
    showT("追加しました");
    return true;
  }
  function addInc(){
    const a=parseYenAmount(incF.amt);
    if(!a||a<=0){showT("金額を入力","error");return false;}
    setIncomes(p=>[...p,{id:newId(),category:incF.cat,amount:a,date:incF.date,memo:incF.memo}]);
    setIncF(f=>({...f,amt:"",memo:""}));
    showT("追加しました");
    return true;
  }
  // 固定費追加：keepOpen=true なら追加後もフォームを開いたまま（連続入力モード）
  function addFx(keepOpen?: boolean){
    const a=parseYenAmount(fxF.amt);
    if(!fxF.name||!a){showT("項目名と金額を入力","error");return false;}
    setFixedExpenses(p=>[...p,{id:newId(),name:fxF.name,category:fxF.cat,amount:a,payDay:"未設定"}]);
    setFxF({name:"",cat:"家賃",amt:"",note:""});
    if(!keepOpen) setShowFx(false);
    showT("追加しました");
    return true;
  }
  // 口座間振替を先頭に追加する
  function addTransfer(transfer: Transfer){setTransfers(prev=>[transfer,...prev]);showT("振替しました");}

  // チュートリアル表示状態（localStorage に kk_tutorial_done=1 がなければ初回表示）
  const [showTutorial, setShowTutorial] = useState(() => localStorage.getItem("kk_tutorial_done") !== "1");
  // チュートリアルを閉じる：表示済みフラグを localStorage に保存する
  function handleCloseTutorial() {
    localStorage.setItem("kk_tutorial_done", "1");
    setShowTutorial(false);
  }

  if(!allOk) return <div style={{minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center",background:COLOR_BACKGROUND,flexDirection:"column",gap:14}}><div style={{fontSize:40,filter:"drop-shadow(0 0 12px rgba(34,211,238,0.5))"}}>💰</div><div style={{color:COLOR_TEXT_SECONDARY,fontSize:13,letterSpacing:"2px",textTransform:"uppercase"}}>Loading...</div></div>;

  return <div style={{background:COLOR_BACKGROUND,minHeight:"100vh",color:COLOR_TEXT_PRIMARY,fontFamily:'"Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif',WebkitTapHighlightColor:"transparent"}}>
    <Toast data={toast}/>
    <ConfirmDialog data={dlg} onOk={()=>{dlg?.onOk();setDlg(null);}} onCancel={()=>setDlg(null)}/>
    <TutorialModal open={showTutorial} onClose={handleCloseTutorial}/>
    <div style={{position:"sticky",top:0,zIndex:50,background:"rgba(7,11,20,0.95)",backdropFilter:"blur(24px)",borderBottom:`1px solid ${COLOR_BORDER_GLOW}`,padding:"0 16px"}}>
      <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"14px 0 12px",maxWidth:520,margin:"0 auto"}}>
        <div><div style={{fontSize:9,letterSpacing:"3px",color:COLOR_ACCENT,textTransform:"uppercase",marginBottom:3,fontWeight:600}}>Before You Broke</div><div style={{fontSize:18,fontWeight:700,letterSpacing:"-0.5px"}}>BYB</div></div>
        <div style={{textAlign:"right"}}><div style={{fontSize:9,color:COLOR_TEXT_HINT,marginBottom:3,letterSpacing:"1px",textTransform:"uppercase"}}>今月の手残り</div><div style={{fontFamily:"monospace",fontSize:18,fontWeight:700,color:net>=0?COLOR_POSITIVE:COLOR_NEGATIVE,letterSpacing:"-0.5px"}}>{net>=0?"+":""}{formatYen(net)}</div></div>
      </div>
    </div>
    <div style={{padding:"16px 16px calc(110px + env(safe-area-inset-bottom))",maxWidth:520,margin:"0 auto"}}>
      {/* lazy ロードされたタブの読み込み中フォールバック（小さなインジケーター） */}
      <Suspense fallback={<div style={{textAlign:"center",padding:"40px 0",color:COLOR_TEXT_HINT,fontSize:13}}>読み込み中…</div>}>
      {tab==="dash"&&<DashboardView
        selectedYear={selectedYear}
        selectedMonth={selectedMonth}
        onMonthChange={(y,m)=>{setSelectedYear(y);setSelectedMonth(m);}}
        totalIncome={totalIncome}
        totalBurden={totalBurden}
        net={net}
        totalVariableExpense={totalVariableExpense}
        totalFixedExpense={totalFixedExpense}
        totalLoanRepayment={totalLoanRepayment}
        accounts={accounts}
        setAccounts={setAccounts}
        showAccF={showAccF}
        setShowAccF={setShowAccF}
        accF={accF}
        setAccF={setAccF}
        editAccId={editAccId}
        setEditAccId={setEditAccId}
        expByCat={expByCat}
        prevTInc={prevTInc}
        prevTVar={prevTVar}
        allL={allL}
        transactions={transactions}
        incomes={incomes}
        transfers={transfers}
        addTransfer={addTransfer}
        exportBackup={exportBackup}
        importBackup={importBackup}
        fileInputRef={fileInputRef}
        ts={ts}
        showT={showT}
        ask={ask}
        delItem={delItem}
        savingGoal={savingGoal}
        setSavingGoal={setSavingGoal}
        budget={budget}
      />}
      {tab==="inc"&&<IncomeView
        incF={incF}
        setIncF={setIncF}
        addInc={addInc}
        selectedYear={selectedYear}
        selectedMonth={selectedMonth}
        onMonthChange={(y,m)=>{setSelectedYear(y);setSelectedMonth(m);}}
        exportMonthlyIncomeCsv={exportMonthlyIncomeCsv}
        monthlyIncomes={monthlyIncomes}
        setIncomes={setIncomes}
        showT={showT}
        ask={ask}
        categoryConfig={categoryConfig}
        delItem={delItem}
      />}
      {tab==="fix"&&<FixedExpenseView
        totalFixedExpense={totalFixedExpense}
        fixedExpenses={fixedExpenses}
        setFixedExpenses={setFixedExpenses}
        showFx={showFx}
        setShowFx={setShowFx}
        fxF={fxF}
        setFxF={setFxF}
        addFx={addFx}
        showT={showT}
        ask={ask}
        categoryConfig={categoryConfig}
        delItem={delItem}
      />}
      {tab==="exp"&&<ExpenseView
        tpls={tpls}
        setTpls={setTpls}
        txF={txF}
        setTxF={setTxF}
        showTxForm={showTxForm}
        setShowTxForm={setShowTxForm}
        addTx={addTx}
        budget={budget}
        setBudget={setBudget}
        monthlyTransactions={monthlyTransactions}
        selectedYear={selectedYear}
        selectedMonth={selectedMonth}
        onMonthChange={(y,m)=>{setSelectedYear(y);setSelectedMonth(m);}}
        totalVariableExpense={totalVariableExpense}
        exportMonthlyCsv={exportMonthlyCsv}
        setTransactions={setTransactions}
        showT={showT}
        ask={ask}
        txListRef={txListRef}
        categoryConfig={categoryConfig}
        delItem={delItem}
      />}
      {tab==="loan"&&<LoanView
        allL={allL}
        totalLoanRepayment={totalLoanRepayment}
        ltab={ltab}
        setLtab={setLtab}
        cashFlow={cashFlow}
        setCashFlow={setCashFlow}
        balance={balance}
        setBalance={setBalance}
        loans={loans}
        setLoans={setLoans}
        pays={pays}
        setPays={setPays}
        delItem={delItem}
        showT={showT}
      />}
      {tab==="set"&&<SettingsView
        categoryConfig={categoryConfig}
        setCategoryConfig={setCategoryConfig}
        transactions={transactions}
        setTransactions={setTransactions}
        incomes={incomes}
        setIncomes={setIncomes}
        fixedExpenses={fixedExpenses}
        setFixedExpenses={setFixedExpenses}
        onReset={()=>{}}
        onOpenTutorial={() => setShowTutorial(true)}
      />}
      </Suspense>
    </div>
    <nav style={{position:"fixed",bottom:0,left:0,right:0,background:"rgba(7,11,20,0.96)",backdropFilter:"blur(24px)",borderTop:`1px solid ${COLOR_BORDER}`,display:"flex",zIndex:100,paddingBottom:"env(safe-area-inset-bottom)"}}>
      {[["dash","📊","概要"],["inc","💰","収入"],["fix","📌","固定費"],["exp","💸","支出"],["loan","🏦","ローン"],["set","⚙️","設定"]].map(([key,icon,label])=>(
        <button key={key} onClick={()=>setTab(key)} style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",padding:"12px 4px 14px",cursor:"pointer",border:"none",background:"none",color:tab===key?COLOR_ACCENT:COLOR_TEXT_HINT,fontSize:10,gap:3,fontFamily:"inherit",minHeight:60,position:"relative",WebkitTapHighlightColor:"transparent"}}>
          {tab===key&&<div style={{position:"absolute",top:0,left:"50%",transform:"translateX(-50%)",width:30,height:2,background:COLOR_ACCENT,borderRadius:1,boxShadow:`0 0 8px ${COLOR_ACCENT},0 0 16px rgba(34,211,238,0.4)`}}/>}
          <span style={{fontSize:22,lineHeight:1,transform:tab===key?"scale(1.12)":"scale(1)",transition:"transform 0.15s ease"}}>{icon}</span>
          <span style={{fontWeight:tab===key?700:400,letterSpacing:tab===key?"0.5px":"0"}}>{label}</span>
        </button>
      ))}
    </nav>
  </div>;
}

// 外側（PasswordGate でラップして AppInner に Context を届ける）
export default function App(){
  return <PasswordGate><AppInner /></PasswordGate>;
}
