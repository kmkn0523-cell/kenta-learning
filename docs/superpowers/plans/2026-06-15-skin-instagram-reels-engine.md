# skin Instagram Reels 量産エンジン Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 既存カルーセル画像から ffmpeg で縦型(9:16)スライド動画を自動生成し、Instagram Reels として全自動投稿する GitHub Actions 常駐エンジンを作る。

**Architecture:** 純粋関数（テーマ選択・パス組み立て・ffmpegコマンド生成・キャプション・秒数計算）を `skin/skin_reels_engine.py` に集約し pytest でテスト。動画生成(`generate`)と公開(`publish`)を2サブコマンドに分け、間で GitHub Actions が mp4 を commit & push して公開URLを生やす。公開は既存 `wait_for_container_ready()` / `publish_media()` を再利用。

**Tech Stack:** Python 3.12 / ffmpeg / requests / pytest / GitHub Actions cron。AI動画なし・トレンド音源なし（mp4に焼き込んだCC0音源のみ）。

---

## ファイル構成

- 作成: `skin/skin_reels_engine.py` — エンジン本体（純粋関数＋generate/publish）
- 作成: `skin/skin_reels_engine_config.json` — 秒数・上限・パス設定
- 作成: `skin/tests/test_skin_reels_engine.py` — 純粋関数のテスト
- 作成: `.github/workflows/skin_instagram_reels.yml` — cron ワークフロー
- 実行時自動生成: `skin/skin_instagram_reels/latest_reel.mp4`（動画・固定パス上書き）/ `skin/skin_reels_pending.json`（generate→publish受け渡し）/ `skin/skin_reels_progress.json`（テーマ進捗）
- 手動配置（Task 0）: `skin/skin_reels_assets/bgm.mp3`（CC0音源）
- 参照（変更しない）: `skin/skin_instagram_auto_post.py`（`wait_for_container_ready`,`publish_media`）/ `skin/carousel_content.json` / `skin/skin_instagram_carousels/themeNN_slideM.png`(160枚)
- 追記: `learning/learning_notes.md`

共通定数（全タスクで固定）:
- カルーセル画像ディレクトリ: `skin/skin_instagram_carousels/`、命名 `theme{NN:02d}_slide{M}.png`
- 動画 raw URL ベース: `https://raw.githubusercontent.com/kmkn0523-cell/kenta-learning/main/skin/skin_instagram_reels`
- 解像度 1080x1920 / fps 30 / H.264(libx264) / 音声 aac

pending.json スキーマ（generate が書き、publish が読む）:
```json
{"theme_id": 1, "caption": "…本文＋#タグ…", "video_filename": "latest_reel.mp4"}
```
progress.json スキーマ:
```json
{"reels_index": 0, "history": ["2026-06-15"]}
```

---

## Task 0: 事前作業（ユーザー手動・コード不要）

- [ ] **Step 1: CC0音源を配置**

商用利用可・著作権フリー(CC0等)の音源を入手し、`skin/skin_reels_assets/bgm.mp3` として置く（Claudeは音源取得不可）。30秒以上の長さが望ましい。

- [ ] **Step 2: 有効化スイッチの変数を作成**

GitHub リポジトリの Settings → Secrets and variables → Actions → Variables に、名前 `SKIN_REELS_ENGINE_ENABLED`、値 `false` を作る（テスト完了まで false）。

- [ ] **Step 3: skin Instagram の Secrets 確認**

GitHub Secrets に skin IG 用トークン（既存ワークフローが使う `SKIN_INSTAGRAM_ACCESS_TOKEN` / `SKIN_INSTAGRAM_USER_ID` 等）があることを確認（既存カルーセル投稿が動いている＝あるはず）。

---

## Task 1: 設定ファイルを作る

**Files:**
- Create: `skin/skin_reels_engine_config.json`

- [ ] **Step 1: 設定ファイルを作成**

```json
{
  "total_themes": 20,
  "seconds_per_slide": 3.5,
  "max_slides": 7,
  "min_total_seconds": 5,
  "max_total_seconds": 60,
  "fps": 30,
  "width": 1080,
  "height": 1920,
  "video_filename": "latest_reel.mp4",
  "raw_video_base": "https://raw.githubusercontent.com/kmkn0523-cell/kenta-learning/main/skin/skin_instagram_reels"
}
```

