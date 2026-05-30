# skin Threads バズ追撃ボーナス投稿 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** skin Threads で前日に反応が跳ねた日だけ、翌 JST 20:00 にボーナス投稿を1本だけ自動追撃する。

**Architecture:** Phase 0 で反応データ収集バグ（`threads` キー走査・取得件数不足）を直して `posts_history` を埋め戻す。Phase 1 で純関数トリガー `should_fire_bonus` と専用エントリポイント `--bonus` を `skin_threads_action.py` に足し、新ワークフロー `skin_threads_bonus.yml` から起動する。通常4枠の `main()` 経路と進捗キー（特に `last_posted_at`）には一切触れず、進行中の A/B 検証（〜2026-06-06）を完全に独立させる。

**Tech Stack:** Python 3.12 / requests / Threads Graph API v1.0 / GitHub Actions / pytest

---

## 守るべき制約（全タスク共通・最優先）

- **A/B検証（〜2026-06-06）を絶対に汚さない。** これが最重要。
- `last_posted_at` を**読まない・書かない**。これを更新すると通常の 21:30 枠が `check_should_skip(skip_minutes=90)` で「直前に投稿済み」と誤判定してスキップし、A/B検証に穴が空く。ボーナスは `save_progress(progress)` を**引数なし**で呼ぶ（`save_progress` は `last_posted_at=None` のとき同キーを書かない実装＝`skin/skin_threads_action.py:311-318` で確認済み）。
- `daily_index` / `ab_index_per_theme` / `ab_results` / `flip_ab_variant` に触れない・呼ばない。
- `progress.json` 系（`skin_threads_progress.json`・`skin_analytics.json`）は GitHub Actions が書き換える → **手動編集禁止**。新キーは `.get()` で安全に読む。
- ワークフロー新規追加・投稿JSON新規追加は**ユーザー承認が必要**（CLAUDE.md「実行前に必ず確認」）。該当タスクに ⚠️ を明記。
- 既存の `threads_post.yml`（通常4枠）と `skin_analytics_daily.yml` の挙動には**手を加えない**。
- 各行に初心者向け日本語コメントを付ける。変数名・関数名は略さない英単語にする。

---

## File Structure

| ファイル | 操作 | 責務 | フェーズ |
|----------|------|------|----------|
| `skin/skin_data_collector.py` | Modify | 投稿照合を `threads_a`+`threads_b` 走査に修正・`limit:100` 追加 | Phase 0 |
| `skin/tests/test_skin_data_collector.py` | Create | 収集の純関数 `match_day_and_type` / `build_fetch_params` の単体テスト | Phase 0 |
| `skin/skin_analytics.json` | （手動実行で埋め戻し・直接編集しない） | 反応データ履歴 | Phase 0 |
| `skin/skin_threads_action.py` | Modify | 定数・`should_fire_bonus`・`bonus_main`・`--bonus` を追加 | Phase 1 |
| `skin/tests/test_skin_threads_bonus.py` | Create | 発火判定 `should_fire_bonus` の単体テスト | Phase 1 |
| `skin/skin_threads_bonus_posts.json` | Create | ボーナス専用の弾プール | Phase 1 |
| `skin/skin_threads_progress.json` | （新キー `bonus_index`・`last_bonus_date` をコードが追記・手動編集しない） | 進捗 | Phase 1 |
| `.github/workflows/skin_threads_bonus.yml` | Create | 発火ワークフロー（JST 20:00） | Phase 1 |

**触らない:** `.github/workflows/threads_post.yml`、`.github/workflows/skin_analytics_daily.yml`。

---

## Phase 0: 反応データ収集バグの修正（前提）

Phase 0 を先に直さないと、ボーナスのトリガーに使う反応データが埋まらない。Phase 1 より**必ず先**に実施する。

### Task 0.1: 投稿照合を threads_a + threads_b 走査に修正

**Files:**
- Create: `skin/tests/test_skin_data_collector.py`
- Modify: `skin/skin_data_collector.py:105-152`（`identify_day_and_type` から純関数 `match_day_and_type` を抽出）

**背景:** 現状 `skin/skin_data_collector.py:118` が存在しない `threads` キーを走査しているため全件スキップされ、`posts_history` が凍結している。現在の投稿JSONは `threads_a` / `threads_b` 構造。照合ロジックを純関数に切り出してテスト可能にし、両キーを走査するよう直す。

- [ ] **Step 1: 失敗するテストを書く**

`skin/tests/test_skin_data_collector.py` を新規作成する（既存 `skin/tests/test_skin_threads_action.py` のヘッダ作法をミラー）。

```python
"""skin_data_collector.py の投稿照合ロジックの単体テスト。"""
# pytestを使って純関数の挙動を確認するファイル（APIは叩かない）
import sys
from pathlib import Path

# skin/ 配下を import path に追加する
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_data_collector import match_day_and_type


def test_match_day_and_type_finds_post_in_threads_a():
    # threads_a 側の朝投稿（index 0）を正しく morning と判定できることを確認
    posts_data = {
        "threads_a": [
            {"id": 5, "theme": "腸活", "posts": ["朝の投稿テキストです", "2本目の投稿", "夜の投稿テキスト"]},
        ],
        "threads_b": [],
    }
    result = match_day_and_type(posts_data, "朝の投稿テキストです")
    assert result == (5, "腸活", "morning")


def test_match_day_and_type_finds_post_in_threads_b():
    # threads_b 側の3本目（index 2）を evening と判定し、threads_b も走査することを確認
    posts_data = {
        "threads_a": [],
        "threads_b": [
            {"id": 7, "theme": "睡眠", "posts": ["b朝1", "b朝2", "夜の睡眠投稿テキスト"]},
        ],
    }
    result = match_day_and_type(posts_data, "夜の睡眠投稿テキスト")
    assert result == (7, "睡眠", "evening")


def test_match_day_and_type_returns_none_when_no_match():
    # どのパターンにも一致しなければ (None, None, None) を返すことを確認
    posts_data = {
        "threads_a": [{"id": 1, "theme": "X", "posts": ["abc"]}],
        "threads_b": [],
    }
    result = match_day_and_type(posts_data, "存在しないテキスト")
    assert result == (None, None, None)
```

