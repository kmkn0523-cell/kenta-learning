# test_ronin_hashtags.py
# ハッシュタグ・ローテーションの純粋関数テスト
# 実行: pytest ronin/tests/test_ronin_hashtags.py -v
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # ronin/ をimport可能にする

from ronin_hashtags import pick_hashtag_set, HASHTAG_SETS


def test_四セットを順番に回す():
    assert pick_hashtag_set(0) == HASHTAG_SETS["A"]
    assert pick_hashtag_set(1) == HASHTAG_SETS["B"]
    assert pick_hashtag_set(2) == HASHTAG_SETS["C"]
    assert pick_hashtag_set(3) == HASHTAG_SETS["D"]


def test_四を超えたら先頭に戻る():
    assert pick_hashtag_set(4) == HASHTAG_SETS["A"]
    assert pick_hashtag_set(7) == HASHTAG_SETS["D"]


def test_各セットはハッシュタグ文字列():
    for value in HASHTAG_SETS.values():
        assert value.startswith("#")
        assert "  " not in value  # 二重スペースが無い
