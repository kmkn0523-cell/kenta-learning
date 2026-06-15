# skin Threads リプライ・エンジン Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 公式 Threads API の `keyword_search` でニッチ投稿を見つけ、テンプレ返信を全自動で送る GitHub Actions 常駐エンジンを作る。

**Architecture:** 純粋関数（分類・選別・テンプレ合成・状態管理）を `skin/skin_reply_engine.py` に集約し pytest でテスト。ネットワーク I/O（検索・返信）は薄いラッパーにして main() から呼ぶ。返信送信は既存 `skin_threads_action.post_to_threads(reply_to_id=...)` を再利用。状態は `skin/skin_reply_history.json` に保存し GitHub Actions のキャッシュ＋コミットで永続化。

**Tech Stack:** Python 3.12 / requests / pytest / GitHub Actions cron。LLM 不使用（テンプレのみ）。

---

## ファイル構成

- 作成: `skin/skin_reply_engine.py` — エンジン本体（純粋関数＋main）
- 作成: `skin/skin_reply_engine_config.json` — キーワード・上限・スリープ設定
- 作成: `skin/skin_reply_history.json` — 実行時に自動生成される状態ファイル（初期はGit管理外でも可、初回はエンジンが作る）
- 作成: `skin/tests/test_skin_reply_engine.py` — 純粋関数のテスト
- 作成: `.github/workflows/skin_threads_reply_engine.yml` — cron ワークフロー
- 参照（変更しない）: `skin/skin_threads_action.py`（`post_to_threads`）/ `skin/skin_comment_templates.py`（`COMMENT_TEMPLATES`,`GENERIC_TEMPLATES`）/ `skin/skin_reply_hunter.py`（`KEYWORD_MAP`）
- 追記: `learning/learning_notes.md`（新規スクリプト一覧へ1行）

状態ファイルのスキーマ（全タスクで共通・固定）:
```json
{
  "date": "2026-06-15",
  "count_today": 0,
  "replied_post_ids": ["<media_id>"],
  "author_counts": {"<username>": 1},
  "recent_replies": ["<送信済みの合成文>"]
}
```
検索結果 post の正規化スキーマ（全タスク共通）:
```python
{"id": "<media_id>", "text": "<本文>", "author": "<username>", "timestamp": "<ISO8601>"}
```

---

## Task 0: 事前作業（ユーザー手動・コード不要）

**これはコードではなく Kenta 本人が一度だけ行う準備。実装着手前に完了させる。**

- [ ] **Step 1: Threads アプリに keyword_search スコープを追加**

Meta for Developers のダッシュボードで skin の Threads アプリを開き、権限 `threads_keyword_search` を追加する。
参考: https://developers.facebook.com/docs/threads/keyword-search/

- [ ] **Step 2: トークンを再発行**

`threads_keyword_search` を含めてアクセストークンを再発行する。手順は `docs/threads_token_renewal.md` を踏襲。

- [ ] **Step 3: トークンを `.env` と GitHub Secrets に登録**

再発行したトークンを `.env` の `THREADS_ACCESS_TOKEN` に上書き保存（`.env` を触るので Kenta が手動で実施）。同じ値を GitHub リポジトリの Secrets `THREADS_ACCESS_TOKEN` にも更新。

- [ ] **Step 4: 有効化スイッチ用のリポジトリ変数を作成**

GitHub リポジトリの Settings → Secrets and variables → Actions → Variables に、名前 `SKIN_REPLY_ENGINE_ENABLED`、値 `false` の変数を作る（テスト完了まで false。後で true に変える）。

- [ ] **Step 5: keyword_search のレスポンス形を実機確認**

ターミナルで以下を実行し、返ってくる JSON の `data[]` に `id` `text` `username` `timestamp` が含まれるか目視確認する（フィールド名が違えば Task 9 のコードを実機に合わせる）。
```bash
curl -s "https://graph.threads.net/v1.0/keyword_search?q=%E8%85%B8%E6%B4%BB&search_type=RECENT&fields=id,text,username,timestamp&access_token=YOUR_TOKEN" | head -c 1500
```
Expected: `{"data":[{"id":"...","text":"...","username":"...","timestamp":"..."}, ...]}`

---

## Task 1: 設定ファイルを作る

**Files:**
- Create: `skin/skin_reply_engine_config.json`

- [ ] **Step 1: 設定ファイルを作成**

