# Threadsトークン更新手順（60日ごと）

## 次回期限
**2026/06/26頃**（リマインド予約済み）

## 更新手順
1. Meta for Developers（developers.facebook.com）にログイン
2. アプリ → Threadsアクセストークン → 長期トークン取得
3. `.env` の `THREADS_ACCESS_TOKEN` を新しいトークンに書き換え
4. GitHub の Secrets（Settings → Secrets）も同様に更新

## 対象アカウント
- @RoninWords: `THREADS_ACCESS_TOKEN`
- skin（肌荒れ）: 同じトークンを使用

---

# Instagram トークン更新手順（60日ごと）

## 次回期限
**2026/07/07頃**（今回2026/05/08に更新）

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
