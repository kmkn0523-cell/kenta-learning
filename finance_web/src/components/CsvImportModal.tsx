// ────────── CSVインポートモーダル ──────────
// 銀行やカード会社からダウンロードしたCSVを読み込んで
// 変動支出（または収入）として一括登録できる機能
//
// ステップ1: ファイル選択
// ステップ2: 列マッピング（どの列が日付/金額/メモか）を確認・修正
// ステップ3: プレビュー確認 → インポート実行

import { useState, useRef, useMemo, CSSProperties } from "react";
import { CategoryConfig } from "../types";
import { newId } from "../utils/crypto";
import {
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_SECONDARY,
  COLOR_TEXT_HINT,
  COLOR_BORDER,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
  COLOR_ACCENT,
  STYLE_CARD,
  STYLE_BUTTON_PRIMARY,
  STYLE_BUTTON_OUTLINE,
} from "../utils/styles";

// ── スタイル定数 ──────────────────────────────────────────

// モーダル背景オーバーレイ（画面全体を覆う半透明黒）
const STYLE_CSV_OVERLAY: CSSProperties = {
  position: "fixed",
  inset: 0,
  zIndex: 200,
  background: "rgba(0,0,0,0.7)",
  backdropFilter: "blur(4px)",
  display: "flex",
  alignItems: "flex-end",
  justifyContent: "center",
  padding: "0 0 env(safe-area-inset-bottom)",
};

// ファイルドロップゾーンの静的スタイル
const STYLE_CSV_DROPZONE: CSSProperties = {
  border: `2px dashed ${COLOR_BORDER}`,
  borderRadius: 12,
  padding: "40px 20px",
  textAlign: "center",
  cursor: "pointer",
  background: "rgba(255,255,255,0.02)",
  marginBottom: 16,
  transition: "border-color 0.15s",
};

// プレビュー行の静的スタイル（background/border/opacity は動的に上書き）
const STYLE_CSV_ROW_BASE: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  padding: "8px 10px",
  borderRadius: 8,
  marginBottom: 4,
  cursor: "pointer",
};

// チェックバッジの静的スタイル（border/background は動的に上書き）
const STYLE_CSV_BADGE_BASE: CSSProperties = {
  width: 16,
  height: 16,
  borderRadius: "50%",
  flexShrink: 0,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

// ─────────────────────────────────────────────────────────

// ────────── 型定義 ──────────

// インポート後に返す1行分のデータ
export interface ImportedRow {
  id: string;
  date: string;       // "YYYY-MM-DD" 形式
  amount: number;     // 金額（円）
  memo: string;       // メモ・摘要
  category: string;   // カテゴリ名
  accountId?: string; // 口座ID（任意）
}

// モーダルが受け取る props
interface CsvImportModalProps {
  // "expense" なら変動支出、"income" なら収入
  mode: "expense" | "income";
  // カテゴリ設定（カテゴリ一覧の表示に使う）
  categoryConfig: CategoryConfig;
  // インポート実行時のコールバック（確定した行の配列を渡す）
  onImport: (rows: ImportedRow[]) => void;
  // モーダルを閉じるコールバック
  onClose: () => void;
}

// CSVをパース後の内部表現（行列）
interface ParsedCsv {
  headers: string[];        // ヘッダー行
  rows: string[][];         // データ行（各セルが文字列）
}

// 列マッピングの設定（どの列インデックスを何として使うか）
interface ColumnMap {
  dateCol: number | null;    // 日付列のインデックス
  amountCol: number | null;  // 金額列のインデックス
  memoCol: number | null;    // メモ列のインデックス
}

// ────────── ユーティリティ関数 ──────────

// 全角数字・全角記号をASCII半角に変換する（銀行CSVは全角が多い）
function toHalfWidth(str: string): string {
  return str.replace(/[！-～]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0));
}

// 数字文字列から金額（正の整数）を取り出す
// カンマ区切り・全角数字・「円」付きなども吸収する
function parseAmount(str: string): number {
  if (!str) return 0;
  // 全角→半角に変換してから余計な文字を除去
  const cleaned = toHalfWidth(str).replace(/[¥￥,，円\s]/g, "").replace(/[^0-9\-.]/g, "");
  const n = parseFloat(cleaned);
  // NaN や 0 以下は 0 とみなす（収入のマイナス表記は正にする）
  return isNaN(n) ? 0 : Math.abs(Math.round(n));
}