```json
{
  "my_username": "skin_reset_jp",
  "keywords": ["腸活", "大人ニキビ", "肌荒れ", "インナーケア", "睡眠 肌", "食事 肌", "便秘 肌", "乾燥肌", "ニキビ 改善", "腸活 肌"],
  "daily_cap": 25,
  "per_run": 4,
  "max_per_author_per_day": 1,
  "min_post_length": 15,
  "max_urls": 1,
  "recent_window": 60,
  "min_sleep_seconds": 20,
  "max_sleep_seconds": 90
}
```

- [ ] **Step 2: コミット**

```bash
git add skin/skin_reply_engine_config.json
git commit -m "feat: skin リプライ・エンジンの設定ファイル追加"
```

---

## Task 2: 日本語判定とURL数のヘルパー（TDD）

**Files:**
- Create: `skin/skin_reply_engine.py`
- Test: `skin/tests/test_skin_reply_engine.py`

- [ ] **Step 1: 失敗するテストを書く**

`skin/tests/test_skin_reply_engine.py`:
```python
# test_skin_reply_engine.py
# skin_reply_engine.py の純粋ロジックをテストする（ネットワーク・対話は対象外）
# 実行: pytest skin/tests/test_skin_reply_engine.py

import sys
from pathlib import Path

# skin/ フォルダをimportできる場所に加える（既存テストと同じやり方）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_reply_engine import contains_japanese, count_urls


def test_contains_japanese_日本語ありはTrue():
    assert contains_japanese("腸活を始めた") is True

def test_contains_japanese_英数字だけはFalse():
    assert contains_japanese("hello 123") is False

def test_count_urls_リンク2本を数える():
    assert count_urls("見てね http://a.com と https://b.com") == 2

def test_count_urls_リンク無しは0():
    assert count_urls("リンクなしの投稿") == 0
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `pytest skin/tests/test_skin_reply_engine.py -v`
Expected: FAIL（`No module named 'skin_reply_engine'`）

- [ ] **Step 3: 最小実装を書く**

`skin/skin_reply_engine.py`:
```python
# skin_reply_engine.py
# skin Threads 自動リプライ・エンジン（GitHub Actions専用・対話なし・全自動）
# keyword_search で見つけたニッチ投稿に、テンプレ返信を自動で送る。
# ★リプライ生成はテンプレのみ（LLM不使用）。固定文連投を避けるため、合成＋連投禁止で署名を薄める。

import json     # 設定・状態ファイルを読み書きする道具
import os       # 環境変数（トークン・有効化スイッチ）を読む道具
import random   # テンプレ選択・スリープ揺らぎ・キーワード順のランダム化に使う道具
import time     # 返信の間に人間らしい待機を入れる道具
from datetime import datetime, timezone, timedelta  # 日本時間で「今日」を求める道具
from pathlib import Path  # ファイルの場所を組み立てる道具

import requests  # Threads API にHTTPリクエストを送る道具


def contains_japanese(text):
    """文字列に日本語（ひらがな・カタカナ・漢字）が含まれるかを返す"""
    for character in text:
        if "぀" <= character <= "ヿ":  # ひらがな・カタカナの範囲
            return True
        if "一" <= character <= "鿿":  # よく使う漢字の範囲
            return True
    return False


def count_urls(text):
    """文字列に含まれるURL（http:// か https://）の本数を数える"""
    return text.count("http://") + text.count("https://")
```

- [ ] **Step 4: テストが通ることを確認**

Run: `pytest skin/tests/test_skin_reply_engine.py -v`
Expected: PASS（4件）

- [ ] **Step 5: コミット**

```bash
git add skin/skin_reply_engine.py skin/tests/test_skin_reply_engine.py
git commit -m "feat: リプライ・エンジンの日本語判定とURL数ヘルパー"
```

---

## Task 3: 投稿のカテゴリ分類（TDD）

**Files:**
- Modify: `skin/skin_reply_engine.py`
- Test: `skin/tests/test_skin_reply_engine.py`

- [ ] **Step 1: 失敗するテストを書く**

`test_skin_reply_engine.py` の import に `classify_category` を加え、テストを追記:
```python
from skin_reply_engine import contains_japanese, count_urls, classify_category


def test_classify_category_腸活文は1():
    assert classify_category("腸活を始めて発酵食品を毎日食べてる") == "1"

