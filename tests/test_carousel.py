# tests/test_carousel.py
# カルーセル生成・投稿スクリプトのテスト

import json
import os
import pytest


def test_carousel_content_json_structure():
    """carousel_content.json の形式が正しいことを確認する"""
    json_path = os.path.join(os.path.dirname(__file__), '..', 'skin', 'carousel_content.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert 'themes' in data
    assert len(data['themes']) == 20  # 20テーマあること

    for theme in data['themes']:
        assert 'id' in theme
        assert 'caption' in theme
        assert 'slides' in theme
        # slide_count キーがあればそれと一致、無ければ最低5枚以上を期待
        # （v2でcover+hook+point×N+ctaの8枚構成に拡張）
        expected = theme.get('slide_count', len(theme['slides']))
        assert len(theme['slides']) == expected
        assert theme['slides'][0]['type'] == 'cover'  # 1枚目はカバー
        assert theme['slides'][-1]['type'] == 'cta'   # 最後はCTA


def test_carousel_content_no_empty_fields():
    """各スライドに空のフィールドがないことを確認する"""
    json_path = os.path.join(os.path.dirname(__file__), '..', 'skin', 'carousel_content.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for theme in data['themes']:
        # v2 は build_caption() で動的生成するため theme.caption は未使用
        # v1 互換テーマ（version != "v2"）のときだけ caption の中身を要求する
        if theme.get('version') != 'v2':
            assert theme['caption'].strip() != '', f"theme id={theme.get('id')} の captionが空"
        for slide in theme['slides']:
            assert slide.get('type', '').strip() != ''


def test_build_carousel_image_urls():
    """テーマIDとスライド枚数からカルーセル画像URLが生成されることを確認する（v2: 8枚対応）"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "auto_post",
        os.path.join(os.path.dirname(__file__), '..', 'skin', 'skin_instagram_auto_post.py')
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # 8枚（v2標準）のケース
    urls_8 = mod.build_carousel_image_urls(theme_id=1, slide_count=8)
    assert len(urls_8) == 8
    assert urls_8[0].endswith('theme01_slide1.png')
    assert urls_8[7].endswith('theme01_slide8.png')
    assert all('raw.githubusercontent.com' in url for url in urls_8)

    # 5枚（v1互換）のケースも動作することを確認
    urls_5 = mod.build_carousel_image_urls(theme_id=1, slide_count=5)
    assert len(urls_5) == 5
    assert urls_5[4].endswith('theme01_slide5.png')
