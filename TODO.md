# TODO リスト

最終更新: 2026/06/04（SNS反応集約ダッシュボード reaction_dashboard.py 実装・analyzerの日付解析/反応収集バグ修正）

---

## 🔥 今週やること（最優先・3つだけに絞る）

- [x] Task 8: Instagram Batch 1 初動チェック（v2 8枚カルーセル4件・公開確認済み 2026-05-20）
- [ ] Task 4: Instagram insights 権限申請（Facebook Developer Console で `instagram_manage_insights`）
- [ ] Week 2 (5/25〜) リプ運用準備 — `skin/skin_account_targets.json` の10アカウントの最新投稿を再確認

> 完了済み（5/18〜5/19）: プロフィールv2・ヘッダー画像（IG版含む）・観測対象10アカウント・日次ログ雛形
> 計画書: `docs/superpowers/plans/2026-05-18-skin-monetize-m1-w1-w2.md`（M1 Week 1-2 全8タスク）
> 上位スペック: `docs/superpowers/specs/2026-05-18-skin-monetize-roadmap-design.md`（半年ロードマップ・月3〜5万円目標）

### 先週完了
- [x] note: 肌荒れ改善noteの販売準備（価格設定・公開日決め）
- [x] 肌荒れ改善Threads: 画像投稿対応（Pillowで画像生成→GitHub→Threads）
- [x] @RoninWords: Day31以降のThreads投稿文を作る（Day31〜60完成・threads_posts.jsonに追加済み）

---

## 📚 プロジェクト別TODO

### 0. 家計管理アプリ（finance_web）マネタイズ

**現状**: https://financeweb-nine.vercel.app で本番公開済み（2026/05/05）

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
- [ ] SNS（Threads / X）でアプリを紹介する投稿を出す

#### 機能追加（後回しOK）
- [x] OGP設定（SNSシェア時にカード表示されるようにする・2026/05/19確認時すでに実装＆ogp.pngデプロイ済み）
- [x] **v1.5.0 リリース**（2026/05/24 デプロイ済み）
  - [x] 📊 カテゴリ別支出割合の円グラフ（概要タブ・月別ドーナツグラフ）
  - [x] 📥 CSVエクスポート（設定タブ・全期間の支出+収入をCSVダウンロード）
- [x] **v1.4.0 リリース**（2026/05/24 デプロイ済み）
  - [x] ⚡定期支出：繰り返し変動費（Netflix・ジム代等）の自動追加機能（支出タブ）
  - [x] 📈純資産推移グラフ：過去12ヶ月の累積手残りチャート（概要タブ）
  - [x] 🗑️一括削除：指定月末以前の支出・収入・振替を一括削除（設定タブ）
  - [x] バックアップに `kk_rec_exp`（繰り返し支出）を追加
- [ ] 複数端末同期（有料機能の候補・設計案: finance_web/docs/finance_web_sync_design.md / 案C Vercel KV推奨・着手目安2026/08〜10）

---

### 1. @RoninWords（書道カード・Threads/X/LinkedIn）

**現状**: 
- Threads自動投稿稼働中（1日4回・7:17/12:17/18:17/22:17 JST）
- LinkedIn自動投稿実装完了（GitHubにデプロイ済み）、アカウント作成待ち

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
  - [ ] LinkedInアカウント作成（準備中）
  - [ ] OAuth認証実施（アカウント作成後）
  - [ ] GitHub Secret設定（認証後・自動投稿開始）
- [ ] X（Twitter）の運用開始（Day01スケジュールから）
- [ ] TikTok/Reels用の動画台本（30本作成済み）から1本作って投稿

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
- [ ] フォロワー数・反応をスプレッドシートで記録する仕組み
- [ ] 反応の良かった投稿パターンを分析する
- [x] **ronin_analyzer「現在: 0日」問題**（2026/06/07 修正：`should_analyze` が `posts_history[0]` を最古と仮定していたのを、全件 `min` で最古を求める `earliest_post_datetime` に変更）

