# ronin_theme_classifier.py のテーマ分類ロジックをテストする
# 実行: pytest ronin/tests/test_ronin_theme_classifier.py -v
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ronin_theme_classifier import KEYWORD_MAP, classify_category


def test_6カテゴリすべてキーワードを持つ():
    assert set(KEYWORD_MAP.keys()) == {"1", "2", "3", "4", "5", "6"}
    for words in KEYWORD_MAP.values():
        assert len(words) >= 3


def test_規律文は1():
    assert classify_category("Discipline and a daily routine build consistency") == "1"


def test_逆境文は2():
    assert classify_category("I failed after a long struggle and setback") == "2"


def test_集中文は3():
    assert classify_category("I can't focus, too much distraction and noise") == "3"


def test_ストイック文は4():
    assert classify_category("Stay calm, this is a stoic mindset lesson") == "4"


def test_熟達文は5():
    assert classify_category("Mastery takes years of practice and craft") == "5"


def test_目的文は6():
    assert classify_category("Still searching for purpose and meaning") == "6"


def test_無該当はNone():
    assert classify_category("The weather is nice and the sky is blue today") is None


def test_同点は番号の若い方():
    # "discipline"（1）と"purpose"（6）が1個ずつ当たる → 若い方の"1"が残る
    assert classify_category("Discipline and purpose both matter") == "1"
