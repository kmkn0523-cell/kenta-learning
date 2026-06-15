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


# テンプレ本文の前に付ける短い枕詞。先頭の "" は「枕詞なし」。
# 本文×枕詞の組み合わせで母数を増やし、固定文の連投（スパム署名）を避ける。
OPENERS = ["", "わかります。", "それ大事ですよね。", "なるほどです。", "共感します。"]


def compose_reply(category_key, recent_replies, rng):
    """カテゴリに合うテンプレ本文に枕詞を合成して1件の返信文を返す。
    recent_replies（直近で送った合成文）に入っている文は避ける。
    全部使い切っていたら重複を許して選ぶ。rng は random.Random（テストで固定するため）。"""
    pool = COMMENT_TEMPLATES[category_key]["comments"] if category_key else GENERIC_TEMPLATES
    combos = [opener + body for body in pool for opener in OPENERS]
    fresh = [combo for combo in combos if combo not in recent_replies]
    return rng.choice(fresh) if fresh else rng.choice(combos)


def is_repliable(post, my_username, state, config):
    """この投稿に返信して良いかを判定する（除外フィルタ）。"""
    if post.get("author") == my_username:  # 自分の投稿には返信しない
        return False
    if post.get("id") in state["replied_post_ids"]:  # 既に返信済み
        return False
    if state["author_counts"].get(post.get("author"), 0) >= config["max_per_author_per_day"]:  # 同一著者の上限
        return False
    text = post.get("text") or ""
    if len(text) < config["min_post_length"]:  # 短すぎる投稿は中身が薄い
        return False
    if not contains_japanese(text):  # 日本語以外（ターゲット外）
        return False
    if count_urls(text) > config["max_urls"]:  # 宣伝色が強い投稿
        return False
    return True


def select_targets(posts, my_username, state, config, rng):
    """検索結果から、今回返信する投稿を選ぶ。
    フィルタ通過 → 重複ID除去 → 新しい順 → （per_run と 日次残量）で頭打ち。"""
    candidates = [p for p in posts if is_repliable(p, my_username, state, config)]
    seen_ids = set()
    unique = []
    for post in candidates:
        if post["id"] in seen_ids:  # 複数キーワードで同じ投稿が来ることがある
            continue
        seen_ids.add(post["id"])
        unique.append(post)
    unique.sort(key=lambda p: p.get("timestamp", ""), reverse=True)  # 新しい順（早押し優先）
    remaining_today = config["daily_cap"] - state["count_today"]  # 今日あと何件送れるか
    limit = max(0, min(config["per_run"], remaining_today))
    return unique[:limit]


def new_state(today):
    """その日の空っぽの状態を作る"""
    return {"date": today, "count_today": 0, "replied_post_ids": [], "author_counts": {}, "recent_replies": []}


def reset_if_new_day(state, today):
    """日付が変わっていたら状態を初期化して返す。同じ日ならそのまま返す。"""
    if state.get("date") != today:
        return new_state(today)
    return state


def record_reply(state, post_id, author, reply_text, config):
    """1件返信したことを状態に記録する（重複防止・著者上限・連投禁止の材料）。"""
    state["replied_post_ids"].append(post_id)
    state["author_counts"][author] = state["author_counts"].get(author, 0) + 1
    state["count_today"] += 1
    state["recent_replies"].append(reply_text)
    state["recent_replies"] = state["recent_replies"][-config["recent_window"]:]  # 直近だけ保持
    return state
