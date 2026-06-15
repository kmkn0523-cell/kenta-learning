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

CONFIG = {"max_per_author_per_day": 1, "min_post_length": 15, "max_urls": 1}

def _fresh_state():
    return {"date": "2026-06-15", "count_today": 0, "replied_post_ids": [], "author_counts": {}, "recent_replies": []}

def _post(**kw):
    base = {"id": "p1", "text": "腸活を始めて肌が変わってきた気がします", "author": "someone", "timestamp": "2026-06-15T00:00:00+0000"}
    base.update(kw)
    return base

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
