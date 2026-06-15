# skin_reply_engine.py
# skin Threads 自動リプライ・エンジン（GitHub Actions専用・対話なし・全自動）
# keyword_search で見つけたニッチ投稿に、テンプレ返信を自動で送る。
# ★リプライ生成はテンプレのみ（LLM不使用）。固定文連投を避けるため、合成＋連投禁止で署名を薄める。

import json     # 設定・状態ファイルを読み書きする道具
import os       # 環境変数（トークン・有効化スイッチ）を読む道具
import random   # テンプレ選択・スリープ揺らぎ・キーワード順のランダム化に使う道具
import time     # 返信の間に人間らしい待機を入れる道具
from datetime import datetime, timezone, timedelta  # 日本時間で「今日」を求める道具
from pathlib import Path  # ファイルの場所を組み立てる道具

import requests  # Threads API にHTTPリクエストを送る道具

# テンプレ集とキーワード対応表は既存モジュールから再利用する。
# 直接実行でも pytest 経由でも動くよう2通り import を試す（既存スクリプトと同じ作法）。
try:
    from skin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES
    from skin_reply_hunter import KEYWORD_MAP
except ImportError:
    from skin.skin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES
    from skin.skin_reply_hunter import KEYWORD_MAP


def contains_japanese(text):
    """文字列に日本語（ひらがな・カタカナ・漢字）が含まれるかを返す"""
    for character in text:
        if "぀" <= character <= "ヿ":  # ひらがな・カタカナの範囲
            return True
        if "一" <= character <= "鿿":  # よく使う漢字の範囲
            return True
    return False


def count_urls(text):
    """文字列に含まれるURL（http:// か https://）の本数を数える"""
    return text.count("http://") + text.count("https://")


def classify_category(post_text):
    """投稿本文から最も当てはまるテンプレのカテゴリキー（"1"〜"6"）を返す。
    どのキーワードにも当たらなければ None（汎用テンプレを使う合図）。"""
    text = post_text.lower()
    best_key = None
    best_hits = 0
    for key, words in KEYWORD_MAP.items():
        hits = sum(1 for word in words if word.lower() in text)
        if hits > best_hits:
            best_key = key
            best_hits = hits
    return best_key
