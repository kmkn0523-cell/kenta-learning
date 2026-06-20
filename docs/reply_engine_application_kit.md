# リプライ・エンジン 申請キット（これ1枚で提出まで進める）

> skin の自動リプライ・エンジンを本番稼働させるための、**Kenta本人がやる手作業を最小化**した実行キット。
> コード・申請素材・プライバシーポリシーは準備済み。あなたは「録画」と「フォーム提出」だけ。
> 作成: 2026-06-20 / 素材: `docs/privacy_policy.html`・`docs/threads_app_review_keyword_search.md`

---

## 全体像（所要：あなたの実作業は合計1〜2時間＋審査待ち数日〜数週）

```
ステップ0  プライバシーポリシーを公開      … 5分（GitHub設定）
ステップ1  アプリ設定の確認               … 5分
ステップ2  画面録画                       … 15分（台本あり・読むだけ）
ステップ3  申請フォーム提出               … 20分（貼り付け文あり）
ステップ4  ビジネス認証（求められたら）    … 書類提出→数日
─────────  ここから審査待ち（数日〜数週）  ─────────
ステップ5  承認後の本稼働                 … 15分（手順あり）
```

---

## ステップ0: プライバシーポリシーを公開する（✅完了済み）

GitHub Pages は既に有効（公開元: main / ルート）。`docs/privacy_policy.html` を
`.gitignore` の許可漏れで未pushだったのを修正し、コミット＆pushで公開済み。
申請フォームに貼る公開URLはこれ（`/docs/` が付く点に注意）:
```
https://kmkn0523-cell.github.io/kenta-learning/docs/privacy_policy.html
```
ブラウザで開いて表示されることを確認するだけでOK。

> ※ ルート公開なのでリポジトリ内の他ファイルもURLで読める状態（元々Publicなので新たな漏えいは無い）。

---

## ステップ1: アプリ設定の確認（5分）

Meta開発者コンソール:
```
https://developers.facebook.com/apps/
```
**RoninWordsアプリ（APP_ID=1173361818193107）** を開く。skinとroninは同じMetaアプリを共用しており、skin専用アプリは存在しない（トークン更新手順書 `docs/threads_token_renewal.md` 参照）。以下が埋まっているか確認：
- [ ] アプリ名（例: `skin_reset_jp content tool`）
- [ ] アプリアイコン（正方形画像。無ければ簡単なものでOK）
- [ ] カテゴリ
- [ ] プライバシーポリシーURL欄に**ステップ0のURL**を貼る（設定→基本設定）

---

## ステップ2: 画面録画（15分・台本を読みながら操作するだけ）

App Review は「権限を実際に使う画面」の録画が要る。**全自動cronの裏側ではなく、人が確認して送る前段のUI**を見せるのがコツ（全自動ボットは却下されやすい）。録画用UIは作成済み。

### 起動
ターミナルで:
```
cd skin && python3 skin_reply_review_ui.py --demo
```
ブラウザで開く:
```
http://127.0.0.1:8765
```

### 録画する操作（この順番で。字幕は任意だが入れると通りやすい）
1. 画面を録画開始（Windowsは `Win+G` のゲームバー、またはOBS）。
2. **キーワード入力 → 検索**: 検索欄に `腸活` と入れて検索。
   - 字幕例:「特定キーワードで関連する公開投稿を検索します」
3. **検索結果の一覧表示**: 投稿本文・著者・日時が並ぶ様子を3秒以上映す。
   - 字幕例:「keyword_searchで取得した公開投稿を一覧表示（read目的）」
4. **1件を選んで返信**: 関連性を確認 → 返信文を確認 → 送信ボタン、まで手動で見せる。
   - 字幕例:「運用者が関連性を確認した上で返信します（無差別送信ではありません）」
5. **スパム抑制の説明**: 最後に字幕で「1日◯件まで／同一ユーザー1日1件／送信間隔ランダム／定型文連投禁止」。
6. 録画停止。mp4で保存。

