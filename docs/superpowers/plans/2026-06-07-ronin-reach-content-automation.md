# @RoninWords reach加速（コンテンツ強化＋自動化）実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** @RoninWordsのThreads投稿に「コメント誘発型コンテンツ・動的ハッシュタグ・投稿直後の自動first-comment」を加え、非フォロワー拡散（reach）を増やす。

**Architecture:** 既存の`threads_posts.json`(教えの投稿400本)は不可侵。新カテゴリ`engagement post`を別ファイルで持ち、4投稿に1回差し込む。本文からマネタイズCTAリンクを外し、公開直後に自分の投稿へ返信する「1コメ目」へ移す。ハッシュタグは4セットをローテーション。純粋関数を小モジュールに分離しTDD、API部はモック。`ronin_threads_action.py`がオーケストレーション。

**Tech Stack:** Python 3.12 / requests / pytest / Threads Graph API（`reply_to_id`はskin側で実証済み）/ GitHub Actions（スケジュール変更なし）。

**設計書:** `docs/superpowers/specs/2026-06-07-ronin-reach-content-automation-design.md`

---

## ⚠️ 実行前に必読：本番ポスター保護

`auto_sync.sh` が **10分ごとに cron で `git add . && git commit && git push` を実行**している。`main` 上で作業すると壊れかけのコードが10分以内に本番へpushされ、稼働中のThreadsポスターが壊れる。
→ **必ず feature ブランチで作業する**（Task 0）。新ブランチはupstream未設定なので auto_sync の `git push` は無害に失敗し、`main` は保護される。全テスト合格＋dry-run検証後にだけ意図的に `main` へマージする。

import規約（既存に合わせる）: roninスクリプトは `cd ronin && python ...` で動くので **モジュール間はベアimport**（例 `import ronin_hashtags`）。テストは `ronin/tests/` に置き、先頭で `sys.path.insert(0, str(Path(__file__).resolve().parents[1]))`（skin/testsと同型）。

テスト実行コマンド（このプロジェクト）:
```
pytest ronin/tests/ -v
```

---

## ファイル構成（作成/変更マップ）

| ファイル | 区分 | 責務 |
|---|---|---|
| `ronin/ronin_hashtags.py` | 新規 | ハッシュタグ4セットのローテーション（純粋関数） |
| `ronin/ronin_engagement_posts.json` | 新規 | コメント誘発投稿の在庫（最初は手書き種→Workflowで30本） |
| `ronin/ronin_engagement.py` | 新規 | engagement在庫のロード/選択/検証（純粋関数） |
| `ronin/ronin_comment_seeder.py` | 新規 | 1コメ目テキストの生成（純粋関数） |
| `ronin/ronin_threads_action.py` | 変更 | `post_to_threads`に`reply_to_id`追加・オーケストレーション改造・`--dry-run` |
| `ronin/ronin_analyzer.py` | 変更 | 「0日」バグ修正（最古投稿を`min`で求める） |
| `ronin/tests/test_ronin_hashtags.py` | 新規 | Task 1 |
| `ronin/tests/test_ronin_engagement.py` | 新規 | Task 2 |
| `ronin/tests/test_ronin_comment_seeder.py` | 新規 | Task 3 |
| `ronin/tests/test_ronin_threads_action.py` | 新規 | Task 4・Task 6-8 |
| `ronin/tests/test_ronin_analyzer.py` | 新規 | Task 5 |
| `threads_posts.json` | 変更（要承認） | day43-evening を別フックへ（Task 10） |

---

## Phase 0: 作業隔離

### Task 0: feature ブランチを切る

**Files:** なし（git操作のみ）

- [ ] **Step 1: main最新化してブランチ作成**

```bash
cd /home/kenta_kamijyo
git checkout main
git pull --rebase origin main
git checkout -b feature/ronin-reach-boost
```

- [ ] **Step 2: ブランチ確認**

Run: `git branch --show-current`
Expected: `feature/ronin-reach-boost`

> 以降のコミットはこのブランチに溜まる。auto_syncが「自動同期」コミットを混ぜても無害（mainには行かない）。

---

## Phase 1: ハッシュタグ動的ローテーション

### Task 1: `ronin_hashtags.py`

**Files:**
- Create: `ronin/ronin_hashtags.py`
- Test: `ronin/tests/test_ronin_hashtags.py`

- [ ] **Step 1: 失敗するテストを書く**

```python
# ronin/tests/test_ronin_hashtags.py
# ハッシュタグ・ローテーションの純粋関数テスト
# 実行: pytest ronin/tests/test_ronin_hashtags.py -v
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # ronin/ をimport可能にする

from ronin_hashtags import pick_hashtag_set, HASHTAG_SETS


def test_四セットを順番に回す():
    assert pick_hashtag_set(0) == HASHTAG_SETS["A"]
    assert pick_hashtag_set(1) == HASHTAG_SETS["B"]
    assert pick_hashtag_set(2) == HASHTAG_SETS["C"]
    assert pick_hashtag_set(3) == HASHTAG_SETS["D"]


def test_四を超えたら先頭に戻る():
    assert pick_hashtag_set(4) == HASHTAG_SETS["A"]
    assert pick_hashtag_set(7) == HASHTAG_SETS["D"]


def test_各セットはハッシュタグ文字列():
    for value in HASHTAG_SETS.values():
        assert value.startswith("#")
        assert "  " not in value  # 二重スペースが無い
```

- [ ] **Step 2: 失敗確認**

