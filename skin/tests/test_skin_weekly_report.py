# test_skin_weekly_report.py
# skin_weekly_report.py の純粋ロジックをテストする（ネットワーク・実ファイル書き出しは対象外）

import os
import sys
from datetime import datetime, timezone, timedelta

# skinフォルダをimportパスに追加する（テストからモジュールを読み込むため）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from skin_weekly_report import (
    recent_posts,
    summarize,
    top_posts,
    suggest_next_actions,
    ab_summary,
    build_report,
)

JST = timezone(timedelta(hours=9))
TODAY = datetime(2026, 6, 20, 12, 0, tzinfo=JST)


def _post(days_ago, views=50, likes=0, engagement=2.0, type_="テーマ"):
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
    # 7日以内だけ残し、8日前は落とすこと
    history = [_post(1), _post(6), _post(8)]
    result = recent_posts(history, TODAY, days=7)
    assert len(result) == 2


def test_recent_posts_skips_broken_date():
    # 日付が壊れたデータは飛ばす（全体は止めない）
    history = [_post(1), {"posted_at": "こわれた日付", "views": 10}]
    result = recent_posts(history, TODAY)
    assert len(result) == 1


def test_summarize_computes_averages():
    posts = [_post(1, views=100, likes=2), _post(2, views=200, likes=0)]
    s = summarize(posts)
    assert s["count"] == 2
    assert s["avg_views"] == 150.0
    assert s["avg_likes"] == 1.0
    assert s["total_views"] == 300


def test_summarize_empty_is_zero():
    s = summarize([])
    assert s == {"count": 0, "avg_views": 0.0, "avg_likes": 0.0, "avg_engagement": 0.0, "total_views": 0}


def test_top_posts_sorts_by_views():
    posts = [_post(1, views=30), _post(2, views=90), _post(3, views=60)]
    tops = top_posts(posts, n=2)
    assert [p["views"] for p in tops] == [90, 60]


def test_suggest_actions_flags_zero_likes_and_low_views():
    # いいね極小・閲覧低だと、シード見直しとリプ有効化が提案される
    s = summarize([_post(1, views=40, likes=0)])
    actions = suggest_next_actions(s)
    joined = " ".join(actions)
    assert "1コメ目" in joined
    assert "リプライ・エンジン" in joined


def test_suggest_actions_no_data():
    actions = suggest_next_actions(summarize([]))
    assert "データ" in actions[0]


def test_ab_summary_counts_verdicts():
    # 十分なデータ（各3投稿以上）でA優位ならA_winsが立つ
    ab_results = {
        "1": {"a_score": 30.0, "b_score": 10.0, "a_posts": 3, "b_posts": 3},
        "2": {"a_score": 0.0, "b_score": 0.0, "a_posts": 1, "b_posts": 0},
    }
    counts = ab_summary(ab_results)
    assert counts["A_wins"] == 1
    assert counts["insufficient_data"] == 1


def test_build_report_has_sections():
    history = [_post(1, views=40, likes=0)]
    report = build_report(history, TODAY, ab_results={})
    assert "週次レポート" in report
    assert "直近7日のサマリー" in report
    assert "次の打ち手" in report
