"""skin_account_metrics_collector.py の純関数の単体テスト。"""
# pytestを使って純関数の挙動を確認するファイル（APIは叩かない）
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# skin/ 配下を import path に追加する
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_account_metrics_collector import (
    compute_jst_yesterday_window,
    build_metric_record,
    JST,
)


def test_compute_jst_yesterday_window_returns_previous_day_date():
    # JST 2026-07-01 10:00 を基準にすると、対象日は前日の2026-06-30になることを確認
    now_jst = datetime(2026, 7, 1, 10, 0, 0, tzinfo=JST)
    since_ts, until_ts, date_str = compute_jst_yesterday_window(now_jst)
    assert date_str == "2026-06-30"


def test_compute_jst_yesterday_window_spans_exactly_one_day():
    # since〜untilの範囲がちょうど24時間(86400秒)になることを確認
    now_jst = datetime(2026, 7, 1, 10, 0, 0, tzinfo=JST)
    since_ts, until_ts, _ = compute_jst_yesterday_window(now_jst)
    assert until_ts - since_ts == 86400


def test_compute_jst_yesterday_window_handles_month_boundary():
    # 月初(7/1 0:05)を基準にしても、対象日は前月末日(6/30)になることを確認
    now_jst = datetime(2026, 7, 1, 0, 5, 0, tzinfo=JST)
    _, _, date_str = compute_jst_yesterday_window(now_jst)
    assert date_str == "2026-06-30"


def test_build_metric_record_keeps_none_when_missing():
    # API取得に失敗した項目はNoneのまま記録し、値を捏造しないことを確認
    record = build_metric_record("2026-06-30", views_total=None, followers_total=500)
    assert record["date"] == "2026-06-30"
    assert record["views_total"] is None
    assert record["followers_total"] == 500


def test_build_metric_record_includes_both_metrics():
    # 取得できた値がそのまま記録されることを確認
    record = build_metric_record("2026-06-30", views_total=12000, followers_total=340)
    assert record["views_total"] == 12000
    assert record["followers_total"] == 340
