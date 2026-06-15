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
    current = progress.get("reels_index", 0)
    return (current + 1) % total_themes


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


def build_caption(theme):
    """テーマのフック文＋ハッシュタグでReelsキャプションを組み立てる。"""
    tags = theme.get("fixed_hashtags", []) + theme.get("theme_hashtags", []) + theme.get("size_mix_hashtags", [])
    hashtag_line = " ".join(f"#{tag}" for tag in tags)
    return f"{theme.get('hook', '')}\n\n{hashtag_line}"


def build_raw_video_url(raw_video_base, filename):
    """動画のraw公開URLを組み立てる。"""
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
