// ────────── 支出タブ ビューコンポーネント ──────────
// 変動支出の入力フォーム・クイックテンプレート・予算管理・月別一覧をまとめたコンポーネント
// App.tsx から切り出して、見通しを良くしている

import React, { useMemo, useState, useRef } from "react";
import { Tx, Budget, CategoryConfig } from "../types";
import { newId } from "../utils/crypto";
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
import MonthNav from "../components/MonthNav";

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
  // 支出入力フォームの中身（カテゴリ・金額・日付・メモ）
  txF: { cat: string; amt: string; date: string; memo: string };
  setTxF: (u: ((prev: { cat: string; amt: string; date: string; memo: string }) => { cat: string; amt: string; date: string; memo: string })) => void;
  // 支出追加フォームの表示フラグ
  showTxForm: boolean;
  setShowTxForm: (v: boolean) => void;
  // 支出を追加する関数（成功時 true、失敗時 false を返す）
  addTx: () => boolean;
  // カテゴリ別予算と更新関数
  budget: Budget;
  setBudget: (u: Budget | ((prev: Budget) => Budget)) => void;
  // 表示中の月の支出一覧
  monthlyTransactions: Tx[];
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
}

// 支出タブ全体を表示するコンポーネント
export default function ExpenseView({
  tpls,
  setTpls,
  txF,
  setTxF,
  showTxForm,
  setShowTxForm,
  addTx,
  budget,
  setBudget,
  monthlyTransactions,
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
}: ExpenseViewProps) {
  // categoryConfig.expense を order 順で並べ、カテゴリ名とアイコンのマップを作る
  const expenseCategoryNames = categoryConfig.expense.slice().sort((a, b) => a.order - b.order).map(c => c.name);
  const expenseCategoryIcons: Record<string, string> = Object.fromEntries(categoryConfig.expense.map(c => [c.name, c.icon]));
  // 検索・絞り込み条件をまとめた state
  const [filter, setFilter] = useState<TransactionFilter>({});
  // フィルターパネルの表示フラグ
  const [showFilter, setShowFilter] = useState(false);
  // 金額入力欄への参照：連続入力時に追加成功後の再フォーカスに使う
  const amountInputRef = useRef<HTMLInputElement>(null);

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

  return (
    <div>
      {/* ────────── クイックテンプレート一覧 ────────── */}
      {tpls.length>0&&<div style={{marginBottom:12}}>
        <div style={{fontSize:10,color:COLOR_TEXT_HINT,letterSpacing:"1.5px",textTransform:"uppercase",marginBottom:8}}>よく使う支出</div>
        <div style={{display:"flex",gap:8,overflowX:"auto",paddingBottom:4,WebkitOverflowScrolling:"touch" as any}}>
          {tpls.map(tp=>(
            <div key={tp.id} onClick={()=>{setTxF(f=>({...f,cat:tp.cat,amt:String(tp.amount),memo:tp.note}));setShowTxForm(true);}} style={{flexShrink:0,background:"rgba(148,163,184,0.06)",border:`1px solid ${COLOR_BORDER}`,borderRadius:12,padding:"10px 30px 10px 14px",cursor:"pointer",position:"relative",minWidth:100}}>
              <div style={{fontSize:12,fontWeight:600,color:COLOR_TEXT_SECONDARY}}>{expenseCategoryIcons[tp.cat]} {tp.cat}</div>
              <div style={{fontFamily:"monospace",fontSize:14,fontWeight:700,marginTop:2}}>{formatYen(tp.amount)}</div>
              {tp.note&&<div style={{fontSize:10,color:COLOR_TEXT_HINT,marginTop:2,maxWidth:80,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{tp.note}</div>}
              <button onClick={e=>{e.stopPropagation();delItem(tp.id,setTpls,"テンプレートを削除しました");}} style={{position:"absolute",top:6,right:8,background:"none",border:"none",color:COLOR_TEXT_HINT,cursor:"pointer",fontSize:13,padding:2,lineHeight:1}}>✕</button>
            </div>
          ))}
        </div>
      </div>}
      {/* ────────── 支出追加ボタン or 入力フォーム ────────── */}
      {!showTxForm
        ? <button onClick={()=>setShowTxForm(true)} style={{...STYLE_BUTTON_PRIMARY,marginBottom:12}}>＋ 支出を追加</button>
        : <div style={STYLE_CARD}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:14}}>
              <div style={{fontSize:10,color:COLOR_TEXT_HINT,textTransform:"uppercase",letterSpacing:"1.5px"}}>変動支出を入力</div>
              <button onClick={()=>setShowTxForm(false)} style={{...STYLE_BUTTON_OUTLINE,fontSize:12,padding:"4px 10px",minHeight:30}}>✕ 閉じる</button>
            </div>
            <div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:12}}>
              <Select value={txF.cat} onChange={e=>setTxF(f=>({...f,cat:e.target.value}))} options={expenseCategoryNames} icons={expenseCategoryIcons}/>
              <Input ref={amountInputRef} money type="number" value={txF.amt} onChange={e=>setTxF(f=>({...f,amt:e.target.value}))} placeholder="金額（円）"/>
              <Input type="date" value={txF.date} onChange={e=>setTxF(f=>({...f,date:e.target.value}))}/>
              <Input value={txF.memo} onChange={e=>setTxF(f=>({...f,memo:e.target.value}))} placeholder="メモ（任意）"/>
            </div>
            {/* テンプレートとして保存するボタン（金額が入力済みの時だけ有効） */}
            <button onClick={()=>{
              const a=parseYenAmount(txF.amt);
              if(!a||a<=0){showT("金額を入力してから保存","error");return;}
              if(tpls.some(t=>t.cat===txF.cat&&Number(t.amount)===a&&t.note===(txF.memo||""))){showT("同じパターンが既に保存されています");return;}
              setTpls(p=>[...p,{id:newId(),cat:txF.cat,amount:a,note:txF.memo||""}]);
              showT("テンプレートに保存しました");
            }} style={{...STYLE_BUTTON_OUTLINE,width:"100%",marginBottom:10,fontSize:12}}>⭐ テンプレートとして保存</button>
            {/* 追加後は金額入力欄に再フォーカスして連続入力をスムーズにする */}
            <button onClick={()=>{if(addTx()) setTimeout(()=>amountInputRef.current?.focus(),50);}} style={STYLE_BUTTON_PRIMARY}>追加</button>
          </div>
      }
      {/* ────────── 予算管理：カテゴリ別の月予算を設定・追跡 ────────── */}
      <BudgetSection budget={budget} setBudget={setBudget} mTx={monthlyTransactions}/>
      {/* ────────── 月ナビと合計金額 ────────── */}
      <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:4}}>
        <div style={{flex:1}}>
          <MonthNav selectedYear={selectedYear} selectedMonth={selectedMonth} onChange={onMonthChange}/>
        </div>
        <span style={{fontFamily:"monospace",fontSize:14,fontWeight:700,marginLeft:4}}>{formatYen(totalVariableExpense)}</span>
      </div>
      {/* ────────── CSV出力ボタン（支出がある月だけ表示） ────────── */}
      {monthlyTransactions.length>0&&<button onClick={() => exportMonthlyCsv(`${selectedYear}年${MONTH_LABELS[selectedMonth]}`)} style={{...STYLE_BUTTON_OUTLINE,width:"100%",marginBottom:10,fontSize:12}}>📥 CSV出力</button>}

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
            <button
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
                    <button
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
                      <button
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
                  <button
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
                onSave={u=>{setTransactions(p=>p.map(x=>x.id===u.id?u:x));showT("更新しました");}}
                onDelete={()=>delItem(t.id,setTransactions,"支出を削除しました")}
              />
            ))
      }
    </div>
  );
}