- [ ] **Step 2: コミット**

```bash
git add skin/skin_reels_engine_config.json
git commit -m "feat: skin Reelsエンジンの設定ファイル追加"
```

---

## Task 2: テーマローテーション（TDD）

**Files:**
- Create: `skin/skin_reels_engine.py`
- Test: `skin/tests/test_skin_reels_engine.py`

- [ ] **Step 1: 失敗するテストを書く**

`skin/tests/test_skin_reels_engine.py`:
```python
# test_skin_reels_engine.py
# skin_reels_engine.py の純粋ロジックをテストする（ffmpeg実行・ネットワークは対象外）
# 実行: pytest skin/tests/test_skin_reels_engine.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_reels_engine import next_theme_index


def test_next_theme_index_通常は1進む():
    assert next_theme_index({"reels_index": 0}, 20) == 1

def test_next_theme_index_末尾で先頭に戻る():
    assert next_theme_index({"reels_index": 19}, 20) == 0

def test_next_theme_index_キー無しは0扱いで1():
    assert next_theme_index({}, 20) == 1
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `pytest skin/tests/test_skin_reels_engine.py -v`
Expected: FAIL（`No module named 'skin_reels_engine'`）

- [ ] **Step 3: 最小実装を書く**

`skin/skin_reels_engine.py`:
```python
# skin_reels_engine.py
# skin Instagram Reels 量産エンジン（GitHub Actions専用・対話なし・全自動）
# 既存カルーセル画像から ffmpeg で縦型スライド動画を作り、Reelsとして自動投稿する。
# generate（動画生成）と publish（公開）の2サブコマンドを持つ。

import json     # 設定・状態ファイルを読み書きする道具
import os       # 環境変数（トークン・有効化スイッチ）を読む道具
import subprocess  # ffmpeg を実行する道具
import sys      # コマンド引数（generate / publish）を読む道具
import time     # URL配信待ち・ポーリングに使う道具
from datetime import datetime, timezone, timedelta  # 日本時間で「今日」を求める道具
from pathlib import Path  # ファイルの場所を組み立てる道具

import requests  # 動画URLの配信確認・API投稿に使う道具


def next_theme_index(progress, total_themes):
    """進捗から次に使うテーマのインデックス（0始まり）を返す。末尾の次は先頭へ循環。"""
    current = progress.get("reels_index", -1)
    return (current + 1) % total_themes
```

- [ ] **Step 4: テストが通ることを確認**

Run: `pytest skin/tests/test_skin_reels_engine.py -v`
Expected: PASS（3件）

- [ ] **Step 5: コミット**

```bash
git add skin/skin_reels_engine.py skin/tests/test_skin_reels_engine.py
git commit -m "feat: Reelsエンジンのテーマローテーション"
```

---

## Task 3: スライド枚数の決定とローカルパス組み立て（TDD）

**Files:**
- Modify: `skin/skin_reels_engine.py`
- Test: `skin/tests/test_skin_reels_engine.py`

- [ ] **Step 1: 失敗するテストを書く**

import に追加し、追記:
```python
from skin_reels_engine import slides_to_use, build_local_slide_paths


def test_slides_to_use_上限max_slidesで頭打ち():
    # 8枚あっても max_slides=7 で7枚まで
    assert slides_to_use(8, 3.5, 7, 60) == 7

def test_slides_to_use_合計秒数の上限で頭打ち():
    # seconds_per_slide=3.5, max_total=10 → floor(10/3.5)=2枚
    assert slides_to_use(8, 3.5, 7, 10) == 2

def test_slides_to_use_スライドが少なければその枚数():
    assert slides_to_use(3, 3.5, 7, 60) == 3

def test_build_local_slide_paths_命名規則どおり():
    paths = build_local_slide_paths(1, 3, "skin/skin_instagram_carousels")
    assert paths == [
        "skin/skin_instagram_carousels/theme01_slide1.png",
        "skin/skin_instagram_carousels/theme01_slide2.png",
        "skin/skin_instagram_carousels/theme01_slide3.png",
    ]
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `pytest skin/tests/test_skin_reels_engine.py -v`
Expected: FAIL（`cannot import name 'slides_to_use'`）

- [ ] **Step 3: 最小実装を書く**

