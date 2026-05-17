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

**前提:** 本文制作は冒頭の「コンテンツ生成共通ガイドライン（Task 8〜11 で共通）」に従う。

**テーマ割当:**

| id | テーマ | フック型 (id%3) | CTA型 (id%4) | A本題切り口 | B本題切り口 |
|---|---|---|---|---|---|
| 6 | 小麦とグルテン | エピソード(%3==0) | コメント(%4==2) | 原因解説 | 解決策提示 |
| 7 | ストレスと皮脂 | 数字(%3==1) | note誘導(%4==3) | 原因解説 | 解決策提示 |
| 8 | 失敗談型 | 逆張り(%3==2) | フォロー(%4==0) | 原因解説 | 解決策提示 |
| 9 | やめた習慣 | エピソード(%3==0) | 保存(%4==1) | 原因解説 | 解決策提示 |
| 10 | 腸活食習慣 | 数字(%3==1) | コメント(%4==2) | 原因解説 | 解決策提示 |

- [ ] **Step 1: テーマ6 A版（エピソードフック・コメントCTA・原因解説）**

`skin/skin_threads_posts.json` の `threads_a` 配列で id=6 を以下構造で上書き:

- 本1 (100〜200文字): エピソードフック。「毎日パンを食べていた頃」など書き手の過去の食習慣エピソードから入る
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: グルテンが腸内環境に影響する報告がある
  2. 具体例: 朝パン・昼パスタ・夜ピザの典型的食生活
  3. 数字根拠: 「研究では小麦頻度と腸内炎症の相関の傾向が報告されています」
  4. 読み手への意味: 「つまり小麦を完全に切る必要はなく、頻度を下げる意味があるという話です」
- 本3 (150〜250文字): コメント型CTA「あなたが小麦を控えてみて気付いた変化あったら教えてね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #小麦 #グルテンフリー`

- [ ] **Step 2: テーマ6 B版（エピソードフック・コメントCTA・解決策提示）**

`threads_b` 配列に id=6 を追加:

- 本1 (100〜200文字): エピソードフック（A版と別角度。例: 小麦を控えた後の肌の変化エピソード）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: 完全カットではなく頻度を下げるアプローチ
  2. 3〜5ステップ: ①朝食のパンをおにぎりに ②週2日小麦オフデー ③外食でパスタを避ける
  3. 数字根拠: 「研究では小麦頻度低減群で腸内環境改善の傾向が報告されています」
  4. 今日からの行動: 「今日の朝食をおにぎりに切り替えるだけで始められます」
- 本3 (150〜250文字): コメント型CTA「小麦を控えるコツあったら教えてね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #小麦 #グルテンフリー`

- [ ] **Step 3: テーマ7 A版（数字フック・note誘導CTA・原因解説）**

`threads_a` 配列で id=7 を以下構造で上書き:

- 本1 (100〜200文字): 数字フック「ストレスを感じると皮脂が○倍に」など数値で引きを作る
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: ストレス時にコルチゾールが分泌され皮脂腺を刺激する報告がある
  2. 具体例: 仕事の繁忙期にニキビが急増した経験
  3. 数字根拠: 「研究では高ストレス群が低ストレス群より皮脂量が高い傾向が報告されています」
  4. 読み手への意味: 「つまり肌荒れ対策は気のせいではなくメンタルケアと地続きです」
- 本3 (150〜250文字): note誘導型CTA「もっと詳しいストレス対策メニューはプロフィールのnoteへ」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #ストレスケア #皮脂`

- [ ] **Step 4: テーマ7 B版（数字フック・note誘導CTA・解決策提示）**

`threads_b` 配列に id=7 を追加:

- 本1 (100〜200文字): 数字フック（A版と別角度。例: ストレス軽減で肌が変わるまでの日数）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: ストレスを「ゼロ」にせずコルチゾールピークを下げる方法
  2. 3〜5ステップ: ①朝の5分散歩 ②深呼吸タイマー ③寝る前のスマホ断ち
  3. 数字根拠: 「研究では呼吸法と運動でコルチゾール値が下がる傾向が報告されています」
  4. 今日からの行動: 「今日の昼休みに5分の散歩から始められます」