// 日付文字列を "YYYY-MM-DD" に正規化する
// 対応フォーマット: YYYY/MM/DD, YYYY-MM-DD, YYYY年M月D日, YYYYMMDD, MM/DD（今年補完）
function normalizeDate(str: string): string {
  if (!str) return "";
  // 全角→半角
  const s = toHalfWidth(str).trim();
  // YYYY/MM/DD または YYYY-MM-DD
  const m1 = s.match(/^(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})/);
  if (m1) return `${m1[1]}-${m1[2].padStart(2, "0")}-${m1[3].padStart(2, "0")}`;
  // YYYY年M月D日
  const m2 = s.match(/^(\d{4})年(\d{1,2})月(\d{1,2})日/);
  if (m2) return `${m2[1]}-${m2[2].padStart(2, "0")}-${m2[3].padStart(2, "0")}`;
  // YYYYMMDD（8桁数字）
  const m3 = s.match(/^(\d{4})(\d{2})(\d{2})$/);
  if (m3) return `${m3[1]}-${m3[2]}-${m3[3]}`;
  // MM/DD（今年を補完）
  const m4 = s.match(/^(\d{1,2})\/(\d{1,2})$/);
  if (m4) return `${new Date().getFullYear()}-${m4[1].padStart(2, "0")}-${m4[2].padStart(2, "0")}`;
  return "";
}

// CSVテキストをパースして headers と rows に分解する
// カンマ区切り・タブ区切り両方に対応。ダブルクォート囲みも処理
function parseCsv(text: string): ParsedCsv {
  // BOM（バイトオーダーマーク）を除去する
  const cleaned = text.replace(/^﻿/, "");
  // 行に分割（CR+LF / LF どちらも対応）
  const lines = cleaned.split(/\r?\n/).filter(l => l.trim() !== "");
  if (lines.length < 2) return { headers: [], rows: [] };

  // 区切り文字を推測する（カンマかタブか）
  const firstLine = lines[0];
  const sep = firstLine.includes("\t") ? "\t" : ",";

  // 1行をセルに分割（ダブルクォート内のカンマは無視する）
  function splitLine(line: string): string[] {
    const cells: string[] = [];
    let cur = "";
    let inQ = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"') {
        if (inQ && line[i + 1] === '"') { cur += '"'; i++; } // エスケープ済みダブルクォート
        else inQ = !inQ;
      } else if (c === sep && !inQ) {
        cells.push(cur.trim());
        cur = "";
      } else {
        cur += c;
      }
    }
    cells.push(cur.trim());
    return cells;
  }

  const headers = splitLine(lines[0]);
  const rows = lines.slice(1).map(l => splitLine(l)).filter(r => r.some(c => c !== ""));
  return { headers, rows };
}

// ヘッダーを見て列マッピングを自動推定する
function autoDetectColumns(headers: string[]): ColumnMap {
  // 日付列のキーワード
  const dateKeywords = ["日付", "取引日", "年月日", "date", "日時", "決済日", "振替日", "入出金日"];
  // 金額列のキーワード
  const amountKeywords = ["金額", "出金", "支出", "引落", "amount", "利用金額", "請求金額", "入金", "収入", "出入金"];
  // メモ列のキーワード
  const memoKeywords = ["メモ", "摘要", "内容", "備考", "memo", "商品名", "利用先", "先方", "店名", "description"];

  // 小文字変換は1度だけ行う（ループごとに変換するとO(n×k)になるため）
  const lowerHeaders = headers.map(h => h.toLowerCase());
  function findCol(keywords: string[]): number | null {
    for (const kw of keywords) {
      const lkw = kw.toLowerCase();
      const idx = lowerHeaders.findIndex(h => h.includes(lkw));
      if (idx !== -1) return idx;
    }
    return null;
  }

  return {
    dateCol:   findCol(dateKeywords),
    amountCol: findCol(amountKeywords),
    memoCol:   findCol(memoKeywords),
  };
}

