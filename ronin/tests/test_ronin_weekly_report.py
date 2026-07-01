# ronin/tests/test_ronin_weekly_report.py
# ronin_weekly_report.py の純粋ロジックをテストする（ネットワーク・実ファイル書き出しは対象外）
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ronin_weekly_report import (
    recent_posts,
    summarize,
    top_posts,
    suggest_next_actions,
    build_report,
)

JST = timezone(timedelta(hours=9))
TODAY = datetime(2026, 7, 1, 12, 0, tzinfo=JST)


def _post(days_ago, views=10, likes=0, engagement=10.0, type_="morning"):
    """TODAYから days_ago 日前の投稿データを作る（テスト用）"""
    posted = (TODAY - timedelta(days=days_ago)).astimezone(timezone.utc)
    return {
        "posted_at": posted.strftime("%Y-%m-%dT%H:%M:%S+0000"),
        "views": views,
        "likes": likes,
        "engagement_rate": engagement,
        "type": type_,
    }


def test_recent_posts_keeps_within_window():
    history = [_post(1), _post(6), _post(8)]
    result = recent_posts(history, TODAY, days=7)
    assert len(result) == 2


def test_recent_posts_skips_broken_date():
    history = [_post(1), {"posted_at": "こわれた日付", "views": 10}]
    result = recent_posts(history, TODAY)
    assert len(result) == 1


def test_summarize_computes_averages():
    posts = [_post(1, views=10, likes=1), _post(2, views=20, likes=0)]
    s = summarize(posts)
    assert s["count"] == 2
    assert s["avg_views"] == 15.0
    assert s["avg_likes"] == 0.5
    assert s["total_views"] == 30


def test_summarize_empty_is_zero():
    s = summarize([])
    assert s == {"count": 0, "avg_views": 0.0, "avg_likes": 0.0, "avg_engagement": 0.0, "total_views": 0}


def test_top_posts_sorts_by_views():
    posts = [_post(1, views=5), _post(2, views=20), _post(3, views=10)]
    tops = top_posts(posts, n=2)
    assert [p["views"] for p in tops] == [20, 10]


def test_suggest_actions_flags_zero_likes_and_low_views():
    s = summarize([_post(1, views=10, likes=0, engagement=2.0)])
    actions = suggest_next_actions(s)
    joined = " ".join(actions)
    assert "1コメ目" in joined
    assert "reply_hunter" in joined


def test_suggest_actions_no_data():
    actions = suggest_next_actions(summarize([]))
    assert "データ" in actions[0]


def test_build_report_has_sections():
    history = [_post(1, views=10, likes=0)]
    report = build_report(history, TODAY, pattern_ranking=[{"day": 140, "score": 14.3, "priority": 1}])
    assert "週次レポート" in report
    assert "直近7日のサマリー" in report
    assert "高反応パターン" in report
    assert "次の打ち手" in report


def test_build_report_pattern_ranking省略可():
    history = [_post(1, views=10, likes=0)]
    report = build_report(history, TODAY)
    assert "週次レポート" in report
    assert "高反応パターン" not in report
