# test_skin_incoming_reply_engine.py
# skin_incoming_reply_engine.py の純粋ロジックをテストする（ネットワーク・対話は対象外）
# 実行: pytest skin/tests/test_skin_incoming_reply_engine.py

import sys
from pathlib import Path

# skin/ フォルダをimportできる場所に加える（既存テストと同じやり方）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_incoming_reply_engine import (
    is_answerable_reply,
    select_targets,
    new_state,
    reset_if_new_day,
    record_reply,
)

REC_CONFIG = {"recent_window": 3}


def test_new_state_初期値():
    state = new_state("2026-06-15")
    assert state == {"date": "2026-06-15", "count_today": 0, "replied_reply_ids": [], "recent_replies": []}


def test_reset_if_new_day_日付が違えば初期化():
    old = {"date": "2026-06-14", "count_today": 5, "replied_reply_ids": ["x"], "recent_replies": ["a"]}
    assert reset_if_new_day(old, "2026-06-15") == new_state("2026-06-15")


def test_reset_if_new_day_同じ日付はそのまま():
    same = {"date": "2026-06-15", "count_today": 5, "replied_reply_ids": ["x"], "recent_replies": ["a"]}
    assert reset_if_new_day(same, "2026-06-15") is same


def test_record_reply_カウントと履歴が増える():
    state = new_state("2026-06-15")
    record_reply(state, "r1", "返信文A", REC_CONFIG)
    assert state["count_today"] == 1
    assert state["replied_reply_ids"] == ["r1"]
    assert state["recent_replies"] == ["返信文A"]


def test_record_reply_recent_replyはwindow件に保つ():
    state = new_state("2026-06-15")
    for i in range(5):
        record_reply(state, f"r{i}", f"返信{i}", REC_CONFIG)
    assert state["recent_replies"] == ["返信2", "返信3", "返信4"]  # 直近3件だけ残る


CONFIG = {"min_comment_length": 2}


def _fresh_state():
    return {"date": "2026-06-15", "count_today": 0, "replied_reply_ids": [], "recent_replies": []}


def _reply(**kw):
    base = {"id": "r1", "text": "私も同じ悩みです", "username": "someone", "timestamp": "2026-06-15T00:00:00+0000"}
    base.update(kw)
    return base


def test_is_answerable_reply_自分自身のコメントは除外():
    state = _fresh_state()
    reply = _reply(username="skin_reset_jp")
    assert is_answerable_reply(reply, "skin_reset_jp", state, CONFIG) is False


def test_is_answerable_reply_返信済みは除外():
    state = _fresh_state()
    state["replied_reply_ids"] = ["r1"]
    reply = _reply()
    assert is_answerable_reply(reply, "skin_reset_jp", state, CONFIG) is False


def test_is_answerable_reply_短すぎるコメントは除外():
    state = _fresh_state()
    reply = _reply(text="!")
    assert is_answerable_reply(reply, "skin_reset_jp", state, CONFIG) is False


def test_is_answerable_reply_条件を満たせば対象になる():
    state = _fresh_state()
    reply = _reply()
    assert is_answerable_reply(reply, "skin_reset_jp", state, CONFIG) is True


SELECT_CONFIG = {"min_comment_length": 2, "daily_cap": 25, "per_run": 2}


def test_select_targets_新しい順にper_run件まで返す():
    state = _fresh_state()
    replies = [
        _reply(id="r1", timestamp="2026-06-15T00:00:00+0000"),
        _reply(id="r2", timestamp="2026-06-15T02:00:00+0000"),
        _reply(id="r3", timestamp="2026-06-15T01:00:00+0000"),
    ]
    targets = select_targets(replies, "skin_reset_jp", state, SELECT_CONFIG)
    assert [t["id"] for t in targets] == ["r2", "r3"]  # 新しい順に2件（per_run=2）


def test_select_targets_日次上限の残り分だけ返す():
    state = _fresh_state()
    state["count_today"] = 24  # 残り1件しかない状態
    replies = [_reply(id="r1"), _reply(id="r2")]
    targets = select_targets(replies, "skin_reset_jp", state, SELECT_CONFIG)
    assert len(targets) == 1


def test_select_targets_上限到達済みなら空():
    state = _fresh_state()
    state["count_today"] = 25
    replies = [_reply(id="r1")]
    targets = select_targets(replies, "skin_reset_jp", state, SELECT_CONFIG)
    assert targets == []