- [ ] **Step 2: テストを実行して失敗を確認**

Run: `pytest skin/tests/test_skin_data_collector.py -v`
Expected: FAIL（`ImportError: cannot import name 'match_day_and_type'`）

- [ ] **Step 3: 最小実装（純関数を抽出して両キー走査に修正）**

`skin/skin_data_collector.py:105-152`（`identify_day_and_type` の定義全体）を、以下の2関数に置き換える。純関数 `match_day_and_type` を新設し、`identify_day_and_type` はファイル読み込みだけ担当して純関数に委譲する。

```python
def match_day_and_type(posts_data, post_text):
    """投稿テキストを posts_data の投稿パターンと照合し (Day番号, テーマ, 朝夜) を返す純関数。
    threads_a と threads_b の両方を走査する（旧 threads キーは存在しないため全件スキップしていたバグの修正）。
    一致しなければ (None, None, None) を返す。
    """
    # threads_a と threads_b を1つのリストに連結して両方走査する
    all_threads = posts_data.get("threads_a", []) + posts_data.get("threads_b", [])

    # 比較対象テキストの最初の50文字を取り出す（正確な比較用）
    post_text_normalized = post_text[:50].strip()

    # 各投稿パターンを順番にチェックする
    for thread_info in all_threads:
        day_num = thread_info.get("id")            # このパターンのDay番号
        theme_name = thread_info.get("theme", "")  # このパターンのテーマ名
        post_texts = thread_info.get("posts", [])  # このパターンの投稿文リスト

        for index, stored_text in enumerate(post_texts):
            # 保存テキストの最初の50文字を取り出す
            stored_text_normalized = stored_text[:50].strip()

            # 最初の50文字が完全一致したら、その投稿に確定する
            if post_text_normalized == stored_text_normalized:
                # 投稿位置で朝夜を判定する（index 0,1 = 朝 / それ以降 = 夜）
                post_type = "morning" if index <= 1 else "evening"
                return (day_num, theme_name, post_type)

    # どのパターンにも一致しなかった場合
    return (None, None, None)


def identify_day_and_type(post_text):
    """
    投稿テキストをskin_threads_posts.jsonの投稿パターンと照合して
    Day番号とテーマを特定する関数（ファイル読み込み担当・照合は match_day_and_type に委譲）
    """

    try:
        # skin_threads_posts.jsonから投稿パターンを読み込む
        with open(POSTS_FILE, "r", encoding="utf-8") as f:
            posts_data = json.load(f)

        # 読み込んだデータを純関数に渡して照合する
        return match_day_and_type(posts_data, post_text)

    except FileNotFoundError:
        print(f"⚠️  警告: {POSTS_FILE}が見つかりません")
        return (None, None, None)
    except json.JSONDecodeError:
        print(f"⚠️  警告: {POSTS_FILE}のJSON解析に失敗しました")
        return (None, None, None)
    except Exception as e:
        print(f"⚠️  警告: identify_day_and_type実行中にエラーが発生しました: {str(e)}")
        return (None, None, None)
```

- [ ] **Step 4: テストを実行して成功を確認**

Run: `pytest skin/tests/test_skin_data_collector.py -v`
Expected: PASS（3件すべて）

- [ ] **Step 5: コミット**

```bash
git add skin/tests/test_skin_data_collector.py skin/skin_data_collector.py
git commit -m "fix(skin): データ収集の投稿照合を threads_a+threads_b 走査に修正"
```

---

### Task 0.2: API取得件数に limit=100 を追加

**Files:**
- Modify: `skin/tests/test_skin_data_collector.py`（テスト追記・import 更新）
- Modify: `skin/skin_data_collector.py:50-53`（`params` を純関数 `build_fetch_params` に切り出し `limit` 追加）

**背景:** `fetch_threads_data` が取得件数を絞らず、デフォルトの最近25件しか取れない（過去12日＝約50件に届かない）。`params` を純関数に切り出して `"limit": 100` を足す。

- [ ] **Step 1: context7 で Threads API の limit 上限を確認**

Run（MCP）:
- `mcp__context7__resolve-library-id` に `libraryName: "Meta Threads API"`
- `mcp__context7__query-docs` に `query: "GET /{threads-user-id}/threads pagination limit maximum value"`

Expected: `limit` の最大が 100。**もし上限が 100 未満だった場合のみ**、以降の `100` をその上限値に下げる（それ以外は `100` のまま進める）。

- [ ] **Step 2: 失敗するテストを書く**

`skin/tests/test_skin_data_collector.py` の import 行を更新し、末尾にテストを2件追記する。

import 行を次に変更:

```python
from skin_data_collector import match_day_and_type, build_fetch_params
```

ファイル末尾に追記:

