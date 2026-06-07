# ronin_engagement.py
# @RoninWords用：コメント誘発投稿(engagement post)の在庫を扱う
# ・load_engagement_posts: JSONから読む
# ・pick_engagement_post: engagement_indexで順番に1本選ぶ
# ・validate_engagement_posts: 必須キー/字数/重複をチェック（CIや手動検証用）

import os
import json

# このファイルと同じ ronin/ にある在庫JSON
_DIR = os.path.dirname(os.path.abspath(__file__))
ENGAGEMENT_FILE = os.path.join(_DIR, "ronin_engagement_posts.json")

# 在庫の各エントリに必須のキー
REQUIRED_KEYS = ("id", "archetype", "theme", "text", "seed_comment")

# Threads APIの本文上限
MAX_LEN = 500


def load_engagement_posts():
    """在庫JSONを読み、postsリストを返す（無ければ空リスト）"""
    if not os.path.exists(ENGAGEMENT_FILE):
        return []
    with open(ENGAGEMENT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("posts", [])


def pick_engagement_post(posts, engagement_index):
    """engagement_index(0始まり)で在庫を順番に1本選ぶ（末尾を超えたら先頭へ）"""
    return posts[engagement_index % len(posts)]


def validate_engagement_posts(posts):
    """在庫の不備をエラーメッセージのリストで返す（空＝問題なし）"""
    errors = []
    seen_ids = set()
    seen_texts = set()
    for i, post in enumerate(posts):
        # 必須キーの欠落チェック
        for key in REQUIRED_KEYS:
            if not post.get(key):
                errors.append(f"[{i}] 必須キー欠落: {key}")
        # ID重複チェック
        post_id = post.get("id")
        if post_id in seen_ids:
            errors.append(f"[{i}] IDが重複: {post_id}")
        seen_ids.add(post_id)
        # 本文の重複チェック
        text = post.get("text", "")
        if text in seen_texts:
            errors.append(f"[{i}] 本文が重複: {post_id}")
        seen_texts.add(text)
        # 字数チェック（本文・seed_comment両方）
        if len(text) > MAX_LEN:
            errors.append(f"[{i}] 本文が500字超: {post_id} ({len(text)}字)")
        if len(post.get("seed_comment", "")) > MAX_LEN:
            errors.append(f"[{i}] seed_commentが500字超: {post_id}")
    return errors
