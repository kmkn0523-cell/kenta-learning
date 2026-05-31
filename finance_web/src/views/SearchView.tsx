// ────────── 横断検索タブ「🔍 検索」本体 ──────────
// 収入(Income)と変動支出(Tx)をまたいで検索・絞り込み・集計して一覧表示する画面。
// 検索条件(criteria)はこの画面の中だけで持ち、純粋関数に渡して結果を計算する。
import { useState, useMemo } from "react";
import { Tx, Income, Account, CategoryConfig } from "../types";
import {
  SearchCriteria,
  emptyCriteria,
  filterTransactions,
  summarizeResults,
} from "../utils/searchFilter";
import { formatYen } from "../utils/format";
import SearchFilters from "../components/SearchFilters";
import SearchResultRow from "../components/SearchResultRow";
import {
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_SECONDARY,
  COLOR_TEXT_HINT,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
  STYLE_CARD,
} from "../utils/styles";

// この画面が受け取る値の形
interface SearchViewProps {
  transactions: Tx[];              // 変動支出の一覧
  incomes: Income[];               // 収入の一覧
  accounts: Account[];             // 口座の一覧（名前表示・絞り込みに使う）
  categoryConfig: CategoryConfig;  // カテゴリ設定（チップの候補に使う）
}

// サマリーの数値1つ分の見た目（ラベル＋金額）を作る小さな部品
function SummaryCell({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ flex: 1, textAlign: "center" }}>
      <div style={{ color: COLOR_TEXT_HINT, fontSize: 11, marginBottom: 4 }}>{label}</div>
      <div style={{ color, fontSize: 15, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
        {value}
      </div>
    </div>
  );
}

// 横断検索の画面本体
export default function SearchView({ transactions, incomes, accounts, categoryConfig }: SearchViewProps) {
  // 検索条件をこの画面の状態として持つ（初期値は「何も絞り込んでいない」状態）
  const [criteria, setCriteria] = useState<SearchCriteria>(emptyCriteria());

  // カテゴリチップの候補（変動費＋収入のカテゴリ名を重複なくまとめる）
  const categoryNames = useMemo(() => {
    const names = [
      ...categoryConfig.expense.map((c) => c.name),  // 変動費カテゴリ名
      ...categoryConfig.income.map((c) => c.name),   // 収入カテゴリ名
    ];
    return Array.from(new Set(names));               // 重複を取り除く
  }, [categoryConfig]);

  // 口座IDから口座名を引くための対応表（結果行に口座名を出すため）
  const accountNameById = useMemo(() => {
    const map: Record<string, string> = {};
    accounts.forEach((account) => {
      map[account.id] = account.name;
    });
    return map;
  }, [accounts]);

  // 条件にあう結果を計算する（条件かデータが変わった時だけ再計算）
  const results = useMemo(
    () => filterTransactions(transactions, incomes, criteria),
    [transactions, incomes, criteria]
  );

  // 結果の集計値（件数・収入計・支出計・差引）を計算する
  const summary = useMemo(() => summarizeResults(results), [results]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* 上部：結果に連動するサマリーバー */}
      <div style={{ ...STYLE_CARD, display: "flex", alignItems: "center", padding: "14px 12px" }}>
        <SummaryCell label="件数" value={`${summary.count}件`} color={COLOR_TEXT_PRIMARY} />
        <SummaryCell label="収入計" value={formatYen(summary.incomeTotal)} color={COLOR_POSITIVE} />
        <SummaryCell label="支出計" value={formatYen(summary.expenseTotal)} color={COLOR_NEGATIVE} />
        <SummaryCell
          label="差引"
          value={`${summary.net >= 0 ? "＋" : "−"}${formatYen(Math.abs(summary.net))}`}
          color={summary.net >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE}
        />
      </div>

      {/* 中部：絞り込み条件の入力フォーム */}
      <div style={{ ...STYLE_CARD, padding: 16 }}>
        <SearchFilters
          criteria={criteria}
          onChange={setCriteria}
          categories={categoryNames}
          accounts={accounts}
        />
      </div>

      {/* 下部：検索結果の一覧 */}
      <div style={{ ...STYLE_CARD, padding: 0, overflow: "hidden" }}>
        {results.length === 0 ? (
          // 0件のときの空状態メッセージ（クラッシュさせない）
          <div style={{ textAlign: "center", padding: "40px 16px", color: COLOR_TEXT_HINT, fontSize: 13 }}>
            条件にあう収入・支出が見つかりませんでした
          </div>
        ) : (
          // 1件ずつ結果行を並べる
          results.map((item) => (
            <SearchResultRow
              key={`${item.kind}-${item.id}`}
              item={item}
              accountName={item.accountId ? accountNameById[item.accountId] : undefined}
            />
          ))
        )}
      </div>

      {/* 補足：この画面は表示専用であることの注意書き */}
      <div style={{ textAlign: "center", color: COLOR_TEXT_SECONDARY, fontSize: 11 }}>
        ※ この画面は検索・確認専用です。編集は各タブから行ってください
      </div>
    </div>
  );
}