Run: `pytest ronin/tests/test_ronin_hashtags.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'ronin_hashtags'`）

- [ ] **Step 3: 実装**

```python
# ronin/ronin_hashtags.py
# @RoninWords用：ハッシュタグを4セットで回す（発見タブ流入を広げる）
# 投稿カウントを渡すと A→B→C→D→A... の順でセットを返す純粋関数

# 4つのハッシュタグセット（1セット3個に抑える＝スパム判定回避）
HASHTAG_SETS = {
    "A": "#JapaneseWisdom #Bushido #Zen",      # 王道（コアの世界観）
    "B": "#StoicMindset #SelfDiscipline #Mindset",  # 越境（自己鍛錬・ストイック層へ）
    "C": "#Discipline #Resilience #Focus",     # 行動（モチベ層へ）
    "D": "#Samurai #Kanji #RoninWords",        # ブランド（指名検索を育てる）
}

# 回す順番（リストの順にローテーションする）
_ROTATION = ["A", "B", "C", "D"]


def pick_hashtag_set(count):
    """投稿カウント(0始まり)から、その回に使うハッシュタグ文字列を返す"""
    key = _ROTATION[count % len(_ROTATION)]  # 余りでA〜Dを選ぶ
    return HASHTAG_SETS[key]
```

- [ ] **Step 4: 成功確認**

Run: `pytest ronin/tests/test_ronin_hashtags.py -v`
Expected: PASS（3件）

- [ ] **Step 5: コミット**

```bash
git add ronin/ronin_hashtags.py ronin/tests/test_ronin_hashtags.py
git commit -m "feat(ronin): ハッシュタグ4セット動的ローテーション追加"
```

---

## Phase 2: engagement在庫のロード・選択・検証

### Task 2: `ronin_engagement.py` ＋ 種ファイル

**Files:**
- Create: `ronin/ronin_engagement_posts.json`（最初は手書き種2本。30本はTask 9で追加）
- Create: `ronin/ronin_engagement.py`
- Test: `ronin/tests/test_ronin_engagement.py`

- [ ] **Step 1: 種ファイルを作る**

```json
{
  "posts": [
    {
      "id": "eng001",
      "archetype": "either_or",
      "theme": "discipline",
      "text": "Train for a war that never comes.\n\nWise preparation — or wasted years?\n\nReply 🅰 wise  /  🅱 wasted.",
      "seed_comment": "I say 🅰. A blade kept sharp for nothing is still a sharp blade. Which did you pick — and why?"
    },
    {
      "id": "eng002",
      "archetype": "fill_blank",
      "theme": "mastery",
      "text": "The hardest discipline is ___.\n\nFinish the sentence in one word.",
      "seed_comment": "Mine is patience. The slow work feels like doing nothing — until it isn't. What's your word?"
    }
  ]
}
```

- [ ] **Step 2: 失敗するテストを書く**

```python
# ronin/tests/test_ronin_engagement.py
# engagement在庫のロード/選択/検証の純粋関数テスト
# 実行: pytest ronin/tests/test_ronin_engagement.py -v
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ronin_engagement import pick_engagement_post, validate_engagement_posts, load_engagement_posts


SAMPLE = [
    {"id": "eng001", "archetype": "either_or", "theme": "x",
     "text": "a?", "seed_comment": "s1"},
    {"id": "eng002", "archetype": "fill_blank", "theme": "y",
     "text": "b ___", "seed_comment": "s2"},
]


def test_engagement_indexで順番に選ぶ():
    assert pick_engagement_post(SAMPLE, 0)["id"] == "eng001"
    assert pick_engagement_post(SAMPLE, 1)["id"] == "eng002"
    assert pick_engagement_post(SAMPLE, 2)["id"] == "eng001"  # 末尾を超えたら戻る


def test_検証_正常データはエラーなし():
    assert validate_engagement_posts(SAMPLE) == []


def test_検証_必須キー欠落を検出():
    broken = [{"id": "x", "archetype": "a", "theme": "t", "text": "t"}]  # seed_comment欠落
    errors = validate_engagement_posts(broken)
    assert any("seed_comment" in e for e in errors)


def test_検証_id重複を検出():
    dup = [
        {"id": "same", "archetype": "a", "theme": "t", "text": "1", "seed_comment": "s"},
        {"id": "same", "archetype": "a", "theme": "t", "text": "2", "seed_comment": "s"},
    ]
    errors = validate_engagement_posts(dup)
    assert any("重複" in e for e in errors)


def test_検証_本文500字超を検出():
    longp = [{"id": "x", "archetype": "a", "theme": "t",
              "text": "a" * 501, "seed_comment": "s"}]
    errors = validate_engagement_posts(longp)
    assert any("500" in e for e in errors)


def test_実ファイルが検証を通る():
    posts = load_engagement_posts()
    assert len(posts) >= 2
    assert validate_engagement_posts(posts) == []
```

- [ ] **Step 3: 失敗確認**

Run: `pytest ronin/tests/test_ronin_engagement.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'ronin_engagement'`）

- [ ] **Step 4: 実装**

