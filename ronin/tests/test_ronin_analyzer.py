# test_ronin_analyzer.py
# 「最古の投稿日時」を順序に依存せず求められるかのテスト
# 実行: pytest ronin/tests/test_ronin_analyzer.py -v
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ronin_analyzer import earliest_post_datetime


def test_並びが新しい順でも最古を返す():
    history = [
        {"posted_at": "2026-06-01T00:00:00+0000"},  # 新しいものが先頭
        {"posted_at": "2026-05-01T00:00:00+0000"},  # 本当の最古は末尾
    ]
    dt = earliest_post_datetime(history)
    assert dt.month == 5 and dt.day == 1


def test_空なら_None():
    assert earliest_post_datetime([]) is None


def test_posted_at欠落は無視():
    history = [{"foo": "bar"}, {"posted_at": "2026-05-10T00:00:00+0000"}]
    dt = earliest_post_datetime(history)
    assert dt.day == 10