def test_classify_category_ニキビ文は4():
    assert classify_category("繰り返すニキビと肌荒れがつらい") == "4"

def test_classify_category_無該当はNone():
    assert classify_category("今日はいい天気で散歩しました") is None
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `pytest skin/tests/test_skin_reply_engine.py -v`
Expected: FAIL（`cannot import name 'classify_category'`）

- [ ] **Step 3: 最小実装を書く**

`skin_reply_engine.py` の import 群の下に追記（既存 `KEYWORD_MAP` を再利用＝DRY）:
```python
# テンプレ集とキーワード対応表は既存モジュールから再利用する。
# 直接実行でも pytest 経由でも動くよう2通り import を試す（既存スクリプトと同じ作法）。
try:
    from skin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES
    from skin_reply_hunter import KEYWORD_MAP
except ImportError:
    from skin.skin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES
    from skin.skin_reply_hunter import KEYWORD_MAP


def classify_category(post_text):
    """投稿本文から最も当てはまるテンプレのカテゴリキー（"1"〜"6"）を返す。
    どのキーワードにも当たらなければ None（汎用テンプレを使う合図）。"""
    text = post_text.lower()
    best_key = None
    best_hits = 0
    for key, words in KEYWORD_MAP.items():
        hits = sum(1 for word in words if word.lower() in text)
        if hits > best_hits:
            best_key = key
            best_hits = hits
    return best_key
```

- [ ] **Step 4: テストが通ることを確認**

Run: `pytest skin/tests/test_skin_reply_engine.py -v`
Expected: PASS（7件）

- [ ] **Step 5: コミット**

```bash
git add skin/skin_reply_engine.py skin/tests/test_skin_reply_engine.py
git commit -m "feat: 投稿カテゴリ分類（KEYWORD_MAP再利用）"
```

---

## Task 4: テンプレ返信の合成（連投禁止）（TDD）

**Files:**
- Modify: `skin/skin_reply_engine.py`
- Test: `skin/tests/test_skin_reply_engine.py`

- [ ] **Step 1: 失敗するテストを書く**

import に `compose_reply` を加え、追記:
```python
import random as _random  # テスト内で決定的な乱数を作るため
from skin_reply_engine import compose_reply, OPENERS
from skin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES


def _all_combos(pool):
    return [opener + body for body in pool for opener in OPENERS]

def test_compose_reply_カテゴリ指定は該当プールから合成される():
    rng = _random.Random(0)
    reply = compose_reply("1", [], rng)
    assert reply in _all_combos(COMMENT_TEMPLATES["1"]["comments"])

def test_compose_reply_Noneは汎用プールから合成される():
    rng = _random.Random(0)
    reply = compose_reply(None, [], rng)
    assert reply in _all_combos(GENERIC_TEMPLATES)

def test_compose_reply_直近に使った文は避ける():
    rng = _random.Random(1)
    combos = _all_combos(COMMENT_TEMPLATES["1"]["comments"])
    recent = combos[:-1]  # 1つだけ残して全部「使用済み」にする
    reply = compose_reply("1", recent, rng)
    assert reply == combos[-1]  # 残った唯一の未使用が選ばれる
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `pytest skin/tests/test_skin_reply_engine.py -v`
Expected: FAIL（`cannot import name 'compose_reply'`）

- [ ] **Step 3: 最小実装を書く**

`classify_category` の下に追記:
```python
# テンプレ本文の前に付ける短い枕詞。先頭の "" は「枕詞なし」。
# 本文×枕詞の組み合わせで母数を増やし、固定文の連投（スパム署名）を避ける。
OPENERS = ["", "わかります。", "それ大事ですよね。", "なるほどです。", "共感します。"]


def compose_reply(category_key, recent_replies, rng):
    """カテゴリに合うテンプレ本文に枕詞を合成して1件の返信文を返す。
    recent_replies（直近で送った合成文）に入っている文は避ける。
    全部使い切っていたら重複を許して選ぶ。rng は random.Random（テストで固定するため）。"""
    pool = COMMENT_TEMPLATES[category_key]["comments"] if category_key else GENERIC_TEMPLATES
    combos = [opener + body for body in pool for opener in OPENERS]
    fresh = [combo for combo in combos if combo not in recent_replies]
    return rng.choice(fresh) if fresh else rng.choice(combos)