```python
# ronin/ronin_engagement.py
# @RoninWords用：コメント誘発投稿(engagement post)の在庫を扱う
# ・load_engagement_posts: JSONから読む
# ・pick_engagement_post: engagement_indexで順番に1本選ぶ
# ・validate_engagement_posts: 必須キー/字数/重複をチェック（CIや手動検証用）

import os
import json

# このファイルと同じ ronin/ にある在庫JSON
_DIR = os.path.dirname(os.path.abspath(__file__))
ENGAGEMENT_FILE = os.path.join(_DIR, "ronin_engagement_posts.json")

# 在庫の各エントリに必須のキー
REQUIRED_KEYS = ("id", "archetype", "theme", "text", "seed_comment")

# Threads APIの本文上限
MAX_LEN = 500


def load_engagement_posts():
    """在庫JSONを読み、postsリストを返す（無ければ空リスト）"""
    if not os.path.exists(ENGAGEMENT_FILE):
        return []
    with open(ENGAGEMENT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("posts", [])


def pick_engagement_post(posts, engagement_index):
    """engagement_index(0始まり)で在庫を順番に1本選ぶ（末尾を超えたら先頭へ）"""
    return posts[engagement_index % len(posts)]


def validate_engagement_posts(posts):
    """在庫の不備をエラーメッセージのリストで返す（空＝問題なし）"""
    errors = []
    seen_ids = set()
    seen_texts = set()
    for i, post in enumerate(posts):
        # 必須キーの欠落チェック
        for key in REQUIRED_KEYS:
            if not post.get(key):
                errors.append(f"[{i}] 必須キー欠落: {key}")
        # ID重複チェック
        post_id = post.get("id")
        if post_id in seen_ids:
            errors.append(f"[{i}] IDが重複: {post_id}")
        seen_ids.add(post_id)
        # 本文の重複チェック
        text = post.get("text", "")
        if text in seen_texts:
            errors.append(f"[{i}] 本文が重複: {post_id}")
        seen_texts.add(text)
        # 字数チェック（本文・seed_comment両方）
        if len(text) > MAX_LEN:
            errors.append(f"[{i}] 本文が500字超: {post_id} ({len(text)}字)")
        if len(post.get("seed_comment", "")) > MAX_LEN:
            errors.append(f"[{i}] seed_commentが500字超: {post_id}")
    return errors
```

- [ ] **Step 5: 成功確認**

Run: `pytest ronin/tests/test_ronin_engagement.py -v`
Expected: PASS（6件）

- [ ] **Step 6: コミット**

```bash
git add ronin/ronin_engagement.py ronin/ronin_engagement_posts.json ronin/tests/test_ronin_engagement.py
git commit -m "feat(ronin): engagement投稿の在庫ロード/選択/検証を追加"
```

---

## Phase 3: 1コメ目テキスト生成

### Task 3: `ronin_comment_seeder.py`

**Files:**
- Create: `ronin/ronin_comment_seeder.py`
- Test: `ronin/tests/test_ronin_comment_seeder.py`

- [ ] **Step 1: 失敗するテストを書く**

```python
# ronin/tests/test_ronin_comment_seeder.py
# 1コメ目テキスト生成の純粋関数テスト
# 実行: pytest ronin/tests/test_ronin_comment_seeder.py -v
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ronin_comment_seeder import (
    build_seed_comment,
    pick_generic_seed,
    GENERIC_SEED_QUESTIONS,
)


def test_CTA無しならベースだけ返す():
    assert build_seed_comment("What hit hardest today?") == "What hit hardest today?"


def test_CTAありなら2行空けて連結():
    out = build_seed_comment("Base question.", cta="Link here")
    assert out == "Base question.\n\nLink here"


def test_500字に丸める():
    out = build_seed_comment("a" * 600)
    assert len(out) <= 500


def test_汎用シードをカウントで回す():
    first = pick_generic_seed(0)
    assert first == GENERIC_SEED_QUESTIONS[0]
    # 末尾を超えたら先頭へ
    assert pick_generic_seed(len(GENERIC_SEED_QUESTIONS)) == GENERIC_SEED_QUESTIONS[0]


def test_汎用シードは複数用意されている():
    assert len(GENERIC_SEED_QUESTIONS) >= 3
```

- [ ] **Step 2: 失敗確認**

Run: `pytest ronin/tests/test_ronin_comment_seeder.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: 実装**

```python
# ronin/ronin_comment_seeder.py
# @RoninWords用：投稿直後に自分で付ける「1コメ目」の文章を作る（純粋関数のみ）
# 早期リプライでアルゴリズムに会話を認識させ、reachを伸ばす狙い。
# 実際の返信送信は ronin_threads_action.post_to_threads(reply_to_id=...) を使う。

# Threads APIの本文上限
MAX_LEN = 500

# 教えの投稿（既存400本）に付ける汎用の問いかけ。カウントで回す。
GENERIC_SEED_QUESTIONS = [
    "Which line hit hardest for you today? Drop it below. 👇",
    "Where does this show up in your life right now?",
    "Save this if you needed it today — and tell me why.",
    "One word: what does this teaching ask of you tomorrow?",
    "Agree, or does your experience say otherwise?",
]


def pick_generic_seed(count):
    """カウント(0始まり)で汎用の問いかけを順番に選ぶ（末尾を超えたら先頭へ）"""
    return GENERIC_SEED_QUESTIONS[count % len(GENERIC_SEED_QUESTIONS)]


def build_seed_comment(base, cta=""):
    """1コメ目の本文を作る。ベースの問いかけ＋（CTAサイクル時のみ）リンク行を連結する。"""
    text = base
    if cta:
        text = f"{base}\n\n{cta}"  # 2行空けてリンクを足す（本文には入れない）
    return text[:MAX_LEN]  # 念のため500字に丸める
