// ────────── ダッシュボードタブのビューコンポーネント ──────────
// App.tsx から「概要タブ」の JSX を切り出して独立させたファイル
// 表示に必要なデータはすべて props（親から渡す値）で受け取る

import React, { useState, useMemo, lazy, Suspense } from "react";
import { Tx, Income, Loan, Account, Transfer, SavingGoal, FixedExpense } from "../types";
import MonthNav from "../components/MonthNav";
import { Input, StatLabel, ProgressBar } from "../components/ui";
import TransferForm from "../components/TransferForm";
// グラフコンポーネントは画面下部にあり recharts(500KB) を引っ張ってくるので遅延ロードで分離
const MonthlyChart = lazy(() => import("../components/MonthlyChart"));
const CategoryTrendChart = lazy(() => import("../components/CategoryTrendChart"));
import SavingGoalCard from "../components/SavingGoalCard";
import BudgetAlertBanner from "../components/BudgetAlertBanner";
import HealthCheckCard from "../components/HealthCheckCard";
import YearlySummary from "../components/YearlySummary";
import { parseYenAmount, formatYen, EXPENSE_CATEGORY_ICONS } from "../utils/format";
import { calculateMonthlyInterest, calculateTotalInterest, calculateCompletionDate } from "../utils/loanCalc";
import { calculateAccountBalance } from "../utils/accountBalance";
import { newId } from "../utils/crypto";
import {
  COLOR_TEXT_HINT,
  COLOR_ACCENT,
  COLOR_TEXT_SECONDARY,
  COLOR_TEXT_PRIMARY,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
  COLOR_BORDER,
  STYLE_CARD,
  STYLE_BUTTON_PRIMARY,
  STYLE_BUTTON_OUTLINE,
} from "../utils/styles";

// Account 型に updatedAt・color フィールドを追加した拡張型
// 型定義には updatedAt がないので、ここだけローカルに定義する
type AccountWithDate = Account & { updatedAt?: string; color?: string };

// ────────── このコンポーネントが受け取る props の型定義 ──────────
interface DashboardViewProps {
  // 現在選択中の年
  selectedYear: number;
  // 現在選択中の月（0〜11）
  selectedMonth: number;
  // 月を変更したとき呼ばれる関数
  onMonthChange: (year: number, month: number) => void;
  // 今月の収入合計
  totalIncome: number;
  // 今月の支出合計（変動＋固定＋返済）
  totalBurden: number;
  // 今月の手残り（収入 - 支出合計）
  net: number;
  // 今月の変動支出合計
  totalVariableExpense: number;
  // 今月の固定費合計
  totalFixedExpense: number;
  // 今月のローン返済合計
  totalLoanRepayment: number;
  // 口座一覧（更新日付付き）
  accounts: AccountWithDate[];
  // 口座一覧を更新する関数
  setAccounts: (u: any) => void;
  // 口座追加フォームの表示状態
  showAccF: boolean;
  // 口座フォーム表示を切り替える関数
  setShowAccF: React.Dispatch<React.SetStateAction<boolean>>;
  // 口座フォームの入力値（color は選択中のカラーコード、未選択なら空文字）
  accF: { name: string; balance: string; color: string };
  // 口座フォームの入力値を更新する関数
  setAccF: React.Dispatch<React.SetStateAction<{ name: string; balance: string; color: string }>>;
  // 編集中の口座ID（null なら新規追加）
  editAccId: string | null;
  // 編集中の口座IDを変更する関数
  setEditAccId: React.Dispatch<React.SetStateAction<string | null>>;
  // カテゴリ別支出の集計（[カテゴリ名, 金額] の配列）
  expByCat: [string, number][];
  // 前月の収入合計
  prevTInc: number;
  // 前月の変動支出合計
  prevTVar: number;
  // 全ローン一覧（消費者金融・銀行・住宅ローンを合わせた配列）
  allL: Loan[];
  // 固定費一覧（年間サマリーの月支出計算に使う）
  fixedExpenses: FixedExpense[];
  // 全変動支出一覧
  transactions: Tx[];
  // 全収入一覧
  incomes: Income[];
  // 口座間振替の一覧（残高計算に使う）
  transfers: Transfer[];
  // 新しい振替を追加するコールバック
  addTransfer: (transfer: Transfer) => void;
  // バックアップJSONをダウンロードする関数
  exportBackup: () => void;
  // バックアップJSONを読み込んで復元する関数
  importBackup: (file: File) => void;
  // 隠しファイル入力への参照（復元ボタンで使う）
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  // 今日の日付文字列（YYYY-MM-DD）
  ts: string;
  // トースト通知を表示する関数
  showT: (msg: string, type?: string) => void;
  // 確認ダイアログを表示する関数
  ask: (title: string, msg: string, onOk: () => void) => void;
  // 削除＋Undo：即削除してToastに「元に戻す」を出す
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  delItem: (id: string, setArr: (u: any) => void, label?: string) => void;
  // 貯金目標（未設定なら null）
  savingGoal: SavingGoal | null;
  // 貯金目標の更新関数
  setSavingGoal: (u: SavingGoal | null) => void;
  // カテゴリ別月予算（予算超過アラートに使う）
  budget: Record<string, number>;
}