```

- [ ] **Step 4: テストが通ることを確認**

Run: `pytest skin/tests/test_skin_reply_engine.py -v`
Expected: PASS（10件）

- [ ] **Step 5: コミット**

```bash
git add skin/skin_reply_engine.py skin/tests/test_skin_reply_engine.py
git commit -m "feat: テンプレ返信の合成（枕詞＋連投禁止）"
```

---

## Task 5: 返信可否フィルタ（TDD）

**Files:**
- Modify: `skin/skin_reply_engine.py`
- Test: `skin/tests/test_skin_reply_engine.py`

- [ ] **Step 1: 失敗するテストを書く**

import に `is_repliable` を加え、追記:
```python
from skin_reply_engine import is_repliable

CONFIG = {"max_per_author_per_day": 1, "min_post_length": 15, "max_urls": 1}

def _fresh_state():
    return {"date": "2026-06-15", "count_today": 0, "replied_post_ids": [], "author_counts": {}, "recent_replies": []}

def _post(**kw):
    base = {"id": "p1", "text": "腸活を始めて肌が変わってきた気がします", "author": "someone", "timestamp": "2026-06-15T00:00:00+0000"}
    base.update(kw)
    return base

def test_is_repliable_通常はTrue():
    assert is_repliable(_post(), "skin_reset_jp", _fresh_state(), CONFIG) is True

def test_is_repliable_自分の投稿はFalse():
    assert is_repliable(_post(author="skin_reset_jp"), "skin_reset_jp", _fresh_state(), CONFIG) is False

def test_is_repliable_返信済みはFalse():
    state = _fresh_state()
    state["replied_post_ids"].append("p1")
    assert is_repliable(_post(), "skin_reset_jp", state, CONFIG) is False

def test_is_repliable_同一著者が上限到達はFalse():
    state = _fresh_state()
    state["author_counts"]["someone"] = 1
    assert is_repliable(_post(), "skin_reset_jp", state, CONFIG) is False

def test_is_repliable_短すぎる投稿はFalse():
    assert is_repliable(_post(text="短い"), "skin_reset_jp", _fresh_state(), CONFIG) is False

def test_is_repliable_日本語なしはFalse():
    assert is_repliable(_post(text="this is an english only post about skin"), "skin_reset_jp", _fresh_state(), CONFIG) is False

def test_is_repliable_URL過多はFalse():
    assert is_repliable(_post(text="腸活いいよ https://a.com https://b.com 見て"), "skin_reset_jp", _fresh_state(), CONFIG) is False
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `pytest skin/tests/test_skin_reply_engine.py -v`
Expected: FAIL（`cannot import name 'is_repliable'`）

- [ ] **Step 3: 最小実装を書く**

`compose_reply` の下に追記:
```python
def is_repliable(post, my_username, state, config):
    """この投稿に返信して良いかを判定する（除外フィルタ）。"""
    if post.get("author") == my_username:  # 自分の投稿には返信しない
        return False
    if post.get("id") in state["replied_post_ids"]:  # 既に返信済み
        return False
    if state["author_counts"].get(post.get("author"), 0) >= config["max_per_author_per_day"]:  # 同一著者の上限
        return False
    text = post.get("text") or ""
    if len(text) < config["min_post_length"]:  # 短すぎる投稿は中身が薄い
        return False
    if not contains_japanese(text):  # 日本語以外（ターゲット外）
        return False
    if count_urls(text) > config["max_urls"]:  # 宣伝色が強い投稿
        return False
    return True
```

- [ ] **Step 4: テストが通ることを確認**

Run: `pytest skin/tests/test_skin_reply_engine.py -v`
Expected: PASS（17件）

- [ ] **Step 5: コミット**

```bash
git add skin/skin_reply_engine.py skin/tests/test_skin_reply_engine.py
git commit -m "feat: 返信可否フィルタ"
```

---

## Task 6: 返信対象の選定（TDD）

**Files:**
- Modify: `skin/skin_reply_engine.py`
- Test: `skin/tests/test_skin_reply_engine.py`

- [ ] **Step 1: 失敗するテストを書く**

