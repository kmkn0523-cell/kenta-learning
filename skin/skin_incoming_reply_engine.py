#!/usr/bin/env python3
# skin_incoming_reply_engine.py
# skin Threads「自分の投稿に来た外部コメント」への自動返信エンジン（GitHub Actions専用・全自動）
#
# skin_reply_engine.py（他人の投稿をkeyword_searchで探して絡む）は Meta の keyword_search 権限が
# 未承認で使えないと判明したため（docs/reply_engine_application_kit.md 参照）、
# 代わりに「自分の投稿に付いた外部コメントへ即レスする」方向で自動化する。
# こちらは自分の投稿・自分のトークンだけで完結するため、keyword_search のような重い権限は不要。
# ★返信生成はテンプレのみ（LLM不使用）。skin_reply_engine.py と同じ枕詞合成・連投禁止の考え方を流用する。

import json     # 設定・状態ファイルを読み書きする道具
import os       # 環境変数（トークン・有効化スイッチ）を読む道具
import random   # テンプレ選択・スリープ揺らぎに使う道具
import time     # 返信の間に人間らしい待機を入れる道具
from datetime import datetime, timezone, timedelta  # 日本時間で「今日」を求める道具
from pathlib import Path  # ファイルの場所を組み立てる道具

import requests  # Threads API にHTTPリクエストを送る道具

# テンプレ選定・合成ロジックは skin_reply_engine.py から再利用する（重複実装を避ける）。
# 直接実行でも pytest 経由でも動くよう2通り import を試す（既存スクリプトと同じ作法）。
try:
    from skin_reply_engine import classify_category, compose_reply
except ImportError:
    from skin.skin_reply_engine import classify_category, compose_reply


# -----------------------------------------------
# ファイルの場所・定数（このスクリプトと同じ skin/ にある前提）
# -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "skin_incoming_reply_engine_config.json"  # 上限設定（読むだけ）
STATE_PATH = BASE_DIR / "skin_incoming_reply_history.json"          # 状態（読み書き・無ければ初回作成）
DAILY_LOG_PATH = BASE_DIR / "skin_daily_log.md"                     # 日次ログ（追記）
JST = timezone(timedelta(hours=9))                                  # 日本時間
API_TIMEOUT = 15  # APIリクエストのタイムアウト時間（秒）


def is_answerable_reply(reply, my_username, state, config):
    """このコメントに返信して良いかを判定する（除外フィルタ）。"""
    if not reply.get("id"):  # IDが取れないコメントは記録できないのでスキップ
        return False
    if reply.get("username") == my_username:  # 自分自身のセルフリプには返信しない（無限ループ防止）
        return False
    if reply.get("id") in state["replied_reply_ids"]:  # 既に返信済み
        return False
    text = reply.get("text") or ""
    if len(text) < config["min_comment_length"]:  # 短すぎる（絵文字だけ等）は対象外
        return False
    return True


def select_targets(replies, my_username, state, config):
    """取得したコメント一覧から、今回返信する分を選ぶ。
    フィルタ通過 → 新しい順 → 本日の残り上限で頭打ち。"""
    candidates = [r for r in replies if is_answerable_reply(r, my_username, state, config)]
    candidates.sort(key=lambda r: r.get("timestamp", ""), reverse=True)  # 新しい順（早押し優先）
    remaining_today = config["daily_cap"] - state["count_today"]
    limit = max(0, min(config["per_run"], remaining_today))
    return candidates[:limit]


def new_state(today):
    """その日の空っぽの状態を作る"""
    return {"date": today, "count_today": 0, "replied_reply_ids": [], "recent_replies": []}


def reset_if_new_day(state, today):
    """日付が変わっていたら状態を初期化して返す。同じ日ならそのまま返す。"""
    if state.get("date") != today:
        return new_state(today)
    return state


def record_reply(state, reply_id, reply_text, config):
    """1件返信したことを状態に記録する（重複防止・連投禁止の材料）。"""
    state["replied_reply_ids"].append(reply_id)
    state["count_today"] += 1
    state["recent_replies"].append(reply_text)
    state["recent_replies"] = state["recent_replies"][-config["recent_window"]:]  # 直近だけ保持
    return state


def load_config():
    """設定ファイルを読み込んで辞書で返す"""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_state(path, today):
    """状態ファイルを読み込む。無ければ空。日付が変わっていれば初期化して返す。"""
    if not os.path.exists(path):
        return new_state(today)
    with open(path, encoding="utf-8") as f:
        state = json.load(f)
    return reset_if_new_day(state, today)


