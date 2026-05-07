# @RoninWords 画像付きThreads自動投稿 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** @RoninWords のThreads自動投稿に書道カード画像を添付する

**Architecture:** GitHub Pagesで画像を公開し、そのURLをThreads APIの `media_type: IMAGE` に渡す。コードは `ronin/ronin_threads_action.py` の2箇所のみ変更。

**Tech Stack:** Python 3, Threads API, GitHub Pages

---

## 事前手作業（コード変更の前にユーザーが実施）

### 【手作業】GitHub Pages を有効化する

以下の手順をブラウザで実施してください：

1. `https://github.com/kmkn0523-cell/kenta-learning` を開く
2. 上部の **Settings** タブをクリック
3. 左サイドバーの **Pages** をクリック
4. **Source** で `Deploy from a branch` を選択
5. **Branch** を `main` / `/ (root)` に設定して **Save**
6. 数分待つと `https://kmkn0523-cell.github.io/kenta-learning/` が公開される

有効化後、以下のURLで画像が表示されることを確認してください：  
`https://kmkn0523-cell.github.io/kenta-learning/ronin/ronin_images/day01.png`

---

## ファイル構成

| ファイル | 変更内容 |
|---|---|
| `ronin/ronin_threads_action.py` | `GITHUB_RAW_BASE` のURL変更（1行）＋ `main()` で `image_url` を渡す（1行） |

---

### Task 1: URLを確認するテストを書いて実行する

**Files:**
- Test: `ronin/test_image_url.py`（新規作成・確認後に削除してOK）

- [ ] **Step 1: テストファイルを作成する**

`ronin/test_image_url.py` を以下の内容で作成する：

```python
# test_image_url.py
# get_image_url() が正しいGitHub Pages URLを返すか確認するテスト

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# 環境変数のダミーを設定（importエラー防止）
os.environ["THREADS_ACCESS_TOKEN"] = "dummy"
os.environ["THREADS_USER_ID"] = "dummy"

from ronin_threads_action import get_image_url, GITHUB_RAW_BASE

def test_image_url_format():
    """get_image_url()がGitHub PagesのURLを返すことを確認"""
    url = get_image_url(1)
    assert "github.io" in url, f"GitHub Pages URLではありません: {url}"
    assert "day01.png" in url, f"ファイル名が正しくありません: {url}"
    assert "raw.githubusercontent.com" not in url, f"Raw URLが残っています: {url}"
    print(f"✅ URLの形式OK: {url}")

def test_image_url_day_padding():
    """Day番号が2桁のゼロ埋めになっているか確認"""
    url = get_image_url(5)
    assert "day05.png" in url, f"ゼロ埋めされていません: {url}"
    print(f"✅ ゼロ埋めOK: {url}")

if __name__ == "__main__":
    test_image_url_format()
    test_image_url_day_padding()
    print("\n全テスト通過！")
```

- [ ] **Step 2: テストを実行して「失敗」することを確認する**

```bash
cd /home/kenta_kamijyo/ronin && python test_image_url.py
```

期待する出力（失敗）：
```
AssertionError: GitHub Pages URLではありません: https://raw.githubusercontent.com/...
```

---

### Task 2: `ronin_threads_action.py` を2箇所修正する

**Files:**
- Modify: `ronin/ronin_threads_action.py`

- [ ] **Step 1: `GITHUB_RAW_BASE` のURLを変更する**

`ronin/ronin_threads_action.py` の22行目付近を変更する：

```python
# 変更前
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/kmkn0523-cell/kenta-learning/main/ronin/ronin_images"

# 変更後
GITHUB_RAW_BASE = "https://kmkn0523-cell.github.io/kenta-learning/ronin/ronin_images"
```

- [ ] **Step 2: `main()` で `image_url` を渡すよう変更する**

`ronin/ronin_threads_action.py` の148〜151行目付近を変更する：

```python
# 変更前
    # Threads APIで投稿する（テキストのみ）
    # ※ GitHub Raw URLはThreads APIでブロックされるためテキスト投稿に戻す
    post_id = post_to_threads(full_text)

# 変更後
    # Threads APIで投稿する（書道カード画像付き）
    image_url = get_image_url(post["day"])
    post_id = post_to_threads(full_text, image_url=image_url)
```

- [ ] **Step 3: テストを再実行して「成功」することを確認する**

```bash
cd /home/kenta_kamijyo/ronin && python test_image_url.py
```

期待する出力（成功）：
```
✅ URLの形式OK: https://kmkn0523-cell.github.io/kenta-learning/ronin/ronin_images/day01.png
✅ ゼロ埋めOK: https://kmkn0523-cell.github.io/kenta-learning/ronin/ronin_images/day05.png

全テスト通過！
```

- [ ] **Step 4: テストファイルを削除する**

```bash
rm /home/kenta_kamijyo/ronin/test_image_url.py
```

---

### Task 3: コミット＆プッシュ

**Files:**
- Commit: `ronin/ronin_threads_action.py`

- [ ] **Step 1: 変更内容を確認する**

```bash
cd /home/kenta_kamijyo && git diff ronin/ronin_threads_action.py
```

差分で以下2点が変わっていればOK：
- `GITHUB_RAW_BASE` の URL が `github.io` に変わっている
- `post_to_threads(full_text)` → `post_to_threads(full_text, image_url=image_url)` に変わっている

- [ ] **Step 2: コミットする**

```bash
cd /home/kenta_kamijyo && git add ronin/ronin_threads_action.py && git commit -m "feat: Threadsに書道カード画像を添付して投稿するよう変更（GitHub Pages URL使用）"
```

- [ ] **Step 3: プッシュする**

```bash
cd /home/kenta_kamijyo && git push
```

プッシュ後、GitHub Pagesに画像が公開されるまで数分待つ。

---

### Task 4: 動作確認（手動テスト投稿）

- [ ] **Step 1: 手動で1回テスト投稿する**

```bash
cd /home/kenta_kamijyo/ronin && python ronin_threads_action.py
```

期待する出力：
```
=== Ronin自動投稿開始: 2026/05/06 XX:XX ===
投稿番号: X/120
投稿タイプ: DayXX morning/evening
  画像URL: https://kmkn0523-cell.github.io/kenta-learning/ronin/ronin_images/dayXX.png
コンテナ作成完了。30秒待機中...
✅ 投稿成功！（投稿ID: XXXXXXXXXX）
```

- [ ] **Step 2: Threadsアプリで画像付き投稿を確認する**

@RoninWords のアカウントを開き、最新投稿に書道カード画像が表示されていればOK。

---

## TODO.md の更新

Task 4 完了後、`TODO.md` の以下の行を `[x]` にマークする：

```
- [x] 画像投稿対応（書道カード画像をThreadsに自動投稿）
```
