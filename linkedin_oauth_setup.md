# LinkedIn OAuth 2.0 セットアップガイド for @RoninWords

このドキュメントは、LinkedIn APIを使って@RoninWordsから自動投稿するための初期設定手順を説明します。

**このタスクについて**
- LinkedIn APIを自動投稿に必要な「認証情報」を取得するための初期設定です
- Threadsと同じように、アクセストークンを使って自動投稿できるようになります
- トークンは60日間有効です（期限切れ前にリマインドが来ます）

---

## Step 1: LinkedIn Developer Console でアプリを登録

### 1-1 LinkedIn Developer Consoleにアクセス
ブラウザで以下のURLを開いてください:
```
https://www.linkedin.com/developers/apps
```

### 1-2 ログイン
- LinkedInアカウントでログインします
- @RoninWordsと同じLinkedInアカウント（Kenta Kamijyo個人アカウント）を使用します

### 1-3 新しいアプリを作成
1. 「Create app」ボタンをクリック
2. 以下の情報を入力:
   - **App name**: `RoninWords Automation`
   - **LinkedIn Page**: （@RoninWordsがLinkedInページを持つ場合は選択。個人アカウントの場合は空白でOK）
   - **App logo**: お好みで設定（スキップしてもOK）
   - 利用規約に同意してチェック
3. 「Create app」をクリック

### 1-4 認証情報を保存
アプリ作成後、以下の画面に進みます:
- **Client ID**: コピーして記録する
- **Client Secret**: コピーして記録する（絶対に誰かに教えないこと！）

例:
```
Client ID:     xxxxxxxxxxxxxxxx
Client Secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**この情報は Step 3 で .env ファイルに追加します。**

---

## Step 2: API 製品を有効化（重要）

このステップをスキップすると、後で投稿ができなくなります。

### 2-1 Products タブを開く
作成したアプリのページで、「**Products**」タブをクリック

### 2-2 Share on LinkedIn を有効化（投稿用）
1. 検索欄に `Share on LinkedIn` と入力
2. 「Share on LinkedIn」を見つけてクリック
3. 「Request access」をクリック
4. 説明が出たら内容を確認して「Request」をクリック

### 2-3 Sign In with LinkedIn を有効化（認証用）
1. 同じProducts タブで、検索欄に `Sign In with LinkedIn` と入力
2. 「Sign In with LinkedIn using OpenID Connect」を見つけてクリック
3. 「Request access」をクリック
4. 「Request」をクリック

### 2-4 承認を待つ
- LinkedInからメールが来ます（通常24時間以内）
- メール内のリンクをクリックして「Approve」を選択
- アプリのProducts タブで状態が「Approved」に変わるのを確認

**この間、他のStepは進めてOKです。**

---

## Step 3: .env ファイルに認証情報を追加

### 3-1 .env ファイルを開く
以下のファイルをテキストエディタで開きます:
```
/home/kenta_kamijyo/.env
```

### 3-2 LinkedIn認証情報を追加
ファイルの最後に以下を追加します（Step 1で記録したClient IDとClient Secretを入力）:

```env
# LinkedIn OAuth 2.0 (RoninWords 自動投稿用)
LINKEDIN_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxx
LINKEDIN_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LINKEDIN_REDIRECT_URI=http://localhost:8000/callback
```

**注意**: 
- `Client ID` と `Client Secret` をコピー&ペーストするときは、スペースを削除してください
- このファイルは `.gitignore` に登録されているため、GitHubにアップロードされません（安全です）

### 3-3 ファイルを保存
変更を保存します。

---

## Step 4: OAuth 2.0 認可コードを取得（初回認証）

このステップで、LinkedInに「このアプリは私のアカウントで投稿する権限をください」と許可します。

### 4-1 ブラウザで以下のURLを開く
Step 3で追加した `LINKEDIN_CLIENT_ID` を以下のURLに入れて、ブラウザで開きます:

```
https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=LINKEDIN_CLIENT_IDをここに貼り付け&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fcallback&scope=w_member_social
```

**例** (実際のIDは異なります):
```
https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=1234567890abc&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fcallback&scope=w_member_social
```

### 4-2 LinkedInで許可する
- LinkedInログインページが出ます（すでにログイン済みの場合はスキップ）
- 「Authorize」ボタンをクリック
- 権限の説明が出ます。内容を確認して「Authorize」をクリック

### 4-3 コールバックから認可コードを取得
ブラウザのアドレスバーが以下のように変わります:
```
http://localhost:8000/callback?code=XXXXXXXXXXXXXXXX&state=XXXXXXX
```

**URLの `code=` の後ろの部分（XXXXXXXXXXXXXXXX）をコピーして記録してください。** この部分が「認可コード」です。

---

## Step 5: アクセストークンを取得（コマンド実行）

ここからは、ターミナルで以下のコマンドを実行します。Windowsの場合はWSL2（Ubuntu）のターミナルを使用してください。

### 5-1 ターミナルを開く

### 5-2 以下のコマンドを実行
Step 3で追加した `LINKEDIN_CLIENT_ID`、`LINKEDIN_CLIENT_SECRET` と、Step 4で取得した `認可コード` を使います:

```bash
curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code=STEP4で取得した認可コード&client_id=LINKEDIN_CLIENT_ID&client_secret=LINKEDIN_CLIENT_SECRET&redirect_uri=http://localhost:8000/callback"
```

**例** (実際の値は異なります):
```bash
curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code=AQaB1C2DeFgHi3jKlMnOpQrStuVwXyZ&client_id=1234567890abc&client_secret=abcdefghijk1234567890&redirect_uri=http://localhost:8000/callback"
```

### 5-3 結果から必要な情報を抽出
コマンドを実行すると、以下のような JSON が返ります:

```json
{
  "access_token": "AQa1BC2DEfGhIjKlMNopQRstuvWxYZaBcDeFGhIjKlMNopQRstuvWxYZaBcDeFGhIjKlMNopQRstuvWxYZ",
  "expires_in": 5184000,
  "refresh_token": "AQa1BC2DEfGhIjKlMNopQRstuvWxYZaBcDeFGhIjKlMNopQRstuvWxYZ",
  "token_type": "Bearer"
}
```

**記録してください:**
- `access_token`: このコードがメインのトークンです
- `expires_in`: 5184000 秒 = 60日間有効という意味です
- `refresh_token`: 期限切れ前に新しいトークンを取得するときに使います

---

## Step 6: LinkedIn ユーザーURNを取得（API呼び出し）

投稿するときに、「どのアカウントで投稿するか」をLinkedInに伝える必要があります。それが「ユーザーURN」です。

### 6-1 以下のコマンドを実行
Step 5で取得した `access_token` を使います:

```bash
curl -X GET https://api.linkedin.com/v2/me \
  -H "Authorization: Bearer アクセストークンをここに貼り付け"