import に `select_targets` を加え、追記:
```python
from skin_reply_engine import select_targets

SELECT_CONFIG = {"max_per_author_per_day": 1, "min_post_length": 15, "max_urls": 1, "daily_cap": 25, "per_run": 2}

def test_select_targets_新しい順にper_run件まで返す():
    rng = _random.Random(0)
    posts = [
        _post(id="a", author="u1", timestamp="2026-06-15T01:00:00+0000"),
        _post(id="b", author="u2", timestamp="2026-06-15T03:00:00+0000"),
        _post(id="c", author="u3", timestamp="2026-06-15T02:00:00+0000"),
    ]
    result = select_targets(posts, "skin_reset_jp", _fresh_state(), SELECT_CONFIG, rng)
    assert [p["id"] for p in result] == ["b", "c"]  # 新しい順に2件

def test_select_targets_重複IDは1件に():
    rng = _random.Random(0)
    posts = [_post(id="a", author="u1"), _post(id="a", author="u1")]
    result = select_targets(posts, "skin_reset_jp", _fresh_state(), SELECT_CONFIG, rng)
    assert len(result) == 1

def test_select_targets_日次残量で頭打ち():
    rng = _random.Random(0)
    state = _fresh_state()
    state["count_today"] = 24  # 残り1件（daily_cap=25）
    posts = [_post(id="a", author="u1"), _post(id="b", author="u2")]
    result = select_targets(posts, "skin_reset_jp", state, SELECT_CONFIG, rng)
    assert len(result) == 1
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `pytest skin/tests/test_skin_reply_engine.py -v`
Expected: FAIL（`cannot import name 'select_targets'`）

- [ ] **Step 3: 最小実装を書く**

`is_repliable` の下に追記:
```python
def select_targets(posts, my_username, state, config, rng):
    """検索結果から、今回返信する投稿を選ぶ。
    フィルタ通過 → 重複ID除去 → 新しい順 → （per_run と 日次残量）で頭打ち。"""
    candidates = [p for p in posts if is_repliable(p, my_username, state, config)]
    seen_ids = set()
    unique = []
    for post in candidates:
        if post["id"] in seen_ids:  # 複数キーワードで同じ投稿が来ることがある
            continue
        seen_ids.add(post["id"])
        unique.append(post)
    unique.sort(key=lambda p: p.get("timestamp", ""), reverse=True)  # 新しい順（早押し優先）
    remaining_today = config["daily_cap"] - state["count_today"]  # 今日あと何件送れるか
    limit = max(0, min(config["per_run"], remaining_today))
    return unique[:limit]
```

- [ ] **Step 4: テストが通ることを確認**

Run: `pytest skin/tests/test_skin_reply_engine.py -v`
Expected: PASS（20件）

- [ ] **Step 5: コミット**

```bash
git add skin/skin_reply_engine.py skin/tests/test_skin_reply_engine.py
git commit -m "feat: 返信対象の選定（新しい順・日次残量で頭打ち）"
```

---

## Task 7: 状態の初期化・日付リセット・記録（TDD）

**Files:**
- Modify: `skin/skin_reply_engine.py`
- Test: `skin/tests/test_skin_reply_engine.py`

- [ ] **Step 1: 失敗するテストを書く**

import に追加し、追記:
```python
from skin_reply_engine import new_state, reset_if_new_day, record_reply

REC_CONFIG = {"recent_window": 3}

def test_new_state_初期値():
    state = new_state("2026-06-15")
    assert state == {"date": "2026-06-15", "count_today": 0, "replied_post_ids": [], "author_counts": {}, "recent_replies": []}

def test_reset_if_new_day_日付が違えば初期化():
    old = {"date": "2026-06-14", "count_today": 5, "replied_post_ids": ["x"], "author_counts": {"u": 1}, "recent_replies": ["a"]}
    assert reset_if_new_day(old, "2026-06-15") == new_state("2026-06-15")

def test_reset_if_new_day_同じ日付はそのまま():
    same = {"date": "2026-06-15", "count_today": 5, "replied_post_ids": ["x"], "author_counts": {"u": 1}, "recent_replies": ["a"]}
    assert reset_if_new_day(same, "2026-06-15") is same

def test_record_reply_カウントと履歴が増える():
    state = new_state("2026-06-15")
    record_reply(state, "p1", "u1", "返信文A", REC_CONFIG)
    assert state["count_today"] == 1
    assert state["replied_post_ids"] == ["p1"]
    assert state["author_counts"] == {"u1": 1}
    assert state["recent_replies"] == ["返信文A"]

