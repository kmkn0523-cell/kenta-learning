// ────────── 支出タブ ビューコンポーネント ──────────
// 変動支出の入力フォーム・クイックテンプレート・予算管理・月別一覧をまとめたコンポーネント
// App.tsx から切り出して、見通しを良くしている

import React, { useMemo, useState, useRef, useCallback, CSSProperties } from "react";
import { Tx, Budget, CategoryConfig, Account, RecurringExpense } from "../types";
import { newId } from "../utils/crypto";
import CsvImportModal, { ImportedRow } from "../components/CsvImportModal";
import {
  parseYenAmount,
  formatYen,
  MONTH_LABELS,
} from "../utils/format";
import {
  COLOR_BACKGROUND,
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_SECONDARY,
  COLOR_TEXT_HINT,
  COLOR_BORDER,
  COLOR_ACCENT,
  COLOR_SURFACE,
  STYLE_CARD,
  STYLE_BUTTON_PRIMARY,
  STYLE_BUTTON_OUTLINE,
} from "../utils/styles";
import { filterAndSortTransactions, TransactionFilter } from "../utils/filterTransactions";
import { Input, Select } from "../components/ui";
import TxRow from "../components/TxRow";
import BudgetSection from "../components/BudgetSection";
import WeeklyBreakdown from "../components/WeeklyBreakdown";
import DayOfWeekBreakdown from "../components/DayOfWeekBreakdown";
import MonthNav from "../components/MonthNav";
import SubscriptionInventory from "../components/SubscriptionInventory";

// ── スタイル定数 ──────────────────────────────────────────

// クイックテンプレートカードの静的スタイル
const STYLE_EX_TPL_CARD: CSSProperties = {
  flexShrink: 0, background: "rgba(148,163,184,0.06)", border: `1px solid ${COLOR_BORDER}`,
  borderRadius: 12, padding: "10px 30px 10px 14px", cursor: "pointer",
  position: "relative", minWidth: 100,
};

// テンプレートカード内「✕」削除ボタンの静的スタイル
const STYLE_EX_TPL_DEL_BTN: CSSProperties = {
  position: "absolute", top: 6, right: 8, background: "none", border: "none",
  color: COLOR_TEXT_HINT, cursor: "pointer", fontSize: 13, padding: 2, lineHeight: 1,
};

// 口座選択セレクトボックスの静的スタイル（color は口座選択状態で動的に上書き）
const STYLE_EX_ACCOUNT_SELECT: CSSProperties = {
  width: "100%", background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 10, fontSize: 14, padding: "12px 14px", fontFamily: "inherit",
  appearance: "none", WebkitAppearance: "none",
};

// ─────────────────────────────────────────────────────────

// クイックテンプレートの形（id・カテゴリ・金額・メモ）
interface Template {
  id: string;
  cat: string;
  amount: number;
  note: string;
}

// このコンポーネントが受け取るプロパティの型定義
interface ExpenseViewProps {
  // テンプレート一覧と更新関数
  tpls: Template[];
  setTpls: (u: Template[] | ((prev: Template[]) => Template[])) => void;
  // 今日の日付文字列（"YYYY-MM-DD"）。入力フォームの初期日付に使う
  ts: string;
  // 口座一覧（口座が登録されていれば支出に紐づける選択肢を表示する）
  accounts?: Account[];
  // 支出追加フォームの表示フラグ
  showTxForm: boolean;
  setShowTxForm: (v: boolean) => void;
  // 支出を追加する関数（フォーム内容を渡す。成功時 true、失敗時 false を返す）
  addTx: (form: { cat: string; amt: string; date: string; memo: string; accountId?: string }) => boolean;
  // カテゴリ別予算と更新関数
  budget: Budget;
  setBudget: (u: Budget | ((prev: Budget) => Budget)) => void;
  // 使いすぎ通知の設定（任意。予算の下に通知設定カードを出すため BudgetSection に渡す）
  notifySettings?: {
    enabled: boolean;
    onToggle: (value: boolean) => void;
    permission: NotificationPermission | "unsupported";
    onRequestPermission: () => void;
  };
  // 表示中の月の支出一覧
  monthlyTransactions: Tx[];
  // 前月の支出一覧（カテゴリ別前月比バッジに使う）
  prevMonthlyTransactions?: Tx[];
  // 全期間の支出一覧（メモ候補の集計に使う。同カテゴリで過去に使ったメモを提案する）
  allTransactions?: Tx[];
  // 選択中の年月
  selectedYear: number;
  selectedMonth: number;
  // 月を変更したときのコールバック
  onMonthChange: (y: number, m: number) => void;
  // その月の変動支出合計
  totalVariableExpense: number;
  // CSVエクスポート関数（ラベル文字列を渡す）
  exportMonthlyCsv: (label: string) => void;
  // 全支出一覧の更新関数（編集・削除に使う）
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  setTransactions: (u: any) => void;
  // トースト通知を出す関数
  showT: (msg: string, type?: string) => void;
  // 確認ダイアログを出す関数
  ask: (title: string, msg: string, ok: () => void) => void;
  // 支出一覧の先頭要素へのref（スクロール用）
  txListRef: React.RefObject<HTMLDivElement | null>;
  // カテゴリ設定（動的にカテゴリ名・アイコンを取得するために使う）
  categoryConfig: CategoryConfig;
  // 削除＋Undo：即削除してToastに「元に戻す」を出す
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  delItem: (id: string, setArr: (u: any) => void, label?: string) => void;
  // 繰り返し支出の設定一覧（毎月自動追加するサブスク等を登録する）
  recurringExpenses: RecurringExpense[];
  // 繰り返し支出の設定を更新する関数
  setRecurringExpenses: (u: RecurringExpense[] | ((prev: RecurringExpense[]) => RecurringExpense[])) => void;
}

