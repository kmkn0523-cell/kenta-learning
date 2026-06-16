# Threads keyword_search App Review 申請ガイド

> skin リプライ・エンジン（`skin/skin_reply_engine.py`）を本番稼働させるための、
> `threads_keyword_search` の **Advanced Access**（他人の投稿を検索する権限）を取るための申請手順書。
> 作成: 2026-06-16 / 関連計画書: `docs/superpowers/plans/2026-06-15-skin-threads-reply-engine.md`

---

## なぜ App Review が必要か

`keyword_search` には2段階のアクセスがある。

| アクセス区分 | 検索できる範囲 | App Review |
|---|---|---|
| Standard Access | **自分（Threadsテスター）の投稿だけ** | 不要 |
| Advanced Access | **他人を含む全公開投稿** | **必須**（＋ビジネス認証を求められる場合あり） |

リプライ・エンジンの目的は「**他人**のニッチ投稿を見つけて返信し、フォロワーを増やす」こと。
標準アクセスのままだと自分の投稿しか引っかからず、`is_repliable` が自分の投稿を弾くため **返信対象ゼロで空振り**する。
したがって本稼働には Advanced Access＝App Review が避けられない。

---

## ⚠️ 最大のリスク：全自動ボットは却下されやすい

App Review のスクリーンキャストは本来「**アプリ内でユーザーがどう操作してこの権限を使うか**」を見せる前提。
ところがこのエンジンは **UIのない全自動ボット**（GitHub Actions の cron が勝手に検索・返信）。
Meta は「自動化された無差別エンゲージメント＝スパム」を警戒するため、**素の自動返信ボットは却下リスクが高い**。

### 通しやすくするための方針（どれかに寄せる）
1. **「運用者向け内部ツール」として申請する**
   「skin運用者が、自社テーマ（インナーケア／肌悩み）の公開投稿を**収集・モニタリング**し、関連性の高い投稿に**人間が確認した上で**返信するための社内補助ツール」という位置づけにする。
   → スクリーンキャストでは「検索結果が一覧表示され、運用者が選んで返信する」フローを見せる（＝半自動のUIを1枚噛ませる）。
2. **検索（read）を主目的に申請する**
   申請の主眼を「キーワードで関連投稿を**集めて分析する**」に置き、返信は副次機能として控えめに説明する。keyword_search 自体は read 権限なので、検索ユースケースのほうが説明が通りやすい。
3. **無差別連投に見せない**
   日次上限・著者あたり上限・ランダム間隔・テンプレ連投禁止など、**スパム抑制の仕組みが入っている**ことを明記する（実際にコードに実装済み。下記参照）。

> 結論：純粋な「cronで全自動返信」を正直に申請すると弾かれやすい。
> **「投稿モニタリング＋運用者補助」**として申請し、最小限のUI（検索結果ビュー）を用意するのが現実的。

---

## 申請に必要なもの チェックリスト

- [ ] Meta開発者アカウントのビジネス認証（Business Verification）— 求められたら会社/個人事業の確認書類が必要
- [ ] アプリのプライバシーポリシーURL（公開Webページ）
- [ ] アプリアイコン・名称・カテゴリ設定の完了
- [ ] `threads_keyword_search` の Advanced Access 申請フォーム記入
- [ ] ユースケース説明文（下記ドラフト）
- [ ] スクリーンキャスト動画（下記台本）— 実際に権限を使う様子を録画
- [ ] テストユーザー手順（レビュアーが再現できる手順）

---

## ユースケース説明文ドラフト（コピペ用）

申請フォームの「How will your app use this permission?」に貼る想定。日本語申請でも英語併記が無難。

### 日本語
```
本アプリは、スキンケア／インナーケア領域のコンテンツ運用を支援する社内ツールです。
threads_keyword_search を用いて「腸活」「肌荒れ」「インナーケア」等の特定キーワードに
関連する公開投稿を収集し、運用者がテーマとの関連性を確認した上で、
有益な情報提供を目的とした返信を行います。
無差別な送信を防ぐため、1日あたりの返信上限・同一ユーザーへの上限・
送信間隔のランダム化・定型文の連続使用禁止を実装しています。
```