def test_record_reply_recent_replyはwindow件に保つ():
    state = new_state("2026-06-15")
    for i in range(5):
        record_reply(state, f"p{i}", f"u{i}", f"返信{i}", REC_CONFIG)
    assert state["recent_replies"] == ["返信2", "返信3", "返信4"]  # 直近3件だけ残る
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `pytest skin/tests/test_skin_reply_engine.py -v`
Expected: FAIL（`cannot import name 'new_state'`）

- [ ] **Step 3: 最小実装を書く**

`select_targets` の下に追記:
```python
def new_state(today):
    """その日の空っぽの状態を作る"""
    return {"date": today, "count_today": 0, "replied_post_ids": [], "author_counts": {}, "recent_replies": []}


def reset_if_new_day(state, today):
    """日付が変わっていたら状態を初期化して返す。同じ日ならそのまま返す。"""
    if state.get("date") != today:
        return new_state(today)
    return state


def record_reply(state, post_id, author, reply_text, config):
    """1件返信したことを状態に記録する（重複防止・著者上限・連投禁止の材料）。"""
    state["replied_post_ids"].append(post_id)
    state["author_counts"][author] = state["author_counts"].get(author, 0) + 1
    state["count_today"] += 1
    state["recent_replies"].append(reply_text)
    state["recent_replies"] = state["recent_replies"][-config["recent_window"]:]  # 直近だけ保持
    return state
```

- [ ] **Step 4: テストが通ることを確認**

Run: `pytest skin/tests/test_skin_reply_engine.py -v`
Expected: PASS（25件）

- [ ] **Step 5: コミット**

```bash
git add skin/skin_reply_engine.py skin/tests/test_skin_reply_engine.py
git commit -m "feat: 状態の初期化・日付リセット・返信記録"
```

---

## Task 8: 設定・状態のファイル入出力＋ネットワーク関数（テストなし・コードのみ）

**Files:**
- Modify: `skin/skin_reply_engine.py`

ネットワーク I/O はユニットテスト対象外（Task 0 Step 5 で実機確認済み）。コードを追加する。

- [ ] **Step 1: 定数とファイル入出力・検索関数を追記**

`record_reply` の下に追記:
```python
# -----------------------------------------------
# ファイルの場所・定数（このスクリプトと同じ skin/ にある前提）
# -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "skin_reply_engine_config.json"  # キーワード・上限設定（読むだけ）
STATE_PATH = BASE_DIR / "skin_reply_history.json"          # 状態（読み書き・無ければ初回作成）
DAILY_LOG_PATH = BASE_DIR / "skin_daily_log.md"            # 日次ログ（追記）
JST = timezone(timedelta(hours=9))                         # 日本時間


def load_config():
    """設定ファイルを読み込んで辞書で返す"""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_state(path, today):
    """状態ファイルを読み込む。無ければ空。日付が変わっていれば初期化して返す。"""
    if not os.path.exists(path):
        return new_state(today)
    with open(path, encoding="utf-8") as f:
        state = json.load(f)
    return reset_if_new_day(state, today)


def save_state(path, state):
    """状態ファイルを書き出す"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def search_recent_posts(keyword, token):
    """keyword_search で直近の公開投稿を取得し、正規化した辞書のリストで返す。
    返るキー: id / text / author / timestamp（Task 0 Step 5 で実機確認済みの形）。"""
    url = "https://graph.threads.net/v1.0/keyword_search"
    params = {
        "q": keyword,
        "search_type": "RECENT",
        "fields": "id,text,username,timestamp",
        "access_token": token,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json().get("data", [])
    posts = []
    for item in data:
        posts.append({
            "id": item.get("id"),
            "text": item.get("text") or "",
            "author": item.get("username"),
            "timestamp": item.get("timestamp") or "",
        })
    return posts


def append_daily_log(count, today):
    """その回の返信件数を日次ログに1行追記する"""
    line = f"\n- {today} リプライ・エンジン: {count}件自動返信"
    with open(DAILY_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
```

- [ ] **Step 2: 既存テストが壊れていないことを確認**

Run: `pytest skin/tests/test_skin_reply_engine.py -v`
Expected: PASS（25件のまま）

- [ ] **Step 3: コミット**

```bash
git add skin/skin_reply_engine.py
git commit -m "feat: 設定・状態のファイル入出力とkeyword_search呼び出し"
```

---

## Task 9: main() オーケストレーション＋キルスイッチ

**Files:**
- Modify: `skin/skin_reply_engine.py`