- 本3 (150〜250文字): note誘導型CTA「ストレス管理の30日プランはプロフィールのnoteへ」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #ストレスケア #セルフケア`

- [ ] **Step 5: テーマ8 A版（逆張りフック・フォローCTA・原因解説）**

`threads_a` 配列で id=8 を以下構造で上書き:

- 本1 (100〜200文字): 逆張りフック「8年間全部間違えてた、私の肌荒れ対策」など定説を覆す形
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: 過剰な保湿・洗顔がバリア機能を弱める報告がある
  2. 具体例: 高級美容液を重ねるほど肌が荒れた経験
  3. 数字根拠: 「皮膚科の調査では過剰スキンケアによる肌トラブルが増加傾向と紹介されています」
  4. 読み手への意味: 「つまり『何を足すか』より『何をやめるか』を見直す価値があります」
- 本3 (150〜250文字): フォロー型CTA「毎日肌改善のヒントを発信中。続きを受け取りたい人はフォローしておいてね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #肌荒れ体験談 #スキンケア`

- [ ] **Step 6: テーマ8 B版（逆張りフック・フォローCTA・解決策提示）**

`threads_b` 配列に id=8 を追加:

- 本1 (100〜200文字): 逆張りフック（失敗から学んだ反対のアプローチ）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: ケアを「減らす」方向に振ると肌は安定する
  2. 3〜5ステップ: ①美容液を1本に絞る ②朝はぬるま湯のみ ③週末はノーメイク
  3. 数字根拠: 「研究ではシンプルケア群で肌のキメ改善が報告されています」
  4. 今日からの行動: 「今夜のスキンケアを1ステップ減らすだけで始められます」
- 本3 (150〜250文字): フォロー型CTA「肌荒れから抜けたコツ、毎日発信中。フォローしておいてね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #ミニマルケア #スキンケア`

- [ ] **Step 7: テーマ9 A版（エピソードフック・保存CTA・原因解説）**

`threads_a` 配列で id=9 を以下構造で上書き:

- 本1 (100〜200文字): エピソードフック「8年間でやめた7つの習慣、肌が変わった話」
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: 日常の小さな習慣が皮脂・ホルモン・睡眠の質に影響する報告がある
  2. 具体例: 寝る前の甘いコーヒー、深夜のスマホ操作、頬杖の癖
  3. 数字根拠: 「研究では夜間ブルーライト曝露と肌バリア低下の関連が報告されています」
  4. 読み手への意味: 「つまり大きな対策より、小さな習慣の連鎖を断つほうが早いです」
- 本3 (150〜250文字): 保存型CTA「読み返したくなったら保存しておいてね。1つずつ手放していこう」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #生活習慣 #ミニマルライフ`

- [ ] **Step 8: テーマ9 B版（エピソードフック・保存CTA・解決策提示）**

`threads_b` 配列に id=9 を追加:

- 本1 (100〜200文字): エピソードフック（やめた後の変化のエピソード）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: やめる代わりに「置き換える」と続きやすい
  2. 3〜5ステップ: ①夜のコーヒー→白湯 ②寝る前スマホ→読書 ③頬杖→姿勢ストレッチ
  3. 数字根拠: 「研究では代替行動を設定した群で習慣変容の成功率が高い傾向が報告されています」
  4. 今日からの行動: 「今夜のコーヒー1杯を白湯に切り替えるだけで始められます」
- 本3 (150〜250文字): 保存型CTA「自分のやめたい習慣を見返したくなったら保存してね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #生活習慣 #置き換え`

- [ ] **Step 9: テーマ10 A版（数字フック・コメントCTA・原因解説）**

`threads_a` 配列で id=10 を以下構造で上書き:

- 本1 (100〜200文字): 数字フック「腸が整ってる人がやっている食習慣、7つ全部見せます」など数字導入
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: 腸内環境のバランスが肌の状態に直接影響する報告がある
  2. 具体例: 発酵食品ゼロの食生活で肌が荒れていた過去
  3. 数字根拠: 「研究では腸内多様性の高い群ほど肌トラブルが少ない傾向が報告されています」
  4. 読み手への意味: 「つまり化粧品より発酵食品が先という話です」
- 本3 (150〜250文字): コメント型CTA「あなたが続いてる腸活食習慣あったら教えてね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #腸活 #発酵食品`

