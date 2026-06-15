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
