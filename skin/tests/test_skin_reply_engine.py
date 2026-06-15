# test_skin_reply_engine.py
# skin_reply_engine.py の純粋ロジックをテストする（ネットワーク・対話は対象外）
# 実行: pytest skin/tests/test_skin_reply_engine.py

import sys
from pathlib import Path

# skin/ フォルダをimportできる場所に加える（既存テストと同じやり方）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_reply_engine import contains_japanese, count_urls, classify_category


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
