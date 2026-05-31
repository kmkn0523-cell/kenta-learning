// ────────── 横断検索の絞り込み条件を入力するUI（制御コンポーネント） ──────────
// 親（SearchView）から現在の条件(criteria)を受け取り、変更を onChange で返すだけ。
// 自分では状態を持たない（=制御コンポーネント）ので、表示と入力に専念する。
import type { CSSProperties } from "react";
import { SearchCriteria } from "../utils/searchFilter";
import { Account } from "../types";
import {
  COLOR_TEXT_SECONDARY,
  COLOR_TEXT_HINT,
  COLOR_ACCENT,
  COLOR_BORDER,
  STYLE_INPUT,
} from "../utils/styles";

// このコンポーネントが受け取る値の形
interface SearchFiltersProps {
  criteria: SearchCriteria;                       // 今の絞り込み条件
  onChange: (next: SearchCriteria) => void;       // 条件が変わったら親に返す
  categories: string[];                           // 選べるカテゴリ名の一覧
  accounts: Account[];                            // 選べる口座の一覧
}

// 種別（全部/収入/支出）の選択肢
const KIND_OPTIONS: { value: SearchCriteria["kind"]; label: string }[] = [
  { value: "all", label: "すべて" },
  { value: "income", label: "収入" },
  { value: "expense", label: "支出" },
];