// 支出タブ全体を表示するコンポーネント
export default function ExpenseView({
  tpls,
  setTpls,
  ts,
  showTxForm,
  setShowTxForm,
  addTx,
  budget,
  setBudget,
  notifySettings,
  monthlyTransactions,
  prevMonthlyTransactions = [],
  allTransactions = [],
  selectedYear,
  selectedMonth,
  onMonthChange,
  totalVariableExpense,
  exportMonthlyCsv,
  setTransactions,
  showT,
  ask,
  txListRef,
  categoryConfig,
  delItem,
  accounts = [],
  recurringExpenses,
  setRecurringExpenses,
}: ExpenseViewProps) {
  // categoryConfig.expense を order 順で並べ、カテゴリ名とアイコンのマップを作る
  // （useMemo で参照を安定させ、下の TxRow の memo を効かせる）
  const expenseCategoryNames = useMemo(
    () => categoryConfig.expense.slice().sort((a, b) => a.order - b.order).map(c => c.name),
    [categoryConfig.expense]
  );
  const expenseCategoryIcons = useMemo<Record<string, string>>(
    () => Object.fromEntries(categoryConfig.expense.map(c => [c.name, c.icon])),
    [categoryConfig.expense]
  );

  // 支出入力フォームの中身（App.tsx から降格したローカルstate）。タイピングはこの View 内で完結し、App 全体を再レンダしない。
  const [txF, setTxF] = useState<{ cat: string; amt: string; date: string; memo: string; accountId?: string }>(
    { cat: "食費", amt: "", date: ts, memo: "" }
  );

  // 一覧の各行に渡す保存／削除ハンドラ。useCallback で参照を固定し、TxRow の memo を効かせる（タイピングで全行が再描画されるのを防ぐ）。
  const handleSaveTx = useCallback((updated: { id: string; category: string; amount: number; date: string; memo?: string }) => {
    // 既存レコードに編集後の値を重ねる（accountId など編集対象外のフィールドは保持）
    setTransactions((prev: Tx[]) => prev.map(x => x.id === updated.id ? { ...x, ...updated } : x));
    showT("更新しました");
  }, [setTransactions, showT]);
  const handleDeleteTx = useCallback((item?: { id: string }) => {
    if (item) delItem(item.id, setTransactions, "支出を削除しました");
  }, [delItem, setTransactions]);

  // ────── ⚡定期支出セクションの state ──────
  // 定期支出セクションを開いているかどうか（アコーディオン）
  const [showRecSection, setShowRecSection] = useState(false);
  // 定期支出の追加フォームを表示するかどうか
  const [showRecForm, setShowRecForm] = useState(false);
  // 定期支出フォームの入力値
  const [recExpF, setRecExpF] = useState({
    name: "",
    cat: expenseCategoryNames[0] || "食費",
    amt: "",
    payDay: "未設定",
  });
  // 引落日の選択肢（1〜31日 + 未設定）
  const PAY_DAY_OPTIONS = ["未設定", ...Array.from({length: 31}, (_, i) => `${i + 1}日`)];

  // 検索・絞り込み条件をまとめた state
  const [filter, setFilter] = useState<TransactionFilter>({});
  // フィルターパネルの表示フラグ
  const [showFilter, setShowFilter] = useState(false);
  // 金額入力欄への参照：連続入力時に追加成功後の再フォーカスに使う
  const amountInputRef = useRef<HTMLInputElement>(null);
  // CSVインポートモーダルの表示フラグ
  const [showCsvModal, setShowCsvModal] = useState(false);

  // フィルター・並び替えを適用した支出一覧（monthlyTransactions が変わったらリセット）
  const filteredTransactions = useMemo(
    () => filterAndSortTransactions(monthlyTransactions, filter),
    [monthlyTransactions, filter]
  );

  // この月に登場するカテゴリだけを抽出（カテゴリフィルターボタンの表示に使う）
  const categories = useMemo(
    () => expenseCategoryNames.filter(c => monthlyTransactions.some(t => t.category === c)),
    [monthlyTransactions]
  );

  // メモ候補：選択中カテゴリ(txF.cat)で過去によく使ったメモを頻度順に最大4件提案する（店名などの再入力を省く）
  const memoSuggestions = useMemo(() => {
    const counts = new Map<string, number>();
    for (const t of allTransactions) {
      if (t.category === txF.cat && t.memo) counts.set(t.memo, (counts.get(t.memo) || 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4).map(([memo]) => memo);
  }, [allTransactions, txF.cat]);

  return (
    <div>
      {/* ──────────────────────────────────────────── */}
      {/* ── ⚡定期支出セクション（サブスク・ジム代等） ── */}
      {/* ──────────────────────────────────────────── */}
      <div style={STYLE_CARD}>
        {/* セクションヘッダー（タップで開閉） */}
        <div
          style={{display:"flex",justifyContent:"space-between",alignItems:"center",cursor:"pointer"}}
          onClick={() => setShowRecSection(v => !v)}
        >
          <div style={{fontSize:12,color:COLOR_TEXT_HINT,textTransform:"uppercase",letterSpacing:"1.5px"}}>
            ⚡ 定期支出
            {/* 登録件数バッジ */}
            {recurringExpenses.length > 0 && (
              <span style={{marginLeft:8,fontSize:12,color:COLOR_ACCENT,fontFamily:"monospace"}}>
                {recurringExpenses.length}件
              </span>
            )}
          </div>
          <span style={{fontSize:12,color:COLOR_TEXT_HINT}}>{showRecSection ? "▲" : "▼"}</span>
        </div>

        {/* 開いたときだけ中身を表示（アコーディオン） */}
        {showRecSection && (
          <div style={{marginTop:14}}>
            {/* 定期支出の一覧 */}
            {recurringExpenses.length === 0 ? (
              <div style={{textAlign:"center",padding:"12px 0",color:COLOR_TEXT_HINT,fontSize:13}}>
                まだ登録された定期支出はありません
              </div>
            ) : (
              recurringExpenses.map(rec => (
                <div
                  key={rec.id}
                  style={{display:"flex",alignItems:"center",gap:10,padding:"10px 0",borderBottom:`1px solid ${COLOR_BORDER}`}}
                >
                  <div style={{flex:1,minWidth:0}}>
                    {/* 停止中はグレーで表示 */}
                    <div style={{fontSize:13,fontWeight:600,color:rec.active===false?COLOR_TEXT_HINT:COLOR_TEXT_PRIMARY}}>
                      {rec.active===false && "⏸ "}{rec.name}
                    </div>
                    <div style={{fontSize:12,color:COLOR_TEXT_SECONDARY,marginTop:2}}>
                      {expenseCategoryIcons[rec.category]} {rec.category} · {rec.payDay} · {formatYen(rec.amount)}/月
                    </div>
                  </div>
                  {/* 有効/停止の切り替えボタン */}
                  <button type="button"
                    onClick={() =>
                      setRecurringExpenses(prev =>
                        prev.map(r => r.id === rec.id ? {...r, active: r.active === false ? true : false} : r)
                      )
                    }
                    style={{
                      ...STYLE_BUTTON_OUTLINE,
                      fontSize:12,
                      padding:"4px 10px",
                      minHeight:30,
                      color: rec.active===false ? COLOR_TEXT_HINT : COLOR_ACCENT,
                      borderColor: rec.active===false ? COLOR_BORDER : `${COLOR_ACCENT}44`,
                    }}
                  >
                    {rec.active===false ? "再開" : "停止"}
                  </button>
                  {/* 削除ボタン */}
                  <button type="button"
                    onClick={() => delItem(rec.id, setRecurringExpenses, "定期支出を削除しました")}
                    style={{...STYLE_BUTTON_OUTLINE,fontSize:12,padding:"4px 10px",minHeight:30}}
                  >
                    削除
                  </button>
                </div>
              ))
            )}

            {/* 定期支出の追加フォームの開閉ボタン */}
            <button type="button"
              onClick={() => setShowRecForm(v => !v)}
              style={{...STYLE_BUTTON_OUTLINE,width:"100%",marginTop:10,fontSize:12}}
            >
              {showRecForm ? "閉じる" : "＋ 定期支出を追加"}
            </button>

            {/* 追加フォーム本体 */}
            {showRecForm && (
              <div style={{marginTop:10,display:"flex",flexDirection:"column",gap:10}}>
                {/* 支出名 */}
                <Input
                  value={recExpF.name}
                  onChange={e => setRecExpF(f => ({...f, name: e.target.value}))}
                  placeholder="支出名（例: Netflix、ジム会費）"
                />
                {/* カテゴリ */}
                <Select
                  value={recExpF.cat}
                  onChange={e => setRecExpF(f => ({...f, cat: e.target.value}))}
                  options={expenseCategoryNames}
                  icons={expenseCategoryIcons}
                />
                {/* 金額 */}
                <Input
                  money
                  type="number"
                  value={recExpF.amt}
                  onChange={e => setRecExpF(f => ({...f, amt: e.target.value}))}
                  placeholder="金額（円）"
                />
                {/* 引落日 */}
                <Select
                  value={recExpF.payDay}
                  onChange={e => setRecExpF(f => ({...f, payDay: e.target.value}))}
                  options={PAY_DAY_OPTIONS}
                />
                {/* 登録ボタン */}
                <button type="button"
                  onClick={() => {
                    const a = parseYenAmount(recExpF.amt);
                    if (!recExpF.name) { showT("支出名を入力してください", "error"); return; }
                    if (!a || a <= 0) { showT("金額を入力してください", "error"); return; }
                    setRecurringExpenses(prev => [
                      ...prev,
                      {
                        id: newId(),
                        name: recExpF.name,
                        category: recExpF.cat,
                        amount: a,
                        payDay: recExpF.payDay,
                        active: true,
                      }
                    ]);
                    // フォームをリセットして閉じる
                    setRecExpF({name:"", cat: expenseCategoryNames[0] || "食費", amt:"", payDay:"未設定"});
                    setShowRecForm(false);
                    showT("定期支出を登録しました");
                  }}
                  style={STYLE_BUTTON_PRIMARY}
                >
                  登録する
                </button>
                {/* 注意書き */}
                <div style={{fontSize:12,color:COLOR_TEXT_HINT,lineHeight:1.6}}>
                  ※ 引落日が来た月から自動的に変動支出として追加されます。
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ────────── サブスク棚卸し（年間コストで見える化・登録があるときだけ表示） ────────── */}
      <SubscriptionInventory recurringExpenses={recurringExpenses} icons={expenseCategoryIcons} />

      {/* ────────── クイックテンプレート一覧 ────────── */}
      {tpls.length>0&&<div style={{marginBottom:12}}>
        <div style={{fontSize:12,color:COLOR_TEXT_HINT,letterSpacing:"1.5px",textTransform:"uppercase",marginBottom:8}}>よく使う支出</div>
        <div style={{display:"flex",gap:8,overflowX:"auto",paddingBottom:4,WebkitOverflowScrolling:"touch" as any}}>
          {tpls.map(tp=>(
            <div key={tp.id} onClick={()=>{setTxF(f=>({...f,cat:tp.cat,amt:String(tp.amount),memo:tp.note}));setShowTxForm(true);}} style={STYLE_EX_TPL_CARD}>
              <div style={{fontSize:12,fontWeight:600,color:COLOR_TEXT_SECONDARY}}>{expenseCategoryIcons[tp.cat]} {tp.cat}</div>
              <div style={{fontFamily:"monospace",fontSize:14,fontWeight:700,marginTop:2}}>{formatYen(tp.amount)}</div>
              {tp.note&&<div style={{fontSize:12,color:COLOR_TEXT_HINT,marginTop:2,maxWidth:80,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{tp.note}</div>}
              <button type="button" onClick={e=>{e.stopPropagation();delItem(tp.id,setTpls,"テンプレートを削除しました");}} style={STYLE_EX_TPL_DEL_BTN}>✕</button>
            </div>
          ))}
        </div>
      </div>}
      {/* ────────── 支出追加ボタン or 入力フォーム ────────── */}
      {!showTxForm
        ? <button type="button" onClick={()=>setShowTxForm(true)} style={{...STYLE_BUTTON_PRIMARY,marginBottom:12}}>＋ 支出を追加</button>
        : <div style={STYLE_CARD}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:14}}>
              <div style={{fontSize:12,color:COLOR_TEXT_HINT,textTransform:"uppercase",letterSpacing:"1.5px"}}>変動支出を入力</div>
              <button type="button" onClick={()=>setShowTxForm(false)} style={{...STYLE_BUTTON_OUTLINE,fontSize:12,padding:"4px 10px",minHeight:30}}>✕ 閉じる</button>
            </div>
            <div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:12}}>
              <Select value={txF.cat} onChange={e=>setTxF(f=>({...f,cat:e.target.value}))} options={expenseCategoryNames} icons={expenseCategoryIcons}/>
              <Input ref={amountInputRef} money type="number" value={txF.amt} onChange={e=>setTxF(f=>({...f,amt:e.target.value}))} placeholder="金額（円）"/>
              <Input type="date" value={txF.date} onChange={e=>setTxF(f=>({...f,date:e.target.value}))}/>
              <Input value={txF.memo} onChange={e=>setTxF(f=>({...f,memo:e.target.value}))} placeholder="メモ（任意）"/>
              {/* よく使うメモの候補（同カテゴリの過去メモをタップで入力。再入力の手間を省く） */}
              {memoSuggestions.length > 0 && (
                <div style={{display:"flex",flexWrap:"wrap",gap:6}}>
                  {memoSuggestions.map(m => (
                    <button type="button" key={m} onClick={()=>setTxF(f=>({...f,memo:m}))}
                      style={{padding:"4px 10px",borderRadius:999,border:`1px solid ${COLOR_BORDER}`,background:"transparent",color:COLOR_TEXT_SECONDARY,fontSize:13,cursor:"pointer",fontFamily:"inherit",maxWidth:"100%",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                      {m}
                    </button>
                  ))}
                </div>
              )}
              {/* 口座が登録されている時だけ「どの口座から引き落とすか」を選べる */}
              {accounts.length > 0 && (
                <select
                  value={txF.accountId || ""}
                  onChange={e => setTxF(f => ({ ...f, accountId: e.target.value || undefined }))}
                  style={{
                    ...STYLE_EX_ACCOUNT_SELECT,
                    color: txF.accountId ? "#e2e8f0" : "#64748b",
                  }}
                >
                  {/* 空欄＝口座指定なし */}
                  <option value="">🏦 口座を選択（任意）</option>
                  {accounts.map(acc => (
                    <option key={acc.id} value={acc.id}>{acc.name}</option>
                  ))}
                </select>
              )}
            </div>
            {/* テンプレートとして保存するボタン（金額が入力済みの時だけ有効） */}
            <button type="button" onClick={()=>{
              const a=parseYenAmount(txF.amt);
              if(!a||a<=0){showT("金額を入力してから保存","error");return;}
              if(tpls.some(t=>t.cat===txF.cat&&Number(t.amount)===a&&t.note===(txF.memo||""))){showT("同じパターンが既に保存されています");return;}
              setTpls(p=>[...p,{id:newId(),cat:txF.cat,amount:a,note:txF.memo||""}]);
              showT("テンプレートに保存しました");
            }} style={{...STYLE_BUTTON_OUTLINE,width:"100%",marginBottom:10,fontSize:12}}>⭐ テンプレートとして保存</button>
            {/* 追加後は金額・メモ・口座をクリアし、金額入力欄に再フォーカスして連続入力をスムーズにする */}
            <button type="button" onClick={()=>{if(addTx(txF)){setTxF(f=>({...f,amt:"",memo:"",accountId:undefined}));setTimeout(()=>amountInputRef.current?.focus(),50);}}} style={STYLE_BUTTON_PRIMARY}>追加</button>
          </div>
      }
      {/* ────────── 予算管理：カテゴリ別の月予算を設定・追跡 ────────── */}
      <BudgetSection budget={budget} setBudget={setBudget} mTx={monthlyTransactions} prevMTx={prevMonthlyTransactions} notifySettings={notifySettings}/>
      {/* ────────── 週別支出内訳 ────────── */}
      <WeeklyBreakdown mTx={monthlyTransactions} selectedYear={selectedYear} selectedMonth={selectedMonth}/>
      {/* ────────── 曜日別支出内訳 ────────── */}
      <DayOfWeekBreakdown mTx={monthlyTransactions}/>
      {/* ────────── 月ナビと合計金額 ────────── */}
      <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:4}}>
        <div style={{flex:1}}>
          <MonthNav selectedYear={selectedYear} selectedMonth={selectedMonth} onChange={onMonthChange}/>
        </div>
        <span style={{fontFamily:"monospace",fontSize:14,fontWeight:700,marginLeft:4}}>{formatYen(totalVariableExpense)}</span>
      </div>
      {/* ────────── CSV出力・インポートボタン ────────── */}
      <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
        {/* CSV出力：支出が1件以上あるときだけ表示 */}
        {monthlyTransactions.length > 0 && (
          <button type="button"
            onClick={() => exportMonthlyCsv(`${selectedYear}年${MONTH_LABELS[selectedMonth]}`)}
            style={{ ...STYLE_BUTTON_OUTLINE, flex: 1, fontSize: 12 }}
          >
            📤 CSV出力
          </button>
        )}
        {/* CSVインポート：常に表示（銀行CSVを一括取り込みする） */}
        <button type="button"
          onClick={() => setShowCsvModal(true)}
          style={{ ...STYLE_BUTTON_OUTLINE, flex: 1, fontSize: 12 }}
        >
          📥 CSVインポート
        </button>
      </div>

      {/* CSVインポートモーダル（showCsvModal が true のときだけ表示） */}
      {showCsvModal && (
        <CsvImportModal
          mode="expense"
          categoryConfig={categoryConfig}
          onImport={(rows: ImportedRow[]) => {
            // インポートされた行を変動支出として一括追加する
            setTransactions((prev: Tx[]) => [
              ...prev,
              ...rows.map(r => ({
                id: r.id,
                date: r.date,
                category: r.category,
                amount: r.amount,
                memo: r.memo,
                accountId: r.accountId,
              } as Tx)),
            ]);
            showT(`${rows.length}件の支出をインポートしました`);
            setShowCsvModal(false);
          }}
          onClose={() => setShowCsvModal(false)}
        />
      )}

      {/* ────────── 検索バー ────────── */}
      {monthlyTransactions.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          {/* キーワード入力と「絞り込み」ボタンを横に並べる */}
          <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
            <Input
              value={filter.text || ""}
              onChange={e => setFilter(f => ({ ...f, text: e.target.value || undefined }))}
              placeholder="キーワード検索（メモ・カテゴリ）"
            />
            <button type="button"
              onClick={() => setShowFilter(f => !f)}
              style={{
                ...STYLE_BUTTON_OUTLINE,
                padding: "0 14px",
                whiteSpace: "nowrap",
                background: showFilter ? COLOR_ACCENT : undefined,
                color: showFilter ? "#fff" : undefined,
              }}
            >
              絞り込み
            </button>
          </div>

          {/* フィルターパネル（「絞り込み」ボタンを押したときだけ表示） */}
          {showFilter && (
            <div style={{ background: COLOR_SURFACE, borderRadius: 10, padding: 14, marginBottom: 12 }}>
              {/* カテゴリ選択 */}
              <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginBottom: 6 }}>カテゴリ</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
                {categories.map(cat => {
                  const checked = (filter.categories || []).includes(cat);
                  return (
                    <button type="button"
                      key={cat}
                      onClick={() => setFilter(f => {
                        const prev = f.categories || [];
                        return {
                          ...f,
                          categories: checked ? prev.filter(c => c !== cat) : [...prev, cat],
                        };
                      })}
                      style={{
                        padding: "4px 10px",
                        borderRadius: 999,
                        border: `1px solid ${checked ? COLOR_ACCENT : COLOR_BORDER}`,
                        background: checked ? COLOR_ACCENT : "transparent",
                        color: checked ? "#fff" : COLOR_TEXT_PRIMARY,
                        fontSize: 13,
                        cursor: "pointer",
                      }}
                    >
                      {cat}
                    </button>
                  );
                })}
              </div>

              {/* 日付範囲 */}
              <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginBottom: 6 }}>日付</div>
              <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                <Input
                  type="date"
                  value={filter.dateFrom || ""}
                  onChange={e => setFilter(f => ({ ...f, dateFrom: e.target.value || undefined }))}
                />
                <span style={{ color: COLOR_TEXT_SECONDARY, alignSelf: "center" }}>〜</span>
                <Input
                  type="date"
                  value={filter.dateTo || ""}
                  onChange={e => setFilter(f => ({ ...f, dateTo: e.target.value || undefined }))}
                />
              </div>

              {/* 金額範囲 */}
              <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginBottom: 6 }}>金額</div>
              <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                <Input
                  money
                  placeholder="下限"
                  value={filter.amountMin !== undefined ? String(filter.amountMin) : ""}
                  onChange={e => setFilter(f => ({ ...f, amountMin: e.target.value ? Number(e.target.value) : undefined }))}
                />
                <span style={{ color: COLOR_TEXT_SECONDARY, alignSelf: "center" }}>〜</span>
                <Input
                  money
                  placeholder="上限"
                  value={filter.amountMax !== undefined ? String(filter.amountMax) : ""}
                  onChange={e => setFilter(f => ({ ...f, amountMax: e.target.value ? Number(e.target.value) : undefined }))}
                />
              </div>

              {/* ソート選択 */}
              <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginBottom: 6 }}>並び替え</div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {(["date", "amount"] as const).map(by => (
                  (["desc", "asc"] as const).map(dir => {
                    const label = by === "date"
                      ? (dir === "desc" ? "日付 新しい順" : "日付 古い順")
                      : (dir === "desc" ? "金額 高い順" : "金額 低い順");
                    const active = filter.sortBy === by && filter.sortDir === dir;
                    return (
                      <button type="button"
                        key={`${by}-${dir}`}
                        onClick={() => setFilter(f => ({ ...f, sortBy: by, sortDir: dir }))}
                        style={{
                          padding: "4px 10px",
                          borderRadius: 999,
                          border: `1px solid ${active ? COLOR_ACCENT : COLOR_BORDER}`,
                          background: active ? COLOR_ACCENT : "transparent",
                          color: active ? "#fff" : COLOR_TEXT_PRIMARY,
                          fontSize: 13,
                          cursor: "pointer",
                        }}
                      >
                        {label}
                      </button>
                    );
                  })
                ))}
                {/* ソートのリセットボタン（ソートが設定されているときだけ表示） */}
                {filter.sortBy && (
                  <button type="button"
                    onClick={() => setFilter(f => ({ ...f, sortBy: undefined, sortDir: undefined }))}
                    style={{
                      padding: "4px 10px",
                      borderRadius: 999,
                      border: `1px solid ${COLOR_BORDER}`,
                      background: "transparent",
                      color: COLOR_TEXT_SECONDARY,
                      fontSize: 13,
                      cursor: "pointer",
                    }}
                  >
                    リセット
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ────────── スクロール位置のアンカー ────────── */}
      <div ref={txListRef}/>
      {/* ────────── 支出一覧（空の場合・検索ゼロの場合・通常表示） ────────── */}
      {monthlyTransactions.length===0
        ? <div style={{textAlign:"center",padding:"44px 0",color:COLOR_TEXT_HINT}}>
            <div style={{fontSize:36,marginBottom:10}}>💸</div>
            <div>この月の支出はありません</div>
            <div style={{fontSize:12,marginTop:8}}>「＋ 支出を追加」から記録してみましょう</div>
          </div>
        : filteredTransactions.length===0
          ? <div style={{textAlign:"center",padding:"44px 0",color:COLOR_TEXT_HINT}}>🔍 該当なし</div>
          : filteredTransactions.map(t=>(
              <TxRow
                key={t.id}
                item={t}
                cats={expenseCategoryNames}
                ico={expenseCategoryIcons}
                onSave={handleSaveTx}
                onDelete={handleDeleteTx}
              />
            ))
      }
    </div>
  );
}
