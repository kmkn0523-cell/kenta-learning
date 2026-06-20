# test_skin_note_matcher.py
# skin_note_matcher.py（投稿テーマに合う無料note選び）のテスト

import json
import os
import sys

# skinフォルダをimportパスに追加する（テストからモジュールを読み込むため）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from skin_note_matcher import match_note_url, NOTE_KEYWORDS

ROOT = os.path.join(os.path.dirname(__file__), "..")


def load_articles():
    """本番の無料note一覧を読み込む（テストでも実データでマッチを確かめる）"""
    with open(os.path.join(ROOT, "note_promo_articles.json"), encoding="utf-8") as f:
        return json.load(f)["articles"]


def test_sugar_theme_matches_sugar_note():
    # 「砂糖とニキビ」→ 甘いものnote
    url = match_note_url("砂糖とニキビ", "", load_articles())
    assert url == "https://note.com/neima/n/n4d52787c48d6"


def test_sleep_theme_matches_sleep_note():
    # 「睡眠と肌」→ 睡眠note
    url = match_note_url("睡眠と肌", "", load_articles())
    assert url == "https://note.com/neima/n/n668abed2d2a7"


def test_dairy_theme_matches_dairy_note():
    # 「乳製品と肌」→ 乳製品note（ヨーグルトnoteに誤爆しない）
    url = match_note_url("乳製品と肌", "", load_articles())
    assert url == "https://note.com/neima/n/nd6c4a831644b"


def test_gut_start_theme_matches_gut_note():
    # 「腸活の始め方」→ 腸活3ステップnote
    url = match_note_url("腸活の始め方", "", load_articles())
    assert url == "https://note.com/neima/n/n688396a1a5b9"


def test_vitamin_d_theme_matches_vitamin_d_note():
    # 「ビタミンDと肌」→ ビタミンDnote（ビタミンB/Cに誤爆しない）
    url = match_note_url("ビタミンDと肌", "", load_articles())
    assert url == "https://note.com/neima/n/n59efb37557b5"


def test_match_from_body_text_when_theme_generic():
    # テーマ名が曖昧でも本文から拾う（「問いかけ型」→本文の「甘いもの」で砂糖note）
    url = match_note_url("問いかけ型", "甘いものをやめて2週間、ニキビが減った", load_articles())
    assert url == "https://note.com/neima/n/n4d52787c48d6"


def test_no_match_returns_empty():
    # 関係ないテーマは空文字（呼び出し側でローテにフォールバックする合図）
    url = match_note_url("宇宙旅行と未来", "全く関係ない話", load_articles())
    assert url == ""


def test_only_returns_url_present_in_articles():
    # NOTE_KEYWORDSにあっても、articlesに無いURLは候補にしない（記事差し替えで壊れない）
    fake_articles = [{"title": "x", "url": "https://note.com/neima/n/n4d52787c48d6"}]
    url = match_note_url("睡眠と肌", "", fake_articles)  # 睡眠noteはfakeに無いので出ない
    assert url == ""


def test_all_keyword_urls_exist_in_articles():
    # NOTE_KEYWORDSのURLが全部、本番の無料note一覧に実在する（タイポ・リンク切れ検出）
    valid = {a["url"] for a in load_articles()}
    for url in NOTE_KEYWORDS:
        assert url in valid, f"NOTE_KEYWORDSのURLがnote一覧に無い: {url}"