> 動画は30秒〜2分でよい。きれいさより「検索→一覧→人が選んで送信」の流れが見えることが重要。

---

## ステップ3: 申請フォーム提出（20分・貼り付け文あり）

Meta開発者コンソール → **RoninWordsアプリ（1173361818193107）** → **App Review → Permissions and Features** →
`threads_keyword_search` の **Advanced Access** を Request。

### 「How will your app use this permission?」に貼る（日本語）
```
本アプリは、スキンケア／インナーケア領域のコンテンツ運用を支援する社内ツールです。
threads_keyword_search を用いて「腸活」「肌荒れ」「インナーケア」等の特定キーワードに
関連する公開投稿を収集し、運用者がテーマとの関連性を確認した上で、
有益な情報提供を目的とした返信を行います。
無差別な送信を防ぐため、1日あたりの返信上限・同一ユーザーへの上限・
送信間隔のランダム化・定型文の連続使用禁止を実装しています。
```

### 英語併記（その下に貼る）
```
This app is an internal tool that supports content operations in the
skincare / inner-care space. Using threads_keyword_search, it collects
public posts related to specific keywords (e.g. gut health, skin troubles,
inner care). An operator reviews topical relevance before any reply is sent,
with the goal of providing helpful information. To prevent indiscriminate
sending, the tool enforces a daily reply cap, a per-author cap, randomized
send intervals, and a no-repeat rule for templated text.
```

### フォームの他の欄
- [ ] スクリーンキャスト動画（ステップ2のmp4）をアップロード
- [ ] プライバシーポリシーURL（ステップ0）
- [ ] テストユーザー手順（下を貼る）:
```
1. Run: cd skin && python3 skin_reply_review_ui.py --demo
2. Open http://127.0.0.1:8765
3. Enter a keyword (e.g. "腸活") and press Search.
4. The app lists public posts via keyword_search.
5. Select one post, review the suggested reply, and send.
```
- [ ] 提出

---

## ステップ4: ビジネス認証（求められたら・数日）

審査の過程で Business Verification を求められることがある。個人事業/個人の確認書類を提出 → 数日。求められなければスキップ。

---

## ステップ5: 承認後の本稼働（承認メールが来てから・15分）

1. **トークン再発行**（`threads_keyword_search` 込み）: Meta開発者コンソールでアクセストークンを再生成。
2. **`.env` と GitHub Secret を更新**:
   - ローカル `.env` の `THREADS_ACCESS_TOKEN` を新トークンに差し替え
   - GitHub Secret も更新:
```
gh secret set THREADS_ACCESS_TOKEN -R kmkn0523-cell/kenta-learning
```
3. **権限が付いたか確認**（500エラーが消え200になればOK）:
```
cd skin && python3 -c "import os;from dotenv import load_dotenv;load_dotenv('../.env');import requests;print(requests.get('https://graph.threads.net/v1.0/keyword_search',params={'q':'腸活','search_type':'RECENT','fields':'id','access_token':os.environ['THREADS_ACCESS_TOKEN']}).status_code)"
```
4. **手動テスト**（1回だけ動かして誤爆が無いか確認）:
```
gh workflow run skin_threads_reply_engine.yml -R kmkn0523-cell/kenta-learning
```
   → Actionsのログで「返信 N/M → @誰」を確認。
5. **本稼働ON**:
```
gh variable set SKIN_REPLY_ENGINE_ENABLED --body true -R kmkn0523-cell/kenta-learning
```
   → 以降は1日6回のcronで自動。日次上限10件（控えめ）で開始。数日様子を見て安全なら `skin_reply_engine_config.json` の `daily_cap` を段階的に上げる。

---

## もし審査が重い／却下されたら（代替ルート）

「他人投稿の自動返信」は審査が重い。通過が難しい場合は keyword_search を使わず、
`skin_reply_hunter.py` を**運用者の手動補助**に使う／観測対象アカウント（`skin_account_targets.json`）への手動リプ運用に切り替える選択肢がある。
その場合は「自動」ではなくなるが、reachを増やす目的は達成できる。
