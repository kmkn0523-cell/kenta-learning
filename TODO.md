# TODO リスト

最終更新: 2026/05/07（LinkedInオートメーション実装完了・アカウント作成待ち）

---

## 🔥 今週やること（最優先・3つだけに絞る）

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
- [ ] 審査通過を確認する（審査中）
- [ ] 取得できたブランドのアフィリエイトリンクをアプリに組み込む
- [ ] SNS（Threads / X）でアプリを紹介する投稿を出す

#### 機能追加（後回しOK）
- [ ] OGP設定（SNSシェア時にカード表示されるようにする）
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

**現状**: noteコンテンツ作成済み、Threads自動投稿1日16回稼働中（毎時30分 JST）。フォロワー成長機構（Day1-20学習、Day21以降最適化）完全実装済み

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

#### Instagram自動投稿（仕組みは完成・画像待ち）
- [ ] Instagram投稿用画像を作り込む（現在の自動生成画像はNG・参考画像を集めてデザイン見直し）
- [ ] 画像完成後にGitHub Actionsを有効化する（現在 disabled_manually で停止中）

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
- [ ] 投稿ログを1箇所にまとめて見られるようにする

---

## 💡 アイデア・後回し

- [x] Instagram連携（@RoninWords Instagram自動投稿 毎日21:17 JST・GitHub Actions稼働）
- [ ] 別ジャンルのアカウント開設（テンプレが完成してから）
- [ ] ホーム直下のファイル数が多すぎる問題 → フォルダ分け（落ち着いたら）

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
- 「アイデア・後回し」に書いておけば、忘れてもOK
