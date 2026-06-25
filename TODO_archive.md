# TODO 完了アーカイブ

`TODO.md` から完了済み（`[x]`）のタスクを退避した置き場です。やる気アップ用＆経緯確認用に残します。
未完了タスクは `TODO.md` を見てください。

最終整理: 2026/06/25

---

## 0. 家計管理アプリ（finance_web）

#### インフラ
- [x] Vercel 本番デプロイ（financeweb-nine.vercel.app）
- [x] パスワードを各自設定できる仕組みに変更
- [x] パスワードリセット機能追加

#### アフィリエイト
- [x] A8.net 登録
- [x] バリューコマース 登録
- [x] アフィリエイトB 登録
- [x] 審査通過を確認する（審査通過済み）
- [x] 取得できたブランドのアフィリエイトリンクをアプリに組み込む（2026/05/17 cf/bl/loタブにバナー追加・Vercelデプロイ済み。承認済み4件のpx.a8.netリンクをAFFILIATE定数に設定完了：フジトミ証券/DMM株/TOSSY/マネーフォワード。残りはA8.net審査通過後に差し替え）

#### 機能追加
- [x] **v1.6.0 リリース（収益ファースト・ブラッシュアップ）**（2026/06/11 実装完了）
  - [x] 壊れたアフィリエイトリンク5件（審査待ちプレースホルダー）を非表示化。広告定義を `src/utils/affiliates.ts` に一元化
  - [x] 診断連動の提案枠：家計診断カード＋月次レポートに文脈が合う時だけ広告1枠（貯蓄率20%以上→投資系・2〜3月→確定申告）
  - [x] 設定タブに「📣 友達に教える」シェアカード（Web Share API＋URLコピー）
  - [x] サマリーPNG書き出しにアプリURL透かし（シェア画像が宣伝になる）
  - [x] バージョン表記3箇所バラバラ問題をviteのdefineで一元化
  - [x] gitignore漏れでリポジトリ未登録だったテスト7件を追加（テスト153件全パス）
  - 設計書: `finance_web/docs/superpowers/specs/2026-06-11-monetize-brushup-design.md`
- [x] OGP設定（SNSシェア時にカード表示・2026/05/19確認時すでに実装＆ogp.pngデプロイ済み）
- [x] **v1.5.0 リリース**（2026/05/24 デプロイ済み）
  - [x] 📊 カテゴリ別支出割合の円グラフ（概要タブ・月別ドーナツグラフ）
  - [x] 📥 CSVエクスポート（設定タブ・全期間の支出+収入をCSVダウンロード）
- [x] **v1.4.0 リリース**（2026/05/24 デプロイ済み）
  - [x] ⚡定期支出：繰り返し変動費（Netflix・ジム代等）の自動追加機能（支出タブ）
  - [x] 📈純資産推移グラフ：過去12ヶ月の累積手残りチャート（概要タブ）
  - [x] 🗑️一括削除：指定月末以前の支出・収入・振替を一括削除（設定タブ）
  - [x] バックアップに `kk_rec_exp`（繰り返し支出）を追加

---

## 1. @RoninWords（Threads/X/LinkedIn）

#### 運用
- [x] Facebook認証問題解決・APIキー取得・.envに設定（2026/04/27完了）
- [x] GitHub Actions自動投稿稼働（cron混雑回避で17分発火に修正済み）
- [x] Day31以降のThreads投稿文を作る（Day31〜60完成・threads_posts.jsonに追加済み）
- [x] LinkedIn 自動投稿システム実装完了（Task 1-7全て完了・GitHub Actions デプロイ済み）
  - [x] Task 1: API設定・OAuth認証ツール作成
  - [x] Task 2-3: linkedin_auto_post.py（Day1-60ローテーション・自動投稿）
  - [x] Task 4: linkedin_analytics.py（エンゲージメント計測）
  - [x] Task 5: GitHub Actions ワークフロー（毎週金曜17:00JST自動実行）
  - [x] Task 6: ローカル統合テスト完了
  - [x] Task 7: デプロイメント検証完了