#### reach加速（2026/06/07・feature/ronin-reach-boost → main マージ済み）
- [x] コメント誘発engagement投稿32本（6型×5＋種2・`ronin/ronin_engagement_posts.json`）。4投稿に1回自動差し込み
- [x] 投稿直後の1コメ目自動シード（`reply_to_id`・早期リプライで非フォロワー拡散）。ライブ実証済み（本投稿18108549884317438＋1コメ目17967528567091426）
- [x] ハッシュタグ動的ローテーション（固定5個→4セット・越境タグ #StoicMindset 等で新規流入・`ronin/ronin_hashtags.py`）
- [x] Gumroad/SubstackのCTAを本文から1コメ目へ移動（本文クリーン化で配信抑制回避）
- [x] 死んだ最適化パス（should_use_optimization/post_optimized）を撤去し本線を単純化
- [x] `--dry-run` 追加・テスト24件 全通過・設計書/計画書を `docs/superpowers/` に追加
- [ ] 1〜2週後：engagement投稿のコメント数・1コメ目以降の自然リプライ・非フォロワー流入をダッシュボードで確認

#### マネタイズ（海外版note販売）
- [ ] 英語翻訳スクリプト作成（自動翻訳 or 手動テンプレート）
- [ ] Substack / Medium / LinkedIn Newsletter 比較選定
- [ ] 有料note記事作成（Day1-20の最高反応パターン）
- [ ] 英語版を LinkedIn で先行配信（Day1-60ローテーション・英語版）
- [ ] 海外版noteで販売化開始

---

### 2. 肌荒れ改善note（Threads・note販売・Instagram）

**現状**: noteコンテンツ作成済み、Threads自動投稿1日4回稼働中（JST 7:30/12:30/18:30/21:30）。A/B構造化リライト Batch 1（テーマ1-20）リリース完了・観測期間中

#### 自動化（完了）
- [x] Meta for Developers認証・APIキー取得
- [x] Threads自動投稿をGitHub Actionsに乗せる（1日16回稼働中）
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

#### X（Twitter）自動投稿
- [ ] X API Pay-Per-Useにクレジットをチャージする（developer.twitter.com → Usage & Billing → Add Credits、$5〜$10）
  - 月480投稿 ≈ 月$5（約750円）で稼働できる
  - スクリプト（skin_x_action.py）・ワークフロー（skin_x_post.yml）は作成済み
  - チャージ後、GitHubにX_API_KEY等のSecretsを追加してpushするだけ

#### Threadsリライト（A/B構造化・216セット 6バッチ計画）
- [x] Batch 1（テーマ1-20、40セット）リリース完了（2026/05/18・コミット 38cf4da）
  - [x] A/B選択ロジック実装（skin_threads_action.py・15テストPASS）
  - [x] skin_ab_report.py（A/B勝者判定スクリプト）作成
  - [x] テーマ1-20 のA/B 全40セット制作（薬機法準拠：辞書形＋活用形NG 0件）
  - [x] バッチ進行管理ファイル（skin_threads_batch_progress.json）作成
- [ ] 2026/05/31: Batch 1 中間レポート確認（`python3 skin/skin_ab_report.py --batch 1`）
- [ ] 2026/06/06: Batch 1 最終レポート → status を `validated` に更新
- [ ] 2026/06/07〜: Batch 2（テーマ21-40）制作開始・新計画書作成
- [ ] Batch 3〜6（テーマ41-108）順次制作・リリース

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
- [ ] **Batch 2 制作（2026/06/07予定）**：v1 16テーマを v2（8スライド）化 or 新規追加
- [ ] **投稿内容ブラッシュアップ（プロ目線、新セッションでbrainstormingから）**
  - アカウント: https://www.instagram.com/skin_reset_jp/
  - 既存ファイル: skin/carousel_content.json（themes配列）、skin/skin_instagram_image_gen_v3.py（v1画像）、skin/skin_instagram_image_gen_v4.py（v2画像）、skin/skin_instagram_auto_post.py（投稿）
  - 流れ: brainstorming → 設計 → 実装計画 → コンテンツ制作（skin Threads Batch 1 と同じプロセス）

