"""skin_ab_report.py の判定ロジックのテスト。"""
# レポート関数の判定結果を確認するファイル
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_ab_report import judge_theme, generate_report, aggregate_ab_scores


def test_aggregate_sums_engagement_rate_per_variant():
    # テーマ5でA投稿1件(rate=10)・B投稿1件(rate=4) → a_score=10, b_score=4
    history = [
        {"theme_id": 5, "variant": "A", "post_id": "111"},
        {"theme_id": 5, "variant": "B", "post_id": "222"},
    ]
    posts_history = [
        {"post_id": "111", "engagement_rate": 10.0},
        {"post_id": "222", "engagement_rate": 4.0},
    ]
    results = aggregate_ab_scores(history, posts_history)
    assert results["5"]["a_score"] == 10.0
    assert results["5"]["b_score"] == 4.0
    assert results["5"]["a_posts"] == 1
    assert results["5"]["b_posts"] == 1


def test_aggregate_skips_posts_without_reaction_data():
    # analyticsに反応が無いpost_idは集計対象外（投稿カウントもしない）
    history = [
        {"theme_id": 7, "variant": "A", "post_id": "333"},
        {"theme_id": 7, "variant": "A", "post_id": "999"},  # analyticsに無い
    ]
    posts_history = [
        {"post_id": "333", "engagement_rate": 6.0},
    ]
    results = aggregate_ab_scores(history, posts_history)
    assert results["7"]["a_score"] == 6.0
    assert results["7"]["a_posts"] == 1


def test_aggregate_ignores_incomplete_history_entries():
    # theme_id や variant が欠けたエントリは無視する
    history = [
        {"variant": "A", "post_id": "444"},          # theme_id無し
        {"theme_id": 8, "post_id": "555"},            # variant無し
        {"theme_id": 8, "variant": "A"},              # post_id無し
    ]
    posts_history = [
        {"post_id": "444", "engagement_rate": 5.0},
        {"post_id": "555", "engagement_rate": 5.0},
    ]
    results = aggregate_ab_scores(history, posts_history)
    assert results == {}


def test_judge_theme_returns_no_data_when_posts_below_threshold():
    # A=2回・B=3回 → 不足
    result = judge_theme(theme_id=1, a_score=100, b_score=50, a_posts=2, b_posts=3, min_posts=3)
    assert result["verdict"] == "insufficient_data"


def test_judge_theme_returns_A_winner_when_20pct_lead():
    # A平均80・B平均50 → A勝ち
    result = judge_theme(theme_id=1, a_score=240, b_score=150, a_posts=3, b_posts=3, min_posts=3)
    assert result["verdict"] == "A_wins"
    assert result["lead_pct"] >= 0.2


def test_judge_theme_returns_B_winner_when_20pct_lead():
    # A平均50・B平均80 → B勝ち
    result = judge_theme(theme_id=1, a_score=150, b_score=240, a_posts=3, b_posts=3, min_posts=3)
    assert result["verdict"] == "B_wins"


def test_judge_theme_returns_no_diff_when_under_20pct():
    # A平均70・B平均65 → 差なし
    result = judge_theme(theme_id=1, a_score=210, b_score=195, a_posts=3, b_posts=3, min_posts=3)
    assert result["verdict"] == "no_significant_diff"


def test_generate_report_returns_string_with_theme_lines():
    progress = {
        "ab_results": {
            "1": {"a_score": 240.0, "b_score": 150.0, "a_posts": 3, "b_posts": 3},
            "2": {"a_score": 100.0, "b_score": 95.0, "a_posts": 3, "b_posts": 3},
        }
    }
    report = generate_report(progress, themes=[1, 2])
    assert "テーマ1" in report
    assert "テーマ2" in report
    assert "A勝ち" in report or "A_wins" in report