#### フォロワー成長機構（2026/05/07 新規実装・完全完了）
- [x] ハッシュタグ戦略（3セット: 基本・アクション・感情） → threads_posts.json に追加
- [x] エンゲージメント促進（いいね×1.0 + コメント×2.5 + シェア×5.0） → engagement_score 算出
- [x] 投稿時間最適化（データ収集→分析で最適時間を検出） → ronin_analyzer.py で best_hour 計算
- [x] 高反応パターン自動選別（Day21以降の優先度ランキング） → ronin_optimizer.py で pattern_ranking 生成
- [x] GitHub Actions 毎日自動実行（06:00: データ収集、07:00: 分析・最適化） → ronin_analytics_daily.yml デプロイ済み
- [x] ronin_data_collector.py（Threads API データ取得）完成
- [x] ronin_analyzer.py（パターン分析）完成
- [x] ronin_optimizer.py（最適化インデックス生成）完成
- [x] ronin_threads_auto_post.py 改造（Day21チェック・最適化投稿分岐）完成
- [x] ローカル統合テスト（全スクリプト合格）実施完了
- [x] GitHub Actions デプロイ（ronin_analytics_daily.yml 登録・動作確認）完了

#### 改善
- [x] 画像投稿対応（書道カード画像をThreadsに自動投稿）
- [x] **ronin_analyzer「現在: 0日」問題**（2026/06/07 修正：`should_analyze` が `posts_history[0]` を最古と仮定していたのを、全件 `min` で最古を求める `earliest_post_datetime` に変更）

#### reach加速（2026/06/07・feature/ronin-reach-boost → main マージ済み）
- [x] コメント誘発engagement投稿32本（6型×5＋種2・`ronin/ronin_engagement_posts.json`）。4投稿に1回自動差し込み
- [x] 投稿直後の1コメ目自動シード（`reply_to_id`・早期リプライで非フォロワー拡散）。ライブ実証済み（本投稿18108549884317438＋1コメ目17967528567091426）
- [x] ハッシュタグ動的ローテーション（固定5個→4セット・越境タグ #StoicMindset 等で新規流入・`ronin/ronin_hashtags.py`）
- [x] Gumroad/SubstackのCTAを本文から1コメ目へ移動（本文クリーン化で配信抑制回避）
- [x] 死んだ最適化パス（should_use_optimization/post_optimized）を撤去し本線を単純化
- [x] `--dry-run` 追加・テスト24件 全通過・設計書/計画書を `docs/superpowers/` に追加

---

## 2. 肌荒れ改善note（skin）

#### 自動化
- [x] Meta for Developers認証・APIキー取得
- [x] Threads自動投稿をGitHub Actionsに乗せる
- [x] cron混雑回避（毎時30分発火に修正済み）

#### フォロワー成長機構（2026/05/07 新規実装・完全完了）
- [x] ハッシュタグ戦略（3セット: 基本・ケア・症状別） → skin_threads_posts.json に追加
- [x] エンゲージメント促進（いいね×1.0 + コメント×2.5 + シェア×5.0） → engagement_score 算出
- [x] 投稿時間最適化（データ収集→分析で最適時間を検出） → skin_analyzer.py で best_hour 計算
- [x] 高反応パターン自動選別（Day21以降の優先度ランキング） → skin_optimizer.py で pattern_ranking 生成
- [x] GitHub Actions 毎日自動実行（06:00: データ収集、07:00: 分析・最適化） → skin_analytics_daily.yml デプロイ済み
- [x] skin_data_collector.py（Threads API データ取得）完成
- [x] skin_analyzer.py（パターン分析）完成
- [x] skin_optimizer.py（最適化インデックス生成）完成
- [x] skin_threads_auto_post.py 改造（Day21チェック・最適化投稿分岐）完成
- [x] ローカル統合テスト（全スクリプト合格）実施完了
- [x] GitHub Actions デプロイ（skin_analytics_daily.yml 登録・動作確認）完了

#### 自動リプライ・エンジン
- [x] 停止時にworkflowがfailureになるバグ修正（2026/06/20・履歴ファイル無しならコミットskip・commit ff36acf）

