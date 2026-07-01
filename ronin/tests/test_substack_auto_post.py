# test_substack_auto_post.py
# Substackカード自動投稿の「重複諺スキップ」ロジックの純粋関数テスト
# 実行: pytest ronin/tests/test_substack_auto_post.py -v
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # ronin/ をimport可能にする

from substack_auto_post import (
    posted_japanese_set,
    find_next_unposted_day,
    japanese_from_titles,
    build_article_url,
    PUBLICATION_URL,
)


# テスト用の諺データ（day番号 → 諺）。day32が day16 と同じ諺＝データ重複を再現
SAMPLE_PROVERBS = {
    14: {"japanese": "継続は力なり"},
    15: {"japanese": "以心伝心"},
    16: {"japanese": "千里の道も一歩から"},
    32: {"japanese": "千里の道も一歩から"},  # day16 と重複
    33: {"japanese": "継続は力なり"},        # day14 と重複
    34: {"japanese": "塵も積もれば山となる"},  # 未投稿のユニーク諺
}


def test_履歴から投稿済み諺を集合で取り出す():
    progress = {
        "history": [
            {"day": 14, "title": "継続は力なり — Consistency is strength."},
            {"day": 16, "title": "千里の道も一歩から — A thousand miles begins with one step."},
        ]
    }
    posted = posted_japanese_set(progress)
    assert posted == {"継続は力なり", "千里の道も一歩から"}


def test_既出諺のdayはスキップして次の未投稿諺を返す():
    # day14と16は投稿済み。next_dayが32（＝16の重複）を指していても
    # 重複2件（32,33）を飛ばしてユニークなday34を返すべき
    progress = {
        "next_day": 32,
        "history": [
            {"day": 14, "title": "継続は力なり — Consistency is strength."},
            {"day": 16, "title": "千里の道も一歩から — A thousand miles begins with one step."},
        ],
    }
    assert find_next_unposted_day(progress, SAMPLE_PROVERBS) == 34


def test_重複でなければnext_dayをそのまま返す():
    progress = {
        "next_day": 15,
        "history": [{"day": 14, "title": "継続は力なり — Consistency is strength."}],
    }
    assert find_next_unposted_day(progress, SAMPLE_PROVERBS) == 15


def test_公開記事タイトルから日本語諺だけ取り出す():
    titles = [
        "千里の道も一歩から — A thousand miles begins with one step.",  # カード（日本語あり）
        "The First Step of a Thousand Miles",                          # deep-dive（英語のみ）→無視
        "塵も積もれば山となる — Dust, piled up, becomes a mountain.",
        "",                                                            # 空→無視
    ]
    assert japanese_from_titles(titles) == {"千里の道も一歩から", "塵も積もれば山となる"}


def test_ライブ公開済みの諺もスキップする():
    # progress.jsonの履歴は空（巻き戻った想定）でも、ライブ公開済みを渡せば重複を防ぐ
    progress = {"next_day": 14, "history": []}
    live_posted = {"継続は力なり", "以心伝心", "千里の道も一歩から"}
    # day14,15,16はライブ公開済み、day32,33も同諺→day34まで飛ぶ
    assert find_next_unposted_day(progress, SAMPLE_PROVERBS, also_posted=live_posted) == 34


def test_投稿できる諺がもう無ければNoneを返す():
    progress = {
        "next_day": 32,
        "history": [
            {"day": 14, "title": "継続は力なり — x"},
            {"day": 16, "title": "千里の道も一歩から — x"},
            {"day": 34, "title": "塵も積もれば山となる — x"},
        ],
    }
    # 32,33は重複、34は投稿済み、それ以降はSAMPLEに無い → None
    assert find_next_unposted_day(progress, SAMPLE_PROVERBS) is None


def test_build_article_url_slugありならURLを組み立てる():
    assert build_article_url("ichi-go-ichi-e") == f"{PUBLICATION_URL}/p/ichi-go-ichi-e"


def test_build_article_url_slugなしはNone():
    assert build_article_url(None) is None
    assert build_article_url("") is None
