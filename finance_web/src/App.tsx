// ────────── アプリ本体 ──────────
// 全タブの状態管理・画面切替・CSV出力・バックアップ機能をまとめた中心ファイル
// UI部品・ユーティリティ・フックはすべて外部ファイルから読み込む

import { useState, useEffect, useMemo, useRef, useCallback, lazy, Suspense } from "react";
import { usePersist } from "./hooks/usePersist";
import { useMonthlyData } from "./hooks/useMonthlyData";
import { useAutoPayment } from "./hooks/useAutoPayment";
import { useAutoIncome } from "./hooks/useAutoIncome";
import { useAutoExpense } from "./hooks/useAutoExpense";
import { useAutoFixedExpense } from "./hooks/useAutoFixedExpense";
import { useDataExport } from "./hooks/useDataExport";
import { useToast } from "./hooks/useToast";
import { useBackup } from "./hooks/useBackup";
import { newId } from "./utils/crypto";
import { parseYenAmount, formatYen, MONTH_LABELS, EXPENSE_CATEGORIES, FIXED_EXPENSE_CATEGORIES, INCOME_CATEGORIES, EXPENSE_CATEGORY_ICONS, FIXED_EXPENSE_CATEGORY_ICONS, INCOME_CATEGORY_ICONS } from "./utils/format";
import { calculateMonthlyInterest, calculateTotalInterest, calculateCompletionDate, BRANDS_CF, BRANDS_BL } from "./utils/loanCalc";
import { COLOR_BACKGROUND, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_HINT, COLOR_BORDER, COLOR_BORDER_GLOW, COLOR_ACCENT, COLOR_POSITIVE, COLOR_NEGATIVE, STYLE_CARD, STYLE_BUTTON_PRIMARY, STYLE_BUTTON_OUTLINE } from "./utils/styles";
import { migrateTransactions, migrateIncomes, migrateFixedExpenses, migrateLoans } from "./utils/dataMigration";
import { useCloudSync } from "./hooks/useCloudSync";
import type { SyncValues } from "./utils/syncState";
import CloudSyncSection from "./components/CloudSyncSection";
import { Transfer, CategoryConfig, SavingGoal, RecurringIncome, RecurringExpense, SummaryStats } from "./types";
import { computeSavingRate } from "./utils/summaryExport";
import { makeDefaultCategoryConfig } from "./utils/defaultCategories";
import { CSSProperties } from "react";
import PasswordGate from "./components/PasswordGate";

// ── スタイル定数 ──────────────────────────────────────────

// 通知許可バナー全体
const STYLE_NOTIF_BANNER: CSSProperties = {
  display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10,
  background: "rgba(34,211,238,0.06)", border: "1px solid rgba(34,211,238,0.2)",
  borderRadius: 10, padding: "10px 14px", marginBottom: 12, fontSize: 12,
};

// 通知許可バナー内「有効にする」ボタン
const STYLE_NOTIF_BTN: CSSProperties = {
  background: "rgba(34,211,238,0.15)", border: "1px solid rgba(34,211,238,0.4)",
  borderRadius: 6, color: COLOR_ACCENT, fontSize: 11, fontWeight: 700,
  padding: "4px 12px", cursor: "pointer", fontFamily: "inherit", whiteSpace: "nowrap",
};

// 下部ナビゲーションバー全体
const STYLE_BOTTOM_NAV: CSSProperties = {
  position: "fixed", bottom: 0, left: 0, right: 0,
  background: "rgba(7,11,20,0.96)", backdropFilter: "blur(24px)",
  borderTop: `1px solid ${COLOR_BORDER}`, display: "flex",
  zIndex: 100, paddingBottom: "env(safe-area-inset-bottom)",
};

// 下部ナビの各タブボタンの静的スタイル（color は active 状態で動的に変わる）
const STYLE_NAV_BTN_BASE: CSSProperties = {
  flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
  padding: "12px 4px 14px", cursor: "pointer", border: "none", background: "none",
  fontSize: 10, gap: 3, fontFamily: "inherit", minHeight: 60,
  position: "relative", WebkitTapHighlightColor: "transparent",
};

