# test_skin_hashtags.py
# skin_hashtags.py（ハッシュタグローテーション）のテスト

import os
import sys

# skinフォルダをimportパスに追加する（テストからモジュールを読み込むため）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from skin_hashtags import HASHTAG_SETS, pick_hashtag_set


def test_rotation_order_a_to_d():
    # カウント0〜3でA→B→C→Dの順に返ること
    assert pick_hashtag_set(0) == HASHTAG_SETS["A"]
    assert pick_hashtag_set(1) == HASHTAG_SETS["B"]
    assert pick_hashtag_set(2) == HASHTAG_SETS["C"]
    assert pick_hashtag_set(3) == HASHTAG_SETS["D"]


def test_rotation_wraps_back_to_a():
    # カウント4で先頭のAに戻ること
    assert pick_hashtag_set(4) == HASHTAG_SETS["A"]


def test_each_set_has_three_tags():
    # 各セットがちょうど3個のタグであること（スパム判定回避の設計）
    for key, tags in HASHTAG_SETS.items():
        assert tags.count("#") == 3, f"セット{key}のタグ数が3個ではない"


def test_no_duplicate_tags_within_set():
    # 1セット内に同じタグが重複していないこと
    for key, tags in HASHTAG_SETS.items():
        tag_list = tags.split()
        assert len(tag_list) == len(set(tag_list)), f"セット{key}内にタグ重複"