- [ ] **Step 10: テーマ10 B版（数字フック・コメントCTA・解決策提示）**

`threads_b` 配列に id=10 を追加:

- 本1 (100〜200文字): 数字フック（A版と別角度。例: 1週間で腸が変わる食習慣の数）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: 毎食「発酵1品＋食物繊維1品」で腸は1週間で変わる
  2. 3〜5ステップ: ①朝はヨーグルト ②昼は味噌汁＋海藻 ③夜は納豆＋きのこ
  3. 数字根拠: 「研究では発酵食品＋食物繊維3週間継続群で肌のキメ改善が報告されています」
  4. 今日からの行動: 「今日のランチに味噌汁を1杯足すだけで始められます」
- 本3 (150〜250文字): コメント型CTA「あなたの続けてる発酵食品あったら教えてね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #腸活 #発酵食品`

- [ ] **Step 11: 5テーマ分の文字数チェック**

Run:
```bash
python3 - <<'EOF'
import json
data = json.load(open("skin/skin_threads_posts.json", encoding="utf-8"))
for variant in ("threads_a", "threads_b"):
    for entry in data[variant]:
        if not (6 <= entry["id"] <= 10):
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
import json
data = json.load(open("skin/skin_threads_posts.json", encoding="utf-8"))
ng_words = ["治る", "治す", "効く", "効果がある", "完全に", "100%", "必ず", "確実に"]
for variant in ("threads_a", "threads_b"):
    for entry in data[variant]:
        if not (6 <= entry["id"] <= 10):
            continue
        for i, p in enumerate(entry["posts"], 1):
            hits = [w for w in ng_words if w in p]
            if hits:
                print(f"NG {variant} id={entry['id']} post{i}: {hits}")
print("チェック完了")
EOF
```

Expected: NG表示なし、最後に「チェック完了」

NG が出たら該当ステップに戻って書き直す。

- [ ] **Step 13: コミット**

```bash
git add skin/skin_threads_posts.json
git commit -m "feat: rewrite skin threads themes 6-10 with A/B variants"
```

---

## Task 10: テーマ11〜15 のA+Bパターン制作（30本）

**Files:**
- Modify: `skin/skin_threads_posts.json`

**前提:** 本文制作は冒頭の「コンテンツ生成共通ガイドライン（Task 8〜11 で共通）」に従う。

**テーマ割当:**

| id | テーマ | フック型 (id%3) | CTA型 (id%4) | A本題切り口 | B本題切り口 |
|---|---|---|---|---|---|
| 11 | お金をかけない美肌 | 数字(%3==1) | note誘導(%4==3) | 原因解説 | 解決策提示 |
| 12 | タイプ別診断 | 逆張り(%3==2) | フォロー(%4==0) | 原因解説 | 解決策提示 |
| 13 | 水分と肌 | エピソード(%3==0) | 保存(%4==1) | 原因解説 | 解決策提示 |
| 14 | 亜鉛と皮脂 | 数字(%3==1) | コメント(%4==2) | 原因解説 | 解決策提示 |
| 15 | ビタミンと肌 | 逆張り(%3==2) | note誘導(%4==3) | 原因解説 | 解決策提示 |

- [ ] **Step 1: テーマ11 A版（数字フック・note誘導CTA・原因解説）**

`skin/skin_threads_posts.json` の `threads_a` 配列で id=11 を以下構造で上書き:

- 本1 (100〜200文字): 数字フック「3万円の化粧水より先にやること、8つ」など金額×個数で引きを作る
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: 肌の状態は食事・睡眠・腸内環境の影響が大きいと報告される
  2. 具体例: 化粧水を高級品にしても肌が荒れたままだった経験
  3. 数字根拠: 「研究では生活習慣改善群がスキンケア単独群より肌状態改善の傾向が報告されています」
  4. 読み手への意味: 「つまり化粧水のグレードを上げる前に、見直す土台がある話です」
- 本3 (150〜250文字): note誘導型CTA「3万の化粧水より先にやる8項目チェックリストはプロフィールのnoteへ」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #節約美容 #セルフケア`

- [ ] **Step 2: テーマ11 B版（数字フック・note誘導CTA・解決策提示）**

`threads_b` 配列に id=11 を追加:

- 本1 (100〜200文字): 数字フック（A版と別角度。例: 1ヶ月0円で肌が変わる習慣の数）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: 化粧水より「睡眠・水・発酵食品」が先
  2. 3〜5ステップ: ①23時就寝 ②起床時に白湯 ③毎食発酵食品1品 ④水500ml×3回 ⑤週末ノーメイク
  3. 数字根拠: 「研究では生活習慣改善群で肌のキメ改善の傾向が報告されています」
  4. 今日からの行動: 「今夜23時就寝を1日試すところから始められます」
- 本3 (150〜250文字): note誘導型CTA「0円で肌を変える30日プランはプロフィールのnoteへ」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #節約美容 #生活習慣`

- [ ] **Step 3: テーマ12 A版（逆張りフック・フォローCTA・原因解説）**

`threads_a` 配列で id=12 を以下構造で上書き:

- 本1 (100〜200文字): 逆張りフック「大人ニキビ、タイプが違うと対策が逆効果」など定説の落とし穴
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: 大人ニキビには皮脂過剰型と乾燥バリア低下型が混在する報告がある
  2. 具体例: 乾燥タイプなのに皮脂吸着の洗顔料を使ってさらに悪化させた経験
  3. 数字根拠: 「皮膚科の調査では成人ニキビの約半数が乾燥起因と紹介されています」
  4. 読み手への意味: 「つまりタイプ判別をせずにケアを選ぶと逆効果になる話です」
- 本3 (150〜250文字): フォロー型CTA「肌タイプ別ケアを毎日発信中。続きを受け取りたい人はフォローしておいてね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌タイプ #スキンケア #肌改善`

- [ ] **Step 4: テーマ12 B版（逆張りフック・フォローCTA・解決策提示）**

`threads_b` 配列に id=12 を追加:

- 本1 (100〜200文字): 逆張りフック（タイプ判別ミスから抜けたエピソード）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: 朝のTゾーンと頬の状態でタイプを見極めてからケアを変える
  2. 3〜5ステップ: ①朝のTゾーン油分チェック ②頬のつっぱりチェック ③朝起き直後のつっぱり有無 ④判別表でタイプ確定 ⑤タイプ別ケアに切替
  3. 数字根拠: 「研究ではタイプ別ケア群で肌バリア指数の改善の傾向が報告されています」
  4. 今日からの行動: 「明日の朝、起きてすぐのTゾーンと頬を観察するところから始められます」
- 本3 (150〜250文字): フォロー型CTA「タイプ判別表は明日の朝の投稿で配布。受け取りたい人はフォローしておいてね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌タイプ #スキンケア #肌改善`

- [ ] **Step 5: テーマ13 A版（エピソードフック・保存CTA・原因解説）**

`threads_a` 配列で id=13 を以下構造で上書き:

- 本1 (100〜200文字): エピソードフック「コーヒー4杯で水を1滴も飲まなかった頃の肌」など水分不足エピソード
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: 慢性的な水分不足はターンオーバーの停滞に関わると報告される
  2. 具体例: 1日コーヒー4杯で水ゼロの生活で肌がくすんで角質が厚くなっていた頃
  3. 数字根拠: 「研究では飲水量が少ない群で皮膚バリア機能低下の傾向が報告されています」
  4. 読み手への意味: 「つまり化粧水より体内の水分供給を増やすほうが早い話です」
- 本3 (150〜250文字): 保存型CTA「水分タイミングを忘れがちな人は保存しておいてね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #水分補給 #ハイドレーション`

- [ ] **Step 6: テーマ13 B版（エピソードフック・保存CTA・解決策提示）**

`threads_b` 配列に id=13 を追加:

- 本1 (100〜200文字): エピソードフック（1日2L始めた後の肌変化エピソード）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: 飲水は「タイミング」を決めるだけで2Lに届く
  2. 3〜5ステップ: ①起床時にコップ1杯 ②毎食前に1杯 ③15時に1杯 ④寝る前に1杯
  3. 数字根拠: 「研究では水分摂取増加群で角質水分量増加の傾向が報告されています」
  4. 今日からの行動: 「明日の朝、起きてすぐコップ1杯の白湯から始められます」
- 本3 (150〜250文字): 保存型CTA「自分の水分スケジュールを作りたくなったら保存してね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #水分補給 #生活習慣`

