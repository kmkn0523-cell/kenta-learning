# skin 画像付きThreads自動投稿 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** skinのThreads自動投稿（3本ツリー）の本1（フック）にテーマ別カード画像を添付する

**Architecture:** `skin_threads_action.py` に画像URL生成関数と画像投稿対応を追加し、`post_to_threads()` に `image_url` 引数を加える。画像はGitHub Pagesで公開済みの `skin/skin_images/theme{id:02d}.png` を使用。本2・本3はテキストのまま変更しない。

**Tech Stack:** Python 3, Threads API (`media_type: IMAGE`), GitHub Pages, python-dotenv

---

## ファイル構成

| ファイル | 変更内容 |
|---|---|
| `skin/skin_threads_action.py` | dotenv追加・画像URL関数追加・`post_to_threads()`に`image_url`引数追加・`main()`で本1に画像URL渡す |
| `skin/skin_images/theme01〜14.png` | 生成済み・コミット対象 |

---

### Task 1: 画像URLの形式を確認するテストを書く

**Files:**
- Test: `skin/test_skin_image_url.py`（新規・確認後に削除）

- [ ] **Step 1: テストファイルを作成する**

`skin/test_skin_image_url.py` を以下の内容で作成する：

```python
# test_skin_image_url.py
# get_image_url() が正しいGitHub Pages URLを返すか確認するテスト

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ["THREADS_ACCESS_TOKEN"] = "dummy"
os.environ["THREADS_USER_ID"]      = "dummy"

from skin_threads_action import get_image_url, GITHUB_BASE

def test_url_format():
    url = get_image_url(1)
    assert "github.io" in url,                    f"GitHub Pages URLではない: {url}"
    assert "theme01.png" in url,                  f"ファイル名が違う: {url}"
    assert "raw.githubusercontent.com" not in url, f"Raw URLが残っている: {url}"
    print(f"✅ URL形式OK: {url}")

def test_zero_padding():
    assert "theme05.png" in get_image_url(5),  "ゼロ埋めされていない"
    assert "theme14.png" in get_image_url(14), "14番が正しくない"
    print("✅ ゼロ埋めOK")

if __name__ == "__main__":
    test_url_format()
    test_zero_padding()
    print("\n全テスト通過！")
```

- [ ] **Step 2: テストを実行して「失敗」することを確認する**

```bash
cd /home/kenta_kamijyo/skin && python3 test_skin_image_url.py
```

期待する出力（失敗）：
```
ImportError: cannot import name 'get_image_url' from 'skin_threads_action'
```

---

### Task 2: `skin_threads_action.py` を修正する

**Files:**
- Modify: `skin/skin_threads_action.py`

- [ ] **Step 1: ファイル冒頭のimportとAPIキー読み込み部分を修正する**

現在の4〜13行目：

```python
import json                    # JSONファイルを扱う道具
import os                      # 環境変数を読み込む道具
import time                    # 待機処理に使う道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime  # 今の日時を取得する道具

# 環境変数からAPIキーを読み込む（GitHub Actionsのsecretsから渡される）
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
THREADS_USER_ID      = os.environ["THREADS_USER_ID"]
```

以下に置き換える：

```python
import json                    # JSONファイルを扱う道具
import os                      # 環境変数を読み込む道具
import time                    # 待機処理に使う道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime  # 今の日時を取得する道具

# ローカル実行時は .env ファイルからAPIキーを読み込む（GitHub Actionsでは不要）
try:
    from dotenv import load_dotenv
    load_dotenv("/home/kenta_kamijyo/.env")
except ImportError:
    pass

# 環境変数からAPIキーを読み込む（GitHub Actionsのsecretsから渡される）
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
THREADS_USER_ID      = os.environ["THREADS_USER_ID"]

# GitHub Pagesの画像ベースURL
GITHUB_BASE = "https://kmkn0523-cell.github.io/kenta-learning/skin/skin_images"
```

- [ ] **Step 2: `get_image_url()` 関数を追加する**

`GITHUB_BASE = ...` の行の直後に追加する：

```python
def get_image_url(thread_id):
    """スレッドIDに対応するカード画像のURLを返す（GitHub Pages）"""
    return f"{GITHUB_BASE}/theme{thread_id:02d}.png"
```

- [ ] **Step 3: `post_to_threads()` に `image_url` 引数を追加する**

現在の `post_to_threads(text, reply_to_id=None):` 関数のコンテナ作成部分を修正する：

