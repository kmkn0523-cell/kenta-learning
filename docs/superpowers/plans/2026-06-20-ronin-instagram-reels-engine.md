# ローニン Instagram Reels 自動生成・自動投稿エンジン Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** @RoninWords の格言1件を段階リビールする縦型(9:16)リール動画を ffmpeg で自動生成し、Instagram Graph API(REELS) で1日1回自動投稿する仕組みを作る。

**Architecture:** skin で実証済みの「単一エンジン＋generate/publish 2フェーズ」方式を踏襲。`generate` が格言の4フレーム(背景→日本語→ローマ字→英語)を Pillow で描画し ffmpeg で fade 付き連結＋CC0音源を焼き込んで `latest_reel.mp4` を作る。GitHub Actions が push して raw URL を生やし、`publish` が REELS コンテナ作成→FINISHEDポーリング→公開する。純粋関数(index計算・ffmpeg引数・キャプション・フレーム計画)と IO を分離する。

**Tech Stack:** Python 3.12 / Pillow / ffmpeg(libx264,aac) / requests / GitHub Actions / Instagram Graph API v19.0

## Global Constraints

- 各行に初心者向け日本語コメントを付ける。変数名・関数名は略さない英単語。
- Reels 掲載条件を厳守: **9:16(1080×1920)・H.264(libx264)・yuv420p・5〜90秒**。
- BGM は **CC0/ロイヤリティフリーのみ**。音源が無ければ generate は明確なエラーで停止する。
- キルスイッチ: 環境変数 `RONIN_REEL_ENGINE_ENABLED` が `true` 以外なら generate/publish とも即終了。
- env 変数は既存画像投稿と共通: `INSTAGRAM_ACCESS_TOKEN` / `INSTAGRAM_USER_ID`。
- 動画は固定パス `ronin/ronin_instagram_reels/latest_reel.mp4` に上書き(リポジトリ肥大防止)。
- リール進捗 `ronin/ronin_reel_progress.json` は画像投稿の進捗と完全分離。
- 既存の ronin ワークフロー(画像・Threads・Substack)・既存スクリプトの挙動は一切変えない。
- テストは `pytest ronin/tests/` 配下。純粋関数のみ対象、ffmpeg実行/Pillow描画/API/URLポーリングは対象外。
- フォントはリポジトリ相対 `ronin/fonts/` から読む(CIで解決できるようにするため)。

---

## ファイル構成

| パス | 責務 |
|---|---|
| `ronin/fonts/YujiSyuku.ttf` (新規追加) | 筆文字フォント(CIで使う・OFL再配布可) |
| `ronin/fonts/CormorantGaramond-Italic.ttf` (新規追加) | 欧文フォント(CIで使う・OFL再配布可) |
| `ronin/ronin_reel_engine_config.json` (新規) | 秒数・解像度・fps・fade・出力名・raw URLベース |
| `ronin/ronin_reel_engine.py` (新規) | 本体。純粋関数群＋generate/publish |
| `ronin/ronin_reel_frames.py` (新規) | 1格言→縦型4フレームPNGを Pillow で描画 |
| `ronin/ronin_reel_assets/bgm.mp3` (ユーザーが手動配置) | CC0 BGM |
| `ronin/ronin_instagram_reels/latest_reel.mp4` (生成物) | 最新動画 |
| `ronin/ronin_reel_pending.json` (生成物) | generate→publish 受け渡し |
| `ronin/ronin_reel_progress.json` (生成物) | リール進捗 |
| `ronin/tests/test_ronin_reel_engine.py` (新規) | 純粋関数のテスト |
| `.github/workflows/ronin_instagram_reels.yml` (新規) | 1日1回 generate→push→publish |

---

### Task 1: CIで使うフォントをリポジトリに追加

筆文字フォントと欧文フォントは現在 `~/fonts/`(リポジトリ外)にしか無く、GitHub Actions では存在しない。リール動画をCIで生成するため、リポジトリ内 `ronin/fonts/` に追加する。両フォントとも SIL OFL ライセンスで再配布可。

**Files:**
- Create: `ronin/fonts/YujiSyuku.ttf` (コピー)
- Create: `ronin/fonts/CormorantGaramond-Italic.ttf` (コピー)

**Interfaces:**
- Produces: `ronin/fonts/YujiSyuku.ttf`, `ronin/fonts/CormorantGaramond-Italic.ttf`, `ronin/fonts/NotoSerifJP.otf`(既存) の3フォントが揃う

- [ ] **Step 1: フォントを ronin/fonts/ にコピー**

```bash
cp /home/kenta_kamijyo/fonts/YujiSyuku.ttf /home/kenta_kamijyo/ronin/fonts/YujiSyuku.ttf
cp /home/kenta_kamijyo/fonts/CormorantGaramond-Italic.ttf /home/kenta_kamijyo/ronin/fonts/CormorantGaramond-Italic.ttf
```

- [ ] **Step 2: 3フォントが Pillow で開けることを確認**