`next_theme_index` の下に追記:
```python
def slides_to_use(slide_count, seconds_per_slide, max_slides, max_total_seconds):
    """使うスライド枚数を決める。max_slides と『合計秒数が上限を超えない枚数』の小さい方で頭打ち。"""
    by_duration = int(max_total_seconds // seconds_per_slide)  # 合計秒数で許される最大枚数
    return min(slide_count, max_slides, by_duration)


def build_local_slide_paths(theme_id, slide_count, carousel_dir):
    """テーマIDと枚数から、カルーセル画像のローカルパス一覧を作る（命名: themeNN_slideM.png）。"""
    return [
        f"{carousel_dir}/theme{theme_id:02d}_slide{i}.png"
        for i in range(1, slide_count + 1)
    ]
```

- [ ] **Step 4: テストが通ることを確認**

Run: `pytest skin/tests/test_skin_reels_engine.py -v`
Expected: PASS（7件）

- [ ] **Step 5: コミット**

```bash
git add skin/skin_reels_engine.py skin/tests/test_skin_reels_engine.py
git commit -m "feat: スライド枚数決定とローカルパス組み立て"
```

---

## Task 4: ffmpegコマンド生成（TDD）

**Files:**
- Modify: `skin/skin_reels_engine.py`
- Test: `skin/tests/test_skin_reels_engine.py`

- [ ] **Step 1: 失敗するテストを書く**

import に追加し、追記:
```python
from skin_reels_engine import build_ffmpeg_command


def test_build_ffmpeg_command_必須フラグを含む():
    images = ["a.png", "b.png"]
    cmd = build_ffmpeg_command(images, "bgm.mp3", "out.mp4", 3.5, 30, 1080, 1920)
    # 画像2枚＋音声1＝-i が3回
    assert cmd.count("-i") == 3
    # 各画像が -loop 1 -t 3.5 で入る
    assert "-loop" in cmd
    assert "3.5" in cmd
    # H.264・縦型・音声・shortest・出力が含まれる
    assert "libx264" in cmd
    assert "-shortest" in cmd
    assert "1080:1920" in " ".join(cmd)
    assert "concat=n=2" in " ".join(cmd)
    assert cmd[-1] == "out.mp4"
    assert cmd[0] == "ffmpeg"
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `pytest skin/tests/test_skin_reels_engine.py -v`
Expected: FAIL（`cannot import name 'build_ffmpeg_command'`）

- [ ] **Step 3: 最小実装を書く**

`build_local_slide_paths` の下に追記:
```python
def build_ffmpeg_command(image_paths, audio_path, output_path, seconds_per_slide, fps, width, height):
    """静止画スライド＋音源から縦型(9:16)H.264動画を作る ffmpeg コマンド（引数リスト）を返す。
    各画像を seconds_per_slide 秒ずつ表示し、scale+pad で width x height に収め、concat で連結。
    音声は動画の長さに合わせて -shortest で切る。"""
    command = ["ffmpeg", "-y"]  # -y: 既存ファイルを上書き
    for path in image_paths:  # 画像を1枚ずつ静止画入力として追加
        command += ["-loop", "1", "-t", str(seconds_per_slide), "-i", path]
    command += ["-i", audio_path]  # 最後に音源を追加（入力インデックス = 画像枚数）

    # 各画像を縦型キャンバスに収める filter を組み立てる
    filters = []
    for index in range(len(image_paths)):
        filters.append(
            f"[{index}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{index}]"
        )
    concat_inputs = "".join(f"[v{i}]" for i in range(len(image_paths)))
    filters.append(f"{concat_inputs}concat=n={len(image_paths)}:v=1:a=0[outv]")
    filter_complex = ";".join(filters)

    audio_index = len(image_paths)  # 音源の入力番号
    command += [
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", f"{audio_index}:a",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-c:a", "aac",
        "-shortest",
        output_path,
    ]
    return command
```

- [ ] **Step 4: テストが通ることを確認**

Run: `pytest skin/tests/test_skin_reels_engine.py -v`
Expected: PASS（8件）

- [ ] **Step 5: コミット**

```bash
git add skin/skin_reels_engine.py skin/tests/test_skin_reels_engine.py
git commit -m "feat: ffmpegコマンド生成（縦型スライド＋音源）"
```

---

## Task 5: キャプション組み立てと動画URL組み立て（TDD）

**Files:**
- Modify: `skin/skin_reels_engine.py`
- Test: `skin/tests/test_skin_reels_engine.py`

- [ ] **Step 1: 失敗するテストを書く**

import に追加し、追記:
```python
from skin_reels_engine import build_caption, build_raw_video_url


