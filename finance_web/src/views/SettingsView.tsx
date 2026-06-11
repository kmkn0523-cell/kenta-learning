// ────────── 設定画面（カテゴリ管理） ──────────
import { useState, CSSProperties } from "react";
import { CategoryConfig, CategoryItem, Tx, Income, FixedExpense, Transfer } from "../types";
import { Input } from "../components/ui";
import {
  STYLE_CARD,
  STYLE_BUTTON_PRIMARY,
  STYLE_BUTTON_OUTLINE,
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_SECONDARY,
  COLOR_NEGATIVE,
} from "../utils/styles";
import { makeDefaultCategoryConfig } from "../utils/defaultCategories";
import ShareCard from "../components/ShareCard";

import { useRef } from "react";

// ── スタイル定数 ──────────────────────────────────────────

// 年・月セレクトボックスの共通スタイル
const STYLE_SELECT_INPUT: CSSProperties = {
  flex: 1,
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 10,
  color: "#e2e8f0",
  fontSize: 14,
  padding: "10px 12px",
  fontFamily: "inherit",
  appearance: "none",
  WebkitAppearance: "none",
};

// 確認モーダルの背景オーバーレイ共通スタイル
const STYLE_MODAL_OVERLAY: CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.72)",
  zIndex: 200,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: 20,
};

// ─────────────────────────────────────────────────────────

// カテゴリの種類（変動費・固定費・収入）
type CategoryKind = "expense" | "fixedExpense" | "income";

// このコンポーネントが受け取る props の型
interface SettingsViewProps {
  categoryConfig: CategoryConfig;
  setCategoryConfig: (updater: CategoryConfig | ((p: CategoryConfig) => CategoryConfig)) => void;
  transactions: Tx[];
  setTransactions: (updater: Tx[] | ((p: Tx[]) => Tx[])) => void;
  incomes: Income[];
  setIncomes: (updater: Income[] | ((p: Income[]) => Income[])) => void;
  fixedExpenses: FixedExpense[];
  setFixedExpenses: (updater: FixedExpense[] | ((p: FixedExpense[]) => FixedExpense[])) => void;
  onReset: () => void;
  onOpenTutorial: () => void;
  // バックアップ・リストア関数（App.tsx の useBackup フックから渡す）
  exportBackup: () => void;
  importBackup: (file: File) => void;
  // 口座間振替一覧と更新関数（一括削除で使う）
  transfers: Transfer[];
  setTransfers: (updater: Transfer[] | ((p: Transfer[]) => Transfer[])) => void;
}

