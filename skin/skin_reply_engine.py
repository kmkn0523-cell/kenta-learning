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
