# ronin Threads「投稿の外側」自動強化 設計書（2026-07-01）

## 背景・課題

@RoninWordsのThreads自動投稿は稼働しているが、reachが壊滅的（直近投稿で views 4〜20・いいねほぼ0・コメントは自分の1コメ目シードのみ）。既存の自動化資産（ET基準の配信時刻・コメント誘発engagement投稿32本ローテ・1コメ目自動シード・ハッシュタグ4セット動的ローテ・14投稿サイクルのCTA配置・Instagram Reels自動投稿）はskinより先行しているが、「投稿テーマとの連動」が弱い。またreply_engine（自動リプ本体）はMeta App Reviewのkeyword_search権限が取得できず（RoninWordsアプリにThreadsユースケースが無いため）本稼働できない。

skinで実施済みの「投稿の外側」施策（CTAのnoteテーマ連動・1コメ目シードのテーマ連動・週次自動レポート）と同じ発想をroninに移植する。手動コピペが必須な`ronin_reply_hunter.py`（半自動リプ下書き）は今回のスコープ外（完全自動施策のみ）。

## スコープ

1. テーマ分類ロジックの共通化
2. 1コメ目シードのテーマ連動
3. CTA（Substack）のテーマ連動（前提: 公開URLの自動記録）
4. reply_engineの設定強化（本稼働はしない）
5. 週次自動レポート（Gmail通知）

## 1. テーマ分類の共通化（新規: `ronin/ronin_theme_classifier.py`）

`ronin_reply_hunter.py`にある`KEYWORD_MAP`（6カテゴリ: 1=規律/習慣、2=逆境/打たれ強さ、3=集中/誘惑、4=ストイック/心の在り方、5=熟達/鍛錬、6=目的/意味）と、`ronin_reply_engine.py`にある`classify_category`関数を、新モジュール`ronin_theme_classifier.py`に切り出す。

- `KEYWORD_MAP`: 6カテゴリの英語キーワード辞書（既存のものを移動）
- `classify_category(text)`: 本文からキーワード一致数が最多のカテゴリキー（"1"〜"6"）を返す。どれにも当たらなければ`None`

`ronin_reply_hunter.py`・`ronin_reply_engine.py`は、この新モジュールから`KEYWORD_MAP`/`classify_category`をimportするよう変更する（ロジック自体は変えない・動作互換）。`ronin_threads_action.py`・`ronin_comment_seeder.py`は新たにこのモジュールをimportして使う。

## 2. 1コメ目シードのテーマ連動（`ronin/ronin_comment_seeder.py`）

6カテゴリ別の問いかけ`THEME_SEED_QUESTIONS`（各カテゴリ5パターン、英語）を追加する。既存の`GENERIC_SEED_QUESTIONS`はカテゴリ不明時のフォールバックとして残す。

- `pick_seed_question(count, theme_key)`: `theme_key`が`THEME_SEED_QUESTIONS`にあればそのカテゴリ内でcountローテ、無ければ`pick_generic_seed(count)`にフォールバック
- 既存の`pick_generic_seed(count)`はそのまま残す（後方互換・他箇所からの参照可能性のため）

`ronin_threads_action.py`は投稿本文を`classify_category`に通してカテゴリを判定し、`pick_generic_seed`の呼び出しを`pick_seed_question(count, theme_key)`に置き換える。

## 3. CTA（Substack）のテーマ連動

### 前提: 公開URLの自動記録

現状、`substack_auto_post.py`・`substack_deep_dive_auto_post.py`は公開後に`post_id`のみ`progress`に保存しており、公開URLが記録されていない。両スクリプトの`create_and_publish_post`で、ドラフト作成レスポンス（`draft_resp.json()`）から`slug`を取得し、`return post_id, slug`に変更。呼び出し側の`main()`で`progress["history"]`への追記時に`"url": f"{PUBLICATION_URL}/p/{slug}"`を追加する。既存の履歴エントリ（過去分）には`url`が無いため、テーマ連動の対象は新規記事のみ（過去記事は対象外）。

### CTAテーマ連動（`ronin_threads_action.py`）

`cta_line_for_cycle(history_count)`を拡張し、投稿テキストの`theme_key`を引数に追加: `cta_line_for_cycle(history_count, theme_key=None)`。

- cycle==0（Gumroad回）: 変更なし（単一商品のため連動不要）
- cycle==7（Substack回）: `theme_key`が渡され、`deep_dive_progress.json`/`substack_progress.json`の履歴に同じ`theme_key`で分類できて`url`を持つ記事があれば、その記事のURLを使ったCTA行を返す。該当が無ければ既存の`SUBSTACK_LINE`（プロフィールURL）にフォールバック
- 記事側のカテゴリ判定は、記事の`title`（英語）を`classify_category`に通して行う（本文全文は長すぎるため）

## 4. reply_engineの設定強化（本稼働はしない）

`ronin_reply_engine.py`の`OPENERS`を5種→8種に拡充（英語の枕詞を追加）。`ronin_reply_engine_config.json`の`daily_cap`/`per_run`をskinの見直し比率（daily_cap 25→10、per_run 4→2）に合わせて調整。`RONIN_REPLY_ENGINE_ENABLED`は設定しない（未設定=OFFのまま）。Meta App Reviewでキーワード検索権限が取れた場合にすぐ動かせる状態にするだけの準備。

## 5. 週次自動レポート（新規: `ronin/ronin_weekly_report.py` + workflow）

`skin_weekly_report.py`を移植した`ronin_weekly_report.py`を新規作成する。

- データソース: `ronin_analytics.json`の`posts_history`（直近7日を抽出）
- サマリー: 投稿数・平均views・平均いいね・平均エンゲージ率・合計views
- 伸びた投稿Top5（views順）
- roninにはA/B判定が無いため、代わりに`ronin_optimization_index.json`の`pattern_ranking`上位を表示するセクションに置き換える
- 次の打ち手: ルールベース（views低迷・いいね低迷・エンゲージ率低迷それぞれに対する提案文。「reply_engineの有効化」は権限問題があるため提案文からは除外し、代わりに「reply_hunterでの手動巡回」を促す文言にする）
- レポート本文を`ronin/ronin_weekly_report.md`に書き出し、`GMAIL_APP_PASSWORD`（既存Secret共用）があればGmail通知

新規workflow `.github/workflows/ronin_weekly_report.yml`（skinと同型）:
- `cron: '0 23 * * 0'`（JST月曜08:00、skinと同時刻）
- `workflow_dispatch`で手動実行可
- レポートmdをコミット＆push

## テスト方針

既存の`ronin/tests/`にpytestを追加する。

- `ronin_theme_classifier.classify_category`: 既存の`test_ronin_reply_engine.py`（あれば）のテストケースを移動・拡張
- `ronin_comment_seeder.pick_seed_question`: カテゴリ有り/無しの分岐
- `ronin_threads_action.cta_line_for_cycle`: theme_key有り（記事URL見つかる/見つからない）・theme_key無しの3パターン
- `ronin_weekly_report`: `skin_weekly_report`のテストケースを移植（`build_report`・`summarize`・`recent_posts`・`suggest_next_actions`）

## スコープ外（今回やらないこと）

- `ronin_reply_hunter.py`（半自動リプ下書き）の改善・運用開始 — 手動コピペが必須なため対象外
- reply_engineの本稼働（`RONIN_REPLY_ENGINE_ENABLED=true`） — Meta App Review権限が無いため不可能
- Gumroadの複数商品化・テーマ別パック — 現状1商品のみで連動する対象がない
- 過去のSubstack記事へのURL遡及記録 — 新規記事から記録開始
