# ローニン Instagram Reels 自動生成・自動投稿エンジン 設計書

- 作成日: 2026-06-20
- 対象: @RoninWords Instagram アカウント
- 目的: 非フォロワーに届く唯一の発見面（Reels）を完全自動で量産・投稿し、reach を伸ばす

---

## 1. 背景

IG はフィード/画像が非フォロワーにほぼ届かず、発見エンジンは Reels のみ。ローニンは既に
「格言カード画像（1080×1080）の自動生成」＋「Instagram 画像の API 自動投稿」＋「GitHub Actions」が
稼働中。この資産を再利用し、縦型ショート動画を自動生成→自動投稿する。

skin アカウントには既に実証済みの Reels エンジン（`skin/skin_reels_engine.py`・単一スクリプトで
`generate`/`publish` の2サブコマンド）が稼働中。**本設計はその実証済みアーキテクチャを踏襲し、
ローニン特有の「1格言を段階リビールする動画」部分だけを作り替える。**

> 注: ブレスト時は4ファイル分割案で合意したが、skin の単一エンジン方式が実証済みで保守も容易なため、
> 単一エンジン方式（`ronin_reel_engine.py` に generate/publish を集約）へ寄せる。責務は関数単位で分離する。

## 2. 方針の決定事項（ユーザー合意済み）

- 動画生成: **既存カードのレンダリングを流用し ffmpeg で合成（無料・GitHub Actions）**。AI動画（Higgsfield）は使わない
- BGM: **ロイヤリティフリー/CC0 音源を mp4 に焼き込む**（API投稿ではトレンド音源を付けられないため）
- 構成: **演出リビール型**（日本語格言→ローマ字→英語の意味を段階的にフェードで見せる）
- 運用: **1日1回・既存の画像投稿とは別枠で追加**（画像投稿はそのまま残す）

## 3. 技術的前提（確認済み）

- Reels 投稿は既存画像と同じ Content Publishing API。`media_type=REELS` ＋ 公開動画URL の3ステップ
  （コンテナ作成→`status_code` が FINISHED までポーリング→公開）。
- ローニンは既に画像を API 投稿できている＝**ビジネスアカウント・公開権限は取得済み。追加申請不要**。
- Reels タブ掲載条件: **9:16（1080×1920）・5〜90秒・H.264**。
- **トレンド音源は API 投稿では付けられない** → mp4 に焼き込んだ著作権フリー音源のみ。
- 既存資産:
  - 格言データ: `ronin/generate_ronin_cards.py` 内の `proverbs`（day / jp / roma / en）
  - 既存カードのフォント・配色（YujiSyuku / CormorantGaramond / 和紙色 / 朱・墨）
  - 投稿基盤: `ronin/ronin_instagram_auto_post.py` の `publish_media()`、`create_media_container()`
  - ハッシュタグ: `ronin/ronin_hashtags.py` の `pick_hashtag_set(count)`（純粋関数）
- env 変数: `INSTAGRAM_ACCESS_TOKEN` / `INSTAGRAM_USER_ID`（既存画像投稿と共通）。
- **`ronin_instagram_auto_post.py` には `wait_for_container_ready` が無い** → エンジン内に自前実装し自己完結させる。
- 出典: https://developers.facebook.com/docs/instagram-platform/content-publishing/

## 4. システム設計

### 4.1 ファイル構成

| パス | 役割 |
|---|---|
| `ronin/ronin_reel_engine.py` | 本体。`generate` / `publish` の2サブコマンド。純粋関数（フレーム計画・ffmpeg引数・URL組み立て・キャプション）と IO を分離 |
| `ronin/ronin_reel_engine_config.json` | 秒数・解像度・fps・出力ファイル名・raw URLベース等の設定 |
| `ronin/ronin_reel_frames.py` | 1格言から縦型(1080×1920)の段階リビール用フレーム画像を Pillow で生成（カード描画ロジックを流用） |
| `ronin/ronin_reel_assets/bgm.mp3` | ロイヤリティフリー/CC0 のBGM（**ユーザーが手動で配置**） |
| `ronin/ronin_instagram_reels/latest_reel.mp4` | 生成された最新動画（固定パス上書き＝リポジトリ肥大防止） |
| `ronin/ronin_reel_pending.json` | generate→publish の受け渡し（格言index・キャプション・ファイル名） |
| `ronin/ronin_reel_progress.json` | リール用の進捗（次に作る格言index・投稿履歴）。**画像投稿の進捗と完全分離** |
| `.github/workflows/ronin_instagram_reels.yml` | 1日1回 generate→push→publish を回すワークフロー |

### 4.2 動画の中身（演出リビール型・約10秒）

1格言につき縦型フレームを4枚生成し、各フレームを ffmpeg で連結。各フレームは**フェードイン**して
「続きが見たくなる」リビール感を出す。

- フレーム1（約2秒）: 和紙背景＋右上 RW シール（テキストなし）
- フレーム2（約3秒）: ＋ 日本語格言（筆文字・中央大）
- フレーム3（約2秒）: ＋ ローマ字読み
- フレーム4（約3秒）: ＋ 英語の意味＋CTA（`Follow for one Japanese wisdom, every day.`）