// ────────── メインコンポーネント ──────────

export default function CsvImportModal({
  mode,
  categoryConfig,
  onImport,
  onClose,
}: CsvImportModalProps) {
  // ステップ管理: 1=ファイル選択, 2=列マッピング, 3=プレビュー確認
  const [step, setStep] = useState<1 | 2 | 3>(1);
  // パース済みCSVデータ
  const [parsed, setParsed] = useState<ParsedCsv | null>(null);
  // 列マッピング設定
  const [colMap, setColMap] = useState<ColumnMap>({ dateCol: null, amountCol: null, memoCol: null });
  // プレビュー行の選択状態（インデックス → 選択中かどうか）
  const [selected, setSelected] = useState<Record<number, boolean>>({});
  // 全行に適用するデフォルトカテゴリ
  const defaultCat = mode === "expense"
    ? (categoryConfig.expense[0]?.name || "食費")
    : (categoryConfig.income[0]?.name || "給与");
  const [globalCategory, setGlobalCategory] = useState(defaultCat);
  // エラーメッセージ
  const [error, setError] = useState("");
  // ファイル入力への参照
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // 利用可能なカテゴリ一覧
  const categories = mode === "expense"
    ? categoryConfig.expense.map(c => c.name)
    : categoryConfig.income.map(c => c.name);

  // ────────── ステップ1：ファイル読み込み ──────────

  function handleFileSelect(file: File) {
    setError("");
    // CSV以外のファイルは拒否する
    if (!file.name.endsWith(".csv") && file.type !== "text/csv") {
      setError("CSVファイル（.csv）を選択してください");
      return;
    }
    const reader = new FileReader();
    // まず Shift-JIS で試みる（日本の銀行CSVに多い）
    reader.onload = (e) => {
      let text = e.target?.result as string;
      if (!text) { setError("ファイルを読み込めませんでした"); return; }
      const result = parseCsv(text);
      if (result.headers.length === 0 || result.rows.length === 0) {
        setError("CSVのデータが見つかりませんでした。ヘッダー行とデータ行が必要です");
        return;
      }
      const detected = autoDetectColumns(result.headers);
      setParsed(result);
      setColMap(detected);
      // 全行を「選択中」にする
      const initSel: Record<number, boolean> = {};
      result.rows.forEach((_, i) => { initSel[i] = true; });
      setSelected(initSel);
      setStep(2);
    };
    reader.onerror = () => setError("ファイルの読み込みに失敗しました");
    // UTF-8 で読む（多くの環境は UTF-8、Shift-JIS は TextDecoder で別途対応）
    reader.readAsText(file, "UTF-8");
  }

  function handleFileDrop(e: React.DragEvent) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  }

  // ────────── ステップ2：列マッピング確認後プレビューへ ──────────

  // プレビュー行を変換する（列マッピングに基づいてデータを抽出）
  const previewRows = useMemo(() => {
    if (!parsed) return [];
    return parsed.rows.map((row, i) => {
      const dateRaw = colMap.dateCol !== null ? (row[colMap.dateCol] || "") : "";
      const amtRaw  = colMap.amountCol !== null ? (row[colMap.amountCol] || "") : "";
      const memoRaw = colMap.memoCol !== null ? (row[colMap.memoCol] || "") : "";
      const date = normalizeDate(dateRaw);
      const amount = parseAmount(amtRaw);
      return { rowIndex: i, date, amount, memo: memoRaw, rawDate: dateRaw, rawAmount: amtRaw };
    }).filter(r => r.amount > 0); // 金額0の行はスキップ
  }, [parsed, colMap]);

  // 確定するためのバリデーション
  function validateAndGoPreview() {
    if (colMap.amountCol === null) { setError("金額列を指定してください"); return; }
    if (colMap.dateCol === null)   { setError("日付列を指定してください"); return; }
    const validRows = previewRows.filter(r => r.amount > 0 && r.date);
    if (validRows.length === 0)    { setError("有効なデータ行が見つかりませんでした。列マッピングを確認してください"); return; }
    setError("");
    setStep(3);
  }

  // ────────── ステップ3：インポート実行 ──────────

  function handleImport() {
    const rows: ImportedRow[] = previewRows
      .filter(r => selected[r.rowIndex] && r.amount > 0 && r.date)
      .map(r => ({
        id: newId(),
        date: r.date,
        amount: r.amount,
        memo: r.memo,
        category: globalCategory,
      }));
    if (rows.length === 0) { setError("インポートする行を1件以上選択してください"); return; }
    onImport(rows);
  }

  // ────────── 共通スタイル ──────────

  // Select コンポーネント代わりのインライン select
  const selectStyle: CSSProperties = {
    width: "100%",
    background: "rgba(255,255,255,0.06)",
    border: `1px solid ${COLOR_BORDER}`,
    borderRadius: 8,
    color: COLOR_TEXT_PRIMARY,
    fontSize: 12,
    padding: "8px 10px",
    fontFamily: "inherit",
    cursor: "pointer",
  };

  // ────────── レンダリング ──────────

  return (
    // オーバーレイ（背景クリックで閉じる）
    <div
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
      style={STYLE_CSV_OVERLAY}
    >
      {/* モーダル本体 */}
      <div style={{
        ...STYLE_CARD,
        width: "100%", maxWidth: 520, maxHeight: "88vh",
        borderRadius: "16px 16px 0 0", overflow: "auto",
        margin: 0, padding: "20px 16px 24px",
      }}>
        {/* ヘッダー */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, letterSpacing: "1.5px", marginBottom: 3 }}>
              {mode === "expense" ? "📥 変動支出" : "📥 収入"} CSVインポート
            </div>
            <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY }}>
              {step === 1 && "CSVファイルを選択"}
              {step === 2 && "列の確認・修正"}
              {step === 3 && `プレビュー（${previewRows.filter(r => selected[r.rowIndex]).length}件選択中）`}
            </div>
          </div>
          {/* ステップインジケーター */}
          <div style={{ display: "flex", gap: 4 }}>
            {([1, 2, 3] as const).map(s => (
              <div key={s} style={{
                width: 8, height: 8, borderRadius: "50%",
                background: step >= s ? COLOR_ACCENT : "rgba(255,255,255,0.15)",
              }}/>
            ))}
          </div>
        </div>

        {/* ────── ステップ1: ファイル選択 ────── */}
        {step === 1 && (
          <div>
            {/* ドラッグ&ドロップ / クリックエリア */}
            <div
              onDragOver={e => e.preventDefault()}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current?.click()}
              style={STYLE_CSV_DROPZONE}
            >
              <div style={{ fontSize: 36, marginBottom: 12 }}>📄</div>
              <div style={{ fontSize: 14, color: COLOR_TEXT_PRIMARY, fontWeight: 600, marginBottom: 6 }}>
                CSVファイルをここにドロップ
              </div>
              <div style={{ fontSize: 12, color: COLOR_TEXT_HINT }}>またはクリックして選択</div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,text/csv"
                onChange={e => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); e.target.value = ""; }}
                style={{ display: "none" }}
              />
            </div>

            {/* 対応フォーマットの説明 */}
            <div style={{ ...STYLE_CARD, background: "rgba(255,255,255,0.02)", marginBottom: 16, padding: 12 }}>
              <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginBottom: 8 }}>対応フォーマット</div>
              {[
                "ヘッダー行（列名）＋データ行があるCSV",
                "カンマ区切り（.csv）",
                "文字コード: UTF-8 / Shift-JIS",
                "日付形式: YYYY/MM/DD、YYYY-MM-DD、YYYY年M月D日",
                "金額の全角数字・カンマ区切りに対応",
              ].map(t => (
                <div key={t} style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, lineHeight: 1.8 }}>✓ {t}</div>
              ))}
            </div>

            {error && <div style={{ color: COLOR_NEGATIVE, fontSize: 12, marginBottom: 10 }}>⚠ {error}</div>}
            <button type="button" onClick={onClose} style={{ ...STYLE_BUTTON_OUTLINE, width: "100%", minHeight: 44, padding: "11px 18px" }}>キャンセル</button>
          </div>
        )}

        {/* ────── ステップ2: 列マッピング ────── */}
        {step === 2 && parsed && (
          <div>
            <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginBottom: 12, lineHeight: 1.6 }}>
              CSVの列を自動検出しました。間違っている場合は修正してください。
            </div>

            {/* 列マッピングの選択UI */}
            {(
              [
                { label: "📅 日付列", key: "dateCol" as keyof ColumnMap, required: true },
                { label: "💴 金額列", key: "amountCol" as keyof ColumnMap, required: true },
                { label: "📝 メモ列", key: "memoCol" as keyof ColumnMap, required: false },
              ] as { label: string; key: keyof ColumnMap; required: boolean }[]
            ).map(({ label, key, required }) => (
              <div key={key} style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginBottom: 5 }}>
                  {label}{required && <span style={{ color: COLOR_NEGATIVE }}> *</span>}
                </div>
                <select
                  value={colMap[key] ?? -1}
                  onChange={e => setColMap(m => ({ ...m, [key]: Number(e.target.value) === -1 ? null : Number(e.target.value) }))}
                  style={selectStyle}
                >
                  <option value={-1}>{"— 使わない —"}</option>
                  {parsed.headers.map((h, i) => (
                    <option key={i} value={i}>{h} （{parsed.rows[0]?.[i] ?? ""}）</option>
                  ))}
                </select>
              </div>
            ))}

            {/* 先頭5行のプレビュー */}
            <div style={{ marginTop: 16, marginBottom: 4 }}>
              <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginBottom: 6 }}>CSVの先頭3行（参考）</div>
              <div style={{ overflowX: "auto", fontSize: 12, color: COLOR_TEXT_HINT }}>
                <table style={{ borderCollapse: "collapse", width: "100%", minWidth: 280 }}>
                  <thead>
                    <tr>
                      {parsed.headers.map((h, i) => (
                        <th key={i} style={{
                          padding: "4px 8px", textAlign: "left",
                          borderBottom: `1px solid ${COLOR_BORDER}`,
                          color: [colMap.dateCol, colMap.amountCol, colMap.memoCol].includes(i) ? COLOR_ACCENT : COLOR_TEXT_HINT,
                          fontWeight: [colMap.dateCol, colMap.amountCol, colMap.memoCol].includes(i) ? 700 : 400,
                          whiteSpace: "nowrap",
                        }}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {parsed.rows.slice(0, 3).map((row, ri) => (
                      <tr key={ri}>
                        {row.map((cell, ci) => (
                          <td key={ci} style={{
                            padding: "4px 8px",
                            borderBottom: `1px solid rgba(255,255,255,0.04)`,
                            color: [colMap.dateCol, colMap.amountCol, colMap.memoCol].includes(ci) ? COLOR_TEXT_PRIMARY : COLOR_TEXT_HINT,
                            whiteSpace: "nowrap", maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis",
                          }}>
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {error && <div style={{ color: COLOR_NEGATIVE, fontSize: 12, marginBottom: 10 }}>⚠ {error}</div>}

            <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
              <button type="button" onClick={() => { setStep(1); setError(""); }} style={{ ...STYLE_BUTTON_OUTLINE, flex: 1, minHeight: 44, padding: "11px 18px" }}>
                ← 戻る
              </button>
              <button type="button" onClick={validateAndGoPreview} style={{ ...STYLE_BUTTON_PRIMARY, flex: 2 }}>
                プレビューへ →
              </button>
            </div>
          </div>
        )}

        {/* ────── ステップ3: プレビュー確認 ────── */}
        {step === 3 && (
          <div>
            {/* カテゴリ一括設定 */}
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginBottom: 5 }}>
                全行のカテゴリ（一括変更）
              </div>
              <select
                value={globalCategory}
                onChange={e => setGlobalCategory(e.target.value)}
                style={selectStyle}
              >
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            {/* 全選択・全解除 */}
            <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
              <button type="button"
                onClick={() => {
                  const s: Record<number, boolean> = {};
                  previewRows.forEach(r => { s[r.rowIndex] = true; });
                  setSelected(s);
                }}
                style={{ ...STYLE_BUTTON_OUTLINE, flex: 1, fontSize: 12, minHeight: 32, padding: "6px 8px" }}
              >
                全選択
              </button>
              <button type="button"
                onClick={() => {
                  const s: Record<number, boolean> = {};
                  previewRows.forEach(r => { s[r.rowIndex] = false; });
                  setSelected(s);
                }}
                style={{ ...STYLE_BUTTON_OUTLINE, flex: 1, fontSize: 12, minHeight: 32, padding: "6px 8px" }}
              >
                全解除
              </button>
            </div>

            {/* プレビューリスト（最大100件） */}
            <div style={{ maxHeight: "38vh", overflowY: "auto", marginBottom: 12 }}>
              {previewRows.slice(0, 100).map((r, idx) => {
                const isOk = r.date !== "" && r.amount > 0;
                const isSel = selected[r.rowIndex] !== false;
                return (
                  <div
                    key={r.rowIndex}
                    onClick={() => setSelected(s => ({ ...s, [r.rowIndex]: !s[r.rowIndex] }))}
                    style={{
                      ...STYLE_CSV_ROW_BASE,
                      background: isSel
                        ? (isOk ? "rgba(255,255,255,0.04)" : "rgba(248,113,113,0.06)")
                        : "rgba(255,255,255,0.01)",
                      border: `1px solid ${isSel ? (isOk ? "rgba(255,255,255,0.08)" : "rgba(248,113,113,0.2)") : "transparent"}`,
                      opacity: isSel ? 1 : 0.4,
                    }}
                  >
                    {/* チェックボックス代わりの丸バッジ */}
                    <div style={{
                      ...STYLE_CSV_BADGE_BASE,
                      border: `2px solid ${isSel ? COLOR_ACCENT : "rgba(255,255,255,0.2)"}`,
                      background: isSel ? "rgba(34,211,238,0.15)" : "transparent",
                    }}>
                      {isSel && <div style={{ width: 6, height: 6, borderRadius: "50%", background: COLOR_ACCENT }}/>}
                    </div>

                    {/* 日付 */}
                    <div style={{ fontSize: 12, color: r.date ? COLOR_TEXT_SECONDARY : COLOR_NEGATIVE, minWidth: 72, fontFamily: "monospace" }}>
                      {r.date || "日付NG"}
                    </div>

                    {/* メモ */}
                    <div style={{ flex: 1, fontSize: 12, color: COLOR_TEXT_HINT, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {r.memo || `行${idx + 1}`}
                    </div>

                    {/* 金額 */}
                    <div style={{ fontFamily: "monospace", fontSize: 12, fontWeight: 700, color: r.amount > 0 ? COLOR_TEXT_PRIMARY : COLOR_NEGATIVE, flexShrink: 0 }}>
                      {r.amount > 0 ? `¥${r.amount.toLocaleString()}` : "金額NG"}
                    </div>
                  </div>
                );
              })}
              {previewRows.length > 100 && (
                <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, textAlign: "center", padding: 8 }}>
                  ※ 先頭100件を表示（全{previewRows.length}件）
                </div>
              )}
            </div>

            {/* 選択件数と合計金額 */}
            {(() => {
              const selRows = previewRows.filter(r => selected[r.rowIndex] && r.amount > 0 && r.date);
              const total = selRows.reduce((s, r) => s + r.amount, 0);
              return (
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: COLOR_TEXT_SECONDARY, marginBottom: 12, padding: "8px 0", borderTop: `1px solid ${COLOR_BORDER}` }}>
                  <span>{selRows.length}件を登録</span>
                  <span style={{ fontFamily: "monospace", fontWeight: 700, color: mode === "expense" ? COLOR_NEGATIVE : COLOR_POSITIVE }}>
                    合計 ¥{total.toLocaleString()}
                  </span>
                </div>
              );
            })()}

            {error && <div style={{ color: COLOR_NEGATIVE, fontSize: 12, marginBottom: 10 }}>⚠ {error}</div>}

            <div style={{ display: "flex", gap: 8 }}>
              <button type="button" onClick={() => { setStep(2); setError(""); }} style={{ ...STYLE_BUTTON_OUTLINE, flex: 1, minHeight: 44, padding: "11px 18px" }}>
                ← 戻る
              </button>
              <button type="button" onClick={handleImport} style={{ ...STYLE_BUTTON_PRIMARY, flex: 2 }}>
                📥 インポート実行
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
