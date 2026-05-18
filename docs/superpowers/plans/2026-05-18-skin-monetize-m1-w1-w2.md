# skin マネタイズ M1 Week 1〜2 実装計画（土台再構築）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** skin アカウントの「読まれる前提」を整える土台2週間。プロフィール再設計・固定ポスト・ヘッダー・観測対象10アカウント・Instagram insights 権限の5本を完了し、Week 2 から能動的リプ運用を開始できる状態にする。

**Architecture:** 既存テンプレ（`skin/skin_playbook_3month.md` STEP 1-3）の再利用が中核。コード新規作成はゼロ。成果物は文章ファイル・画像・JSON設定・外部サービス設定の4種類。各タスクは独立して完了でき、順序は緩く守れば良い（外部依存があるタスクのみ厳格な順序）。

**Tech Stack:** Markdown（文章成果物）、JSON（設定）、Canva（ヘッダー画像）、Facebook Developer Console（Instagram 権限）、Threads / Instagram の公式アプリ（プロフィール反映）

**期間:** 2026/05/18（月）〜 2026/05/31（日）

**関連スペック:** `docs/superpowers/specs/2026-05-18-skin-monetize-roadmap-design.md`

---

## File Structure

| パス | 種別 | 責務 |
|---|---|---|
| `skin/profile/profile_v2.md` | 新規 | プロフィール本文・表示名・固定ポスト本文の確定版。手で SNS にコピペする原本 |
| `skin/profile/header_image_v2.png` | 新規 | ヘッダー画像（Canva 出力）|
| `skin/skin_account_targets.json` | 新規 | 観測・リプ対象10アカウントのリスト（URL・テーマ・観測開始日）|
| `skin/skin_daily_log.md` | 新規 | 毎日のリプ件数・投稿数・気づきを記録する単純なログファイル |
| `skin/skin_reply_helper.py` | 既存（参照のみ）| 既存のリプ補助スクリプト。Week 2 のリプ運用で使用 |
| `skin/skin_threads_posts.json` | 既存（参照のみ）| Week 2 で手動追加投稿を出すときに参照 |
| `TODO.md` | 既存（更新）| 完了タスクのチェック更新 |

---

## Task 1: プロフィール文・表示名・固定ポストの確定（Week 1 Day 1）

**Files:**
- Create: `skin/profile/profile_v2.md`
- Reference: `skin/skin_playbook_3month.md`（STEP 1-2 のテンプレ）

**完了基準:** Threads と Instagram にコピペ可能な「表示名」「自己紹介4行」「固定ポスト本文」の3点が、1つのファイルに揃っている。

- [ ] **Step 1: 既存テンプレを確認する**

Run: `Read skin/skin_playbook_3month.md` の STEP 1-2（プロフィール文・固定ポストのテンプレ）

確認する点:
- 4行構成（1.何者か+実績／2.発信内容／3.信頼の裏付け／4.導線）
- 固定ポストのテンプレ（10年悩んだ・美容200万・スキンケアを減らす）

- [ ] **Step 2: ファイルを作る**

Create `skin/profile/profile_v2.md` with:

```markdown
# skin プロフィール v2（2026-05-18 確定版）

## 表示名（Threads / Instagram 共通）

ハダキ | 大人ニキビを内側から治す

> 補足: 「ハダキ」はジャンル＋呼びやすさで仮置き。本人の好みで上書き可。

## 自己紹介（4行構成・250文字以内）

10年の大人ニキビ・慢性肌荒れを内側から克服／美容に200万使った失敗体験者

外側ケアで治らなかった人に「本当に効いた "食事・腸・睡眠" の整え方」を毎日投稿

医師ではありません。あくまで体験ベースの発信です

noteに全工程をまとめました → 固定ポスト

## 固定ポスト本文（Threads）

はじめまして。

10年以上、大人ニキビと慢性肌荒れに悩みました。
美容に使った総額は200万円を超えました。

高級化粧品、美容皮膚科、SNSで話題の成分、レーザー、エステ。
どれも一時的で、根本は変わりませんでした。

変わり始めたのは、
スキンケアを減らして、
食事・腸・睡眠を整え始めてからです。

このアカウントでは、
同じ遠回りをしてほしくない人に向けて、
「内側から肌を整える方法」を発信しています。

医師ではありません。
一人の当事者が試して効いたことを、
誠実に書いていくだけです。

▼ 全工程をまとめたnoteはこちら
（現在準備中・2026年8月公開予定）

## 固定ポスト本文（Instagram キャプション・短縮版）

10年悩んだ大人ニキビ。
美容に200万使って気づいたのは、
肌は外側ではなく内側で変わるということ。

このアカウントでは、
体験ベースで「食事・腸・睡眠」の整え方を発信します。

▼ 詳しい全工程は note にまとめ中（2026年8月公開予定）
プロフィールリンクから飛べます
```

- [ ] **Step 3: 内容を自分の言葉で見直す**

「ハダキ」を別の呼び名にしたい場合、または200万→100万など実態に合わせる場合は、この時点で書き換える。

判断基準:
- 嘘の数字は書かない（誇張も含む）
- ペルソナ（10年悩んだ・美容に高額投資）の軸は崩さない
- 「医師ではない」の免責は必ず残す

- [ ] **Step 4: Threads アプリで反映**

スマホの Threads アプリで:
1. プロフィール → 編集
2. 表示名を上書き
3. 自己紹介4行を貼り付け
4. 保存

確認: アプリ上で改行が崩れていないか目視

- [ ] **Step 5: Instagram アプリで反映**

スマホの Instagram アプリで:
1. プロフィール → プロフィールを編集
2. 名前を上書き
3. 自己紹介4行を貼り付け（150文字制限あり、必要なら省略）
4. 保存

- [ ] **Step 6: 固定ポストを投稿（Threads）**

Threads アプリで固定ポスト本文を投稿 → 投稿を長押し → 「ピン留め」

- [ ] **Step 7: コミット**

```bash
git add skin/profile/profile_v2.md
git commit -m "skin プロフィール v2 確定（表示名・自己紹介・固定ポスト）"
```

---

## Task 2: ヘッダー画像の作成（Week 1 Day 1〜2）

**Files:**
- Create: `skin/profile/header_image_v2.png`

**完了基準:** Threads / Instagram にアップロード可能な解像度のヘッダー画像が `skin/profile/header_image_v2.png` に保存されている。

- [ ] **Step 1: Canva のテンプレを選ぶ**

Canva（無料プラン）にログイン:
- URL: https://www.canva.com/
- テンプレ検索: "Twitter ヘッダー" or "SNS バナー"
- 黒地ベースのシンプルなテンプレを選ぶ

サイズ:
- Threads: 1080×270 px 推奨
- Instagram: 1080×1080 px のプロフィール用画像で代用も可（ヘッダー機能はないため）

- [ ] **Step 2: テキストを差し替える**

メインテキスト:
```
スキンケアでは、治らない。
```

サブテキスト（中央下・小さく）:
```
大人ニキビと慢性肌荒れの内側改善
／ 200万円の失敗で辿り着いた答え
```

フォント: ゴシック系・太字（Noto Sans JP Bold が無難）

- [ ] **Step 3: 画像を書き出す**

Canva の「共有」→「ダウンロード」→ PNG → 推奨サイズ

保存先（WSL から見えるパス）:
- Windows のダウンロードフォルダ経由でWSLにコピー
- 例: `cp /mnt/c/Users/kenta\ kamijyo/Downloads/skin_header.png /home/kenta_kamijyo/skin/profile/header_image_v2.png`

- [ ] **Step 4: ファイル存在確認**

```bash
ls -lh skin/profile/header_image_v2.png
```

期待: ファイルサイズが 50KB 以上（小さすぎたら解像度を確認）