```python
def test_build_fetch_params_includes_limit_100():
    # 取得パラメータに limit=100 が含まれることを確認（25件しか取れないバグの修正）
    params = build_fetch_params()
    assert params["limit"] == 100


def test_build_fetch_params_keeps_insights_fields():
    # insights のメトリクス指定とアクセストークンが維持されていることを確認
    params = build_fetch_params()
    assert "insights.metric(likes,replies,shares,views)" in params["fields"]
    assert "access_token" in params
```

- [ ] **Step 3: テストを実行して失敗を確認**

Run: `pytest skin/tests/test_skin_data_collector.py -v`
Expected: FAIL（`ImportError: cannot import name 'build_fetch_params'`）

- [ ] **Step 4: 最小実装（params を純関数化して limit を追加）**

`skin/skin_data_collector.py` の `calculate_engagement_rate` 定義の**直前**（現状の85行目あたり・空行2つの位置）に純関数を新設する。

```python
def build_fetch_params():
    """Threads API に送る取得パラメータを組み立てる純関数。
    limit=100 で過去分の取りこぼし（デフォルト25件）を防ぐ。
    """
    return {
        # 取得したいデータフィールド（反応メトリクスを insights で取得）
        "fields": "id,text,timestamp,insights.metric(likes,replies,shares,views)",
        # APIキー（.envから読み込んだもの）
        "access_token": THREADS_ACCESS_TOKEN,
        # 1回に取得する件数の上限（過去分も拾えるよう多めに取る）
        "limit": 100,
    }
```

続けて `fetch_threads_data` 内の `params` 辞書（`skin/skin_data_collector.py:50-53`）を純関数呼び出しに置き換える。

置換前:

```python
        # APIに送るパラメータ（取得したいデータフィールドを指定）
        params = {
            "fields": "id,text,timestamp,insights.metric(likes,replies,shares,views)",
            "access_token": THREADS_ACCESS_TOKEN
        }
```

置換後:

```python
        # APIに送るパラメータを純関数で組み立てる（limit=100 で取りこぼし防止）
        params = build_fetch_params()
```

- [ ] **Step 5: テストを実行して成功を確認**

Run: `pytest skin/tests/test_skin_data_collector.py -v`
Expected: PASS（5件すべて）

- [ ] **Step 6: コミット**

```bash
git add skin/tests/test_skin_data_collector.py skin/skin_data_collector.py
git commit -m "fix(skin): データ収集に limit=100 を追加し過去分の取りこぼしを防止"
```

---

### Task 0.3: 反応データの埋め戻し（運用作業・コミットなし）⚠️ 要ユーザー承認

**Files:** なし（GitHub Actions の手動実行のみ。`skin_analytics.json` は直接編集しない）

**背景:** バグ修正後、`skin_analytics_daily.yml` を1回手動実行して過去分（5/18〜5/29）を埋める。`post_id` 重複排除は既存実装（`skin/skin_data_collector.py:230-234`）が担保する。

⚠️ これはライブのワークフロー起動。実行前にユーザー承認を取る。

- [ ] **Step 1: データ収集ワークフローを手動実行**

```bash
gh workflow run skin_analytics_daily.yml
```

- [ ] **Step 2: 実行完了を確認**

```bash
gh run list --workflow=skin_analytics_daily.yml --limit 1
```
Expected: 最新 run の status が `completed` / conclusion が `success`

- [ ] **Step 3: 最新化されたデータを取得して中身を確認**

```bash
git pull origin main
jq '[.posts_history[].posted_at] | max' skin/skin_analytics.json
```
Expected: `2026-05-29` 以降の日付が返る（履歴が 5/29 まで埋まっている）

- [ ] **Step 4: 重複が無いことを確認**

```bash
jq '[.posts_history[].post_id] | (length) - (unique | length)' skin/skin_analytics.json
```
Expected: `0`（重複ゼロ）

---

## Phase 1: ボーナス投稿本体

Phase 0 完了（`posts_history` が 5/29 まで埋まっている）を確認してから着手する。

### Task 1.1: ボーナス用の定数と timedelta import を追加

**Files:**
- Modify: `skin/skin_threads_action.py:10`（import に `timedelta` 追加）
- Modify: `skin/skin_threads_action.py:40`（`HASHTAGS` の直後に定数追加）

- [ ] **Step 1: import に timedelta を追加**

`skin/skin_threads_action.py:10` を置き換える。

置換前:

```python
from datetime import datetime, timezone  # 今の日時とタイムゾーンを扱う道具
```

置換後:

```python
from datetime import datetime, timezone, timedelta  # 今の日時・タイムゾーン・時間差を扱う道具
```

- [ ] **Step 2: ボーナス用の定数を追加**

`skin/skin_threads_action.py:40` の `HASHTAGS` 行の**直後**（`# ===== note宣伝投稿の設定 =====` の直前）に挿入する。

挿入する内容（`HASHTAGS` 行のあとに続けて配置）:

```python

# ===== ボーナス投稿の設定（バズ追撃・案A クリーン加速） =====
BONUS_POSTS_FILE = "skin_threads_bonus_posts.json"  # ボーナス専用の弾プール（通常投稿と被らない）
BONUS_ANALYTICS_FILE = "skin_analytics.json"        # 反応データ履歴（収集スクリプトが更新）
BONUS_MIN_VIEWS = 15          # views 足切り（低viewでengagement_rateが暴れるのを排除）
BONUS_MIN_LIKES = 2           # likes 足切り（今の自己ベスト級）
BONUS_LOOKBACK_DAYS = 14      # 相対平均を取る期間（日）
BONUS_RATE_MULTIPLIER = 1.5   # 相対閾値の倍率（直近平均 × この値を超えたら発火）
BONUS_MAX_PER_DAY = 1         # 1日に撃つ上限本数（= +1本）
```

