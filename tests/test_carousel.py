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
        assert len(theme['slides']) == 5         # 各テーマ5枚あること
        assert theme['slides'][0]['type'] == 'cover'  # 1枚目はカバー
        assert theme['slides'][-1]['type'] == 'cta'   # 最後はCTA


def test_carousel_content_no_empty_fields():
    """各スライドに空のフィールドがないことを確認する"""
    json_path = os.path.join(os.path.dirname(__file__), '..', 'skin', 'carousel_content.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for theme in data['themes']:
        assert theme['caption'].strip() != ''
        for slide in theme['slides']:
            assert slide.get('type', '').strip() != ''


def test_build_carousel_image_urls():
    """テーマIDからカルーセル画像URLが5件生成されることを確認する"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "auto_post",
        os.path.join(os.path.dirname(__file__), '..', 'skin', 'skin_instagram_auto_post.py')
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    urls = mod.build_carousel_image_urls(theme_id=1)
    assert len(urls) == 5
    assert urls[0].endswith('theme01_slide1.png')
    assert urls[4].endswith('theme01_slide5.png')
    assert all('raw.githubusercontent.com' in url for url in urls)
