#!/usr/bin/env python3
# skin_repost_engine.py
# skin Threads 過去バズ投稿・自動リポストエンジン（GitHub Actions専用・全自動）
#
# 一定期間が経過し、かつ平均より閲覧数が良かった過去の自分の投稿を
# Threads公式の「リポスト」機能（POST /{post_id}/repost）で再浮上させる。
# 新しい文章を作らず既存投稿をそのまま再共有するだけなので、重複投稿にはならない。
# 1日1件までの控えめな頻度にして、フォロワーのタイムラインを埋め尽くさないようにする。

import json     # 設定・状態・分析データを読み書きする道具
import os       # 環境変数（トークン・有効化スイッチ）を読む道具
from datetime import datetime, timezone, timedelta  # 日本時間・投稿日時の計算に使う道具
from pathlib import Path  # ファイルの場所を組み立てる道具
import re       # Threads APIの日時("+0000")をPython3.9が読める形に直すために使う道具

import requests  # Threads API にHTTPリクエストを送る道具


# -----------------------------------------------
# ファイルの場所・定数（このスクリプトと同じ skin/ にある前提）
# -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
ANALYTICS_PATH = BASE_DIR / "skin_analytics.json"                # 投稿ごとの閲覧数データ（読むだけ）
CONFIG_PATH = BASE_DIR / "skin_repost_engine_config.json"        # 上限・条件設定（読むだけ）
STATE_PATH = BASE_DIR / "skin_repost_history.json"                # 状態（読み書き・無ければ初回作成）
DAILY_LOG_PATH = BASE_DIR / "skin_daily_log.md"                   # 日次ログ（追記）
JST = timezone(timedelta(hours=9))                                # 日本時間
API_TIMEOUT = 15  # APIリクエストのタイムアウト時間（秒）


def parse_iso_datetime(text):
    """Threads APIの日時 "+0000"(コロン無し)を Python3.9 が読める "+00:00" に直して datetime に変換する。"""
    text = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", text)
    return datetime.fromisoformat(text)


def compute_average_views(posts_history):
    """views が記録されている投稿だけを対象に、平均閲覧数を計算する純関数。
    対象が1件も無ければ 0 を返す。"""
    views_list = [p["views"] for p in posts_history if p.get("views")]
    if not views_list:
        return 0
    return sum(views_list) / len(views_list)


def is_repost_candidate(post, now, state, config, average_views):
    """この投稿がリポスト対象になり得るかを判定する（除外フィルタ）。"""
    if not post.get("post_id") or not post.get("posted_at"):  # IDや日時が無い投稿は対象外
        return False
    if post["post_id"] in state["reposted_post_ids"]:  # 既にリポスト済み
        return False
    if state["failed_attempts"].get(post["post_id"], 0) >= config["max_failed_attempts"]:  # 失敗し過ぎた投稿は諦める
        return False
    try:
        posted_at = parse_iso_datetime(post["posted_at"])
    except ValueError:
        return False  # 日時が壊れているものは対象外
    age_days = (now - posted_at).total_seconds() / 86400
    if age_days < config["min_age_days"]:  # 新しすぎる投稿はまだリポストしない（賞味期限を待つ）
        return False
    views = post.get("views") or 0
    if views < average_views * config["min_views_multiplier"]:  # 平均より十分伸びた投稿だけを対象にする
        return False
    return True


def select_repost_candidate(posts_history, now, state, config):
    """今日リポストする1件を選ぶ純関数。
    条件を満たす投稿の中から、閲覧数が最も高いものを返す。無ければ None。"""
    average_views = compute_average_views(posts_history)
    candidates = [p for p in posts_history if is_repost_candidate(p, now, state, config, average_views)]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p["views"], reverse=True)
    return candidates[0]


def new_state():
    """空っぽの状態を作る"""
    return {"reposted_post_ids": [], "failed_attempts": {}, "last_repost_date": None}


def load_state():
    """状態ファイルを読み込む。無ければ空。"""
    if not os.path.exists(STATE_PATH):
        return new_state()
    with open(STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    """状態ファイルを書き出す"""
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def load_config():
    """設定ファイルを読み込んで辞書で返す"""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_analytics():
    """skin_analytics.json を読み込んで posts_history を返す"""
    with open(ANALYTICS_PATH, encoding="utf-8") as f:
        return json.load(f).get("posts_history", [])


def repost_post(post_id, token):
    """Threads APIでリポストを実行する。成功したら (True, レスポンス)、失敗したら (False, エラー内容) を返す。"""
    url = f"https://graph.threads.net/v1.0/{post_id}/repost"
    try:
        response = requests.post(url, params={"access_token": token}, timeout=API_TIMEOUT)
        data = response.json()
        if response.status_code == 200 and "id" in data:
            return True, data
        return False, data
    except requests.exceptions.RequestException as error:
        return False, {"error": str(error)}
    except json.JSONDecodeError:
        return False, {"error": "レスポンスのJSON解析に失敗しました"}


def append_daily_log(post_id, views, today):
    """リポストした投稿を日次ログに1行追記する"""
    line = f"\n- {today} リポスト・エンジン: post_id={post_id}（views={views}）を自動リポスト"
    with open(DAILY_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)


def main():
    # キルスイッチ：環境変数が "true" でなければ何もしないで終了
    if os.environ.get("SKIN_REPOST_ENGINE_ENABLED") != "true":
        print("SKIN_REPOST_ENGINE_ENABLED が true でないため停止します。")
        return

    token = os.environ["THREADS_ACCESS_TOKEN"]
    config = load_config()
    state = load_state()
    now = datetime.now(JST)
    today = now.strftime("%Y-%m-%d")

    # 今日すでにリポスト済みなら終了（1日1件までの上限）
    if state.get("last_repost_date") == today:
        print("本日は既にリポスト済みです。")
        return

    posts_history = load_analytics()
    candidate = select_repost_candidate(posts_history, now, state, config)

    if candidate is None:
        print("リポスト対象の投稿が見つかりませんでした。")
        return

    success, response = repost_post(candidate["post_id"], token)

    if success:
        state["reposted_post_ids"].append(candidate["post_id"])
        state["last_repost_date"] = today
        save_state(state)
        append_daily_log(candidate["post_id"], candidate["views"], today)
        print(f"✅ リポスト成功: post_id={candidate['post_id']} views={candidate['views']}")
    else:
        state["failed_attempts"][candidate["post_id"]] = state["failed_attempts"].get(candidate["post_id"], 0) + 1
        save_state(state)
        print(f"❌ リポスト失敗: post_id={candidate['post_id']} response={response}")


if __name__ == "__main__":
    main()
