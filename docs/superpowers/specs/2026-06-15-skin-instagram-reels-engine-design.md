# skin Instagram Reels 量産エンジン 設計書

- 作成日: 2026-06-15
- 対象: skin Instagram アカウント
- 目的: IGで非フォロワーに届く唯一の発見面（Reels）を完全自動で量産・投稿する

---

## 1. 背景

IGはフィード/カルーセルが非フォロワーにほぼ届かず、発見エンジンは Reels のみ。skin はフォロワー1人で停滞中で、Reels 未着手が最大の機会損失。既存のカルーセル画像（160枚）と投稿APIインフラを再利用し、縦型ショート動画を自動生成→自動投稿する。

## 2. 方針の決定事項（ユーザー合意済み）

- 動画生成: **静止画スライド + 音源（ffmpegで合成・無料）**。AI動画（Higgsfield）は使わない
- ③コメント→自動DMは別件（Meta審査が必要なため後回し）

## 3. 技術的前提（確認済み）

- Reels投稿は既存カルーセルと同じ Content Publishing API。`media_type=REELS` ＋ 公開動画URL の3ステップ（コンテナ作成→`status_code`がFINISHEDまでポーリング→公開）。
- skin は既にカルーセルをAPI投稿できている＝**`instagram_business_content_publish`権限・ビジネスアカウント取得済み。追加の権限申請は不要**。
- Reelsタブ掲載条件: **9:16・5〜90秒・H.264**。
- **トレンド音源はAPI投稿では付けられない** → mp4に焼き込んだ著作権フリー音源のみ。
- 既存資産: `skin/skin_instagram_carousels/themeNN_slideM.png`（160枚）/ `build_carousel_image_urls()` / `wait_for_container_ready()` / `publish_media()` / `skin_hashtags`（純粋）/ `carousel_content.json`。
- 出典: https://developers.facebook.com/docs/instagram-platform/content-publishing/

## 4. システム設計

### 4.1 動画生成 → 公開の2フェーズ（GitHub Actions内で分割）

動画の公開URLが必要なため、生成 → git push（URLを公開）→ 公開、の順で回す。スクリプトは2サブコマンドを持つ:

- `python skin_reels_engine.py generate`
  1. 次に使うテーマを選ぶ（`skin_reels_progress.json` でローテーション）
  2. そのテーマのスライド画像（ローカル `skin/skin_instagram_carousels/`）を集める
  3. ffmpegで縦型(1080x1920) mp4 を合成。各スライド数秒・著作権フリー音源を埋め込み・H.264・合計5〜90秒に収める
  4. 出力を固定パス `skin/skin_instagram_reels/latest_reel.mp4` に上書き（リポジトリ肥大を抑える）
  5. キャプション（`carousel_content.json` のテーマ説明＋`skin_hashtags`）と公開に必要な情報を `skin_reels_pending.json` に保存
- （ワークフローが `latest_reel.mp4` を commit & push して公開URLを生やす）
- `python skin_reels_engine.py publish`
  1. `skin_reels_pending.json` を読む
  2. 動画の raw URL が配信され始めるまで HTTP GET で 200 を待つ（最大数分）
  3. `media_type=REELS`＋`video_url`＋`caption` でコンテナ作成 → `wait_for_container_ready()` で FINISHED 待ち → `publish_media()` で公開
  4. `skin_reels_progress.json` を進める・`skin_daily_log.md` に記録

### 4.2 キルスイッチ

- 環境変数 `SKIN_REELS_ENGINE_ENABLED` が `true` 以外なら generate/publish とも即終了。

### 4.3 スケジュール

- 新規 GitHub Actions ワークフロー。Reelsは重いので **1日1回**（例: JST 19:00）。
- ステップ順: ffmpeg導入 → `generate` → mp4をcommit&push → `publish`。

### 4.4 テスト対象（純粋関数）

- テーマローテーション（次インデックス計算）
- スライドのローカルパス組み立て
- ffmpegコマンド生成（引数リストを返すだけ・実行はしない）
- スライド枚数→合計秒数の計算と上限丸め（5〜90秒に収める）
- raw URL 組み立て
- キャプション組み立て（`skin_hashtags`再利用）

ネットワーク/IO（ffmpeg実行・URLポーリング・API投稿）はユニットテスト対象外。

## 5. 事前作業（ユーザーが1回だけ・コード不可）

- **著作権フリー音源**を `skin/skin_reels_assets/bgm.mp3` として配置（CC0/ロイヤリティフリー）。Claudeは音源を取得できないため必須の手動準備。無い場合 `generate` は明確なエラーで停止する。

## 6. リスクと対策

- **音源の著作権**: 必ずCC0/商用可の音源のみ。これを誤ると著作権侵害でアカウントリスク。
- **動画URLの配信遅延**: push直後にrawが200を返すまでポーリングして待つ。
- **ffmpeg未導入**: ローカルは未導入。常駐はGitHub Actionsで `apt-get install -y ffmpeg`。ローカル検証したい場合のみ別途導入（要承認）。
- **リポジトリ肥大**: mp4は固定パス上書きで最新1本のみ保持。
- **Reels非該当**: 9:16・5〜90秒・H.264を厳守。外れると通常動画扱いで発見面に乗らない。

## 7. スコープ外（YAGNI）

- AI動画生成（Higgsfield）。
- トレンド音源の自動付与（API不可）。
- ③コメント→自動DM（別設計・Meta審査後）。
- 複数音源ローテーション（v1は単一bgm.mp3。必要なら後で拡張）。

## 8. 完了の定義

- `SKIN_REELS_ENGINE_ENABLED=true` のとき、cronで generate→push→publish が全自動で動き、9:16・5〜90秒のReelsが1日1本投稿される。
- `false` で完全停止。音源が無ければ明確に停止する。