export default function SettingsView(props: SettingsViewProps) {
  // バックアップ用の隠しファイル選択inputへの参照
  const backupFileRef = useRef<HTMLInputElement | null>(null);
  // 現在選択中のカテゴリ種類
  const [kind, setKind] = useState<CategoryKind>("expense");
  // 新規追加フォームの値
  const [newName, setNewName] = useState("");
  const [newIcon, setNewIcon] = useState("📦");
  // 編集中のカテゴリID（nullなら編集中なし）
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editIcon, setEditIcon] = useState("");
  // リセット確認モーダルの表示フラグ
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  // 削除確認モーダル用のターゲット
  const [deleteTarget, setDeleteTarget] = useState<CategoryItem | null>(null);

  // ────── 一括削除セクションの state ──────
  // 一括削除カードを開いているかどうか
  const [showBulkDelete, setShowBulkDelete] = useState(false);
  // カットオフ年（これより前のデータを削除する）
  const currentYear = new Date().getFullYear();
  const [bulkYear, setBulkYear] = useState(currentYear - 1);
  // カットオフ月（0〜11 = 1〜12月）
  const [bulkMonth, setBulkMonth] = useState(11); // デフォルト：昨年12月
  // 一括削除の実行確認フラグ
  const [showBulkConfirm, setShowBulkConfirm] = useState(false);

  // 現在のタブのカテゴリを order 順で並べる
  const items: CategoryItem[] = props.categoryConfig[kind].slice().sort((a, b) => a.order - b.order);

  // 新しいカテゴリを追加する
  function addCategory() {
    if (!newName.trim()) return;
    const newItem: CategoryItem = {
      id: `${kind}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      name: newName.trim(),
      icon: newIcon || "📦",
      order: items.length,
    };
    props.setCategoryConfig(prev => ({ ...prev, [kind]: [...prev[kind], newItem] }));
    setNewName("");
    setNewIcon("📦");
  }

  // カテゴリの編集を保存する（リネーム時は既存取引データも更新）
  function saveEdit(item: CategoryItem) {
    const newNameTrimmed = editName.trim();
    if (!newNameTrimmed) return;
    const oldName = item.name;
    // カテゴリ設定を更新
    props.setCategoryConfig(prev => ({
      ...prev,
      [kind]: prev[kind].map(i =>
        i.id === item.id ? { ...i, name: newNameTrimmed, icon: editIcon || i.icon } : i
      ),
    }));
    // 名前が変わった場合は既存取引データのカテゴリ名も一括更新
    if (newNameTrimmed !== oldName) {
      if (kind === "expense") {
        props.setTransactions(prev =>
          prev.map(t => t.category === oldName ? { ...t, category: newNameTrimmed } : t)
        );
      } else if (kind === "income") {
        props.setIncomes(prev =>
          prev.map(t => t.category === oldName ? { ...t, category: newNameTrimmed } : t)
        );
      } else if (kind === "fixedExpense") {
        props.setFixedExpenses(prev =>
          prev.map(t => t.category === oldName ? { ...t, category: newNameTrimmed } : t)
        );
      }
    }
    setEditingId(null);
    setEditName("");
    setEditIcon("");
  }

  // 削除を試みる（使用中ならアラートで拒否する）
  function attemptDelete(item: CategoryItem) {
    const inUse =
      kind === "expense"
        ? props.transactions.some(t => t.category === item.name)
        : kind === "income"
        ? props.incomes.some(t => t.category === item.name)
        : props.fixedExpenses.some(t => t.category === item.name);
    if (inUse) {
      alert(
        `「${item.name}」は既存のデータで使われているため削除できません。先に該当データを別カテゴリに移してください。`
      );
      return;
    }
    setDeleteTarget(item);
  }

  // 削除確認後に実際に削除する
  function confirmDelete() {
    if (!deleteTarget) return;
    props.setCategoryConfig(prev => ({
      ...prev,
      [kind]: prev[kind].filter(i => i.id !== deleteTarget.id),
    }));
    setDeleteTarget(null);
  }

  // カテゴリを1つ上に移動する（order の入れ替え）
  function moveUp(item: CategoryItem) {
    const sorted = items.slice();
    const idx = sorted.findIndex(i => i.id === item.id);
    if (idx <= 0) return;
    const above = sorted[idx - 1];
    props.setCategoryConfig(prev => ({
      ...prev,
      [kind]: prev[kind].map(i => {
        if (i.id === item.id) return { ...i, order: above.order };
        if (i.id === above.id) return { ...i, order: item.order };
        return i;
      }),
    }));
  }

  // カテゴリを1つ下に移動する（order の入れ替え）
  function moveDown(item: CategoryItem) {
    const sorted = items.slice();
    const idx = sorted.findIndex(i => i.id === item.id);
    if (idx < 0 || idx >= sorted.length - 1) return;
    const below = sorted[idx + 1];
    props.setCategoryConfig(prev => ({
      ...prev,
      [kind]: prev[kind].map(i => {
        if (i.id === item.id) return { ...i, order: below.order };
        if (i.id === below.id) return { ...i, order: item.order };
        return i;
      }),
    }));
  }

  // カテゴリをデフォルトにリセットする
  function resetAll() {
    props.setCategoryConfig(makeDefaultCategoryConfig());
    setShowResetConfirm(false);
  }

  return (
    <div>
      {/* ────────── バックアップ・リストアカード ────────── */}
      <div style={{ ...STYLE_CARD, marginBottom: 16 }}>
        {/* セクションタイトル */}
        <div style={{ fontSize: 15, fontWeight: 700, color: COLOR_TEXT_PRIMARY, marginBottom: 4 }}>
          🗄️ データのバックアップ・復元
        </div>
        <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginBottom: 14, lineHeight: 1.6 }}>
          全データをJSONファイルに書き出します。機種変更・ブラウザ変更の前に必ず取得してください。
          復元時は既存データが上書きされます。
        </div>

        {/* 2つのボタンを横並びに配置 */}
        <div style={{ display: "flex", gap: 10 }}>
          {/* バックアップ：全データをJSONとしてダウンロード */}
          <button type="button"
            onClick={props.exportBackup}
            style={{ ...STYLE_BUTTON_PRIMARY, flex: 1, fontSize: 13 }}
          >
            📥 バックアップ
          </button>

          {/* リストア：JSONファイルを選んで全データを復元 */}
          <button type="button"
            onClick={() => backupFileRef.current?.click()}
            style={{ ...STYLE_BUTTON_OUTLINE, flex: 1, fontSize: 13 }}
          >
            📤 復元する
          </button>
          {/* ファイル選択ダイアログ用の隠しinput（直接表示はしない） */}
          <input
            ref={backupFileRef}
            type="file"
            accept=".json"
            style={{ display: "none" }}
            onChange={e => {
              const file = e.target.files?.[0];
              if (file) {
                props.importBackup(file);
                // 同じファイルを再選択できるようにinputの値をリセット
                e.target.value = "";
              }
            }}
          />
        </div>

        {/* 注意書き */}
        <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginTop: 10, lineHeight: 1.5, paddingTop: 10, borderTop: "1px solid rgba(255,255,255,0.06)" }}>
          ⚠️ バックアップファイルは暗号化済みです。同じパスワードでのみ復元できます。
        </div>
      </div>

      {/* ────────── CSVエクスポートカード ────────── */}
      {/* 支出・収入データをCSVファイルとしてダウンロードできる。Excelで開いて分析するのに使う */}
      {(() => {
        // CSVエクスポートを実行する関数（クリック時に呼び出す）
        function exportCsv() {
          // BOM（﻿）を先頭に付けると Excel が文字化けしない
          const rows: string[] = ["﻿日付,種別,カテゴリ,金額,メモ"];

          // 収入データを1行ずつ変換する
          for (const inc of props.incomes) {
            // カンマが含まれるフィールドは「、」に置換して CSV が壊れないようにする
            const memo = (inc.memo || "").replace(/,/g, "、").replace(/\n/g, " ");
            rows.push([inc.date || "", "収入", inc.category || "", String(inc.amount || 0), memo].join(","));
          }

          // 支出データを1行ずつ変換する
          for (const tx of props.transactions) {
            const memo = (tx.memo || "").replace(/,/g, "、").replace(/\n/g, " ");
            rows.push([tx.date || "", "支出", tx.category || "", String(tx.amount || 0), memo].join(","));
          }

          // 日付順（昇順）に並べ替える（ヘッダー行を除く）
          const header = rows[0];
          const dataRows = rows.slice(1).sort((a, b) => {
            const dateA = a.split(",")[0] || "";
            const dateB = b.split(",")[0] || "";
            return dateA.localeCompare(dateB);
          });

          // CSV 文字列を Blob にしてダウンロードリンクを生成する
          const csv = [header, ...dataRows].join("\n");
          const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          // ファイル名に今日の日付を入れる
          a.download = `家計データ_${new Date().toISOString().slice(0, 10)}.csv`;
          a.click();
          // 使い終わった Blob URL を解放してメモリを節約する
          URL.revokeObjectURL(url);
        }

        // 支出・収入のデータ件数（ボタン横に表示する）
        const txCount = props.transactions.length;
        const incCount = props.incomes.length;

        return (
          <div style={{ ...STYLE_CARD, marginBottom: 16 }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: COLOR_TEXT_PRIMARY, marginBottom: 4 }}>
              📊 CSVエクスポート
            </div>
            <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginBottom: 14, lineHeight: 1.6 }}>
              支出・収入データをCSVファイルとして書き出します。Excel や Google スプレッドシートで開けます。
            </div>
            {/* データ件数のプレビュー */}
            <div style={{ display: "flex", gap: 12, marginBottom: 14 }}>
              <div style={{
                flex: 1, background: "rgba(255,255,255,0.04)", borderRadius: 8,
                padding: "8px 12px", textAlign: "center",
              }}>
                <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "monospace" }}>{txCount}</div>
                <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginTop: 2 }}>件の支出</div>
              </div>
              <div style={{
                flex: 1, background: "rgba(255,255,255,0.04)", borderRadius: 8,
                padding: "8px 12px", textAlign: "center",
              }}>
                <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "monospace" }}>{incCount}</div>
                <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginTop: 2 }}>件の収入</div>
              </div>
              <div style={{
                flex: 1, background: "rgba(255,255,255,0.04)", borderRadius: 8,
                padding: "8px 12px", textAlign: "center",
              }}>
                <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "monospace" }}>{txCount + incCount}</div>
                <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginTop: 2 }}>件 合計</div>
              </div>
            </div>
            {/* エクスポートボタン */}
            <button type="button"
              onClick={exportCsv}
              disabled={txCount + incCount === 0}
              style={{
                ...STYLE_BUTTON_PRIMARY,
                width: "100%",
                opacity: txCount + incCount === 0 ? 0.4 : 1,
                cursor: txCount + incCount === 0 ? "not-allowed" : "pointer",
              }}
            >
              📥 CSVをダウンロード（全期間）
            </button>
            <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginTop: 8, lineHeight: 1.5 }}>
              形式：日付・種別（収入/支出）・カテゴリ・金額・メモ。日付順に並んで出力されます。
            </div>
          </div>
        );
      })()}

      {/* ────────── 一括削除カード ────────── */}
      <div style={{ ...STYLE_CARD, marginBottom: 16 }}>
        {/* ヘッダー（タップで開閉） */}
        <div
          style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
          onClick={() => { setShowBulkDelete(v => !v); setShowBulkConfirm(false); }}
        >
          <div style={{ fontSize: 15, fontWeight: 700, color: COLOR_TEXT_PRIMARY }}>
            🗑️ 古いデータを一括削除
          </div>
          <span style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY }}>{showBulkDelete ? "▲" : "▼"}</span>
        </div>

        {showBulkDelete && (() => {
          // 選択した「年YYYY・月mm（0始まり）」より前のデータ件数を計算する
          // 例：2024年12月を選んだ場合 → 2024-12-31以前が対象
          const cutoffStr =
            bulkYear + "-" + String(bulkMonth + 1).padStart(2, "0") + "-31";

          // 各データ配列で cutoff 以前のものの件数を数える
          const txCount = props.transactions.filter(t => t.date <= cutoffStr).length;
          const incCount = props.incomes.filter(i => i.date <= cutoffStr).length;
          const trCount = props.transfers.filter(t => t.date <= cutoffStr).length;
          const totalCount = txCount + incCount + trCount;

          // 年の選択肢（5年前〜今年）
          const yearOptions = Array.from({ length: 6 }, (_, i) => currentYear - 5 + i);
          const monthLabels = ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"];

          return (
            <div style={{ marginTop: 14 }}>
              <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginBottom: 12, lineHeight: 1.6 }}>
                指定した月（月末）までの支出・収入・振替を一括で削除します。
                固定費・ローン設定は削除されません。
              </div>

              {/* 年・月 セレクター */}
              <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                {/* 年 */}
                <select
                  value={bulkYear}
                  onChange={e => setBulkYear(Number(e.target.value))}
                  style={STYLE_SELECT_INPUT}
                >
                  {yearOptions.map(y => (
                    <option key={y} value={y}>{y}年</option>
                  ))}
                </select>
                {/* 月 */}
                <select
                  value={bulkMonth}
                  onChange={e => setBulkMonth(Number(e.target.value))}
                  style={STYLE_SELECT_INPUT}
                >
                  {monthLabels.map((label, idx) => (
                    <option key={idx} value={idx}>{label}</option>
                  ))}
                </select>
              </div>

              {/* 削除件数プレビュー */}
              <div style={{
                background: "rgba(148,163,184,0.06)",
                borderRadius: 10,
                padding: "10px 14px",
                marginBottom: 12,
                fontSize: 12,
                color: COLOR_TEXT_SECONDARY,
                lineHeight: 1.8,
              }}>
                <div>対象期間：{bulkYear}年{bulkMonth + 1}月末まで</div>
                <div>変動支出：{txCount}件 ／ 収入：{incCount}件 ／ 振替：{trCount}件</div>
                <div style={{ fontWeight: 700, color: totalCount > 0 ? "#f87171" : COLOR_TEXT_SECONDARY, marginTop: 2 }}>
                  合計 {totalCount} 件が削除されます
                </div>
              </div>

              {/* 実行ボタン（0件なら無効） */}
              {!showBulkConfirm ? (
                <button type="button"
                  onClick={() => { if (totalCount > 0) setShowBulkConfirm(true); }}
                  disabled={totalCount === 0}
                  style={{
                    ...STYLE_BUTTON_PRIMARY,
                    width: "100%",
                    background: totalCount > 0 ? COLOR_NEGATIVE : undefined,
                    opacity: totalCount === 0 ? 0.4 : 1,
                  }}
                >
                  🗑️ {totalCount}件を削除する
                </button>
              ) : (
                <div>
                  <div style={{ fontSize: 13, color: "#f87171", marginBottom: 10, textAlign: "center", fontWeight: 700 }}>
                    本当に削除しますか？元に戻せません
                  </div>
                  <div style={{ display: "flex", gap: 10 }}>
                    <button type="button"
                      onClick={() => setShowBulkConfirm(false)}
                      style={{ ...STYLE_BUTTON_OUTLINE, flex: 1 }}
                    >
                      キャンセル
                    </button>
                    <button type="button"
                      onClick={() => {
                        // cutoff 以前のデータを各配列から除外する
                        props.setTransactions(prev => prev.filter(t => t.date > cutoffStr));
                        props.setIncomes(prev => prev.filter(i => i.date > cutoffStr));
                        props.setTransfers(prev => prev.filter(t => t.date > cutoffStr));
                        setShowBulkConfirm(false);
                        setShowBulkDelete(false);
                      }}
                      style={{ ...STYLE_BUTTON_PRIMARY, flex: 1, background: COLOR_NEGATIVE }}
                    >
                      削除する
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })()}
      </div>

      <div style={{ ...STYLE_CARD }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: COLOR_TEXT_PRIMARY, marginBottom: 12 }}>
          カテゴリ管理
        </div>

        {/* タブ切替（変動費 / 固定費 / 収入） */}
        <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
          {(["expense", "fixedExpense", "income"] as CategoryKind[]).map(k => (
            <button type="button"
              key={k}
              onClick={() => setKind(k)}
              style={{
                ...STYLE_BUTTON_OUTLINE,
                flex: 1,
                borderColor: kind === k ? COLOR_TEXT_PRIMARY : undefined,
              }}
            >
              {k === "expense" ? "変動費" : k === "fixedExpense" ? "固定費" : "収入"}
            </button>
          ))}
        </div>

        {/* 新しいカテゴリを追加するフォーム */}
        <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
          <input
            value={newIcon}
            onChange={e => setNewIcon(e.target.value)}
            placeholder="📦"
            style={{ width: 50, fontSize: 18, textAlign: "center", background: "transparent", border: "1px solid rgba(148,163,184,0.2)", borderRadius: 8, color: COLOR_TEXT_PRIMARY }}
          />
          <Input value={newName} onChange={e => setNewName(e.target.value)} placeholder="新しいカテゴリ名" />
          <button type="button" onClick={addCategory} style={{ ...STYLE_BUTTON_PRIMARY, width: 80 }}>追加</button>
        </div>

        {/* カテゴリ一覧 */}
        {items.map(item => (
          <div
            key={item.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "8px 0",
              borderBottom: "1px solid rgba(148,163,184,0.08)",
            }}
          >
            {editingId === item.id ? (
              // 編集モード
              <>
                <input
                  value={editIcon}
                  onChange={e => setEditIcon(e.target.value)}
                  style={{ width: 36, fontSize: 18, background: "transparent", border: "1px solid rgba(148,163,184,0.2)", borderRadius: 6, color: COLOR_TEXT_PRIMARY }}
                />
                <Input value={editName} onChange={e => setEditName(e.target.value)} />
                <button type="button" onClick={() => saveEdit(item)} style={{ ...STYLE_BUTTON_PRIMARY, width: 60 }}>保存</button>
                <button type="button" onClick={() => setEditingId(null)} style={{ ...STYLE_BUTTON_OUTLINE, width: 60 }}>取消</button>
              </>
            ) : (
              // 表示モード
              <>
                <span style={{ fontSize: 20 }}>{item.icon}</span>
                <span style={{ flex: 1, color: COLOR_TEXT_PRIMARY }}>{item.name}</span>
                <button type="button"
                  onClick={() => moveUp(item)}
                  title="上へ"
                  style={{ background: "none", border: "none", color: COLOR_TEXT_SECONDARY, cursor: "pointer" }}
                >
                  ↑
                </button>
                <button type="button"
                  onClick={() => moveDown(item)}
                  title="下へ"
                  style={{ background: "none", border: "none", color: COLOR_TEXT_SECONDARY, cursor: "pointer" }}
                >
                  ↓
                </button>
                <button type="button"
                  onClick={() => { setEditingId(item.id); setEditName(item.name); setEditIcon(item.icon); }}
                  style={{ background: "none", border: "none", color: COLOR_TEXT_SECONDARY, cursor: "pointer" }}
                >
                  ✏️
                </button>
                <button type="button"
                  onClick={() => attemptDelete(item)}
                  style={{ background: "none", border: "none", color: COLOR_NEGATIVE, cursor: "pointer" }}
                >
                  🗑️
                </button>
              </>
            )}
          </div>
        ))}

        {/* デフォルトに戻すボタン */}
        <button type="button"
          onClick={() => setShowResetConfirm(true)}
          style={{ ...STYLE_BUTTON_OUTLINE, marginTop: 20, color: COLOR_NEGATIVE }}
        >
          カテゴリをデフォルトにリセット
        </button>
      </div>

      {/* リセット確認モーダル */}
      {showResetConfirm && (
        <div
          onClick={() => setShowResetConfirm(false)}
          style={STYLE_MODAL_OVERLAY}
        >
          <div onClick={e => e.stopPropagation()} style={{ ...STYLE_CARD, maxWidth: 340 }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: COLOR_TEXT_PRIMARY, marginBottom: 8 }}>
              カテゴリをリセット
            </div>
            <div style={{ fontSize: 13, color: COLOR_TEXT_SECONDARY, marginBottom: 16 }}>
              カスタマイズが全て削除されデフォルトに戻ります。既存の取引データは保持されます。
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button type="button" onClick={() => setShowResetConfirm(false)} style={{ ...STYLE_BUTTON_OUTLINE, flex: 1 }}>
                キャンセル
              </button>
              <button type="button" onClick={resetAll} style={{ ...STYLE_BUTTON_PRIMARY, flex: 1, background: COLOR_NEGATIVE }}>
                リセット
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ────────── 使い方カード ────────── */}
      <div style={{ ...STYLE_CARD, marginTop: 16 }}>
        <button type="button"
          onClick={props.onOpenTutorial}
          style={{ ...STYLE_BUTTON_OUTLINE, width: "100%" }}
        >
          📖 使い方を見る
        </button>
      </div>

      {/* ────────── 友達に教えるカード ────────── */}
      <ShareCard />

      {/* ────────── アプリ情報カード（バージョン・制作者・著作権） ────────── */}
      <div style={{ ...STYLE_CARD, marginTop: 16 }}>
        <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: 10 }}>
          アプリ情報
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12, color: COLOR_TEXT_SECONDARY }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span>アプリ名</span>
            <span style={{ color: COLOR_TEXT_PRIMARY }}>BYB — Before You Broke</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span>バージョン</span>
            <span style={{ color: COLOR_TEXT_PRIMARY, fontFamily: "monospace" }}>v{__APP_VERSION__}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span>制作</span>
            <span style={{ color: COLOR_TEXT_PRIMARY }}>kmkn0523</span>
          </div>
          <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginTop: 6, paddingTop: 8, borderTop: "1px solid rgba(255,255,255,0.06)" }}>
            © 2026 kmkn0523. All Rights Reserved.
          </div>
        </div>
      </div>

      {/* 削除確認モーダル */}
      {deleteTarget && (
        <div
          onClick={() => setDeleteTarget(null)}
          style={STYLE_MODAL_OVERLAY}
        >
          <div onClick={e => e.stopPropagation()} style={{ ...STYLE_CARD, maxWidth: 340 }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: COLOR_TEXT_PRIMARY, marginBottom: 8 }}>
              カテゴリを削除
            </div>
            <div style={{ fontSize: 13, color: COLOR_TEXT_SECONDARY, marginBottom: 16 }}>
              「{deleteTarget.name}」を削除します。よろしいですか？
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button type="button" onClick={() => setDeleteTarget(null)} style={{ ...STYLE_BUTTON_OUTLINE, flex: 1 }}>
                キャンセル
              </button>
              <button type="button" onClick={confirmDelete} style={{ ...STYLE_BUTTON_PRIMARY, flex: 1, background: COLOR_NEGATIVE }}>
                削除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