```python
def post_to_threads(text, reply_to_id=None, image_url=None):
    """
    Threads APIを使って投稿する（2段階APIコール）
    reply_to_id を渡すとリプライ投稿になる（ツリーの2本目・3本目に使う）
    image_url を渡すと画像付き投稿になる（本1のみ使用）
    """

    # ステップ1: 投稿コンテナ（投稿の下書き）を作成する
    container_url = f"https://graph.threads.net/{THREADS_USER_ID}/threads"

    if image_url:
        # 画像付き投稿
        container_params = {
            "media_type": "IMAGE",
            "image_url": image_url,
            "text": text,
            "access_token": THREADS_ACCESS_TOKEN
        }
        print(f"  画像URL: {image_url}")
    else:
        # テキストのみ投稿
        container_params = {
            "media_type": "TEXT",
            "text": text,
            "access_token": THREADS_ACCESS_TOKEN
        }

    if reply_to_id:
        container_params["reply_to_id"] = reply_to_id

    response = requests.post(container_url, params=container_params)
    data = response.json()

    if "id" not in data:
        raise Exception(f"コンテナ作成失敗: {data}")

    creation_id = data["id"]

    print("  コンテナ作成完了。30秒待機中...")
    time.sleep(30)

    publish_url = f"https://graph.threads.net/{THREADS_USER_ID}/threads_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": THREADS_ACCESS_TOKEN
    }
    publish_response = requests.post(publish_url, params=publish_params)
    publish_data = publish_response.json()

    if "id" not in publish_data:
        raise Exception(f"公開失敗: {publish_data}")

    return publish_data["id"]
```

- [ ] **Step 4: `main()` の本1投稿部分を修正する**

`main()` 内の「本1を投稿する」箇所を以下に変更する：

```python
    # 本1を投稿する（新規投稿・ツリーの起点・画像付き）
    print("\n本1を投稿中（フック＋画像）...")
    image_url = get_image_url(thread_set["id"])
    post_id_1 = post_to_threads(text_1, image_url=image_url)
    print(f"  ✅ 本1投稿成功！（ID: {post_id_1}）")
```

---

### Task 3: テストを通してコミットする

- [ ] **Step 1: テストを実行して「成功」することを確認する**

```bash
cd /home/kenta_kamijyo/skin && python3 test_skin_image_url.py
```

期待する出力（成功）：
```
✅ URL形式OK: https://kmkn0523-cell.github.io/kenta-learning/skin/skin_images/theme01.png
✅ ゼロ埋めOK

全テスト通過！
```

- [ ] **Step 2: テストファイルを削除する**

```bash
rm /home/kenta_kamijyo/skin/test_skin_image_url.py
```

- [ ] **Step 3: 差分を確認する**

```bash
cd /home/kenta_kamijyo && git diff skin/skin_threads_action.py
```

以下の3点が変わっていればOK：
- dotenvのtry/importが追加されている
- `GITHUB_BASE` と `get_image_url()` が追加されている
- `post_to_threads()` に `image_url` 引数が追加されている
- `main()` で `post_to_threads(text_1, image_url=image_url)` を呼んでいる

- [ ] **Step 4: 画像ファイルと修正スクリプトをコミットする**

```bash
cd /home/kenta_kamijyo && git add skin/skin_images/ skin/skin_threads_action.py skin/generate_skin_cards.py && git commit -m "feat: skinのThreads本1投稿にテーマ別カード画像を添付"
```

- [ ] **Step 5: プッシュする**

```bash
cd /home/kenta_kamijyo && git push
```

---

### Task 4: 手動テスト投稿で動作確認する

- [ ] **Step 1: ローカルで手動テスト投稿する**

```bash
cd /home/kenta_kamijyo/skin && python3 skin_threads_action.py
```

期待する出力：
```
=== skin自動投稿開始: 2026/05/06 XX:XX ===
投稿セット: X/14 (テーマ名)

本1を投稿中（フック＋画像）...
  画像URL: https://kmkn0523-cell.github.io/kenta-learning/skin/skin_images/themeXX.png
  コンテナ作成完了。30秒待機中...
  ✅ 本1投稿成功！（ID: XXXXXXXXXX）

本2を投稿中（本題）...
  コンテナ作成完了。30秒待機中...
  ✅ 本2投稿成功！（ID: XXXXXXXXXX）

本3を投稿中（CTA）...
  コンテナ作成完了。30秒待機中...
  ✅ 本3投稿成功！（ID: XXXXXXXXXX）
=== 完了 ===
```

- [ ] **Step 2: Threadsアプリで画像付き投稿を確認する**

skinアカウントを開き、最新投稿（本1）にカード画像が表示されていればOK。

---

### Task 5: TODO.mdを更新する

- [ ] **Step 1: TODO.mdの該当行を完了にする**

`/home/kenta_kamijyo/TODO.md` の以下の行を更新する：

```
- [x] 画像投稿対応（Pillowで画像生成→GitHubにホスト→Threads画像投稿）
```

- [ ] **Step 2: コミットする**

```bash
cd /home/kenta_kamijyo && git add TODO.md && git commit -m "docs: skin画像投稿対応をTODO完了に更新" && git push
```