- [ ] **Step 5: Threads / Instagram に反映**

スマホアプリで:
- Threads → プロフィール編集 → ヘッダー画像を変更
- Instagram → 投稿として固定（プロフィール最上部に表示）

- [ ] **Step 6: コミット**

```bash
git add skin/profile/header_image_v2.png
git commit -m "skin ヘッダー画像 v2 追加（スキンケアでは治らないコピー）"
```

---

## Task 3: 観測・リプ対象10アカウントのリスト化（Week 1 Day 2〜3）

**Files:**
- Create: `skin/skin_account_targets.json`

**完了基準:** Threads 上で「肌荒れ・大人ニキビ・腸活・健康」ジャンルの活動的アカウント10件のリストが JSON に揃っている。

- [ ] **Step 1: Threads アプリで候補を探す**

検索キーワード（順に試す）:
- 肌荒れ
- 大人ニキビ
- 腸活
- 美肌
- インナーケア
- 食生活 肌
- 睡眠 肌

各キーワードで上位投稿者を見て、以下の条件を満たすアカウントをメモ:
- フォロワー 500〜50,000人
- 直近1週間以内に投稿あり
- 似たジャンル（肌・腸・睡眠・食事のいずれか）
- 顔出しの有無は問わない
- 商品アカウント（化粧品ブランドなど）は除外

10アカウント揃うまで続ける。

- [ ] **Step 2: JSONファイルを作る**

Create `skin/skin_account_targets.json`:

```json
{
  "version": "1.0",
  "created_at": "2026-05-18",
  "purpose": "Threads の能動アクション（リプ・コメント）対象。週次で見直す。",
  "review_cycle": "weekly",
  "targets": [
    {
      "handle": "@xxxxxx",
      "url": "https://www.threads.net/@xxxxxx",
      "theme": "肌荒れ全般",
      "follower_estimate": 5000,
      "added_at": "2026-05-18",
      "notes": "投稿頻度高い・体験談ベース・絡みやすい"
    }
  ]
}
```

10件分の `targets` 配列を埋める。`handle` `url` `theme` `follower_estimate` `notes` を必ず書く。

- [ ] **Step 3: JSON の文法チェック**

```bash
python3 -c "import json; json.load(open('skin/skin_account_targets.json')); print('OK')"
```

期待: `OK`

- [ ] **Step 4: コミット**

```bash
git add skin/skin_account_targets.json
git commit -m "skin 観測対象10アカウントリスト追加（リプ運用の起点）"
```

---

## Task 4: Instagram insights 権限の追加（Week 1 Day 3〜4）

**Files:** なし（外部設定）
**完了基準:** Facebook Developer Console で `instagram_manage_insights` 権限が追加され、トークンが再発行され、`.env` の `SKIN_INSTAGRAM_ACCESS_TOKEN` が更新済み。再発行後の Instagram insights エンドポイントが OAuthException を返さない。

**前提:** [[project_instagram_image_todo]] の memory に記載されている未解決課題。Batch 1 の保存数測定に必須。

- [ ] **Step 1: Facebook Developer Console にログイン**

URL: https://developers.facebook.com/apps/

skin 用のアプリを選択。

- [ ] **Step 2: アプリの「アプリレビュー」→「権限と機能」を開く**

検索: `instagram_manage_insights`

「リクエスト」をクリック → 必要事項を埋める:
- アプリの使用方法: 「自分が運営する Instagram ビジネスアカウントの投稿パフォーマンス（保存数・リーチ・インプレッション）を取得し、コンテンツ改善に使用」
- 動作確認手順: ダミー動画でデモを撮るか、コードのスクリーンショット

- [ ] **Step 3: 権限承認を待つ（即時 or 数日）**

ビジネス認証済みのアプリなら即時、未認証なら数営業日。

承認待ちの間に Task 5 に進む。

- [ ] **Step 4: アクセストークンを再発行**

