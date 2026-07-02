# Threads keyword_search App Review 申請ガイド（ronin / @RoninWords版）

> ronin リプライ・エンジン（`ronin/ronin_reply_engine.py`）を本番稼働させるための、
> `threads_keyword_search` の **Advanced Access**（他人の投稿を検索する権限）を取るための申請手順書。
> 作成: 2026-07-02 / skin版（`docs/threads_app_review_keyword_search.md`）の構成を踏襲し、@RoninWords（英語アカウント）向けに書き換えたもの。
> 関連: `docs/reply_engine_manual_steps.md`

⚠️ **skin と ronin は別アカウント＝別Metaアプリ**。App Review は skinで申請済みでも免除されない。**このファイルの内容で ronin 側のMetaアプリに別途申請する**。

---

## なぜ App Review が必要か

`keyword_search` には2段階のアクセスがある。

| アクセス区分 | 検索できる範囲 | App Review |
|---|---|---|
| Standard Access | **自分（Threadsテスター）の投稿だけ** | 不要 |
| Advanced Access | **他人を含む全公開投稿** | **必須**（＋ビジネス認証を求められる場合あり） |

リプライ・エンジンの目的は「**他人**の英語圏のニッチ投稿（discipline / stoicism / purpose 系）を見つけて返信し、フォロワーを増やす」こと。
標準アクセスのままだと自分の投稿しか引っかからず、`is_repliable` が自分の投稿を弾くため **返信対象ゼロで空振り**する。
したがって本稼働には Advanced Access＝App Review が避けられない。

---

## ⚠️ 最大のリスク：全自動ボットは却下されやすい

App Review のスクリーンキャストは本来「**アプリ内でユーザーがどう操作してこの権限を使うか**」を見せる前提。
ところがこのエンジンは **UIのない全自動ボット**（GitHub Actions の cron が勝手に検索・返信）。
Meta は「自動化された無差別エンゲージメント＝スパム」を警戒するため、**素の自動返信ボットは却下リスクが高い**。

### 通しやすくするための方針（どれかに寄せる）
1. **「運用者向け内部ツール」として申請する**
   「RoninWords運用者が、自社テーマ（規律／ストイシズム／自己成長）の公開投稿を**収集・モニタリング**し、関連性の高い投稿に**人間が確認した上で**返信するための社内補助ツール」という位置づけにする。
   → スクリーンキャストでは「検索結果が一覧表示され、運用者が選んで返信する」フローを見せる（＝半自動のUIを1枚噛ませる）。
2. **検索（read）を主目的に申請する**
   申請の主眼を「キーワードで関連投稿を**集めて分析する**」に置き、返信は副次機能として控えめに説明する。keyword_search 自体は read 権限なので、検索ユースケースのほうが説明が通りやすい。
3. **無差別連投に見せない**
   日次上限・著者あたり上限・ランダム間隔・テンプレ連投禁止など、**スパム抑制の仕組みが入っている**ことを明記する（実際にコードに実装済み。下記参照）。

> 結論：純粋な「cronで全自動返信」を正直に申請すると弾かれやすい。
> **「投稿モニタリング＋運用者補助」**として申請し、最小限のUI（検索結果ビュー）を用意するのが現実的。

---

## 申請に必要なもの チェックリスト

- [ ] Meta開発者アカウントのビジネス認証（Business Verification）— 求められたら会社/個人事業の確認書類が必要（skinで認証済みでも、ronin用アプリが別なら再度求められる場合あり）
- [ ] アプリのプライバシーポリシーURL（公開Webページ）
- [ ] アプリアイコン・名称・カテゴリ設定の完了
- [ ] `threads_keyword_search` の Advanced Access 申請フォーム記入
- [ ] ユースケース説明文（下記ドラフト・英語）
- [ ] スクリーンキャスト動画（下記台本）— 実際に権限を使う様子を録画
- [ ] テストユーザー手順（レビュアーが再現できる手順）

---

## ユースケース説明文ドラフト（コピペ用）

申請フォームの「How will your app use this permission?」に貼る想定。
RoninWordsは**英語圏アカウント**のため、申請フォームには英語をそのまま使う（日本語訳は社内理解用の補足）。

