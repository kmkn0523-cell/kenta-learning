# test_skin_optimizer.py
# skin_optimizer.py の複合スコア計算をテストする
# 目的：閲覧数（リーチ）主軸・少数分母の外れ値抑制が効いているかを確認する
# 実行: pytest skin/tests/test_skin_optimizer.py

import os
import sys

# skinディレクトリをimportパスに追加する（skin_optimizerを読み込むため）
_SKIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKIN_DIR not in sys.path:
    sys.path.insert(0, _SKIN_DIR)

from skin_optimizer import calculate_pattern_score, generate_pattern_ranking


def test_views_zero_returns_zero():
    """閲覧数が0なら評価不能なのでスコアは0になる"""
    assert calculate_pattern_score(0, 0, 0) == 0.0


def test_reach_beats_low_view_outlier():
    """
    旧ロジックの欠陥を再現するケース：
    Aは閲覧数100・反応0、Bは閲覧数9・コメント2（旧来は率22%で1位）。
    新ロジックではリーチの大きいAがBに勝つはず。
    """
    score_high_reach = calculate_pattern_score(avg_views=100, avg_likes=0, avg_comments=0)
    score_low_view_outlier = calculate_pattern_score(avg_views=9, avg_likes=0, avg_comments=2)
    assert score_high_reach > score_low_view_outlier


def test_engagement_adds_bonus():
    """同じ閲覧数なら、反応が付いた方がスコアが高くなる（エンゲージ加点が効く）"""
    without_engagement = calculate_pattern_score(avg_views=50, avg_likes=0, avg_comments=0)
    with_engagement = calculate_pattern_score(avg_views=50, avg_likes=3, avg_comments=2)
    assert with_engagement > without_engagement


def test_smoothing_caps_small_denominator():
    """
    分母が小さい時の跳ね上がりを平滑化が抑えること。
    閲覧数5・コメント2（生の率40%）でも、スコアは閲覧数5の数倍までに収まる。
    """
    score = calculate_pattern_score(avg_views=5, avg_likes=0, avg_comments=2)
    # 平滑化なし（生の率×倍率）なら 5×(1+0.4×10)=25 まで膨らむが、
    # 平滑化ありなら 5×(1+2/35×10)=約7.9 に抑えられる
    assert score < 10


def test_ranking_orders_by_score_desc():
    """generate_pattern_ranking がスコア降順で優先度を振ること"""
    performance = {
        "day_1": {"テーマX": {"total_posts": 2, "avg_views": 100, "avg_likes": 1, "avg_comments": 0}},
        "day_2": {"テーマY": {"total_posts": 2, "avg_views": 10, "avg_likes": 0, "avg_comments": 2}},
    }
    ranking = generate_pattern_ranking(performance)
    # 先頭（priority 1）は閲覧数の大きい day_1 になるはず
    assert ranking[0]["day"] == 1
    assert ranking[0]["priority"] == 1
    assert ranking[1]["priority"] == 2