// 絞り込み条件の入力フォーム本体
export default function SearchFilters({ criteria, onChange, categories, accounts }: SearchFiltersProps) {
  // 条件の一部だけを書き換えて親に返す小さなヘルパー
  function update(patch: Partial<SearchCriteria>) {
    onChange({ ...criteria, ...patch });
  }

  // 金額入力を数値に直す（空欄なら null、負数は0に丸めて弾く）
  function parseAmount(text: string): number | null {
    if (text.trim() === "") return null;          // 空欄は「指定なし」
    const value = Number(text);                   // 文字列を数値にする
    if (Number.isNaN(value) || value < 0) return 0; // 数字でない/負数は0扱い（負数を弾く）
    return value;
  }

  // カテゴリチップを押したときの切り替え（入っていれば外す・無ければ足す）
  function toggleCategory(name: string) {
    const isSelected = criteria.categories.includes(name);
    const nextCategories = isSelected
      ? criteria.categories.filter((c) => c !== name)  // すでに選択中→外す
      : [...criteria.categories, name];                // 未選択→足す
    update({ categories: nextCategories });
  }

  // 小見出しの共通スタイル
  const labelStyle: CSSProperties = {
    color: COLOR_TEXT_SECONDARY,
    fontSize: 12,
    fontWeight: 600,
    marginBottom: 6,
    display: "block",
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* キーワード入力 */}
      <div>
        <label style={labelStyle}>キーワード（メモ・カテゴリ）</label>
        <input
          type="text"
          value={criteria.keyword}
          onChange={(e) => update({ keyword: e.target.value })}
          placeholder="例：ランチ、給与"
          style={STYLE_INPUT}
        />
      </div>

      {/* 種別（すべて/収入/支出）の3択ボタン */}
      <div>
        <label style={labelStyle}>種別</label>
        <div style={{ display: "flex", gap: 8 }}>
          {KIND_OPTIONS.map((opt) => {
            const active = criteria.kind === opt.value; // 今選ばれているか
            return (
              <button
                type="button"
                key={opt.value}
                onClick={() => update({ kind: opt.value })}
                style={{
                  flex: 1,
                  padding: "8px 0",
                  borderRadius: 10,
                  border: `1px solid ${active ? COLOR_ACCENT : COLOR_BORDER}`,
                  background: active ? "rgba(34,211,238,0.12)" : "transparent",
                  color: active ? COLOR_ACCENT : COLOR_TEXT_HINT,
                  fontSize: 13,
                  fontWeight: active ? 700 : 400,
                  cursor: "pointer",
                }}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* カテゴリチップ（複数選べる） */}
      {categories.length > 0 && (
        <div>
          <label style={labelStyle}>カテゴリ（複数選択可）</label>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {categories.map((name) => {
              const active = criteria.categories.includes(name); // 選択中か
              return (
                <button
                  type="button"
                  key={name}
                  onClick={() => toggleCategory(name)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: 999,                 // 角を丸くしてチップ風に
                    border: `1px solid ${active ? COLOR_ACCENT : COLOR_BORDER}`,
                    background: active ? "rgba(34,211,238,0.12)" : "transparent",
                    color: active ? COLOR_ACCENT : COLOR_TEXT_SECONDARY,
                    fontSize: 12,
                    fontWeight: active ? 700 : 400,
                    cursor: "pointer",
                  }}
                >
                  {name}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* 期間（開始日〜終了日） */}
      <div>
        <label style={labelStyle}>期間</label>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="date"
            value={criteria.dateFrom}
            onChange={(e) => update({ dateFrom: e.target.value })}
            style={{ ...STYLE_INPUT, flex: 1 }}
          />
          <span style={{ color: COLOR_TEXT_HINT, fontSize: 13 }}>〜</span>
          <input
            type="date"
            value={criteria.dateTo}
            onChange={(e) => update({ dateTo: e.target.value })}
            style={{ ...STYLE_INPUT, flex: 1 }}
          />
        </div>
      </div>

      {/* 金額帯（下限〜上限） */}
      <div>
        <label style={labelStyle}>金額（円）</label>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="number"
            min={0}
            inputMode="numeric"
            value={criteria.amountMin === null ? "" : criteria.amountMin}
            onChange={(e) => update({ amountMin: parseAmount(e.target.value) })}
            placeholder="下限"
            style={{ ...STYLE_INPUT, flex: 1 }}
          />
          <span style={{ color: COLOR_TEXT_HINT, fontSize: 13 }}>〜</span>
          <input
            type="number"
            min={0}
            inputMode="numeric"
            value={criteria.amountMax === null ? "" : criteria.amountMax}
            onChange={(e) => update({ amountMax: parseAmount(e.target.value) })}
            placeholder="上限"
            style={{ ...STYLE_INPUT, flex: 1 }}
          />
        </div>
      </div>

      {/* 口座の絞り込み（全口座 or 1つ） */}
      {accounts.length > 0 && (
        <div>
          <label style={labelStyle}>口座</label>
          <select
            value={criteria.accountId}
            onChange={(e) => update({ accountId: e.target.value })}
            style={STYLE_INPUT}
          >
            <option value="">すべての口座</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* 並び替え（日付の新しい順 / 金額の大きい順） */}
      <div>
        <label style={labelStyle}>並び替え</label>
        <div style={{ display: "flex", gap: 8 }}>
          {([
            { value: "dateDesc", label: "日付の新しい順" },
            { value: "amountDesc", label: "金額の大きい順" },
          ] as { value: SearchCriteria["sort"]; label: string }[]).map((opt) => {
            const active = criteria.sort === opt.value;
            return (
              <button
                type="button"
                key={opt.value}
                onClick={() => update({ sort: opt.value })}
                style={{
                  flex: 1,
                  padding: "8px 0",
                  borderRadius: 10,
                  border: `1px solid ${active ? COLOR_ACCENT : COLOR_BORDER}`,
                  background: active ? "rgba(34,211,238,0.12)" : "transparent",
                  color: active ? COLOR_ACCENT : COLOR_TEXT_HINT,
                  fontSize: 13,
                  fontWeight: active ? 700 : 400,
                  cursor: "pointer",
                }}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* 条件をすべてリセットするボタン */}
      <button
        type="button"
        onClick={() =>
          onChange({
            keyword: "",
            kind: "all",
            categories: [],
            dateFrom: "",
            dateTo: "",
            amountMin: null,
            amountMax: null,
            accountId: "",
            sort: "dateDesc",
          })
        }
        style={{
          alignSelf: "flex-start",
          padding: "6px 14px",
          borderRadius: 10,
          border: `1px solid ${COLOR_BORDER}`,
          background: "transparent",
          color: COLOR_TEXT_SECONDARY,
          fontSize: 12,
          cursor: "pointer",
        }}
      >
        条件をクリア
      </button>
    </div>
  );
}