#### 改善
- [ ] 画像投稿対応（Pillowで画像生成→GitHubにホスト→Threads画像投稿）
- [ ] 投稿の反応をメモする（どのパターンが伸びたか）

#### note販売
- [x] noteの価格を決める
- [x] note公開日を決める
- [ ] `skin_x_launch_playbook.md` のローンチ投稿を実行
- [x] **note 完全自動投稿システム実装完了**（2026-05-23・月水金9:00 JST）
  - Playwrightでnote.comにヘッドレス自動投稿（`skin/post_to_note.py`）
  - 投稿成功/失敗をメール通知（`skin/send_note_email.py`）
  - 失敗時はスクリーンショットをアーティファクト保存
  - 進捗履歴 `note_queue_progress.json` の `history[]` に追加
  - 旧 `generate_note_page.py` / `note_article.html` は削除
- [x] **note 自動投稿の手動セットアップ（4ステップ・完了）**
  - [x] ① クッキー取得：note.com にログイン状態でブラウザDevTools → Application → Cookies → `_note_session_v5` の Value をコピー（手順: `docs/note_cookie_setup.md`）
  - [x] ② GitHub Secrets 登録：`https://github.com/kmkn0523-cell/kenta-learning/settings/secrets/actions` で Name=`NOTE_SESSION_V5` に値を貼り付けて Add secret
  - [x] ③ 手動テスト実行：`gh workflow run skin_note_release.yml` を叩いて、成功メール `【skin note 自動投稿成功】...` が届くか確認（失敗時はアーティファクト `note-screenshots` でセレクタ調整）
  - [x] ④ cron-job.org スケジュール設定：③ 成功確認後に「月水金 9:00 JST」に変更（テスト前にcron組むと失敗投稿が連発するので最後）

#### アフィリエイト
- [ ] Amazonアソシエイトに登録する（affiliate.amazon.co.jp）
- [ ] 楽天アフィリエイトにも登録する
- [ ] 亜鉛サプリ・緑茶・発酵食品のアフィリリンクを取得する
- [ ] Threads投稿にアフィリリンクを貼る運用を開始する
- [ ] フォロワー500人超えたらサプリ系ASP（Mosh・afb）に登録する

#### コンテンツ
- [ ] 日常投稿7種ローテーション以外の投稿パターンを増やす
- [ ] 売上・反応の記録方法を決める
- [x] 睡眠テーマの無料note（note_article_sleep.md）をnoteに投稿する

---

### 3. Python学習

**現状**: 7つのプログラム作成済み（おみくじ〜ronin自動投稿）

- [ ] `learning_notes.md` の「今後の学習予定」を進める
  - [ ] エラー対応の型を身につける
  - [x] 定期実行の仕組み（cron / クラウド）← GitHub Actionsで達成
- [ ] 何か1つ新しい小さなプログラムを作る（楽しむ用）

---

### 4. インフラ・自動化

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

## 💡 アイデア・後回し

- [x] Instagram連携（@RoninWords Instagram自動投稿 毎日21:17 JST・GitHub Actions稼働）
- [ ] 別ジャンルのアカウント開設（テンプレが完成してから）
- [x] ホーム直下のファイル数が多すぎる問題 → フォルダ分け（2026/05/12完了）

---

## ✅ 完了済み（やる気アップ用に残す）

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

---

## 📝 使い方ルール

- やることは **今週3つだけ** に絞る（増やしすぎない）
- 終わったら `[ ]` を `[x]` にする
- 1週間に1回、見直して並び替える
- 「アイデア・後回し」に書いておけば、忘れても