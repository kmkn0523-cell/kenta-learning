# TODO リスト

最終更新: 2026/06/25（完了済みを `TODO_archive.md` に退避してスリム化・古い現状記述を更新）

> 完了済みタスクは `TODO_archive.md` に移しました。経緯を見たいときはそちら。

---

## 🔥 今週やること（最優先・3つだけに絞る）

- [ ] **skinリプ運用**: 入替推奨3件（@lii_gohan/@watashino_kohkatsu/@skincarebunnyy）をアプリで最終確認し、外すなら新ターゲット補充（腸活×肌・大人ニキビ系で500〜3万規模）
- [ ] **skinアフィリエイト導線**（コード準備済 2026/06/13・あとはリンク差すだけ）
  - [ ] 楽天アフィリエイト登録（楽天会員なら審査ほぼなしで即発行・Threads認定SNS済）。または afb（Threads原則OK・案件ごと要項確認）
        ※⚠️ A8.netは使わない（公式がThreads投稿への広告掲載を非推奨＝iOSアプリでリンクが正常遷移しない不具合のため。A8はプロフィールリンク欄のみ可）。1コメ目CTAには楽天/afbを使う（2026/06/15リサーチ）
  - [ ] スキンケア商品のアフィリリンクを取得し `skin/skin_affiliate_products.json` の `products` に追記
        （`{"name": 商品名, "url": リンク}` 形式。入れた瞬間からThreadsの1コメ目CTAに「リポスト⇄アフィリ」交互で出る。空の間は一切出ない）
  - [ ] Instagram用にbioリンク（linktr.ee無料 or 楽天room）を用意（IGは本文リンク不可のためプロフィール誘導型）

---

## 📚 プロジェクト別TODO

### 0. 家計管理アプリ（finance_web）

**現状**: https://financeweb-nine.vercel.app で本番公開済み。v1.6.0まで稼働中

- [ ] SNS（Threads / X）でアプリを紹介する投稿を出す（下書き作成済み: `finance_web/docs/sns_launch_posts.md`・スクショ3枚撮って投稿するだけ）
- [ ] 複数端末同期（有料機能の候補・設計案: `finance_web/docs/finance_web_sync_design.md` / 案C Vercel KV推奨・着手目安2026/08〜10）

---

### 1. @RoninWords（書道カード・Threads/X/LinkedIn）

**現状**: Threads自動投稿稼働中（1日約12回・約2時間おき＝cron 4回/日＋外部スケジューラの毎時dispatchを90分間隔ガードで間引いた実態）。LinkedIn自動投稿は実装済み・アカウント作成待ち

#### 運用
- [ ] LinkedInアカウント作成（準備中）
- [ ] OAuth認証実施（アカウント作成後）
- [ ] GitHub Secret設定（認証後・自動投稿開始）
- [ ] X（Twitter）の運用開始（Day01スケジュールから）
- [ ] TikTok/Reels用の動画台本（30本作成済み）から1本作って投稿

#### 改善
- [ ] フォロワー数・反応をスプレッドシートで記録する仕組み
- [ ] 反応の良かった投稿パターンを分析する
- [ ] 1〜2週後：engagement投稿のコメント数・1コメ目以降の自然リプライ・非フォロワー流入をダッシュボードで確認
- [ ] **頻度実験の効果測定（2026/07/16頃）**: 12回/日→約6回/日（2026/07/02にskip_minutes 90→240）で1投稿あたりのviews/likesが回復したか before/after 比較。回復なければ90分に戻すか、さらに360分（4回/日）を試す

#### マネタイズ（海外版note販売）
- [ ] 英語翻訳スクリプト作成（自動翻訳 or 手動テンプレート）
- [ ] Substack / Medium / LinkedIn Newsletter 比較選定
- [ ] 有料note記事作成（Day1-20の最高反応パターン）
- [ ] 英語版を LinkedIn で先行配信（Day1-60ローテーション・英語版）
- [ ] 海外版noteで販売化開始

---

### 2. 肌荒れ改善note（Threads・note販売・Instagram）

