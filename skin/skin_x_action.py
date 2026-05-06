# skin_x_action.py
# GitHub Actions専用 X（旧Twitter）自動投稿スクリプト（対話なし・全自動）
# 使い方: python skin_x_action.py（GitHub Actionsから自動実行される）

import json        # JSONファイルを扱う道具
import os          # 環境変数を読み込む道具
import tweepy      # XのAPIを使うための道具
from datetime import datetime  # 今の日時を取得する道具

# ローカル実行時は .env ファイルからAPIキーを読み込む（GitHub Actionsでは不要）
try:
    from dotenv import load_dotenv
    load_dotenv("/home/kenta_kamijyo/.env")
except ImportError:
    pass

# 環境変数からXのAPIキーを読み込む（GitHub Actionsのsecretsから渡される）
API_KEY             = os.environ["X_API_KEY"]
API_SECRET          = os.environ["X_API_SECRET"]
ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]

# 投稿データと進捗ファイルのパス（GitHub Actionsはskinフォルダで実行する）
POSTS_FILE    = "skin_x_posts.json"
PROGRESS_FILE = "skin_x_progress.json"

# 全投稿の末尾に追加するハッシュタグ
HASHTAGS = "\n\n#肌荒れ #大人ニキビ #ニキビ改善 #腸活 #美肌習慣"


def connect_to_x():
    """XのAPIに接続してクライアントを返す"""
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET
    )
    return client


def load_posts():
    """投稿データをJSONファイルから読み込む"""
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_progress():
    """進捗ファイルを読み込む（なければ初期値で始める）"""
    if not os.path.exists(PROGRESS_FILE):
        return {"daily_index": 0, "history": []}
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(progress):
    """進捗をファイルに保存する"""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def main():
    """メイン処理（全自動・対話なし）"""
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    print(f"=== skin X自動投稿開始: {now} ===")

    # Xに接続する
    print("Xに接続中...")
    client = connect_to_x()
    print("✅ 接続成功！")

    # 投稿データと進捗を読み込む
    posts    = load_posts()
    progress = load_progress()

    daily_posts = posts["daily_posts"]

    # ローテーションで今回の投稿を選ぶ（55種を繰り返す）
    index = progress.get("daily_index", 0) % len(daily_posts)
    post  = daily_posts[index]

    print(f"投稿: {index + 1}/{len(daily_posts)} ({post['type']})")

    # 投稿テキストにハッシュタグを追加する
    full_text = post["content"] + HASHTAGS

    # 280文字を超える場合はハッシュタグなしで投稿する（X の文字数上限）
    if len(full_text) > 280:
        full_text = post["content"]
        print("  ※ 文字数オーバーのためハッシュタグなしで投稿します")

    print(f"\n投稿内容（先頭50文字）: {full_text[:50]}...")

    # Xに投稿する
    response = client.create_tweet(text=full_text)
    tweet_id = response.data["id"]
    print(f"✅ 投稿成功！（ツイートID: {tweet_id}）")

    # 次の投稿番号に進める（55種を超えたら0に戻る）
    progress["daily_index"] = (index + 1) % len(daily_posts)
    next_post = daily_posts[progress["daily_index"]]
    print(f"次回: {next_post['type']}")

    # 履歴に記録する
    if "history" not in progress:
        progress["history"] = []
    progress["history"].append({
        "date": now,
        "type": post["type"],
        "tweet_id": tweet_id
    })

    save_progress(progress)
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
