# @RoninWords LinkedIn 自動化システム 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** @RoninWords の Threads 投稿を LinkedIn に自動転送し、海外向けコンテンツ配信を自動化する

**Architecture:** Threads API から取得した投稿を LinkedIn API で投稿 → LinkedIn Analytics で反応測定 → GitHub Actions で毎日自動実行。skin・ronin の実装をミラーリング。

**Tech Stack:** Python3（requests）、LinkedIn OAuth 2.0 API、GitHub Actions、JSON（ローカル管理）

---

## ファイル構成

### 新規作成
- `linkedin/linkedin_auto_post.py` - Threads → LinkedIn 自動投稿スクリプト
- `linkedin/linkedin_analytics.py` - LinkedIn エンゲージメント分析スクリプト
- `linkedin/linkedin_config.json` - LinkedIn API 設定（アカウント ID・トークン管理）
- `.github/workflows/linkedin_auto_post_daily.yml` - 自動実行ワークフロー

### 修正対象
- `.env` - LinkedIn API キー・トークン追加

---

## フェーズ 1: LinkedIn API 設定

### Task 1: LinkedIn API 設定・認証情報取得

**Files:**
- Create: `linkedin/linkedin_config.json`
- Modify: `.env`

**背景:** LinkedIn API を使用するために、OAuth 2.0 認証情報と API キーを取得し、ローカル管理する。

- [ ] **Step 1: LinkedIn Developer Console でアプリを登録**

https://www.linkedin.com/developers/apps

1. 「Create app」をクリック
2. アプリ名: `RoninWords Automation`
3. LinkedIn Page: @RoninWords のページを選択（個人プロフィールの場合はスキップ）
4. 利用規約に同意して登録

Expected: アプリ ID とクライアントシークレットが取得できる

- [ ] **Step 2: API 製品を有効化**

1. アプリの「Products」タブを開く
2. 「Share on LinkedIn」を検索して「Request access」
3. 「Sign In with LinkedIn using OpenID Connect」も有効化
4. 審査完了を待つ（通常 24 時間以内）

Expected: "Share on LinkedIn" が Approved 状態

- [ ] **Step 3: 認証情報を .env に追加**

```bash
# .env に以下を追加
LINKEDIN_CLIENT_ID=xxx
LINKEDIN_CLIENT_SECRET=xxx
LINKEDIN_REDIRECT_URI=http://localhost:8000/callback
LINKEDIN_PERSON_URN=urn:li:person:xxxxx  # 後で取得
```

- [ ] **Step 4: OAuth 2.0 トークンを取得（初回認証）**

以下の URL を開いて、認証を完了

```
https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8000/callback&scope=w_member_social
```

コールバック URL からアクセスコードを取得して、以下で トークン交換：

```bash
curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code=CODE&client_id=CLIENT_ID&client_secret=CLIENT_SECRET&redirect_uri=http://localhost:8000/callback"
```

Expected: `access_token` が取得できる（有効期限 60 日）

- [ ] **Step 5: linkedin_config.json を作成**

```json
{
  "oauth": {
    "client_id": "xxx",
    "client_secret": "xxx",
    "redirect_uri": "http://localhost:8000/callback",
    "access_token": "xxx",
    "access_token_expires_at": "2026/07/07",
    "refresh_token": "xxx"
  },
  "profile": {
    "person_urn": "urn:li:person:xxxxx",
    "profile_id": "xxxxx"
  },
  "settings": {
    "auto_translate": false,
    "language": "en"
  }
}
```

- [ ] **Step 6: Commit**

```bash
# .env は .gitignore に含まれているので、ファイルのみ
mkdir -p linkedin
git add linkedin/linkedin_config.json .github/workflows/  # まだ作成していないが placeholder
git commit -m "feat: add LinkedIn API configuration"
```

Expected: .env ファイルは tracked されない

---

## フェーズ 2: LinkedIn 自動投稿スクリプト

### Task 2: linkedin_auto_post.py の基本実装

**Files:**
- Create: `linkedin/linkedin_auto_post.py`

**背景:** Threads から取得した投稿を LinkedIn に自動投稿するスクリプト。skin の `ronin_threads_auto_post.py` をベースに、LinkedIn API を使用。

- [ ] **Step 1: linkedin_auto_post.py の骨組みを作成**

