# substack_deep_dive_auto_post.py の公開URL組み立てロジックをテストする
# 実行: pytest ronin/tests/test_substack_deep_dive_auto_post.py -v
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from substack_deep_dive_auto_post import build_article_url, PUBLICATION_URL


def test_build_article_url_slugありならURLを組み立てる():
    assert build_article_url("the-hawk-hides-its-talons") == f"{PUBLICATION_URL}/p/the-hawk-hides-its-talons"


def test_build_article_url_slugなしはNone():
    assert build_article_url(None) is None
    assert build_article_url("") is None