各フレームは前フレームに要素を足した「累積表示」。フォント・配色・シールは
`generate_ronin_cards.py` と統一し、ブランドの世界観を保つ。

### 4.3 generate → publish の2フェーズ（skin と同じ流れ）

動画の公開URLが必要なため、生成 → git push（URL公開）→ 公開、の順で回す。

**`python ronin_reel_engine.py generate`**
1. キルスイッチ `RONIN_REEL_ENGINE_ENABLED` が `true` 以外なら即終了
2. BGM `ronin_reel_assets/bgm.mp3` が無ければ著作権事故防止のため明確なエラーで停止
3. `ronin_reel_progress.json` から次の格言 index を決める（末尾の次は先頭へ循環）
4. その格言の4フレームを `ronin_reel_frames.py` で生成（一時PNG）
5. ffmpeg で 1080×1920・H.264・各フレームfade付き連結＋BGM焼き込み → `latest_reel.mp4`
6. キャプション（格言の en ＋ `pick_hashtag_set()`）と公開情報を `ronin_reel_pending.json` に保存

**（ワークフローが `latest_reel.mp4` と `pending.json` を commit & push して公開URLを生やす）**

**`python ronin_reel_engine.py publish`**
1. キルスイッチ確認 → `ronin_reel_pending.json` を読む
2. 動画の raw URL が配信され始める（HTTP 200）まで待つ（最大3分・15秒間隔）
3. `media_type=REELS`＋`video_url`＋`caption` でコンテナ作成
4. `wait_for_container_ready()`（自前実装）で `status_code=FINISHED` までポーリング
5. `ronin_instagram_auto_post.publish_media()` を遅延import して公開
6. `ronin_reel_progress.json` を進める・履歴に当日を追記

### 4.4 キルスイッチ

- 環境変数 `RONIN_REEL_ENGINE_ENABLED` が `true` 以外なら generate/publish とも即終了。
  GitHub の Variables で管理し、いつでも停止できる。

### 4.5 スケジュール

- 新規ワークフロー `ronin_instagram_reels.yml`。Reels は重いので **1日1回**（JST 19:30＝UTC 10:30 想定。
  既存 ronin 画像/Threads の時間帯と重ならないよう配置）。
- ステップ順: checkout → Python → ffmpeg導入 → `pip install requests python-dotenv pillow` →
  `generate` → mp4 を commit&push → `publish` → 進捗 commit&push。
- 既存の ronin ワークフロー（画像・Threads・Substack）には一切触れない。

### 4.6 テスト対象（純粋関数・`ronin/tests/` に追加）

- `next_proverb_index`: 進捗からの次index計算（循環）
- `build_ffmpeg_command`: フレーム枚数・秒数・解像度から ffmpeg 引数リストを返す（実行はしない）
- `build_caption`: en ＋ハッシュタグの組み立て
- `build_raw_video_url`: raw URL 組み立て
- フレーム計画（どの格言要素をどのフレームに載せるかのプラン関数）

ネットワーク/IO（ffmpeg実行・Pillow描画・URLポーリング・API投稿）はユニットテスト対象外。

## 5. 事前作業（ユーザーが1回だけ・コード不可）

- **著作権フリー/CC0 のBGM**を `ronin/ronin_reel_assets/bgm.mp3` として配置。
  Claude は音源を取得できないため必須の手動準備。無い場合 `generate` は明確なエラーで停止する。
  落ち着いた和風インスト（CC0）を Claude が候補提示 → ユーザーがDLして配置。
- GitHub の Variables に `RONIN_REEL_ENGINE_ENABLED=true` を設定（動作確認後に有効化）。
- secrets `INSTAGRAM_ACCESS_TOKEN` / `INSTAGRAM_USER_ID` は既存画像投稿用が流用可（確認のみ）。

## 6. リスクと対策

- **音源の著作権**: 必ず CC0/商用可のみ。誤るとアカウントリスク。無ければ generate を停止。
- **動画URLの配信遅延**: push 直後に raw が 200 を返すまでポーリングして待つ。
- **ffmpeg 未導入**: ローカル WSL は未導入。常駐は GitHub Actions で `apt-get install -y ffmpeg`。
  ローカル検証したい場合のみ別途導入（要承認）。
- **リポジトリ肥大**: mp4 は固定パス上書きで最新1本のみ保持。
- **Reels 非該当**: 9:16・5〜90秒・H.264 を厳守。外れると通常動画扱いで発見面に乗らない。
- **二重投稿**: 進捗を画像投稿と完全分離。媒体（画像/リール）が違えば同じ格言が両方に出てもよい想定。
- **`generate_ronin_cards.py` の import 副作用**: 同モジュールがトップレベルで描画を実行する場合は、
  `proverbs` データと描画関数を安全に取り出せるようリファクタ（`if __name__ == "__main__"` ガード化）。
  既存の画像生成挙動は変えない。

## 7. スコープ外（YAGNI）

- AI動画生成（Higgsfield）
- 複数格言のスライドショー型リール
- コメント→自動DM（Meta審査が必要なため別件）
- Instagram 公式音楽ライブラリのトレンド音源（API投稿では不可）