Run:
```bash
cd /home/kenta_kamijyo && python -c "from PIL import ImageFont; [ImageFont.truetype(f'ronin/fonts/{n}', 40) for n in ['YujiSyuku.ttf','CormorantGaramond-Italic.ttf','NotoSerifJP.otf']]; print('OK 3 fonts loadable')"
```
Expected: `OK 3 fonts loadable`

- [ ] **Step 3: Commit**

```bash
cd /home/kenta_kamijyo && git add ronin/fonts/YujiSyuku.ttf ronin/fonts/CormorantGaramond-Italic.ttf
git commit -m "ローニンReel: CIで使うフォントをリポジトリに追加"
```

---

### Task 2: 設定ファイルと純粋ヘルパー関数

エンジンの中核となる純粋関数(index計算・キャプション・raw URL・フレーム計画)と設定ファイルを作る。env や ffmpeg に依存せず、import だけでテストできる形にする。

**Files:**
- Create: `ronin/ronin_reel_engine_config.json`
- Create: `ronin/ronin_reel_engine.py` (純粋関数部のみ・この時点では generate/publish は未実装)
- Test: `ronin/tests/test_ronin_reel_engine.py`

**Interfaces:**
- Produces:
  - `next_proverb_index(progress: dict, total: int) -> int` — `progress["reel_index"]`(無ければ-1)の次。末尾の次は先頭へ循環
  - `frame_reveal_plan() -> list[dict]` — 4フレーム分の表示プラン。各要素 `{"jp": bool, "roma": bool, "en": bool}`
  - `build_caption(proverb: dict, hashtags: str) -> str` — jp/roma/en＋CTA＋ハッシュタグ
  - `build_raw_video_url(raw_video_base: str, filename: str) -> str`
  - `load_json(path, default)` / `save_json(path, data)`

- [ ] **Step 1: 設定ファイルを作成**

Create `ronin/ronin_reel_engine_config.json`:
```json
{
  "total_proverbs": 100,
  "seconds_per_frame": 2.6,
  "fps": 30,
  "width": 1080,
  "height": 1920,
  "fade_duration": 0.5,
  "video_filename": "latest_reel.mp4",
  "raw_video_base": "https://raw.githubusercontent.com/kmkn0523-cell/kenta-learning/main/ronin/ronin_instagram_reels"
}
```

- [ ] **Step 2: 失敗するテストを書く**

Create `ronin/tests/test_ronin_reel_engine.py`:
```python
# ronin_reel_engine.py の純粋関数をテストする（IOやffmpegは対象外）
import sys
from pathlib import Path

# ronin/ をimportパスに追加する（テストをどこから実行しても通るように）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ronin_reel_engine as engine  # テスト対象


def test_next_proverb_index_wraps_to_zero_at_end():
    # 最後(99)の次は先頭(0)に戻る
    assert engine.next_proverb_index({"reel_index": 99}, 100) == 0


def test_next_proverb_index_increments():
    # 5の次は6
    assert engine.next_proverb_index({"reel_index": 5}, 100) == 6


def test_next_proverb_index_starts_at_zero_when_empty():
    # 進捗が無ければ最初は0（-1の次）
    assert engine.next_proverb_index({}, 100) == 0


def test_frame_reveal_plan_is_cumulative_four_frames():
    plan = engine.frame_reveal_plan()
    assert len(plan) == 4
    # 1枚目は背景のみ、最後は全要素
    assert plan[0] == {"jp": False, "roma": False, "en": False}
    assert plan[3] == {"jp": True, "roma": True, "en": True}
    # 累積表示：jpは2枚目以降ずっとTrue
    assert [f["jp"] for f in plan] == [False, True, True, True]
    assert [f["roma"] for f in plan] == [False, False, True, True]
    assert [f["en"] for f in plan] == [False, False, False, True]


def test_build_caption_contains_all_parts():
    proverb = {"jp": "一期一会", "roma": "Ichi go ichi e", "en": "This moment will never come again."}
    caption = engine.build_caption(proverb, "#JapaneseWisdom #Bushido #Zen")
    assert "一期一会" in caption
    assert "Ichi go ichi e" in caption
    assert "This moment will never come again." in caption
    assert "Follow for one Japanese wisdom, every day." in caption
    assert "#JapaneseWisdom #Bushido #Zen" in caption


def test_build_raw_video_url():
    url = engine.build_raw_video_url("https://raw.example.com/ronin/ronin_instagram_reels", "latest_reel.mp4")
    assert url == "https://raw.example.com/ronin/ronin_instagram_reels/latest_reel.mp4"
```

- [ ] **Step 3: テストが失敗することを確認**

Run: `cd /home/kenta_kamijyo && python -m pytest ronin/tests/test_ronin_reel_engine.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'ronin_reel_engine'`）

- [ ] **Step 4: 純粋関数を実装**