### English
```
This app is an internal tool that supports content operations in the
skincare / inner-care space. Using threads_keyword_search, it collects
public posts related to specific keywords (e.g. gut health, skin troubles,
inner care). An operator reviews topical relevance before any reply is sent,
with the goal of providing helpful information. To prevent indiscriminate
sending, the tool enforces a daily reply cap, a per-author cap, randomized
send intervals, and a no-repeat rule for templated text.
```

---

## スクリーンキャスト台本（録画する内容）

レビュアーは「権限が実際に使われる様子」を見たい。以下を画面録画する。

1. **アプリのログイン／権限同意画面**を映す（Threadsアカウントで認可する流れ）。
2. **キーワード入力 → 検索実行**：例「腸活」で検索し、`keyword_search` の結果一覧が表示される様子。
3. **検索結果の一覧表示**：取得した投稿（本文・著者・日時）が並ぶUIを見せる ← ここが「read目的」の証拠になる。
4. **運用者が1件選んで返信**：関連性を確認 → 返信文を確認 → 送信、までを手動操作で見せる。
5. **スパム抑制の説明テロップ**：「1日◯件まで／同一ユーザー1日1件／送信間隔ランダム」を字幕で補足。

> ポイント：全自動cronの裏側ではなく、**人が確認して送る前段のUI**を見せること。
> このUIは現状エンジンに無いので、申請用に最小の検索結果ビューを別途用意する必要がある（下記「申請のために追加実装が要るもの」）。

---

## 既に実装済みのスパム抑制（申請でアピールできる材料）

`skin/skin_reply_engine_config.json` と `skin_reply_engine.py` に実装済み。

| 抑制策 | 設定キー / 実装 | 値 |
|---|---|---|
| 1日の返信上限 | `daily_cap` | 25 |
| 1回の実行あたり上限 | `per_run` | 4 |
| 同一著者への上限/日 | `max_per_author_per_day` | 1 |
| 短すぎる投稿を除外 | `min_post_length` | 15 |
| 宣伝投稿を除外（URL過多） | `max_urls` | 1 |
| 日本語以外を除外 | `contains_japanese()` | — |
| 自分の投稿を除外 | `is_repliable()` | — |
| 返信済み重複防止 | `replied_post_ids` | — |
| 定型文の連続使用禁止 | `recent_replies` / `compose_reply()` | 直近60件 |
| 送信間隔のランダム化 | `min/max_sleep_seconds` | 20〜90秒 |
| キルスイッチ | `SKIN_REPLY_ENGINE_ENABLED` | 既定で停止 |

---

## 申請のために追加実装が要るもの（PCに触れる時の作業候補）

App Review を「投稿モニタリング＋運用者補助」として通すなら、最低限これが要る。
（現状エンジンは全自動でUIが無いため）

1. **検索結果ビュー**（最小UI）：keyword_search の結果を一覧表示し、運用者が選んで返信できる簡易画面。
   - 案: ローカルで動く軽量な確認用スクリプト or 簡易Webページ。スクリーンキャスト用に最小限でよい。
2. **プライバシーポリシーの公開ページ**：1枚の静的ページで可。
3. （任意）申請文・台本の最終版を `docs/` に確定保存。

> ※これらは「審査を通すため」の作業。標準アクセス検証で空振りを確認してから着手するのが順序として正しい。

---

## 申請後の流れ

1. フォーム提出 → ビジネス認証が未了なら先に求められる（書類提出 → 数日）。
2. App Review 審査（数日〜数週、却下されたら理由を見て再提出）。
3. 承認 → Advanced Access 有効 → トークン再発行（`threads_keyword_search` 込み）。
4. `.env` / GitHub Secrets 更新 → 実機検証 → リハーサル → `SKIN_REPLY_ENGINE_ENABLED=true` で本稼働。

---

## 補足：審査が重いと感じたら

「他人投稿の自動返信」は審査・ポリシー両面で重い。もし通過が難しい／時間がかかりすぎる場合、
keyword_search を使わずフォロワーを増やす代替ルート（既存 `skin_reply_hunter.py` を運用者の手動補助に使う、
観測対象アカウントへの手動リプ運用など）に切り替える選択肢もある。
その場合は計画書を別途作り直す。
