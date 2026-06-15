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