```

- [ ] **Step 4: 成功確認**

Run: `pytest ronin/tests/test_ronin_comment_seeder.py -v`
Expected: PASS（5件）

- [ ] **Step 5: コミット**

```bash
git add ronin/ronin_comment_seeder.py ronin/tests/test_ronin_comment_seeder.py
git commit -m "feat(ronin): 1コメ目テキスト生成（汎用問い＋CTA連結）を追加"
```

---

## Phase 4: 返信投稿対応（`post_to_threads`に`reply_to_id`）

### Task 4: `ronin_threads_action.py` の `post_to_threads` 拡張

**Files:**
- Modify: `ronin/ronin_threads_action.py`（`post_to_threads` シグネチャと本文）
- Test: `ronin/tests/test_ronin_threads_action.py`

> skin側 `skin_threads_action.py:238-267` と同型。`reply_to_id`を渡すと返信コンテナになる。

- [ ] **Step 1: 失敗するテストを書く（requestsをモック）**

```python
# ronin/tests/test_ronin_threads_action.py
# ronin_threads_action の純粋ロジック＋post_to_threadsのreply対応テスト（APIはモック）
# 実行: pytest ronin/tests/test_ronin_threads_action.py -v
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ronin_threads_action as action


def _fake_post(*args, **kwargs):
    """requests.post のフェイク：常に成功IDを返す"""
    resp = MagicMock()
    resp.json.return_value = {"id": "12345"}
    return resp


def test_post_to_threads_replyはreply_to_idを送る():
    captured = {}

    def capture(url, params=None, **kwargs):
        captured.setdefault("calls", []).append(params)
        resp = MagicMock()
        resp.json.return_value = {"id": "999"}
        return resp

    with patch.object(action, "requests") as m, \
         patch.object(action.time, "sleep", return_value=None):  # 30秒待機を飛ばす
        m.post.side_effect = capture
        result = action.post_to_threads("hi", reply_to_id="parent123")

    # コンテナ作成のparamsにreply_to_idが入っている
    container_params = captured["calls"][0]
    assert container_params.get("reply_to_id") == "parent123"
    assert result == "999"
```

- [ ] **Step 2: 失敗確認**

Run: `pytest ronin/tests/test_ronin_threads_action.py::test_post_to_threads_replyはreply_to_idを送る -v`
Expected: FAIL（`post_to_threads() got an unexpected keyword argument 'reply_to_id'`）

- [ ] **Step 3: 実装（`post_to_threads`にreply_to_id追加）**

`ronin/ronin_threads_action.py` の `def post_to_threads(text, image_url=None):` を次に置き換える（既存リトライ構造は保持し、分岐を1つ足すだけ）:

```python
def post_to_threads(text, image_url=None, reply_to_id=None):
    """
    Threads APIで投稿する（2段階APIコール）
    - image_url を渡すと画像付き投稿
    - reply_to_id を渡すと、その投稿への返信になる（1コメ目シーディング用）
    """

    container_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"

    if reply_to_id:
        # 返信投稿（テキストのみ・親投稿IDを指定）
        container_params = {
            "media_type": "TEXT",
            "text": text,
            "reply_to_id": reply_to_id,
            "access_token": THREADS_ACCESS_TOKEN
        }
        print(f"  返信先ID: {reply_to_id}")
    elif image_url:
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

    # 一時的なAPIエラーに備えてリトライ（最大2回・30秒待つ）
    for attempt in range(1, 3):
        response = requests.post(container_url, params=container_params)
        data = response.json()

        if "id" in data:
            break

        error_info = data.get("error", {})
        error_subcode = error_info.get("error_subcode")
        is_transient = error_info.get("is_transient") or error_subcode == 2207052
        if is_transient and attempt < 2:
            print(f"  ⚠️ コンテナ作成エラー（試行{attempt}/2）。30秒後にリトライします: {error_info.get('message', '')}")
            time.sleep(30)
        else:
            raise Exception(f"コンテナ作成失敗（試行{attempt}/2）: {data}")

    creation_id = data["id"]

    print("コンテナ作成完了。30秒待機中...")
    time.sleep(30)

    publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": THREADS_ACCESS_TOKEN
    }
    for attempt in range(1, 4):
        publish_response = requests.post(publish_url, params=publish_params)
        publish_data = publish_response.json()

        if "id" in publish_data:
            break

        error_info = publish_data.get("error", {})
        if error_info.get("is_transient") and attempt < 3:
            print(f"  ⚠️ 一時的なAPIエラー（試行{attempt}/3）。30秒後にリトライします...")
            time.sleep(30)
        else:
            raise Exception(f"公開失敗（試行{attempt}/3）: {publish_data}")

    return publish_data["id"]
```

- [ ] **Step 4: 成功確認**

Run: `pytest ronin/tests/test_ronin_threads_action.py -v`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
git add ronin/ronin_threads_action.py ronin/tests/test_ronin_threads_action.py
git commit -m "feat(ronin): post_to_threadsにreply_to_id対応を追加（1コメ目用）"
```

---

## Phase 5: analyzer「0日」バグ修正

### Task 5: `ronin_analyzer.py` の最古投稿判定を堅牢化

**Files:**
- Modify: `ronin/ronin_analyzer.py`（`should_analyze`内のdays計算を関数に切り出す）
- Test: `ronin/tests/test_ronin_analyzer.py`

