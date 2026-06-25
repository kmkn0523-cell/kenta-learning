# skin Threads A/B検証 フォーマット全体集計 設計メモ

作成日: 2026/06/25

## 背景・問題

skin Threads の A/B検証（A型＝既存フォーマット / B型＝新フォーマット）は、勝者判定が永遠にできない状態だった。原因は2つ。

1. **配線切れ**（本日修正済み）: 投稿時に `a_posts`/`b_posts`（投稿回数）はカウントしていたが、反応スコア（`a_score`/`b_score`）を `skin_analytics.json` から埋める処理がコードのどこにも存在しなかった。`ab_results` のスコアが全108テーマで 0.0 のままだった。
   - 修正: `aggregate_ab_scores(history, posts_history)` を `skin_ab_report.py` に追加し、投稿履歴(history)と反応データ(posts_history)を post_id で突き合わせて `engagement_rate` を集計するようにした。

2. **テーマ単位判定の非現実性**: テーマ選択は `daily_index % 108 + 1` の全テーマ順繰り。同じテーマが戻るのは108投稿ごとで、A/Bは毎回反転する。1テーマでAを3サンプル集めるには理論上432投稿（1日4回で100日超）かかる。テーマ単位（min_posts=3）の判定はデータ量的に成立しない。

## 方針

A/B検証で知りたいのは「テーマごとの文面勝敗」ではなく「**A型とB型、どちらのフォーマットが全体として伸びるか**」（フォーマット改善の効果測定）。よってテーマをまたいで A型全体 vs B型全体 を集計する。

今あるデータ（A型101件・B型102件）での試算で、A型 平均1.69% / B型 平均0.66% と明確な差（60.8%）が出ており、この方針の妥当性は実証済み。

## 設計

### 1. `aggregate_format_scores(history, posts_history)` （純粋関数・新規）
- テーマをまたいで variant=A/B ごとに `engagement_rate` のリストを集める。
- 反応データ（analytics）に post_id が無い投稿は除外。theme_id/variant/post_id が欠けた履歴も除外（`aggregate_ab_scores` と同じルール）。
- 返り値: `{"A": {"count": n, "mean": x, "median": y}, "B": {...}}`。サンプル0件なら mean/median は 0.0。

### 2. 判定ルール `judge_format(stats, min_samples=20, min_lead=0.2)`
- 両型が `min_samples`（20件）未満 → `insufficient_data`。
- 平均の差（`|a_mean - b_mean| / max(a_mean, b_mean)`）が `min_lead`（20%）未満 → `no_significant_diff`。
- それ以上で平均が高い方を勝者（`A_wins` / `B_wins`）。

### 3. レポート出力
- `skin_ab_report.py` の出力末尾に「=== フォーマット全体A/B ===」セクションを追加。
- A型/B型の 件数・平均・中央値・勝者・差% を表示。既存のテーマ別表示は残す（参考情報）。

### 4. 非対象（YAGNI）
- t検定など統計的有意性検定は入れない（平均と中央値の併記で十分・未経験者には過剰）。
- `skin_threads_progress.json` への書き戻しはしない（毎回フレッシュ集計・既存方針を踏襲）。

## テスト（TDD）
- `aggregate_format_scores`: A/B各複数件で件数・平均・中央値が正しい / 反応データ無しを除外 / 不完全な履歴を除外。
- `judge_format`: サンプル不足 / 差なし / A勝ち / B勝ち。
