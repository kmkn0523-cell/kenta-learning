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


# -----------------------------------------------
# ファイルの場所・定数（このスクリプトと同じ skin/ にある前提）
# -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "skin_reply_engine_config.json"  # キーワード・上限設定（読むだけ）
STATE_PATH = BASE_DIR / "skin_reply_history.json"          # 状態（読み書き・無ければ初回作成）
DAILY_LOG_PATH = BASE_DIR / "skin_daily_log.md"            # 日次ログ（追記）
JST = timezone(timedelta(hours=9))                         # 日本時間


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


def search_recent_posts(keyword, token):
    """keyword_search で直近の公開投稿を取得し、正規化した辞書のリストで返す。
    返るキー: id / text / author / timestamp（Task 0 Step 5 で実機確認済みの形）。"""
    url = "https://graph.threads.net/v1.0/keyword_search"
    params = {
        "q": keyword,
        "search_type": "RECENT",
        "fields": "id,text,username,timestamp",
        "access_token": token,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json().get("data", [])
    posts = []
    for item in data:
        posts.append({
            "id": item.get("id"),
            "text": item.get("text") or "",
            "author": item.get("username"),
            "timestamp": item.get("timestamp") or "",
        })
    return posts


def append_daily_log(count, today):
    """その回の返信件数を日次ログに1行追記する"""
    line = f"\n- {today} リプライ・エンジン: {count}件自動返信"
    with open(DAILY_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)


def main():
    # キルスイッチ：環境変数が "true" でなければ何もしないで終了
    if os.environ.get("SKIN_REPLY_ENGINE_ENABLED") != "true":
        print("SKIN_REPLY_ENGINE_ENABLED が true でないため停止します。")
        return

    token = os.environ["THREADS_ACCESS_TOKEN"]  # 返信に使うアクセストークン
    config = load_config()
    today = datetime.now(JST).strftime("%Y-%m-%d")
    state = load_state(STATE_PATH, today)

    # 本日の上限に達していたら終了（状態だけ保存して日付リセットを永続化）
    if state["count_today"] >= config["daily_cap"]:
        print("本日の上限に到達済み。")
        save_state(STATE_PATH, state)
        return

    # キーワードをシャッフルして検索（毎回同じ並びにしない）
    keywords = config["keywords"][:]
    random.shuffle(keywords)
    posts = []
    for keyword in keywords:
        try:
            posts.extend(search_recent_posts(keyword, token))
        except Exception as error:  # 1キーワードの失敗で全体を止めない
            print(f"検索失敗 keyword={keyword}: {error}")
        if len(posts) >= config["per_run"] * 5:  # 十分集まったら早めに切り上げる
            break

    rng = random.Random()
    targets = select_targets(posts, config["my_username"], state, config, rng)
    if not targets:
        print("返信対象が見つかりませんでした。")
        save_state(STATE_PATH, state)
        return

    # 返信送信は既存スクリプトを再利用（env必須なので遅延import）
    from skin_threads_action import post_to_threads

    sent = 0
    for post in targets:
        category = classify_category(post["text"])
        reply = compose_reply(category, state["recent_replies"], rng)
        try:
            post_to_threads(reply, reply_to_id=post["id"])
        except Exception as error:  # 1件の失敗で残りを止めない
            print(f"返信失敗 post={post['id']}: {error}")
            continue
        record_reply(state, post["id"], post["author"], reply, config)
        save_state(STATE_PATH, state)  # 1件ごとに保存（途中で落ちても二重返信しない）
        sent += 1
        print(f"返信 {sent}/{len(targets)} → @{post['author']}")
        time.sleep(random.randint(config["min_sleep_seconds"], config["max_sleep_seconds"]))

    append_daily_log(sent, today)
    print(f"完了: {sent} 件返信")


if __name__ == "__main__":
    main()
