# ジュエリーSNS週次ダイジェスト 設計書

作成日: 2026-06-20

## 1. 目的

毎週土曜の朝（JST 7:30）に、以下2つのジュエリーに関するSNS投稿を直近1週間ぶん集めて、メールで自分宛てに送る。

- サントスネックレス
- ジュストアンクルブレスレット

目的は「とにかく言及を網羅」すること。価格・スタイリング等に絞らず、その週に出た言及を広く拾う。

## 2. 前提・制約

- 無料運用・初心者運用・壊れにくさを最優先する。
- X / Instagram / Threads を各APIで直接叩く方式は、無料枠では検索ができない・審査が必要・スクレイピングが壊れやすい、という理由で採用しない。
- 代わりに **Web検索API（Exa）でSNS各ドメインを横断検索する** 方式を採る。1つの仕組みで全SNS＋Web全般をカバーでき、壊れにくい。
- Exaは無料枠（月1000検索）があり、週1回×数クエリなら無料内に収まる。
- 実行基盤は既存の iPhone 価格監視（`price_watch/`）と同じ GitHub Actions cron + Python + Gmail送信 + 状態JSONコミット のパターンを流用する。

## 3. ディレクトリ・ファイル構成

```
jewelry_watch/
  jewelry_sns_digest.py      # 本体スクリプト
  jewelry_watch_state.json   # 送信済みURLの記録（重複防止）
.github/workflows/
  jewelry_sns_weekly.yml     # 土曜 7:30 JST に実行する cron
tests/
  test_jewelry_sns_digest.py # pytest
```

## 4. データの流れ

1. 監視キーワード2件 × 検索対象（X / Instagram / Threads / Web全般）の組み合わせで **Exa API** に「直近7日」の条件で問い合わせる。
2. 各結果から タイトル・URL・抜粋・投稿日・プラットフォーム を取り出して集約する。
3. `jewelry_watch_state.json` に記録した送信済みURLと照合し、**新規分だけ**を残す（毎週同じ投稿が再掲されないようにする）。
4. キーワード別 → プラットフォーム別にグループ化した **HTMLメール** を組み立て、Gmail（`smtplib` の `SMTP_SSL`）で自分宛てに送る。
5. 今回拾ったURLを state に追記し、Gitにコミット＆プッシュする（既存ワークフローと同じ仕組み）。

## 5. 仕様詳細

### 検索対象ドメイン
- X: `x.com`, `twitter.com`
- Instagram: `instagram.com`
- Threads: `threads.net`, `threads.com`
- Web全般: ドメイン指定なしの検索を1本追加（ブログ・まとめ記事等の言及も拾う）

### Exa API 呼び出し
- エンドポイント: `POST https://api.exa.ai/search`
- 認証: ヘッダー `x-api-key: <EXA_API_KEY>`
- 主なパラメータ:
  - `query`: キーワード（例: `サントスネックレス`）
  - `startPublishedDate`: 実行時刻の7日前（ISO8601）
  - `includeDomains`: 上記ドメイン群（Web全般クエリでは指定なし）
  - `numResults`: 20
  - `contents`: タイトル・抜粋（text）を取得
- プラットフォーム名はヒットしたURLのドメインから判定する。

### 件数・絞り込み
- キーワード × 検索対象ごとに最大20件。
- 新規（state未登録）のURLのみメールに載せる。

### メール
- 件名例: `【ジュエリーSNS週報】6/20 新規◯件`
- 本文はHTML。キーワード見出し → プラットフォーム小見出し → 各投稿（タイトル＋抜粋＋クリック可能なリンク＋投稿日）の順に並べる。
- 新規がゼロの週も「今週は新しい言及なし」と1通送る（稼働確認を兼ねる）。

### 重複防止（state）
- `jewelry_watch_state.json` は `{"seen": [{"url": ..., "first_seen": "YYYY-MM-DD"}, ...]}` 形式。
- URL単位で重複判定する。
- stateが肥大化しないよう、`first_seen` が60日より古いエントリは保存時に捨てる。

### エラーハンドリング
- Exa呼び出し失敗（HTTPエラー・タイムアウト）は握りつぶさず、可能ならエラー内容をメール本文かログに全文出す。
- 一部のクエリだけ失敗しても、成功したぶんは送る（全部巻き込んで落とさない）。
- メール送信失敗時は例外を上げてActionsを失敗扱いにし、気付けるようにする。

## 6. 必要なシークレット / ライブラリ

- シークレット（GitHub Actions secrets）:
  - `EXA_API_KEY`（新規取得・設定が必要）
  - `GMAIL_ADDRESS`（既存流用）
  - `GMAIL_APP_PASSWORD`（既存流用）
- ライブラリ:
  - `requests`（Exa呼び出し用・新規）
  - `python-dotenv`（既存）

## 7. テスト

`tests/test_jewelry_sns_digest.py` を追加し、外部I/O（Exa API・メール送信）はモックして以下を検証する。

- ExaレスポンスJSONのパース（タイトル・URL・抜粋・日付・プラットフォーム判定）
- 重複除外ロジック（state済みURLが除かれる／新規だけ残る）
- 60日より古いstateエントリの掃除
- 新規ゼロ時の本文生成
- HTMLメール本文の組み立て（キーワード別・プラットフォーム別グループ化）

## 8. スケジュール

`.github/workflows/jewelry_sns_weekly.yml`:
- cron: `30 22 * * 5`（UTC金曜22:30 = JST土曜7:30）
- `workflow_dispatch` で手動実行も可能にする（テスト用）
- `concurrency` グループで多重実行を防ぐ
- state更新のコミット＆プッシュ手順は iPhone 価格監視ワークフローと同形にする。

## 9. やらないこと（スコープ外）

- SNS各APIの直接連携（X有料API・Instagramハッシュタグ連携・Threads keyword_search 審査）。
- 投稿への自動アクション（いいね・リプ等）。
- ダッシュボードやWeb UI。今回はメール送付のみ。