- [ ] **Step 7: テーマ14 A版（数字フック・コメントCTA・原因解説）**

`threads_a` 配列で id=14 を以下構造で上書き:

- 本1 (100〜200文字): 数字フック「皮脂が多い人が不足してるミネラル、たった1つ」など数字で絞り込む
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: 亜鉛不足は皮脂腺の働きに影響すると報告される
  2. 具体例: 加工食品中心の食生活で亜鉛が足りず皮脂とニキビが増えた経験
  3. 数字根拠: 「研究では亜鉛欠乏群で皮脂分泌増加の傾向が報告されています」
  4. 読み手への意味: 「つまりニキビ対策にはサプリより先に亜鉛食材を見直す価値がある話です」
- 本3 (150〜250文字): コメント型CTA「亜鉛食材で続けてるものあったら教えてね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #亜鉛 #ミネラル`

- [ ] **Step 8: テーマ14 B版（数字フック・コメントCTA・解決策提示）**

`threads_b` 配列に id=14 を追加:

- 本1 (100〜200文字): 数字フック（A版と別角度。例: 亜鉛で皮脂が落ち着くまでの週数）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: 食材だけで1日の亜鉛目安量に届く組み合わせがある
  2. 3〜5ステップ: ①朝はゆで卵 ②昼は牡蠣or赤身肉 ③夜は納豆 ④間食はナッツ
  3. 数字根拠: 「研究では亜鉛食材を継続摂取した群で皮脂量改善の傾向が報告されています」
  4. 今日からの行動: 「明日の朝、ゆで卵を1つ足すだけで始められます」
- 本3 (150〜250文字): コメント型CTA「あなたの亜鉛食材レシピあったら教えてね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #亜鉛 #食事改善`

- [ ] **Step 9: テーマ15 A版（逆張りフック・note誘導CTA・原因解説）**

`threads_a` 配列で id=15 を以下構造で上書き:

- 本1 (100〜200文字): 逆張りフック「ビタミンCサプリを買う前に、見直すべきビタミンがある」など定説の前段に焦点
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: 肌の代謝にはB群・D・Eのバランスが先に必要と報告される
  2. 具体例: ビタミンCサプリだけ飲んでも肌が変わらなかった経験
  3. 数字根拠: 「研究ではビタミンB群欠乏群で皮膚症状の発生頻度が高い傾向が報告されています」
  4. 読み手への意味: 「つまりビタミンは『種類より順番』を考える価値がある話です」
- 本3 (150〜250文字): note誘導型CTA「肌のためのビタミン順番ガイドはプロフィールのnoteへ」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #ビタミン #栄養`

- [ ] **Step 10: テーマ15 B版（逆張りフック・note誘導CTA・解決策提示）**

`threads_b` 配列に id=15 を追加:

- 本1 (100〜200文字): 逆張りフック（サプリより食材から摂る順序のエピソード）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: 食材から「B群→D→E」の順に整えるとサプリ依存を抜けられる
  2. 3〜5ステップ: ①今月はB群（豚肉・卵） ②来月はD（鮭・卵黄・日光） ③再来月はE（ナッツ・アボカド）
  3. 数字根拠: 「研究ではビタミン群を食事で補った群で皮膚状態改善の傾向が報告されています」
  4. 今日からの行動: 「今日の昼食に豚肉か卵を1品足すところから始められます」
- 本3 (150〜250文字): note誘導型CTA「3ヶ月ビタミン食事プランはプロフィールのnoteへ」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #ビタミン #食事改善`

- [ ] **Step 11: 5テーマ分の文字数チェック**

Run:
```bash
python3 - <<'EOF'
import json
data = json.load(open("skin/skin_threads_posts.json", encoding="utf-8"))
for variant in ("threads_a", "threads_b"):
    for entry in data[variant]:
        if not (11 <= entry["id"] <= 15):
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
import json
data = json.load(open("skin/skin_threads_posts.json", encoding="utf-8"))
ng_words = ["治る", "治す", "効く", "効果がある", "完全に", "100%", "必ず", "確実に"]
for variant in ("threads_a", "threads_b"):
    for entry in data[variant]:
        if not (11 <= entry["id"] <= 15):
            continue
        for i, p in enumerate(entry["posts"], 1):
            hits = [w for w in ng_words if w in p]
            if hits:
                print(f"NG {variant} id={entry['id']} post{i}: {hits}")
print("チェック完了")
EOF
```

