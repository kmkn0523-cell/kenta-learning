# Threadsトークン更新手順（60日ごと）

## 次回期限
**2026/08/24頃**（2026/06/25にリフレッシュ更新済み・60日有効）

## 更新手順（推奨：リフレッシュ方式）
今の長期トークンが有効なうちは、再生成不要でリフレッシュするだけで60日延長できる。
Claude Code に「Threadsトークンをリフレッシュして」と頼めば以下を自動でやる。

```
GET https://graph.threads.net/refresh_access_token?grant_type=th_refresh_token&access_token=（今のトークン）
```

1. `.env` の各トークンでリフレッシュAPIを叩き、新60日トークンを取得
2. `.env` を新トークンに書き換え
3. GitHub Secrets も同様に更新
4. `https://graph.threads.net/v1.0/me` で疎通確認

※ 期限切れ後はリフレッシュ不可。その場合は Meta for Developers でアプリ→Threads→
「Generate access token」で短期トークンを取り、`grant_type=th_exchange_token` で長期変換する。

## 対象アカウント（skinとroninは別トークン）
- skin（肌荒れ・`skin_reset_jp`）: `.env`＝`THREADS_ACCESS_TOKEN` / Secret＝`THREADS_ACCESS_TOKEN`
- @RoninWords（`ronin_words111`）: `.env`＝`RONIN_THREADS_ACCESS_TOKEN` / Secret＝`RONIN_THREADS_ACCESS_TOKEN`

---

# Instagram トークン更新手順（60日ごと）

## 次回期限
**2026/07/07頃**（今回2026/05/09に更新）

## ⚠️ 注意：必ず「長期トークン変換」をすること
Graph API ExplorerのUIで生成したトークンは短期（約2時間）で切れる。
必ず下記の手順で変換すること。

## 更新手順

### Step 1 — 新しい短期トークンを取得
1. https://developers.facebook.com/tools/explorer/ を開く
2. 右上のアプリで「RoninWords (1173361818193107)」を選択
3. 「アクセストークンを生成」→ ユーザートークン
4. 権限にチェック：`instagram_basic` `instagram_content_publish` `pages_show_list` `pages_read_engagement`
5. 生成されたトークンをコピー

### Step 2 — Claude Code に貼るだけ（自動で変換・更新）
Claude Code のチャットに以下を貼る：

```
短期トークン: （Step1でコピーしたもの）
アプリシークレット: （Meta for Developers → RoninWords → 設定 → ベーシック → アプリシークレット → 表示）
```

→ Claude が自動で長期トークン（60日）に変換して `.env` と GitHub Secrets を更新する。

### Step 3 — 動作確認
```bash
gh workflow run ronin_instagram_auto_post.yml
```
→ ✅ 投稿成功 と表示されればOK

## 対象
- @RoninWords Instagram: `INSTAGRAM_ACCESS_TOKEN`
  - アプリID: `1173361818193107`
  - ユーザーID: `17841426221570497`
- skin（肌荒れ）Instagram: `SKIN_INSTAGRAM_ACCESS_TOKEN`
  - アプリID: `1173361818193107`（同じアプリ）
  - ユーザーID: `17841424221734739`
  - ※ skinアカウントでログインした状態でGraph API Explorerを開くこと
