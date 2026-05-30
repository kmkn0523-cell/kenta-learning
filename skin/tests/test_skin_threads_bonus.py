"""ボーナス投稿の発火判定 should_fire_bonus のテスト

投稿APIは一切叩かず、判定ロジック（純関数）だけを検証する。
"""
import sys                              # モジュール検索パスをいじる道具
from pathlib import Path               # ファイルパスを扱う道具
from datetime import date              # 日付を作る道具

# テスト対象のファイルがある skin/ ディレクトリをimport対象に加える
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_threads_action import should_fire_bonus  # 判定する純関数


def test_should_fire_bonus_true_when_yesterday_spiked():
    """前日(5/15)に跳ねた投稿があれば True を返す"""
    # 5/15 に views19/likes2/rate10.53 の跳ねた投稿。直近14日平均は4.2575
    # 閾値 = 4.2575 × 1.5 = 6.38625 < 10.53 なので発火する
    posts_history = [
        {"posted_at": "2026-05-15T04:01:07+0000", "views": 19, "likes": 2, "engagement_rate": 10.53},
        {"posted_at": "2026-05-14T04:01:07+0000", "views": 30, "likes": 1, "engagement_rate": 3.33},
        {"posted_at": "2026-05-13T04:01:07+0000", "views": 40, "likes": 1, "engagement_rate": 2.50},
        {"posted_at": "2026-05-12T04:01:07+0000", "views": 50, "likes": 0, "engagement_rate": 0.0},
    ]
    today = date(2026, 5, 16)  # 5/15 の翌日に判定する
    assert should_fire_bonus(posts_history, today) is True


def test_should_fire_bonus_false_when_likes_too_low():
    """likes が足切り(2)未満なら False"""
    posts_history = [
        {"posted_at": "2026-05-15T04:01:07+0000", "views": 19, "likes": 1, "engagement_rate": 10.53},
        {"posted_at": "2026-05-14T04:01:07+0000", "views": 30, "likes": 1, "engagement_rate": 3.33},
        {"posted_at": "2026-05-13T04:01:07+0000", "views": 40, "likes": 1, "engagement_rate": 2.50},
    ]
    today = date(2026, 5, 16)
    assert should_fire_bonus(posts_history, today) is False


def test_should_fire_bonus_false_when_views_too_low():
    """views が足切り(15)未満なら False"""
    posts_history = [
        {"posted_at": "2026-05-15T04:01:07+0000", "views": 14, "likes": 2, "engagement_rate": 10.53},
        {"posted_at": "2026-05-14T04:01:07+0000", "views": 30, "likes": 1, "engagement_rate": 3.33},
        {"posted_at": "2026-05-13T04:01:07+0000", "views": 40, "likes": 1, "engagement_rate": 2.50},
    ]
    today = date(2026, 5, 16)
    assert should_fire_bonus(posts_history, today) is False


def test_should_fire_bonus_false_when_below_relative_threshold():
    """相対閾値（直近14日平均×1.5）に届かなければ False"""
    # 全部 rate5.0 → 平均5.0、閾値7.5。前日の rate5.0 は届かない
    posts_history = [
        {"posted_at": "2026-05-15T04:01:07+0000", "views": 100, "likes": 5, "engagement_rate": 5.0},
        {"posted_at": "2026-05-14T04:01:07+0000", "views": 100, "likes": 5, "engagement_rate": 5.0},
        {"posted_at": "2026-05-13T04:01:07+0000", "views": 100, "likes": 5, "engagement_rate": 5.0},
    ]
    today = date(2026, 5, 16)
    assert should_fire_bonus(posts_history, today) is False


def test_should_fire_bonus_false_when_history_empty():
    """履歴が空なら安全側で False"""
    assert should_fire_bonus([], date(2026, 5, 16)) is False