> 原因: `posts_history[0]["posted_at"]` を最古と仮定しているが、並びが逆/混在だと0日に張り付く。全件の最小日時を取れば順序に依存しない。

- [ ] **Step 1: 失敗するテストを書く**

```python
# ronin/tests/test_ronin_analyzer.py
# 「最古の投稿日時」を順序に依存せず求められるかのテスト
# 実行: pytest ronin/tests/test_ronin_analyzer.py -v
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ronin_analyzer import earliest_post_datetime


def test_並びが新しい順でも最古を返す():
    history = [
        {"posted_at": "2026-06-01T00:00:00+0000"},  # 新しいものが先頭
        {"posted_at": "2026-05-01T00:00:00+0000"},  # 本当の最古は末尾
    ]
    dt = earliest_post_datetime(history)
    assert dt.month == 5 and dt.day == 1


def test_空なら None():
    assert earliest_post_datetime([]) is None


def test_posted_at欠落は無視():
    history = [{"foo": "bar"}, {"posted_at": "2026-05-10T00:00:00+0000"}]
    dt = earliest_post_datetime(history)
    assert dt.day == 10
```

- [ ] **Step 2: 失敗確認**

Run: `pytest ronin/tests/test_ronin_analyzer.py -v`
Expected: FAIL（`cannot import name 'earliest_post_datetime'`）

- [ ] **Step 3: 実装（ヘルパー追加＋should_analyzeで利用）**

`ronin/ronin_analyzer.py` の `parse_iso_datetime` の直後に追加:

```python
def earliest_post_datetime(posts_history):
    """posts_history全件から最古の投稿日時を返す（並び順に依存しない）。無ければNone。"""
    dates = []
    for post in posts_history:
        posted_at = post.get("posted_at")
        if not posted_at:
            continue  # posted_atが無いレコードは無視
        try:
            dates.append(parse_iso_datetime(posted_at))
        except (ValueError, TypeError):
            continue  # 壊れた日時も無視
    return min(dates) if dates else None
```

`should_analyze()` 内の次の3行:

```python
        first_post_datetime_str = posts_history[0]["posted_at"]
        first_post_datetime = parse_iso_datetime(first_post_datetime_str)
        now = datetime.now(first_post_datetime.tzinfo)
```

を次に置き換える:

```python
        first_post_datetime = earliest_post_datetime(posts_history)
        if first_post_datetime is None:
            print("⚠️  学習フェーズ: 有効な投稿日時がありません")
            return False
        now = datetime.now(first_post_datetime.tzinfo)
```

- [ ] **Step 4: 成功確認**

Run: `pytest ronin/tests/test_ronin_analyzer.py -v`
Expected: PASS（3件）

- [ ] **Step 5: コミット**

```bash
git add ronin/ronin_analyzer.py ronin/tests/test_ronin_analyzer.py
git commit -m "fix(ronin): analyzerの最古投稿判定を全件minにして0日バグ修正"
```

---

## Phase 6: オーケストレーション改造

### Task 6: 投稿種別の選択 `decide_post_kind`

**Files:**
- Modify: `ronin/ronin_threads_action.py`（関数追加）
- Test: `ronin/tests/test_ronin_threads_action.py`（追記）

- [ ] **Step 1: 失敗するテストを追記**

```python
def test_4投稿に1回engagementを選ぶ():
    assert action.decide_post_kind(0) == "teaching"
    assert action.decide_post_kind(1) == "teaching"
    assert action.decide_post_kind(2) == "teaching"
    assert action.decide_post_kind(3) == "engagement"
    assert action.decide_post_kind(7) == "engagement"
    assert action.decide_post_kind(4) == "teaching"
```

- [ ] **Step 2: 失敗確認**

Run: `pytest ronin/tests/test_ronin_threads_action.py::test_4投稿に1回engagementを選ぶ -v`
Expected: FAIL（`module 'ronin_threads_action' has no attribute 'decide_post_kind'`）

- [ ] **Step 3: 実装（`post_to_threads`の下に追加）**

```python
def decide_post_kind(history_count):
    """投稿履歴の件数から、今回が教えの投稿かengagement投稿かを決める。
    4投稿に1回(余り3)をengagementにする。"""
    return "engagement" if history_count % 4 == 3 else "teaching"
```

- [ ] **Step 4: 成功確認** → PASS
- [ ] **Step 5: コミット**

```bash
git add ronin/ronin_threads_action.py ronin/tests/test_ronin_threads_action.py
git commit -m "feat(ronin): 4投稿に1回engagementを差し込むdecide_post_kind追加"
```

### Task 7: 本文ビルドとCTAサイクル（CTAは本文から外す）

**Files:**
- Modify: `ronin/ronin_threads_action.py`（定数追加・関数追加）
- Test: `ronin/tests/test_ronin_threads_action.py`（追記）

- [ ] **Step 1: 失敗するテストを追記**

```python
def test_本文はハッシュタグを末尾に付ける():
    out = action.build_full_text("Hello world", "#A #B #C")
    assert out == "Hello world\n\n#A #B #C"


def test_本文が500字を超えたら丸める():
    out = action.build_full_text("x" * 600, "#A #B #C")
    assert len(out) <= 500
    assert out.endswith("#A #B #C")  # ハッシュタグは必ず残す


def test_CTAサイクル_14ごとにGumroad_Substack():
    assert action.cta_line_for_cycle(0) == action.GUMROAD_LINE
    assert action.cta_line_for_cycle(7) == action.SUBSTACK_LINE
    assert action.cta_line_for_cycle(3) == ""  # 通常回はCTA無し
```