def test_build_caption_フックとハッシュタグを含む():
    theme = {
        "hook": "肌を荒らす食卓 5 チェック",
        "fixed_hashtags": ["肌荒れ", "大人ニキビ"],
        "theme_hashtags": ["食事と肌"],
        "size_mix_hashtags": ["30代肌悩み"],
    }
    caption = build_caption(theme)
    assert "肌を荒らす食卓 5 チェック" in caption
    assert "#肌荒れ" in caption
    assert "#食事と肌" in caption
    assert "#30代肌悩み" in caption

def test_build_raw_video_url_ベースとファイル名を連結():
    url = build_raw_video_url("https://example.com/reels", "latest_reel.mp4")
    assert url == "https://example.com/reels/latest_reel.mp4"
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `pytest skin/tests/test_skin_reels_engine.py -v`
Expected: FAIL（`cannot import name 'build_caption'`）

- [ ] **Step 3: 最小実装を書く**

`build_ffmpeg_command` の下に追記:
```python
def build_caption(theme):
    """テーマのフック文＋ハッシュタグでReelsキャプションを組み立てる。"""
    tags = theme.get("fixed_hashtags", []) + theme.get("theme_hashtags", []) + theme.get("size_mix_hashtags", [])
    hashtag_line = " ".join(f"#{tag}" for tag in tags)
    return f"{theme.get('hook', '')}\n\n{hashtag_line}"


def build_raw_video_url(raw_video_base, filename):
    """動画のraw公開URLを組み立てる。"""
    return f"{raw_video_base}/{filename}"
```

- [ ] **Step 4: テストが通ることを確認**

Run: `pytest skin/tests/test_skin_reels_engine.py -v`
Expected: PASS（10件）

- [ ] **Step 5: コミット**

```bash
git add skin/skin_reels_engine.py skin/tests/test_skin_reels_engine.py
git commit -m "feat: キャプションと動画URL組み立て"
```

---

## Task 6: 設定・状態のファイル入出力（TDD）

**Files:**
- Modify: `skin/skin_reels_engine.py`
- Test: `skin/tests/test_skin_reels_engine.py`

- [ ] **Step 1: 失敗するテストを書く**

