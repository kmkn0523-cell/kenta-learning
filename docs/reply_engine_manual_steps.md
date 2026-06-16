# リプライ・エンジン 手動作業 ステップバイステップ

> skin / ronin の自動リプライ・エンジンを「本番で動く」状態にするための、Kenta本人がPCでやる作業のまとめ。
> コードは全部できている。ここに書いてあるのは**人がやる手作業だけ**。
> 作成: 2026-06-16 / 関連: `docs/threads_app_review_keyword_search.md`

---

## 全体の流れ（先に地図）

```
Phase A: 録画（トークン不要・すぐできる）
   ↓
Phase B: Meta に App Review 申請（skin と ronin で別々に）
   ↓  ←★ここが一番時間かかる（数日〜数週・審査）
Phase C: 承認後のトークン・設定まわり
   ↓
Phase D: リハーサル → 本稼働
```

⚠️ **skin と ronin は別アカウント＝別Metaアプリ**。App Review も**それぞれ別に申請**が必要。
作業も基本「skinで一通り → roninで同じこと」をやる。

---

## Phase A: スクリーンキャストの録画（トークン不要・今すぐできる）

App Review では「権限を実際に使う画面」の録画動画が要る。先に撮っておく。

### A-1. skin の画面を録画
ターミナルで起動:
```
cd skin && python3 skin_reply_review_ui.py --demo
```
ブラウザで開く:
```
http://127.0.0.1:8765
```
画面録画しながら次の順で操作する:
1. キーワード（例: `腸活`）を入れて「検索」
2. 投稿が一覧で出るのを見せる
3. 1件選んで、返信文を確認して「この内容で返信を送る」を押す
4. 「送信しました」的な表示を見せる

録画を止める → サーバは `Ctrl+C` で停止。

### A-2. ronin の画面を録画
```
cd ronin && python3 ronin_reply_review_ui.py --demo
```
ブラウザで開く:
```
http://127.0.0.1:8766
```
同じ流れで録画（キーワードは `discipline` など英語）。

> ポイント: 「検索して一覧を見て、人が選んで送る」流れを見せること。これが審査を通しやすくする。

---

## Phase B: Meta App Review 申請（skin・ronin それぞれ）

申請に貼る文章・台本・注意点は別ファイルに用意済み:
```
docs/threads_app_review_keyword_search.md
```

### B-1. 開発者ダッシュボードで権限を追加
1. https://developers.facebook.com/ → 対象のThreadsアプリを開く（まずskin）
2. 権限に追加:
   ```
   threads_keyword_search
   ```
3. その権限の **Advanced Access** を申請する（他人の投稿を検索するのに必須）

### B-2. 申請フォームに必要なものを入れる
- **ユースケース説明文**: `docs/threads_app_review_keyword_search.md` の「説明文ドラフト」をコピペ
- **プライバシーポリシーURL**: 下記を貼る
  ```
  https://kmkn0523-cell.github.io/kenta-learning/privacy.html
  ```
- **スクリーンキャスト**: Phase A で撮った動画をアップロード

### B-3. ビジネス認証を求められたら対応
書類提出を求められたら出す（数日かかる）。

### B-4. ronin でも B-1〜B-3 を同じようにやる
roninのMetaアプリで `threads_keyword_search` の Advanced Access を申請。
説明文・プライバシーポリシーURLは同じものを流用してよい。録画はroninの動画を使う。

> ★審査の結果待ち。承認が出るまで Phase C には進めない。

---

## Phase C: 承認が出たあとの設定（トークン・シークレット・変数）

### C-1. トークンを再発行（keyword_search 込み）
手順書に従って、`threads_keyword_search` を含めてアクセストークンを取り直す:
```
docs/threads_token_renewal.md
```
skin・ronin それぞれのアカウントで行う。

### C-2. `.env` を更新（自分のPCで手で書き換え）
`.env` を開いて、該当のトークンを新しい値に上書き保存する。

- skin:
  ```
  THREADS_ACCESS_TOKEN
  ```
- ronin:
  ```
  RONIN_THREADS_ACCESS_TOKEN
  ```

### C-3. GitHub Secrets を更新
GitHubリポジトリ → Settings → Secrets and variables → Actions → **Secrets** タブで、上と同じ名前のシークレットを新しいトークン値に更新する。

### C-4. 有効化スイッチ（変数）を作る
同じ画面の **Variables** タブで、次の変数を作る（値はまず `false`）:

- skin:
  ```
  SKIN_REPLY_ENGINE_ENABLED = false
  ```
- ronin:
  ```
  RONIN_REPLY_ENGINE_ENABLED = false
  ```

> この変数が `true` でない限りエンジンは絶対に動かない（安全装置）。テストが終わるまで `false`。

### C-5. （任意）roninのハンドル名を確認
`ronin/ronin_reply_engine_config.json` の `my_username` を `roninwords` と仮置きしている。
実際のThreadsのユーザー名と違うなら直す（大小の違いは無視するので、綴りが同じならOK）。

---

## Phase D: リハーサル → 本稼働

### D-1. 1回だけ手動でテスト実行
1. C-4 の変数を一時的に `true` にする（まず skin だけ）
2. GitHub → Actions タブ → `skin Threads リプライ・エンジン` → `Run workflow`（手動実行）
3. 実行ログで「返信 1/4 → @… 完了: N 件返信」を確認
4. 実際にThreadsアプリで、返信が自然に付いているか目視確認

### D-2. 問題なければ本稼働
- 文面・送信先に問題なし → 変数 `true` のままにすると、cron（1日6回）で自動稼働が始まる
- 違和感あり → 変数を `false` に戻して停止 → テンプレやキーワードを調整

### D-3. ronin も同じように D-1〜D-2
roninは `ronin Threads リプライ・エンジン` ワークフロー、変数 `RONIN_REPLY_ENGINE_ENABLED` で同じ手順。

---

## 困ったときの早見表

| やりたいこと | コマンド/場所 |
|---|---|
| skin UIを見る | `cd skin && python3 skin_reply_review_ui.py --demo` → `http://127.0.0.1:8765` |
| ronin UIを見る | `cd ronin && python3 ronin_reply_review_ui.py --demo` → `http://127.0.0.1:8766` |
| エンジンを止める | GitHub変数 `*_REPLY_ENGINE_ENABLED` を `false` |
| 申請の説明文・台本 | `docs/threads_app_review_keyword_search.md` |
| プライバシーポリシー | `https://kmkn0523-cell.github.io/kenta-learning/privacy.html` |
| トークン再発行手順 | `docs/threads_token_renewal.md` |

> ★迷ったらClaude Codeに「リプライ・エンジンの手動作業、今どこまでやればいい？」と聞けば、このファイルを見て次の一歩を案内できる。