- [ ] **Step 3: 既存テストが壊れていないことを確認**

Run: `pytest skin/tests/ -v`
Expected: PASS（既存テストすべて。import エラーや構文エラーが無いこと）

- [ ] **Step 4: コミット**

```bash
git add skin/skin_threads_action.py
git commit -m "feat(skin): ボーナス投稿用の定数と timedelta import を追加"
```

---

### Task 1.2: 発火判定の純関数 should_fire_bonus を追加

**Files:**
- Create: `skin/tests/test_skin_threads_bonus.py`
- Modify: `skin/skin_threads_action.py`（`save_progress` 定義の直後・`skin/skin_threads_action.py:319` 付近に追加）

**背景:** 「JST前日に投稿したもののうち、`views>=15` かつ `likes>=2` かつ `engagement_rate >= 直近14日平均×1.5` を1本でも満たせば True」を判定する純関数。投稿APIは叩かない。

- [ ] **Step 1: 失敗するテストを書く**

`skin/tests/test_skin_threads_bonus.py` を新規作成する。算数は事前検証済み（コメントに内訳を明記）。

```python
"""skin_threads_action.py のボーナス発火判定 should_fire_bonus の単体テスト。"""
# pytestを使って純関数の挙動を確認するファイル（投稿APIは叩かない）
import sys
from pathlib import Path
from datetime import date

# skin/ 配下を import path に追加する
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_threads_action import should_fire_bonus


def test_should_fire_bonus_true_when_yesterday_spiked():
    # 前日(5/15)が views19/likes2/rate10.53。直近平均=(0.0+4.0+2.5+10.53)/4=4.2575、閾値=6.386 < 10.53 → True
    posts_history = [
        {"posted_at": "2026-05-12T03:00:00+0000", "views": 10, "likes": 0, "engagement_rate": 0.0},
        {"posted_at": "2026-05-13T03:00:00+0000", "views": 25, "likes": 1, "engagement_rate": 4.0},
        {"posted_at": "2026-05-14T03:00:00+0000", "views": 40, "likes": 1, "engagement_rate": 2.5},
        {"posted_at": "2026-05-15T04:01:07+0000", "views": 19, "likes": 2, "engagement_rate": 10.53},
    ]
    today = date(2026, 5, 16)
    assert should_fire_bonus(posts_history, today) is True


def test_should_fire_bonus_false_when_likes_too_low():
    # 前日 likes1 で足切り脱落。閾値=(1.0+1.0+10.53)/3*1.5=6.265 < 10.53 だが likes1<2 → False
    posts_history = [
        {"posted_at": "2026-05-13T03:00:00+0000", "views": 30, "likes": 0, "engagement_rate": 1.0},
        {"posted_at": "2026-05-14T03:00:00+0000", "views": 30, "likes": 0, "engagement_rate": 1.0},
        {"posted_at": "2026-05-15T04:01:07+0000", "views": 19, "likes": 1, "engagement_rate": 10.53},
    ]
    today = date(2026, 5, 16)
    assert should_fire_bonus(posts_history, today) is False


def test_should_fire_bonus_false_when_views_too_low():
    # 前日 views14 で足切り脱落。likes3・rate21.43 は満たすが views14<15 → False
    posts_history = [
        {"posted_at": "2026-05-13T03:00:00+0000", "views": 30, "likes": 0, "engagement_rate": 1.0},
        {"posted_at": "2026-05-14T03:00:00+0000", "views": 30, "likes": 0, "engagement_rate": 1.0},
        {"posted_at": "2026-05-15T04:01:07+0000", "views": 14, "likes": 3, "engagement_rate": 21.43},
    ]
    today = date(2026, 5, 16)
    assert should_fire_bonus(posts_history, today) is False


def test_should_fire_bonus_false_when_below_relative_threshold():
    # 前日 rate5.0。直近平均=(8.0+9.0+10.0+5.0)/4=8.0、閾値=12.0 > 5.0 → 相対未達で False
    posts_history = [
        {"posted_at": "2026-05-12T03:00:00+0000", "views": 100, "likes": 8, "engagement_rate": 8.0},
        {"posted_at": "2026-05-13T03:00:00+0000", "views": 100, "likes": 9, "engagement_rate": 9.0},
        {"posted_at": "2026-05-14T03:00:00+0000", "views": 100, "likes": 10, "engagement_rate": 10.0},
        {"posted_at": "2026-05-15T04:01:07+0000", "views": 100, "likes": 5, "engagement_rate": 5.0},
    ]
    today = date(2026, 5, 16)
    assert should_fire_bonus(posts_history, today) is False


def test_should_fire_bonus_false_when_history_empty():
    # 履歴が空なら安全側で False
    posts_history = []
    today = date(2026, 5, 16)
    assert should_fire_bonus(posts_history, today) is False
```

- [ ] **Step 2: テストを実行して失敗を確認**

Run: `pytest skin/tests/test_skin_threads_bonus.py -v`
Expected: FAIL（`ImportError: cannot import name 'should_fire_bonus'`）

- [ ] **Step 3: 最小実装（純関数を追加）**

