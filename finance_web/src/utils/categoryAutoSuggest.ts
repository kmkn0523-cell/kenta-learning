// ────────── メモからカテゴリを自動推定するユーティリティ ──────────
// 入力されたメモ文字列を使い、過去の取引履歴の中から
// 同じ（または似た）メモに対して最も多く使われたカテゴリを返す。
// AIや外部APIを使わず、完全にローカルで動く。

// メモを持つ取引の最小型（Tx 全体を引数にしなくても動くよう最小化）
interface TxLike {
  memo: string;
  category: string;
}

/**
 * memo に対して最も使われているカテゴリ名を返す。
 *
 * マッチング方式:
 *   入力 memo（2文字以上）が過去取引の memo に「部分一致」する件数を集計し、
 *   最多カテゴリを返す。大文字小文字・前後スペースは無視。
 *
 * @param memo       - ユーザーが入力したメモ文字列
 * @param pastTx     - 過去の取引履歴（memo と category だけ使う）
 * @returns カテゴリ名（候補なしの場合は null）
 */
export function suggestCategory(memo: string, pastTx: TxLike[]): string | null {
  // 入力が短すぎる場合は推定しない（誤マッチを防ぐため2文字以上を要件とする）
  const trimmed = memo.trim().toLowerCase();
  if (trimmed.length < 2) return null;

  // 過去取引のうち、メモがtrimmedを含むものを抽出
  const matched = pastTx.filter(
    t => t.memo && t.memo.trim().toLowerCase().includes(trimmed)
  );

  // 一致する取引がなければ候補なし
  if (matched.length === 0) return null;

  // カテゴリごとの出現回数を集計
  const counts: Record<string, number> = {};
  for (const t of matched) {
    counts[t.category] = (counts[t.category] || 0) + 1;
  }

  // 最も出現回数が多いカテゴリを選ぶ
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  return sorted[0]?.[0] ?? null;
}