// 下部ナビ・アクティブタブの上部インジケーターバー
const STYLE_NAV_INDICATOR: CSSProperties = {
  position: "absolute", top: 0, left: "50%", transform: "translateX(-50%)",
  width: 30, height: 2, background: COLOR_ACCENT,
  borderRadius: 1, boxShadow: `0 0 8px ${COLOR_ACCENT},0 0 16px rgba(34,211,238,0.4)`,
};

// ─────────────────────────────────────────────────────────
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
// 月次レポートモーダル（月が変わった初回アクセス時に前月振り返りを表示）
import MonthlyReportModal from "./components/MonthlyReportModal";
// ブラウザ通知フック（予算超過・自動収入追加などのローカル通知）
import { useNotification } from "./hooks/useNotification";
// それ以外のビューは初回ロードを軽くするためタブを開いた時に動的ロード（コード分割）
const IncomeView = lazy(() => import("./views/IncomeView"));
const FixedExpenseView = lazy(() => import("./views/FixedExpenseView"));
const ExpenseView = lazy(() => import("./views/ExpenseView"));
const LoanView = lazy(() => import("./views/LoanView"));
const SettingsView = lazy(() => import("./views/SettingsView"));
const SummaryView = lazy(() => import("./views/SummaryView"));
const SearchView = lazy(() => import("./views/SearchView"));

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
  // 定期収入の設定一覧（給与・副業など毎月自動追加する収入の設定）
  const [recurringIncomes,setRecurringIncomes,recIncReady]=usePersist<RecurringIncome[]>("kk_rec_inc",[]);
  // 繰り返し支出の設定一覧（サブスク・ジム代など毎月自動追加する変動支出の設定）
  const [recurringExpenses,setRecurringExpenses,recExpReady]=usePersist<RecurringExpense[]>("kk_rec_exp",[]);
  // 支出フォーム（accountId: 口座に紐づける任意フィールド）
  const [txF,setTxF]=useState<{cat:string;amt:string;date:string;memo:string;accountId?:string}>({cat:"食費",amt:"",date:ts,memo:""});
  const [fxF,setFxF]=useState({name:"",cat:"家賃",amt:"",note:""});
  // 収入フォーム（accountId: 口座に紐づける任意フィールド）
  const [incF,setIncF]=useState<{cat:string;amt:string;date:string;memo:string;accountId?:string}>({cat:"給与",amt:"",date:ts,memo:""});
  const [showFx,setShowFx]=useState(false),[showTxForm,setShowTxForm]=useState(false),[ltab,setLtab]=useState("cf");
  const [pays,setPays]=useState({});
  const txListRef=useRef<HTMLDivElement | null>(null);
  // バックアップ復元時に「ファイルを選ぶ」ダイアログを開くための隠しinputへの参照
  const fileInputRef=useRef<HTMLInputElement | null>(null);
  // トースト・確認ダイアログ・削除Undo をまとめた共通フック
  const { toast, dlg, setDlg, showT, ask, delItem } = useToast();
  // ブラウザ通知フック（予算超過・自動収入などのローカル通知）
  const { permission: notifPermission, requestPermission, notify } = useNotification();
  // 月次レポートモーダルの表示状態とデータ
  const [showMonthlyReport, setShowMonthlyReport] = useState(false);
  const [reportData, setReportData] = useState<{
    year: number; month: number; income: number; expense: number;
    topCats: [string, number][]; overBudget: [string, number][];
  }>({ year: 0, month: 0, income: 0, expense: 0, topCats: [], overBudget: [] });
  // 月次レポートのチェックを1回だけ実行するためのフラグ
  const reportCheckedRef = useRef(false);
  // 月切り替えハンドラをメモ化してインライン lambda の再生成を防ぐ
  const handleMonthChange = useCallback((y: number, m: number) => { setSelectedYear(y); setSelectedMonth(m); }, []);
  // 口座フォームの入力値（name: 口座名、balance: 残高、color: カラーラベル）
  const [accF,setAccF]=useState({name:"",balance:"",color:""}),[showAccF,setShowAccF]=useState(false),[editAccId,setEditAccId]=useState<string | null>(null);
  const allOk=txReady&&fxReady&&loansReady&&cashFlowReady&&balanceReady&&incomesReady&&accountsReady&&budgetReady&&tplsReady&&transfersReady&&categoryConfigReady&&savingGoalReady&&recIncReady&&recExpReady;

  // ────────── クラウド同期の配線 ──────────
  // 同期対象14種(kk_*)の「今の値」を1つの箱にまとめて返す関数（呼ぶたび最新値を返す）
  const syncGetValues = useCallback((): SyncValues => ({
    kk_tx: transactions,           // 取引
    kk_inc: incomes,               // 収入
    kk_fx: fixedExpenses,          // 固定費
    kk_lo: loans,                  // ローン
    kk_cf: cashFlow,               // キャッシング
    kk_bl: balance,                // 銀行ローン
    kk_accounts: accounts,         // 口座
    kk_transfers: transfers,       // 振替
    kk_tpls: tpls,                 // テンプレート
    kk_rec_inc: recurringIncomes,  // 定期収入
    kk_rec_exp: recurringExpenses, // 定期支出
    kk_budget: budget,             // 予算（単一値）
    kk_categories: categoryConfig, // カテゴリ設定（単一値）
    kk_savingGoal: savingGoal,     // 貯金目標（単一値）
  }), [transactions, incomes, fixedExpenses, loans, cashFlow, balance, accounts, transfers, tpls, recurringIncomes, recurringExpenses, budget, categoryConfig, savingGoal]);

  // マージ結果を各ストアへ書き戻すセッター表（key→setter）。型はunknownで受けてキャストする
  const syncSetters = useMemo<Record<string, (value: unknown) => void>>(() => ({
    kk_tx: setTransactions as (v: unknown) => void,
    kk_inc: setIncomes as (v: unknown) => void,
    kk_fx: setFixedExpenses as (v: unknown) => void,
    kk_lo: setLoans as (v: unknown) => void,
    kk_cf: setCashFlow as (v: unknown) => void,
    kk_bl: setBalance as (v: unknown) => void,
    kk_accounts: setAccounts as (v: unknown) => void,
    kk_transfers: setTransfers as (v: unknown) => void,
    kk_tpls: setTpls as (v: unknown) => void,
    kk_rec_inc: setRecurringIncomes as (v: unknown) => void,
    kk_rec_exp: setRecurringExpenses as (v: unknown) => void,
    kk_budget: setBudget as (v: unknown) => void,
    kk_categories: setCategoryConfig as (v: unknown) => void,
    kk_savingGoal: setSavingGoal as (v: unknown) => void,
  }), []);

  // 同期フック本体。allOk（全データ読込済）になったら稼働できる
  const cloudSync = useCloudSync({ getValues: syncGetValues, setters: syncSetters, ready: allOk });

  // 同期対象のどれかが変わったら、5秒debounceでサーバへ送る（変更検知）
  const notifyChange = cloudSync.notifyChange;
  useEffect(() => {
    if (!allOk) return;
    notifyChange();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [transactions, incomes, fixedExpenses, loans, cashFlow, balance, accounts, transfers, tpls, recurringIncomes, recurringExpenses, budget, categoryConfig, savingGoal]);

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
  // 前月の変動支出トランザクション配列（カテゴリ別前月比バッジで使う）
  const prevMonthlyTransactions=useMemo(()=>transactions.filter(t=>t.date?.startsWith(prevMs)),[transactions,prevMs]);
  const prevTInc=useMemo(()=>incomes.filter(i=>i.date?.startsWith(prevMs)).reduce((s,i)=>s+Number(i.amount||0),0),[incomes,prevMs]);
  // ── 月次サマリータブ用の集計 ──────────────────────────
  // 前月の年月（前月比サマリーで使う。1月の前は前年12月になるように分岐）
  const prevSummaryMonth = selectedMonth === 0 ? 11 : selectedMonth - 1;        // 前月の月番号（0〜11）
  const prevSummaryYear = selectedMonth === 0 ? selectedYear - 1 : selectedYear; // 前月の年（1月なら前年）
  // 前月分の集計（固定費・ローン返済も含めた支出合計を正しく出すためフックを前月の年月で呼び直す）
  const prevMonthData = useMonthlyData({ transactions, incomes, fixedExpenses, loans: allL, selectedYear: prevSummaryYear, selectedMonth: prevSummaryMonth });
  // 当月の集計値（収入・支出・手残り・貯蓄率）を1つにまとめる
  const currentSummary: SummaryStats = useMemo(() => ({
    income: totalIncome,                              // 収入合計
    expense: totalBurden,                             // 支出合計（変動＋固定＋ローン返済）
    net,                                              // 手残り（収入 − 支出）
    savingRate: computeSavingRate(net, totalIncome),  // 貯蓄率（％・小数第1位まで）
  }), [totalIncome, totalBurden, net]);
  // 前月の集計値。収入も支出も両方0なら「前月データなし」とみなして null にする
  const previousSummary: SummaryStats | null = useMemo(() => {
    if (prevMonthData.totalIncome === 0 && prevMonthData.totalBurden === 0) return null;
    return {
      income: prevMonthData.totalIncome,
      expense: prevMonthData.totalBurden,
      net: prevMonthData.net,
      savingRate: computeSavingRate(prevMonthData.net, prevMonthData.totalIncome),
    };
  }, [prevMonthData.totalIncome, prevMonthData.totalBurden, prevMonthData.net]);
  // カテゴリ内訳を SummaryView が受け取る形（{category, amount}の配列）に変換する。expByCat は降順済み
  const categoryBreakdown = useMemo(() => expByCat.map(([category, amount]) => ({ category, amount })), [expByCat]);
  // サマリーに表示する月ラベル（例:「2026年5月」）
  const summaryMonthLabel = `${selectedYear}年${selectedMonth + 1}月`;
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
  // ──────── 定期収入の自動追加（useAutoIncome フックに移動済み） ────────
  useAutoIncome({
    recurringIncomes, setRecurringIncomes, setIncomes, ready: allOk,
    // 自動追加が起きたらブラウザ通知を送る
    onAutoAdded: (count) => notify(`定期収入を${count}件自動追加しました`, "アプリを開いてご確認ください"),
  });
  // ──────── 繰り返し支出の自動追加（useAutoExpense フックに移動済み） ────────
  useAutoExpense({
    recurringExpenses, setRecurringExpenses, setTransactions, ready: allOk,
    onAutoAdded: (count) => notify(`繰り返し支出を${count}件自動追加しました`, "アプリを開いてご確認ください"),
  });
  // ──────── 固定費の自動月次反映（autoTrack=true の固定費を変動支出として自動追加） ────────
  useAutoFixedExpense({
    fixedExpenses, setFixedExpenses, setTransactions, ready: allOk,
    onAutoAdded: (count) => notify(`固定費を${count}件自動追加しました`, "アプリを開いてご確認ください"),
  });

  // ──────── 月次レポート：月が変わった最初のアクセス時に前月振り返りを表示 ────────
  useEffect(() => {
    // データが復号完了するまで待つ・1セッションで1回だけ実行する
    if (!allOk || reportCheckedRef.current) return;
    reportCheckedRef.current = true;

    // 現在の年月文字列（例: "2026-05"）
    const currentMs = today.getFullYear() + "-" + String(today.getMonth() + 1).padStart(2, "0");
    // 前回アクセス時の年月（localStorage に保存してある）
    const storedMs = localStorage.getItem("kk_last_report_month") || "";

    // 月が変わっていた場合だけレポートを表示する
    if (storedMs && storedMs !== currentMs) {
      const [py, pm] = storedMs.split("-").map(Number);

      // 前月の収入合計
      const prevInc = incomes
        .filter(i => i.date?.startsWith(storedMs))
        .reduce((s, i) => s + Number(i.amount || 0), 0);
      // 前月の変動支出合計
      const prevVar = transactions
        .filter(t => t.date?.startsWith(storedMs))
        .reduce((s, t) => s + Number(t.amount || 0), 0);
      // 固定費は現在の設定を近似として使う
      const prevFixed = fixedExpenses.reduce((s, f) => s + Number(f.amount || 0), 0);
      const prevExpense = prevVar + prevFixed;

      // カテゴリ別支出を集計してTOP3を出す
      const catMap: Record<string, number> = {};
      transactions
        .filter(t => t.date?.startsWith(storedMs))
        .forEach(t => { if (t.category) catMap[t.category] = (catMap[t.category] || 0) + Number(t.amount || 0); });
      const topCats = Object.entries(catMap)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3) as [string, number][];

      // 予算超過カテゴリ（変動支出で予算が設定されているもののみ）
      const overBudget = Object.entries(catMap)
        .filter(([cat, amt]) => budget[cat as keyof typeof budget] && amt > Number(budget[cat as keyof typeof budget]))
        .map(([cat, amt]) => [cat, amt - Number(budget[cat as keyof typeof budget])] as [string, number]);

      setReportData({ year: py, month: pm, income: prevInc, expense: prevExpense, topCats, overBudget });
      setShowMonthlyReport(true);
    }

    // 今月の年月を保存する（次回アクセス時の比較に使う）
    localStorage.setItem("kk_last_report_month", currentMs);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allOk]);

  // ──────── CSV出力（useDataExport フックに移動済み） ────────
  const { exportMonthlyCsv, exportMonthlyIncomeCsv } = useDataExport({ monthlyTransactions, monthlyIncomes, showT });
  // ────────── バックアップ・復元（useBackup フックに移動済み） ──────────
  const { exportBackup, importBackup } = useBackup({ todayStr: ts, showT, ask });
  // 支出追加：連続入力できるよう、金額・メモのみクリアしてフォームは閉じない（スクロール移動も廃止）
  // 成功時に true を返す→View 側で「金額入力欄に再フォーカス」できる
  function addTx(){
    const a=parseYenAmount(txF.amt);
    if(!a||a<=0){showT("金額を入力","error");return false;}
    // 口座IDを含めて支出を追加する（accountId が未選択なら undefined のまま）
    setTransactions(p=>[...p,{id:newId(),category:txF.cat,amount:a,date:txF.date,memo:txF.memo,accountId:txF.accountId}]);
    setTxF(f=>({...f,amt:"",memo:"",accountId:undefined}));
    showT("追加しました");
    // 予算超過チェック：追加後の月合計が予算を超えたらブラウザ通知を送る
    const budgetAmt = budget[txF.cat as keyof typeof budget];
    if(budgetAmt){
      const catTotal=monthlyTransactions.filter(t=>t.category===txF.cat).reduce((s,t)=>s+Number(t.amount||0),0)+a;
      if(catTotal>Number(budgetAmt)){
        notify(`「${txF.cat}」の予算を超過しました`,`今月: ${formatYen(catTotal)} / 予算: ${formatYen(Number(budgetAmt))}`);
      }
    }
    return true;
  }
  function addInc(){
    const a=parseYenAmount(incF.amt);
    if(!a||a<=0){showT("金額を入力","error");return false;}
    // 口座IDを含めて収入を追加する（accountId が未選択なら undefined のまま）
    setIncomes(p=>[...p,{id:newId(),category:incF.cat,amount:a,date:incF.date,memo:incF.memo,accountId:incF.accountId}]);
    setIncF(f=>({...f,amt:"",memo:"",accountId:undefined}));
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
    {/* 月次レポートモーダル（月が変わった最初の起動時に自動表示） */}
    <MonthlyReportModal
      open={showMonthlyReport}
      onClose={() => setShowMonthlyReport(false)}
      year={reportData.year}
      month={reportData.month}
      income={reportData.income}
      expense={reportData.expense}
      topCats={reportData.topCats}
      overBudget={reportData.overBudget}
      hasAccounts={accounts.length > 0}
    />
    <div style={{position:"sticky",top:0,zIndex:50,background:"rgba(7,11,20,0.95)",backdropFilter:"blur(24px)",borderBottom:`1px solid ${COLOR_BORDER_GLOW}`,padding:"0 16px"}}>
      <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"14px 0 12px",maxWidth:520,margin:"0 auto"}}>
        <div><div style={{fontSize:9,letterSpacing:"3px",color:COLOR_ACCENT,textTransform:"uppercase",marginBottom:3,fontWeight:600}}>Before You Broke</div><div style={{fontSize:18,fontWeight:700,letterSpacing:"-0.5px"}}>BYB</div></div>
        <div style={{textAlign:"right"}}><div style={{fontSize:9,color:COLOR_TEXT_HINT,marginBottom:3,letterSpacing:"1px",textTransform:"uppercase"}}>{isCur?"今月の手残り":`${selectedMonth+1}月の手残り`}</div><div style={{fontFamily:"monospace",fontSize:18,fontWeight:700,color:net>=0?COLOR_POSITIVE:COLOR_NEGATIVE,letterSpacing:"-0.5px"}}>{net>=0?"+":""}{formatYen(net)}</div></div>
      </div>
    </div>
    <div style={{padding:"16px 16px calc(110px + env(safe-area-inset-bottom))",maxWidth:520,margin:"0 auto"}}>
      {/* 通知許可バナー（まだ許可/拒否を選んでいない時だけ表示） */}
      {notifPermission === "default" && (
        <div style={STYLE_NOTIF_BANNER}>
          <span style={{color:COLOR_TEXT_SECONDARY}}>🔔 予算超過などをブラウザ通知で受け取れます</span>
          <button
            type="button"
            onClick={requestPermission}
            style={STYLE_NOTIF_BTN}
          >
            有効にする
          </button>
        </div>
      )}
      {/* lazy ロードされたタブの読み込み中フォールバック（小さなインジケーター） */}
      <Suspense fallback={<div style={{textAlign:"center",padding:"40px 0",color:COLOR_TEXT_HINT,fontSize:13}}>読み込み中…</div>}>
      {tab==="dash"&&<DashboardView
        selectedYear={selectedYear}
        selectedMonth={selectedMonth}
        onMonthChange={handleMonthChange}
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
        fixedExpenses={fixedExpenses}
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
      {tab==="sum"&&<SummaryView
        monthLabel={summaryMonthLabel}
        current={currentSummary}
        previous={previousSummary}
        categoryBreakdown={categoryBreakdown}
        showT={showT}
      />}
      {tab==="inc"&&<IncomeView
        incF={incF}
        setIncF={setIncF}
        accounts={accounts}
        addInc={addInc}
        selectedYear={selectedYear}
        selectedMonth={selectedMonth}
        onMonthChange={handleMonthChange}
        exportMonthlyIncomeCsv={exportMonthlyIncomeCsv}
        monthlyIncomes={monthlyIncomes}
        setIncomes={setIncomes}
        showT={showT}
        ask={ask}
        categoryConfig={categoryConfig}
        delItem={delItem}
        recurringIncomes={recurringIncomes}
        setRecurringIncomes={setRecurringIncomes}
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
        accounts={accounts}
        showTxForm={showTxForm}
        setShowTxForm={setShowTxForm}
        addTx={addTx}
        budget={budget}
        setBudget={setBudget}
        monthlyTransactions={monthlyTransactions}
        prevMonthlyTransactions={prevMonthlyTransactions}
        selectedYear={selectedYear}
        selectedMonth={selectedMonth}
        onMonthChange={handleMonthChange}
        totalVariableExpense={totalVariableExpense}
        exportMonthlyCsv={exportMonthlyCsv}
        setTransactions={setTransactions}
        showT={showT}
        ask={ask}
        txListRef={txListRef}
        categoryConfig={categoryConfig}
        delItem={delItem}
        recurringExpenses={recurringExpenses}
        setRecurringExpenses={setRecurringExpenses}
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
      {tab==="search"&&<SearchView
        transactions={transactions}
        incomes={incomes}
        accounts={accounts}
        categoryConfig={categoryConfig}
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
        exportBackup={exportBackup}
        importBackup={importBackup}
        transfers={transfers}
        setTransfers={setTransfers}
      />}
      {/* 設定タブの末尾にクラウド同期カードを表示する */}
      {tab==="set"&&<CloudSyncSection
        status={cloudSync.status}
        lastSyncedAt={cloudSync.lastSyncedAt}
        onActivate={cloudSync.activate}
        onDeactivate={cloudSync.deactivate}
        onSyncNow={cloudSync.syncNow}
      />}
      </Suspense>
    </div>
    <nav style={STYLE_BOTTOM_NAV}>
      {[["dash","📊","概要"],["sum","🧾","サマリー"],["inc","💰","収入"],["fix","📌","固定費"],["exp","💸","支出"],["loan","🏦","ローン"],["search","🔍","検索"],["set","⚙️","設定"]].map(([key,icon,label])=>(
        <button type="button" key={key} onClick={()=>setTab(key)} aria-current={tab===key?"page":undefined} style={{...STYLE_NAV_BTN_BASE,color:tab===key?COLOR_ACCENT:COLOR_TEXT_HINT}}>
          {tab===key&&<div style={STYLE_NAV_INDICATOR}/>}
          <span aria-hidden="true" style={{fontSize:22,lineHeight:1,transform:tab===key?"scale(1.12)":"scale(1)",transition:"transform 0.15s ease"}}>{icon}</span>
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
