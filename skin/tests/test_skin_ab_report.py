"""skin_ab_report.py の判定ロジックのテスト。"""
# レポート関数の判定結果を確認するファイル
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_ab_report import judge_theme, generate_report


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