import に追加し、追記:
```python
import json as _json

from skin_reels_engine import load_json, save_json


def test_save_と_load_で往復できる(tmp_path):
    path = tmp_path / "state.json"
    data = {"reels_index": 3, "history": ["2026-06-15"]}
    save_json(str(path), data)
    assert load_json(str(path), default={}) == data

def test_load_json_無ければdefault(tmp_path):
    path = tmp_path / "missing.json"
    assert load_json(str(path), default={"reels_index": 0}) == {"reels_index": 0}
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `pytest skin/tests/test_skin_reels_engine.py -v`
Expected: FAIL（`cannot import name 'load_json'`）

- [ ] **Step 3: 最小実装を書く**

`build_raw_video_url` の下に追記:
```python
def load_json(path, default):
    """JSONファイルを読み込む。無ければ default を返す。"""
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    """JSONファイルを書き出す（日本語そのまま・読みやすいインデント）。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: テストが通ることを確認**

Run: `pytest skin/tests/test_skin_reels_engine.py -v`
Expected: PASS（12件）

- [ ] **Step 5: コミット**

```bash
git add skin/skin_reels_engine.py skin/tests/test_skin_reels_engine.py
git commit -m "feat: 設定・状態のJSON入出力"
```

---

## Task 7: generate サブコマンド（コードのみ・ffmpeg実行はテスト外）

**Files:**
- Modify: `skin/skin_reels_engine.py`

- [ ] **Step 1: 定数と generate を追記**

`save_json` の下に追記:
```python
# -----------------------------------------------
# ファイルの場所・定数（このスクリプトと同じ skin/ にある前提）
# -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "skin_reels_engine_config.json"
CAROUSEL_DIR = BASE_DIR / "skin_instagram_carousels"
CAROUSEL_CONTENT_PATH = BASE_DIR / "carousel_content.json"
AUDIO_PATH = BASE_DIR / "skin_reels_assets" / "bgm.mp3"
REELS_DIR = BASE_DIR / "skin_instagram_reels"
PENDING_PATH = BASE_DIR / "skin_reels_pending.json"
PROGRESS_PATH = BASE_DIR / "skin_reels_progress.json"
DAILY_LOG_PATH = BASE_DIR / "skin_daily_log.md"
JST = timezone(timedelta(hours=9))


def load_themes():
    """carousel_content.json からテーマ一覧（リスト）を取り出す。"""
    data = load_json(str(CAROUSEL_CONTENT_PATH), default={})
    return data.get("themes", data if isinstance(data, list) else [])


def generate():
    """動画を生成して pending.json に公開情報を書き出す。"""
    if os.environ.get("SKIN_REELS_ENGINE_ENABLED") != "true":
        print("SKIN_REELS_ENGINE_ENABLED が true でないため停止します。")
        return
    if not AUDIO_PATH.exists():  # 音源が無ければ著作権事故防止のため明確に停止
        print(f"音源が見つかりません: {AUDIO_PATH}（CC0音源を置いてください）")
        return

    config = load_json(str(CONFIG_PATH), default={})
    themes = load_themes()
    if not themes:
        print("テーマが読み込めませんでした。")
        return

    progress = load_json(str(PROGRESS_PATH), default={"reels_index": -1, "history": []})
    index = next_theme_index(progress, min(config["total_themes"], len(themes)))
    theme = themes[index]
    theme_id = theme.get("id", index + 1)

    n_slides = slides_to_use(
        theme.get("slide_count", len(theme.get("slides", []))),
        config["seconds_per_slide"], config["max_slides"], config["max_total_seconds"],
    )
    image_paths = build_local_slide_paths(theme_id, n_slides, str(CAROUSEL_DIR))

    REELS_DIR.mkdir(exist_ok=True)  # 出力先フォルダを用意
    output_path = str(REELS_DIR / config["video_filename"])
    command = build_ffmpeg_command(
        image_paths, str(AUDIO_PATH), output_path,
        config["seconds_per_slide"], config["fps"], config["width"], config["height"],
    )
    print("ffmpeg実行:", " ".join(command))
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:  # 生成失敗なら中身を出して停止
        print("ffmpeg失敗:", result.stderr[-1000:])
        return

    caption = build_caption(theme)
    save_json(str(PENDING_PATH), {
        "theme_id": theme_id,
        "theme_index": index,
        "caption": caption,
        "video_filename": config["video_filename"],
    })
    print(f"生成完了: theme_id={theme_id}, slides={n_slides} → {output_path}")
```

- [ ] **Step 2: 既存テストが壊れていないことを確認**

Run: `pytest skin/tests/test_skin_reels_engine.py -v`
Expected: PASS（12件のまま）

- [ ] **Step 3: キルスイッチ確認（ffmpegに触れない）**

Run: `cd skin && SKIN_REELS_ENGINE_ENABLED=false python3 skin_reels_engine.py generate` ※ Task 8 で main を追加後に実行。ここでは確認をスキップしてよい

- [ ] **Step 4: コミット**

```bash
git add skin/skin_reels_engine.py
git commit -m "feat: generateサブコマンド（動画生成）"
```

---

## Task 8: publish サブコマンドと main 振り分け（コードのみ）

**Files:**
- Modify: `skin/skin_reels_engine.py`

- [ ] **Step 1: REELSコンテナ作成・URL待ち・publish・main を追記**

`generate` の下に追記:
```python
def wait_for_url(url, max_wait=180):
    """動画のraw URLが配信され始める（HTTP 200）まで待つ。"""
    waited = 0
    while waited < max_wait:
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return True
        except Exception as error:
            print(f"URL確認エラー: {error}")
        time.sleep(15)
        waited += 15
    return False


def create_reels_container(video_url, caption, user_id, token):
    """media_type=REELS でコンテナ（下書き）を作り、creation_id を返す。"""
    url = f"https://graph.facebook.com/v19.0/{user_id}/media"
    params = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": token,
    }
    response = requests.post(url, params=params, timeout=60)
    data = response.json()
    if "id" in data:
        return data["id"]
    print(f"Reelsコンテナ作成失敗: {data}")
    return ""


def publish():
    """pending.json を読み、動画URLの配信を待ってから Reels を公開する。"""
    if os.environ.get("SKIN_REELS_ENGINE_ENABLED") != "true":
        print("SKIN_REELS_ENGINE_ENABLED が true でないため停止します。")
        return

    config = load_json(str(CONFIG_PATH), default={})
    pending = load_json(str(PENDING_PATH), default={})
    if not pending:
        print("公開対象（pending.json）がありません。")
        return

    token = os.environ["SKIN_INSTAGRAM_ACCESS_TOKEN"]
    user_id = os.environ["SKIN_INSTAGRAM_USER_ID"]
    video_url = build_raw_video_url(config["raw_video_base"], pending["video_filename"])

    if not wait_for_url(video_url):  # URLが生えるまで待つ
        print(f"動画URLが配信されませんでした: {video_url}")
        return

    creation_id = create_reels_container(video_url, pending["caption"], user_id, token)
    if not creation_id:
        return

    # 公開処理は既存スクリプトを再利用（env必須なので遅延import）
    from skin_instagram_auto_post import wait_for_container_ready, publish_media
    if not wait_for_container_ready(creation_id):
        print("動画の処理が完了しませんでした。")
        return
    result = publish_media(creation_id)
    if not result.get("id"):
        print(f"公開失敗: {result}")
        return

    # 進捗を進める・ログに記録する
    progress = load_json(str(PROGRESS_PATH), default={"reels_index": -1, "history": []})
    today = datetime.now(JST).strftime("%Y-%m-%d")
    progress["reels_index"] = pending["theme_index"]
    progress.setdefault("history", []).append(today)
    save_json(str(PROGRESS_PATH), progress)
    with open(DAILY_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n- {today} Reels自動投稿: theme_id={pending['theme_id']}")
    print(f"公開完了: post_id={result['id']}")


def main():
    """引数 generate / publish でサブコマンドを振り分ける。"""
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "generate":
        generate()
    elif command == "publish":
        publish()
    else:
        print("使い方: python skin_reels_engine.py [generate|publish]")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: キルスイッチ確認（ネットワーク・ffmpegに触れない）**

Run: `cd skin && SKIN_REELS_ENGINE_ENABLED=false python3 skin_reels_engine.py generate`
Expected: `SKIN_REELS_ENGINE_ENABLED が true でないため停止します。`

Run: `cd skin && SKIN_REELS_ENGINE_ENABLED=false python3 skin_reels_engine.py publish`
Expected: `SKIN_REELS_ENGINE_ENABLED が true でないため停止します。`

- [ ] **Step 3: 全テストが通ることを確認**

Run: `pytest skin/tests/test_skin_reels_engine.py -v`
Expected: PASS（12件）

- [ ] **Step 4: コミット**

```bash
git add skin/skin_reels_engine.py
git commit -m "feat: publishサブコマンドとmain振り分け"
```

---

## Task 9: GitHub Actions ワークフロー

**Files:**
- Create: `.github/workflows/skin_instagram_reels.yml`

- [ ] **Step 1: ワークフローを作成**

`.github/workflows/skin_instagram_reels.yml`:
```yaml
# skin_instagram_reels.yml
# skin Instagram Reels 量産エンジン
# 1日1回 JST 19:00 に起動し、縦型スライド動画を生成→push→Reels公開する

name: skin Instagram Reels

on:
  schedule:
    - cron: '0 10 * * *'  # JST 19:00 = UTC 10:00
  workflow_dispatch:

concurrency:
  group: skin-instagram-reels
  cancel-in-progress: false

jobs:
  reels:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: リポジトリをチェックアウト
        uses: actions/checkout@v4

      - name: Python 3.12 をセットアップ
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: ffmpeg をインストール
        run: sudo apt-get update && sudo apt-get install -y ffmpeg

      - name: ライブラリをインストール
        run: pip install requests

      - name: 動画を生成
        env:
          SKIN_REELS_ENGINE_ENABLED: ${{ vars.SKIN_REELS_ENGINE_ENABLED }}
        run: cd skin && python skin_reels_engine.py generate

      - name: 動画と受け渡しファイルをコミット＆プッシュ（公開URLを生やす）
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add skin/skin_instagram_reels/latest_reel.mp4 skin/skin_reels_pending.json
          if ! git diff --staged --quiet; then
            git commit -m "自動生成: skin Reels動画更新"
            for i in 1 2 3; do
              git pull --rebase origin main && git push && break
              echo "push失敗 リトライ $i/3..."
              sleep 5
            done
          fi

      - name: Reels を公開
        env:
          SKIN_REELS_ENGINE_ENABLED: ${{ vars.SKIN_REELS_ENGINE_ENABLED }}
          SKIN_INSTAGRAM_ACCESS_TOKEN: ${{ secrets.SKIN_INSTAGRAM_ACCESS_TOKEN }}
          SKIN_INSTAGRAM_USER_ID: ${{ secrets.SKIN_INSTAGRAM_USER_ID }}
        run: cd skin && python skin_reels_engine.py publish

      - name: 進捗をコミット＆プッシュ
        run: |
          git add skin/skin_reels_progress.json skin/skin_daily_log.md
          if ! git diff --staged --quiet; then
            git commit -m "自動同期: skin Reels進捗更新"
            for i in 1 2 3; do
              git pull --rebase origin main && git push && break
              echo "push失敗 リトライ $i/3..."
              sleep 5
            done
          fi
```

- [ ] **Step 2: YAML構文を確認**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/skin_instagram_reels.yml')); print('YAML OK')"`
Expected: `YAML OK`

- [ ] **Step 3: コミット**

```bash
git add .github/workflows/skin_instagram_reels.yml
git commit -m "feat: skin Instagram ReelsのGitHub Actionsワークフロー"
```

---

## Task 10: 学習ノート追記と本番リハーサル

**Files:**
- Modify: `learning/learning_notes.md`

- [ ] **Step 1: 学習ノートの一覧表に1行追記**

`learning/learning_notes.md` の既存テーブルの実カラム順に合わせて1行追加（例。実際のカラム順はファイルを見て合わせる）:
```markdown
| 6/15 | skin_reels_engine.py | 既存カルーセル画像からffmpegで縦型Reelsを自動生成・投稿 | ffmpeg/subprocess/Reels API |
```

- [ ] **Step 2: コミット**

```bash
git add learning/learning_notes.md
git commit -m "docs: learning_notesにReelsエンジンを追記"
```

- [ ] **Step 3: 本番リハーサル（Kenta が手動）**

Task 0 完了後（`bgm.mp3` 配置済み・変数 `SKIN_REELS_ENGINE_ENABLED` 作成済み）、Actions タブから `skin Instagram Reels` を `Run workflow` で手動実行し、変数を一時的に `true` にする。ログで「生成完了 → 公開完了: post_id=…」を確認し、実際に Reels が9:16・5〜90秒で投稿されているか目視確認する。

- [ ] **Step 4: 本稼働へ**

問題なければ `SKIN_REELS_ENGINE_ENABLED` を `true` のままにして cron 常駐開始。違和感があれば `false` に戻す。

---

## Self-Review（記入済み）

- **Spec coverage:** テーマ選択=Task2、スライド/パス=Task3、ffmpeg生成=Task4/7、キャプション/URL=Task5、状態IO=Task6、generate=Task7、publish(URL待ち＋REELS＋既存publish再利用)=Task8、ワークフロー(ffmpeg導入＋2フェーズpush)=Task9、事前作業(bgm/変数)=Task0、リハーサル=Task10。設計書の全節に対応タスクあり。
- **Placeholder scan:** 各コードステップに実コードあり。空文言なし。
- **Type consistency:** pending.json(theme_id/theme_index/caption/video_filename)・progress.json(reels_index/history)・config キー(total_themes/seconds_per_slide/max_slides/max_total_seconds/fps/width/height/video_filename/raw_video_base)・関数名(next_theme_index/slides_to_use/build_local_slide_paths/build_ffmpeg_command/build_caption/build_raw_video_url/load_json/save_json/load_themes/generate/wait_for_url/create_reels_container/publish/main) を全タスクで統一。
- **env非依存テスト:** トップレベルで `skin_instagram_auto_post` を import しない（publish内で遅延import）。純粋関数のみテストするためトークン不要。
