// ────────── データ出力ユーティリティ ──────────
// CSV/JSON エクスポートとファイルダウンロードをまとめた関数群
import { Tx } from "../types";

// CSV式インジェクション対策：
// メモやカテゴリ名が = + - @ や制御文字(タブ・改行)で始まると、ExcelやGoogleスプレッドシートが
// それを「数式」と解釈して実行してしまう（例: =1+2、@SUM、外部URLの呼び出し等）。
// 文字列セルの先頭がこれらの場合だけ、先頭に ' を付けて「ただの文字」として無害化する。
// 数値(amount等)はアプリ側で生成する安全な値なので対象にしない。
function neutralizeFormula(value: string | number): string {
  if (typeof value !== "string") return String(value); // 数値はそのまま
  // 先頭文字が数式トリガーなら ' を付ける（= + - @ タブ CR 改行）
  return /^[=+\-@\t\r\n]/.test(value) ? "'" + value : value;
}

// RFC 4180 準拠：カンマ・ダブルクオート・改行を含むセルをクオートで囲む
function csvCell(value: string | number): string {
  // 先に式インジェクションを無害化してから、RFCのクオート処理にかける
  const str = neutralizeFormula(value);
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
