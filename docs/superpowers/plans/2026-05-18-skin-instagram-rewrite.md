# skin Instagram カルーセル全面リライト 実装計画 (Batch 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** skin Instagramの20テーマカルーセルを8枚×3軸フック×4軸CTAでリライトし、Batch 1（テーマ1〜4、32枚）を本番投入する。並行して Instagram Graph API のデータ収集を新規実装し、保存率ベースラインを取得する。

**Architecture:** 既存の `skin_instagram_auto_post.py` を最小改修して動的 `slide_count` と新キャプション組み立てに対応。新規 `skin_instagram_image_gen_v4.py` で8枚PILテンプレを生成。`carousel_content.json` に `version` `slide_count` 3層ハッシュタグキーを追加して新旧並走を可能にする。データ収集は別ワークフローで毎日06:00 JST稼働。

**Tech Stack:** Python 3 / Pillow (PIL) / json / requests / GitHub Actions / pytest

**設計書:** `/home/kenta_kamijyo/docs/superpowers/specs/2026-05-18-skin-instagram-rewrite-design.md`

---

## File Structure

### 既存ファイル（書き換え）

| ファイル | 変更内容 |
|---|---|
| `skin/carousel_content.json` | 各テーマに `version` `slide_count` `fixed_hashtags` `theme_hashtags` `size_mix_hashtags` を追加。Batch 1で theme01〜04 のみ v2（8スライド）化、残りは v1 のまま |
| `skin/skin_instagram_auto_post.py` | `SLIDES_PER_CAROUSEL` 廃止 → テーマ毎の `slide_count` を読む実装に変更／キャプション組み立てロジック（フック再掲＋CTA本文＋3層ハッシュタグ）追加 |

### 新規ファイル

| ファイル | 用途 |
|---|---|
| `skin/skin_instagram_image_gen_v4.py` | 8枚カルーセル用PIL生成スクリプト（新テンプレ） |
| `skin/skin_instagram_batch_progress.json` | バッチ進行管理 |
| `skin/skin_instagram_data_collector.py` | Instagram Graph APIデータ収集スクリプト |
| `skin/skin_instagram_analytics.json` | Instagram分析データ保存先 |
| `skin/skin_instagram_report.py` | バッチ毎の保存率検証レポート |
| `.github/workflows/skin_instagram_data_collect.yml` | データ収集を毎日06:00 JSTに起動 |
| `skin/tests/test_skin_instagram_caption.py` | キャプション組み立てロジックの単体テスト |
| `skin/tests/test_skin_instagram_hashtag.py` | ハッシュタグ結合の単体テスト |

### 変更しないファイル

- `.github/workflows/skin_instagram_auto_post.yml`（1日4回維持）
- `.github/workflows/skin_instagram_watchdog.yml`（既存稼働中）
- `skin/skin_data_collector.py` / `skin/skin_analyzer.py`（Threads用、既存稼働中）
- `.env`・APIキー周辺

---

## 進行フェーズ概要

1. **バックアップ・基礎整備** (Task 1〜2): Gitタグ、バッチ進行管理ファイル作成
2. **データ収集基盤の先行稼働** (Task 3〜5): ベースライン取得を最優先で起動
3. **コードのリファクタ** (Task 6〜7): 投稿スクリプトを動的slide_count対応＋キャプション組み立て
4. **画像生成テンプレ** (Task 8): 新8枚PILテンプレ実装
5. **Batch 1 コンテンツ制作** (Task 9〜10): theme01〜04 v2 + 画像生成
6. **検証レポート** (Task 11): 保存率レポートスクリプト
7. **Batch 1 リリース** (Task 12): コミット・push・初動確認
8. **Batch 2〜5 展開手順** (Task 13): 繰り返し手順のドキュメント化

---

## Task 1: Gitタグでバックアップと作業ブランチ作成

**Files:**
- 既存ファイル全てが対象（追跡対象のみ）

- [ ] **Step 1: 作業ブランチ作成（main上で直接作業しない）**

```bash
git checkout main
git pull --ff-only
git checkout -b skin-instagram-batch-1
```

- [ ] **Step 2: Batch 1リリース前のロールバックポイントをタグで保存**

```bash
git tag skin-instagram-batch-1-before main
git push origin skin-instagram-batch-1-before
```

- [ ] **Step 3: タグが打たれたか確認**

Run: `git tag -l "skin-instagram-batch-*"`
Expected output: `skin-instagram-batch-1-before`

---

## Task 2: バッチ進行管理ファイルを新規作成

**Files:**
- Create: `skin/skin_instagram_batch_progress.json`

**目的:** 5バッチの進行状態と日程を管理するファイルを作成。各バッチの themes / status / 日付を記録する。

- [ ] **Step 1: ファイルを新規作成**

Create: `skin/skin_instagram_batch_progress.json`

```json
{
  "current_batch": 1,
  "total_batches": 5,
  "batches": {
    "1": {
      "themes": [1, 2, 3, 4],
      "status": "in_progress",
      "production_start": "2026-05-18",
      "release_date": "2026-05-24",
      "validation_until": "2026-06-06",
      "notes": ""
    },
    "2": {
      "themes": [5, 6, 7, 8],
      "status": "pending",
      "production_start": "2026-05-25",
      "release_date": "2026-05-31",
      "validation_until": "2026-06-13",
      "notes": ""
    },
    "3": {
      "themes": [9, 10, 11, 12],
      "status": "pending",
      "production_start": "2026-06-01",
      "release_date": "2026-06-07",
      "validation_until": "2026-06-20",
      "notes": ""
    },
    "4": {
      "themes": [13, 14, 15, 16],
      "status": "pending",
      "production_start": "2026-06-08",
      "release_date": "2026-06-14",
      "validation_until": "2026-06-27",
      "notes": ""
    },
    "5": {
      "themes": [17, 18, 19, 20],
      "status": "pending",
      "production_start": "2026-06-15",
      "release_date": "2026-06-21",
      "validation_until": "2026-07-04",
      "notes": ""
    }
  }
}
```

- [ ] **Step 2: JSONの構文をPythonで確認**

Run: `python3 -c "import json; json.load(open('skin/skin_instagram_batch_progress.json'))" && echo OK`
Expected output: `OK`

- [ ] **Step 3: コミット**

```bash
git add skin/skin_instagram_batch_progress.json
git commit -m "feat: skin Instagram バッチ進行管理ファイル新規追加"
```

---

## Task 3: Instagramデータ収集スクリプト新規作成（テスト先行）

**Files:**
- Create: `skin/tests/__init__.py`（既存有無を確認、なければ作る）
- Create: `skin/tests/test_skin_instagram_data_collector.py`
- Create: `skin/skin_instagram_data_collector.py`

**目的:** Instagram Graph APIから過去30日分の投稿データを遡って取得し、`skin_instagram_analytics.json` に蓄積する。Batch 1リリース時点で旧版（v1）の保存率ベースラインを確立するために最優先で稼働させる。

### Step群

- [ ] **Step 1: tests ディレクトリの初期化**

Run: `ls skin/tests/ 2>/dev/null`

→ 既に存在する場合は次のStepへ。存在しない場合のみ以下を実行:

```bash
mkdir -p skin/tests
touch skin/tests/__init__.py
```

- [ ] **Step 2: 失敗するテストを書く（保存率計算関数）**

Create: `skin/tests/test_skin_instagram_data_collector.py`

```python
# skin Instagram データ収集スクリプトの単体テスト
# 使い方: pytest skin/tests/test_skin_instagram_data_collector.py -v

import sys
from pathlib import Path
# skin ディレクトリをimportパスに追加（プロジェクトルートからの実行用）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skin_instagram_data_collector import calculate_save_rate


def test_calculate_save_rate_normal():
    """通常ケース: 保存数100/インプレッション5000 = 2.0%"""
    rate = calculate_save_rate(saved=100, impressions=5000)
    assert rate == 2.0


def test_calculate_save_rate_zero_impressions():
    """インプレッションがゼロのときはゼロ除算を避けて0.0を返す"""
    rate = calculate_save_rate(saved=10, impressions=0)
    assert rate == 0.0


def test_calculate_save_rate_zero_saved():
    """保存数がゼロのときは0.0を返す"""
    rate = calculate_save_rate(saved=0, impressions=1000)
    assert rate == 0.0


def test_calculate_save_rate_rounding():
    """小数第2位までで丸める（4.16666... → 4.17）"""
    rate = calculate_save_rate(saved=250, impressions=6000)
    assert rate == 4.17
```

- [ ] **Step 3: テストを実行して失敗することを確認**

Run: `pytest skin/tests/test_skin_instagram_data_collector.py -v`
Expected: `ModuleNotFoundError: No module named 'skin_instagram_data_collector'`

- [ ] **Step 4: データ収集スクリプトの最小実装（calculate_save_rate のみ）**

Create: `skin/skin_instagram_data_collector.py`

```python
# skin_instagram_data_collector.py
# skin Instagram用 データ収集スクリプト
# 使い方: python3 skin/skin_instagram_data_collector.py
#         python3 skin/skin_instagram_data_collector.py --backfill 30   （過去30日遡り）

import os                    # 環境変数を扱う道具
import sys                   # コマンドライン引数を扱う道具
import json                  # JSONを読み書きする道具
import argparse              # コマンドライン引数のパース
from pathlib import Path     # ファイルパスを扱う道具
from datetime import datetime, timezone, timedelta  # 日時を扱う道具
import requests              # インターネット通信用の道具
from dotenv import load_dotenv  # .envからAPIキーを読み込む道具

# .envファイルを読み込む（APIキーは安全に管理）
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Instagram Graph API用のキー
ACCESS_TOKEN = os.getenv("SKIN_INSTAGRAM_ACCESS_TOKEN")
USER_ID      = os.getenv("SKIN_INSTAGRAM_USER_ID")

# ファイルパス（プロジェクトルートからの相対が安定）
_DIR           = Path(__file__).resolve().parent
ANALYTICS_FILE = _DIR / "skin_instagram_analytics.json"

# APIリクエストのタイムアウト時間（秒）
API_TIMEOUT = 15


def calculate_save_rate(saved: int, impressions: int) -> float:
    """
    保存率（％）を計算する。
    - インプレッションがゼロのときは 0.0 を返す（ゼロ除算回避）
    - 小数第2位で四捨五入する
    """
    if impressions <= 0:
        return 0.0
    rate = (saved / impressions) * 100.0
    return round(rate, 2)
```

- [ ] **Step 5: テストを実行して合格することを確認**

Run: `pytest skin/tests/test_skin_instagram_data_collector.py -v`
Expected: 4 passed

- [ ] **Step 6: コミット**

```bash
git add skin/tests/__init__.py skin/tests/test_skin_instagram_data_collector.py skin/skin_instagram_data_collector.py
git commit -m "feat: skin Instagram データ収集スクリプトの保存率計算を追加（TDD）"
```

---

## Task 4: Instagramデータ収集スクリプトの本体実装

**Files:**
- Modify: `skin/skin_instagram_data_collector.py`
- Create: `skin/skin_instagram_analytics.json`（空ファイル）

**目的:** Instagram Graph APIから過去N日分の投稿を取得し、各投稿の insights（saved, impressions, reach 等）を analytics ファイルに蓄積する関数を追加。

- [ ] **Step 1: 既存のスクリプトに本体ロジックを追記**

`skin/skin_instagram_data_collector.py` の末尾に以下を追記:

```python


def load_analytics() -> dict:
    """analyticsファイルを読み込む（なければ空の辞書を返す）"""
    if not ANALYTICS_FILE.exists():
        return {"posts": {}, "follower_history": []}
    try:
        return json.loads(ANALYTICS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"posts": {}, "follower_history": []}


def save_analytics(data: dict) -> None:
    """analyticsファイルに書き込む（インデント2、UTF-8）"""
    ANALYTICS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def fetch_recent_posts(limit: int = 30) -> list[dict]:
    """
    最新の投稿 limit 件を取得する（ID と timestamp のみ）。
    取得失敗時は空リストを返す。
    """
    if not ACCESS_TOKEN or not USER_ID:
        print("❌ SKIN_INSTAGRAM_ACCESS_TOKEN または SKIN_INSTAGRAM_USER_ID が未設定")
        return []

    url = f"https://graph.facebook.com/v19.0/{USER_ID}/media"
    params = {
        "fields":       "id,timestamp,caption",
        "limit":        limit,
        "access_token": ACCESS_TOKEN,
    }
    try:
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"⚠️ 投稿一覧取得エラー: {e}")
        return []


def fetch_post_insights(post_id: str) -> dict:
    """
    1投稿の insights（saved, impressions, reach 等）を取得する。
    取得失敗時は空辞書を返す。
    """
    url = f"https://graph.facebook.com/v19.0/{post_id}/insights"
    params = {
        "metric":       "saved,impressions,reach",
        "access_token": ACCESS_TOKEN,
    }
    try:
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        data = response.json()
        result = {}
        for item in data.get("data", []):
            name   = item.get("name")
            values = item.get("values", [])
            if values:
                result[name] = values[0].get("value", 0)
        return result
    except Exception as e:
        print(f"⚠️ insights取得エラー ({post_id}): {e}")
        return {}


def fetch_account_followers() -> int:
    """アカウントの現在フォロワー数を取得する（失敗時は -1）"""
    url = f"https://graph.facebook.com/v19.0/{USER_ID}"
    params = {
        "fields":       "followers_count",
        "access_token": ACCESS_TOKEN,
    }
    try:
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        data = response.json()
        return int(data.get("followers_count", -1))
    except Exception as e:
        print(f"⚠️ フォロワー数取得エラー: {e}")
        return -1


def collect_once(backfill_days: int = 0) -> None:
    """
    投稿のinsightsとフォロワー数を取得して analytics に追記する。
    backfill_days が指定された場合、その日数前までの投稿を遡って取得する。
    """
    analytics = load_analytics()
    posts = fetch_recent_posts(limit=50 if backfill_days > 0 else 10)

    if backfill_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=backfill_days)
        posts = [p for p in posts if datetime.fromisoformat(p["timestamp"].replace("+0000", "+00:00")) >= cutoff]

    today_iso = datetime.now(timezone.utc).date().isoformat()
    updated_count = 0

    for post in posts:
        post_id   = post["id"]
        insights  = fetch_post_insights(post_id)
        if not insights:
            continue

        saved       = insights.get("saved", 0)
        impressions = insights.get("impressions", 0)
        reach       = insights.get("reach", 0)
        save_rate   = calculate_save_rate(saved, impressions)

        # 投稿ごとに最新値を上書き保存（累積データ）
        analytics["posts"][post_id] = {
            "timestamp":   post["timestamp"],
            "caption":     post.get("caption", "")[:120],
            "saved":       saved,
            "impressions": impressions,
            "reach":       reach,
            "save_rate":   save_rate,
            "last_updated": today_iso,
        }
        updated_count += 1

    # フォロワー数を履歴として記録
    follower_count = fetch_account_followers()
    if follower_count >= 0:
        analytics["follower_history"].append({
            "date":   today_iso,
            "count":  follower_count,
        })

    save_analytics(analytics)
    print(f"✅ 更新完了: 投稿 {updated_count} 件, フォロワー {follower_count} 人")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backfill", type=int, default=0, help="過去N日分を遡って取得")
    args = parser.parse_args()

    print(f"=== skin Instagram データ収集 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")
    if not ACCESS_TOKEN or not USER_ID:
        print("❌ APIキーが未設定。終了します。")
        sys.exit(1)

    collect_once(backfill_days=args.backfill)
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 空のanalyticsファイルを作成**

Create: `skin/skin_instagram_analytics.json`

```json
{
  "posts": {},
  "follower_history": []
}
```

- [ ] **Step 3: 既存テスト4本が引き続き通ることを確認**

Run: `pytest skin/tests/test_skin_instagram_data_collector.py -v`
Expected: 4 passed

- [ ] **Step 4: 過去30日分をローカルから手動で取得（ドライラン）**

Run: `python3 skin/skin_instagram_data_collector.py --backfill 30`
Expected output: `✅ 更新完了: 投稿 N 件, フォロワー M 人`（N >= 1, M >= 0）

→ もし `❌ APIキーが未設定` が出る場合は `.env` の `SKIN_INSTAGRAM_ACCESS_TOKEN` `SKIN_INSTAGRAM_USER_ID` を確認。

- [ ] **Step 5: 取得できたデータを確認**

Run: `python3 -c "import json; d=json.load(open('skin/skin_instagram_analytics.json')); print(f'投稿数: {len(d[\"posts\"])}, フォロワー履歴: {len(d[\"follower_history\"])}')"`
Expected output（例）: `投稿数: 15, フォロワー履歴: 1`

- [ ] **Step 6: コミット**

```bash
git add skin/skin_instagram_data_collector.py skin/skin_instagram_analytics.json
git commit -m "feat: skin Instagram データ収集本体（投稿insights/フォロワー数の取得）"
```

---

## Task 5: データ収集ワークフローをGitHub Actionsに追加

**Files:**
- Create: `.github/workflows/skin_instagram_data_collect.yml`

**目的:** データ収集スクリプトを毎日06:00 JSTに自動実行する。

- [ ] **Step 1: ワークフローファイル作成**

Create: `.github/workflows/skin_instagram_data_collect.yml`

```yaml
name: skin Instagram データ収集（毎日06:00 JST）

on:
  schedule:
    # 毎日 21:00 UTC = 06:00 JST
    - cron: "0 21 * * *"
  workflow_dispatch:  # 手動実行も可能にしておく

jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
      - name: リポジトリをチェックアウト
        uses: actions/checkout@v4

      - name: Python セットアップ
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: 依存ライブラリをインストール
        run: |
          python -m pip install --upgrade pip
          pip install requests python-dotenv

      - name: データ収集を実行
        env:
          SKIN_INSTAGRAM_ACCESS_TOKEN: ${{ secrets.SKIN_INSTAGRAM_ACCESS_TOKEN }}
          SKIN_INSTAGRAM_USER_ID:      ${{ secrets.SKIN_INSTAGRAM_USER_ID }}
        run: |
          python3 skin/skin_instagram_data_collector.py

      - name: analyticsをコミット
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add skin/skin_instagram_analytics.json
          git diff --cached --quiet && echo "変更なし、スキップ" && exit 0 || true
          git commit -m "chore: skin Instagram analytics 自動更新 $(date -u +'%Y-%m-%d %H:%M UTC')"
          git push
```

- [ ] **Step 2: YAML構文を確認**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/skin_instagram_data_collect.yml'))" && echo OK`
Expected output: `OK`

→ `yaml` が未インストールなら `pip install pyyaml` 後に再実行。

- [ ] **Step 3: コミット**

```bash
git add .github/workflows/skin_instagram_data_collect.yml
git commit -m "ci: skin Instagram データ収集ワークフローを追加（毎日06:00 JST）"
```

- [ ] **Step 4: pushしてGitHub上で手動トリガー実行**

```bash
git push -u origin skin-instagram-batch-1
```

その後、GitHubのActionsタブから `skin Instagram データ収集` ワークフローを手動実行（`workflow_dispatch`）して、初回バックフィルを起動する。

→ 手動実行時に backfill 30 をつけたい場合は、ワークフローファイルに `inputs:` を追加して `backfill` パラメータを受け取れるよう次の機会に拡張。今は CLI から `--backfill 30` を一度実行済みなので、定期実行は累積更新でOK。

---

## Task 6: carousel_content.json の構造拡張

**Files:**
- Modify: `skin/carousel_content.json`

**目的:** 各テーマに `version` `slide_count` `fixed_hashtags` `theme_hashtags` `size_mix_hashtags` を追加。既存20テーマは全て v1（5スライド）のまま保持し、Batch 1 で theme01〜04 だけ v2 にアップデートする（コンテンツ本体の差し替えはTask 9で実施）。

- [ ] **Step 1: 既存JSONを読み込んで構造拡張するスクリプトを実行**

Run（プロジェクトルートで）:

```bash
python3 - <<'EOF'
import json
from pathlib import Path

src = Path("skin/carousel_content.json")
data = json.loads(src.read_text(encoding="utf-8"))

# テーマ別ハッシュタグの仮埋め（Task 9で各テーマに合わせて精緻化）
fixed = ["肌荒れ", "大人ニキビ", "肌改善"]
size_mix = ["美容", "美肌習慣", "肌の悩み相談", "スキンケア初心者", "30代肌悩み"]

# theme_hashtagsのプレースホルダ（テーマ別の最適化はコンテンツ制作時に上書き）
default_theme = ["腸活", "スキンケア", "美肌食", "食事改善", "生活習慣", "美肌", "肌の悩み"]

for theme in data["themes"]:
    theme["version"]           = theme.get("version", "v1")
    theme["slide_count"]       = theme.get("slide_count", 5)
    theme["fixed_hashtags"]    = theme.get("fixed_hashtags", fixed)
    theme["theme_hashtags"]    = theme.get("theme_hashtags", default_theme)
    theme["size_mix_hashtags"] = theme.get("size_mix_hashtags", size_mix)

src.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✅ 構造拡張完了: {len(data['themes'])} テーマ")
EOF
```

Expected output: `✅ 構造拡張完了: 20 テーマ`

- [ ] **Step 2: 構造を確認**

Run: `python3 -c "import json; d=json.load(open('skin/carousel_content.json')); t=d['themes'][0]; print(t['version'], t['slide_count'], len(t['fixed_hashtags']), len(t['theme_hashtags']), len(t['size_mix_hashtags']))"`
Expected output: `v1 5 3 7 5`

- [ ] **Step 3: コミット**

```bash
git add skin/carousel_content.json
git commit -m "feat: carousel_content.json に version/slide_count/3層ハッシュタグキーを追加"
```

---

## Task 7: 投稿スクリプトを動的slide_countとキャプション組み立てに対応（テスト先行）

**Files:**
- Create: `skin/tests/test_skin_instagram_caption.py`
- Modify: `skin/skin_instagram_auto_post.py`

**目的:** `SLIDES_PER_CAROUSEL = 5` の固定値を廃止し、テーマごとの `slide_count` を読む。また、フック再掲＋CTA本文＋3層ハッシュタグの新キャプションを組み立てるロジックを追加。

- [ ] **Step 1: 失敗するテストを書く（ハッシュタグ結合、CTA選択、キャプション組み立て）**

Create: `skin/tests/test_skin_instagram_caption.py`

```python
# skin Instagram 投稿スクリプトの単体テスト
# 使い方: pytest skin/tests/test_skin_instagram_caption.py -v

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skin_instagram_auto_post import (
    select_cta_type,
    build_hashtag_block,
    build_caption,
)


def test_select_cta_type_save():
    """id % 4 == 1 のとき '保存' 型を返す"""
    assert select_cta_type(theme_id=1) == "保存"
    assert select_cta_type(theme_id=5) == "保存"


def test_select_cta_type_comment():
    """id % 4 == 2 のとき 'コメント' 型を返す"""
    assert select_cta_type(theme_id=2) == "コメント"
    assert select_cta_type(theme_id=6) == "コメント"


def test_select_cta_type_note():
    """id % 4 == 3 のとき 'note誘導' 型を返す"""
    assert select_cta_type(theme_id=3) == "note誘導"
    assert select_cta_type(theme_id=7) == "note誘導"


def test_select_cta_type_follow():
    """id % 4 == 0 のとき 'フォロー' 型を返す"""
    assert select_cta_type(theme_id=4) == "フォロー"
    assert select_cta_type(theme_id=8) == "フォロー"


def test_build_hashtag_block():
    """3層のハッシュタグを # 付きで結合する"""
    block = build_hashtag_block(
        fixed=["肌荒れ", "大人ニキビ", "肌改善"],
        theme=["腸活", "発酵食品"],
        size_mix=["美容", "美肌習慣"],
    )
    # # 付き、半角スペース区切り
    assert "#肌荒れ" in block
    assert "#大人ニキビ" in block
    assert "#腸活" in block
    assert "#発酵食品" in block
    assert "#美容" in block
    # 計7個
    assert block.count("#") == 7


def test_build_caption_save_type():
    """保存型(id=1)のキャプションは『保存して』を含み、ハッシュタグも末尾に付く"""
    caption = build_caption(
        theme_id=1,
        hook="化粧水を変えても、肌は治りません。",
        fixed=["肌荒れ"],
        theme=["腸活"],
        size_mix=["美容"],
    )
    assert "化粧水を変えても、肌は治りません。" in caption
    assert "保存して" in caption
    assert "#肌荒れ" in caption
    assert "#腸活" in caption
    assert "#美容" in caption


def test_build_caption_note_type():
    """note誘導型(id=3)のキャプションは『note』を含む"""
    caption = build_caption(
        theme_id=3,
        hook="8年間試した結果、効いた習慣は3つだけ。",
        fixed=["肌荒れ"],
        theme=["腸活"],
        size_mix=["美容"],
    )
    assert "note" in caption
    assert "プロフィール" in caption
```

- [ ] **Step 2: テスト実行して失敗を確認**

Run: `pytest skin/tests/test_skin_instagram_caption.py -v`
Expected: `ImportError: cannot import name 'select_cta_type'` 等

- [ ] **Step 3: 投稿スクリプトに新ロジックを追加**

`skin/skin_instagram_auto_post.py` の `# 設定` セクション直後（`HASHTAGS = ...` の上あたり）に以下の関数を追加:

```python
# =============================
# キャプション組み立てロジック（新設計 v2）
# =============================

CTA_TYPES = {
    1: "保存",       # id % 4 == 1
    2: "コメント",   # id % 4 == 2
    3: "note誘導",   # id % 4 == 3
    0: "フォロー",   # id % 4 == 0
}

CTA_BODIES = {
    "保存": (
        "肌荒れが長引く人の共通点は、内側にあります。\n"
        "8枚で「今日から変えられる習慣」をまとめました。\n\n"
        "保存して、1つずつ試してみてください。\n"
        "3ヶ月で肌が変わります。"
    ),
    "コメント": (
        "あなたの「これが効いた」を教えてください。\n"
        "コメント欄を読み返すと、実例の宝庫になっています。\n\n"
        "あなたが効いた習慣を1つだけ、コメントで教えてください。"
    ),
    "note誘導": (
        "カルーセル8枚で要点をまとめましたが、\n"
        "詳しい改善ステップは note に全部書きました。\n\n"
        "プロフィールのリンクから読めます。\n"
        "8枚で「何を」がわかり、note で「どう進めるか」がわかります。"
    ),
    "フォロー": (
        "このアカウントでは肌荒れを内側から治す習慣を毎日発信中。\n"
        "8年間試してまとめた、本当に効いた習慣だけを投稿しています。\n\n"
        "フォローして、明日の朝の投稿も一緒に。"
    ),
}


def select_cta_type(theme_id: int) -> str:
    """テーマIDから4軸ローテーションのCTA型を返す"""
    return CTA_TYPES[theme_id % 4]


def build_hashtag_block(fixed: list, theme: list, size_mix: list) -> str:
    """3層のハッシュタグを # 付き・半角スペース区切りで結合する"""
    tags = []
    for layer in (fixed, theme, size_mix):
        tags.extend(f"#{t}" for t in layer)
    return " ".join(tags)


def build_caption(
    theme_id: int,
    hook: str,
    fixed: list,
    theme: list,
    size_mix: list,
) -> str:
    """v2 キャプションを組み立てる: フック再掲 + CTA本文 + ハッシュタグ"""
    cta_type = select_cta_type(theme_id)
    cta_body = CTA_BODIES[cta_type]
    hashtags = build_hashtag_block(fixed, theme, size_mix)

    return f"{hook}\n\n{cta_body}\n\n{hashtags}"
```

- [ ] **Step 4: テスト実行して合格を確認**

Run: `pytest skin/tests/test_skin_instagram_caption.py -v`
Expected: 7 passed

- [ ] **Step 5: 投稿スクリプト本体の動的slide_count対応**

`skin/skin_instagram_auto_post.py` の以下を変更:

**変更前（24行目）**:
```python
SLIDES_PER_CAROUSEL   = 5  # 1投稿あたりのスライド枚数
```

**変更後**: この行は削除する（定数を廃止）。

**変更前（`build_carousel_image_urls` 関数、81-86行目）**:
```python
def build_carousel_image_urls(theme_id: int) -> list:
    """テーマIDからカルーセル画像のURL一覧を作る（5枚分）"""
    return [
        f"{GITHUB_CAROUSEL_BASE}/theme{theme_id:02d}_slide{i}.png"
        for i in range(1, SLIDES_PER_CAROUSEL + 1)
    ]
```

**変更後**:
```python
def build_carousel_image_urls(theme_id: int, slide_count: int) -> list:
    """テーマIDとスライド枚数からカルーセル画像のURL一覧を作る"""
    return [
        f"{GITHUB_CAROUSEL_BASE}/theme{theme_id:02d}_slide{i}.png"
        for i in range(1, slide_count + 1)
    ]
```

- [ ] **Step 6: main() の呼び出し側を新設計に合わせて修正**

`skin/skin_instagram_auto_post.py` の `main()` 内、`image_urls = build_carousel_image_urls(theme_id)` の行を以下に変更:

**変更前（365行目あたり）**:
```python
    image_urls = build_carousel_image_urls(theme_id)
    print(f"🖼️  スライド画像: {len(image_urls)}枚")
```

**変更後**:
```python
    slide_count = theme.get("slide_count", 5)  # 旧版は5、新版は8
    image_urls  = build_carousel_image_urls(theme_id, slide_count)
    print(f"🖼️  スライド画像: {len(image_urls)}枚 (version={theme.get('version', 'v1')})")
```

- [ ] **Step 7: キャプションの組み立て呼び出しを v2 ロジックに切り替え**

`skin/skin_instagram_auto_post.py` の `main()` 内、`caption = theme["caption"]` の行を以下に変更:

**変更前**:
```python
    theme_id      = theme["id"]
    caption       = theme["caption"]
```

**変更後**:
```python
    theme_id = theme["id"]

    # v2 ならビルダーで組み立て、v1 なら既存の caption をそのまま使う（後方互換）
    if theme.get("version") == "v2":
        caption = build_caption(
            theme_id=theme_id,
            hook=theme.get("hook", theme.get("slides", [{}])[0].get("title", "")),
            fixed=theme["fixed_hashtags"],
            theme=theme["theme_hashtags"],
            size_mix=theme["size_mix_hashtags"],
        )
    else:
        caption = theme["caption"]
```

- [ ] **Step 8: 既存テスト＋新テストが全て通ることを確認**

Run: `pytest skin/tests/ -v`
Expected: 11 passed (test_skin_instagram_data_collector の4本 + test_skin_instagram_caption の7本)

- [ ] **Step 9: 既存のv1テーマで投稿が壊れないことをドライランで確認**

Run: `python3 -c "
import sys; sys.path.insert(0, 'skin')
from skin_instagram_auto_post import load_carousel_content, build_carousel_image_urls
themes = load_carousel_content()
t = themes[0]
urls = build_carousel_image_urls(t['id'], t.get('slide_count', 5))
print('v1既存テーマで', len(urls), '枚のURL生成成功')
"`
Expected output: `v1既存テーマで 5 枚のURL生成成功`

- [ ] **Step 10: コミット**

```bash
git add skin/tests/test_skin_instagram_caption.py skin/skin_instagram_auto_post.py
git commit -m "feat: skin Instagram 投稿スクリプトを動的slide_count+v2キャプション組み立てに対応"
```

---

## Task 8: 8枚カルーセル用PIL生成スクリプトを新規作成

**Files:**
- Create: `skin/skin_instagram_image_gen_v4.py`

**目的:** 1080x1080 の8枚スライドを生成。役割別レイアウト（cover/hook/point/cta）を関数で分離。テーマ別 dark/accent/pale 3色を `generate_skin_cards.py` の `CARDS` 定義から流用。

- [ ] **Step 1: PILとフォント存在確認**

Run: `python3 -c "from PIL import Image, ImageDraw, ImageFont; ImageFont.truetype('/home/kenta_kamijyo/fonts/NotoSerifJP.otf', 32); print('OK')"`
Expected output: `OK`

→ NGなら `apt install fonts-noto-cjk` などでフォントを入れる。または `generate_skin_cards.py` で使われているパスを確認。

- [ ] **Step 2: 新スクリプトを作成**

Create: `skin/skin_instagram_image_gen_v4.py`

```python
# skin_instagram_image_gen_v4.py
# skin Instagram 用 8枚カルーセル画像生成スクリプト（v2 テンプレ）
# 使い方:
#   python3 skin/skin_instagram_image_gen_v4.py              # 全 v2 テーマを生成
#   python3 skin/skin_instagram_image_gen_v4.py --theme 1    # theme01 のみ生成

import os                                              # ファイル操作の道具
import json                                            # JSON 読み書きの道具
import argparse                                        # コマンドライン引数のパース
from pathlib import Path                               # ファイルパスの道具
from PIL import Image, ImageDraw, ImageFont            # 画像描画の道具

W, H        = 1080, 1080
FONT_JP     = "/home/kenta_kamijyo/fonts/NotoSerifJP.otf"
_DIR        = Path(__file__).resolve().parent
CONTENT     = _DIR / "carousel_content.json"
OUTPUT_DIR  = _DIR / "skin_instagram_carousels"
PAD_X       = 80
PAD_Y       = 120
LINE_GAP    = 10


# =====================================================
# 描画ユーティリティ
# =====================================================

def text_width(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def text_height(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


def draw_center_lines(draw, text, font, fill, y, gap=LINE_GAP):
    """改行で区切ったテキストを中央寄せで描く"""
    lines = text.split("\n")
    line_h = text_height(draw, "あ", font) + gap
    for i, line in enumerate(lines):
        x = (W - text_width(draw, line, font)) // 2
        draw.text((x, y + i * line_h), line, font=font, fill=fill)
    return y + len(lines) * line_h


def draw_left_aligned(draw, text, font, fill, x, y, gap=LINE_GAP, max_width=None):
    """テキストを左寄せで描く（長文用、行送りあり）"""
    lines = text.split("\n")
    line_h = text_height(draw, "あ", font) + gap
    for i, line in enumerate(lines):
        draw.text((x, y + i * line_h), line, font=font, fill=fill)
    return y + len(lines) * line_h


def draw_footer_bar(draw, dark_color):
    """全スライド共通のフッターバー（細いダーク帯＋ブランドコピー）"""
    bar_h = 50
    draw.rectangle([0, H - bar_h, W, H], fill=dark_color)
    font  = ImageFont.truetype(FONT_JP, 22)
    brand = "@skin_reset_jp ｜ 毎日肌改善のヒントを投稿中"
    bb    = draw.textbbox((0, 0), brand, font=font)
    bw    = bb[2] - bb[0]
    bh    = bb[3] - bb[1]
    light = tuple(min(c + 130, 255) for c in dark_color)
    draw.text(((W - bw) // 2, H - bar_h + (bar_h - bh) // 2), brand, font=font, fill=light)


# =====================================================
# スライド描画関数（役割別）
# =====================================================

def draw_cover(slide, colors, output_path):
    """スライド1: カバー（フック）"""
    dark, accent, pale = colors
    img  = Image.new("RGB", (W, H), dark)
    draw = ImageDraw.Draw(img)

    font_title = ImageFont.truetype(FONT_JP, 72)
    font_sub   = ImageFont.truetype(FONT_JP, 30)

    # メインタイトル（中央寄せ、複数行）
    title  = slide["title"]
    bottom = draw_center_lines(draw, title, font_title, pale, y=H // 2 - 220, gap=20)

    # 区切り線
    draw.rectangle([(W - 80) // 2, bottom + 30, (W + 80) // 2, bottom + 34], fill=accent)

    # サブタイトル
    if slide.get("subtitle"):
        draw_center_lines(draw, slide["subtitle"], font_sub, pale, y=bottom + 60, gap=8)

    draw_footer_bar(draw, dark)
    img.save(output_path, "PNG")


def draw_hook(slide, colors, output_path):
    """スライド2: 共感フック（問題提起）"""
    dark, accent, pale = colors
    img  = Image.new("RGB", (W, H), (250, 249, 246))
    draw = ImageDraw.Draw(img)

    # 上部のアクセント帯
    draw.rectangle([0, 0, W, 120], fill=accent)
    font_label = ImageFont.truetype(FONT_JP, 28)
    label = "こんな悩みはありませんか？"
    bb = draw.textbbox((0, 0), label, font=font_label)
    draw.text((PAD_X, 120 // 2 - (bb[3] - bb[1]) // 2), label, font=font_label, fill=(255, 255, 255))

    # 本文
    font_body = ImageFont.truetype(FONT_JP, 40)
    body = slide.get("body", "")
    draw_left_aligned(draw, body, font_body, (28, 34, 28), x=PAD_X, y=200, gap=16)

    draw_footer_bar(draw, dark)
    img.save(output_path, "PNG")


def draw_point(slide, colors, output_path, point_number):
    """スライド3〜7: ポイントスライド（1枚1要点、4文構造）"""
    dark, accent, pale = colors
    img  = Image.new("RGB", (W, H), (250, 249, 246))
    draw = ImageDraw.Draw(img)

    # 番号バッジ
    badge_size = 90
    badge_x    = PAD_X
    badge_y    = PAD_Y
    draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size], fill=accent)
    font_num = ImageFont.truetype(FONT_JP, 48)
    num_text = f"{point_number}"
    bb = draw.textbbox((0, 0), num_text, font=font_num)
    nw, nh = bb[2] - bb[0], bb[3] - bb[1]
    draw.text((badge_x + (badge_size - nw) // 2, badge_y + (badge_size - nh) // 2 - 5), num_text, font=font_num, fill=(255, 255, 255))

    # 見出し
    font_heading = ImageFont.truetype(FONT_JP, 56)
    heading      = slide.get("heading", "")
    draw_left_aligned(draw, heading, font_heading, dark, x=badge_x + badge_size + 30, y=badge_y + 15, gap=10)

    # 本文（事実→具体例→数字→意味の4文）
    font_body = ImageFont.truetype(FONT_JP, 32)
    body      = slide.get("body", "")
    draw_left_aligned(draw, body, font_body, (28, 34, 28), x=PAD_X, y=badge_y + badge_size + 80, gap=14)

    draw_footer_bar(draw, dark)
    img.save(output_path, "PNG")


def draw_cta(slide, colors, output_path):
    """スライド8: CTA（4軸ローテーション）"""
    dark, accent, pale = colors
    img  = Image.new("RGB", (W, H), dark)
    draw = ImageDraw.Draw(img)

    font_main = ImageFont.truetype(FONT_JP, 80)
    font_sub  = ImageFont.truetype(FONT_JP, 32)

    main_text = slide.get("text", "")
    bottom    = draw_center_lines(draw, main_text, font_main, pale, y=H // 2 - 200, gap=20)

    draw.rectangle([(W - 80) // 2, bottom + 30, (W + 80) // 2, bottom + 34], fill=accent)

    sub_text = slide.get("sub", "")
    if sub_text:
        draw_center_lines(draw, sub_text, font_sub, pale, y=bottom + 60, gap=10)

    draw_footer_bar(draw, dark)
    img.save(output_path, "PNG")


# =====================================================
# テーマ別配色（generate_skin_cards.py の CARDS から流用）
# =====================================================

# theme_id -> (dark, accent, pale)
THEME_COLORS = {
    1:  ((28, 42, 65),   (70, 140, 190),  (228, 240, 250)),
    2:  ((22, 48, 32),   (72, 160, 100),  (232, 246, 236)),
    3:  ((58, 22, 22),   (200, 80, 80),   (252, 232, 232)),
    4:  ((22, 50, 55),   (50, 160, 170),  (228, 246, 248)),
    5:  ((30, 28, 60),   (110, 100, 200), (238, 236, 252)),
    6:  ((52, 38, 18),   (180, 130, 50),  (252, 244, 224)),
    7:  ((55, 32, 18),   (210, 110, 50),  (252, 238, 224)),
    8:  ((50, 28, 45),   (170, 80, 150),  (250, 232, 246)),
    9:  ((30, 48, 22),   (120, 170, 60),  (238, 248, 224)),
    10: ((20, 46, 36),   (50, 170, 120),  (224, 246, 238)),
    11: ((38, 36, 20),   (180, 155, 50),  (252, 248, 220)),
    12: ((38, 22, 58),   (130, 80, 200),  (240, 232, 252)),
    13: ((18, 38, 58),   (50, 140, 200),  (224, 238, 252)),
    14: ((32, 44, 28),   (100, 155, 80),  (234, 246, 228)),
    15: ((30, 50, 40),   (60, 170, 110),  (220, 248, 234)),
    16: ((28, 40, 58),   (70, 130, 195),  (224, 238, 252)),
    17: ((50, 35, 55),   (160, 90, 180),  (244, 232, 250)),
    18: ((18, 46, 54),   (45, 155, 175),  (220, 245, 250)),
    19: ((55, 28, 28),   (190, 80, 80),   (252, 228, 228)),
    20: ((26, 44, 30),   (80, 165, 95),   (228, 248, 232)),
}


# =====================================================
# テーマ生成
# =====================================================

def generate_theme(theme: dict) -> None:
    """1テーマ分の8枚を生成する"""
    theme_id    = theme["id"]
    slides      = theme["slides"]
    slide_count = theme.get("slide_count", 5)

    if theme.get("version") != "v2":
        print(f"  ⏭️  theme{theme_id:02d}: v1 のためスキップ")
        return

    colors = THEME_COLORS.get(theme_id)
    if not colors:
        print(f"❌ theme{theme_id:02d}: 配色未定義")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    point_number = 0
    for i, slide in enumerate(slides, start=1):
        output = OUTPUT_DIR / f"theme{theme_id:02d}_slide{i}.png"
        slide_type = slide.get("type")

        if slide_type == "cover":
            draw_cover(slide, colors, output)
        elif slide_type == "hook":
            draw_hook(slide, colors, output)
        elif slide_type == "point":
            point_number += 1
            draw_point(slide, colors, output, point_number)
        elif slide_type == "cta":
            draw_cta(slide, colors, output)
        else:
            print(f"  ⚠️ theme{theme_id:02d} slide{i}: 未対応タイプ '{slide_type}'")
            continue

        print(f"  ✅ theme{theme_id:02d}_slide{i}.png ({slide_type})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", type=int, help="指定テーマだけ生成（省略時は全 v2 を生成）")
    args = parser.parse_args()

    data   = json.loads(CONTENT.read_text(encoding="utf-8"))
    themes = data["themes"]

    if args.theme:
        themes = [t for t in themes if t["id"] == args.theme]
        if not themes:
            print(f"❌ theme{args.theme:02d} が見つかりません")
            return

    print(f"🎨 画像生成開始: {len(themes)} テーマ")
    for theme in themes:
        generate_theme(theme)
    print("🎉 完了")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 構文チェック**

Run: `python3 -m py_compile skin/skin_instagram_image_gen_v4.py && echo OK`
Expected output: `OK`

- [ ] **Step 4: コミット**

```bash
git add skin/skin_instagram_image_gen_v4.py
git commit -m "feat: skin Instagram 8枚カルーセル用 PIL 生成スクリプト v4 を新規追加"
```

---

## Task 9: Batch 1（theme01〜04）の v2 コンテンツを制作

**Files:**
- Modify: `skin/carousel_content.json`

**目的:** Batch 1 対象の4テーマについて、`version: "v2"` `slide_count: 8` に切り替え、`slides` を 8枚構造（cover/hook/point×5/cta）に書き直す。3層ハッシュタグも各テーマに合わせて精緻化する。

**設計参照:**
- フック型: `id % 3` → 1=数字 / 2=逆張り / 0=エピソード（theme03は数字型）
- CTA型: `id % 4` → 1=保存 / 2=コメント / 3=note誘導 / 0=フォロー

→ Batch 1のテーマ別割り当て:
| ID | テーマ | フック型 | CTA型 |
|---|---|---|---|
| 1 | 肌荒れ原因チェック | 数字 | 保存 |
| 2 | 腸と肌のつながり | 逆張り | コメント |
| 3 | 砂糖とニキビ | 数字 | note誘導 |
| 4 | 洗顔のやりすぎ | 逆張り | フォロー |

### Step群

- [ ] **Step 1: theme01（数字型・保存型）の v2 コンテンツを反映**

`skin/carousel_content.json` の `themes[0]`（id=1）を以下のように差し替える。ファイルを開いて該当部分のみ書き換え:

```json
{
  "id": 1,
  "version": "v2",
  "slide_count": 8,
  "hook": "肌荒れを長引かせる\n7つの習慣",
  "fixed_hashtags": ["肌荒れ", "大人ニキビ", "肌改善"],
  "theme_hashtags": ["スキンケア", "肌荒れチェック", "美肌習慣", "肌の悩み", "美肌食", "生活改善", "腸活"],
  "size_mix_hashtags": ["美容", "美肌", "肌の悩み相談", "スキンケア初心者", "30代肌悩み"],
  "slides": [
    {"type": "cover", "title": "肌荒れを長引かせる\n7つの習慣", "subtitle": "あなたも当てはまるかも"},
    {"type": "hook",  "body": "化粧水を3年変え続けても、\n肌は治りませんでした。\n\n原因は肌の外側ではなく、\n内側にありました。\n\n7つのチェックで原因を見つけられます。"},
    {"type": "point", "heading": "甘い飲み物を毎日飲んでいる", "body": "事実: 液体の糖質は固形より吸収が速い。\n具体例: 砂糖入りコーヒー・ジュース・乳酸菌飲料。\n数字: 血糖値が急上昇して皮脂分泌ホルモンが過剰になる傾向。\n意味: 飲み物を水や緑茶に変えるだけで皮脂は落ち着く。"},
    {"type": "point", "heading": "就寝が深夜0時を過ぎる",         "body": "事実: 成長ホルモンの分泌ピークは22〜翌2時。\n具体例: スマホで寝るのが0時超えになる夜。\n数字: 6時間睡眠でも0時前と0時後で修復力が大きく違う報告。\n意味: 「23時には布団に入る」を週に5日できれば肌は変わる。"},
    {"type": "point", "heading": "パン・麺が毎日の主食",             "body": "事実: 小麦のグルテンは腸の粘膜を刺激する。\n具体例: 朝パン、昼パスタ、夜うどんの生活。\n数字: 2週間減らすだけで腹部膨満感が和らぐ傾向の報告あり。\n意味: 主食の半分を玄米や芋類に置き換えるところから始める。"},
    {"type": "point", "heading": "洗顔を1日3回以上している",        "body": "事実: 皮脂を取りすぎると肌は「乾燥」と判断する。\n具体例: 朝・昼・夜と泡洗顔フォームを使う。\n数字: 過剰分泌は皮脂量が通常の1.5〜2倍に増える目安。\n意味: 夜1回・朝はぬるま湯だけ、に減らすと毛穴詰まりが減る。"},
    {"type": "point", "heading": "便秘または下痢が続いている",       "body": "事実: 腸壁が荒れると炎症物質が全身に回る。\n具体例: 朝の排便がなく、夕方おなかが張る日が続く。\n数字: 腸内環境の乱れは2週間以内で変化が出る報告がある。\n意味: みそ汁＋発酵食品＋水で「内側の通り」を整える。"},
    {"type": "cta",   "text": "保存して\n1つずつ試してね", "sub": "3ヶ月で\n肌は変わります"}
  ],
  "caption": ""
}
```

→ `caption` フィールドは空でOK（投稿スクリプトが v2 のときは `hook` から動的に組み立てる）。

- [ ] **Step 2: theme02（逆張り型・コメント型）の v2 コンテンツを反映**

`themes[1]`（id=2）を以下に差し替え:

```json
{
  "id": 2,
  "version": "v2",
  "slide_count": 8,
  "hook": "化粧水を変えても\n肌は治りません",
  "fixed_hashtags": ["肌荒れ", "大人ニキビ", "肌改善"],
  "theme_hashtags": ["腸活", "発酵食品", "腸内環境", "食事改善", "美肌食", "みそ汁", "納豆"],
  "size_mix_hashtags": ["美容", "美肌習慣", "肌の悩み相談", "スキンケア初心者", "30代肌悩み"],
  "slides": [
    {"type": "cover", "title": "化粧水を変えても\n肌は治りません", "subtitle": "答えは腸にありました"},
    {"type": "hook",  "body": "肌荒れの原因は\n肌の外側ではなく、\n「腸」にあることが多いです。\n\n腸内環境と肌の炎症は\n直結していることが分かっています。"},
    {"type": "point", "heading": "朝のみそ汁から始める",       "body": "事実: 麹菌と乳酸菌が善玉菌を増やす。\n具体例: 1日1杯のみそ汁を朝食に入れる。\n数字: 1杯で約100億の乳酸菌を摂れる目安。\n意味: 内側からの改善は、朝1杯から始められる。"},
    {"type": "point", "heading": "毎日「発酵食品」を1つ加える", "body": "事実: 善玉菌が腸壁のバリアを強くする。\n具体例: 納豆・ぬか漬け・キムチを夜に1品。\n数字: 2週間で便通の変化を実感する人が多い傾向。\n意味: 「毎日1つ」を続ければ腸の地盤が整う。"},
    {"type": "point", "heading": "甘い飲み物を水に置き換える", "body": "事実: 糖質は腸内の悪玉菌のエサになる。\n具体例: ジュース・砂糖入りコーヒー・甘い乳酸菌飲料。\n数字: 1日1L以上の水分補給が腸に必要な目安。\n意味: 善玉菌の住みやすい環境は飲み物から作れる。"},
    {"type": "point", "heading": "食物繊維を毎食1品入れる",     "body": "事実: 食物繊維は善玉菌のエサになる。\n具体例: 野菜・きのこ・海藻・もち麦・玄米。\n数字: 1日20g以上が目安、現代人は平均14gで不足傾向。\n意味: 善玉菌は「食事のエサ」なしには増えない。"},
    {"type": "point", "heading": "腸が整うと肌に出る順番",       "body": "事実: 腸が整う → 全身炎症が下がる → 肌に出る。\n具体例: 便通改善 → 赤みが引く → ニキビが減る。\n数字: 4〜8週間で肌の変化を感じる人が多い目安。\n意味: 焦らず「内側から」を続けることが最短ルート。"},
    {"type": "cta",   "text": "あなたが効いた\n習慣を教えて", "sub": "コメント欄で\nみんなの実例を共有"}
  ],
  "caption": ""
}
```

- [ ] **Step 3: theme03（数字型・note誘導型）の v2 コンテンツを反映**

`themes[2]`（id=3）を以下に差し替え:

```json
{
  "id": 3,
  "version": "v2",
  "slide_count": 8,
  "hook": "肌荒れを悪化させる\n食べ物ワースト5",
  "fixed_hashtags": ["肌荒れ", "大人ニキビ", "肌改善"],
  "theme_hashtags": ["食事改善", "美肌食", "糖質制限", "血糖値", "腸活", "ニキビ食事", "美肌レシピ"],
  "size_mix_hashtags": ["美容", "美肌習慣", "肌の悩み相談", "スキンケア初心者", "30代肌悩み"],
  "slides": [
    {"type": "cover", "title": "肌荒れを悪化させる\n食べ物ワースト5", "subtitle": "知らずに毎日食べているかも"},
    {"type": "hook",  "body": "「スキンケアは合ってるはずなのに\n肌が治らない」\n\nそれは食事が原因かもしれません。\n肌に悪影響の強い5つを知ってください。"},
    {"type": "point", "heading": "砂糖入り飲み物",       "body": "事実: 液体の糖質は固形より吸収が速い。\n具体例: ジュース・甘いコーヒー・甘いヨーグルト飲料。\n数字: 血糖値が30分で急上昇する傾向。\n意味: まず1日1本を水か緑茶に置き換える。"},
    {"type": "point", "heading": "白い小麦製品",         "body": "事実: グリセミック指数が高く血糖を急上昇させる。\n具体例: 食パン・パスタ・うどん・菓子パン。\n数字: 白米よりGI値が10〜15ポイント高い傾向。\n意味: 主食の半分を玄米や芋に変えるだけで肌が変わる。"},
    {"type": "point", "heading": "乳製品の摂りすぎ",     "body": "事実: 乳製品のIGF-1とホエイが皮脂腺を刺激する。\n具体例: 牛乳・チーズ・甘いヨーグルト。\n数字: 1日コップ2杯以上で肌荒れ報告が増える傾向。\n意味: 「毎日」をやめて「週2〜3回」に減らす。"},
    {"type": "point", "heading": "揚げ物・スナック菓子", "body": "事実: 酸化した油が腸の粘膜を傷つける。\n具体例: スナック・ファストフード・コンビニ揚げ物。\n数字: 油の酸化は加熱後30分から進む報告。\n意味: 食べる頻度を週1回以下に下げる。"},
    {"type": "point", "heading": "アルコールの常習",     "body": "事実: 肝臓の解毒機能が落ち、腸の炎症が悪化する。\n具体例: 毎日の晩酌・週末のまとめ飲み。\n数字: 週2日の休肝日で肝数値が改善する報告。\n意味: 「飲まない日」を週に2日作ることから始める。"},
    {"type": "cta",   "text": "改善の全工程は\nnoteにまとめた", "sub": "プロフィールリンクから\nすぐ読めます"}
  ],
  "caption": ""
}
```

- [ ] **Step 4: theme04（逆張り型・フォロー型）の v2 コンテンツを反映**

`themes[3]`（id=4）を以下に差し替え:

```json
{
  "id": 4,
  "version": "v2",
  "slide_count": 8,
  "hook": "洗顔を減らしたら\n肌が整った話",
  "fixed_hashtags": ["肌荒れ", "大人ニキビ", "肌改善"],
  "theme_hashtags": ["スキンケア", "洗顔", "肌バリア", "敏感肌", "美肌習慣", "毛穴ケア", "ニキビケア"],
  "size_mix_hashtags": ["美容", "美肌", "肌の悩み相談", "スキンケア初心者", "30代肌悩み"],
  "slides": [
    {"type": "cover", "title": "洗顔を減らしたら\n肌が整った話", "subtitle": "「足す」より「引く」が答え"},
    {"type": "hook",  "body": "1日3回洗顔していたとき、\n肌はずっと荒れていました。\n\n夜1回・朝はぬるま湯だけに変えたら、\n2週間で肌が落ち着いてきました。"},
    {"type": "point", "heading": "皮脂を取りすぎている",     "body": "事実: 過剰な洗顔が肌のバリア機能を壊す。\n具体例: 朝晩フォーム洗顔＋昼の洗顔シート。\n数字: 皮脂膜の再生には数時間かかる目安。\n意味: 取りすぎは「乾燥→過剰分泌」のループを作る。"},
    {"type": "point", "heading": "夜1回だけにする",          "body": "事実: 夜だけで1日の汚れは十分に落とせる。\n具体例: 夜は泡で優しく、朝はぬるま湯だけ。\n数字: 2週間で皮脂バランスが整い始める報告。\n意味: 「やらない勇気」が肌バリアを取り戻す。"},
    {"type": "point", "heading": "こすらず泡で包む",          "body": "事実: 摩擦は肌の表皮を傷つけて炎症を招く。\n具体例: ゴシゴシ洗い・タオルで強くこする。\n数字: 摩擦の刺激は紫外線の数倍ダメージという報告も。\n意味: 「触らない・こすらない」がスキンケアの基本。"},
    {"type": "point", "heading": "ぬるま湯（35〜38℃）で",     "body": "事実: 熱いお湯は皮脂を奪いすぎる。\n具体例: 冬の熱いシャワー・40℃以上の洗顔。\n数字: 38℃を超えると皮脂膜が溶け出す傾向。\n意味: 「気持ちいい温度」より「肌が許す温度」で。"},
    {"type": "point", "heading": "化粧水1本で十分",            "body": "事実: 多成分の重ね塗りは刺激源になる。\n具体例: 美容液5種＋ブースター＋オイルの重ね塗り。\n数字: バリア機能が低下している肌は「引き算」で回復する報告。\n意味: シンプルなケアが、肌の回復力を最大化する。"},
    {"type": "cta",   "text": "毎日肌改善の\nヒントを発信中", "sub": "フォローして\n明日の朝の投稿も一緒に"}
  ],
  "caption": ""
}
```

- [ ] **Step 5: JSON構文を確認**

Run: `python3 -c "import json; d=json.load(open('skin/carousel_content.json')); print('v2 themes:', [t['id'] for t in d['themes'] if t.get('version')=='v2'])"`
Expected output: `v2 themes: [1, 2, 3, 4]`

- [ ] **Step 6: コミット**

```bash
git add skin/carousel_content.json
git commit -m "feat: Batch 1 (theme01〜04) の v2 コンテンツを反映"
```

---

## Task 10: Batch 1 の画像生成と目視確認

**Files:**
- 出力: `skin/skin_instagram_carousels/theme0[1-4]_slide[1-8].png`

**目的:** Batch 1の4テーマ × 8枚 = 32枚の画像を生成し、目視で確認する。

- [ ] **Step 1: Batch 1の画像を生成**

Run: `python3 skin/skin_instagram_image_gen_v4.py --theme 1 && python3 skin/skin_instagram_image_gen_v4.py --theme 2 && python3 skin/skin_instagram_image_gen_v4.py --theme 3 && python3 skin/skin_instagram_image_gen_v4.py --theme 4`
Expected output（例）: 各テーマ8枚 = 計32回の `✅ themeNN_slideX.png` ログ

- [ ] **Step 2: 生成された画像枚数を確認**

Run: `ls skin/skin_instagram_carousels/theme0[1-4]_slide*.png | wc -l`
Expected output: `32`

→ 旧 5枚版の画像（`theme0N_slide1.png`〜`theme0N_slide5.png`）は上書きされる。新8枚目（`theme0N_slide8.png`）は新規作成される。

- [ ] **Step 3: 目視確認（重要）**

Threadsと違いカルーセルは目で見る成果物が全て。以下を一枚ずつ確認:

- カバーに大きく見やすいフックが入っているか
- フッターバー（@skin_reset_jp）が全スライドに入っているか
- ポイントスライドで番号バッジ①②③④⑤が見やすいか
- 文字が画像枠からはみ出していないか
- 配色（dark/accent/pale）が読みやすいか

問題があればテーマごとに `carousel_content.json` のテキストを調整し、再生成。

- [ ] **Step 4: コミット**

```bash
git add skin/skin_instagram_carousels/theme0[1-4]_slide*.png
git commit -m "feat: Batch 1 (theme01〜04) の v2 画像 32枚を生成"
```

---

## Task 11: 検証レポートスクリプトを新規作成

**Files:**
- Create: `skin/skin_instagram_report.py`

**目的:** バッチごとに、保存率・リーチ・フォロワー増加を旧版ベースラインと比較してレポートを出力する。Batch 1リリース後2週間（〜2026-06-06）の時点で初回実行する。

- [ ] **Step 1: スクリプトを新規作成**

Create: `skin/skin_instagram_report.py`

```python
# skin_instagram_report.py
# skin Instagram バッチごとの保存率検証レポート
# 使い方: python3 skin/skin_instagram_report.py --batch 1

import argparse                       # コマンドライン引数のパース
import json                           # JSON読み書き
from pathlib import Path              # ファイルパスの道具
from datetime import datetime         # 日時の道具

_DIR              = Path(__file__).resolve().parent
ANALYTICS_FILE    = _DIR / "skin_instagram_analytics.json"
BATCH_FILE        = _DIR / "skin_instagram_batch_progress.json"
CONTENT_FILE      = _DIR / "carousel_content.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_batch_themes(batch_id: int) -> list[int]:
    """バッチ番号から該当テーマIDのリストを返す"""
    data    = load_json(BATCH_FILE)
    batches = data.get("batches", {})
    batch   = batches.get(str(batch_id))
    if not batch:
        raise ValueError(f"Batch {batch_id} が見つかりません")
    return batch["themes"]


def get_v1_baseline_save_rate(analytics: dict, exclude_post_ids: set) -> float:
    """旧版（v1）の平均保存率を計算する。指定の投稿IDは除外する（v2投稿の混在を防ぐ）"""
    rates = []
    for post_id, post_data in analytics.get("posts", {}).items():
        if post_id in exclude_post_ids:
            continue
        rate = post_data.get("save_rate", 0.0)
        if rate > 0:
            rates.append(rate)
    if not rates:
        return 0.0
    return round(sum(rates) / len(rates), 2)


def get_v2_save_rates_by_theme(analytics: dict, target_theme_ids: list[int]) -> dict[int, list[float]]:
    """v2投稿をテーマ別に集計する（captionに theme_id を埋め込んだ前提だが暫定で空辞書を返す）"""
    # 注: Instagram投稿APIには独自タグを埋める手段が限定的なので、
    #     初版ではcaption冒頭のフックでテーマ識別。または投稿日とbatch_progressの突合で識別。
    # ここでは Batch リリース後の投稿日時で簡易判定する。
    return {tid: [] for tid in target_theme_ids}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, required=True, help="検証対象のバッチ番号 (1-5)")
    args = parser.parse_args()

    batch_id     = args.batch
    theme_ids    = get_batch_themes(batch_id)
    analytics    = load_json(ANALYTICS_FILE)

    # ベースライン: バッチリリース前の全投稿の平均保存率
    baseline = get_v1_baseline_save_rate(analytics, exclude_post_ids=set())

    # v2投稿の保存率（テーマ別）— 初版では暫定実装
    v2_rates = get_v2_save_rates_by_theme(analytics, theme_ids)

    print(f"=== Batch {batch_id} 検証レポート（{datetime.now().strftime('%Y-%m-%d')}）===\n")
    print(f"対象テーマ: {theme_ids}")
    print(f"v1ベースライン平均保存率: {baseline}%\n")

    print("テーマ別 v2 保存率（v1ベースライン比）:")
    for tid in theme_ids:
        rates = v2_rates.get(tid, [])
        if not rates:
            print(f"  テーマ{tid}: データ不足（投稿後の蓄積待ち）")
            continue
        avg = round(sum(rates) / len(rates), 2)
        delta = round((avg - baseline) / baseline * 100, 1) if baseline > 0 else 0
        flag = "🟢" if delta >= 30 else "🟡" if delta >= -10 else "🔴"
        print(f"  テーマ{tid}: v2={avg}%  v1={baseline}%  → {delta:+.1f}% {flag}")

    print("\nロールバック判定:")
    print("  黄信号(-10%下落で3日連続) | 赤信号(-30%下落で2日連続)")
    print("  Batch 1 はベースライン蓄積が薄い場合、絶対値判定 (黄1.5%/赤0.8%) を併用すること。")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 構文チェック**

