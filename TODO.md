# TODO リスト

最終更新: 2026/05/18（skin Threads Batch 1 リリース・A/B構造化開始）

---

## 🔥 今週やること（最優先・3つだけに絞る）

- [x] skin プロフィール v2 確定（`skin/profile/profile_v2.md` 確認・修正 → Threads/Instagram にコピペ反映）
- [x] skin ヘッダー画像作成（Canva で「スキンケアでは、治らない。」→ `skin/profile/header_image_v2.png` 保存・SNS反映）
- [x] skin 観測対象10アカウントのリスト化（Threads検索 → `skin/skin_account_targets.json` に10件記入）

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
- [ ] 複数端末同期（有料機能の候補）

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
- [ ] **投稿内容ブラッシュアップ（プロ目線、新セッションでbrainstormingから）**
  - アカウント: https://www.instagram.com/skin_reset_jp/
  - 既存ファイル: skin/carousel_content.json（themes配列）、skin/generate_skin_cards.py（画像生成）、skin/skin_instagram_auto_post.py（投稿）、skin/skin_instagram_progress.json（next_index: 5）
  - 進行状況: 20テーマ稼働中、現在 next_index=5
  - 流れ: brainstorming → 設計 → 実装計画 → コンテンツ制作（skin Threads Batch 1 と同じプロセス）

#### 改善
- [ ] 画像投稿対応（Pillowで画像生成→GitHubにホスト→Threads画像投稿）
- [ ] 投稿の反応をメモする（どのパターンが伸びたか）

#### note販売
- [x] noteの価格を決める
- [x] note公開日を決める
- [ ] `skin_x_launch_playbook.md` のローンチ投稿を実行

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
- [ ] 投稿ログを1箇所にまとめて見られるようにする

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