`skin/skin_threads_action.py` の `save_progress` 定義の終わり（`skin/skin_threads_action.py:318` の次・空行2つの位置）に、ヘルパーと純関数を追加する。

```python
def _parse_posted_at_to_jst_date(posted_at):
    """UTCの投稿時刻文字列（例 "2026-05-15T04:01:07+0000"）をJSTの日付に変換する。
    Threads APIのタイムスタンプはUTCなので、+9時間してから日付を取り出す。
    """
    # "+0000" は Python が読めるよう "+00:00" に直す
    normalized = posted_at.replace("+0000", "+00:00")
    # UTCのdatetimeに変換する
    dt_utc = datetime.fromisoformat(normalized)
    # 9時間足してJSTにする
    dt_jst = dt_utc + timedelta(hours=9)
    # 日付部分だけ返す
    return dt_jst.date()


def should_fire_bonus(posts_history, today):
    """ボーナス投稿を撃つべきか判定する純関数。
    JST前日の投稿のうち views>=BONUS_MIN_VIEWS かつ likes>=BONUS_MIN_LIKES かつ
    engagement_rate >= 直近BONUS_LOOKBACK_DAYS日平均 × BONUS_RATE_MULTIPLIER を
    1本でも満たせば True。満たさなければ False（安全側 = 撃たない）。
    today は date 型（JST基準の今日）。
    """
    # JSTの前日を求める
    yesterday = today - timedelta(days=1)

    # 各投稿に JST日付を付けたリストを作る（壊れた posted_at はスキップ）
    dated_posts = []
    for post in posts_history:
        posted_at = post.get("posted_at", "")
        if not posted_at:
            continue
        try:
            jst_date = _parse_posted_at_to_jst_date(posted_at)
        except (ValueError, TypeError):
            # 日付として解釈できないものは無視する
            continue
        dated_posts.append((jst_date, post))

    # 前日に投稿したものだけ抜き出す
    yesterday_posts = [post for (jst_date, post) in dated_posts if jst_date == yesterday]

    # 前日の投稿が無ければ撃たない
    if not yesterday_posts:
        return False

    # 直近BONUS_LOOKBACK_DAYS日のengagement_rateを集める（views=0/rate=0も母集団に含める）
    window_start = today - timedelta(days=BONUS_LOOKBACK_DAYS)
    recent_rates = [
        post.get("engagement_rate", 0)
        for (jst_date, post) in dated_posts
        if window_start <= jst_date <= today
    ]

    # 母集団が空なら撃たない（ゼロ除算回避・安全側）
    if not recent_rates:
        return False

    # 相対閾値 = 直近平均 × 倍率
    average_rate = sum(recent_rates) / len(recent_rates)
    relative_threshold = average_rate * BONUS_RATE_MULTIPLIER

    # 前日の投稿のうち1本でも3条件すべてを満たせば撃つ（any判定）
    for post in yesterday_posts:
        views = post.get("views", 0)
        likes = post.get("likes", 0)
        rate = post.get("engagement_rate", 0)
        if views >= BONUS_MIN_VIEWS and likes >= BONUS_MIN_LIKES and rate >= relative_threshold:
            return True

    # どれも満たさなければ撃たない
    return False
```

- [ ] **Step 4: テストを実行して成功を確認**

Run: `pytest skin/tests/test_skin_threads_bonus.py -v`
Expected: PASS（5件すべて）

- [ ] **Step 5: コミット**

```bash
git add skin/tests/test_skin_threads_bonus.py skin/skin_threads_action.py
git commit -m "feat(skin): ボーナス発火判定の純関数 should_fire_bonus を追加"
```

---

### Task 1.3: 弾読み込みとボーナス投稿処理 bonus_main を追加

**Files:**
- Modify: `skin/skin_threads_action.py`（Task 1.2 で追加した `should_fire_bonus` の直後に追加）

**背景:** 判定→投稿→進捗更新までを1関数にまとめる。投稿APIを叩く副作用があるため単体テストは付けず、Task 1.6 のワークフロー手動実行で検証する（YAGNI）。`save_progress(progress)` を**引数なし**で呼び、`last_posted_at` を絶対に書かない。

- [ ] **Step 1: 弾読み込みと bonus_main を実装**

`skin/skin_threads_action.py` の `should_fire_bonus` 定義の直後（空行2つの位置）に追加する。