- [ ] **Step 1: main を追記**

`append_daily_log` の下に追記:
```python
def main():
    # キルスイッチ：環境変数が "true" でなければ何もしないで終了
    if os.environ.get("SKIN_REPLY_ENGINE_ENABLED") != "true":
        print("SKIN_REPLY_ENGINE_ENABLED が true でないため停止します。")
        return

    token = os.environ["THREADS_ACCESS_TOKEN"]  # 返信に使うアクセストークン
    config = load_config()
    today = datetime.now(JST).strftime("%Y-%m-%d")
    state = load_state(STATE_PATH, today)

    # 本日の上限に達していたら終了（状態だけ保存して日付リセットを永続化）
    if state["count_today"] >= config["daily_cap"]:
        print("本日の上限に到達済み。")
        save_state(STATE_PATH, state)
        return

    # キーワードをシャッフルして検索（毎回同じ並びにしない）
    keywords = config["keywords"][:]
    random.shuffle(keywords)
    posts = []
    for keyword in keywords:
        try:
            posts.extend(search_recent_posts(keyword, token))
        except Exception as error:  # 1キーワードの失敗で全体を止めない
            print(f"検索失敗 keyword={keyword}: {error}")
        if len(posts) >= config["per_run"] * 5:  # 十分集まったら早めに切り上げる
            break

    rng = random.Random()
    targets = select_targets(posts, config["my_username"], state, config, rng)
    if not targets:
        print("返信対象が見つかりませんでした。")
        save_state(STATE_PATH, state)
        return

    # 返信送信は既存スクリプトを再利用（env必須なので遅延import）
    from skin_threads_action import post_to_threads

    sent = 0
    for post in targets:
        category = classify_category(post["text"])
        reply = compose_reply(category, state["recent_replies"], rng)
        try:
            post_to_threads(reply, reply_to_id=post["id"])
        except Exception as error:  # 1件の失敗で残りを止めない
            print(f"返信失敗 post={post['id']}: {error}")
            continue
        record_reply(state, post["id"], post["author"], reply, config)
        save_state(STATE_PATH, state)  # 1件ごとに保存（途中で落ちても二重返信しない）
        sent += 1
        print(f"返信 {sent}/{len(targets)} → @{post['author']}")
        time.sleep(random.randint(config["min_sleep_seconds"], config["max_sleep_seconds"]))

    append_daily_log(sent, today)
    print(f"完了: {sent} 件返信")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: キルスイッチが効くことを確認（ネットワークに触れない）**

Run: `cd skin && SKIN_REPLY_ENGINE_ENABLED=false python3 skin_reply_engine.py`
Expected: `SKIN_REPLY_ENGINE_ENABLED が true でないため停止します。` と表示され、何も送信しない

- [ ] **Step 3: 全テストが通ることを確認**

Run: `pytest skin/tests/test_skin_reply_engine.py -v`
Expected: PASS（25件）

- [ ] **Step 4: コミット**

```bash
git add skin/skin_reply_engine.py
git commit -m "feat: main()オーケストレーションとキルスイッチ"
```

---

## Task 10: GitHub Actions ワークフロー

**Files:**
- Create: `.github/workflows/skin_threads_reply_engine.yml`

- [ ] **Step 1: ワークフローを作成**

`.github/workflows/skin_threads_reply_engine.yml`:
```yaml
# skin_threads_reply_engine.yml
# skin Threads 自動リプライ・エンジン
# JST 日中に1日6回起動し、1回あたり数件だけ自動返信する（合計が日次上限25の下に収まる設計）

name: skin Threads リプライ・エンジン

on:
  schedule:
    - cron: '15 23 * * *'  # JST 08:15
    - cron: '15 2 * * *'   # JST 11:15
    - cron: '15 5 * * *'   # JST 14:15
    - cron: '15 8 * * *'   # JST 17:15
    - cron: '15 11 * * *'  # JST 20:15
    - cron: '15 13 * * *'  # JST 22:15
  workflow_dispatch:  # 手動実行（テスト用）

concurrency:
  group: skin-threads-reply-engine  # 二重起動・push競合を防ぐ専用グループ
  cancel-in-progress: false

