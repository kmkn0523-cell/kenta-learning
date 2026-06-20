# skin Threads「投稿の外側」自動化強化 設計書

最終更新: 2026-06-20
関連: `docs/superpowers/specs/2026-05-18-skin-monetize-roadmap-design.md`（上位ロードマップ）、
`docs/superpowers/specs/2026-06-13-skin-threads-content-overhaul-design.md`（投稿本体の刷新）

## 1. 背景・現状診断（2026-06-20 時点）

skin（@skin_reset_jp）の Threads は自動投稿の仕組みが高度に揃っているが、数字が伸びていない。

- Threads 直近の投稿: views 33〜90 / いいね **全投稿0** / コメント1（=自分の1コメ目シードのみ）/ リポスト0
- Instagram: フォロワー **1人のまま約1ヶ月停滞**
- 手動リプ運用: 日次ログ全欄空白（=手動作業は続いていない実績）
- 6/10 の大規模リライトの効果は、まだ数字に出ていない

### 構造的ボトルネック
`reach（閲覧）が極小` × `エンゲージ（いいね/保存/リポスト）が実質ゼロ` の二重苦。
入口（プロフィール流入）と拡散の燃料（保存・リポスト・返信）の両方が枯れている。

### 見つかった機会損失
1. **リプライエンジンが停止中** — `SKIN_REPLY_ENGINE_ENABLED` が GitHub 変数に存在せず、6回/日のワークフローが起動のたび即停止。views/いいねゼロを"外側から"破れる唯一の自動手段が動いていない。
2. **CTAのnote誘導がテーマ非連動** — `pick_cta_note_url` が投稿テーマと無関係なローテ。睡眠の投稿に乳製品noteが出るなど、転換率を自ら下げている。

## 2. 制約

- **A/B測定中（〜2026-06-24）**: `skin_threads_posts.json` の `threads_a`（128テーマ）の番号には一切触らない。測定データを守る。
- 投稿本体（フック文・テーマ）の刷新は 6/24 以降（別作業）。
- 自動投稿スクリプトの停止/開始、ワークフローの大きな変更はユーザー承認が必要。

## 3. 方針

「投稿の**外側**」を **reach × 収益導線の両輪** で自動強化する。投稿番号は凍結したまま、その周辺（CTA・1コメ目・リプ営業・分析）を磨き込む。各施策は **TDD（テストファースト）** で1つずつ実装・検証する。

## 4. コア4施策

### 施策1: CTAのnoteテーマ連動（収益）
- 新規 `skin/skin_note_matcher.py`（純粋関数）。投稿テーマ名＋本文のキーワードから、最も合う無料note（`note_promo_articles.json` の19本）を選ぶ。マッチしなければ空文字。
- `skin_threads_action.py` の `pick_cta_note_url(count)` を `pick_cta_note_url(count, theme="", text="")` に拡張。テーマ優先 → 従来のローテにフォールバック。
- 効果: 投稿内容と一致したnoteが1コメ目に出るので、クリック・読了・note誘導の転換率が上がる。既存リンクのみ使用＝壊れない。

### 施策2: リプエンジン品質強化＋小さく開始（reach）
- `skin_comment_templates.py` のテンプレ母数を拡充（署名分散＝スパム判定回避）。`skin_reply_engine.py` の `OPENERS` も増やす。
- `skin_reply_engine_config.json` の `daily_cap` を 25→**10**、`per_run` を控えめに（小さく開始）。
- 有効化スイッチ ON（`SKIN_REPLY_ENGINE_ENABLED=true`）は品質強化後に**ユーザー最終承認**を得てから。数日様子を見て安全なら増量。

### 施策3: 1コメ目シードのテーマ連動問いかけ（エンゲージ）
- `skin_comment_seeder.py` に theme連動の問いかけマップと `pick_seed_question(count, theme="")` を追加（汎用5種はフォールバック）。
- `skin_threads_action.py` の human_post 分岐で theme を渡す。
- 効果: テーマに刺さる問いかけで返信を誘発 → 会話シグナル → reach 拡大。

### 施策4: 週次自動レポート（運用）
- 新規 `skin/skin_weekly_report.py`。既存 `skin_analyzer.py`（成績分析）と `skin_ab_report.py`（A/B判定）を束ね、直近7日の views/likes/engagement 推移・伸びた投稿Top5・A/B判定・次の打ち手を人間可読で出力（`skin_weekly_report.md` 書き出し＋stdout）。
- 効果: 6/24 のA/B判定と運用判断を自動化。ユーザーが状況を一目で把握できる。
- ワークフロー化（cron＋通知）は別途ユーザー承認。

## 5. 検証

- 各施策で `tests/test_*.py` をTDDで追加し、`pytest skin/tests/` 全パスを確認。
- `skin_threads_action.py` の dry-run でCTA/シード連動が壊れていないか確認（投稿しない）。
- `skin_weekly_report.py` を実機データで実行して目視。

## 6. スコープ外（第2段・今回やらない）

- リール品質強化（テロップ焼き込み・BGM確認）
- アフィリ登録手順の1枚化（楽天/afb登録はユーザー作業）
- 投稿本体（フック・新規18本）の投入（6/24以降）