#### Threadsリライト（A/B構造化）
- [x] Batch 1（テーマ1-20、40セット）リリース完了（2026/05/18・コミット 38cf4da）
  - [x] A/B選択ロジック実装（skin_threads_action.py・15テストPASS）
  - [x] skin_ab_report.py（A/B勝者判定スクリプト）作成
  - [x] テーマ1-20 のA/B 全40セット制作（薬機法準拠：辞書形＋活用形NG 0件）
  - [x] バッチ進行管理ファイル（skin_threads_batch_progress.json）作成
- [x] **A/B検証の配線切れを修正（2026/06/25）**：反応スコアが永遠に0だった根本原因（反応収集データを`ab_results`へ反映する処理が未実装）を特定。`skin_ab_report.py`に`aggregate_ab_scores`/`aggregate_format_scores`/`judge_format`を追加（TDD・テスト194件全パス）。設計書: `docs/superpowers/specs/2026-06-25-skin-ab-format-aggregation-design.md`
- [x] **フォーマット全体A/B判定が出た（2026/06/25）**：テーマ単位は108全ローテーションで1サンプルずつしか溜まらず判定不能と判明 → テーマ横断で「A型 vs B型」を集計する方式に変更。結果 **A型（既存）平均1.69% / B型（新フォーマット）平均0.66% → A型の勝ち（差60.8%）**。確認は `python3 skin/skin_ab_report.py --batch 1` の末尾「フォーマット全体A/B」

#### Instagram自動投稿
- [x] GitHub Actions有効化・稼働中（2026/05/12）
- [x] 重複4テーマ差し替え（2026/05/20）
  - ID10: グルテンやめて1ヶ月 → 乳製品をやめて1ヶ月で起きた変化
  - ID12: 洗顔を減らしたら起きた5つの変化 → コンビニで買える美肌食ベスト7
  - ID19: 発酵食品を毎日 → ニキビの場所でわかる体からのサイン
  - ID20: 今日から始めるToDo7選 → やってはいけない逆効果スキンケア7つ
  - 画像も再生成＆GitHub push済（commit 43757ef）
- [x] v1（5枚）/v2（8枚）の4:1交互投稿ロジック実装（2026/05/20・commit d00b1b1）
  - 5投稿に1回 v2 を挟む。progress.json を {v1_index, v2_index, post_count} に拡張
- [x] 投稿頻度を1日4回→2回に削減（2026/05/20・commit 1cea40e）
  - 7:00 / 19:00 JST に集約。1周5日→10日に伸ばしてネタ切れ防止

#### note販売
- [x] noteの価格を決める
- [x] note公開日を決める
- [x] **note 完全自動投稿システム実装完了**（2026-05-23・月水金9:00 JST）
  - Playwrightでnote.comにヘッドレス自動投稿（`skin/post_to_note.py`）
  - 投稿成功/失敗をメール通知（`skin/send_note_email.py`）
  - 失敗時はスクリーンショットをアーティファクト保存
  - 進捗履歴 `note_queue_progress.json` の `history[]` に追加
  - 旧 `generate_note_page.py` / `note_article.html` は削除
- [x] **note 自動投稿の手動セットアップ（4ステップ・完了）**
  - [x] ① クッキー取得：note.com にログイン状態でブラウザDevTools → Application → Cookies → `_note_session_v5` の Value をコピー（手順: `docs/note_cookie_setup.md`）
  - [x] ② GitHub Secrets 登録：Name=`NOTE_SESSION_V5` に値を貼り付けて Add secret
  - [x] ③ 手動テスト実行：`gh workflow run skin_note_release.yml` で成功メール確認
  - [x] ④ cron-job.org スケジュール設定：「月水金 9:00 JST」に変更
- [x] 睡眠テーマの無料note（note_article_sleep.md）をnoteに投稿する

#### 今週やること（旧）
- [x] Task 8: Instagram Batch 1 初動チェック（v2 8枚カルーセル4件・公開確認済み 2026-05-20）
- [x] Task 4: Instagram insights 権限申請（`instagram_manage_insights` は両IGトークンに付与済みと2026/06/25確認）
- [x] note: 肌荒れ改善noteの販売準備（価格設定・公開日決め）
- [x] 肌荒れ改善Threads: 画像投稿対応（Pillowで画像生成→GitHub→Threads）
- [x] @RoninWords: Day31以降のThreads投稿文を作る（Day31〜60完成）

