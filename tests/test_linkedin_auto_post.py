# tests/test_linkedin_auto_post.py
# LinkedIn自動投稿スクリプトのテストファイル
# 使い方: pytest tests/test_linkedin_auto_post.py -v

import json
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, '/home/kenta_kamijyo')

# インポート（テスト対象のモジュール）
from linkedin.linkedin_auto_post import load_config, load_threads_posts, post_to_linkedin, select_post_for_linkedin


def test_load_config():
    """linkedin_config.json を読み込めることをテストする"""
    config = load_config()

    # configが辞書であることを確認
    assert isinstance(config, dict), "configは辞書である必要があります"

    # 必要なキーが存在することを確認
    assert "oauth" in config, "oauthキーが存在する必要があります"
    assert "profile" in config, "profileキーが存在する必要があります"
    assert "access_token" in config["oauth"], "oauth.access_tokenが存在する必要があります"
    assert "person_urn" in config["profile"], "profile.person_urnが存在する必要があります"


def test_load_threads_posts():
    """ronin/threads_posts.json を読み込めることをテストする"""
    posts = load_threads_posts()

    # postsがリストであることを確認
    assert isinstance(posts, list), "postsはリストである必要があります"

    # 投稿が存在することを確認
    assert len(posts) > 0, "投稿が1件以上ある必要があります"

    # 最初の投稿に必要なキーが存在することを確認
    first_post = posts[0]
    assert "morning" in first_post, "morningキーが存在する必要があります"
    assert "hashtags_set_A" in first_post, "hashtags_set_Aキーが存在する必要があります"

    # morningとhashtags_set_Aが正しい型であることを確認
    assert isinstance(first_post["morning"], str), "morningは文字列である必要があります"
    assert isinstance(first_post["hashtags_set_A"], list), "hashtags_set_Aはリストである必要があります"


def test_select_post_for_linkedin():
    """select_post_for_linkedin() が正しい形式で値を返すことをテストする"""
    text, hashtags = select_post_for_linkedin()

    # 戻り値が正しい型であることを確認
    assert isinstance(text, str), "textは文字列である必要があります"
    assert isinstance(hashtags, list), "hashtagsはリストである必要があります"

    # textが空でないことを確認
    assert len(text) > 0, "textが空ではない必要があります"

    # hashtagsが空でないことを確認
    assert len(hashtags) > 0, "hashtagsが空ではない必要があります"

    # hashtagsの各要素が文字列であることを確認
    for tag in hashtags:
        assert isinstance(tag, str), "hashtagsの各要素は文字列である必要があります"


if __name__ == "__main__":
    # pytest を使う場合: pytest tests/test_linkedin_auto_post.py -v
    # または pytest を実行
    pass
