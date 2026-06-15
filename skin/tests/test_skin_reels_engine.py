# test_skin_reels_engine.py
# skin_reels_engine.py の純粋ロジックをテストする（ffmpeg実行・ネットワークは対象外）
# 実行: pytest skin/tests/test_skin_reels_engine.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_reels_engine import next_theme_index
from skin_reels_engine import slides_to_use, build_local_slide_paths


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
