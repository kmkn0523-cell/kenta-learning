// ────────── データ出力ユーティリティ ──────────
// CSV/JSON エクスポートとファイルダウンロードをまとめた関数群
import { Tx } from "../types";

// RFC 4180 準拠：カンマ・ダブルクオート・改行を含むセルをクオートで囲む
function csvCell(value: string | number): string {
  const str = String(value);
  // カンマ・ダブルクオート・改行が含まれていたらクオートが必要
  const needsQuote = /[",\n]/.test(str);
  if (!needsQuote) return str;
  // ダブルクオートは "" に変えてからクオートで囲む
  return '"' + str.replace(/"/g, '""') + '"';
}

// 取引一覧を CSV 文字列に変換する
export function transactionsToCsv(transactions: Tx[]): string {
  const header = "date,category,amount,memo\n";
  const rows = transactions
    .map(tx => [tx.date, tx.category, tx.amount, tx.memo || ""].map(csvCell).join(","))
    .join("\n");
  // データがある時だけ末尾に改行を付ける
  return header + (rows ? rows + "\n" : "");
}

// オブジェクトをインデント付きの JSON 文字列に変換する
export function exportAsJson(data: object): string {
  return JSON.stringify(data, null, 2);
}

// ブラウザにファイルとしてダウンロードさせる
export function downloadFile(filename: string, content: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