> 完了済み（5/18〜5/19）: プロフィールv2・ヘッダー画像（IG版含む）・観測対象10アカウント・日次ログ雛形
> 計画書: `docs/superpowers/plans/2026-05-18-skin-monetize-m1-w1-w2.md`（M1 Week 1-2 全8タスク）
> 上位スペック: `docs/superpowers/specs/2026-05-18-skin-monetize-roadmap-design.md`（半年ロードマップ・月3〜5万円目標）

---

## 3. Python学習
- [x] 定期実行の仕組み（cron / クラウド）← GitHub Actionsで達成

---

## 4. インフラ・自動化
- [x] auto_sync.sh（自動バックアップ）
- [x] GitHub Actionsの仕組み構築（skin + @RoninWords両方稼働中）
- [x] Claude Code ステータスバー整備（蛍光水色・気温幅・使用率・カニ停止）
- [x] Claude Code 設定をGitHub同期 → MacBookでもすぐ同じ環境が使える
- [x] Facebook認証問題を解決してAPIキー取得（skin + ronin両方）
- [x] cron混雑回避修正（skin=7分・ronin=17分発火）
- [x] 60日後トークン期限リマインドをスケジュール予約（2026/06/20 9:00）
- [x] GitHub Actionsワークフロー全面整備（2026/05/15）
  - 全11ワークフローに `concurrency: group: git-push-main` 追加（push競合完全解消）
  - 全ワークフローに `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` 追加（Node.js 20廃止対応）
  - 全ワークフローのgit pushに3回リトライループ追加
  - skin_instagram_watchdog を48回/日 → 8回/日に削減
  - ronin/skinアナリティクスのgit設定バグ修正（|| true → if guard）
- [x] 投稿ログを1箇所にまとめて見られるようにする（2026/06/04 `reaction_dashboard.py` 実装。skin/ronin全SNS＝Threads/Instagram/note/Substackの投稿数と反応を `dashboard.md` に集約。標準ライブラリのみ・既存JSONは読むだけ）
- [x] 反応収集・分析まわりのバグ修正（2026/06/04）
  - ronin/skin analyzer の日付解析を `+0000`（コロン無しのタイムゾーン表記）に対応（commit c2d0d3d）
  - ronin 反応収集の comments 取得件数を 500 に修正

---

## 💡 アイデア（完了分）
- [x] Instagram連携（@RoninWords Instagram自動投稿 毎日21:17 JST・GitHub Actions稼働）
- [x] ホーム直下のファイル数が多すぎる問題 → フォルダ分け（2026/05/12完了）

---

## ✅ 日付ログ（やる気アップ用）
- [x] 2026/04/23 環境構築・おみくじ作成
- [x] 2026/04/24 じゃんけん・天気予報作成
- [x] 2026/04/25 タイマー・数当て・曜日表示・CLAUDE.md作成
- [x] 2026/04/26 @RoninWords Threads自動投稿スクリプト＋GitHub Actions構築
- [x] 2026/04/26 肌荒れ改善noteコンテンツ・Threads投稿スクリプト作成
- [x] 2026/04/26 肌荒れ改善Threadsを手動でローテーション投稿（型①〜⑦の1周完了）
- [x] 2026/04/27 ステータスバー整備（蛍光水色・気温幅追加・使用率バグ修正・Linux/Mac両対応）
- [x] 2026/04/27 Claude Code設定をGitHub同期（MacBookでもすぐ使える環境に）
- [x] 2026/04/27 Meta認証突破・skin + ronin両アカウントのThreads APIキー取得
- [x] 2026/04/27 @RoninWordsのThreads完全自動化（1日4回・GitHub Actions稼働）
- [x] 2026/04/27 skin/roninのcron混雑問題修正（0分→7分/17分発火）
- [x] 2026/04/27 60日後トークン更新・翌日cron確認のリマインドをスケジュール予約
- [x] 2026/05/07 @RoninWords LinkedIn自動投稿システム実装完了（Task 1-7、エラーハンドリング・デバッグログ・重複検出・タイムアウト対応含む・GitHub Actions デプロイ済み・アカウント作成待ち）
