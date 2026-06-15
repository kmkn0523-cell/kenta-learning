# test_skin_reply_engine.py
# skin_reply_engine.py の純粋ロジックをテストする（ネットワーク・対話は対象外）
# 実行: pytest skin/tests/test_skin_reply_engine.py

import sys
from pathlib import Path

# skin/ フォルダをimportできる場所に加える（既存テストと同じやり方）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_reply_engine import contains_japanese, count_urls, classify_category
import random as _random  # テスト内で決定的な乱数を作るため
from skin_reply_engine import compose_reply, OPENERS
from skin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES
from skin_reply_engine import is_repliable
from skin_reply_engine import select_targets
from skin_reply_engine import new_state, reset_if_new_day, record_reply

REC_CONFIG = {"recent_window": 3}

def test_new_state_初期値():
    state = new_state("2026-06-15")
    assert state == {"date": "2026-06-15", "count_today": 0, "replied_post_ids": [], "author_counts": {}, "recent_replies": []}

def test_reset_if_new_day_日付が違えば初期化():
    old = {"date": "2026-06-14", "count_today": 5, "replied_post_ids": ["x"], "author_counts": {"u": 1}, "recent_replies": ["a"]}
    assert reset_if_new_day(old, "2026-06-15") == new_state("2026-06-15")

def test_reset_if_new_day_同じ日付はそのまま():
    same = {"date": "2026-06-15", "count_today": 5, "replied_post_ids": ["x"], "author_counts": {"u": 1}, "recent_replies": ["a"]}
    assert reset_if_new_day(same, "2026-06-15") is same

def test_record_reply_カウントと履歴が増える():
    state = new_state("2026-06-15")
    record_reply(state, "p1", "u1", "返信文A", REC_CONFIG)
    assert state["count_today"] == 1
    assert state["replied_post_ids"] == ["p1"]
    assert state["author_counts"] == {"u1": 1}
    assert state["recent_replies"] == ["返信文A"]

def test_record_reply_recent_replyはwindow件に保つ():
    state = new_state("2026-06-15")
    for i in range(5):
        record_reply(state, f"p{i}", f"u{i}", f"返信{i}", REC_CONFIG)
    assert state["recent_replies"] == ["返信2", "返信3", "返信4"]  # 直近3件だけ残る

# 選別系テストで共有するヘルパー（参照より前に定義する）
CONFIG = {"max_per_author_per_day": 1, "min_post_length": 15, "max_urls": 1}

def _fresh_state():
    return {"date": "2026-06-15", "count_today": 0, "replied_post_ids": [], "author_counts": {}, "recent_replies": []}

def _post(**kw):
    base = {"id": "p1", "text": "腸活を始めて肌が変わってきた気がします", "author": "someone", "timestamp": "2026-06-15T00:00:00+0000"}
    base.update(kw)
    return base

SELECT_CONFIG = {"max_per_author_per_day": 1, "min_post_length": 15, "max_urls": 1, "daily_cap": 25, "per_run": 2}

def test_select_targets_新しい順にper_run件まで返す():
    rng = _random.Random(0)
    posts = [
        _post(id="a", author="u1", timestamp="2026-06-15T01:00:00+0000"),
        _post(id="b", author="u2", timestamp="2026-06-15T03:00:00+0000"),
        _post(id="c", author="u3", timestamp="2026-06-15T02:00:00+0000"),
    ]
    result = select_targets(posts, "skin_reset_jp", _fresh_state(), SELECT_CONFIG, rng)
    assert [p["id"] for p in result] == ["b", "c"]  # 新しい順に2件

def test_select_targets_重複IDは1件に():
    rng = _random.Random(0)
    posts = [_post(id="a", author="u1"), _post(id="a", author="u1")]
    result = select_targets(posts, "skin_reset_jp", _fresh_state(), SELECT_CONFIG, rng)
    assert len(result) == 1

def test_select_targets_日次残量で頭打ち():
    rng = _random.Random(0)
    state = _fresh_state()
    state["count_today"] = 24  # 残り1件（daily_cap=25）
    posts = [_post(id="a", author="u1"), _post(id="b", author="u2")]
    result = select_targets(posts, "skin_reset_jp", state, SELECT_CONFIG, rng)
    assert len(result) == 1

def test_is_repliable_通常はTrue():
    assert is_repliable(_post(), "skin_reset_jp", _fresh_state(), CONFIG) is True

def test_is_repliable_自分の投稿はFalse():
    assert is_repliable(_post(author="skin_reset_jp"), "skin_reset_jp", _fresh_state(), CONFIG) is False

def test_is_repliable_返信済みはFalse():
    state = _fresh_state()
    state["replied_post_ids"].append("p1")
    assert is_repliable(_post(), "skin_reset_jp", state, CONFIG) is False

def test_is_repliable_同一著者が上限到達はFalse():
    state = _fresh_state()
    state["author_counts"]["someone"] = 1
    assert is_repliable(_post(), "skin_reset_jp", state, CONFIG) is False

def test_is_repliable_短すぎる投稿はFalse():
    assert is_repliable(_post(text="短い"), "skin_reset_jp", _fresh_state(), CONFIG) is False

def test_is_repliable_日本語なしはFalse():
    assert is_repliable(_post(text="this is an english only post about skin"), "skin_reset_jp", _fresh_state(), CONFIG) is False

def test_is_repliable_URL過多はFalse():
    assert is_repliable(_post(text="腸活いいよ https://a.com https://b.com 見て"), "skin_reset_jp", _fresh_state(), CONFIG) is False

def test_is_repliable_著者不明はFalse():
    assert is_repliable(_post(author=None), "skin_reset_jp", _fresh_state(), CONFIG) is False


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
    assert reply == combos[-1]  # 残った唯一の未使用が選ばれる


def test_classify_category_腸活文は1():
    assert classify_category("腸活を始めて発酵食品を毎日食べてる") == "1"

def test_classify_category_ニキビ文は4():
    assert classify_category("繰り返すニキビと肌荒れがつらい") == "4"

def test_classify_category_無該当はNone():
    assert classify_category("今日はいい天気で散歩しました") is None


def test_contains_japanese_日本語ありはTrue():
    assert contains_japanese("腸活を始めた") is True

def test_contains_japanese_英数字だけはFalse():
    assert contains_japanese("hello 123") is False

def test_count_urls_リンク2本を数える():
    assert count_urls("見てね http://a.com と https://b.com") == 2

def test_count_urls_リンク無しは0():
    assert count_urls("リンクなしの投稿") == 0