承認後:
1. 「ツール」→「グラフAPIエクスプローラー」
2. アプリを選択、ユーザートークンを生成（権限に `instagram_manage_insights` を含める）
3. 短期トークンを長期トークンに変換（60日）

トークン変換コマンド:
```bash
curl -G "https://graph.facebook.com/v18.0/oauth/access_token" \
  -d "grant_type=fb_exchange_token" \
  -d "client_id=YOUR_APP_ID" \
  -d "client_secret=YOUR_APP_SECRET" \
  -d "fb_exchange_token=SHORT_LIVED_TOKEN"
```

- [ ] **Step 5: `.env` を更新**

`.env` の `SKIN_INSTAGRAM_ACCESS_TOKEN` を新トークンで置換。

⚠️ CLAUDE.md ルール: `.env` を触るときは承認が必要。Kenta 本人が手動で書き換えること。

- [ ] **Step 6: GitHub Secrets を更新**

リポジトリの Settings → Secrets and variables → Actions:
- `SKIN_INSTAGRAM_ACCESS_TOKEN` を新トークンで上書き

- [ ] **Step 7: 動作確認**

```bash
python3 -c "
import os, requests
token = os.environ['SKIN_INSTAGRAM_ACCESS_TOKEN']
ig_id = os.environ['SKIN_INSTAGRAM_BUSINESS_ID']
r = requests.get(f'https://graph.facebook.com/v18.0/{ig_id}/insights',
                 params={'metric': 'impressions,reach,saved', 'period': 'day', 'access_token': token})
print(r.status_code, r.json())
"
```

期待: ステータス200、エラーなし

- [ ] **Step 8: コミット（環境設定変更の記録）**

`.env` はコミットしない。記録だけ:

```bash
git commit --allow-empty -m "Instagram insights 権限追加完了（手動設定）"
```

⚠️ Step 1〜7 完了後にこのコミットをすること。承認が下りないうちにダミーコミットを打たない。

---

## Task 5: 日次ログファイルの雛形作成（Week 1 Day 4）

**Files:**
- Create: `skin/skin_daily_log.md`

**完了基準:** 毎日3分でリプ件数・投稿数を追記できる雛形ファイルが存在する。

- [ ] **Step 1: 雛形ファイルを作る**

Create `skin/skin_daily_log.md`:

```markdown
# skin 日次ログ

毎日（夜）に3分でメモ。数字は週次・月次で集計するので、ここでは生データだけ。

## 記入ルール
- 日付・曜日
- リプ件数（その日に他人の投稿につけたリプの数）
- 手動投稿数（自動投稿は数えない）
- 気づき（伸びた投稿・反応の良かったリプ・違和感など、1〜3行）

---

## 2026-05-18（月）
- リプ件数: 0
- 手動投稿数: 0
- 気づき: 土台再構築週スタート。プロフィール再設計から。

## 2026-05-19（火）
- リプ件数:
- 手動投稿数:
- 気づき:

## 2026-05-20（水）
- リプ件数:
- 手動投稿数:
- 気づき:

## 2026-05-21（木）
- リプ件数:
- 手動投稿数:
- 気づき:

## 2026-05-22（金）
- リプ件数:
- 手動投稿数:
- 気づき:

## 2026-05-23（土）
- リプ件数:
- 手動投稿数:
- 気づき:

## 2026-05-24（日）
- リプ件数:
- 手動投稿数:
- 気づき:

## 週次サマリー（2026-05-24 日曜夜に記入）
- 合計リプ件数:
- 合計手動投稿数:
- 一番伸びた投稿:
- 来週の改善1点:
```

- [ ] **Step 2: コミット**

```bash
git add skin/skin_daily_log.md
git commit -m "skin 日次ログの雛形追加（Week 1〜2分）"
```

---

## Task 6: Week 2 — 毎日リプ10件の運用開始（5/25〜5/31）

**Files:**
- Update: `skin/skin_daily_log.md`（毎日追記）
- Reference: `skin/skin_account_targets.json`（リプ先）
- Reference: `skin/skin_reply_helper.py`（既存のリプ補助スクリプト）

