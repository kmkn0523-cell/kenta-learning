// ──────── 月次サマリー書き出しユーティリティ ────────
// 月次サマリー画面の「計算」と「書き出し（CSV・画像）」をまとめたファイル

// 貯蓄率を計算する純粋関数
// net（手残り）を income（収入合計）で割って百分率にする
// income が0以下のときはゼロ除算を避けて 0 を返す
// 小数第1位まで（例: 33.33... → 33.3）に丸める
export function computeSavingRate(net: number, income: number): number {
  if (income <= 0) return 0;
  return Math.round((net / income) * 100 * 10) / 10;
}