- [ ] **Step 2: 失敗確認** → FAIL（`build_full_text`/`cta_line_for_cycle`未定義）

- [ ] **Step 3: 実装**

`ronin/ronin_threads_action.py` 冒頭の定数部を変更する。既存の以下:

```python
HASHTAGS = "\n\n#JapaneseWisdom #Bushido #Zen #Samurai #Wisdom"
GUMROAD_URL = "https://kmknova8.gumroad.com/l/mowuxf"
GUMROAD_CTA = f"\n\n🖌 Get the calligraphy wallpaper pack → {GUMROAD_URL}"
SUBSTACK_URL = "https://substack.com/@roninwords"
SUBSTACK_CTA = f"\n\n📖 Full deep dive on this teaching → {SUBSTACK_URL}"
```

を次に置き換える（CTAは「1コメ目」用のリンク行に変更。本文用の固定HASHTAGSは廃止）:

```python
# マネタイズ導線は本文ではなく「1コメ目」に載せる（本文をクリーンに保ち配信抑制を避ける）
GUMROAD_URL = "https://kmknova8.gumroad.com/l/mowuxf"
SUBSTACK_URL = "https://substack.com/@roninwords"
GUMROAD_LINE = f"🖌 Get the calligraphy wallpaper pack → {GUMROAD_URL}"
SUBSTACK_LINE = f"📖 Full deep dive on this teaching → {SUBSTACK_URL}"
```

ファイル冒頭のimportに次を追加（他のimportの並びに合わせる）:

```python
import ronin_hashtags          # ハッシュタグ・ローテーション
import ronin_engagement        # engagement在庫
import ronin_comment_seeder    # 1コメ目テキスト生成
```

`post_to_threads` の下（`decide_post_kind`の近く）に関数を追加:

```python
def build_full_text(content, hashtags):
    """本文＋ハッシュタグを組み立てる。500字を超える場合は本文側を丸める（タグは必ず残す）。"""
    suffix = f"\n\n{hashtags}"
    if len(content) + len(suffix) > 500:
        content = content[:500 - len(suffix) - 1] + "…"
    return content + suffix


def cta_line_for_cycle(history_count):
    """14投稿サイクルで、1コメ目に載せるCTAリンク行を返す（通常回は空文字）。
    余り0=Gumroad / 余り7=Substack（従来の本文CTAと同じ周期）。"""
    cycle = history_count % 14
    if cycle == 0:
        return GUMROAD_LINE
    if cycle == 7:
        return SUBSTACK_LINE
    return ""
```

- [ ] **Step 4: 成功確認** → PASS
- [ ] **Step 5: コミット**

```bash
git add ronin/ronin_threads_action.py ronin/tests/test_ronin_threads_action.py
git commit -m "feat(ronin): 本文ビルドとCTAサイクルを実装しCTAを1コメ目へ移行"
```

### Task 8: メインフロー改造（engagement分岐・1コメ目・--dry-run）

**Files:**
- Modify: `ronin/ronin_threads_action.py`（`post_sequential`を`post_once`に作り直し、`main`から旧最適化分岐を外す）
- Test: `ronin/tests/test_ronin_threads_action.py`（dry-run統合テスト追記）

- [ ] **Step 1: 失敗するテスト（dry-run）を追記**

```python
def test_dry_runは教え投稿の本文と1コメ目を組み立てAPIを呼ばない(capsys, tmp_path, monkeypatch):
    # 進捗ファイルをテンポラリに差し替え（history_count=0 → teaching, CTA=Gumroad）
    prog = tmp_path / "prog.json"
    prog.write_text('{"index": 0, "engagement_index": 0, "history": []}', encoding="utf-8")
    monkeypatch.setattr(action, "PROGRESS_FILE", str(prog))

    # 教え投稿の在庫はcwdに依存しないようモックする（threads_posts.jsonを読みに行かせない）
    monkeypatch.setattr(action, "flatten_posts",
                        lambda: [{"day": 1, "type": "morning", "content": "Be here now."}])

    called = {"post": False}

    def fail_post(*a, **k):
        called["post"] = True
        raise AssertionError("dry-runでAPIを呼んではいけない")

    monkeypatch.setattr(action, "post_to_threads", fail_post)
    action.post_once(dry_run=True)

    out = capsys.readouterr().out
    assert called["post"] is False          # APIは呼ばれない
    assert "DRY-RUN" in out                  # dry-run表示が出る
    assert "1コメ目" in out or "seed" in out.lower()  # 1コメ目も組み立てる
```

- [ ] **Step 2: 失敗確認** → FAIL（`post_once`未定義 等）

- [ ] **Step 3: 実装**

`post_sequential()` 関数全体を、次の `post_once(dry_run=False)` に置き換える:

```python
def post_once(dry_run=False):
    """1回分の投稿を行う。
    - 4投稿に1回はengagement投稿、それ以外は教えの投稿
    - 本文にCTAリンクは入れず、公開直後に「1コメ目」を自動返信する
    - dry_run=True なら組み立て結果を表示するだけでAPIも保存もしない
    """
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    print(f"=== Ronin自動投稿: {now}{' [DRY-RUN]' if dry_run else ''} ===")

    progress = load_progress()
    teaching_posts = flatten_posts()
    history_count = len(progress.get("history", []))

    # 今回の種別・ハッシュタグ・CTAを決める
    kind = decide_post_kind(history_count)
    hashtags = ronin_hashtags.pick_hashtag_set(history_count)
    cta_line = cta_line_for_cycle(history_count)

    image_url = None  # engagementは画像なし、teachingは後で設定

    if kind == "engagement":
        eng_posts = ronin_engagement.load_engagement_posts()
        if eng_posts:
            eng_index = progress.get("engagement_index", 0)
            eng = ronin_engagement.pick_engagement_post(eng_posts, eng_index)
            content = eng["text"]
            seed_base = eng["seed_comment"]
            label = f"engagement {eng['id']}"
        else:
            # 在庫が無ければ教えの投稿にフォールバック
            print("⚠️ engagement在庫が空。教えの投稿にフォールバックします。")
            kind = "teaching"

    if kind == "teaching":
        index = progress.get("index", 0) % len(teaching_posts)
        post = teaching_posts[index]
        content = post["content"]
        seed_base = ronin_comment_seeder.pick_generic_seed(history_count)
        image_url = get_image_url(post["day"])
        label = f"Day{post['day']:02d} {post['type']}"

    # 本文（CTA無し・ハッシュタグ付き）と1コメ目を組み立てる
    full_text = build_full_text(content, hashtags)
    seed_text = ronin_comment_seeder.build_seed_comment(seed_base, cta=cta_line)

    print(f"種別: {kind} / {label} / タグ: {hashtags}")
    print(f"本文(先頭80字): {full_text[:80]}...")
    print(f"1コメ目(seed): {seed_text[:80]}...")

    if dry_run:
        print("=== DRY-RUN 完了（投稿も保存もしていません）===")
        return

    # 本投稿
    post_id = post_to_threads(full_text, image_url=image_url)
    print(f"✅ 本投稿成功（ID: {post_id}）")

    # 1コメ目を自動返信（失敗しても本投稿は成功扱い）
    try:
        reply_id = post_to_threads(seed_text, reply_to_id=post_id)
        print(f"✅ 1コメ目シード成功（ID: {reply_id}）")
    except Exception as e:
        print(f"⚠️ 1コメ目シード失敗（本投稿は成功済み・スキップ）: {e}")

    # 進捗を進める（種別ごとにインデックスを別管理）
    if kind == "engagement":
        progress["engagement_index"] = progress.get("engagement_index", 0) + 1
    else:
        progress["index"] = (progress.get("index", 0) + 1) % len(teaching_posts)

    progress.setdefault("history", []).append({
        "date": now,
        "kind": kind,
        "label": label,
        "post_id": post_id,
    })
    now_iso = datetime.now(timezone.utc).isoformat()
    save_progress(progress, last_posted_at=now_iso)
    print("=== 完了 ===")
```

次に `main()` を、旧 `should_use_optimization`/`post_optimized`/`post_sequential` 分岐を外して `post_once` を呼ぶ形に置き換える:

```python
def main():
    """メイン処理: 90分以内に投稿済みならスキップ。--dry-runで実投稿せず確認。"""
    import sys
    dry_run = "--dry-run" in sys.argv

    print(f"=== Ronin自動投稿ヘルスチェック: {datetime.now().strftime('%Y/%m/%d %H:%M')} ===")

    if not dry_run and check_should_skip(skip_minutes=90):
        return  # 直近に投稿済み（重複防止）

    post_once(dry_run=dry_run)
```

> `post_optimized()` と `should_use_optimization()` はもう呼ばれない。今は削除せず残す（将来データが貯まったら型別選択を後付けするため）。ファイル冒頭付近に「# NOTE: post_optimized は現在未使用（反応データが貯まるまで休止）」と1行コメントを付ける。

- [ ] **Step 4: 成功確認**

Run: `pytest ronin/tests/ -v`
Expected: 全PASS

- [ ] **Step 5: 実データでdry-run（API無し・目視確認）**

Run: `cd ronin && python ronin_threads_action.py --dry-run`
Expected: 本文・1コメ目・タグが表示され、`DRY-RUN 完了`で終わる（投稿されない）

- [ ] **Step 6: コミット**

```bash
git add ronin/ronin_threads_action.py ronin/tests/test_ronin_threads_action.py
git commit -m "feat(ronin): メインフロー改造（engagement分岐・1コメ目シード・--dry-run）"
```

---

## Phase 7: コメント誘発コンテンツ30本の生成（Workflow）

### Task 9: engagement投稿を30本生成し在庫へ

> ⚠️ この工程はWorkflowで生成＋品質レビューを回すため**プラン使用量を大きく消費**する。着手直前にユーザーへ確認する。

**Files:**
- Modify: `ronin/ronin_engagement_posts.json`（30本に拡充）

- [ ] **Step 1: 生成基準を確定**
  - 6型を均等配分（each ~5本）: either_or / fill_blank / name_one / hot_take / rank_choose / confession
  - 声: 武士道・禅・戦略／英語／欧米男性向け。1アクションで返信できる締め。
  - 比喩は刀鍛冶・茶道・自然・稲穂などへ分散（samurai/path依存を下げる）。
  - 各 `text`・`seed_comment` は500字以内。`id`は `eng003`〜`eng032`。
  - 既存 `threads_posts.json` の本文と意味重複しない。

- [ ] **Step 2: Workflowで生成→対抗レビュー→重複チェック**
  - 生成エージェントが型ごとに候補を作る → 別エージェントが「世界観/英語の自然さ/返信誘発力」で対抗採点 → 合格分だけ採用。
  - 採用分を `ronin_engagement_posts.json` の `posts` 配列へ追記（eng001/eng002は残す）。