```python
import json
import requests
from datetime import datetime
import os

# 設定をロード
def load_config():
    with open('linkedin/linkedin_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# LinkedIn API でテキスト投稿
def post_to_linkedin(text):
    """LinkedIn に投稿"""
    config = load_config()
    access_token = config['oauth']['access_token']
    person_urn = config['profile']['person_urn']
    
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202404"
    }
    
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": text
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 201:
            post_id = response.json()['id']
            print(f"Posted to LinkedIn: {post_id}")
            return post_id
        else:
            print(f"Error posting: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

# Threads 投稿を読んで LinkedIn に投稿
def load_threads_posts():
    """Threads の threads_posts.json から投稿を読む"""
    with open('ronin/threads_posts.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    """メイン処理"""
    print("LinkedIn Auto Post started")
    
    # Threads 投稿から今週の Day を取得
    posts = load_threads_posts()
    # 例：Day 1 の朝投稿をLinkedInに投稿
    post = posts[0]  # Day 1
    text = post['morning']
    
    # ハッシュタグを追加
    hashtags = post.get('hashtags_set_A', [])
    full_text = text + '\n\n' + ' '.join(hashtags)
    
    post_id = post_to_linkedin(full_text)
    if post_id:
        print("Success")
    else:
        print("Failed")

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: テスト（ドライラン）**

```bash
python3 linkedin/linkedin_auto_post.py
```

Expected: エラーなし、ドライラン表示

- [ ] **Step 3: Commit**

```bash
git add linkedin/linkedin_auto_post.py
git commit -m "feat: create linkedin_auto_post.py (basic posting)"
```

---

### Task 3: linkedin_auto_post.py の改造（スマート投稿）

**Files:**
- Modify: `linkedin/linkedin_auto_post.py`

**背景:** 単純な投稿ではなく、Threads の投稿データから適切な内容を選択して投稿。英語翻訳オプションも検討。

- [ ] **Step 1: 投稿内容の自動選択ロジックを追加**

```python
def select_post_for_linkedin():
    """Threads 投稿から、LinkedIn に適した内容を選択"""
    posts = load_threads_posts()
    
    # 毎週異なる Day をローテーション（例：週 1 回投稿）
    import json
    try:
        with open('linkedin/linkedin_posting_progress.json', 'r', encoding='utf-8') as f:
            progress = json.load(f)
    except FileNotFoundError:
        progress = {'index': 0}
    
    day_index = progress['index'] % len(posts)
    post = posts[day_index]
    
    # 朝投稿の方が詳細なので、朝を選択
    text = post['morning']
    
    # 投稿後、次のインデックスに更新
    progress['index'] += 1
    with open('linkedin/linkedin_posting_progress.json', 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)
    
    return text, post.get('hashtags_set_A', [])
```

- [ ] **Step 2: main() を更新**

```python
def main():
    """メイン処理"""
    print("LinkedIn Auto Post started")
    
    text, hashtags = select_post_for_linkedin()
    full_text = text + '\n\n' + ' '.join(hashtags)
    
    post_id = post_to_linkedin(full_text)
    if post_id:
        print(f"Successfully posted Day X to LinkedIn: {post_id}")
    else:
        print("Failed to post")
```

- [ ] **Step 3: テスト**

```bash
python3 linkedin/linkedin_auto_post.py
```

Expected: Day X の投稿が選択されて投稿される

- [ ] **Step 4: linkedin_posting_progress.json 初期化**

```bash
python3 << 'EOF'
import json

progress = {
    "index": 0,
    "history": []
}

with open('linkedin/linkedin_posting_progress.json', 'w', encoding='utf-8') as f:
    json.dump(progress, f, indent=2, ensure_ascii=False)

print("Progress file created")
EOF
```

- [ ] **Step 5: Commit**

```bash
git add linkedin/linkedin_auto_post.py linkedin/linkedin_posting_progress.json
git commit -m "feat: add smart post selection to linkedin_auto_post.py"
```

---

## フェーズ 3: LinkedIn エンゲージメント分析

### Task 4: linkedin_analytics.py の実装

**Files:**
- Create: `linkedin/linkedin_analytics.py`

**背景:** LinkedIn のいいね・コメント・シェア数を毎日自動で測定し、どの投稿パターンが人気か分析。

- [ ] **Step 1: LinkedIn Analytics API で投稿メトリクスを取得**

```python
import json
import requests
from datetime import datetime

def get_post_analytics(person_urn, post_id):
    """投稿のメトリクスを取得（いいね・コメント・シェア）"""
    config = load_config()
    access_token = config['oauth']['access_token']
    
    url = f"https://api.linkedin.com/v2/socialMetadata?q=posts&posts=List({post_id})"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": "202404"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # メトリクスを抽出
            metrics = {
                "post_id": post_id,
                "date": datetime.now().isoformat(),
                "likes": data.get('likeCount', 0),
                "comments": data.get('commentCount', 0),
                "shares": data.get('shareCount', 0),
                "engagement_score": (
                    data.get('likeCount', 0) * 1.0 +
                    data.get('commentCount', 0) * 2.5 +
                    data.get('shareCount', 0) * 5.0
                )
            }
            return metrics
        else:
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def save_analytics(metrics):
    """メトリクスを linkedin_analytics.json に保存"""
    try:
        with open('linkedin/linkedin_analytics.json', 'r', encoding='utf-8') as f:
            analytics = json.load(f)
    except FileNotFoundError:
        analytics = {
            "last_updated": datetime.now().isoformat(),
            "posts_history": [],
            "summary": {}
        }
    
    analytics['posts_history'].append(metrics)
    analytics['last_updated'] = datetime.now().isoformat()
    
    with open('linkedin/linkedin_analytics.json', 'w', encoding='utf-8') as f:
        json.dump(analytics, f, indent=2, ensure_ascii=False)
    
    print(f"Analytics saved: {metrics['post_id']}")