Expected: NG表示なし、最後に「チェック完了」

NG が出たら該当ステップに戻って書き直す。

- [ ] **Step 13: コミット**

```bash
git add skin/skin_threads_posts.json
git commit -m "feat: rewrite skin threads themes 11-15 with A/B variants"
```

---

## Task 11: テーマ16〜20 のA+Bパターン制作（30本）

**Files:**
- Modify: `skin/skin_threads_posts.json`

**前提:** 本文制作は冒頭の「コンテンツ生成共通ガイドライン（Task 8〜11 で共通）」に従う。

**テーマ割当:**

| id | テーマ | フック型 (id%3) | CTA型 (id%4) | A本題切り口 | B本題切り口 |
|---|---|---|---|---|---|
| 16 | 紫外線と肌 | エピソード(%3==0) | フォロー(%4==0) | 原因解説 | 解決策提示 |
| 17 | 鉄分不足と肌 | 数字(%3==1) | 保存(%4==1) | 原因解説 | 解決策提示 |
| 18 | 運動と肌 | 逆張り(%3==2) | コメント(%4==2) | 原因解説 | 解決策提示 |
| 19 | カフェインと肌 | エピソード(%3==0) | note誘導(%4==3) | 原因解説 | 解決策提示 |
| 20 | 摩擦と肌 | 数字(%3==1) | フォロー(%4==0) | 原因解説 | 解決策提示 |

- [ ] **Step 1: テーマ16 A版（エピソードフック・フォローCTA・原因解説）**

`skin/skin_threads_posts.json` の `threads_a` 配列で id=16 を以下構造で上書き:

- 本1 (100〜200文字): エピソードフック「日焼け止めを塗らずに通勤していた頃の肌」など過去の紫外線対策エピソード
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: 紫外線はバリア機能と色素沈着の両方に影響すると報告される
  2. 具体例: 5分の通勤でも夏場は赤くヒリつき、ニキビ跡が消えなかった経験
  3. 数字根拠: 「研究では日焼け止め習慣群が非習慣群より色素沈着スコアが低い傾向が報告されています」
  4. 読み手への意味: 「つまり紫外線対策は美白ケアより先にやる土台の話です」
- 本3 (150〜250文字): フォロー型CTA「季節別の紫外線対策を毎日発信中。続きを受け取りたい人はフォローしておいてね」＋ハッシュタグ `#肌荒れ #紫外線対策 #日焼け止め #肌改善 #スキンケア`

- [ ] **Step 2: テーマ16 B版（エピソードフック・フォローCTA・解決策提示）**

`threads_b` 配列に id=16 を追加:

- 本1 (100〜200文字): エピソードフック（日焼け止めを毎日塗り始めた後の変化）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: 紫外線対策は「外出5分前・2時間ごと・帰宅後」の3点でほぼ完結する
  2. 3〜5ステップ: ①外出5分前にSPF塗布 ②2時間ごとに塗り直し ③帰宅後すぐクレンジング ④日傘・帽子
  3. 数字根拠: 「研究では2時間ごと塗り直し群で日焼け指数の上昇抑制の傾向が報告されています」
  4. 今日からの行動: 「明日朝、家を出る5分前に日焼け止めを塗るところから始められます」
- 本3 (150〜250文字): フォロー型CTA「季節別の紫外線対策の続きを受け取りたい人はフォローしておいてね」＋ハッシュタグ `#肌荒れ #紫外線対策 #日焼け止め #肌改善 #スキンケア`

- [ ] **Step 3: テーマ17 A版（数字フック・保存CTA・原因解説）**

`threads_a` 配列で id=17 を以下構造で上書き:

- 本1 (100〜200文字): 数字フック「女性の3人に1人が不足してる栄養素」など割合×身近さで引きを作る
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: 鉄分不足は血流低下を介して肌の色とハリに影響すると報告される
  2. 具体例: 生理後に顔色が悪くクマが濃くなる経験
  3. 数字根拠: 「研究では鉄欠乏群で皮膚血色スコアの低下傾向が報告されています」
  4. 読み手への意味: 「つまり化粧では隠せないクマ・くすみは食事から見直す価値がある話です」