// ────────── ダッシュボードビュー本体 ──────────
export default function DashboardView({
  selectedYear,
  selectedMonth,
  onMonthChange,
  totalIncome,
  totalBurden,
  net,
  totalVariableExpense,
  totalFixedExpense,
  totalLoanRepayment,
  accounts,
  setAccounts,
  showAccF,
  setShowAccF,
  accF,
  setAccF,
  editAccId,
  setEditAccId,
  expByCat,
  prevTInc,
  prevTVar,
  allL,
  fixedExpenses,
  transactions,
  incomes,
  transfers,
  addTransfer,
  exportBackup,
  importBackup,
  fileInputRef,
  ts,
  showT,
  ask,
  delItem,
  savingGoal,
  setSavingGoal,
  budget,
}: DashboardViewProps) {
  // 振替モーダルの表示・非表示
  const [showTransfer, setShowTransfer] = useState(false);
  // 「月次」と「年間」の表示切り替え（"monthly" or "yearly"）
  const [viewMode, setViewMode] = useState<"monthly" | "yearly">("monthly");
  // 年間サマリーで選択中の年（月次の selectedYear と独立して管理）
  const [yearlyYear, setYearlyYear] = useState(new Date().getFullYear());

  // ────────── 今月の予算消化ペース予測 ──────────
  // 「現在のペースで使い続けると月末にいくらになるか」を可視化する
  // 表示するのは「今月」を見ているときだけ（過去月/未来月の予測は意味がないので非表示）
  const today = new Date();
  const isCurMonth = selectedYear === today.getFullYear() && selectedMonth === today.getMonth();
  // 月末の日付＝翌月の0日。それで月の総日数が取れる
  const daysInMonth = new Date(selectedYear, selectedMonth + 1, 0).getDate();
  const daysElapsed = today.getDate();
  // 月末予想 = 現在の変動支出 × 月の総日数 ÷ 経過日数
  const projectedVariable = isCurMonth && daysElapsed > 0
    ? Math.round(totalVariableExpense * daysInMonth / daysElapsed)
    : 0;
  // 月末予想の総支出（固定費＋ローンは月初に確定するので変動分の予測だけ足す）
  const projectedTotal = projectedVariable + totalFixedExpense + totalLoanRepayment;
  // 予想手残り（マイナスなら赤くする）
  const projectedNet = totalIncome - projectedTotal;
  // 現在ペースが「速い」かどうか：経過日数比で 50% 以上消化したペースなら警告色
  const paceRatio = daysInMonth > 0 ? daysElapsed / daysInMonth : 0;
  const burdenRatio = totalIncome > 0 ? projectedTotal / totalIncome : 0;
  // 段階的なペース警告：80%超で注意（黄色）、100%超で危険（赤）
  const paceYellow = burdenRatio > 0.8 && burdenRatio <= 1; // 80〜100%：注意ライン
  const paceRed    = burdenRatio > 1;                       // 100%超：赤字見込み

  // ────────── 前年同月の集計（YoY比較用） ──────────
  // "2025-05" のような前年同月の年月文字列
  const prevYearMs = useMemo(() => `${selectedYear - 1}-${String(selectedMonth + 1).padStart(2, "0")}`, [selectedYear, selectedMonth]);
  // 前年同月の収入合計
  const prevYearTInc = useMemo(
    () => incomes.filter(i => i.date?.startsWith(prevYearMs)).reduce((s, i) => s + Number(i.amount || 0), 0),
    [incomes, prevYearMs]
  );
  // 前年同月の変動支出合計
  const prevYearTVar = useMemo(
    () => transactions.filter(t => t.date?.startsWith(prevYearMs)).reduce((s, t) => s + Number(t.amount || 0), 0),
    [transactions, prevYearMs]
  );
  // 前年同月にデータがあるかどうか（無ければカード非表示）
  const hasYoyData = prevYearTInc > 0 || prevYearTVar > 0;

  // 家計診断用：全口座残高合計（緊急資金チェックに使う）
  const totalSavings = useMemo(
    () => accounts.reduce((sum, acc) => sum + calculateAccountBalance(acc, transactions, incomes, transfers), 0),
    [accounts, transactions, incomes, transfers]
  );

  // ────────── 今月末の予測残高（繰越残高トラッカー） ──────────
  // "N日" → 数値に変換するヘルパー（"未設定"などはnullを返す）
  function parsePayDayN(payDay: string): number | null {
    const m = payDay?.match(/^(\d+)日$/);
    return m ? Number(m[1]) : null;
  }
  // 今日以降に引き落とされる固定費の合計（今日含む・active な項目のみ）
  const remainingFixed = useMemo(() => {
    const todayD = today.getDate();
    return fixedExpenses
      .filter(f => f.active !== false)
      .reduce((sum, f) => {
        const d = parsePayDayN(f.payDay || "");
        // payDay が今日以降なら残り引落に含める（未設定は月末に引き落とされると仮定して含める）
        if (d === null || d >= todayD) return sum + Number(f.amount || 0);
        return sum;
      }, 0);
  }, [fixedExpenses, today]);
  // 今月末予測残高 = 現在の口座残高合計 − 残り固定費 − ローン月額返済合計
  const predictedEndBalance = totalSavings - remainingFixed - totalLoanRepayment;

  return (
    <div>
      {/* ────────── 月次 / 年間 切り替えトグル ────────── */}
      <div style={{ display:"flex", gap:0, marginBottom:12, borderRadius:8, overflow:"hidden", border:`1px solid rgba(255,255,255,0.1)` }}>
        {(["monthly","yearly"] as const).map(mode => (
          <button
            key={mode}
            onClick={() => {
              setViewMode(mode);
              // 年間モードに切り替えるとき、現在の選択年を引き継ぐ
              if (mode === "yearly") setYearlyYear(selectedYear);
            }}
            style={{
              flex:1, padding:"9px 0", border:"none", cursor:"pointer",
              background: viewMode === mode ? "rgba(34,211,238,0.15)" : "rgba(255,255,255,0.03)",
              color: viewMode === mode ? "#22d3ee" : "#64748b",
              fontWeight: viewMode === mode ? 700 : 400,
              fontSize:13, fontFamily:"inherit",
              transition:"all 0.15s",
            }}
          >
            {mode === "monthly" ? "📅 月次" : "📆 年間"}
          </button>
        ))}
      </div>

      {/* ────────── 年間サマリービュー ────────── */}
      {viewMode === "yearly" && (
        <YearlySummary
          selectedYear={yearlyYear}
          onPrevYear={() => setYearlyYear(y => y - 1)}
          onNextYear={() => setYearlyYear(y => y + 1)}
          transactions={transactions}
          incomes={incomes}
          fixedExpenses={fixedExpenses}
          loans={allL}
          onSelectMonth={month => {
            // 年間サマリーの月をタップ → 月次ビューに戻り、その月に移動
            onMonthChange(yearlyYear, month);
            setViewMode("monthly");
          }}
        />
      )}

      {/* ────────── 月次ビュー（年間モード時は非表示） ────────── */}
      {viewMode === "monthly" && <>

      {/* ────────── 月ナビゲーション ────────── */}
      <MonthNav selectedYear={selectedYear} selectedMonth={selectedMonth} onChange={onMonthChange}/>

      {/* ────────── 予算超過アラート（今月閲覧 & 該当カテゴリがあるときだけ表示） ────────── */}
      <BudgetAlertBanner budget={budget} expByCat={expByCat} isCurrentMonth={isCurMonth}/>

      {/* ────────── 収入サマリーカード ────────── */}
      <div style={{...STYLE_CARD,background:"linear-gradient(135deg,rgba(15,23,42,0.95) 0%,rgba(34,211,238,0.07) 100%)",border:`1px solid rgba(34,211,238,0.18)`}}>
        <div style={{fontSize:9,color:COLOR_ACCENT,textTransform:"uppercase",letterSpacing:"2px",marginBottom:8,fontWeight:600}}>今月の収入</div>
        <div style={{fontFamily:"monospace",fontSize:34,fontWeight:700,marginBottom:12,letterSpacing:"-1px"}}>{formatYen(totalIncome)}</div>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
          <div style={{fontSize:12,color:COLOR_TEXT_SECONDARY}}>
            支出合計 <span style={{fontFamily:"monospace",color:COLOR_TEXT_PRIMARY}}>{formatYen(totalBurden)}</span>
            {totalIncome>0&&<span style={{marginLeft:8,fontSize:11,color:totalBurden>totalIncome?COLOR_NEGATIVE:COLOR_TEXT_HINT}}>({Math.round(totalBurden/totalIncome*100)}%)</span>}
          </div>
          <div style={{fontSize:13,fontWeight:700,color:net>=0?COLOR_POSITIVE:COLOR_NEGATIVE}}>
            手残り <span style={{fontFamily:"monospace"}}>{net>=0?"+":""}{formatYen(net)}</span>
          </div>
        </div>
      </div>

      {/* ────────── 今月のペース予測カード（今月かつ変動支出が1件以上ある時だけ表示） ────────── */}
      {isCurMonth && totalVariableExpense > 0 && (
        <div style={{...STYLE_CARD, borderColor: paceRed ? `${COLOR_NEGATIVE}44` : paceYellow ? "rgba(251,191,36,0.3)" : COLOR_BORDER}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:10}}>
            <div style={{fontSize:10,color:COLOR_TEXT_HINT,textTransform:"uppercase",letterSpacing:"1.5px"}}>📈 今月のペース</div>
            <div style={{fontSize:10,color:COLOR_TEXT_HINT,fontFamily:"monospace"}}>{daysElapsed}日 / {daysInMonth}日 ({Math.round(paceRatio*100)}%)</div>
          </div>
          {/* 月末予想カード本体 */}
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"baseline",marginBottom:6}}>
            <span style={{fontSize:12,color:COLOR_TEXT_SECONDARY}}>月末の支出予想</span>
            <span style={{fontFamily:"monospace",fontSize:18,fontWeight:700,color:paceRed?COLOR_NEGATIVE:paceYellow?"#fbbf24":COLOR_TEXT_PRIMARY}}>{formatYen(projectedTotal)}</span>
          </div>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"baseline",marginBottom:10}}>
            <span style={{fontSize:12,color:COLOR_TEXT_SECONDARY}}>月末の手残り予想</span>
            <span style={{fontFamily:"monospace",fontSize:18,fontWeight:700,color:projectedNet>=0?COLOR_POSITIVE:COLOR_NEGATIVE}}>{projectedNet>=0?"+":""}{formatYen(projectedNet)}</span>
          </div>
          {/* 経過バー：今月どこまで進んだかを視覚化 */}
          <div style={{height:6,background:"rgba(148,163,184,0.08)",borderRadius:3,overflow:"hidden",marginBottom:8}}>
            <div style={{height:"100%",width:`${Math.min(100,paceRatio*100)}%`,background:paceRed?COLOR_NEGATIVE:paceYellow?"#fbbf24":COLOR_ACCENT,borderRadius:3,transition:"width 0.4s ease"}}/>
          </div>
          {/* アドバイス文言：ペースに応じて表示を切り替える */}
          <div style={{fontSize:11,color:paceRed?COLOR_NEGATIVE:paceYellow?"#fbbf24":COLOR_TEXT_HINT,lineHeight:1.5}}>
            {paceRed
              ? `🔴 このペースだと月末に収入を ${formatYen(projectedTotal - totalIncome)} 超過する見込みです`
              : paceYellow
              ? `🟡 このペースだと月末の支出が収入の ${Math.round(burdenRatio*100)}% になる見込みです`
              : `現在のペースなら月末は手残り ${formatYen(Math.max(0,projectedNet))} の見込み`}
          </div>
        </div>
      )}

      {/* ────────── 口座残高カード ────────── */}
      <div style={STYLE_CARD}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
          <div style={{fontSize:10,color:COLOR_TEXT_HINT,textTransform:"uppercase",letterSpacing:"1.5px"}}>口座残高</div>
          <div style={{display:"flex",gap:8}}>
            {/* 振替ボタン：口座が2件以上あるときだけ表示 */}
            {accounts.length >= 2 && (
              <button
                onClick={() => setShowTransfer(true)}
                style={{...STYLE_BUTTON_OUTLINE,fontSize:12,padding:"5px 12px",minHeight:32}}
              >
                振替
              </button>
            )}
            {/* 追加ボタン：フォームの表示・非表示を切り替える */}
            <button
              onClick={()=>{setAccF({name:"",balance:"",color:""});setEditAccId(null);setShowAccF(v=>!v);}}
              style={{...STYLE_BUTTON_OUTLINE,fontSize:12,padding:"5px 12px",minHeight:32}}
            >
              {showAccF?"閉じる":"＋ 追加"}
            </button>
          </div>
        </div>
        {/* 口座が0件でフォームも閉じているときのプレースホルダー */}
        {accounts.length===0&&!showAccF&&(
          <div style={{textAlign:"center",padding:"18px 0",color:COLOR_TEXT_HINT,fontSize:13}}>
            🏦 口座を追加すると残高合計が確認できます
          </div>
        )}
        {/* 口座一覧の表示 */}
        {accounts.map(acc=>(
          <div key={acc.id} style={{display:"flex",alignItems:"center",gap:10,padding:"10px 0",borderBottom:`1px solid ${COLOR_BORDER}`}}>
            {/* カラーラベルドット：color が設定されている口座はカラードットで区別する */}
            {acc.color && (
              <div style={{
                width:10, height:10, borderRadius:"50%",
                background:acc.color, flexShrink:0,
              }}/>
            )}
            <div style={{flex:1,minWidth:0}}>
              <div style={{fontSize:13,fontWeight:600}}>{acc.name}</div>
              {/* updatedAt（更新日）があれば表示する */}
              {acc.updatedAt&&<div style={{fontSize:10,color:COLOR_TEXT_HINT,marginTop:2}}>{acc.updatedAt} 更新</div>}
            </div>
            {/* calculateAccountBalance で入出金・振替を反映した実際の残高を表示 */}
            <div style={{fontFamily:"monospace",fontSize:15,fontWeight:700,color:COLOR_POSITIVE}}>
              {formatYen(calculateAccountBalance(acc, transactions, incomes, transfers))}
            </div>
            {/* 編集ボタン：フォームに既存の値（color も含む）をセットして開く */}
            <button
              onClick={()=>{setAccF({name:acc.name,balance:String(acc.balance),color:acc.color||""});setEditAccId(acc.id);setShowAccF(true);}}
              style={{...STYLE_BUTTON_OUTLINE,fontSize:12,padding:"5px 10px",minHeight:32}}
            >
              編集
            </button>
            {/* 削除ボタン：確認ダイアログを出してから削除 */}
            <button
              onClick={()=>delItem(acc.id,setAccounts,"口座を削除しました")}
              style={{...STYLE_BUTTON_OUTLINE,fontSize:12,padding:"5px 10px",minHeight:32}}
            >
              削除
            </button>
          </div>
        ))}
        {/* 口座が1件以上あれば合計残高を表示 */}
        {accounts.length>0&&(
          <>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",paddingTop:10}}>
              <span style={{fontSize:11,color:COLOR_TEXT_HINT}}>合計残高</span>
              <span style={{fontFamily:"monospace",fontSize:16,fontWeight:700,color:COLOR_POSITIVE}}>
                {formatYen(accounts.reduce((s,a)=>s+calculateAccountBalance(a,transactions,incomes,transfers),0))}
              </span>
            </div>
            {/* ────────── 今月末の予測残高 ──────────
                合計残高から「残り固定費」と「ローン月返済額」を引いた試算値を表示する
                残高がマイナスになりそうなときは赤で警告する */}
            <div style={{
              marginTop:10,
              paddingTop:10,
              borderTop:`1px dashed rgba(255,255,255,0.08)`,
            }}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start"}}>
                <div>
                  <div style={{fontSize:11,color:COLOR_TEXT_HINT}}>今月末の予測残高</div>
                  {/* 内訳：残り固定費とローン返済を小さく補足表示 */}
                  <div style={{fontSize:9,color:COLOR_TEXT_HINT,marginTop:2}}>
                    残り固定費 {formatYen(remainingFixed)} + 返済 {formatYen(totalLoanRepayment)} を差引
                  </div>
                </div>
                <div style={{textAlign:"right"}}>
                  <span style={{
                    fontFamily:"monospace",
                    fontSize:15,
                    fontWeight:700,
                    // 0以上は青緑、マイナスは赤
                    color: predictedEndBalance >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE,
                  }}>
                    {formatYen(predictedEndBalance)}
                  </span>
                  {/* マイナスの場合は小さな警告ラベルを表示 */}
                  {predictedEndBalance < 0 && (
                    <div style={{
                      fontSize:9, color:COLOR_NEGATIVE,
                      background:"rgba(248,113,113,0.1)",
                      borderRadius:4, padding:"1px 6px",
                      marginTop:3, display:"inline-block",
                    }}>残高不足の恐れ</div>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
        {/* 口座の追加・編集フォーム */}
        {showAccF&&(
          <div style={{marginTop:12,paddingTop:12,borderTop:`1px solid ${COLOR_BORDER}`}}>
            <div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:10}}>
              <Input value={accF.name} onChange={e=>setAccF(f=>({...f,name:e.target.value}))} placeholder="口座名（例: 三井住友・楽天銀行）"/>
              <Input money type="number" value={accF.balance} onChange={e=>setAccF(f=>({...f,balance:e.target.value}))} placeholder="現在の残高（円）"/>
              {/* ────── カラーラベル選択（プリセットスウォッチ） ────── */}
              <div>
                <div style={{fontSize:11,color:COLOR_TEXT_HINT,marginBottom:6}}>カラーラベル（任意）</div>
                <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
                  {/* 「なし」ボタン：カラーをクリアする */}
                  <button
                    onClick={()=>setAccF(f=>({...f,color:""}))}
                    style={{
                      width:26, height:26, borderRadius:"50%",
                      background:"rgba(255,255,255,0.06)",
                      border:`2px solid ${accF.color===""?"rgba(34,211,238,0.7)":"rgba(255,255,255,0.15)"}`,
                      cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center",
                      fontSize:11, color:COLOR_TEXT_HINT, padding:0,
                    }}
                    title="なし"
                  >✕</button>
                  {/* 6色のプリセットスウォッチ */}
                  {[
                    {c:"#22c55e", label:"グリーン"},
                    {c:"#22d3ee", label:"シアン"},
                    {c:"#f43f5e", label:"レッド"},
                    {c:"#f59e0b", label:"アンバー"},
                    {c:"#a78bfa", label:"バイオレット"},
                    {c:"#fb923c", label:"オレンジ"},
                  ].map(({c,label})=>(
                    <button
                      key={c}
                      onClick={()=>setAccF(f=>({...f,color:c}))}
                      style={{
                        width:26, height:26, borderRadius:"50%",
                        background:c,
                        border:`2px solid ${accF.color===c?"#fff":"transparent"}`,
                        cursor:"pointer", padding:0,
                        boxShadow:accF.color===c?`0 0 0 2px ${c}55`:"none",
                        transition:"border 0.15s, box-shadow 0.15s",
                      }}
                      title={label}
                    />
                  ))}
                </div>
              </div>
            </div>
            <div style={{display:"flex",gap:10}}>
              {/* 保存ボタン：新規追加 or 編集を判定して処理 */}
              <button
                onClick={()=>{
                  const b=parseYenAmount(accF.balance);
                  if(!accF.name||isNaN(b)){showT("口座名と残高を入力","error");return;}
                  const updated=ts;
                  if(editAccId){
                    // 既存口座の更新（color も保存する）
                    setAccounts((p: AccountWithDate[])=>p.map(a=>a.id===editAccId?{...a,name:accF.name,balance:b,updatedAt:updated,color:accF.color||undefined}:a));
                  }else{
                    // 新規口座を追加（color も保存する）
                    setAccounts((p: AccountWithDate[])=>[...p,{id:newId(),name:accF.name,balance:b,updatedAt:updated,color:accF.color||undefined}]);
                  }
                  setShowAccF(false);setEditAccId(null);setAccF({name:"",balance:"",color:""});showT("保存しました");
                }}
                style={STYLE_BUTTON_PRIMARY}
              >
                保存
              </button>
              <button onClick={()=>{setShowAccF(false);setEditAccId(null);}} style={{...STYLE_BUTTON_OUTLINE,minHeight:44,padding:"11px 18px"}}>
                キャンセル
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ────────── 家計診断カード（5指標で A〜E 評価） ────────── */}
      <HealthCheckCard
        totalIncome={totalIncome}
        totalBurden={totalBurden}
        totalLoanRepayment={totalLoanRepayment}
        totalFixedExpense={totalFixedExpense}
        net={net}
        totalSavings={totalSavings}
        prevNet={prevTInc - prevTVar}
        prevTotalIncome={prevTInc}
      />

      {/* ────────── 貯金目標カード（未設定なら CTA、設定済みなら進捗を表示） ────────── */}
      <SavingGoalCard
        goal={savingGoal}
        setGoal={setSavingGoal}
        accounts={accounts}
        transactions={transactions}
        incomes={incomes}
        transfers={transfers}
        ask={ask}
        showT={showT}
      />

      {/* ────────── 4つの集計ラベル（変動支出・固定費・返済・利息） ────────── */}
      <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:8,marginBottom:12}}>
        <StatLabel label="変動支出" value={formatYen(totalVariableExpense)}/>
        <StatLabel label="固定費" value={formatYen(totalFixedExpense)}/>
        <StatLabel label="返済合計" value={formatYen(totalLoanRepayment)}/>
        <StatLabel label="今月の利息" value={formatYen(allL.reduce((s,l)=>s+calculateMonthlyInterest(l.remaining,l.rate),0))} color={COLOR_NEGATIVE}/>
      </div>

      {/* ────────── 月次収支バランスのプログレスバー ────────── */}
      <div style={STYLE_CARD}>
        <div style={{fontSize:10,color:COLOR_TEXT_HINT,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:14}}>月次収支バランス</div>
        <ProgressBar label="収入" value={totalIncome} max={Math.max(totalIncome,totalBurden)||1} color={COLOR_POSITIVE}/>
        <ProgressBar label="変動支出" value={totalVariableExpense} max={Math.max(totalIncome,totalBurden)||1} color={COLOR_TEXT_SECONDARY}/>
        <ProgressBar label="固定費" value={totalFixedExpense} max={Math.max(totalIncome,totalBurden)||1} color={COLOR_TEXT_SECONDARY}/>
        <ProgressBar label="ローン返済" value={totalLoanRepayment} max={Math.max(totalIncome,totalBurden)||1} color={COLOR_NEGATIVE}/>
      </div>

      {/* ────────── 変動支出カテゴリ別内訳（データがある時だけ表示） ────────── */}
      {expByCat.length>0&&(
        <div style={STYLE_CARD}>
          <div style={{fontSize:10,color:COLOR_TEXT_HINT,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:14}}>変動支出 内訳</div>
          {expByCat.map(([cat,amt])=>(
            <ProgressBar key={cat} label={cat} value={amt} max={expByCat[0][1]||1} color={COLOR_TEXT_SECONDARY} icon={EXPENSE_CATEGORY_ICONS[cat]}/>
          ))}
        </div>
      )}

      {/* ────────── 前月比較カード（前月データがある時だけ表示） ────────── */}
      {(prevTInc>0||prevTVar>0)&&(
        <div style={STYLE_CARD}>
          <div style={{fontSize:10,color:COLOR_TEXT_HINT,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:14}}>前月との比較</div>
          {(([
            {label:"収入",cur:totalIncome,prev:prevTInc,inv:false},
            {label:"変動支出",cur:totalVariableExpense,prev:prevTVar,inv:true},
            {label:"手残り",cur:net,prev:prevTInc-(prevTVar+totalFixedExpense+totalLoanRepayment),inv:false},
          ] as {label:string;cur:number;prev:number;inv:boolean}[]).map(({label,cur,prev,inv})=>{
            const diff=cur-prev;
            const good=diff===0?null:(inv?diff<0:diff>0);
            return (
              <div key={label} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"10px 0",borderBottom:`1px solid ${COLOR_BORDER}`}}>
                <span style={{fontSize:13,color:COLOR_TEXT_SECONDARY}}>{label}</span>
                <div style={{textAlign:"right"}}>
                  <div style={{fontFamily:"monospace",fontSize:14,fontWeight:700}}>{formatYen(cur)}</div>
                  <div style={{fontSize:11,color:good===null?COLOR_TEXT_HINT:good?COLOR_POSITIVE:COLOR_NEGATIVE}}>
                    {diff>=0?"+":""}{formatYen(diff)}
                  </div>
                </div>
              </div>
            );
          }))}
        </div>
      )}

      {/* ────────── 前年同月比カード（去年データがあるときだけ表示） ────────── */}
      {hasYoyData && (
        <div style={STYLE_CARD}>
          <div style={{fontSize:10,color:COLOR_TEXT_HINT,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:14}}>
            前年同月との比較（{selectedYear - 1}年{selectedMonth + 1}月）
          </div>
          {(([
            {label:"収入",cur:totalIncome,prev:prevYearTInc,inv:false},
            {label:"変動支出",cur:totalVariableExpense,prev:prevYearTVar,inv:true},
          ] as {label:string;cur:number;prev:number;inv:boolean}[]).map(({label,cur,prev,inv})=>{
            const diff = cur - prev;
            // ％増減（前年が0の場合は計算しない）
            const pct = prev > 0 ? Math.round((diff / prev) * 100) : null;
            const good = diff === 0 ? null : (inv ? diff < 0 : diff > 0);
            return (
              <div key={label} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"10px 0",borderBottom:`1px solid ${COLOR_BORDER}`}}>
                <span style={{fontSize:13,color:COLOR_TEXT_SECONDARY}}>{label}</span>
                <div style={{textAlign:"right"}}>
                  <div style={{fontFamily:"monospace",fontSize:14,fontWeight:700}}>{formatYen(cur)}</div>
                  <div style={{fontSize:11,color:good===null?COLOR_TEXT_HINT:good?COLOR_POSITIVE:COLOR_NEGATIVE}}>
                    {diff>=0?"+":""}{formatYen(diff)}
                    {pct !== null && <span style={{marginLeft:6,fontFamily:"monospace"}}>({pct>=0?"+":""}{pct}%)</span>}
                  </div>
                </div>
              </div>
            );
          }))}
        </div>
      )}

      {/* ────────── ローン残債一覧カード ────────── */}
      <div style={STYLE_CARD}>
        <div style={{fontSize:10,color:COLOR_TEXT_HINT,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:14,display:"flex",justifyContent:"space-between"}}>
          <span>ローン残債一覧</span><span>{allL.length}件</span>
        </div>
        {allL.map(l=>{
          // 総利息・完済予定日・今月の利息を計算する
          const ti=calculateTotalInterest(l.remaining,l.rate,l.monthly);
          const comp=ti?calculateCompletionDate(ti.months):null;
          const mi=calculateMonthlyInterest(l.remaining,l.rate);
          return (
            <div key={l.id} style={{paddingBottom:12,marginBottom:12,borderBottom:`1px solid ${COLOR_BORDER}`}}>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:5}}>
                <span style={{fontSize:13,fontWeight:600}}>{l.name}</span>
                <span style={{fontFamily:"monospace",fontSize:14,fontWeight:700}}>{formatYen(l.remaining)}</span>
              </div>
              <div style={{display:"flex",gap:12,fontSize:11,color:COLOR_TEXT_HINT,flexWrap:"wrap",marginBottom:4}}>
                <span>月返済 <span style={{fontFamily:"monospace",color:COLOR_TEXT_SECONDARY}}>{formatYen(l.monthly)}</span></span>
                <span>月利息 <span style={{fontFamily:"monospace",color:COLOR_NEGATIVE}}>{formatYen(mi)}</span></span>
                <span style={{fontFamily:"monospace"}}>{l.rate}%</span>
              </div>
              {comp&&(
                <div style={{fontSize:11,color:COLOR_TEXT_HINT}}>
                  完済予定 <span style={{fontFamily:"monospace",color:COLOR_TEXT_PRIMARY,fontWeight:700}}>{comp.y}年{comp.m}月</span>
                  {ti&&<span style={{marginLeft:8}}>総利息 <span style={{fontFamily:"monospace",color:COLOR_NEGATIVE,fontWeight:700}}>{formatYen(ti.interest)}</span></span>}
                </div>
              )}
            </div>
          );
        })}
        {/* 全ローンの支払総利息合計 */}
        <div style={{display:"flex",justifyContent:"space-between"}}>
          <span style={{fontSize:12,color:COLOR_TEXT_HINT}}>全ローン 支払総利息</span>
          <span style={{fontFamily:"monospace",fontSize:14,fontWeight:700,color:COLOR_NEGATIVE}}>
            {formatYen(allL.reduce((s,l)=>{const r=calculateTotalInterest(l.remaining,l.rate,l.monthly);return r?s+r.interest:s;},0))}
          </span>
        </div>
      </div>

      {/* ────────── 振替モーダル ────────── */}
      {showTransfer && (
        <TransferForm
          accounts={accounts}
          onSubmit={transfer => { addTransfer(transfer); setShowTransfer(false); }}
          onCancel={() => setShowTransfer(false)}
        />
      )}

      {/* ────────── 月次推移グラフ（recharts は重いので Suspense で遅延ロード） ────────── */}
      <Suspense fallback={<div style={{...STYLE_CARD,textAlign:"center",color:COLOR_TEXT_HINT,fontSize:12,padding:"40px 0"}}>📊 グラフを読み込み中…</div>}>
        <MonthlyChart tx={transactions} inc={incomes} tFx={totalFixedExpense}/>
        <CategoryTrendChart tx={transactions} icons={EXPENSE_CATEGORY_ICONS}/>
      </Suspense>

      {/* ────────── バックアップ／復元カード ────────── */}
      <div style={STYLE_CARD}>
        <div style={{fontSize:10,color:COLOR_TEXT_HINT,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:10}}>データのバックアップ</div>
        <div style={{fontSize:12,color:COLOR_TEXT_SECONDARY,lineHeight:1.7,marginBottom:14}}>
          家計データをJSONファイルとして保存／復元できます。<br/>
          別端末でも<span style={{color:COLOR_TEXT_PRIMARY,fontWeight:700}}>同じパスワード</span>で復元できます。
        </div>
        <div style={{display:"flex",gap:10}}>
          {/* バックアップ：暗号化済みのlocalStorageを丸ごと書き出す */}
          <button onClick={exportBackup} style={{...STYLE_BUTTON_PRIMARY,flex:1}}>📥 バックアップ</button>
          {/* 復元：隠しinputを開いてファイル選択ダイアログを表示 */}
          <button
            onClick={()=>fileInputRef.current?.click()}
            style={{...STYLE_BUTTON_OUTLINE,flex:1,minHeight:44,padding:"11px 18px",textAlign:"center"}}
          >
            📤 復元
          </button>
        </div>
        {/* 画面には出さない隠しファイル入力。選んだJSONをimportBackupへ渡す */}
        <input
          ref={fileInputRef}
          type="file"
          accept="application/json,.json"
          onChange={e=>{const f=e.target.files?.[0];if(f)importBackup(f);e.target.value="";}}
          style={{display:"none"}}
        />
      </div>
      </> /* ────── 月次ビューここまで ────── */}
    </div>
  );
}