**完了基準:** 5/25〜5/31 の7日間で合計70件以上のリプを実施し、`skin_daily_log.md` に件数が記録されている。

- [ ] **Step 1: 既存の skin_reply_helper.py を確認**

Run: `Read skin/skin_reply_helper.py`

このスクリプトが何をしているか把握する。リプテンプレ生成・送信補助のどれかを担っているはず。

- [ ] **Step 2: 毎日のリプ運用（Day 1: 5/25）**

朝 or 夜に30分:
1. `skin_account_targets.json` の10アカウントを Threads アプリで開く
2. 各アカウントの直近投稿を読み、自分の体験に紐づく1〜2件にリプをつける
3. NG例:「いいですね！」「勉強になります！」（無価値）
4. OK例:「自分も昔は高級化粧水に月3万かけてましたが、朝食抜きに変えたら2ヶ月で肌が落ち着きました」（自分の体験＋情報）
5. 1日10件をノルマに

- [ ] **Step 3: ログに記録**

夜に `skin/skin_daily_log.md` の今日の欄に追記:
```markdown
## 2026-05-25（月）
- リプ件数: 10
- 手動投稿数: 0
- 気づき: アカウントAの腸活投稿に長文リプ。返信あり。
```

- [ ] **Step 4: Day 2〜7 を同じパターンで反復**

5/26〜5/31 まで毎日10件＋記録。

- [ ] **Step 5: 5/31 夜に週次サマリーを記入**

`skin/skin_daily_log.md` の「週次サマリー」欄を埋める:
- 合計リプ件数（目標: 70件以上）
- 合計手動投稿数
- 一番伸びた投稿
- 来週の改善1点

- [ ] **Step 6: 週次コミット**

```bash
git add skin/skin_daily_log.md
git commit -m "skin Week 2 リプ運用ログ（5/25〜5/31）"
```

---

## Task 7: A/B Batch 1 中間レポート確認（5/31）

**Files:**
- Update: `TODO.md`（2026/05/31 のチェックを更新）
- Reference: `skin/skin_ab_report.py`

**完了基準:** Batch 1 の中間レポートが生成され、結果を `skin/skin_improvement_note.md` に追記している。

- [ ] **Step 1: 中間レポートを実行**

```bash
python3 skin/skin_ab_report.py --batch 1
```

期待: テーマ1〜20 の A/B 勝率・engagement_score の差分が出力される。

- [ ] **Step 2: 結果を確認**

出力で見るポイント:
- A/B のどちらが優勢か（半数以上で B 優勢なら B 寄りのリライト方針継続）
- 最も伸びたテーマと最も伸びなかったテーマ
- engagement_score が一桁台のままなら、リプ運用の効果がまだ出ていないので焦らない

- [ ] **Step 3: 結果を skin_improvement_note.md に追記**

Run: `Read skin/skin_improvement_note.md` で既存内容を確認後、Edit で末尾に以下を追記:

```markdown

## 2026-05-31 Batch 1 中間レポート所感

- 出力サマリ（数値はコピペ）
- 優勢パターンの傾向（B 寄り or 拮抗）
- M2 の Batch 2 リライト方針への反映ポイント1〜2点
```

- [ ] **Step 4: TODO.md の対応行を更新**

`TODO.md` を編集:
- `- [ ] 2026/05/31: Batch 1 中間レポート確認（python3 skin/skin_ab_report.py --batch 1）`
- → `- [x] 2026/05/31: Batch 1 中間レポート確認（結果は skin_improvement_note.md）`

- [ ] **Step 5: コミット**

```bash
git add skin/skin_improvement_note.md TODO.md
git commit -m "Batch 1 中間レポート完了・所感を記録"
```

---

## Task 8: Instagram Batch 1 初動チェック（5/19〜5/24 のうちいつでも）