- 本3 (150〜250文字): 保存型CTA「鉄分食材リストを見返したくなったら保存しておいてね」＋ハッシュタグ `#肌荒れ #肌改善 #鉄分 #貧血 #食事改善`

- [ ] **Step 4: テーマ17 B版（数字フック・保存CTA・解決策提示）**

`threads_b` 配列に id=17 を追加:

- 本1 (100〜200文字): 数字フック（A版と別角度。例: 鉄分を1ヶ月続けた後の血色変化）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: 鉄分は「動物性＋ビタミンC同時摂取」で吸収率が上がる
  2. 3〜5ステップ: ①朝は卵 ②昼は赤身肉＋ブロッコリー ③夜はレバー週1 ④間食にプルーン ⑤緑茶・コーヒーは食後1時間後
  3. 数字根拠: 「研究では鉄＋ビタミンC同時摂取群で鉄吸収率の上昇が報告されています」
  4. 今日からの行動: 「明日のランチに赤身肉とブロッコリーを足すところから始められます」
- 本3 (150〜250文字): 保存型CTA「鉄分の組み合わせを忘れがちな人は保存しておいてね」＋ハッシュタグ `#肌荒れ #肌改善 #鉄分 #食事改善 #栄養`

- [ ] **Step 5: テーマ18 A版（逆張りフック・コメントCTA・原因解説）**

`threads_a` 配列で id=18 を以下構造で上書き:

- 本1 (100〜200文字): 逆張りフック「ジムに通っても肌が荒れる人がやってるNG」など定説の落とし穴
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: 運動後の汗を放置するとアクネ菌増殖と摩擦刺激が起こりやすいと報告される
  2. 具体例: 運動後シャワーを後回しにしてニキビが背中と顎に増えた経験
  3. 数字根拠: 「研究では運動後30分以内の洗浄群で皮膚常在菌バランス維持の傾向が報告されています」
  4. 読み手への意味: 「つまり運動そのものより『運動後ケア』が肌を左右する話です」
- 本3 (150〜250文字): コメント型CTA「運動後の肌ケアで続けてることあったら教えてね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #運動 #トレーニング`

- [ ] **Step 6: テーマ18 B版（逆張りフック・コメントCTA・解決策提示）**

`threads_b` 配列に id=18 を追加:

- 本1 (100〜200文字): 逆張りフック（運動後ケアを変えてニキビが減ったエピソード）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: 運動後30分以内の「汗オフ・摩擦ゼロ・水分補給」で肌は守れる
  2. 3〜5ステップ: ①汗を吸う素材のウェア ②運動後30分以内にシャワー ③タオルは押すだけ ④水500ml補給
  3. 数字根拠: 「研究では汗速乾素材使用群で皮膚摩擦刺激の低下が報告されています」
  4. 今日からの行動: 「次回のトレーニング後、タオルでこすらず押し当てるだけにしてみてください」
- 本3 (150〜250文字): コメント型CTA「あなたの運動後ルーティーン教えてね」＋ハッシュタグ `#肌荒れ #大人ニキビ #肌改善 #運動 #ケア`

- [ ] **Step 7: テーマ19 A版（エピソードフック・note誘導CTA・原因解説）**

`threads_a` 配列で id=19 を以下構造で上書き:

- 本1 (100〜200文字): エピソードフック「コーヒー4杯で寝つけなかった頃の肌」など過剰カフェイン期のエピソード
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: カフェインは睡眠の質と利尿作用を介して肌に影響すると報告される
  2. 具体例: 午後3時以降にコーヒーを飲み続け寝つきが悪くなりクマと毛穴が悪化した経験
  3. 数字根拠: 「研究ではカフェイン摂取が午後遅い群で睡眠効率低下の傾向が報告されています」
  4. 読み手への意味: 「つまりカフェインは『量より時間帯』を見直す価値がある話です」
- 本3 (150〜250文字): note誘導型CTA「カフェイン時間帯と肌の関係をまとめたnoteはプロフィールへ」＋ハッシュタグ `#肌荒れ #肌改善 #カフェイン #睡眠 #生活習慣`