Create `ronin/ronin_reel_engine.py`:
```python
# ronin_reel_engine.py
# @RoninWords Instagram Reels 自動生成・自動投稿エンジン（GitHub Actions専用・全自動）
# 格言1件を段階リビールする縦型動画を ffmpeg で作り、Reelsとして自動投稿する。
# generate（動画生成）と publish（公開）の2サブコマンドを持つ。

import json     # 設定・状態ファイルを読み書きする道具
import os       # 環境変数（トークン・有効化スイッチ）を読む道具
import subprocess  # ffmpeg を実行する道具
import sys      # コマンド引数（generate / publish）を読む道具
import time     # URL配信待ち・ポーリングに使う道具
from datetime import datetime, timezone, timedelta  # 日本時間で「今日」を求める道具
from pathlib import Path  # ファイルの場所を組み立てる道具

import requests  # 動画URLの配信確認・API投稿に使う道具


# 投稿の末尾に付けるフォロー誘導文（既存の画像投稿と統一）
CTA = "Follow for one Japanese wisdom, every day."


def next_proverb_index(progress, total):
    """進捗から次に使う格言のインデックス（0始まり）を返す。末尾の次は先頭へ循環。"""
    current = progress.get("reel_index", -1)  # まだ無ければ -1 → 次は 0
    return (current + 1) % total


def frame_reveal_plan():
    """4フレームの『累積リビール』表示プランを返す。背景→日本語→ローマ字→英語の順。"""
    return [
        {"jp": False, "roma": False, "en": False},  # 1枚目: 和紙背景＋シールだけ
        {"jp": True,  "roma": False, "en": False},  # 2枚目: 日本語格言を出す
        {"jp": True,  "roma": True,  "en": False},  # 3枚目: ローマ字を足す
        {"jp": True,  "roma": True,  "en": True},   # 4枚目: 英語の意味＋CTA
    ]


def build_caption(proverb, hashtags):
    """格言の jp/roma/en と CTA・ハッシュタグから Reels キャプションを組み立てる。"""
    return (
        f"{proverb['jp']}\n{proverb['roma']}\n\n"
        f"{proverb['en']}\n\n"
        f"{CTA}\n\n{hashtags}"
    )


def build_raw_video_url(raw_video_base, filename):
    """動画の raw 公開URLを組み立てる。"""
    return f"{raw_video_base}/{filename}"


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

- [ ] **Step 5: テストが通ることを確認**

Run: `cd /home/kenta_kamijyo && python -m pytest ronin/tests/test_ronin_reel_engine.py -v`
Expected: PASS（6件）

- [ ] **Step 6: Commit**

```bash
cd /home/kenta_kamijyo && git add ronin/ronin_reel_engine_config.json ronin/ronin_reel_engine.py ronin/tests/test_ronin_reel_engine.py
git commit -m "ローニンReel: 設定と純粋ヘルパー関数（index/caption/URL/フレーム計画）"
```

---

### Task 3: ffmpeg コマンド組み立て関数

4枚のフレームPNGとBGMから、9:16・H.264・各フレームfade付きの動画を作る ffmpeg コマンド（引数リスト）を返す純粋関数を追加する。実行はせず引数を組み立てるだけなのでテストできる。

**Files:**
- Modify: `ronin/ronin_reel_engine.py`（`build_ffmpeg_command` を追加）
- Test: `ronin/tests/test_ronin_reel_engine.py`（テスト追加）

**Interfaces:**
- Consumes: なし（純粋関数）
- Produces: `build_ffmpeg_command(image_paths: list[str], audio_path: str, output_path: str, seconds_per_frame: float, fps: int, width: int, height: int, fade_duration: float) -> list[str]`

- [ ] **Step 1: 失敗するテストを追記**

Append to `ronin/tests/test_ronin_reel_engine.py`:
```python
def test_build_ffmpeg_command_structure():
    images = ["f1.png", "f2.png", "f3.png", "f4.png"]
    cmd = engine.build_ffmpeg_command(images, "bgm.mp3", "out.mp4", 2.6, 30, 1080, 1920, 0.5)
    # 先頭は ffmpeg -y（上書き）
    assert cmd[0] == "ffmpeg"
    assert "-y" in cmd
    # 画像4枚それぞれが -loop 1 で入力される
    assert cmd.count("-loop") == 4
    # 各画像が入力として渡る
    for image in images:
        assert image in cmd
    # 音源も入力に含まれる
    assert "bgm.mp3" in cmd
    # H.264 / yuv420p / aac を指定している（Reels要件）
    assert "libx264" in cmd
    assert "yuv420p" in cmd
    assert "aac" in cmd
    # fade フィルタが含まれる（リビール感）
    filter_complex = cmd[cmd.index("-filter_complex") + 1]
    assert "fade=t=in" in filter_complex
    assert "concat=n=4" in filter_complex
    # 出力パスは最後
    assert cmd[-1] == "out.mp4"
    # 音源は動画長に合わせて切る
    assert "-shortest" in cmd
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `cd /home/kenta_kamijyo && python -m pytest ronin/tests/test_ronin_reel_engine.py::test_build_ffmpeg_command_structure -v`
Expected: FAIL（`AttributeError: ... has no attribute 'build_ffmpeg_command'`）