jobs:
  reply-engine:
    runs-on: ubuntu-latest
    permissions:
      contents: write  # 状態ファイルのpushに必要
    steps:
      - name: リポジトリをチェックアウト
        uses: actions/checkout@v4

      - name: Python 3.12 をセットアップ
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: ライブラリをインストール
        run: pip install requests

      - name: 状態ファイルをキャッシュから復元
        uses: actions/cache@v4
        with:
          path: skin/skin_reply_history.json
          key: skin-reply-history-${{ github.run_id }}
          restore-keys: |
            skin-reply-history-

      - name: リプライ・エンジンを実行
        env:
          SKIN_REPLY_ENGINE_ENABLED: ${{ vars.SKIN_REPLY_ENGINE_ENABLED }}
          THREADS_ACCESS_TOKEN: ${{ secrets.THREADS_ACCESS_TOKEN }}
          THREADS_USER_ID: ${{ secrets.THREADS_USER_ID }}
        run: cd skin && python skin_reply_engine.py

      - name: 状態ファイルをキャッシュに保存
        uses: actions/cache@v4
        with:
          path: skin/skin_reply_history.json
          key: skin-reply-history-${{ github.run_id }}

      - name: 状態ファイルをGitにコミット＆プッシュ
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add skin/skin_reply_history.json
          if ! git diff --staged --quiet; then
            git commit -m "自動同期: skin リプライ・エンジン状態更新"
            for i in 1 2 3; do
              git pull --rebase origin main && git push && break
              echo "push失敗 リトライ $i/3..."
              sleep 5
            done
          fi
```

- [ ] **Step 2: YAML構文を確認**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/skin_threads_reply_engine.yml')); print('YAML OK')"`
Expected: `YAML OK`
（`yaml` 未インストールなら `pip install pyyaml` 後に再実行）

- [ ] **Step 3: コミット**

```bash
git add .github/workflows/skin_threads_reply_engine.yml
git commit -m "feat: skin リプライ・エンジンのGitHub Actionsワークフロー"
```

---

## Task 11: 学習ノート追記と本番リハーサル

**Files:**
- Modify: `learning/learning_notes.md`

- [ ] **Step 1: 学習ノートの一覧表に1行追記**

`learning/learning_notes.md` の新規スクリプト一覧へ、既存の書式に合わせて1行追加（例）:
```markdown
| skin_reply_engine.py | skin Threads自動リプライ・エンジン（keyword_searchで見つけた投稿にテンプレ返信） | 2026-06-15 |
```

- [ ] **Step 2: コミット**

```bash
git add learning/learning_notes.md
git commit -m "docs: learning_notesにリプライ・エンジンを追記"
```

- [ ] **Step 3: 本番リハーサル（Kenta が手動・少量で安全確認）**

Task 0 完了後、GitHub の Actions タブから `skin Threads リプライ・エンジン` を `Run workflow`（workflow_dispatch）で1回だけ手動実行する。このとき repo 変数 `SKIN_REPLY_ENGINE_ENABLED` を一時的に `true` にしておく。
実行ログで「返信 1/4 → @… 完了: N 件返信」を確認し、skin の Threads アプリで返信が実際に付いているか・文面が不自然でないかを目視確認する。

- [ ] **Step 4: 本稼働へ**

リハーサルで問題なければ `SKIN_REPLY_ENGINE_ENABLED` を `true` のままにして cron 常駐を開始する。違和感があれば `false` に戻して停止し、テンプレ・キーワードを調整する。

---

## Self-Review（記入済み）

- **Spec coverage:** 発見=Task8/9、選別=Task5/6、テンプレ生成（文脈化＝枕詞合成・連投禁止）=Task4、送信=Task9、記録=Task7/8、スロットル（日次上限・per_run・ランダムスリープ）=Task1/6/9、キルスイッチ=Task9、スケジュール=Task10、事前作業（scope/トークン/変数/実機確認）=Task0、ronin巻き添えリスク=設計書に明記済み（別アカウントのためアカウント単位は安全）。すべて対応タスクあり。
- **Placeholder scan:** 「適切に」「TBD」等の空文言なし。各コードステップに実コードあり。
- **Type consistency:** 状態スキーマ（date/count_today/replied_post_ids/author_counts/recent_replies）と post スキーマ（id/text/author/timestamp）を全タスクで統一。関数名（classify_category / compose_reply / is_repliable / select_targets / new_state / reset_if_new_day / record_reply / load_config / load_state / save_state / search_recent_posts / append_daily_log / main）も一貫。