- [ ] **Step 8: テーマ19 B版（エピソードフック・note誘導CTA・解決策提示）**

`threads_b` 配列に id=19 を追加:

- 本1 (100〜200文字): エピソードフック（カフェインを14時までに切り替えた後の肌変化）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: カフェインは「14時カットオフ」を守れば睡眠と肌は両立する
  2. 3〜5ステップ: ①朝のコーヒーは1杯 ②昼食後に1杯 ③14時以降は白湯・ハーブティー ④夜はカフェインレス紅茶 ⑤水分量は維持
  3. 数字根拠: 「研究では14時以降カフェイン断ち群で入眠時間短縮の傾向が報告されています」
  4. 今日からの行動: 「今日の14時以降を白湯に切り替えるだけで始められます」
- 本3 (150〜250文字): note誘導型CTA「カフェイン置き換えドリンク表はプロフィールのnoteへ」＋ハッシュタグ `#肌荒れ #肌改善 #カフェイン #睡眠 #生活習慣`

- [ ] **Step 9: テーマ20 A版（数字フック・フォローCTA・原因解説）**

`threads_a` 配列で id=20 を以下構造で上書き:

- 本1 (100〜200文字): 数字フック「肌を1日30回擦ってる人の共通点」など回数×無自覚で引きを作る
- 本2 (300〜450文字): 原因解説の4文構造
  1. 事実: 摩擦刺激の蓄積は色素沈着と肌バリア低下に関係すると報告される
  2. 具体例: タオルでゴシゴシ、マスクのこすれ、頬杖の癖で頬が黒ずんだ経験
  3. 数字根拠: 「研究では摩擦刺激高頻度群で色素沈着スコアの上昇が報告されています」
  4. 読み手への意味: 「つまりスキンケアより先に『擦らない癖づくり』が肌を守る話です」
- 本3 (150〜250文字): フォロー型CTA「摩擦ゼロ習慣の続きを受け取りたい人はフォローしておいてね」＋ハッシュタグ `#肌荒れ #肌改善 #摩擦 #色素沈着 #スキンケア`

- [ ] **Step 10: テーマ20 B版（数字フック・フォローCTA・解決策提示）**

`threads_b` 配列に id=20 を追加:

- 本1 (100〜200文字): 数字フック（A版と別角度。例: 摩擦をやめて1ヶ月で頬の色が変わった話）
- 本2 (300〜450文字): 解決策提示の4文構造
  1. 結論: 摩擦は「タオル・洗顔・マスク・頬杖」の4箇所を見直すだけで激減する
  2. 3〜5ステップ: ①タオルは押し当てる ②洗顔は泡で滑らせる ③マスク内側に綿ガーゼ ④頬杖を辞めるアラーム
  3. 数字根拠: 「研究では摩擦低減習慣群で肌バリア指数の改善の傾向が報告されています」
  4. 今日からの行動: 「今夜の洗顔後、タオルでこすらず押し当てるだけにしてみてください」
- 本3 (150〜250文字): フォロー型CTA「摩擦ゼロ習慣の続きを受け取りたい人はフォローしておいてね」＋ハッシュタグ `#肌荒れ #肌改善 #摩擦 #色素沈着 #スキンケア`

- [ ] **Step 11: 5テーマ分の文字数チェック**

Run:
```bash
python3 - <<'EOF'
import json
data = json.load(open("skin/skin_threads_posts.json", encoding="utf-8"))
for variant in ("threads_a", "threads_b"):
    for entry in data[variant]:
        if not (16 <= entry["id"] <= 20):
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
import json
data = json.load(open("skin/skin_threads_posts.json", encoding="utf-8"))
ng_words = ["治る", "治す", "効く", "効果がある", "完全に", "100%", "必ず", "確実に"]
for variant in ("threads_a", "threads_b"):
    for entry in data[variant]:
        if not (16 <= entry["id"] <= 20):
            continue
        for i, p in enumerate(entry["posts"], 1):
            hits = [w for w in ng_words if w in p]
            if hits:
                print(f"NG {variant} id={entry['id']} post{i}: {hits}")
print("チェック完了")
EOF
```

Expected: NG表示なし、最後に「チェック完了」

NG が出たら該当ステップに戻って書き直す。

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