```python
def load_bonus_posts():
    """ボーナス専用の弾プールを読み込んで投稿リストを返す。"""
    # ボーナス弾のJSONを開く
    with open(BONUS_POSTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # bonus_posts キーのリストを返す（無ければ空リスト）
    return data.get("bonus_posts", [])


def bonus_main():
    """ボーナス投稿のメイン処理。
    A/B検証を汚さないため main() 経路には一切入らず、last_posted_at も読み書きしない。
    更新するのは bonus_index と last_bonus_date の専用キーだけ。
    """
    # JSTの今日を求める（UTC + 9時間）
    now_jst = datetime.now(timezone.utc) + timedelta(hours=9)
    today_jst = now_jst.date()
    today_str = today_jst.isoformat()

    # 進捗ファイルを読み込む
    progress = load_progress()

    # 今日すでにボーナスを撃っていれば二重投稿防止で終了する
    if progress.get("last_bonus_date") == today_str:
        print(f"⏭️  本日({today_str})は既にボーナス投稿済みのため終了します")
        return

    # 反応データが無ければ判定できないのでスキップする
    if not os.path.exists(BONUS_ANALYTICS_FILE):
        print(f"⚠️  {BONUS_ANALYTICS_FILE} が見つかりません。ボーナス判定をスキップします")
        return

    # 反応データ履歴を読み込む
    with open(BONUS_ANALYTICS_FILE, "r", encoding="utf-8") as f:
        analytics = json.load(f)
    posts_history = analytics.get("posts_history", [])

    # 発火条件を満たさなければ投稿せず終了する（安全側）
    if not should_fire_bonus(posts_history, today_jst):
        print(f"📊 本日({today_str})はボーナス発火条件を満たしません。投稿せず終了します")
        return

    # ボーナス弾を読み込む
    bonus_posts = load_bonus_posts()
    if not bonus_posts:
        print("⚠️  ボーナス弾プールが空です。投稿せず終了します（弾の補充が必要）")
        return

    # 次に使う弾の番号を取り出す（無ければ0から）
    bonus_index = progress.get("bonus_index", 0)

    # 弾を撃ち尽くしていたら補充までスキップする（安全側）
    if bonus_index >= len(bonus_posts):
        print(f"⚠️  ボーナス弾を撃ち尽くしました(bonus_index={bonus_index})。補充するまでスキップします")
        return

    # 今回使う弾を選ぶ
    chosen = bonus_posts[bonus_index]
    post_text = chosen.get("text", "")

    # 弾にテキストが無ければスキップする
    if not post_text:
        print(f"⚠️  bonus_index={bonus_index} の弾にテキストがありません。スキップします")
        return

    # ハッシュタグを末尾に付けて投稿文を組み立てる
    full_text = post_text + HASHTAGS

    # ボーナス投稿を実行する（単発投稿・画像なし）
    print(f"🚀 ボーナス投稿を実行します（bonus_index={bonus_index}）")
    post_id = post_to_threads(full_text)
    print(f"✅ ボーナス投稿完了: post_id={post_id}")

    # 進捗を更新する（専用キーだけ。last_posted_at は絶対に書かない＝A/B非干渉）
    progress["bonus_index"] = bonus_index + 1
    progress["last_bonus_date"] = today_str
    save_progress(progress)
    print(f"💾 進捗を更新しました: bonus_index={bonus_index + 1}, last_bonus_date={today_str}")
```

- [ ] **Step 2: import・構文が壊れていないことを確認**

Run: `pytest skin/tests/ -v`
Expected: PASS（既存テスト＋Phase 0/1.2 のテストすべて。`bonus_main`/`load_bonus_posts` は import 可能で構文エラーが無いこと）

- [ ] **Step 3: コミット**

```bash
git add skin/skin_threads_action.py
git commit -m "feat(skin): ボーナス投稿処理 bonus_main と弾読み込みを追加"
```

---

### Task 1.4: --bonus エントリポイントを追加

**Files:**
- Modify: `skin/skin_threads_action.py:701-708`（`__main__` ブロック）

- [ ] **Step 1: --bonus 分岐を最初に追加**

`skin/skin_threads_action.py:701-708` を置き換える。`--bonus` を**最初の分岐**にする。

置換前:

```python
if __name__ == "__main__":
    import sys
    if "--paid-note-promo" in sys.argv:
        paid_note_promo_main()
    elif "--note-promo" in sys.argv:
        note_promo_main()
    else:
        main()
```

置換後:

```python
if __name__ == "__main__":
    import sys
    if "--bonus" in sys.argv:
        # ボーナス投稿モード（通常4枠とは完全独立・A/Bに触れない）
        bonus_main()
    elif "--paid-note-promo" in sys.argv:
        paid_note_promo_main()
    elif "--note-promo" in sys.argv:
        note_promo_main()
    else:
        main()
```

- [ ] **Step 2: 引数なしで通常モードが壊れていないことを確認**

Run: `pytest skin/tests/ -v`
Expected: PASS（全テスト）

- [ ] **Step 3: コミット**

```bash
git add skin/skin_threads_action.py
git commit -m "feat(skin): --bonus エントリポイントを追加"
```

---

### Task 1.5: ボーナス専用の弾プール skin_threads_bonus_posts.json を追加

**Files:**
- Create: `skin/skin_threads_bonus_posts.json`

**背景:** 通常投稿（`threads_a`/`threads_b`）と絶対に被らない単発の弾を4本用意する。ハッシュタグはコード側（`bonus_main`）で `HASHTAGS` を付けるので、ここには**インラインのハッシュタグを入れない**。

- [ ] **Step 1: 弾プールを作成**

`skin/skin_threads_bonus_posts.json` を新規作成する。

```json
{
  "bonus_posts": [
    {
      "id": 1,
      "text": "肌のために「足す」より先に「引く」。\n\n夜のアイス\n寝る前のコーヒー\n小腹の菓子パン\n\nこの3つを1週間やめるだけで、肌の調子は驚くほど変わります。\n\n高い化粧水を買う前に、まず引き算から。"
    },
    {
      "id": 2,
      "text": "便秘が続くと肌が荒れるのは気のせいじゃないです。\n\n腸に溜まった老廃物→血液に乗る→肌に出る。\n\n対策はシンプルで、1日1.5Lの水。\n\n朝コップ1杯から始めると、お通じも肌も整っていきます。"
    },
    {
      "id": 3,
      "text": "5000円の化粧水より、23時就寝のほうが肌に効きます。\n\n肌が生まれ変わるのは寝ている間。\n\n夜更かしを続けたままスキンケアにお金をかけても、穴の空いたバケツに水を注ぐようなものです。\n\nまず寝る。話はそれから。"
    },
    {
      "id": 4,
      "text": "ニキビができる場所には意味があります。\n\nおでこ→胃腸の疲れ\nほほ→糖質のとりすぎ\nあご・口まわり→ホルモン・睡眠不足\n\n同じ場所に繰り返すなら、それは肌からのサイン。\n\nどこにできやすいですか？"
    }
  ]
}
```