- [ ] **Step 3: build_ffmpeg_command を実装**

Add to `ronin/ronin_reel_engine.py`（`build_raw_video_url` の後あたり）:
```python
def build_ffmpeg_command(image_paths, audio_path, output_path, seconds_per_frame, fps, width, height, fade_duration):
    """静止画フレーム＋音源から縦型(9:16)H.264動画を作る ffmpeg コマンド（引数リスト）を返す。
    各フレームを seconds_per_frame 秒ずつ表示し、fadeで柔らかく出して concat で連結する。
    音声は動画の長さに合わせて -shortest で切る。"""
    command = ["ffmpeg", "-y"]  # -y: 既存ファイルを上書き
    for path in image_paths:  # フレームを1枚ずつ静止画入力として追加
        command += ["-loop", "1", "-t", str(seconds_per_frame), "-i", path]
    command += ["-i", audio_path]  # 最後に音源を追加（入力番号 = フレーム枚数）

    # 各フレームを縦型キャンバスに収め、fade-inで柔らかく出す filter を組み立てる
    filters = []
    for index in range(len(image_paths)):
        filters.append(
            f"[{index}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
            f"fade=t=in:st=0:d={fade_duration}[v{index}]"
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

Run: `cd /home/kenta_kamijyo && python -m pytest ronin/tests/test_ronin_reel_engine.py -v`
Expected: PASS（7件）

- [ ] **Step 5: Commit**

```bash
cd /home/kenta_kamijyo && git add ronin/ronin_reel_engine.py ronin/tests/test_ronin_reel_engine.py
git commit -m "ローニンReel: ffmpegコマンド組み立て関数（fade付き縦型連結）"
```

---

### Task 4: 縦型リビールフレームの描画（Pillow）

1格言から縦型(1080×1920)の4フレームPNGを描画する。フォントは `ronin/fonts/` から読み、配色は既存カードと統一する。描画はIOなので実画像を生成して目視確認する（ユニットテスト対象外）。

**Files:**
- Create: `ronin/ronin_reel_frames.py`

**Interfaces:**
- Consumes: `frame_reveal_plan()`（Task 2）の各 `{"jp","roma","en"}` プラン
- Produces: `render_reveal_frames(proverb: dict, plan: list[dict], out_dir: str, width: int, height: int) -> list[str]` — 生成した4枚のPNG絶対パスを順に返す

- [ ] **Step 1: フレーム描画モジュールを作成**

Create `ronin/ronin_reel_frames.py`:
```python
# ronin_reel_frames.py
# @RoninWords用：1つの格言から「縦型リール」の段階リビール用フレーム画像(1080×1920)を作る。
# 配色・フォントは既存の格言カード(generate_ronin_cards.py)と統一してブランド感を保つ。

from pathlib import Path  # フォントの場所を組み立てる道具
from PIL import Image, ImageDraw, ImageFont  # 画像を描く道具

# このファイルと同じ ronin/ の中の fonts フォルダからフォントを読む（CIでも解決できるように）
FONTS_DIR = Path(__file__).resolve().parent / "fonts"
FONT_JP_PATH = str(FONTS_DIR / "YujiSyuku.ttf")                 # 筆書き風かな漢字
FONT_ROMAN_PATH = str(FONTS_DIR / "CormorantGaramond-Italic.ttf")  # エレガントな欧文
FONT_SERIF_PATH = str(FONTS_DIR / "NotoSerifJP.otf")           # 英語本文用

# 和紙風の背景色とブランドカラー（既存カードと同じ）
PAPER = (240, 230, 208)   # 和紙色 #f0e6d0
RED = (158, 30, 14)       # 朱（シール・アクセント）
INK = (18, 10, 4)         # 墨色（ほぼ黒）
SEPIA = (80, 50, 20)      # セピア（ローマ字・英語）


