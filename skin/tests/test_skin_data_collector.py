"""skin_data_collector.py の投稿照合ロジックの単体テスト。"""
# pytestを使って純関数の挙動を確認するファイル（APIは叩かない）
import sys
from pathlib import Path

# skin/ 配下を import path に追加する
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_data_collector import match_day_and_type


def test_match_day_and_type_finds_post_in_threads_a():
    # threads_a 側の朝投稿（index 0）を正しく morning と判定できることを確認
    posts_data = {
        "threads_a": [
            {"id": 5, "theme": "腸活", "posts": ["朝の投稿テキストです", "2本目の投稿", "夜の投稿テキスト"]},
        ],
        "threads_b": [],
    }
    result = match_day_and_type(posts_data, "朝の投稿テキストです")
    assert result == (5, "腸活", "morning")


def test_match_day_and_type_finds_post_in_threads_b():
    # threads_b 側の3本目（index 2）を evening と判定し、threads_b も走査することを確認
    posts_data = {
        "threads_a": [],
        "threads_b": [
            {"id": 7, "theme": "睡眠", "posts": ["b朝1", "b朝2", "夜の睡眠投稿テキスト"]},
        ],
    }
    result = match_day_and_type(posts_data, "夜の睡眠投稿テキスト")
    assert result == (7, "睡眠", "evening")


def test_match_day_and_type_returns_none_when_no_match():
    # どのパターンにも一致しなければ (None, None, None) を返すことを確認
    posts_data = {
        "threads_a": [{"id": 1, "theme": "X", "posts": ["abc"]}],
        "threads_b": [],
    }
    result = match_day_and_type(posts_data, "存在しないテキスト")
    assert result == (None, None, None)