- [ ] **Step 3: 検証**

Run:
```
cd ronin && python -c "from ronin_engagement import load_engagement_posts, validate_engagement_posts as v; ps=load_engagement_posts(); print('本数:', len(ps)); print(v(ps) or 'OK')"
```
Expected: `本数: 32`（前後可）・`OK`

- [ ] **Step 4: テスト再実行**（在庫差し替えで壊れていないか）

Run: `pytest ronin/tests/ -v`
Expected: 全PASS

- [ ] **Step 5: コミット**

```bash
git add ronin/ronin_engagement_posts.json
git commit -m "content(ronin): コメント誘発engagement投稿を30本追加"
```

---

## Phase 8: 既存重複の解消（要承認）

### Task 10: day43-evening を別フックへ差し替え

> ⚠️ `threads_posts.json` の編集は**ユーザー承認が必須**。編集後 `/validate-threads-posts` を必ず通す。

day18-evening と day43-evening は「規律で始まり、情熱/愛で続く」という同型のメッセージで重複。**day43-evening** を別テーマ（刀鍛冶の比喩・新規）へ差し替える。

- [ ] **Step 1: 現状確認**

day18e:
```
Discipline gets you started.

Passion keeps you going
past the point where discipline gives up.

Find both.
```
day43e（差し替え対象）:
```
Willpower has a limit.

Love keeps you going
when discipline runs out.

Find what you love.
```

- [ ] **Step 2: 差し替え（day43のeveningを置換）**

新 day43-evening 案（刀鍛冶＝研石の比喩・抵抗を歓迎するテーマ・既存と非重複）:
```
A blade is sharpened by what resists it.

Remove all friction from your day
and you stay dull.

Thank the stone.
```

`ronin/threads_posts.json` の day43 エントリの `evening` をこの文字列に置き換える（朝・他Dayは触らない）。

- [ ] **Step 3: 重複チェック**

Run: `/validate-threads-posts`
Expected: 重複エラー0件

- [ ] **Step 4: コミット**

```bash
git add threads_posts.json
git commit -m "content(ronin): day43-eveningを別フックへ差し替え（重複解消）"
```

---

## Phase 9: 統合検証と本番投入

### Task 11: ローカル単発ライブテスト → mainマージ

> ⚠️ 実投稿（@RoninWordsに本物の投稿＋1コメ目が出る）。**ユーザー承認を得てから**実行する。

- [ ] **Step 1: dry-run最終確認**

Run: `cd ronin && python ronin_threads_action.py --dry-run`
Expected: 本文・1コメ目・タグが正しく組み上がる

- [ ] **Step 2: 単発ライブ（90分スキップを一時回避して1回だけ投稿）**

`.env` の `RONIN_THREADS_ACCESS_TOKEN`/`RONIN_THREADS_USER_ID` を使い、`main()`は90分スキップに当たる可能性があるため `post_once(dry_run=False)` を直接1回呼ぶ:

Run:
```
cd ronin && python -c "import ronin_threads_action as a; a.post_once(dry_run=False)"
```
Expected: 本投稿成功＋1コメ目成功のログ。@RoninWordsで本投稿の直下に1コメ目が付いているのを目視確認。

- [ ] **Step 3: 全テスト最終確認**

Run: `pytest ronin/tests/ -v`
Expected: 全PASS

- [ ] **Step 4: mainへマージ（本番反映）**

```bash
git checkout main
git pull --rebase origin main
git merge --no-ff feature/ronin-reach-boost -m "feat(ronin): reach加速（engagement投稿・動的タグ・1コメ目シード・分析修正）"
git push
```
> push後、次のGitHub Actions実行（ET 8:00/12:30/18:00/20:00）から新ロジックで自動投稿される。

### Task 12: 記録の更新

**Files:**
- Modify: `TODO.md`（ronin改善セクションの該当項目を`[x]`へ）
- Modify: `learning/learning_notes.md`（新スクリプトを一覧へ追記）

- [ ] **Step 1: TODO.md更新**
  - 「ronin_analyzer『現在: 0日』問題」を`[x]`に
  - 「反応の良かった投稿パターンを分析する」近辺にengagement/1コメ目導入を追記
- [ ] **Step 2: learning_notes.md に `ronin_hashtags.py` / `ronin_engagement.py` / `ronin_comment_seeder.py` を追記**
- [ ] **Step 3: コミット**

```bash
git add TODO.md learning/learning_notes.md
git commit -m "docs(ronin): reach加速の実装をTODO/学習ノートに反映"
git push
```

---

## 完了の定義（Done）

- `pytest ronin/tests/` が全PASS。
- `--dry-run` で本文（CTAリンク無し・ローテタグ付き）と1コメ目（型対応の問い＋CTAサイクル時リンク）が組み上がる。
- 単発ライブで本投稿直下に1コメ目が付くことを目視確認。
- engagement在庫が30本以上＋`validate_engagement_posts`がOK。
- day43-evening差し替え後 `/validate-threads-posts` が重複0件。
- mainマージ＆push済み。次の自動投稿から新ロジック稼働。

## スコープ外（この計画でやらない）

- 既存400本のリライト（day43-evening除く）。
- データ駆動の型別投稿選択（反応が貯まってから後付け）。
- 手動リプライ運用・X/LinkedIn/Instagramの同等改修。