**Files:**
- Reference: `skin/skin_instagram_analytics.json`
- Reference: `skin/skin_instagram_report.py`

**完了基準:** v2 カルーセル（8枚）が予定通り投稿されており、Instagram アプリ上で目視確認できている。

- [ ] **Step 1: Instagram アプリで投稿確認**

https://www.instagram.com/skin_reset_jp/ を開く:
- 最新投稿が theme01 v2（8枚カルーセル）か
- キャプションが v2 フォーマットか（3軸フック＋4軸CTA＋3層ハッシュタグ）
- 画像が崩れていないか

- [ ] **Step 2: 異常があれば記録**

異常例:
- 投稿が止まっている → GitHub Actions のログを確認
- 画像が崩れている → `skin_instagram_image_gen_v4.py` のフォントパス確認
- キャプションが旧版 → `carousel_content.json` の version 確認

異常があれば `skin/skin_improvement_note.md` に追記し、必要に応じて修正タスクを別途立てる。

- [ ] **Step 3: 正常なら TODO.md にチェック**

`TODO.md` を編集:
- Batch 1 初動確認の項目があれば `[x]` に
- なければスキップ

- [ ] **Step 4: コミット（変更があった場合のみ）**

```bash
git add TODO.md skin/skin_improvement_note.md
git commit -m "Instagram Batch 1 初動確認: 正常稼働"
```

---

## Week 1〜2 完了の判定

5/31 夜に以下を確認:

- [ ] プロフィール文・表示名・固定ポストが Threads / Instagram 両方に反映されている
- [ ] ヘッダー画像が反映されている
- [ ] `skin/skin_account_targets.json` に10件のアカウントが登録されている
- [ ] `skin/skin_daily_log.md` に5/25〜5/31の7日分の記録がある
- [ ] Instagram `instagram_manage_insights` 権限が承認され、insights API が動く
- [ ] Batch 1 中間レポートが完了し、`skin_improvement_note.md` に所感が記録されている

全部 ✅ なら M1 Week 3 へ進む（型探索＋リプ件数を 1日20件に増やす）。

5項目以上 ✅ なら合格。3項目以下なら Week 1〜2 を延長して埋める。

---

## Self-Review

### Spec 対応チェック
- 収益構造（収益源3本足）: M1 では発生しない。Task で触れないのは正しい
- 半年フェーズ分割の M1: Task 1〜8 で土台再構築の主要 5 アクションをカバー ✅
- KPI / レビューサイクル: Task 5（日次ログ雛形）と Task 6（週次サマリー）で実装 ✅
- 既存資産活用: `skin_playbook_3month.md`（Task 1）、`skin_ab_report.py`（Task 7）、`skin_instagram_*.py`（Task 8）を参照 ✅
- 新規作成物 #1（プロフィール）: Task 1 ✅
- 新規作成物 #2（ヘッダー画像）: Task 2 ✅
- 新規作成物 #3（10アカウントリスト）: Task 3 ✅
- 新規作成物 #10（Instagram insights）: Task 4 ✅
- 撤退ライン: M1 末（6/17）の評価。本 Week 1〜2 計画の終了時点ではまだ早い。M1 Week 3〜4 計画に含める

### Placeholder スキャン
- "TBD" / "TODO" / "fill in details": なし
- "appropriate error handling": なし
- 「Task N と同じ」: なし（具体的なコードと手順をすべて記載）

### Type Consistency
- `skin/skin_account_targets.json` のキー名（`handle` `url` `theme` `follower_estimate` `notes`）は Task 3 で定義され、Task 6 で参照されるが、Task 6 では JSON のキー名に依存していない（人間が見て使うだけ）→ 問題なし
- `skin/skin_daily_log.md` の日付フォーマット（`YYYY-MM-DD（曜）`）は Task 5 で雛形を作り Task 6 で踏襲、整合 ✅

### スコープ
- M1 Week 1〜2 の2週間に絞っている。M1 Week 3〜4 と M2 以降は別計画で立てる ✅
