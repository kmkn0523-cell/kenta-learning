# note.com 自動投稿用クッキーのセットアップ

note.com には公式APIが無いため、ブラウザに保存されている**セッションクッキー**を GitHub Actions に渡してログイン状態を再現します。
この手順書では、`_note_session_v5` クッキーを取得して GitHub Secrets に登録するまでの流れを書きます。

---

## 1. クッキーの寿命について

- `_note_session_v5` の有効期限は **約30日**（noteの仕様）
- 失効すると自動投稿が「ログイン失敗」で止まる
- メール通知で失敗が届いたら、再取得して Secrets を更新する

---

## 2. クッキー取得手順（Chrome / Brave 共通）

### ステップ1: note.com にログインする

PCのブラウザで `https://note.com/` を開き、いつもの skin アカウントでログインしておく。

### ステップ2: デベロッパーツールを開く

- Windows: `F12` キー または `Ctrl + Shift + I`
- Mac: `Cmd + Option + I`

### ステップ3: 「Application」タブを開く

上部タブから `Application`（日本語版は「アプリケーション」）を選ぶ。

### ステップ4: 左サイドバーから Cookies → https://note.com を開く

左側ツリーから:

```
Storage
  └─ Cookies
        └─ https://note.com
```

### ステップ5: `_note_session_v5` を探してコピー

クッキー一覧の中から **Name 列が `_note_session_v5`** の行を見つける。
その行の **Value 列の文字列**（300文字くらいの長い文字列）を全選択してコピーする。

メモ:
- ダブルクリックで全選択できる
- 末尾の改行・空白が混ざらないように注意

---

## 3. GitHub Secrets に登録する

### ステップ1: リポジトリのSettingsを開く

ブラウザで以下を開く:

```
https://github.com/kmkn0523-cell/kenta-learning/settings/secrets/actions
```

### ステップ2: 「New repository secret」を押す

右上の緑ボタン `New repository secret` をクリック。

### ステップ3: 名前と値を入力する

- Name:

```
NOTE_SESSION_V5
```

- Secret: **手順2でコピーした長い文字列をそのまま貼り付け**

最後に `Add secret` を押す。

### ステップ4: 既存のSecretを更新する場合（2回目以降）

`NOTE_SESSION_V5` 行の右側にある `Update` ボタンを押し、新しい値で上書きする。

---

## 4. 動作確認

GitHub Actions の手動実行で確認する。

```
gh workflow run skin_note_release.yml
```

その後、実行ログを開いて以下を確認:

- `🌐 noteエディタを開いています...` のあと `❌ ログイン失敗` が出ていないか
- `✅ 投稿完了: https://note.com/...` のURLが出ているか
- 投稿完了メールが届くか

失敗時はアーティファクト `note-screenshots` をダウンロードして `error_login_failed.png` を確認する。

---

## 5. 失敗パターンとリカバリー

| 症状 | 原因 | 対処 |
|------|------|------|
| `❌ ログイン失敗: クッキー期限切れの可能性` | `_note_session_v5` の有効期限切れ（約30日） | 手順2〜3を再実行 |
| `❌ NOTE_SESSION_V5 環境変数が設定されていません` | GitHub Secrets未登録 | 手順3を実行 |
| `タイトル入力欄が見つかりません` | note.comのUI変更 | `post_to_note.py` のセレクタを修正 |
| `カバー画像アップロード失敗` | LP画像パスが間違い or note.comのアップロードUI変更 | `note_lp_map.json` とスクショを確認 |

---

## 6. クッキー流出時の対応

万が一 `_note_session_v5` の値が外部に漏れた場合:

1. note.com にPCブラウザでログインする
2. 設定 → セキュリティ → 「他のセッションをすべてログアウト」を実行
3. 改めて手順2〜3でクッキーを取り直して Secrets を更新

これで古いクッキーは無効化される。
