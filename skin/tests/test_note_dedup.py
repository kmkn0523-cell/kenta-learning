"""note_dedup.py の重複投稿ガードのテスト。"""
# 「今日すでに投稿済みか？」を判定する純粋関数のテストファイル
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from note_dedup import already_posted_today


def test_empty_history_is_not_posted():
    # 履歴が空なら未投稿
    assert already_posted_today([], "2026/06/08") is False


def test_today_entry_as_last_is_detected():
    # 今日の投稿が末尾にある → 投稿済み
    history = [
        {"date": "2026/06/07 21:22", "article": "article_06.md"},
        {"date": "2026/06/08 09:01", "article": "article_07.md"},
    ]
    assert already_posted_today(history, "2026/06/08") is True


def test_no_today_entry_returns_false():
    # 今日の投稿が無い → 未投稿（別日だけ）
    history = [
        {"date": "2026/06/07 21:22", "article": "article_06.md"},
        {"date": "2026/06/05 12:41", "article": "article_05.md"},
    ]
    assert already_posted_today(history, "2026/06/08") is False


def test_today_entry_not_last_is_still_detected():
    # 今日の投稿が末尾でない位置にあっても検知する
    # （旧ガードは history[-1] しか見ず、これを見逃して重複投稿が起きた）
    history = [
        {"date": "2026/06/08 09:01", "article": "article_07.md"},
        {"date": "2026/06/09 09:01", "article": "article_08.md"},  # 末尾は翌日
    ]
    assert already_posted_today(history, "2026/06/08") is True


def test_missing_date_key_is_safe():
    # date キーが無いエントリが混ざっていても落ちない
    history = [{"article": "broken.md"}, {"date": "2026/06/08 09:01"}]
    assert already_posted_today(history, "2026/06/08") is True


def test_partial_date_does_not_false_match():
    # "2026/06/0" のような部分一致で誤検知しないこと（startswithの境界）
    history = [{"date": "2026/06/08 09:01"}]
    assert already_posted_today(history, "2026/06/0") is True  # 前方一致仕様
    assert already_posted_today(history, "2026/06/09") is False