def save_state(path, state):
    """状態ファイルを書き出す"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def fetch_recent_own_posts(user_id, token, window_hours):
    """直近 window_hours 時間以内に自分が投稿した本体の一覧を取得する。
    ここで取れた post_id を使って、その投稿に来たコメントを後で調べる。"""
    url = f"https://graph.threads.net/v1.0/{user_id}/threads"
    params = {
        "fields": "id,timestamp",
        "access_token": token,
        "limit": 50,
    }
    response = requests.get(url, params=params, timeout=API_TIMEOUT)
    response.raise_for_status()
    data = response.json().get("data", [])

    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    recent_ids = []
    for item in data:
        timestamp_text = item.get("timestamp", "")
        try:
            posted_at = datetime.fromisoformat(timestamp_text.replace("Z", "+00:00"))
        except ValueError:
            continue  # 日時が壊れているものはスキップ
        if posted_at >= cutoff:
            recent_ids.append(item["id"])
    return recent_ids


def fetch_replies_for_post(post_id, token):
    """指定した投稿に付いたコメント（返信）一覧を取得する。
    返るキー: id / text / username / timestamp（自分の投稿への外部コメント判定に使う）。"""
    url = f"https://graph.threads.net/v1.0/{post_id}/replies"
    params = {
        "fields": "id,text,username,timestamp,hide_status",
        "access_token": token,
    }
    response = requests.get(url, params=params, timeout=API_TIMEOUT)
    response.raise_for_status()
    data = response.json().get("data", [])

    replies = []
    for item in data:
        # 運営に非表示にされたコメント（スパム等）には返信しない
        if item.get("hide_status") not in (None, "NOT_HIDDEN"):
            continue
        replies.append({
            "id": item.get("id"),
            "text": item.get("text") or "",
            "username": item.get("username"),
            "timestamp": item.get("timestamp") or "",
        })
    return replies


def append_daily_log(count, today):
    """その回の返信件数を日次ログに1行追記する"""
    line = f"\n- {today} 受信コメント返信エンジン: {count}件自動返信"
    with open(DAILY_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)


def main():
    # キルスイッチ：環境変数が "true" でなければ何もしないで終了
    if os.environ.get("SKIN_INCOMING_REPLY_ENABLED") != "true":
        print("SKIN_INCOMING_REPLY_ENABLED が true でないため停止します。")
        return

    token = os.environ["THREADS_ACCESS_TOKEN"]
    user_id = os.environ["THREADS_USER_ID"]
    config = load_config()
    today = datetime.now(JST).strftime("%Y-%m-%d")
    state = load_state(STATE_PATH, today)

    # 本日の上限に達していたら終了（状態だけ保存して日付リセットを永続化）
    if state["count_today"] >= config["daily_cap"]:
        print("本日の上限に到達済み。")
        save_state(STATE_PATH, state)
        return

    try:
        recent_post_ids = fetch_recent_own_posts(user_id, token, config["window_hours"])
    except Exception as error:
        print(f"自分の投稿一覧の取得に失敗しました: {error}")
        return

    all_replies = []
    for post_id in recent_post_ids:
        try:
            all_replies.extend(fetch_replies_for_post(post_id, token))
        except Exception as error:  # 1投稿分の失敗で全体を止めない
            print(f"コメント取得失敗 post={post_id}: {error}")

    targets = select_targets(all_replies, config["my_username"], state, config)
    if not targets:
        print("返信対象のコメントが見つかりませんでした。")
        save_state(STATE_PATH, state)
        return

    # 返信送信は既存スクリプトを再利用（env必須なので遅延import）
    from skin_threads_action import post_to_threads

    rng = random.Random()
    sent = 0
    for reply in targets:
        category = classify_category(reply["text"])
        response_text = compose_reply(category, state["recent_replies"], rng)
        try:
            post_to_threads(response_text, reply_to_id=reply["id"])
        except Exception as error:  # 1件の失敗で残りを止めない
            print(f"返信失敗 reply={reply['id']}: {error}")
            continue
        record_reply(state, reply["id"], response_text, config)
        save_state(STATE_PATH, state)  # 1件ごとに保存（途中で落ちても二重返信しない）
        sent += 1
        print(f"返信 {sent}/{len(targets)} → @{reply['username']}")
        time.sleep(random.randint(config["min_sleep_seconds"], config["max_sleep_seconds"]))

    append_daily_log(sent, today)
    print(f"完了: {sent} 件返信")


if __name__ == "__main__":
    main()