- [ ] **Step 2: 投稿重複チェック（重複NGの担保）**

Run: `/validate-threads-posts`
Expected: 重複なしで PASS（ボーナス弾は通常投稿と別ファイルなので原理的に被らないが、念のため通す）

- [ ] **Step 3: 弾の本数を確認**

```bash
python -c "import json; print(len(json.load(open('skin/skin_threads_bonus_posts.json'))['bonus_posts']), '件')"
```
Expected: `4 件`

- [ ] **Step 4: コミット**

```bash
git add skin/skin_threads_bonus_posts.json
git commit -m "feat(skin): ボーナス専用の弾プール skin_threads_bonus_posts.json を追加"
```

---

### Task 1.6: 発火ワークフロー skin_threads_bonus.yml を追加 ⚠️ 要ユーザー承認

**Files:**
- Create: `.github/workflows/skin_threads_bonus.yml`

**背景:** JST 20:00（UTC 11:00）に1日1回起動し、`--bonus` を走らせる。`threads_post.yml`（`skin/.github/workflows/threads_post.yml` ＝ skin 4枠）の構造をミラーし、concurrency group だけ専用にする。

⚠️ ワークフローの新規追加＋ライブ自動投稿の起動。`git push` 前にユーザー承認を取る（CLAUDE.md「GitHub Actionsワークフローの大きな書き換え」「自動投稿スクリプト」）。

- [ ] **Step 1: ワークフローを作成**

`.github/workflows/skin_threads_bonus.yml` を新規作成する。

```yaml
# skin_threads_bonus.yml
# GitHub Actionsのワークフローファイル
# 1日1回 JST 20:00 に起動し、前日の反応が跳ねていればボーナス投稿を1本だけ撃つ

name: skin Threads ボーナス投稿

on:
  schedule:
    # JST 20:00 = UTC 11:00（通常4枠 18:30/21:30 の隙間。前後90分ずつ空く位置）
    - cron: '0 11 * * *'
  workflow_dispatch:  # 手動でも実行できるようにする（テスト用）

# 同じグループ名のジョブは同時に1つだけ動く（二重起動・push競合を防ぐ）
concurrency:
  group: skin-threads-bonus  # ボーナス専用グループ（投稿系・分析系と競合しない）
  cancel-in-progress: false  # 実行中のジョブを止めず、後から来たジョブを待たせる

jobs:
  bonus-post:
    runs-on: ubuntu-latest  # GitHubのサーバーで動かす
    env:
      FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true  # Node.js 24を使う（Node.js 20廃止対応）
    permissions:
      contents: write  # git pushに必要な書き込み権限

    steps:
      # Step 1: リポジトリのファイルをダウンロードする
      - name: リポジトリをチェックアウト
        uses: actions/checkout@v4

      # Step 2: Pythonをセットアップする
      - name: Python 3.12 をセットアップ
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # Step 3: 必要なライブラリをインストールする
      - name: ライブラリをインストール
        run: pip install requests

      # Step 4: 進捗ファイルをキャッシュから復元する（bonus_index・last_bonus_date を引き継ぐ）
      - name: 進捗ファイルをキャッシュから復元
        uses: actions/cache@v4
        with:
          path: skin/skin_threads_progress.json
          key: skin-threads-progress-${{ github.run_id }}
          restore-keys: |
            skin-threads-progress-

      # Step 5: ボーナス投稿を判定して撃つ
      - name: ボーナス投稿
        env:
          THREADS_ACCESS_TOKEN: ${{ secrets.THREADS_ACCESS_TOKEN }}
          THREADS_USER_ID: ${{ secrets.THREADS_USER_ID }}
        run: cd skin && python skin_threads_action.py --bonus

      # Step 6: 更新した進捗ファイルをキャッシュに保存する
      - name: 進捗ファイルをキャッシュに保存
        uses: actions/cache@v4
        with:
          path: skin/skin_threads_progress.json
          key: skin-threads-progress-${{ github.run_id }}

      # Step 7: 進捗ファイルをGitにコミット＆プッシュする
      - name: 進捗ファイルをGitにコミット＆プッシュ
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add skin/skin_threads_progress.json
          if ! git diff --staged --quiet; then
            git commit -m "自動同期: skin Threadsボーナス進捗更新"
            for i in 1 2 3; do
              git pull --rebase origin main && git push && break
              echo "push失敗 リトライ $i/3..."
              sleep 5
            done
          fi
```