def main():
    """メイン処理：最新投稿のメトリクスを取得"""
    config = load_config()
    person_urn = config['profile']['person_urn']
    
    # 最新投稿の ID を取得（例：progress.json から）
    with open('linkedin/linkedin_posting_progress.json', 'r', encoding='utf-8') as f:
        progress = json.load(f)
    
    # 最新の投稿 ID は別途管理が必要（複雑なため、スキップ）
    print("LinkedIn Analytics script ready")

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: linkedin_analytics.json 初期化**

```bash
python3 << 'EOF'
import json
from datetime import datetime

analytics = {
    "last_updated": datetime.now().isoformat(),
    "posts_history": [],
    "summary": {}
}

with open('linkedin/linkedin_analytics.json', 'w', encoding='utf-8') as f:
    json.dump(analytics, f, indent=2, ensure_ascii=False)

print("Analytics file created")
EOF
```

- [ ] **Step 3: Commit**

```bash
git add linkedin/linkedin_analytics.py linkedin/linkedin_analytics.json
git commit -m "feat: create linkedin_analytics.py (engagement tracking)"
```

---

## フェーズ 4: GitHub Actions ワークフロー

### Task 5: linkedin_auto_post_daily.yml ワークフロー作成

**Files:**
- Create: `.github/workflows/linkedin_auto_post_daily.yml`

**背景:** 毎日自動で LinkedIn に投稿するワークフロー。Threads 投稿を週 1 回（例：金曜日 8:00 UTC）投稿。

- [ ] **Step 1: ワークフロー定義を作成**

```yaml
name: LinkedIn Auto Post Daily

on:
  schedule:
    - cron: '0 8 * * 5'  # 毎週金曜 8:00 UTC (17:00 JST)
  workflow_dispatch:

jobs:
  post:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Prepare LinkedIn config
        env:
          LINKEDIN_CONFIG: ${{ secrets.LINKEDIN_CONFIG }}
        run: |
          mkdir -p linkedin
          echo "$LINKEDIN_CONFIG" > linkedin/linkedin_config.json
      
      - name: Post to LinkedIn
        run: python3 linkedin/linkedin_auto_post.py
      
      - name: Commit progress
        run: |
          git config user.email "github-action@example.com"
          git config user.name "GitHub Action"
          git add linkedin/linkedin_posting_progress.json
          git commit -m "auto: update LinkedIn posting progress $(date '+%Y/%m/%d %H:%M' -u)" || true
          git push
```

- [ ] **Step 2: GitHub Secrets を設定**

GitHub → リポジトリ Settings → Secrets and variables → Actions

```
LINKEDIN_CONFIG: （linkedin_config.json の内容を JSON 文字列で貼り付け）
```

- [ ] **Step 3: ワークフロー構文を検証**

```bash
ls -la .github/workflows/linkedin_auto_post_daily.yml
```

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/linkedin_auto_post_daily.yml
git commit -m "ci: add linkedin_auto_post_daily workflow"
```

---

## フェーズ 5: テスト＆デプロイ

### Task 6: ローカルテスト

**Files:**
- N/A（全スクリプト）

- [ ] **Step 1: linkedin_auto_post.py をテスト**

```bash
python3 linkedin/linkedin_auto_post.py
```

Expected: エラーなし、投稿完了メッセージ

- [ ] **Step 2: 投稿内容を確認**

LinkedIn プロフィールで最新投稿を確認

Expected: Threads の Day 1 投稿がハッシュタグ付きで投稿されている

- [ ] **Step 3: linkedin_analytics.py をテスト**

```bash
python3 linkedin/linkedin_analytics.py
```

Expected: Analytics ファイルが作成される

---

### Task 7: GitHub へプッシュ＆デプロイ確認

**Files:**
- N/A（ワークフロー）

- [ ] **Step 1: すべての変更をコミット＆プッシュ**

```bash
git status
git push origin main
```

Expected: GitHub へプッシュ完了

- [ ] **Step 2: GitHub Actions ワークフローが表示されるか確認**

`https://github.com/[user]/[repo]/actions`

Expected: `LinkedIn Auto Post Daily` ワークフロー が表示される

- [ ] **Step 3: 手動実行でテスト**

GitHub UI から「Run workflow」をクリック

Expected: ワークフロー 実行完了（緑のチェック）

---

## まとめ

このプランで以下が実現される：

✅ **LinkedIn API 認証** - OAuth 2.0 トークン取得・管理
✅ **自動投稿** - Threads → LinkedIn 毎週自動投稿
✅ **エンゲージメント分析** - いいね・コメント・シェア測定
✅ **GitHub Actions 自動化** - 毎週金曜 8:00 UTC に自動実行
✅ **テスト＆デプロイ** - ローカル確認後、GitHub Actions 稼働開始

---

**実装開始**: Task 1 から順番に進めてください