def _draw_seal(draw, width):
    """右上にRWシール（朱の角印風）を描く。"""
    size = 150           # シールの一辺
    margin = 70          # 端からの距離
    x1 = width - margin  # 右端
    x0 = x1 - size       # 左端
    y0 = margin          # 上端
    y1 = y0 + size       # 下端
    draw.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=RED)  # 朱の角印
    seal_font = ImageFont.truetype(FONT_SERIF_PATH, 60)           # 中の文字
    draw.text(((x0 + x1) // 2, (y0 + y1) // 2), "RW", font=seal_font,
              fill=PAPER, anchor="mm")  # 中央に白抜きでRW


def _draw_centered(draw, text, font, fill, center_x, center_y):
    """指定フォントでテキストを中央寄せで描く（複数行は改行で分ける）。"""
    draw.multiline_text((center_x, center_y), text, font=font, fill=fill,
                        anchor="mm", align="center", spacing=18)


def render_reveal_frames(proverb, plan, out_dir, width, height):
    """格言とリビール計画から4フレームPNGを描き、絶対パスのリストを返す。"""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)  # 出力先を用意

    # フォントを準備（日本語格言は大きめ、ローマ字・英語は中くらい）
    font_jp = ImageFont.truetype(FONT_JP_PATH, 110)      # 日本語格言
    font_roma = ImageFont.truetype(FONT_ROMAN_PATH, 64)  # ローマ字読み
    font_en = ImageFont.truetype(FONT_SERIF_PATH, 52)    # 英語の意味
    font_cta = ImageFont.truetype(FONT_SERIF_PATH, 34)   # フォロー誘導

    paths = []
    for frame_number, parts in enumerate(plan, start=1):
        image = Image.new("RGB", (width, height), PAPER)  # 和紙色のキャンバス
        draw = ImageDraw.Draw(image)
        _draw_seal(draw, width)  # どのフレームにもシールは出す

        center_x = width // 2
        if parts["jp"]:
            # 日本語格言は画面中央やや上に大きく
            _draw_centered(draw, proverb["jp"], font_jp, INK, center_x, height // 2 - 120)
        if parts["roma"]:
            # ローマ字は格言の下にセピアで
            _draw_centered(draw, proverb["roma"], font_roma, SEPIA, center_x, height // 2 + 60)
        if parts["en"]:
            # 英語の意味はさらに下に
            _draw_centered(draw, proverb["en"], font_en, INK, center_x, height // 2 + 220)
            # CTAは最下部
            _draw_centered(draw, "Follow for one Japanese wisdom, every day.",
                           font_cta, SEPIA, center_x, height - 180)

        frame_path = str(out_path / f"frame{frame_number}.png")
        image.save(frame_path, "PNG")
        paths.append(frame_path)
    return paths
```

- [ ] **Step 2: 実際に4フレームを描いて目視確認**

Run:
```bash
cd /home/kenta_kamijyo && python -c "
import sys; sys.path.insert(0, 'ronin')
import ronin_reel_engine as e, ronin_reel_frames as f
proverb = {'jp':'七転び八起き','roma':'Nana korobi ya oki','en':'Fall seven times. Rise eight.'}
paths = f.render_reveal_frames(proverb, e.frame_reveal_plan(), '/tmp/ronin_reel_test', 1080, 1920)
print('生成:', paths)
"
```
Expected: 4枚のパス（`/tmp/ronin_reel_test/frame1.png`〜`frame4.png`）が表示され、各PNGが 1080×1920 で、frame4 に日本語・ローマ字・英語・CTA・シールが全部入っていること。

> 注: `/tmp` 配下に出すのはリポジトリを汚さないため（自動同期cron対策）。目視で配色・崩れを確認する。

- [ ] **Step 3: Commit**

```bash
cd /home/kenta_kamijyo && git add ronin/ronin_reel_frames.py
git commit -m "ローニンReel: 縦型リビールフレームの描画（Pillow・既存カードと配色統一）"
```

---

### Task 5: generate サブコマンドの実装

格言を選び→4フレーム描画→ffmpegで動画生成→pending.json保存、までを行う `generate()` を実装する。ローカルに ffmpeg と `ronin_reel_assets/bgm.mp3` が必要。

**Files:**
- Modify: `ronin/ronin_reel_engine.py`（定数・`generate()`・`main()` を追加）

**Interfaces:**
- Consumes: `next_proverb_index`, `frame_reveal_plan`, `build_caption`, `build_ffmpeg_command`, `load_json`, `save_json`（Task 2-3）/ `render_reveal_frames`（Task 4）/ `generate_ronin_cards.proverbs`（既存）/ `ronin_hashtags.pick_hashtag_set`（既存）
- Produces: `ronin/ronin_instagram_reels/latest_reel.mp4` と `ronin/ronin_reel_pending.json`(`{"proverb_index", "caption", "video_filename"}`)

- [ ] **Step 1: 定数と generate/main を追記**

Add to the end of `ronin/ronin_reel_engine.py`:
```python
# -----------------------------------------------
# ファイルの場所・定数（このスクリプトと同じ ronin/ にある前提）
# -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "ronin_reel_engine_config.json"
AUDIO_PATH = BASE_DIR / "ronin_reel_assets" / "bgm.mp3"
FRAMES_TMP_DIR = BASE_DIR / "ronin_reel_frames_tmp"   # フレームPNGの一時置き場
REELS_DIR = BASE_DIR / "ronin_instagram_reels"
PENDING_PATH = BASE_DIR / "ronin_reel_pending.json"
PROGRESS_PATH = BASE_DIR / "ronin_reel_progress.json"
JST = timezone(timedelta(hours=9))  # 日本時間


def generate():
    """格言を選んで動画を生成し、pending.json に公開情報を書き出す。"""
    if os.environ.get("RONIN_REEL_ENGINE_ENABLED") != "true":
        print("RONIN_REEL_ENGINE_ENABLED が true でないため停止します。")
        return
    if not AUDIO_PATH.exists():  # 音源が無ければ著作権事故防止のため明確に停止
        print(f"音源が見つかりません: {AUDIO_PATH}（CC0音源を置いてください）")
        return

    config = load_json(str(CONFIG_PATH), default={})

    # 格言データとハッシュタグは既存スクリプトから読む（遅延importで副作用を避ける）
    sys.path.insert(0, str(BASE_DIR))  # ronin/ をimportパスに入れる
    from generate_ronin_cards import proverbs
    from ronin_hashtags import pick_hashtag_set

    total = min(config["total_proverbs"], len(proverbs))
    progress = load_json(str(PROGRESS_PATH), default={"reel_index": -1, "history": []})
    index = next_proverb_index(progress, total)
    proverb = proverbs[index]

    # フレームを描く（遅延import：Pillow依存をgenerate時だけに閉じ込める）
    from ronin_reel_frames import render_reveal_frames
    image_paths = render_reveal_frames(
        proverb, frame_reveal_plan(), str(FRAMES_TMP_DIR), config["width"], config["height"]
    )

    REELS_DIR.mkdir(exist_ok=True)  # 出力先フォルダを用意
    output_path = str(REELS_DIR / config["video_filename"])
    command = build_ffmpeg_command(
        image_paths, str(AUDIO_PATH), output_path,
        config["seconds_per_frame"], config["fps"], config["width"], config["height"],
        config["fade_duration"],
    )
    print("ffmpeg実行:", " ".join(command))
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:  # 生成失敗なら中身を出して停止
        print("ffmpeg失敗:", result.stderr[-1500:])
        return

    caption = build_caption(proverb, pick_hashtag_set(index))
    save_json(str(PENDING_PATH), {
        "proverb_index": index,
        "caption": caption,
        "video_filename": config["video_filename"],
    })
    print(f"生成完了: index={index}, jp={proverb['jp']} → {output_path}")


def main():
    """引数 generate / publish でサブコマンドを振り分ける。"""
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "generate":
        generate()
    elif command == "publish":
        publish()
    else:
        print("使い方: python ronin_reel_engine.py [generate|publish]")


if __name__ == "__main__":
    main()
```

> 注: `publish` は Task 6 で実装する。それまで `main()` から呼ぶと `NameError` になるが、この Task では `generate` のみ検証する。

- [ ] **Step 2: 既存の純粋関数テストが壊れていないことを確認**

Run: `cd /home/kenta_kamijyo && python -m pytest ronin/tests/test_ronin_reel_engine.py -v`
Expected: PASS（7件のまま）

- [ ] **Step 3: ローカルで実動画を生成して確認（要 ffmpeg・bgm.mp3）**

事前条件: `ronin/ronin_reel_assets/bgm.mp3`（CC0音源）が配置済みで、ffmpeg が使えること。
ローカルに ffmpeg が無い場合はこの Step を飛ばし、Task 7 のワークフローを `workflow_dispatch` で手動実行して確認する（その旨をコミットメッセージに残す）。

Run:
```bash
cd /home/kenta_kamijyo/ronin && RONIN_REEL_ENGINE_ENABLED=true python ronin_reel_engine.py generate
```
Expected: `生成完了: index=0, jp=一期一会 → .../latest_reel.mp4` が出て、`ronin/ronin_instagram_reels/latest_reel.mp4` が出来る。長さ約10秒・1080×1920。確認:
```bash
ffprobe -v error -show_entries stream=width,height,codec_name -show_entries format=duration ronin/ronin_instagram_reels/latest_reel.mp4
```
Expected: width=1080 height=1920 codec_name=h264、duration が 約10。

- [ ] **Step 4: Commit**

```bash
cd /home/kenta_kamijyo && git add ronin/ronin_reel_engine.py
git commit -m "ローニンReel: generateサブコマンド（格言選択→フレーム描画→ffmpeg動画生成）"
```

---

### Task 6: publish サブコマンドの実装

生成済み動画を REELS として公開する `publish()` を実装する。raw URL の配信を待ち、REELSコンテナ作成→FINISHEDポーリング→公開、進捗更新まで行う。`wait_for_container_ready` はローニン投稿スクリプトに無いのでエンジン内に自前実装する。

**Files:**
- Modify: `ronin/ronin_reel_engine.py`（`wait_for_url`・`create_reels_container`・`wait_for_container_ready`・`publish` を追加）

**Interfaces:**
- Consumes: `build_raw_video_url`, `load_json`, `save_json`（Task 2）/ `ronin_instagram_auto_post.publish_media`（既存）/ env `INSTAGRAM_ACCESS_TOKEN`・`INSTAGRAM_USER_ID`
- Produces: `wait_for_url(url, max_wait=180) -> bool` / `create_reels_container(video_url, caption, user_id, token) -> str` / `wait_for_container_ready(creation_id, token, max_wait=180) -> bool` / `publish()`

- [ ] **Step 1: publish 系関数を追記**

Add to `ronin/ronin_reel_engine.py`（`generate()` の後・`main()` の前）:
```python
def wait_for_url(url, max_wait=180):
    """動画の raw URL が配信され始める（HTTP 200）まで待つ。"""
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


def wait_for_container_ready(creation_id, token, max_wait=180):
    """動画コンテナの処理が FINISHED になるまで待つ（最大 max_wait 秒）。"""
    url = f"https://graph.facebook.com/v19.0/{creation_id}"
    params = {"fields": "status_code", "access_token": token}
    waited = 0
    while waited < max_wait:
        try:
            response = requests.get(url, params=params, timeout=15)
            status = response.json().get("status_code", "UNKNOWN")
            print(f"  コンテナ状態: {status}（{waited}秒経過）")
            if status == "FINISHED":
                # FINISHED直後でも内部処理が残ることがあるので30秒待つ（9007対策）
                time.sleep(30)
                return True
            if status == "ERROR":
                print(f"コンテナ処理エラー: {response.json()}")
                return False
        except Exception as error:
            print(f"状態確認エラー: {error}")
        time.sleep(10)
        waited += 10
    print(f"{max_wait}秒待っても処理が完了しませんでした。")
    return False


def publish():
    """pending.json を読み、動画URLの配信を待ってから Reels を公開する。"""
    if os.environ.get("RONIN_REEL_ENGINE_ENABLED") != "true":
        print("RONIN_REEL_ENGINE_ENABLED が true でないため停止します。")
        return

    config = load_json(str(CONFIG_PATH), default={})
    pending = load_json(str(PENDING_PATH), default={})
    if not pending:
        print("公開対象（pending.json）がありません。")
        return

    token = os.environ["INSTAGRAM_ACCESS_TOKEN"]
    user_id = os.environ["INSTAGRAM_USER_ID"]
    video_url = build_raw_video_url(config["raw_video_base"], pending["video_filename"])

    if not wait_for_url(video_url):  # URLが生えるまで待つ
        print(f"動画URLが配信されませんでした: {video_url}")
        return

    creation_id = create_reels_container(video_url, pending["caption"], user_id, token)
    if not creation_id:
        return
    if not wait_for_container_ready(creation_id, token):
        print("動画の処理が完了しませんでした。")
        return

    # 公開は既存スクリプトを再利用（env必須なので遅延import）
    sys.path.insert(0, str(BASE_DIR))
    from ronin_instagram_auto_post import publish_media
    result = publish_media(creation_id)
    if not result.get("id"):
        print(f"公開失敗: {result}")
        return

    # 進捗を進める・履歴に当日を追記
    progress = load_json(str(PROGRESS_PATH), default={"reel_index": -1, "history": []})
    today = datetime.now(JST).strftime("%Y-%m-%d")
    progress["reel_index"] = pending["proverb_index"]
    progress.setdefault("history", []).append(today)
    save_json(str(PROGRESS_PATH), progress)
    print(f"公開完了: post_id={result['id']}")
```

- [ ] **Step 2: create_reels_container のパラメータをテスト（requestsをモック）**

Append to `ronin/tests/test_ronin_reel_engine.py`:
```python
def test_create_reels_container_sends_reels_params(monkeypatch):
    captured = {}

    class FakeResponse:
        def json(self):
            return {"id": "creation_123"}

    def fake_post(url, params, timeout):
        captured["url"] = url
        captured["params"] = params
        return FakeResponse()

    monkeypatch.setattr(engine.requests, "post", fake_post)
    creation_id = engine.create_reels_container(
        "https://raw.example.com/latest_reel.mp4", "caption text", "USER1", "TOKEN1"
    )
    assert creation_id == "creation_123"
    assert captured["params"]["media_type"] == "REELS"
    assert captured["params"]["video_url"] == "https://raw.example.com/latest_reel.mp4"
    assert captured["params"]["access_token"] == "TOKEN1"
    assert "USER1" in captured["url"]
```

- [ ] **Step 3: テストが通ることを確認**

Run: `cd /home/kenta_kamijyo && python -m pytest ronin/tests/test_ronin_reel_engine.py -v`
Expected: PASS（8件）

- [ ] **Step 4: Commit**

```bash
cd /home/kenta_kamijyo && git add ronin/ronin_reel_engine.py ronin/tests/test_ronin_reel_engine.py
git commit -m "ローニンReel: publishサブコマンド（REELSコンテナ作成→FINISHED待ち→公開）"
```

---

### Task 7: GitHub Actions ワークフロー

1日1回 generate→push→publish を回すワークフローを追加する。既存の ronin ワークフローには触れない。

**Files:**
- Create: `.github/workflows/ronin_instagram_reels.yml`

**Interfaces:**
- Consumes: `RONIN_REEL_ENGINE_ENABLED`(Variables) / `INSTAGRAM_ACCESS_TOKEN`・`INSTAGRAM_USER_ID`(Secrets)

- [ ] **Step 1: ワークフローを作成**

Create `.github/workflows/ronin_instagram_reels.yml`:
```yaml
# ronin_instagram_reels.yml
# @RoninWords Instagram Reels 自動生成・自動投稿
# 1日1回 JST 19:30 に起動し、縦型リビール動画を生成→push→Reels公開する

name: ronin Instagram Reels

on:
  schedule:
    - cron: '30 10 * * *'  # JST 19:30 = UTC 10:30
  workflow_dispatch:

concurrency:
  group: ronin-instagram-reels
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
        run: pip install requests python-dotenv pillow

      - name: 動画を生成
        env:
          RONIN_REEL_ENGINE_ENABLED: ${{ vars.RONIN_REEL_ENGINE_ENABLED }}
        run: cd ronin && python ronin_reel_engine.py generate

      - name: 動画と受け渡しファイルをコミット＆プッシュ（公開URLを生やす）
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add ronin/ronin_instagram_reels/latest_reel.mp4 ronin/ronin_reel_pending.json
          if ! git diff --staged --quiet; then
            git commit -m "自動生成: ronin Reels動画更新"
            for i in 1 2 3; do
              git pull --rebase origin main && git push && break
              echo "push失敗 リトライ $i/3..."
              sleep 5
            done
          fi

      - name: Reels を公開
        env:
          RONIN_REEL_ENGINE_ENABLED: ${{ vars.RONIN_REEL_ENGINE_ENABLED }}
          INSTAGRAM_ACCESS_TOKEN: ${{ secrets.INSTAGRAM_ACCESS_TOKEN }}
          INSTAGRAM_USER_ID: ${{ secrets.INSTAGRAM_USER_ID }}
        run: cd ronin && python ronin_reel_engine.py publish

      - name: 進捗をコミット＆プッシュ
        run: |
          git add ronin/ronin_reel_progress.json
          if ! git diff --staged --quiet; then
            git commit -m "自動同期: ronin Reels進捗更新"
            for i in 1 2 3; do
              git pull --rebase origin main && git push && break
              echo "push失敗 リトライ $i/3..."
              sleep 5
            done
          fi
```

> 注: `INSTAGRAM_ACCESS_TOKEN`/`INSTAGRAM_USER_ID` が Secrets に未登録なら、既存の ronin 画像投稿ワークフロー(`ronin_instagram_auto_post.yml`)が使っている secret 名に合わせること。差異があればこの env 名を実態に合わせて直す。

- [ ] **Step 2: YAML 構文を確認**

Run:
```bash
cd /home/kenta_kamijyo && python -c "import yaml; yaml.safe_load(open('.github/workflows/ronin_instagram_reels.yml')); print('YAML OK')"
```
Expected: `YAML OK`

- [ ] **Step 3: 既存 ronin 画像ワークフローの secret 名と一致するか確認**

Run:
```bash
grep -n "INSTAGRAM_ACCESS_TOKEN\|INSTAGRAM_USER_ID\|secrets\." /home/kenta_kamijyo/.github/workflows/ronin_instagram_auto_post.yml
```
Expected: 同じ secret 名が使われていること。違えば Step 1 の env 名を合わせて修正。

- [ ] **Step 4: Commit**

```bash
cd /home/kenta_kamijyo && git add .github/workflows/ronin_instagram_reels.yml
git commit -m "ローニンReel: 1日1回のGitHub Actionsワークフロー追加"
```

---

## 受け入れ確認（全タスク後・ユーザー作業含む）

1. ユーザーが `ronin/ronin_reel_assets/bgm.mp3`（CC0音源）を配置。
2. ユーザーが GitHub Variables に `RONIN_REEL_ENGINE_ENABLED=true` を設定。
3. `INSTAGRAM_ACCESS_TOKEN`/`INSTAGRAM_USER_ID` が Secrets にあることを確認（既存画像投稿用を流用）。
4. `gh workflow run ronin_instagram_reels.yml` で手動実行し、Reels が投稿されることを確認。
5. 確認後はスケジュール(JST 19:30)で自動運用。問題時は `RONIN_REEL_ENGINE_ENABLED=false` で即停止。

---

## Self-Review

- **Spec coverage:** §4.1 ファイル構成→全Taskで網羅。§4.2 リビール4フレーム→Task4。§4.3 generate/publish→Task5/6。§4.4 キルスイッチ→Task5/6 冒頭。§4.5 スケジュール→Task7。§4.6 テスト対象→Task2/3/6。§5 事前作業→受け入れ確認。§6 リスク(フォント未導入)→Task1 で追加対応。
- **Placeholder scan:** TBD/TODO 無し。全コードブロックは実コード。
- **Type consistency:** `next_proverb_index`/`build_caption`/`build_ffmpeg_command`/`build_raw_video_url`/`render_reveal_frames`/`create_reels_container`/`wait_for_container_ready` のシグネチャは定義Taskと利用Task(generate/publish)で一致。pending.json のキー(`proverb_index`/`caption`/`video_filename`)も Task5(生成)と Task6(消費)で一致。progress のキー `reel_index` も Task2/5/6 で一致。