```

**例** (実際のトークンは異なります):
```bash
curl -X GET https://api.linkedin.com/v2/me \
  -H "Authorization: Bearer AQa1BC2DEfGhIjKlMNopQRstuvWxYZaBcDeFGhIjKlMNopQRstuvWxYZ"
```

### 6-2 結果からユーザーURNを抽出
コマンドを実行すると、以下のような JSON が返ります:

```json
{
  "localizedFirstName": "Kenta",
  "localizedLastName": "Kamijyo",
  "id": "1234567890"
}
```

**ここから ユーザーURN を組み立てます:**
- `id` の値（例: 1234567890）を使って:
```
urn:li:person:1234567890
```

この値を記録してください。

---

## Step 7: linkedin/linkedin_config.json を設定

### 7-1 設定ファイルを開く
以下のファイルをテキストエディタで開きます:
```
/home/kenta_kamijyo/linkedin/linkedin_config.json
```

### 7-2 以下の値を入力
- Step 3の `LINKEDIN_CLIENT_ID` → `oauth.client_id`
- Step 3の `LINKEDIN_CLIENT_SECRET` → `oauth.client_secret`
- Step 5で取得した `access_token` → `oauth.access_token`
- Step 5で取得した `refresh_token` → `oauth.refresh_token`
- Step 5の `expires_in` （5184000）で期限を計算して → `oauth.access_token_expires_at`
- Step 6で取得した `urn:li:person:xxxxx` → `profile.person_urn`

**計算方法（期限日時）:**
- expires_in: 5184000 秒 = 60日間
- 今日の日付 + 60日 = 期限日（例: 今日が2026/05/07なら、期限は2026/07/06）

### 7-3 ファイルを保存

例:
```json
{
  "oauth": {
    "client_id": "1234567890abc",
    "client_secret": "abcdefghijk1234567890",
    "redirect_uri": "http://localhost:8000/callback",
    "access_token": "AQa1BC2DEfGhIjKlMNopQRstuvWxYZaBcDeFGhIjKlMNopQRstuvWxYZ",
    "access_token_expires_at": "2026/07/06",
    "refresh_token": "AQa1BC2DEfGhIjKlMNopQRstuvWxYZaBcDeFGhIjKlMNopQRstuvWxYZ"
  },
  "profile": {
    "person_urn": "urn:li:person:1234567890"
  },
  "settings": {
    "auto_translate": false,
    "language": "en"
  }
}
```

---

## Step 8: Gitにコミット

セットアップが完了したら、以下のコマンドを実行してGitにコミットします:

```bash
cd /home/kenta_kamijyo
git add linkedin/linkedin_config.json
git commit -m "feat: add LinkedIn API configuration"
git push
```

---

## トラブルシューティング

### Q: エラーが出ました
A: エラーメッセージを全文コピーして、Claude Codeに貼り付けてください。原因を特定します。

### Q: 「Product が Approved されていない」と言われました
A: Step 2 で「Request access」をクリックしてから、LinkedInからのメール承認まで24時間待ってください。

### Q: アクセストークンが期限切れになったら？
A: `threads_token_renewal.md` と同じやり方で、Step 5 と Step 6 を再度実行します。（詳細は後で文書化します）

### Q: Client Secret が見つかりません
A: LinkedInアプリのページで「Auth」タブをクリックしてください。「Client Secret」が表示されます。

---

## 次のステップ（Task 2）

このセットアップが完了したら、以下を実行します:
- **Task 2**: LinkedIn自動投稿スクリプト（`linkedin_auto_post.py`）の作成
  - Threads と同じように、1日4回自動投稿するPythonスクリプト
  - GitHub Actions で定期実行

---

## 参考リンク
- LinkedIn Developer Console: https://www.linkedin.com/developers/apps
- LinkedIn OAuth Documentation: https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication
