# skin Threads 全面リライト 実装計画 (Batch 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** skin Threads自動投稿を216セット（A=108＋B=108）のA/B構造に再編し、Batch 1（テーマ1〜20、40セット、120本）を本番投入する。

**Architecture:** 既存の3本ツリー投稿スクリプトを最小改修してA/B選択ロジックを追加。`skin_threads_posts.json` を `threads_a` / `threads_b` の2配列に再編し、テーマごとの選択状態を `skin_threads_progress.json` で管理。GitHub Actionsの発火頻度を 1日16回 → 4回 に削減してパターン疲労を抑える。

**Tech Stack:** Python 3 / json / requests / GitHub Actions / pytest（テスト導入）

**設計書:** `/home/kenta_kamijyo/docs/superpowers/specs/2026-05-17-skin-threads-rewrite-design.md`

---

## File Structure

### 既存ファイル（書き換え）

| ファイル | 変更内容 |
|---|---|
| `skin/skin_threads_posts.json` | トップキーを `threads` → `threads_a` + `threads_b` に再編。既存108セットを `threads_a` に移行。`threads_b` はBatch 1の20テーマ分のみ投入。残りは空（後続バッチで追加） |
| `skin/skin_threads_progress.json` | `ab_index_per_theme` `ab_results` キー追加 |
| `skin/skin_threads_action.py` | `select_ab_variant()` `load_posts()` 改修 |
| `.github/workflows/skin_threads_post.yml` | cron 発火を `30 * * * *`（16回/日）→ `30 22,3,9,12 * * *` UTC（4回/日 = JST 7:30/12:30/18:30/21:30）に変更 |

### 新規ファイル

| ファイル | 用途 |
|---|---|
| `skin/skin_threads_batch_progress.json` | バッチ進行管理（current_batch、各バッチstatus） |
| `skin/skin_ab_report.py` | A/B検証レポート生成スクリプト |
| `skin/tests/__init__.py` | テストディレクトリマーカー |
| `skin/tests/test_skin_threads_action.py` | A/B選択ロジックの単体テスト |
| `skin/tests/test_skin_ab_report.py` | レポート生成の単体テスト |

### 変更しないファイル

- `skin/skin_data_collector.py`（既存稼働中）
- `skin/skin_analyzer.py`（既存稼働中）
- `skin/skin_optimizer.py`（既存稼働中）
- `.env`（APIキー）

---

## 進行フェーズ概要

1. **インフラ整備** (Task 1〜7): バックアップ、ファイル構造変更、A/Bロジック実装、ワークフロー変更
2. **コンテンツ制作** (Task 8〜12): テーマ1〜20のA+B計40セット（120本）を制作
3. **リリース・検証** (Task 13〜14): Batch 1投入、観測準備

---

## Task 1: Gitタグでバックアップ

**Files:**
- 既存ファイル全てが対象（追跡対象のみ）

- [ ] **Step 1: 作業ブランチ作成（main上で直接作業しない）**

```bash
git checkout main
git pull --ff-only
git checkout -b skin-threads-batch-1
```

- [ ] **Step 2: Batch 1リリース前のロールバックポイントをタグで保存**

```bash
git tag skin-threads-batch-1-before main
git push origin skin-threads-batch-1-before
```

- [ ] **Step 3: タグが打たれたか確認**

Run: `git tag -l "skin-threads-batch-*"`
Expected output: `skin-threads-batch-1-before`

---

## Task 2: skin_threads_posts.json の構造変更

**Files:**
- Modify: `skin/skin_threads_posts.json`

**目的:** 既存108セットの `threads` 配列を `threads_a` にリネームし、空の `threads_b` を追加。Batch 1の本文はTask 8〜11で `threads_b` に投入する（A側は既存維持）。

- [ ] **Step 1: 既存JSONをローカル変数に読み込んで構造を変換するスクリプトを実行**

Run（プロジェクトルートで）:

```bash
python3 - <<'EOF'
import json
from pathlib import Path

src = Path("skin/skin_threads_posts.json")
data = json.loads(src.read_text(encoding="utf-8"))

# 旧構造の確認
assert "threads" in data, "既存のtopキー 'threads' が見つからない"
assert isinstance(data["threads"], list), "'threads' は list である必要がある"
old_count = len(data["threads"])
print(f"既存セット数: {old_count}")

# 新構造に変換
new_data = {
    "threads_a": data["threads"],   # 既存108セットをそのままAに移行
    "threads_b": [],                  # B側は空で開始（Task 8〜11で投入）
}

# 上書き保存（フォーマット維持: 2スペースインデント、UTF-8、ensure_ascii=False）
src.write_text(
    json.dumps(new_data, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"変換完了: threads_a={len(new_data['threads_a'])}, threads_b={len(new_data['threads_b'])}")
EOF
```

Expected output:
```
既存セット数: 108
変換完了: threads_a=108, threads_b=0
```

- [ ] **Step 2: 構造が正しく変わったか目視確認**

Run: `python3 -c "import json; d=json.load(open('skin/skin_threads_posts.json',encoding='utf-8')); print(list(d.keys())); print('A len:', len(d['threads_a'])); print('B len:', len(d['threads_b']))"`

Expected:
```
['threads_a', 'threads_b']
A len: 108
B len: 0
```

- [ ] **Step 3: コミット**

```bash
git add skin/skin_threads_posts.json
git commit -m "refactor: split skin_threads_posts into threads_a/threads_b"
```

---

## Task 3: skin_threads_progress.json のスキーマ拡張

**Files:**
- Modify: `skin/skin_threads_progress.json`

**目的:** `ab_index_per_theme`（テーマごとの次選択）と `ab_results`（テーマごとのスコア集計）を追加。既存の `daily_index` / `history` などは保持。

- [ ] **Step 1: 現状の中身を確認**

Read `skin/skin_threads_progress.json` を Read tool で開いて既存キー一覧を把握。`daily_index`, `ab_next`, `history` などが既にある想定。

- [ ] **Step 2: 拡張スクリプトを実行**

Run（プロジェクトルートで）:

```bash
python3 - <<'EOF'
import json
from pathlib import Path

src = Path("skin/skin_threads_progress.json")
data = json.loads(src.read_text(encoding="utf-8"))

# 新キーがなければ初期化
if "ab_index_per_theme" not in data:
    # Batch 1のテーマ1〜20について "A" でスタート
    data["ab_index_per_theme"] = {str(i): "A" for i in range(1, 109)}

if "ab_results" not in data:
    data["ab_results"] = {
        str(i): {"a_score": 0.0, "b_score": 0.0, "a_posts": 0, "b_posts": 0}
        for i in range(1, 109)
    }

# 旧 ab_next キーは廃止（新ロジックで使わない）
if "ab_next" in data:
    print("旧キー 'ab_next' を削除")
    del data["ab_next"]

src.write_text(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"ab_index_per_theme: {len(data['ab_index_per_theme'])} entries")
print(f"ab_results: {len(data['ab_results'])} entries")
print(f"top keys: {list(data.keys())}")
EOF
```

Expected output（既存キーが残る + 新キーが追加される）:
```
旧キー 'ab_next' を削除
ab_index_per_theme: 108 entries
ab_results: 108 entries
top keys: [..., 'ab_index_per_theme', 'ab_results']
```

- [ ] **Step 3: コミット**

```bash
git add skin/skin_threads_progress.json
git commit -m "feat: extend skin_threads_progress with ab_index_per_theme and ab_results"
```

---

## Task 4: skin_threads_batch_progress.json を新規作成

**Files:**
- Create: `skin/skin_threads_batch_progress.json`

- [ ] **Step 1: ファイル作成（Write tool）**

```json
{
  "current_batch": 1,
  "batches": {
    "1": {
      "themes": "1-20",
      "status": "in_progress",
      "release_date": "2026-05-24",
      "validation_until": "2026-06-06",
      "winner_decided": false
    },
    "2": {
      "themes": "21-40",
      "status": "pending",
      "release_date": "2026-05-31",
      "validation_until": "2026-06-13",
      "winner_decided": false
    },
    "3": {
      "themes": "41-60",
      "status": "pending",
      "release_date": "2026-06-07",
      "validation_until": "2026-06-20",
      "winner_decided": false
    },
    "4": {
      "themes": "61-80",
      "status": "pending",
      "release_date": "2026-06-14",
      "validation_until": "2026-06-27",
      "winner_decided": false
    },
    "5": {
      "themes": "81-100",
      "status": "pending",
      "release_date": "2026-06-21",
      "validation_until": "2026-07-04",
      "winner_decided": false
    },
    "6": {
      "themes": "101-108",
      "status": "pending",
      "release_date": "2026-06-28",
      "validation_until": "2026-07-11",
      "winner_decided": false
    }
  }
}
```

- [ ] **Step 2: コミット**

```bash
git add skin/skin_threads_batch_progress.json
git commit -m "feat: add skin_threads_batch_progress.json"
```

---

## Task 5: skin_threads_action.py に A/B選択ロジック追加（TDD）

**Files:**
- Create: `skin/tests/__init__.py`
- Create: `skin/tests/test_skin_threads_action.py`
- Modify: `skin/skin_threads_action.py`

**目的:** 投稿時に「今日のテーマ」と「A/B選択」を決め、投稿後に当該テーマのA/Bフラグを反転させる。

**設計:**
- `pick_today_theme(daily_index: int) -> int`: テーマ番号（1〜108）を返す。`daily_index % 108 + 1`。
- `select_ab_variant(progress: dict, theme_id: int) -> str`: `progress["ab_index_per_theme"][str(theme_id)]` を返す。キー欠落時は "A" デフォルト。
- `flip_ab_variant(progress: dict, theme_id: int) -> None`: `ab_index_per_theme[str(theme_id)]` を A↔B 反転。
- `load_posts_for_variant(data: dict, theme_id: int, variant: str) -> dict`: `data["threads_a"]` or `data["threads_b"]` から該当セット取得。Bが未投入のテーマは A にフォールバック。

- [ ] **Step 1: テストディレクトリ初期化**

Create file `skin/tests/__init__.py` with empty content.

- [ ] **Step 2: 失敗テストを書く**

Create file `skin/tests/test_skin_threads_action.py`:

```python
"""skin_threads_action.py の A/B選択ロジックの単体テスト。"""
# pytestを使って関数の挙動を確認するファイル
import sys
from pathlib import Path

# skin/ 配下を import path に追加
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_threads_action import (
    pick_today_theme,
    select_ab_variant,
    flip_ab_variant,
    load_posts_for_variant,
)


def test_pick_today_theme_returns_1_when_index_0():
    # daily_index=0 のとき テーマ1 が返ることを確認
    assert pick_today_theme(0) == 1


def test_pick_today_theme_wraps_at_108():
    # daily_index=108 のとき テーマ1 にループすることを確認
    assert pick_today_theme(108) == 1


def test_pick_today_theme_returns_108():
    # daily_index=107 のとき テーマ108 が返ることを確認
    assert pick_today_theme(107) == 108


def test_select_ab_variant_returns_stored_value():
    # progress に B が記録されていれば B を返す
    progress = {"ab_index_per_theme": {"5": "B"}}
    assert select_ab_variant(progress, 5) == "B"


def test_select_ab_variant_defaults_to_A_when_missing():
    # キーが無いテーマは A をデフォルトで返す
    progress = {"ab_index_per_theme": {}}
    assert select_ab_variant(progress, 99) == "A"


def test_flip_ab_variant_A_to_B():
    progress = {"ab_index_per_theme": {"3": "A"}}
    flip_ab_variant(progress, 3)
    assert progress["ab_index_per_theme"]["3"] == "B"


def test_flip_ab_variant_B_to_A():
    progress = {"ab_index_per_theme": {"3": "B"}}
    flip_ab_variant(progress, 3)
    assert progress["ab_index_per_theme"]["3"] == "A"


def test_load_posts_for_variant_returns_A_post():
    data = {
        "threads_a": [{"id": 1, "theme": "A1", "posts": ["a1", "a2", "a3"]}],
        "threads_b": [],
    }
    result = load_posts_for_variant(data, theme_id=1, variant="A")
    assert result["theme"] == "A1"


def test_load_posts_for_variant_falls_back_to_A_when_B_empty():
    # B側が空のテーマは A にフォールバック
    data = {
        "threads_a": [{"id": 1, "theme": "A1", "posts": ["a1", "a2", "a3"]}],
        "threads_b": [],
    }
    result = load_posts_for_variant(data, theme_id=1, variant="B")
    assert result["theme"] == "A1"


def test_load_posts_for_variant_returns_B_post_when_available():
    data = {
        "threads_a": [{"id": 1, "theme": "A1", "posts": ["a1", "a2", "a3"]}],
        "threads_b": [{"id": 1, "theme": "B1", "posts": ["b1", "b2", "b3"]}],
    }
    result = load_posts_for_variant(data, theme_id=1, variant="B")
    assert result["theme"] == "B1"
```

- [ ] **Step 3: テスト失敗を確認**

Run: `cd /home/kenta_kamijyo && python3 -m pytest skin/tests/test_skin_threads_action.py -v`
Expected: ImportError または該当関数が未定義であることを示すエラー（FAIL）

- [ ] **Step 4: skin_threads_action.py に4関数を追加**

`skin/skin_threads_action.py` を Read で開いて、既存の関数群の直上（importブロックの直後）に以下を追加（既存ロジックには触れない）:

```python
# ==== A/Bテスト機構（2026-05-18 追加） ====

def pick_today_theme(daily_index: int) -> int:
    # daily_indexから今日のテーマ番号（1〜108）を計算する
    return daily_index % 108 + 1


def select_ab_variant(progress: dict, theme_id: int) -> str:
    # progressから指定テーマのA/B選択状態を取得（無ければA）
    table = progress.get("ab_index_per_theme", {})
    return table.get(str(theme_id), "A")


def flip_ab_variant(progress: dict, theme_id: int) -> None:
    # 指定テーマのA/B選択状態を反転（投稿後に呼ぶ）
    table = progress.setdefault("ab_index_per_theme", {})
    current = table.get(str(theme_id), "A")
    table[str(theme_id)] = "B" if current == "A" else "A"


def load_posts_for_variant(data: dict, theme_id: int, variant: str) -> dict:
    # data["threads_a"] or data["threads_b"] から該当セットを返す
    # 指定variantが空 or テーマ未投入なら反対側にフォールバック
    key_primary = "threads_a" if variant == "A" else "threads_b"
    key_fallback = "threads_b" if variant == "A" else "threads_a"
    for arr_key in (key_primary, key_fallback):
        for entry in data.get(arr_key, []):
            if entry.get("id") == theme_id:
                return entry
    raise ValueError(f"テーマ{theme_id}が両配列に見つからない")
```

- [ ] **Step 5: テスト成功を確認**

Run: `cd /home/kenta_kamijyo && python3 -m pytest skin/tests/test_skin_threads_action.py -v`
Expected: 全10テスト PASS

- [ ] **Step 6: 投稿フロー本体にA/B選択を組み込み**

`skin/skin_threads_action.py` 内の「daily_indexで投稿対象を読み込む」既存ロジックを、新しい4関数を使う形に置き換える。具体的にどのコードを書き換えるかは、Read で既存実装を確認した上でその箇所をEditで書き換える。

書き換えのポイント:
- 旧: `target = data["threads"][daily_index % len(data["threads"])]`
- 新:
  ```python
  theme_id = pick_today_theme(progress["daily_index"])
  variant = select_ab_variant(progress, theme_id)
  target = load_posts_for_variant(data, theme_id, variant)
  ```

投稿成功後、`progress["daily_index"]` を +1 する既存処理の直前に以下を追加:
```python
flip_ab_variant(progress, theme_id)
# A/B結果集計用のpost数カウントもインクリメント
results = progress.setdefault("ab_results", {})
theme_key = str(theme_id)
results.setdefault(theme_key, {"a_score": 0.0, "b_score": 0.0, "a_posts": 0, "b_posts": 0})
results[theme_key]["a_posts" if variant == "A" else "b_posts"] += 1
```

`history` に積む際、既存のキーに加えて `variant` フィールドも書き込む:
```python
history_entry = {
    # ... 既存フィールド ...
    "variant": variant,
    "theme_id": theme_id,
}
```

- [ ] **Step 7: dry-run確認**

`skin_threads_action.py` を実際に呼ばずに、本体のmain処理部に「dry-run用ガード」を追加して構文エラーがないか確認。

Run: `cd /home/kenta_kamijyo && python3 -c "import skin.skin_threads_action"`
Expected: エラーなく終了（実投稿は走らない）

- [ ] **Step 8: コミット**

```bash
git add skin/tests/__init__.py skin/tests/test_skin_threads_action.py skin/skin_threads_action.py
git commit -m "feat: add A/B variant selection to skin_threads_action"
```

---

## Task 6: GitHub Actionsワークフローを 1日4回 に変更

**Files:**
- Modify: `.github/workflows/skin_threads_post.yml`

**目的:** 投稿頻度を 1日16回（毎時30分）→ 1日4回（JST 7:30 / 12:30 / 18:30 / 21:30）に削減。

JSTからUTC換算:
- JST 7:30 = UTC 22:30 (前日)
- JST 12:30 = UTC 3:30
- JST 18:30 = UTC 9:30
- JST 21:30 = UTC 12:30

→ cron文字列: `30 22,3,9,12 * * *`

- [ ] **Step 1: 既存ファイルを Read**

Read `.github/workflows/skin_threads_post.yml` で `cron:` 行を特定。

- [ ] **Step 2: cron行を置換**

Edit でcron行を以下のように変更（旧文字列は実ファイル内容に合わせて Edit する）:

```yaml
on:
  schedule:
    # JST 7:30 / 12:30 / 18:30 / 21:30 の1日4回に変更（2026-05-18 リライト）
    - cron: '30 22,3,9,12 * * *'
  workflow_dispatch:
```

- [ ] **Step 3: ファイルが意図通りに書き換わったか目視確認**

Read `.github/workflows/skin_threads_post.yml` で cron が `30 22,3,9,12 * * *` 1行のみであることを確認。

- [ ] **Step 4: コミット**

```bash
git add .github/workflows/skin_threads_post.yml
git commit -m "chore: reduce skin threads post frequency from 16x to 4x daily"
```

---

## Task 7: skin_ab_report.py を新規作成（TDD）

**Files:**
- Create: `skin/tests/test_skin_ab_report.py`
- Create: `skin/skin_ab_report.py`

**目的:** バッチ検証完了時にA/Bの勝者を判定するレポートを出力。

**仕様:**
- `progress["ab_results"]` を読み、テーマごとに `a_score / max(a_posts,1)` と `b_score / max(b_posts,1)` を計算
- 最低3回ずつ投稿済みのテーマのみ判定対象
- (A平均 - B平均) / max(A,B) >= 0.2 で勝者確定
- 出力: テキスト形式のサマリ

- [ ] **Step 1: 失敗テストを書く**

Create file `skin/tests/test_skin_ab_report.py`:

```python
"""skin_ab_report.py の判定ロジックのテスト。"""
# レポート関数の判定結果を確認するファイル
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_ab_report import judge_theme, generate_report


def test_judge_theme_returns_no_data_when_posts_below_threshold():
    # A=2回・B=3回 → 不足
    result = judge_theme(theme_id=1, a_score=100, b_score=50, a_posts=2, b_posts=3, min_posts=3)
    assert result["verdict"] == "insufficient_data"


def test_judge_theme_returns_A_winner_when_20pct_lead():
    # A平均80・B平均50 → A勝ち
    result = judge_theme(theme_id=1, a_score=240, b_score=150, a_posts=3, b_posts=3, min_posts=3)
    assert result["verdict"] == "A_wins"
    assert result["lead_pct"] >= 0.2


def test_judge_theme_returns_B_winner_when_20pct_lead():
    # A平均50・B平均80 → B勝ち
    result = judge_theme(theme_id=1, a_score=150, b_score=240, a_posts=3, b_posts=3, min_posts=3)
    assert result["verdict"] == "B_wins"


def test_judge_theme_returns_no_diff_when_under_20pct():
    # A平均70・B平均65 → 差なし
    result = judge_theme(theme_id=1, a_score=210, b_score=195, a_posts=3, b_posts=3, min_posts=3)
    assert result["verdict"] == "no_significant_diff"


def test_generate_report_returns_string_with_theme_lines():
    progress = {
        "ab_results": {
            "1": {"a_score": 240.0, "b_score": 150.0, "a_posts": 3, "b_posts": 3},
            "2": {"a_score": 100.0, "b_score": 95.0, "a_posts": 3, "b_posts": 3},
        }
    }
    report = generate_report(progress, themes=[1, 2])
    assert "テーマ1" in report
    assert "テーマ2" in report
    assert "A勝ち" in report or "A_wins" in report
```

- [ ] **Step 2: テスト失敗を確認**

Run: `cd /home/kenta_kamijyo && python3 -m pytest skin/tests/test_skin_ab_report.py -v`
Expected: ImportError（skin_ab_report が未作成のため FAIL）

- [ ] **Step 3: skin_ab_report.py を作成**

Create file `skin/skin_ab_report.py`:

```python
"""skin Threads A/B検証レポート生成スクリプト。

使い方:
    python3 skin_ab_report.py [--batch N]

batchを省略すると skin_threads_batch_progress.json の current_batch を読む。
"""
# A/B結果から勝者を判定してレポートを出力するファイル
import argparse
import json
from pathlib import Path
from typing import Iterable

# プロジェクトルート（このファイルが skin/ 直下にある前提）
ROOT = Path(__file__).resolve().parent
PROGRESS_PATH = ROOT / "skin_threads_progress.json"
BATCH_PATH = ROOT / "skin_threads_batch_progress.json"


def judge_theme(
    theme_id: int,
    a_score: float,
    b_score: float,
    a_posts: int,
    b_posts: int,
    min_posts: int = 3,
) -> dict:
    # 1テーマのA/B結果から勝者を判定する
    if a_posts < min_posts or b_posts < min_posts:
        return {
            "theme_id": theme_id,
            "verdict": "insufficient_data",
            "a_avg": 0.0,
            "b_avg": 0.0,
            "lead_pct": 0.0,
        }

    a_avg = a_score / a_posts
    b_avg = b_score / b_posts
    larger = max(a_avg, b_avg)
    if larger == 0:
        return {
            "theme_id": theme_id,
            "verdict": "no_significant_diff",
            "a_avg": 0.0,
            "b_avg": 0.0,
            "lead_pct": 0.0,
        }

    lead_pct = abs(a_avg - b_avg) / larger
    if lead_pct < 0.2:
        verdict = "no_significant_diff"
    elif a_avg > b_avg:
        verdict = "A_wins"
    else:
        verdict = "B_wins"

    return {
        "theme_id": theme_id,
        "verdict": verdict,
        "a_avg": a_avg,
        "b_avg": b_avg,
        "lead_pct": lead_pct,
    }


def generate_report(progress: dict, themes: Iterable[int]) -> str:
    # テーマ一覧からレポート文字列を生成する
    lines = ["=== A/B検証レポート ==="]
    counts = {"A_wins": 0, "B_wins": 0, "no_significant_diff": 0, "insufficient_data": 0}
    results = progress.get("ab_results", {})

    for theme_id in themes:
        entry = results.get(str(theme_id), {})
        judgement = judge_theme(
            theme_id=theme_id,
            a_score=entry.get("a_score", 0.0),
            b_score=entry.get("b_score", 0.0),
            a_posts=entry.get("a_posts", 0),
            b_posts=entry.get("b_posts", 0),
        )
        counts[judgement["verdict"]] += 1
        label = {
            "A_wins": "A勝ち",
            "B_wins": "B勝ち",
            "no_significant_diff": "差なし",
            "insufficient_data": "データ不足",
        }[judgement["verdict"]]
        lines.append(
            f"テーマ{theme_id}: A={judgement['a_avg']:.1f} B={judgement['b_avg']:.1f} "
            f"→ {label}（差{judgement['lead_pct']*100:.1f}%）"
        )

    lines.append("")
    lines.append(
        f"集計: A勝ち {counts['A_wins']} / B勝ち {counts['B_wins']} / "
        f"差なし {counts['no_significant_diff']} / データ不足 {counts['insufficient_data']}"
    )
    return "\n".join(lines)


def parse_theme_range(themes_str: str) -> list:
    # "1-20" のような文字列をテーマID配列に展開する
    start_str, end_str = themes_str.split("-")
    return list(range(int(start_str), int(end_str) + 1))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=None)
    args = parser.parse_args()

    progress = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    batch_data = json.loads(BATCH_PATH.read_text(encoding="utf-8"))

    batch_id = args.batch or batch_data["current_batch"]
    themes_str = batch_data["batches"][str(batch_id)]["themes"]
    themes = parse_theme_range(themes_str)

    print(f"Batch {batch_id} (テーマ{themes_str}) のレポート:")
    print(generate_report(progress, themes))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: テスト成功を確認**

Run: `cd /home/kenta_kamijyo && python3 -m pytest skin/tests/test_skin_ab_report.py -v`
Expected: 全5テスト PASS

- [ ] **Step 5: 実データで dry-run**

Run: `cd /home/kenta_kamijyo && python3 skin/skin_ab_report.py --batch 1`
Expected:
```
Batch 1 (テーマ1-20) のレポート:
=== A/B検証レポート ===
テーマ1: A=0.0 B=0.0 → データ不足（差0.0%）
...
集計: A勝ち 0 / B勝ち 0 / 差なし 0 / データ不足 20
```
（投稿前なので全てデータ不足が正解）

- [ ] **Step 6: コミット**

```bash
git add skin/skin_ab_report.py skin/tests/test_skin_ab_report.py
git commit -m "feat: add skin_ab_report.py for A/B winner judgement"
```

---

## コンテンツ生成共通ガイドライン（Task 8〜11 で共通）

**文字数規則:**

| 本 | 目安 | 上限 |
|---|---|---|
| 本1（フック） | 100〜200文字 | 500 |
| 本2（本題） | 300〜450文字 | 500 |
| 本3（CTA） | 150〜250文字 | 500 |

**本2の4文構造:**
- A版（原因解説）:
  1. 事実（断定せず「○○の報告がある」表現）
  2. 具体例（日常レベルの例示）
  3. 数字根拠（「研究では○○の傾向が報告されています」）
  4. 読み手への意味（「つまり○○という話です」）
- B版（解決策提示）:
  1. 結論（「○○すれば△△になる可能性があります」）
  2. 3〜5ステップ（①②③で行動を箇条書き）
  3. 数字根拠（「研究では○○と報告されています」）
  4. 今日からの行動（「今日から○○だけでも始められます」）

**フック型テンプレ:**

| 型 | 冒頭スタイル |
|---|---|
| 数字フック | 「N年/N回/N割の○○」など数字で引きをつくる |
| 逆張りフック | 「○○が定説だけど、本当は△△」 |
| エピソードフック | 「私が○年間こうしてきた」「○○だった頃の話」 |

**CTA型テンプレ:**

| 型 | 文末スタイル |
|---|---|
| 保存 | 「読み返したくなったら保存しておいてね」 |
| コメント | 「あなたの○○あったら教えてね」 |
| note誘導 | 「もっと詳しくはプロフィールのnoteへ」 |
| フォロー | 「毎日肌改善のヒントを発信中。続きを受け取りたい人はフォローしておいてね」 |

**ハッシュタグ規則:** 本3末尾にのみ3〜5個。基本3個（`#肌荒れ #大人ニキビ #肌改善`）＋テーマ別キーワード1〜2個

**薬機法ガイドライン:**
- NGワード: 治る・治す・効く・効果がある・完全に・100%・必ず・確実に
- 推奨表現: 「報告がある」「目安」「傾向」「のことが多い」「人多いです」

---

## Task 8: テーマ1〜5 のA+Bパターン制作（30本）

**Files:**
- Modify: `skin/skin_threads_posts.json` (threads_b 配列に追加 + threads_a の該当テーマを差し替え)

**前提:** 既存 threads_a のテーマ1〜5は旧版のまま。Batch 1ではA側もリライトする方針なので、threads_a のid=1〜5 を新A版で**差し替え**、threads_b に新B版を**追加**する。

**テーマ割当（設計書セクション2のローテーション規則を適用）:**

| id | テーマ | フック型 (id%3) | CTA型 (id%4) | A本題切り口 | B本題切り口 |
|---|---|---|---|---|---|
| 1 | 問いかけ型 | 数字(%3==1) | 保存(%4==1) | 原因解説 | 解決策提示 |
| 2 | 腸と肌のつながり | 逆張り(%3==2) | コメント(%4==2) | 原因解説 | 解決策提示 |
| 3 | 砂糖とニキビ | note誘導(%4==3) | note誘導(%4==3) | 原因解説 | 解決策提示 |
| 4 | 洗顔のやりすぎ | 数字(%3==1) | フォロー(%4==0) | 原因解説 | 解決策提示 |
| 5 | 睡眠と肌 | 逆張り(%3==2) | 保存(%4==1) | 原因解説 | 解決策提示 |

※ フック型は `id % 3`: 0→エピソード / 1→数字 / 2→逆張り

- [ ] **Step 1: テーマ1のA版を制作**

新規 `skin/skin_threads_posts.json` の `threads_a[0]`（id=1）を以下フォーマットで上書き:

```json
{
  "id": 1,
  "theme": "問いかけ型",
  "posts": [
    "肌荒れが何年も治らない人、共通点が3つあります。\n\n8年間試してきた中で、これに当てはまる人ほど長引いてました。\n\n①夜更かし\n②甘い飲み物が日課\n③洗顔が雑\n\n3つ全部当てはまる人、続き読んでみて。",
    "肌荒れが慢性化する人ほど、外側のケアばかり強化しがちです。\n\n例えば化粧水を3000円→8000円に変えても、夜更かしと砂糖が続いていれば肌は応えません。\n\n皮膚科の研究では、生活習慣が皮脂分泌に直接影響する報告があります。\n\nつまり「何を塗るか」より「何をやめるか」が先という話です。",
    "読み返したくなったら保存しておいてね。\n\n3つのチェック、1週間意識するだけでも肌のざらつきが落ち着いてくる人多いです。\n\n#肌荒れ #大人ニキビ #肌改善 #生活習慣"
  ]
}
```

- [ ] **Step 2: テーマ1のB版を制作（threads_b に追加）**

`threads_b` 配列に以下を追加:

```json
{
  "id": 1,
  "theme": "問いかけ型",
  "posts": [
    "肌荒れが何年も治らない人、共通点が3つあります。\n\n逆に治った人がやっていた3つを今日まとめます。\n\n①23時前に寝る\n②水を意識して1.5L\n③洗顔は朝はぬるま湯だけ\n\n1つだけでも始めてみて。",
    "肌の回復は「足す」より「整える」が早いです。\n\n例えば睡眠は23時前に布団に入るだけで成長ホルモンの分泌時間に乗れます。\n\n研究では7時間以上の睡眠群は肌バリア機能が高い傾向が報告されています。\n\n「夜サプリより夜の睡眠」が地味だけど一番効くという話です。",
    "読み返したくなったら保存しておいてね。\n\n3つのうち、まず1つだけ。今夜から始められるのは寝る時間です。\n\n#肌荒れ #大人ニキビ #肌改善 #睡眠"
  ]
}
```

- [ ] **Step 3: テーマ2のA版（逆張りフック・コメントCTA・原因解説）**

`threads_a[1]`（id=2）を上書き:

```json
{
  "id": 2,
  "theme": "腸と肌のつながり",
  "posts": [
    "化粧水を変えても肌は治りません。\n\n肌の状態は、顔ではなく腸で決まっているからです。\n\n8年間色んな化粧品を試して気づいたのが、結局腸が荒れてる日は何塗ってもダメだったということ。",
    "腸が荒れると肌が荒れる、これには理由があります。\n\n腸内環境が乱れると、本来便で排出されるはずの老廃物が血液に乗って全身を回ります。\n\n研究では腸内細菌のバランスが乱れた人ほど肌トラブルが多い傾向が報告されています。\n\nつまり肌は腸の鏡という話で、外側だけ磨いても限界があるんです。",
    "あなたの腸活で効いた習慣あったら教えてね。\n\nコメントが他の人の参考になります。\n\n#肌荒れ #大人ニキビ #肌改善 #腸活"
  ]
}
```

- [ ] **Step 4: テーマ2のB版（逆張りフック・コメントCTA・解決策提示）**

`threads_b` 配列に追加:

```json
{
  "id": 2,
  "theme": "腸と肌のつながり",
  "posts": [
    "化粧水を変えても肌は治りません。\n\n肌を変えたいなら、明日からヨーグルトと味噌汁を増やすほうが早いです。\n\n外側より内側、これが本気で大人ニキビが治った人の共通点でした。",
    "腸内環境を整える食習慣は、肌に直接効きます。\n\n発酵食品（ヨーグルト・納豆・味噌・キムチ）を毎日1品ずつ、加えて食物繊維（オートミール・きのこ・海藻）。\n\n研究では発酵食品を3週間以上続けた群で肌のキメ改善が報告されています。\n\n今日から1品増やすだけで2週間後の肌が変わる可能性があります。",
    "あなたが続けてる発酵食品あったら教えてね。\n\n参考にしたい人が多いはず。\n\n#肌荒れ #大人ニキビ #肌改善 #腸活 #発酵食品"
  ]
}
```

- [ ] **Step 5: テーマ3のA版（エピソード・note誘導・原因解説）**

`threads_a[2]`（id=3）を上書き:

```json
{
  "id": 3,
  "theme": "砂糖とニキビ",
  "posts": [
    "ニキビが酷かった頃、毎日カフェラテと菓子パンを食べてました。\n\n甘いもの＝ご褒美って思ってたけど、それが原因だったと知ったのは止めて2週間後でした。",
    "砂糖の過剰摂取は皮脂分泌を増やす原因の一つです。\n\n甘いものを食べると血糖値が急上昇し、それを下げるインスリンが分泌され、皮脂腺を刺激します。\n\n研究では高GI食を続けた群でニキビ悪化の傾向が報告されています。\n\nつまり「甘いものを我慢」ではなく「血糖値を上げにくい食べ方」がポイントなんです。",
    "もっと詳しい改善メニューはnoteにまとめてあります。\n\nプロフィールのリンクから読んでみて。\n\n#肌荒れ #大人ニキビ #肌改善 #砂糖 #血糖値"
  ]
}
```

- [ ] **Step 6: テーマ3のB版（エピソード・note誘導・解決策提示）**

`threads_b` に追加:

```json
{
  "id": 3,
  "theme": "砂糖とニキビ",
  "posts": [
    "ニキビが酷かった頃、毎日カフェラテと菓子パンを食べてました。\n\n甘いものを完全に止めずに肌が変わった理由、今日まとめます。",
    "甘いものを「やめる」より「順番を変える」のが続きます。\n\n①食事の最初に野菜やたんぱく質を食べる\n②甘いものは食後すぐに少しだけ\n③飲み物は無糖に切り替え\n\n研究では食物繊維→たんぱく質→炭水化物の順で食べた群が血糖値スパイクを抑えられる傾向が報告されています。\n\n我慢ではなく順番、これだけで続けられます。",
    "もっと詳しい食事の組み立て方はnoteにまとめてあります。\n\nプロフィールのリンクから読んでみて。\n\n#肌荒れ #大人ニキビ #肌改善 #食事 #血糖値"
  ]
}
```

- [ ] **Step 7: テーマ4のA版（数字フック・フォローCTA・原因解説）**

`threads_a[3]`（id=4）を上書き:

```json
{
  "id": 4,
  "theme": "洗顔のやりすぎ",
  "posts": [
    "1日3回、念入りに洗顔してた頃が一番肌荒れてました。\n\n洗顔を1日2回に減らしたら、ニキビが3週間で落ち着いた話です。",
    "肌を清潔に保つはずの洗顔が、やりすぎると逆効果になることがあります。\n\n必要な皮脂まで落ちると、肌は乾燥を補おうとして余計に皮脂を出します。\n\n皮膚科では1日2回（朝と夜）が目安と紹介されることが多いです。\n\nつまり「ちゃんと落とす」より「落としすぎない」を意識するほうが肌は早く整います。",
    "毎日肌改善のヒントを発信中。\n\n気になる人はフォローしておくと続きが届くよ。\n\n#肌荒れ #大人ニキビ #肌改善 #洗顔"
  ]
}
```

- [ ] **Step 8: テーマ4のB版（数字フック・フォローCTA・解決策提示）**

`threads_b` に追加:

```json
{
  "id": 4,
  "theme": "洗顔のやりすぎ",
  "posts": [
    "1日3回、念入りに洗顔してた頃が一番肌荒れてました。\n\n今は朝はぬるま湯だけ。それで肌が安定するようになった具体的な手順を3つ。",
    "正しい洗顔の3ステップで、肌が落ち着きます。\n\n①朝はぬるま湯のみ（皮脂を残す）\n②夜だけ低刺激の洗顔料を泡立てて30秒\n③タオルでこすらず押し当てて水分オフ\n\n皮膚科では「摩擦を減らすこと」が皮脂バランス改善に効くと紹介されています。\n\n手順を変えるだけ、コストはゼロです。",
    "毎日肌改善のヒントを発信中。\n\n続きを受け取りたい人はフォローしておいてね。\n\n#肌荒れ #大人ニキビ #肌改善 #洗顔 #スキンケア"
  ]
}
```

- [ ] **Step 9: テーマ5のA版（逆張りフック・保存CTA・原因解説）**

`threads_a[4]`（id=5）を上書き:

```json
{
  "id": 5,
  "theme": "睡眠と肌",
  "posts": [
    "高い化粧水より、夜23時前に寝るほうが効きます。\n\n地味だけど、これが本当に肌を変える話。",
    "肌の修復は睡眠中に行われています。\n\n特に22時〜2時の間に分泌される成長ホルモンが、肌のターンオーバーを進めます。\n\n研究では7時間未満の睡眠群が肌バリア機能の低下傾向を示すと報告されています。\n\nつまり夜更かしを続けている限り、どんな化粧品でも追いつかないという話です。",
    "読み返したくなったら保存しておいてね。\n\n今夜から「寝る時間を30分前倒し」、これだけでいい。\n\n#肌荒れ #大人ニキビ #肌改善 #睡眠"
  ]
}
```

- [ ] **Step 10: テーマ5のB版（逆張りフック・保存CTA・解決策提示）**

`threads_b` に追加:

```json
{
  "id": 5,
  "theme": "睡眠と肌",
  "posts": [
    "高い化粧水より、夜23時前に寝るほうが効きます。\n\n睡眠の質を上げる3つの夜習慣を今日まとめます。",
    "肌が変わる睡眠の3ステップ。\n\n①寝る2時間前に湯船（38〜40度で10分）\n②寝る1時間前にスマホを置く\n③寝室の照明を電球色に切り替え\n\n研究では入浴と低光量環境が深部体温の低下を促し、入眠の質を高めると報告されています。\n\n寝具を変えるより先に、夜の2時間の過ごし方を整えるのが先です。",
    "読み返したくなったら保存しておいてね。\n\nまず①の湯船から、今夜試してみて。\n\n#肌荒れ #大人ニキビ #肌改善 #睡眠 #ナイトルーティン"
  ]
}
```

- [ ] **Step 11: 5テーマ分の文字数チェック**

Run:
```bash
python3 - <<'EOF'
import json
data = json.load(open("skin/skin_threads_posts.json", encoding="utf-8"))
for variant in ("threads_a", "threads_b"):
    for entry in data[variant]:
        if entry["id"] > 5:
            continue
        for i, p in enumerate(entry["posts"], 1):
            length = len(p)
            mark = "OK" if length <= 500 else "OVER"
            print(f"{variant} id={entry['id']} post{i}: {length}文字 {mark}")
EOF
```

Expected: 全行 OK（500文字以内）

- [ ] **Step 12: 薬機法チェック**

Run:
```bash
python3 - <<'EOF'
import json, re
data = json.load(open("skin/skin_threads_posts.json", encoding="utf-8"))
ng_words = ["治る", "治す", "効く", "効果がある", "完全に", "100%", "必ず", "確実に"]
for variant in ("threads_a", "threads_b"):
    for entry in data[variant]:
        if entry["id"] > 5:
            continue
        for i, p in enumerate(entry["posts"], 1):
            hits = [w for w in ng_words if w in p]
            if hits:
                print(f"NG {variant} id={entry['id']} post{i}: {hits}")
print("チェック完了")
EOF
```

Expected: NG表示なし、最後に「チェック完了」

NG が出たら該当箇所を該当ステップに戻って書き直す。

- [ ] **Step 13: コミット**

```bash
git add skin/skin_threads_posts.json
git commit -m "feat: rewrite skin threads themes 1-5 with A/B variants"
```

---

## Task 9: テーマ6〜10 のA+Bパターン制作（30本）

**Files:**
- Modify: `skin/skin_threads_posts.json`

**テーマ割当:**

| id | テーマ | フック型 | CTA型 |
|---|---|---|---|
| 6 | 小麦とグルテン | エピソード(%3==0) | コメント(%4==2) |
| 7 | ストレスと皮脂 | 数字(%3==1) | note誘導(%4==3) |
| 8 | 失敗談型 | 逆張り(%3==2) | フォロー(%4==0) |
| 9 | やめた習慣 | エピソード(%3==0) | 保存(%4==1) |
| 10 | 腸活食習慣 | 数字(%3==1) | コメント(%4==2) |

- [ ] **Step 1〜10: テーマ6〜10のA版とB版を制作**

Task 8 と同じパターンで、各テーマについて:
- A版: 既存 `threads_a` の該当id を上書き、本題は**原因解説**
- B版: `threads_b` に追加、本題は**解決策提示**

各投稿のフォーマット規則:
- 本1（フック）: 該当型に従う。100〜200文字目安
- 本2（本題）: 4文構造（事実→具体例→数字→読み手にとっての意味）。300〜450文字目安
- 本3（CTA）: 該当型のCTA文＋ハッシュタグ3〜5個。150〜250文字目安

実行手順は Task 8 のステップ1〜10 と同じ流れ（A版上書き → B版追加 を10回繰り返す）。

- [ ] **Step 11: 5テーマ分の文字数チェック**

Run（Task 8 Step 11 のスクリプトで `if entry["id"] > 5:` を `if not 6 <= entry["id"] <= 10:` に書き換え）。

Expected: 全行 OK

- [ ] **Step 12: 薬機法チェック**

Run（Task 8 Step 12 のスクリプトで同様の絞り込み）。

Expected: NG表示なし

- [ ] **Step 13: コミット**

```bash
git add skin/skin_threads_posts.json
git commit -m "feat: rewrite skin threads themes 6-10 with A/B variants"
```

---

## Task 10: テーマ11〜15 のA+Bパターン制作（30本）

**Files:**
- Modify: `skin/skin_threads_posts.json`

**テーマ割当:**

| id | テーマ | フック型 | CTA型 |
|---|---|---|---|
| 11 | お金をかけない美肌 | 数字(%3==1) | note誘導(%4==3) |
| 12 | タイプ別診断 | 逆張り(%3==2) | フォロー(%4==0) |
| 13 | 水分と肌 | エピソード(%3==0) | 保存(%4==1) |
| 14 | 亜鉛と皮脂 | 数字(%3==1) | コメント(%4==2) |
| 15 | ビタミンと肌 | 逆張り(%3==2) | note誘導(%4==3) |

- [ ] **Step 1〜10: テーマ11〜15のA版とB版を制作**

Task 8 と同じ流れで、10回の上書き/追加を実施。

- [ ] **Step 11: 文字数チェック（id 11〜15）**

Run（絞り込み条件を `if not 11 <= entry["id"] <= 15:` に変更）。

Expected: 全行 OK

- [ ] **Step 12: 薬機法チェック**

Expected: NG表示なし

- [ ] **Step 13: コミット**

```bash
git add skin/skin_threads_posts.json
git commit -m "feat: rewrite skin threads themes 11-15 with A/B variants"
```

---

## Task 11: テーマ16〜20 のA+Bパターン制作（30本）

**Files:**
- Modify: `skin/skin_threads_posts.json`

**テーマ割当:**

| id | テーマ | フック型 | CTA型 |
|---|---|---|---|
| 16 | 紫外線と肌 | エピソード(%3==0) | フォロー(%4==0) |
| 17 | 鉄分不足と肌 | 数字(%3==1) | 保存(%4==1) |
| 18 | 運動と肌 | 逆張り(%3==2) | コメント(%4==2) |
| 19 | カフェインと肌 | エピソード(%3==0) | note誘導(%4==3) |
| 20 | 摩擦と肌 | 数字(%3==1) | フォロー(%4==0) |

- [ ] **Step 1〜10: テーマ16〜20のA版とB版を制作**

Task 8 と同じ流れで、10回の上書き/追加を実施。

- [ ] **Step 11: 文字数チェック（id 16〜20）**

Expected: 全行 OK

- [ ] **Step 12: 薬機法チェック**

Expected: NG表示なし

- [ ] **Step 13: コミット**

```bash
git add skin/skin_threads_posts.json
git commit -m "feat: rewrite skin threads themes 16-20 with A/B variants"
```

---

## Task 12: Batch 1 全40セット通読チェック

**Files:**
- 確認のみ（書き換えは見つかった問題に応じて）

- [ ] **Step 1: 全件のJSON整合性確認**

Run:
```bash
python3 - <<'EOF'
import json
data = json.load(open("skin/skin_threads_posts.json", encoding="utf-8"))
print(f"threads_a: {len(data['threads_a'])} entries")
print(f"threads_b: {len(data['threads_b'])} entries")

# Batch 1範囲（id 1〜20）の検証
for variant in ("threads_a", "threads_b"):
    ids_in_batch = [e["id"] for e in data[variant] if 1 <= e["id"] <= 20]
    missing = set(range(1, 21)) - set(ids_in_batch)
    if missing:
        print(f"{variant}: id {sorted(missing)} が欠落")
    else:
        print(f"{variant}: id 1-20 全て揃っている")
    # 各セットのposts要素数チェック
    for e in data[variant]:
        if 1 <= e["id"] <= 20 and len(e["posts"]) != 3:
            print(f"{variant} id={e['id']}: posts要素数が3でない ({len(e['posts'])})")
EOF
```

Expected:
```
threads_a: 108 entries
threads_b: 20 entries
threads_a: id 1-20 全て揃っている
threads_b: id 1-20 全て揃っている
```

- [ ] **Step 2: 全40セット文字数チェック**

Run（Task 8 のスクリプトで `if entry["id"] > 5:` を `if not 1 <= entry["id"] <= 20:` に変更）。

Expected: 全行 OK

- [ ] **Step 3: 全40セット薬機法チェック**

Run（同様に絞り込み）。

Expected: NG表示なし

- [ ] **Step 4: フック型・CTA型ローテーション整合チェック**

Run:
```bash
python3 - <<'EOF'
import json
data = json.load(open("skin/skin_threads_posts.json", encoding="utf-8"))

hook_map = {0: "エピソード", 1: "数字", 2: "逆張り"}
cta_map = {0: "フォロー", 1: "保存", 2: "コメント", 3: "note誘導"}

for variant in ("threads_a", "threads_b"):
    for e in data[variant]:
        if not 1 <= e["id"] <= 20:
            continue
        expected_hook = hook_map[e["id"] % 3]
        expected_cta = cta_map[e["id"] % 4]
        print(f"{variant} id={e['id']} ({e['theme']}): フック={expected_hook}, CTA={expected_cta}")
EOF
```

各セットを目視で開き、本1が `expected_hook` 型、本3が `expected_cta` 型になっているか確認。ズレていたら該当タスクに戻って修正。

- [ ] **Step 5: バッチ進行管理を更新**

`skin/skin_threads_batch_progress.json` の Batch 1 status を `in_progress` → `ready_for_release` に変更:

Edit で `"status": "in_progress",` を Batch 1 ブロック内で `"status": "ready_for_release",` に置換（Batch 2以降の `pending` は触らない）。

- [ ] **Step 6: コミット**

```bash
git add skin/skin_threads_batch_progress.json
git commit -m "chore: mark batch 1 as ready_for_release after content review"
```

---

## Task 13: Batch 1 リリース（本番反映）

**Files:**
- 既存ブランチからmainへのマージ + push

**前提:** Task 1で `skin-threads-batch-1` ブランチを作成済み、Task 1〜12 のコミットが乗っている。

- [ ] **Step 1: リリース前にローカルで最終dry-run**

Run:
```bash
cd /home/kenta_kamijyo && python3 -m pytest skin/tests/ -v
```

Expected: 全テスト PASS

- [ ] **Step 2: skin_threads_action.py の文法・import エラーがないか確認**

Run: `cd /home/kenta_kamijyo && python3 -c "import skin.skin_threads_action"`
Expected: エラーなし

- [ ] **Step 3: mainブランチにマージ**

```bash
git checkout main
git pull --ff-only
git merge --no-ff skin-threads-batch-1 -m "Merge skin-threads-batch-1: A/B rewrite + themes 1-20"
```

- [ ] **Step 4: pushして本番反映（GitHub Actions が次の発火から新ロジック実行）**

```bash
git push origin main
```

- [ ] **Step 5: GitHub Actions の次回発火を確認**

ブラウザで `https://github.com/kmkn0523-cell/kenta-learning/actions` を開き、`skin_threads_post.yml` の最新run（または次回の予定実行）が新cron `30 22,3,9,12 * * *` で動く設定になっていることを確認。

- [ ] **Step 6: バッチ進行管理を `released` に更新**

`skin/skin_threads_batch_progress.json` で Batch 1 status を `ready_for_release` → `released` に変更。

```bash
git add skin/skin_threads_batch_progress.json
git commit -m "chore: mark batch 1 as released"
git push origin main
```

---

## Task 14: Batch 1 観測準備とBatch 2への引き継ぎ

**Files:**
- なし（観測手順の整備のみ）

- [ ] **Step 1: 初回投稿が成功したらワークフローのactionsログをチェック**

JST 7:30 / 12:30 / 18:30 / 21:30 の各タイミングで GitHub Actionsログを開き:
- 3本ツリー投稿が成功しているか
- ログ末尾に `variant=A` or `variant=B` のログが出ているか（Task 5 で組み込んだログ）
- `daily_index` `ab_index_per_theme` の更新がコミットされているか

- [ ] **Step 2: 1週間後（2026-05-31）にデータ収集結果を一度確認**

Run（ローカルから手動実行）:
```bash
cd /home/kenta_kamijyo && python3 skin/skin_ab_report.py --batch 1
```

Expected: 各テーマの a_posts / b_posts が3〜4回ずつ進んでおり、判定が「データ不足」から「A_wins/B_wins/差なし」に変わり始めている。

- [ ] **Step 3: 2週間後（2026-06-06）に最終レポート出力**

Run:
```bash
cd /home/kenta_kamijyo && python3 skin/skin_ab_report.py --batch 1 > skin/reports/batch_1_report_2026-06-06.txt
```

Expected: テーマごとの勝敗が確定、集計サマリが出力される。

- [ ] **Step 4: 検証期間終了時点で Batch 1 status を `validated` に更新**

`skin/skin_threads_batch_progress.json` で `released` → `validated` に変更し、`winner_decided: true` に。

- [ ] **Step 5: Batch 2 の制作開始トリガー**

`current_batch` を 1 → 2 に変更、Batch 2 status を `pending` → `in_progress` に。次計画書 `docs/superpowers/plans/2026-05-25-skin-threads-batch-2.md` の作成を別途開始。

- [ ] **Step 6: コミット**

```bash
git add skin/skin_threads_batch_progress.json
git commit -m "chore: validate batch 1, kick off batch 2"
git push origin main
```

---

## 実行ガード（ロールバック手順）

万一 Batch 1 投入後に問題発生（engagement_score 旧版-30%以上下落2日連続 / 警告コメント等）した場合:

```bash
# Step 1: タグから復元
git checkout skin-threads-batch-1-before -- skin/skin_threads_posts.json
git checkout skin-threads-batch-1-before -- skin/skin_threads_progress.json
git checkout skin-threads-batch-1-before -- .github/workflows/skin_threads_post.yml

# Step 2: コミット&プッシュ
git commit -m "Rollback batch 1"
git push origin main
```

所要時間: 5分程度。投稿頻度・ペイロードが元の状態に戻り、次回発火から旧版が稼働。

---

## このプランで触らないもの

- `skin/skin_data_collector.py`（既存稼働中、変更不要）
- `skin/skin_analyzer.py`（既存稼働中、変更不要）
- `skin/skin_optimizer.py`（既存稼働中、変更不要）
- `.env` ファイル・APIキー（CLAUDE.md「実行前に必ず確認」項目）
- Instagram関連の全ファイル（本プランのスコープ外）
- @RoninWords関連の全ファイル

---

## 完了条件（Batch 1）

- [ ] `skin/skin_threads_posts.json` の `threads_a[0:20]` と `threads_b[0:20]` に新版40セットが入っている
- [ ] `skin/skin_threads_progress.json` が拡張済み
- [ ] `skin/skin_threads_action.py` の単体テスト10件 PASS
- [ ] `skin/skin_ab_report.py` の単体テスト5件 PASS
- [ ] GitHub Actions cron が `30 22,3,9,12 * * *` に変更されている
- [ ] Gitタグ `skin-threads-batch-1-before` が打たれている
- [ ] バッチ進行管理ファイルが Batch 1=released で記録されている
- [ ] mainブランチに全変更がmerge＆pushされている
