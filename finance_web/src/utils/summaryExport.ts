// ──────── 月次サマリー書き出しユーティリティ ────────
// 月次サマリー画面の「計算」と「書き出し（CSV・画像）」をまとめたファイル

import html2canvas from "html2canvas";
import type { SummaryStats } from "../types";
import { downloadFile } from "./dataExport";

// 貯蓄率を計算する純粋関数
// net（手残り）を income（収入合計）で割って百分率にする
// income が0以下のときはゼロ除算を避けて 0 を返す
// 小数第1位まで（例: 33.33... → 33.3）に丸める
export function computeSavingRate(net: number, income: number): number {
  if (income <= 0) return 0;
  return Math.round((net / income) * 100 * 10) / 10;
}

// CSVの1セルを安全な文字列にする（カンマ・改行・ダブルクォートを含む場合は囲む）
// RFC4180準拠：セル内のダブルクォートは2個重ねでエスケープする
function csvCell(value: string): string {
  if (/[",\n]/.test(value)) {
    return '"' + value.replace(/"/g, '""') + '"';
  }
  return value;
}

// 月次サマリーを縦持ちCSV文字列にする（純粋関数）
// previous が null なら2列、あれば3列で前月値も並べる。末尾は改行で終わる
export function buildSummaryCsv(
  monthLabel: string,
  current: SummaryStats,
  previous: SummaryStats | null,
  categoryBreakdown: { category: string; amount: number }[],
): string {
  void monthLabel; // ファイル名生成側で使う。CSV本文では今は未使用だが引数として保持する
  const lines: string[] = [];

  if (previous) {
    // 3列ヘッダー（当月・前月）
    lines.push("項目,当月,前月");
    lines.push(`収入合計,${current.income},${previous.income}`);
    lines.push(`支出合計,${current.expense},${previous.expense}`);
    lines.push(`手残り,${current.net},${previous.net}`);
    lines.push(`貯蓄率,${current.savingRate}%,${previous.savingRate}%`);
  } else {
    // 2列ヘッダー（当月のみ）
    lines.push("項目,金額");
    lines.push(`収入合計,${current.income}`);
    lines.push(`支出合計,${current.expense}`);
    lines.push(`手残り,${current.net}`);
    lines.push(`貯蓄率,${current.savingRate}%`);
  }

  // カテゴリ内訳がある場合は空行を挟んで別ブロックとして並べる
  if (categoryBreakdown.length > 0) {
    lines.push(""); // 空行で区切る
    lines.push("カテゴリ,金額");
    for (const row of categoryBreakdown) {
      lines.push(`${csvCell(row.category)},${row.amount}`);
    }
  }

  // 各行を改行でつなぎ、末尾にも改行を付ける
  return lines.join("\n") + "\n";
}

// 月次サマリーをCSVファイルとして保存する
// buildSummaryCsv で本文を組み立て、downloadFile でブラウザにダウンロードさせる
export function exportSummaryCsv(
  monthLabel: string,
  current: SummaryStats,
  previous: SummaryStats | null,
  categoryBreakdown: { category: string; amount: number }[],
): void {
  const csv = buildSummaryCsv(monthLabel, current, previous, categoryBreakdown);
  // ファイル名は「サマリー_2026年5月.csv」のような形にする
  const fileName = `サマリー_${monthLabel}.csv`;
  // 文字コード（utf-8）を明示してExcelでも文字化けしにくくする
  downloadFile(fileName, csv, "text/csv;charset=utf-8");
}

// 透かしに入れる文言（シェアされた画像からアプリにたどり着けるようにする）
export const WATERMARK_TEXT = "BYB — financeweb-nine.vercel.app";

// PNG画像の下に透かし帯（アプリ名＋URL）を追加した新しいcanvasを返す
// 2Dコンテキストが取れない環境では透かしなしの元canvasをそのまま返す
export function appendWatermark(source: HTMLCanvasElement): HTMLCanvasElement {
  const FOOTER_HEIGHT = 56; // 帯の高さ（scale:2 で出力されるので実質28px相当）
  const output = document.createElement("canvas");
  output.width = source.width;
  output.height = source.height + FOOTER_HEIGHT;
  const context = output.getContext("2d");
  if (!context) return source;

  // 背景をアプリの背景色で塗ってから、元の画像を上に重ねる
  context.fillStyle = "#0a0a0c";
  context.fillRect(0, 0, output.width, output.height);
  context.drawImage(source, 0, 0);

  // 帯の中央に小さくアプリ名とURLを描く
  context.font = "22px monospace";
  context.fillStyle = "#9a9aa3";
  context.textAlign = "center";
  context.fillText(WATERMARK_TEXT, output.width / 2, source.height + 36);
  return output;
}

// 月次サマリーの表示エリア（DOM）をPNG画像にして保存する
// html2canvas で画面の見た目を画像化し、Blob 経由でダウンロードさせる
export async function exportSummaryImage(node: HTMLElement, fileName: string): Promise<void> {
  // node（サマリーカードのまとまり）を画像化してから下部に透かし帯を追加する
  // backgroundColor はアプリの背景色に合わせる。scale:2 で高解像度にする
  const canvas = appendWatermark(await html2canvas(node, { backgroundColor: "#0a0a0c", scale: 2 }));

  // canvas を Blob（画像データのかたまり）に変換する。コールバックをPromiseで包む
  const blob = await new Promise<Blob | null>((resolve) => {
    canvas.toBlob((result) => resolve(result), "image/png");
  });

  // Blob が作れなかった場合はエラーにして呼び出し側で気づけるようにする
  if (!blob) {
    throw new Error("画像の生成に失敗しました");
  }

  // Blob から一時的なURLを作り、リンクをクリックしてダウンロードさせる
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  // 使い終わった一時URLは解放してメモリを無駄にしない
  URL.revokeObjectURL(url);
}