Run: `python3 -m py_compile skin/skin_instagram_report.py && echo OK`
Expected output: `OK`

- [ ] **Step 3: 試しに実行（実データが薄くてもエラーにならないことを確認）**

Run: `python3 skin/skin_instagram_report.py --batch 1`
Expected output: ヘッダーと「データ不足（投稿後の蓄積待ち）」のメッセージが出力される

- [ ] **Step 4: コミット**

```bash
git add skin/skin_instagram_report.py
git commit -m "feat: skin Instagram バッチ検証レポート (初版・データ蓄積後に拡張)"
```

→ 注: 初版はテーマ別 v2 集計が暫定実装（v2_rates が空辞書）。Batch 1リリース後にcaption識別ロジックを追加して `get_v2_save_rates_by_theme` を完成させる（Task 13 内で対応予定）。

---

## Task 12: Batch 1 リリース

**Files:**
- Modify: `skin/skin_instagram_batch_progress.json`
- 全変更ファイルを push

**目的:** Batch 1の変更をmainにマージし、本番のGitHub Actionsで新版が投稿される状態にする。

- [ ] **Step 1: バッチ進行管理ファイルをリリース済みに更新**

`skin/skin_instagram_batch_progress.json` の `batches.1.status` を `released` に変更:

```bash
python3 - <<'EOF'
import json
from pathlib import Path
p = Path("skin/skin_instagram_batch_progress.json")
d = json.loads(p.read_text(encoding="utf-8"))
d["batches"]["1"]["status"] = "released"
d["batches"]["1"]["notes"]  = "2026-05-24 リリース完了。データ収集は2026-05-18から先行稼働中。"
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("✅ Batch 1 を released に更新")
EOF
```

Expected output: `✅ Batch 1 を released に更新`

- [ ] **Step 2: 進行ファイルの変更をコミット**

```bash
git add skin/skin_instagram_batch_progress.json
git commit -m "chore: skin Instagram Batch 1 を released に更新"
```

- [ ] **Step 3: 変更内容を確認**

Run: `git log --oneline main..HEAD`
Expected output: Task 1〜12 で作成した全コミットが順に並ぶこと

- [ ] **Step 4: PRを作るかmainに直接マージするか確認**

このリポジトリの普段のフローに合わせる。プルリクエストを作る場合:

```bash
gh pr create --title "skin Instagram Batch 1 リライト" --body "$(cat <<'EOF'
## Summary
- 8枚カルーセル × 3軸フック × 4軸CTAでBatch 1(theme01〜04)を全面リライト
- Instagram Graph API データ収集スクリプトを新規実装
- バッチ進行管理 / 検証レポートスクリプトを新規追加

## Test plan
- [ ] pytest skin/tests/ が全件PASS
- [ ] skin/skin_instagram_carousels/ に32枚の v2 画像が存在
- [ ] python3 skin/skin_instagram_data_collector.py --backfill 30 が正常終了
- [ ] python3 skin/skin_instagram_image_gen_v4.py --theme 1 が正常終了

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

→ ユーザーがmain直接プッシュ運用なら以下:

```bash
git checkout main
git merge --no-ff skin-instagram-batch-1
git push origin main
```

- [ ] **Step 5: リリース後の初回投稿を確認**

リリース後の最初のスケジュール時刻（次の 7:30 / 12:30 / 18:30 / 21:30 JST）に投稿される予定のテーマが Batch 1 のどれかになるよう、`skin_instagram_progress.json` の `next_index` を確認:

Run: `cat skin/skin_instagram_progress.json`

→ 現在 `next_index=5` のため、次の投稿は theme06（v1）。Batch 1（theme01〜04）が次に登場するのは next_index がループして 0〜3 に戻ったとき。

→ 投稿順を強制的に変えたい場合は、`next_index` を 0 に手動で書き換える（リリース直後に Batch 1 を最初に投稿したいなら）。ユーザーの意向を確認してから実施。

- [ ] **Step 6: 初動チェック（24時間後）**

リリース 24時間後に以下を確認:
- Instagram アカウント（@skin_reset_jp）に v2 カルーセルが投稿されているか
- 画像が正しく8枚表示されているか
- キャプションのフックとCTAが新設計通りか
- 警告コメント・薬機法指摘がないか

→ 異常があれば即ロールバック:
```bash
git checkout skin-instagram-batch-1-before -- skin/carousel_content.json skin/skin_instagram_carousels/
git commit -m "Rollback skin Instagram batch 1"
git push
```

---

## Task 13: Batch 2〜5 への展開手順（ドキュメント化）

**Files:**
- このplanファイル自体に Batch 2〜5の手順を追記、または別planファイルを作る

**目的:** Batch 1完走後に同じ流れを繰り返すための手順を明文化する。

- [ ] **Step 1: Batch N 共通の作業手順を docs に書き起こす**

各 Batch N で実行する作業は以下と同じ:

1. `git checkout -b skin-instagram-batch-N`
2. `git tag skin-instagram-batch-N-before main && git push origin skin-instagram-batch-N-before`
3. Task 9 と同じ手順で、対象4テーマ（Batch N の `themes`）の v2 コンテンツを `carousel_content.json` に反映
   - フック型は `id % 3`、CTA型は `id % 4` で機械的に決まる
4. Task 10 と同じ手順で 4テーマ × 8枚 = 32枚の画像を生成
5. Task 12 と同じ手順で `skin_instagram_batch_progress.json` の `current_batch` を N+1 に、`batches.N.status` を `released` に更新してリリース
6. 旧バッチの検証レポートを `python3 skin/skin_instagram_report.py --batch N-1` で確認
7. 学習を次バッチ制作に反映（伸び悩んだテーマのフック型・CTA型を変える等）

- [ ] **Step 2: Batch 1リリース後、`skin_instagram_report.py` の v2 集計ロジック完成**

初版では `get_v2_save_rates_by_theme` が空辞書を返す暫定実装。Batch 1 投稿後、以下のように完成させる:

```python
def get_v2_save_rates_by_theme(analytics: dict, target_theme_ids: list[int]) -> dict[int, list[float]]:
    """
    v2投稿をテーマ別に集計する。
    投稿のキャプション冒頭（フック）と carousel_content.json の hook 文字列を突き合わせて
    テーマIDを逆引きする。
    """
    # 1. carousel_content.json から hook -> theme_id の対応表を作る
    content    = load_json(CONTENT_FILE)
    hook_to_id = {}
    for theme in content["themes"]:
        if theme.get("version") != "v2":
            continue
        hook_to_id[theme.get("hook", "")] = theme["id"]

    # 2. analytics の各投稿のcaption冒頭をマッチさせる
    result = {tid: [] for tid in target_theme_ids}
    for post_id, post_data in analytics.get("posts", {}).items():
        caption = post_data.get("caption", "")
        for hook, tid in hook_to_id.items():
            if hook and caption.startswith(hook[:30]):  # 先頭30字でマッチ
                if tid in target_theme_ids:
                    result[tid].append(post_data.get("save_rate", 0.0))
                break
    return result
```

→ この拡張は Batch 1 リリース後（投稿が積まれてから）実装する。今は Task 11 の暫定版でOK。

- [ ] **Step 3: 完了**

Batch 5 検証完了時点（2026-07-04）で:
- 全20テーマが v2 化済み
- `skin_instagram_analytics.json` に2週間以上の v2 データ蓄積
- 全テーマで保存率+30%以上を達成（または保存率の絶対値が改善）

→ 達成後の発展（設計書 5/5 セクション参照）:
- 21〜30テーマの新規追加
- カバー画像を Higgsfield AI で生成
- ronin Instagram に同フレーム展開

---

## 全体の動作確認チェックリスト（Batch 1 リリース前）

リリース前最終チェック:

- [ ] `pytest skin/tests/` が 11件 PASS
- [ ] `python3 skin/skin_instagram_data_collector.py` がエラーなく完走
- [ ] `python3 skin/skin_instagram_image_gen_v4.py --theme 1` が `theme01_slide1.png`〜`theme01_slide8.png` を生成
- [ ] `python3 skin/skin_instagram_report.py --batch 1` がヘッダーを出力
- [ ] `carousel_content.json` で theme01〜04 が `version: "v2"`、`slide_count: 8`、`slides` が8枚
- [ ] `skin_instagram_carousels/` に theme01〜04 の slide1〜slide8 が全て存在（計32枚）
- [ ] `skin_instagram_batch_progress.json` の `current_batch=1`、`batches.1.status` が適切
- [ ] `.github/workflows/skin_instagram_data_collect.yml` が main にマージ済みで06:00 JSTに自動実行されている
- [ ] `git tag -l skin-instagram-batch-*` で `skin-instagram-batch-1-before` が存在