- [ ] **Step 2: YAML構文を確認**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/skin_threads_bonus.yml')); print('YAML OK')"
```
Expected: `YAML OK`

- [ ] **Step 3: コミット**

```bash
git add .github/workflows/skin_threads_bonus.yml
git commit -m "feat(skin): ボーナス投稿の発火ワークフロー skin_threads_bonus.yml を追加"
```

- [ ] **Step 4: push（⚠️ ユーザー承認後）**

```bash
git push origin main
```

- [ ] **Step 5: 手動実行で動作確認**

```bash
gh workflow run skin_threads_bonus.yml
gh run list --workflow=skin_threads_bonus.yml --limit 1
```
Expected: run が `completed`。発火条件を満たさなければ「投稿せず終了」のログが出る（正常）。

- [ ] **Step 6: A/B非干渉を確認（最重要）**

手動実行後、進捗ファイルで `last_posted_at` が**変わっていない**ことを確認する。

```bash
git pull origin main
git log -1 --stat -- skin/skin_threads_progress.json
jq '{bonus_index, last_bonus_date, last_posted_at}' skin/skin_threads_progress.json
```
Expected: 変化したのは `bonus_index`・`last_bonus_date` のみ。`last_posted_at` は手動実行前と同じ値のまま（A/B検証の 21:30 枠スキップ判定に影響なし）。

---

## Self-Review

### 1. Spec coverage（設計書の各節 → タスク対応）

| 設計書 § | 内容 | 対応タスク |
|----------|------|-----------|
| §2 Phase 0 bug1 | `threads` → `threads_a`+`threads_b` 走査 | Task 0.1 |
| §2 Phase 0 bug2 | `limit:100` 追加・context7 で上限確認 | Task 0.2（Step 1 で確認） |
| §2 埋め戻し | `skin_analytics_daily.yml` 手動実行・重複排除・5/29まで | Task 0.3 |
| §3-1 トリガー | 3条件AND・前日抽出・14日平均×1.5・安全側 | Task 1.2（`should_fire_bonus`） |
| §3-2 本数刻み | +1本のみ・最低4本維持 | Task 1.1（`BONUS_MAX_PER_DAY=1`）＋通常枠不変 |
| §3-3 弾調達 | 専用プール・被らない・尽きたらスキップ・`bonus_index` | Task 1.5＋Task 1.3（尽きたらスキップ） |
| §3-4 A/B非干渉 | `--bonus`独立・`last_posted_at`等に触れない | Task 1.3（`save_progress(progress)`）＋Task 1.4＋Task 1.6 Step 6 |
| §3-5 発火 | 新ワークフロー・JST20:00・専用concurrency・dispatch | Task 1.6 |
| §3-6 二重投稿防止 | `last_bonus_date`==今日でスキップ・concurrency | Task 1.3＋Task 1.6 |
| §3-7 テスト | 純関数・pytest・APIは叩かない | Task 0.1/0.2/1.2 |
| §4 調整可能な定数 | 5定数をファイル先頭 | Task 1.1 |
| §5 スコープ外 | ページネーション等作らない | 全タスクで非対象（YAGNI遵守） |
| §6 触るファイル一覧 | 7ファイル | File Structure 表と一致 |

→ ギャップなし。設計書の全要件にタスクが対応。

### 2. Placeholder scan

「TBD」「TODO」「適切に実装」「Task N と同様」「テストは上記のとおり書く」等の曖昧記述なし。全コードステップに実コードを記載。→ クリーン。

### 3. Type consistency

- `match_day_and_type(posts_data, post_text) -> (day, theme, post_type)` — Task 0.1 定義、`identify_day_and_type` から委譲呼び出し。整合。
- `build_fetch_params() -> dict` — Task 0.2 定義、`fetch_threads_data` で呼び出し。整合。
- `should_fire_bonus(posts_history, today: date) -> bool` — Task 1.2 定義、Task 1.3 `bonus_main` で `today_jst`（date型）を渡して呼ぶ。整合。
- `_parse_posted_at_to_jst_date(posted_at) -> date` — Task 1.2 内ヘルパー、`should_fire_bonus` 内で使用。整合。
- `load_bonus_posts() -> list` / `bonus_main()` — Task 1.3 定義、Task 1.4 `__main__` から呼ぶ。整合。
- 定数名 `BONUS_MIN_VIEWS`/`BONUS_MIN_LIKES`/`BONUS_LOOKBACK_DAYS`/`BONUS_RATE_MULTIPLIER`/`BONUS_MAX_PER_DAY`/`BONUS_POSTS_FILE`/`BONUS_ANALYTICS_FILE` — Task 1.1 で定義、Task 1.2/1.3 で同名使用。整合。
- `save_progress(progress)` 引数なし呼び出し — `skin/skin_threads_action.py:311` の `save_progress(progress, last_posted_at=None)` シグネチャと整合（`last_posted_at` 不変）。

→ 不整合なし。

---

## 決定事項メモ

- **ハッシュタグ付与**: ボーナス弾には入れず `bonus_main` で `HASHTAGS` を付ける（通常投稿と同じタグ運用）。タグを変えたい場合は弾側に直書きしてコード側付与を外す調整が可能。
- **Phase 0 の純関数抽出**: 「既存コードの修正時は関係ない部分を変えない」と TDD（テスト先行）の両立のため、照合とパラメータ生成だけを純関数（`match_day_and_type`/`build_fetch_params`）に切り出し、API を叩かずにテストする。`identify_day_and_type` の try/except 構造は維持。
- **`bonus_main` の単体テスト無し**: 投稿API副作用があり、判定の核は `should_fire_bonus` で網羅済み。YAGNI に従いワークフロー手動実行（Task 1.6）で検証する。
- **cache の restore-keys を `threads_post.yml` と共有**（`skin-threads-progress-`）: 同じ `skin_threads_progress.json` を復元するため意図的に共有。`bonus_index`/`last_bonus_date` は通常枠が触らないキーなので衝突しない。
- **`BONUS_MIN_LIKES` 引き上げ**: A/B検証終了（6/6）後、反応が育ったら基準を厳しくできる（設計書 §4）。