**現状**: Threads自動投稿1日4回稼働中（JST 7:30/12:30/18:30/21:30）。A/B構造化リライト Batch 1（テーマ1-20）リリース済・観測完了（A型優勢）

#### X（Twitter）自動投稿
- [ ] X API Pay-Per-Useにクレジットをチャージする（developer.twitter.com → Usage & Billing → Add Credits、$5〜$10）
  - 月480投稿 ≈ 月$5（約750円）で稼働できる
  - スクリプト（skin_x_action.py）・ワークフロー（skin_x_post.yml）は作成済み
  - チャージ後、GitHubにX_API_KEY等のSecretsを追加してpushするだけ

#### 自動リプライ・エンジン稼働（コード完成・申請待ちで停止中）
> 手順書: `docs/reply_engine_manual_steps.md` / 申請文: `docs/threads_app_review_keyword_search.md`
> 現状: `SKIN_REPLY_ENGINE_ENABLED` 未設定で停止中。`keyword_search`（他人投稿の検索）は Meta審査の承認が必須なので、変数をtrueにする前に申請が要る
- [ ] **Phase A: 画面録画**（トークン不要・今すぐ可）`cd skin && python3 skin_reply_review_ui.py --demo` → `http://127.0.0.1:8765` で「検索→一覧→選択→送信」を録画
- [ ] **Phase B: Meta App Review 申請**（★審査に数日〜数週）developers.facebook.com → skinアプリ → `threads_keyword_search` の Advanced Access 申請（説明文＋プライバシーポリシーURL＋録画）
- [ ] **Phase C: 承認後**トークン再発行（keyword_search込み）→ `.env`＋GitHub Secret `THREADS_ACCESS_TOKEN` 更新
- [ ] **Phase D: 稼働**`gh variable set SKIN_REPLY_ENGINE_ENABLED --body true` → 手動テスト（`gh workflow run skin_threads_reply_engine.yml`）で誤爆確認 → 本稼働（1日6回）
- [ ] ronin も別Metaアプリで同じ申請が別途必要（`RONIN_REPLY_ENGINE_ENABLED`）

#### Threadsリライト（A/B構造化・216セット 6バッチ計画）
- [ ] Batch 2（テーマ21-40）制作開始・新計画書作成
- [ ] Batch 3〜6（テーマ41-108）順次制作・リリース

#### Instagram自動投稿
- [ ] **Batch 2 制作（未着手）**：v1 16テーマを v2（8スライド）化 or 新規追加
- [ ] **投稿内容ブラッシュアップ（プロ目線、新セッションでbrainstormingから）**
  - アカウント: https://www.instagram.com/skin_reset_jp/
  - 既存ファイル: skin/carousel_content.json（themes配列）、skin/skin_instagram_image_gen_v3.py（v1画像）、skin/skin_instagram_image_gen_v4.py（v2画像）、skin/skin_instagram_auto_post.py（投稿）
  - 流れ: brainstorming → 設計 → 実装計画 → コンテンツ制作（skin Threads Batch 1 と同じプロセス）

#### 改善
- [ ] 画像投稿対応（Pillowで画像生成→GitHubにホスト→Threads画像投稿）
- [ ] 投稿の反応をメモする（どのパターンが伸びたか）

#### note販売
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

---

### 3. Python学習

**現状**: 7つのプログラム作成済み（おみくじ〜ronin自動投稿）

- [ ] `learning_notes.md` の「今後の学習予定」を進める
  - [ ] エラー対応の型を身につける
- [ ] 何か1つ新しい小さなプログラムを作る（楽しむ用）

---

## 💡 アイデア・後回し

- [ ] 別ジャンルのアカウント開設（テンプレが完成してから）

---

## 📝 使い方ルール

- やることは **今週3つだけ** に絞る（増やしすぎない）
- 終わったら `[ ]` を `[x]` にする → 完了は `TODO_archive.md` へ移す
- 1週間に1回、見直して並び替える
- 「アイデア・後回し」に書いておけば、忘れても大丈夫
