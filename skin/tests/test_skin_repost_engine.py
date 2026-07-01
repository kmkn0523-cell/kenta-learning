# test_skin_repost_engine.py
# skin_repost_engine.py の純粋ロジックをテストする（ネットワーク・対話は対象外）
# 実行: pytest skin/tests/test_skin_repost_engine.py

import sys
from datetime import datetime, timezone
from pathlib import Path

# skin/ フォルダをimportできる場所に加える（既存テストと同じやり方）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_repost_engine import (
    compute_average_views,
    is_repost_candidate,
    select_repost_candidate,
    new_state,
)

NOW = datetime(2026, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
CONFIG = {"min_age_days": 21, "min_views_multiplier": 1.5, "max_failed_attempts": 3}


def _post(**kw):
    base = {"post_id": "p1", "posted_at": "2026-06-01T00:00:00+0000", "views": 100}
    base.update(kw)
    return base


def test_compute_average_views_views0件を除外して平均を出す():
    posts = [_post(views=100), _post(views=200), _post(views=0), _post(views=None)]
    assert compute_average_views(posts) == 150.0


def test_compute_average_views_対象が無ければ0():
    assert compute_average_views([]) == 0
    assert compute_average_views([_post(views=0)]) == 0


def test_is_repost_candidate_新しすぎる投稿は除外():
    state = new_state()
    post = _post(posted_at="2026-06-25T00:00:00+0000", views=200)  # 6日前
    assert is_repost_candidate(post, NOW, state, CONFIG, average_views=100) is False


def test_is_repost_candidate_十分古ければ対象():
    state = new_state()
    post = _post(posted_at="2026-06-01T00:00:00+0000", views=200)  # 30日前
    assert is_repost_candidate(post, NOW, state, CONFIG, average_views=100) is True


def test_is_repost_candidate_閲覧数が平均未満なら除外():
    state = new_state()
    post = _post(posted_at="2026-06-01T00:00:00+0000", views=120)  # 平均100の1.5倍未満
    assert is_repost_candidate(post, NOW, state, CONFIG, average_views=100) is False


def test_is_repost_candidate_リポスト済みは除外():
    state = new_state()
    state["reposted_post_ids"] = ["p1"]
    post = _post(views=200)
    assert is_repost_candidate(post, NOW, state, CONFIG, average_views=100) is False


def test_is_repost_candidate_失敗上限に達したら除外():
    state = new_state()
    state["failed_attempts"] = {"p1": 3}
    post = _post(views=200)
    assert is_repost_candidate(post, NOW, state, CONFIG, average_views=100) is False


def test_select_repost_candidate_閲覧数最大のものを選ぶ():
    state = new_state()
    # 平均を押し下げる低閲覧の投稿を混ぜ、p2/p3 が平均の1.5倍を超えるようにする
    posts = [
        _post(post_id="low1", views=10),
        _post(post_id="low2", views=10),
        _post(post_id="p1", views=150),
        _post(post_id="p2", views=300),
        _post(post_id="p3", views=200),
    ]
    result = select_repost_candidate(posts, NOW, state, CONFIG)
    assert result["post_id"] == "p2"


def test_select_repost_candidate_対象が無ければNone():
    state = new_state()
    posts = [_post(posted_at="2026-06-30T00:00:00+0000", views=1000)]  # 新しすぎる
    assert select_repost_candidate(posts, NOW, state, CONFIG) is None