### English（そのまま貼る）
```
This app is an internal tool that supports content operations for the
@RoninWords Threads account, which publishes short quotes and reflections
on stoicism, discipline, and self-improvement. Using threads_keyword_search,
it collects public English-language posts related to specific keywords
(e.g. discipline, stoicism, purpose, deep work, consistency). An operator
reviews topical relevance before any reply is sent, with the goal of
providing encouraging, on-topic responses. To prevent indiscriminate
sending, the tool enforces a daily reply cap, a per-author cap, randomized
send intervals, and a no-repeat rule for templated text.
```

### 日本語（補足用・社内確認のため）
```
本アプリは、ストイシズム・規律・自己成長をテーマにした英語の格言投稿アカウント
@RoninWords のコンテンツ運用を支援する社内ツールです。
threads_keyword_search を用いて「discipline」「stoicism」「purpose」等の
特定キーワードに関連する英語の公開投稿を収集し、運用者がテーマとの関連性を
確認した上で、励ましや共感を目的とした返信を行います。
無差別な送信を防ぐため、1日あたりの返信上限・同一ユーザーへの上限・
送信間隔のランダム化・定型文の連続使用禁止を実装しています。
```

---

## スクリーンキャスト台本（録画する内容）

レビュアーは「権限が実際に使われる様子」を見たい。以下を画面録画する。

1. **アプリのログイン／権限同意画面**を映す（Threadsアカウント `@RoninWords` で認可する流れ）。
2. **キーワード入力 → 検索実行**：例「discipline」で検索し、`keyword_search` の結果一覧が表示される様子。
3. **検索結果の一覧表示**：取得した投稿（本文・著者・日時）が並ぶUIを見せる ← ここが「read目的」の証拠になる。
4. **運用者が1件選んで返信**：関連性を確認 → 返信文を確認 → 送信、までを手動操作で見せる。
5. **スパム抑制の説明テロップ**：「1日◯件まで／同一ユーザー1日1件／送信間隔ランダム」を字幕で補足。

> ポイント：全自動cronの裏側ではなく、**人が確認して送る前段のUI**を見せること。
> このUIは `ronin/ronin_reply_review_ui.py`（`--demo`）に用意済み。これを録画する。

### 録画の段取り（実際にコマンドで動作確認済み）

```
cd /home/kenta_kamijyo/ronin && python3 ronin_reply_review_ui.py --demo
```

ブラウザで開く:
```
http://127.0.0.1:8766
```

画面録画しながら次の順で操作する:
1. キーワード（例: `discipline`）を入れて「検索」ボタンを押す
2. サンプル投稿4件が一覧表示されるのを見せる（`@user_marcus` 等のダミー投稿）
3. 1件選んで、返信文（テンプレ合成の下書き）を確認し「この内容で返信を送る」を押す
4. 「[DEMO] 送信したつもりです」の表示（実送信なし）を見せる

録画を止める → サーバは `Ctrl+C` で停止。

> ✅ 動作確認済み（2026-07-02）: `curl` で `GET /?q=discipline` が `HTTP 200` を返し、
> `@user_marcus` `@user_sen` `@user_kai` `@user_sky` の4件のサンプルカードが表示されることを確認。
> `POST /send` も `[DEMO] @user_marcus への返信を送信したつもりです（実送信なし）` を返すことを確認済み。

---

## レビュアー再現手順ドラフト（Test Instructions・コピペ用）

申請フォームの「Step-by-step instructions to test the integration」に貼る想定。
レビュアーが手元で同じ画面を再現できるよう、UIの操作手順をそのまま書く。

### English
```
This permission is used through an operator-facing review UI.

1. Start the review tool:
   cd ronin && python3 ronin_reply_review_ui.py
2. Open http://127.0.0.1:8766 in a browser.
3. Enter a keyword related to discipline / stoicism / self-improvement
   (e.g. "discipline") and click Search. The app calls
   threads_keyword_search and lists the matching public posts
   (text, author, timestamp).
4. The operator reviews the listed posts for topical relevance, selects one,
   reviews the suggested reply text, edits if needed, and clicks Send.
5. Only the post the operator explicitly selected receives a reply.

A demo mode (add the --demo flag) shows the same flow with sample data and
does not send any live reply, so reviewers can inspect the UI without posting.
```

