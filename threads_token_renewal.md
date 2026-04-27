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
