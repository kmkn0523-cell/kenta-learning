# test_skin_reels_engine.py
# skin_reels_engine.py の純粋ロジックをテストする（ffmpeg実行・ネットワークは対象外）
# 実行: pytest skin/tests/test_skin_reels_engine.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_reels_engine import next_theme_index
from skin_reels_engine import slides_to_use, build_local_slide_paths
from skin_reels_engine import build_ffmpeg_command


def test_next_theme_index_通常は1進む():
    assert next_theme_index({"reels_index": 0}, 20) == 1

def test_next_theme_index_末尾で先頭に戻る():
    assert next_theme_index({"reels_index": 19}, 20) == 0

def test_next_theme_index_キー無しは0扱いで1():
    assert next_theme_index({}, 20) == 1


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