### 日本語（補足用）
```
本権限は、運用者向けの確認UIを通じて使用します。
1. ツール起動: cd ronin && python3 ronin_reply_review_ui.py
2. ブラウザで http://127.0.0.1:8766 を開く
3. discipline／stoicism／self-improvement関連のキーワード（例「discipline」）で
   検索 → threads_keyword_search が公開投稿を一覧表示
4. 運用者が関連性を確認し1件選択 → 返信文を確認・編集 → 送信
5. 運用者が選んだ投稿にのみ返信が送られる
（--demo を付けるとサンプルデータで同じ流れを実送信なしで確認できる）
```

---

## 既に実装済みのスパム抑制（申請でアピールできる材料）

`ronin/ronin_reply_engine_config.json` と `ronin_reply_engine.py` に実装済み。

| 抑制策 | 設定キー / 実装 | 値 |
|---|---|---|
| 1日の返信上限 | `daily_cap` | 10 |
| 1回の実行あたり上限 | `per_run` | 2 |
| 同一著者への上限/日 | `max_per_author_per_day` | 1 |
| 短すぎる投稿を除外 | `min_post_length` | 20 |
| 宣伝投稿を除外（URL過多） | `max_urls` | 1 |
| 英語以外を除外 | `contains_english()` | ASCII英字15文字以上 |
| 自分の投稿を除外 | `is_repliable()` | — |
| 返信済み重複防止 | `replied_post_ids` | — |
| 定型文の連続使用禁止 | `recent_replies` / `compose_reply()` | 直近60件 |
| 送信間隔のランダム化 | `min/max_sleep_seconds` | 20〜90秒 |
| キルスイッチ | `RONIN_REPLY_ENGINE_ENABLED` | 既定で停止 |

> skin版との違い：言語判定が「日本語を含むか」ではなく「ASCII英字15文字以上か」（`contains_english()`）。
> `min_post_length` は skin の15に対して ronin は20（英語は日本語より1文あたりの文字数が多いため）。

---

## 申請のために必要なもの

App Review を「投稿モニタリング＋運用者補助」として通すための準備物。

1. ✅ **検索結果ビュー（運用者補助UI）**：`ronin/ronin_reply_review_ui.py`。`--demo` で起動すると、キーワード検索→結果一覧→運用者が1件選んで返信→送信、までを画面で操作できる。スクリーンキャストはこのUIを録画する。
   ```
   cd /home/kenta_kamijyo/ronin && python3 ronin_reply_review_ui.py --demo
   ```
   ブラウザ: `http://127.0.0.1:8766`（動作確認済み 2026-07-02）
2. ✅ **プライバシーポリシーの公開ページ**：skinと共通のものを流用する（同一リポジトリ内のGitHub Pages）。
   ```
   https://kmkn0523-cell.github.io/kenta-learning/privacy.html
   ```
   ※ ronin用に別ページが必要と審査側から指摘された場合は、@RoninWords向けの文言に差し替えたページを別途用意する（未着手）。
3. ✅ **申請文・台本**：このファイル（説明文ドラフト・スクリーンキャスト台本・レビュアー再現手順）に確定保存済み。

> 準備は完了。あとは Phase A（録画）→ Phase B（フォーム提出）を実行するだけ。手順は `docs/reply_engine_manual_steps.md` の B-4（ronin編）。

---

## 申請後の流れ

1. フォーム提出 → ビジネス認証が未了なら先に求められる（書類提出 → 数日）。
2. App Review 審査（数日〜数週、却下されたら理由を見て再提出）。
3. 承認 → Advanced Access 有効 → トークン再発行（`threads_keyword_search` 込み）。
4. `.env` の `RONIN_THREADS_ACCESS_TOKEN` / GitHub Secrets の同名シークレットを更新 → 実機検証 → リハーサル → `RONIN_REPLY_ENGINE_ENABLED=true` で本稼働。

詳細な手順（トークン再発行・Secrets更新・変数作成・リハーサル）は `docs/reply_engine_manual_steps.md` の Phase C・D を参照（skin/roninで手順は共通、対象の環境変数名だけ読み替える）。

---

## 補足：審査が重いと感じたら

「他人投稿の自動返信」は審査・ポリシー両面で重い。もし通過が難しい／時間がかかりすぎる場合、
keyword_search を使わずフォロワーを増やす代替ルート（観測対象アカウントへの手動リプ運用、
Reels自動投稿〔`project_ronin_instagram_reels_running`〕への投下強化など）に切り替える選択肢もある。
その場合は計画書を別途作り直す。
