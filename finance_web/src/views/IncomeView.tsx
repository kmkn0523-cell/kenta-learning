// ────────── 収入タブ ビューコンポーネント ──────────
// 収入の入力フォーム・月別ナビ・検索フィルター・一覧表示をまとめたコンポーネント
// 検索・並び替えは内部 state で管理する（App.tsx に持ち出さない）

import React, { useMemo, useState, useRef } from "react";
import { Income, RecurringIncome, CategoryConfig, Account } from "../types";
import CsvImportModal, { ImportedRow } from "../components/CsvImportModal";
import { newId } from "../utils/crypto";
import {
  MONTH_LABELS,
  parseYenAmount,
  formatYen,
} from "../utils/format";
import {
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
import { filterAndSortItems, TransactionFilter } from "../utils/filterTransactions";
import { Input, Select } from "../components/ui";
import TxRow from "../components/TxRow";
import MonthNav from "../components/MonthNav";

// このコンポーネントが受け取るデータの型定義
// incSq/setIncSq/incFcat/setIncFcat/fInc はコンポーネント内部で管理するため削除済み
interface IncomeViewProps {
  // 収入入力フォームの現在の値（口座IDも含む）
  incF: { cat: string; amt: string; date: string; memo: string; accountId?: string };
  // 収入フォームの値を更新する関数
  setIncF: (
    u:
      | { cat: string; amt: string; date: string; memo: string; accountId?: string }
      | ((prev: {
          cat: string;
          amt: string;
          date: string;
          memo: string;
          accountId?: string;
        }) => { cat: string; amt: string; date: string; memo: string; accountId?: string })
  ) => void;
  // 口座一覧（口座が登録されていれば収入に紐づける選択肢を表示する）
  accounts?: Account[];
  // 収入を追加するボタンを押したときの処理（成功時 true、失敗時 false を返す）
  addInc: () => boolean;
  // 現在選択中の年
  selectedYear: number;
  // 現在選択中の月（0〜11）
  selectedMonth: number;
  // 月を切り替えたときの処理
  onMonthChange: (y: number, m: number) => void;
  // 月別収入データをCSVファイルとして書き出す処理
  exportMonthlyIncomeCsv: (label: string) => void;
  // 選択中の月の収入一覧
  monthlyIncomes: Income[];
  // 収入データ全体を更新する関数
  setIncomes: (u: Income[] | ((prev: Income[]) => Income[])) => void;
  // トースト通知を表示する関数
  showT: (msg: string, type?: string) => void;
  // 確認ダイアログを表示する関数
  ask: (title: string, msg: string, ok: () => void) => void;
  // カテゴリ設定（動的にカテゴリ名・アイコンを取得するために使う）
  categoryConfig: CategoryConfig;
  // 削除＋Undo：即削除してToastに「元に戻す」を出す
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  delItem: (id: string, setArr: (u: any) => void, label?: string) => void;
  // 定期収入の設定一覧（毎月自動追加する収入の登録）
  recurringIncomes: RecurringIncome[];
  // 定期収入の設定を更新する関数
  setRecurringIncomes: (u: RecurringIncome[] | ((prev: RecurringIncome[]) => RecurringIncome[])) => void;
}

// 収入タブ全体のUIを返すコンポーネント
export default function IncomeView({
  incF,
  setIncF,
  accounts = [],
  addInc,
  selectedYear,
  selectedMonth,
  onMonthChange,
  exportMonthlyIncomeCsv,
  monthlyIncomes,
  setIncomes,
  showT,
  ask,
  categoryConfig,
  delItem,
  recurringIncomes,
  setRecurringIncomes,
}: IncomeViewProps) {
  // categoryConfig.income を order 順で並べ、カテゴリ名とアイコンのマップを作る
  const incomeCategoryNames = categoryConfig.income.slice().sort((a, b) => a.order - b.order).map(c => c.name);

  // ────── 定期収入セクションの state ──────
  // 定期収入セクションを開いているかどうか
  const [showRecSection, setShowRecSection] = useState(false);
  // 定期収入の追加フォームを表示するかどうか
  const [showRecForm, setShowRecForm] = useState(false);
  // 定期収入フォームの入力値
  const [recF, setRecF] = useState({
    name: "",
    cat: incomeCategoryNames[0] || "給与",
    amt: "",
    payDay: "未設定",
  });

  // 振込日の選択肢（1〜31日 + 未設定）
  const PAY_DAY_OPTIONS = ["未設定", ...Array.from({length: 31}, (_, i) => `${i + 1}日`)];
  const incomeCategoryIcons: Record<string, string> = Object.fromEntries(categoryConfig.income.map(c => [c.name, c.icon]));
  // 検索・絞り込み条件をまとめた state（デフォルトは日付の新しい順）
  const [filter, setFilter] = useState<TransactionFilter>({ sortBy: "date", sortDir: "desc" });
  // フィルターパネルの表示フラグ
  const [showFilter, setShowFilter] = useState(false);
  // 金額入力欄への参照：連続入力時に追加成功後の再フォーカスに使う
  const amountInputRef = useRef<HTMLInputElement>(null);
  // CSVインポートモーダルの表示フラグ
  const [showCsvModal, setShowCsvModal] = useState(false);

  // フィルター・並び替えを適用した収入一覧
  const filteredIncomes = useMemo(
    () => filterAndSortItems(monthlyIncomes, filter),
    [monthlyIncomes, filter]
  );

  // この月に登場するカテゴリだけを抽出
  const categories = useMemo(
    () => incomeCategoryNames.filter(c => monthlyIncomes.some(i => i.category === c)),
    [monthlyIncomes]
  );

  return (
    <div>
      {/* ────────────────────────────────────────────────────── */}
      {/* ── 定期収入セクション（給与・副業など自動追加設定） ── */}
      {/* ────────────────────────────────────────────────────── */}
      <div style={STYLE_CARD}>
        {/* セクションヘッダー（タップで開閉） */}
        <div
          style={{display:"flex",justifyContent:"space-between",alignItems:"center",cursor:"pointer"}}
          onClick={() => setShowRecSection(v => !v)}
        >
          <div style={{fontSize:10,color:COLOR_TEXT_HINT,textTransform:"uppercase",letterSpacing:"1.5px"}}>
            ⚡ 定期収入
            {/* 登録件数バッジ */}
            {recurringIncomes.length > 0 && (
              <span style={{marginLeft:8,fontSize:11,color:COLOR_ACCENT,fontFamily:"monospace"}}>
                {recurringIncomes.length}件
              </span>
            )}
          </div>
          <span style={{fontSize:12,color:COLOR_TEXT_HINT}}>{showRecSection ? "▲" : "▼"}</span>
        </div>

        {/* 開いたときだけ中身を表示 */}
        {showRecSection && (
          <div style={{marginTop:14}}>
            {/* 定期収入の一覧 */}
            {recurringIncomes.length === 0 ? (
              <div style={{textAlign:"center",padding:"12px 0",color:COLOR_TEXT_HINT,fontSize:13}}>
                まだ登録された定期収入はありません
              </div>
            ) : (
              recurringIncomes.map(rec => (
                <div
                  key={rec.id}
                  style={{display:"flex",alignItems:"center",gap:10,padding:"10px 0",borderBottom:`1px solid ${COLOR_BORDER}`}}
                >
                  <div style={{flex:1,minWidth:0}}>
                    {/* 停止中はグレーで表示 */}
                    <div style={{fontSize:13,fontWeight:600,color:rec.active===false?COLOR_TEXT_HINT:COLOR_TEXT_PRIMARY}}>
                      {rec.active===false && "⏸ "}{rec.name}
                    </div>
                    <div style={{fontSize:11,color:COLOR_TEXT_SECONDARY,marginTop:2}}>
                      {rec.category} · {rec.payDay} · {formatYen(rec.amount)}/月
                    </div>
                  </div>
                  {/* 有効/停止の切り替えボタン */}
                  <button
                    onClick={() =>
                      setRecurringIncomes(prev =>
                        prev.map(r => r.id === rec.id ? {...r, active: r.active === false ? true : false} : r)
                      )
                    }
                    style={{
                      ...STYLE_BUTTON_OUTLINE,
                      fontSize:11,
                      padding:"4px 10px",
                      minHeight:30,
                      color: rec.active===false ? COLOR_TEXT_HINT : COLOR_ACCENT,
                      borderColor: rec.active===false ? COLOR_BORDER : `${COLOR_ACCENT}44`,
                    }}
                  >
                    {rec.active===false ? "再開" : "停止"}
                  </button>
                  {/* 削除ボタン */}
                  <button
                    onClick={() => delItem(rec.id, setRecurringIncomes, "定期収入を削除しました")}
                    style={{...STYLE_BUTTON_OUTLINE,fontSize:11,padding:"4px 10px",minHeight:30}}
                  >
                    削除
                  </button>
                </div>
              ))
            )}

            {/* 定期収入の追加フォームの開閉ボタン */}
            <button
              onClick={() => setShowRecForm(v => !v)}
              style={{...STYLE_BUTTON_OUTLINE,width:"100%",marginTop:10,fontSize:12}}
            >
              {showRecForm ? "閉じる" : "＋ 定期収入を追加"}
            </button>

            {/* 追加フォーム本体 */}
            {showRecForm && (
              <div style={{marginTop:10,display:"flex",flexDirection:"column",gap:10}}>
                {/* 収入名 */}
                <Input
                  value={recF.name}
                  onChange={e => setRecF(f => ({...f, name: e.target.value}))}
                  placeholder="収入名（例: 給与、副業）"
                />
                {/* カテゴリ */}
                <Select
                  value={recF.cat}
                  onChange={e => setRecF(f => ({...f, cat: e.target.value}))}
                  options={incomeCategoryNames}
                  icons={incomeCategoryIcons}
                />
                {/* 金額 */}
                <Input
                  money
                  type="number"
                  value={recF.amt}
                  onChange={e => setRecF(f => ({...f, amt: e.target.value}))}
                  placeholder="金額（円）"
                />
                {/* 振込日 */}
                <Select
                  value={recF.payDay}
                  onChange={e => setRecF(f => ({...f, payDay: e.target.value}))}
                  options={PAY_DAY_OPTIONS}
                />
                {/* 登録ボタン */}
                <button
                  onClick={() => {
                    const a = parseYenAmount(recF.amt);
                    if (!recF.name) { showT("収入名を入力してください", "error"); return; }
                    if (!a || a <= 0) { showT("金額を入力してください", "error"); return; }
                    setRecurringIncomes(prev => [
                      ...prev,
                      {
                        id: newId(),
                        name: recF.name,
                        category: recF.cat,
                        amount: a,
                        payDay: recF.payDay,
                        active: true,
                      }
                    ]);
                    setRecF({name:"", cat: incomeCategoryNames[0] || "給与", amt:"", payDay:"未設定"});
                    setShowRecForm(false);
                    showT("定期収入を登録しました");
                  }}
                  style={STYLE_BUTTON_PRIMARY}
                >
                  登録する
                </button>
                {/* 注意書き */}
                <div style={{fontSize:11,color:COLOR_TEXT_HINT,lineHeight:1.6}}>
                  ※ 振込日が来た月から自動的に収入として追加されます。過去月は追加されません。
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── 収入入力フォーム ── */}
      <div style={STYLE_CARD}>
        <div
          style={{
            fontSize: 10,
            color: COLOR_TEXT_HINT,
            textTransform: "uppercase",
            letterSpacing: "1.5px",
            marginBottom: 14,
          }}
        >
          収入を入力
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 10,
            marginBottom: 12,
          }}
        >
          {/* カテゴリ選択 */}
          <Select
            value={incF.cat}
            onChange={e => setIncF(f => ({ ...f, cat: e.target.value }))}
            options={incomeCategoryNames}
            icons={incomeCategoryIcons}
          />
          {/* 金額入力 */}
          <Input
            ref={amountInputRef}
            money
            type="number"
            value={incF.amt}
            onChange={e => setIncF(f => ({ ...f, amt: e.target.value }))}
            placeholder="金額（円）"
          />
          {/* 日付入力 */}
          <Input
            type="date"
            value={incF.date}
            onChange={e => setIncF(f => ({ ...f, date: e.target.value }))}
          />
          {/* メモ入力 */}
          <Input
            value={incF.memo}
            onChange={e => setIncF(f => ({ ...f, memo: e.target.value }))}
            placeholder="メモ（任意）"
          />
          {/* 口座選択（口座が登録されているときだけ表示） */}
          {accounts.length > 0 && (
            <select
              value={incF.accountId || ""}
              onChange={e => setIncF(f => ({ ...f, accountId: e.target.value || undefined }))}
              style={{
                width: "100%",
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 10,
                color: incF.accountId ? "#e2e8f0" : "#64748b",
                fontSize: 14,
                padding: "12px 14px",
                fontFamily: "inherit",
                appearance: "none",
                WebkitAppearance: "none",
              }}
            >
              <option value="">🏦 口座を選択（任意）</option>
              {accounts.map(acc => (
                <option key={acc.id} value={acc.id}>{acc.name}</option>
              ))}
            </select>
          )}
        </div>
        {/* 追加ボタン（成功時は金額入力欄に再フォーカスして連続入力できるように） */}
        <button onClick={()=>{if(addInc()) setTimeout(()=>amountInputRef.current?.focus(),50);}} style={STYLE_BUTTON_PRIMARY}>
          追加
        </button>
      </div>

      {/* ── 月を切り替えるナビゲーション ── */}
      <MonthNav
        selectedYear={selectedYear}
        selectedMonth={selectedMonth}
        onChange={onMonthChange}
      />

      {/* ── CSV出力・インポートボタン ── */}
      <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
        {/* CSV出力：収入が1件以上あるときだけ表示 */}
        {monthlyIncomes.length > 0 && (
          <button
            onClick={() =>
              exportMonthlyIncomeCsv(
                `${selectedYear}年${MONTH_LABELS[selectedMonth]}`
              )
            }
            style={{ ...STYLE_BUTTON_OUTLINE, flex: 1, fontSize: 12 }}
          >
            📤 CSV出力
          </button>
        )}
        {/* CSVインポート：常に表示 */}
        <button
          onClick={() => setShowCsvModal(true)}
          style={{ ...STYLE_BUTTON_OUTLINE, flex: 1, fontSize: 12 }}
        >
          📥 CSVインポート
        </button>
      </div>

      {/* CSVインポートモーダル */}
      {showCsvModal && (
        <CsvImportModal
          mode="income"
          categoryConfig={categoryConfig}
          onImport={(rows: ImportedRow[]) => {
            // インポートされた行を収入として一括追加する
            setIncomes((prev: Income[]) => [
              ...prev,
              ...rows.map(r => ({
                id: r.id,
                date: r.date,
                category: r.category,
                amount: r.amount,
                memo: r.memo,
                accountId: r.accountId,
              } as Income)),
            ]);
            showT(`${rows.length}件の収入をインポートしました`);
            setShowCsvModal(false);
          }}
          onClose={() => setShowCsvModal(false)}
        />
      )}

      {/* ── 検索バー（収入がある月だけ表示） ── */}
      {monthlyIncomes.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
            {/* キーワード検索入力 */}
            <Input
              value={filter.text || ""}
              onChange={e =>
                setFilter(f => ({ ...f, text: e.target.value || undefined }))
              }
              placeholder="キーワード検索（メモ・カテゴリ）"
            />
            {/* 絞り込みパネルを開くボタン（アクティブ時は色が変わる） */}
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

          {/* フィルターパネル（絞り込みボタンを押したときだけ表示） */}
          {showFilter && (
            <div
              style={{
                background: COLOR_SURFACE,
                borderRadius: 10,
                padding: 14,
                marginBottom: 12,
              }}
            >
              {/* カテゴリ選択 */}
              <div
                style={{
                  fontSize: 12,
                  color: COLOR_TEXT_SECONDARY,
                  marginBottom: 6,
                }}
              >
                カテゴリ
              </div>
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 6,
                  marginBottom: 10,
                }}
              >
                {categories.map(cat => {
                  // このカテゴリが選択中かどうか確認
                  const checked = (filter.categories || []).includes(cat);
                  return (
                    <button
                      key={cat}
                      onClick={() =>
                        setFilter(f => {
                          const prev = f.categories || [];
                          // 選択中なら外す、未選択なら追加する
                          return {
                            ...f,
                            categories: checked
                              ? prev.filter(c => c !== cat)
                              : [...prev, cat],
                          };
                        })
                      }
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
              <div
                style={{
                  fontSize: 12,
                  color: COLOR_TEXT_SECONDARY,
                  marginBottom: 6,
                }}
              >
                日付
              </div>
              <div
                style={{ display: "flex", gap: 8, marginBottom: 10 }}
              >
                <Input
                  type="date"
                  value={filter.dateFrom || ""}
                  onChange={e =>
                    setFilter(f => ({
                      ...f,
                      dateFrom: e.target.value || undefined,
                    }))
                  }
                />
                <span
                  style={{ color: COLOR_TEXT_SECONDARY, alignSelf: "center" }}
                >
                  〜
                </span>
                <Input
                  type="date"
                  value={filter.dateTo || ""}
                  onChange={e =>
                    setFilter(f => ({
                      ...f,
                      dateTo: e.target.value || undefined,
                    }))
                  }
                />
              </div>

              {/* 金額範囲 */}
              <div
                style={{
                  fontSize: 12,
                  color: COLOR_TEXT_SECONDARY,
                  marginBottom: 6,
                }}
              >
                金額
              </div>
              <div
                style={{ display: "flex", gap: 8, marginBottom: 10 }}
              >
                <Input
                  money
                  placeholder="下限"
                  value={
                    filter.amountMin !== undefined
                      ? String(filter.amountMin)
                      : ""
                  }
                  onChange={e =>
                    setFilter(f => ({
                      ...f,
                      amountMin: e.target.value
                        ? Number(e.target.value)
                        : undefined,
                    }))
                  }
                />
                <span
                  style={{ color: COLOR_TEXT_SECONDARY, alignSelf: "center" }}
                >
                  〜
                </span>
                <Input
                  money
                  placeholder="上限"
                  value={
                    filter.amountMax !== undefined
                      ? String(filter.amountMax)
                      : ""
                  }
                  onChange={e =>
                    setFilter(f => ({
                      ...f,
                      amountMax: e.target.value
                        ? Number(e.target.value)
                        : undefined,
                    }))
                  }
                />
              </div>

              {/* ソート選択 */}
              <div
                style={{
                  fontSize: 12,
                  color: COLOR_TEXT_SECONDARY,
                  marginBottom: 6,
                }}
              >
                並び替え
              </div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {(["date", "amount"] as const).map(by =>
                  (["desc", "asc"] as const).map(dir => {
                    // ボタンのラベル文字列を組み立てる
                    const label =
                      by === "date"
                        ? dir === "desc"
                          ? "日付 新しい順"
                          : "日付 古い順"
                        : dir === "desc"
                        ? "金額 高い順"
                        : "金額 低い順";
                    // 現在選択中かどうか確認
                    const active =
                      filter.sortBy === by && filter.sortDir === dir;
                    return (
                      <button
                        key={`${by}-${dir}`}
                        onClick={() =>
                          setFilter(f => ({ ...f, sortBy: by, sortDir: dir }))
                        }
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
                )}
                {/* ソートをリセットするボタン（sortByが設定済みのときだけ表示） */}
                {filter.sortBy && (
                  <button
                    onClick={() =>
                      setFilter(f => ({
                        ...f,
                        sortBy: undefined,
                        sortDir: undefined,
                      }))
                    }
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

      {/* ── 収入一覧 ── */}
      {monthlyIncomes.length === 0 ? (
        // この月にデータが無い場合の空状態表示
        <div
          style={{
            textAlign: "center",
            padding: "44px 0",
            color: COLOR_TEXT_HINT,
          }}
        >
          <div style={{ fontSize: 36, marginBottom: 10 }}>💰</div>
          <div>この月の収入データがありません</div>
          <div style={{ fontSize: 12, marginTop: 8 }}>
            上のフォームから収入を入力してみましょう
          </div>
        </div>
      ) : filteredIncomes.length === 0 ? (
        // 検索結果が0件の場合
        <div
          style={{
            textAlign: "center",
            padding: "44px 0",
            color: COLOR_TEXT_HINT,
          }}
        >
          🔍 該当なし
        </div>
      ) : (
        // フィルター・並び替え済みの収入一覧を表示
        filteredIncomes.map(i => (
          <TxRow
            key={i.id}
            item={i}
            cats={incomeCategoryNames}
            ico={incomeCategoryIcons}
            isInc
            onSave={u => {
              // 編集保存：該当IDのデータを更新
              setIncomes(p => p.map(x => (x.id === u.id ? (u as Income) : x)));
              showT("更新しました");
            }}
            onDelete={() => delItem(i.id, setIncomes, "収入を削除しました")}
          />
        ))
      )}
    </div>
  );
}
