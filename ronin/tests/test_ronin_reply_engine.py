# test_ronin_reply_engine.py
# ronin_reply_engine.py の純粋ロジックをテストする（ネットワーク・対話は対象外）
# 実行: pytest ronin/tests/test_ronin_reply_engine.py

import sys
from pathlib import Path
import random as _random  # テスト内で決定的な乱数を作るため

# ronin/ フォルダをimportできる場所に加える（既存テストと同じやり方）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ronin_reply_engine import (
    contains_english, count_urls, classify_category,
    compose_reply, OPENERS, is_repliable, select_targets,
    new_state, reset_if_new_day, record_reply,
)
from ronin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES


# ---- contains_english / count_urls ----

def test_contains_english_英語ありはTrue():
    assert contains_english("Discipline builds freedom") is True

def test_contains_english_日本語だけはFalse():
    assert contains_english("規律こそ自由への橋だ") is False

def test_contains_english_短い英語はFalse():
    assert contains_english("ok go") is False  # ASCII英字15文字未満

def test_count_urls_リンク2本を数える():
    assert count_urls("see http://a.com and https://b.com") == 2

def test_count_urls_リンク無しは0():
    assert count_urls("no links here at all") == 0


# ---- classify_category ----

def test_classify_category_規律文は1():
    assert classify_category("Discipline and a daily routine build consistency") == "1"

def test_classify_category_逆境文は2():
    assert classify_category("I failed after a long struggle and setback") == "2"

def test_classify_category_無該当はNone():
    assert classify_category("The weather is nice and the sky is blue today") is None


# ---- compose_reply ----

def _all_combos(pool):
    return [opener + body for body in pool for opener in OPENERS]

def test_compose_reply_カテゴリ指定は該当プールから合成される():
    rng = _random.Random(0)
    reply = compose_reply("1", [], rng)
    assert reply in _all_combos(COMMENT_TEMPLATES["1"]["comments"])

def test_compose_reply_Noneは汎用プールから合成される():
    rng = _random.Random(0)
    reply = compose_reply(None, [], rng)
    assert reply in _all_combos(GENERIC_TEMPLATES)

def test_compose_reply_直近に使った文は避ける():
    rng = _random.Random(1)
    combos = _all_combos(COMMENT_TEMPLATES["1"]["comments"])
    recent = combos[:-1]  # 1つだけ残して全部「使用済み」にする
    reply = compose_reply("1", recent, rng)
    assert reply == combos[-1]


# ---- is_repliable ----

CONFIG = {"max_per_author_per_day": 1, "min_post_length": 20, "max_urls": 1}

def _fresh_state():
    return {"date": "2026-06-16", "count_today": 0, "replied_post_ids": [], "author_counts": {}, "recent_replies": []}

def _post(**kw):
    base = {"id": "p1", "text": "Discipline is the bridge between goals and accomplishment",
            "author": "someone", "timestamp": "2026-06-16T00:00:00+0000"}
    base.update(kw)
    return base

def test_is_repliable_通常はTrue():
    assert is_repliable(_post(), "roninwords", _fresh_state(), CONFIG) is True

def test_is_repliable_自分の投稿はFalse_大小無視():
    assert is_repliable(_post(author="RoninWords"), "roninwords", _fresh_state(), CONFIG) is False

def test_is_repliable_著者名なしはFalse():
    assert is_repliable(_post(author=None), "roninwords", _fresh_state(), CONFIG) is False

def test_is_repliable_返信済みはFalse():
    state = _fresh_state()
    state["replied_post_ids"].append("p1")
    assert is_repliable(_post(), "roninwords", state, CONFIG) is False

def test_is_repliable_同一著者が上限到達はFalse():
    state = _fresh_state()
    state["author_counts"]["someone"] = 1
    assert is_repliable(_post(), "roninwords", state, CONFIG) is False

def test_is_repliable_短すぎる投稿はFalse():
    assert is_repliable(_post(text="too short"), "roninwords", _fresh_state(), CONFIG) is False

def test_is_repliable_英語なしはFalse():
    assert is_repliable(_post(text="これは日本語だけの長い投稿で英語は含まれていません"), "roninwords", _fresh_state(), CONFIG) is False

def test_is_repliable_URL過多はFalse():
    assert is_repliable(_post(text="great discipline https://a.com https://b.com keep going"), "roninwords", _fresh_state(), CONFIG) is False


# ---- select_targets ----

SELECT_CONFIG = {"max_per_author_per_day": 1, "min_post_length": 20, "max_urls": 1, "daily_cap": 25, "per_run": 2}

def test_select_targets_新しい順にper_run件まで返す():
    rng = _random.Random(0)
    posts = [
        _post(id="a", author="u1", timestamp="2026-06-16T01:00:00+0000"),
        _post(id="b", author="u2", timestamp="2026-06-16T03:00:00+0000"),
        _post(id="c", author="u3", timestamp="2026-06-16T02:00:00+0000"),
    ]
    result = select_targets(posts, "roninwords", _fresh_state(), SELECT_CONFIG, rng)
    assert [p["id"] for p in result] == ["b", "c"]

def test_select_targets_重複IDは1件に():
    rng = _random.Random(0)
    posts = [_post(id="a", author="u1"), _post(id="a", author="u1")]
    result = select_targets(posts, "roninwords", _fresh_state(), SELECT_CONFIG, rng)
    assert len(result) == 1

def test_select_targets_日次残量で頭打ち():
    rng = _random.Random(0)
    state = _fresh_state()
    state["count_today"] = 24
    posts = [_post(id="a", author="u1"), _post(id="b", author="u2")]
    result = select_targets(posts, "roninwords", state, SELECT_CONFIG, rng)
    assert len(result) == 1


# ---- 状態管理 ----

REC_CONFIG = {"recent_window": 3}

def test_new_state_初期値():
    assert new_state("2026-06-16") == {"date": "2026-06-16", "count_today": 0, "replied_post_ids": [], "author_counts": {}, "recent_replies": []}

def test_reset_if_new_day_日付が違えば初期化():
    old = {"date": "2026-06-15", "count_today": 5, "replied_post_ids": ["x"], "author_counts": {"u": 1}, "recent_replies": ["a"]}
    assert reset_if_new_day(old, "2026-06-16") == new_state("2026-06-16")

def test_reset_if_new_day_同じ日付はそのまま():
    same = {"date": "2026-06-16", "count_today": 5, "replied_post_ids": ["x"], "author_counts": {"u": 1}, "recent_replies": ["a"]}
    assert reset_if_new_day(same, "2026-06-16") is same

def test_record_reply_カウントと履歴が増える():
    state = new_state("2026-06-16")
    record_reply(state, "p1", "u1", "Reply A", REC_CONFIG)
    assert state["count_today"] == 1
    assert state["replied_post_ids"] == ["p1"]
    assert state["author_counts"] == {"u1": 1}
    assert state["recent_replies"] == ["Reply A"]

def test_record_reply_recent_replyはwindow件に保つ():
    state = new_state("2026-06-16")
    for i in range(5):
        record_reply(state, f"p{i}", f"u{i}", f"Reply{i}", REC_CONFIG)
    assert state["recent_replies"] == ["Reply2", "Reply3", "Reply4"]
