# skin Instagram 投稿スクリプトの単体テスト
# 使い方: pytest skin/tests/test_skin_instagram_caption.py -v

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skin_instagram_auto_post import (
    select_cta_type,
    build_hashtag_block,
    build_caption,
)


def test_select_cta_type_save():
    """id % 4 == 1 のとき '保存' 型を返す"""
    assert select_cta_type(theme_id=1) == "保存"
    assert select_cta_type(theme_id=5) == "保存"


def test_select_cta_type_comment():
    """id % 4 == 2 のとき 'コメント' 型を返す"""
    assert select_cta_type(theme_id=2) == "コメント"
    assert select_cta_type(theme_id=6) == "コメント"


def test_select_cta_type_note():
    """id % 4 == 3 のとき 'note誘導' 型を返す"""
    assert select_cta_type(theme_id=3) == "note誘導"
    assert select_cta_type(theme_id=7) == "note誘導"


def test_select_cta_type_follow():
    """id % 4 == 0 のとき 'フォロー' 型を返す"""
    assert select_cta_type(theme_id=4) == "フォロー"
    assert select_cta_type(theme_id=8) == "フォロー"


def test_build_hashtag_block():
    """3層のハッシュタグを # 付きで結合する"""
    block = build_hashtag_block(
        fixed=["肌荒れ", "大人ニキビ", "肌改善"],
        theme=["腸活", "発酵食品"],
        size_mix=["美容", "美肌習慣"],
    )
    # # 付き、半角スペース区切り
    assert "#肌荒れ" in block
    assert "#大人ニキビ" in block
    assert "#腸活" in block
    assert "#発酵食品" in block
    assert "#美容" in block
    # 計7個
    assert block.count("#") == 7


def test_build_caption_save_type():
    """保存型(id=1)のキャプションは『保存して』を含み、ハッシュタグも末尾に付く"""
    caption = build_caption(
        theme_id=1,
        hook="化粧水を変えても、肌は治りません。",
        fixed=["肌荒れ"],
        theme=["腸活"],
        size_mix=["美容"],
    )
    assert "化粧水を変えても、肌は治りません。" in caption
    assert "保存して" in caption
    assert "#肌荒れ" in caption
    assert "#腸活" in caption
    assert "#美容" in caption


def test_build_caption_note_type():
    """note誘導型(id=3)のキャプションは『note』を含む"""
    caption = build_caption(
        theme_id=3,
        hook="8年間試した結果、効いた習慣は3つだけ。",
        fixed=["肌荒れ"],
        theme=["腸活"],
        size_mix=["美容"],
    )
    assert "note" in caption
    assert "プロフィール" in caption
