// ──────── 月次サマリー書き出しユーティリティ ────────
// 月次サマリー画面の「計算」と「書き出し（CSV・画像）」をまとめたファイル

import type { SummaryStats } from "../types";

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
