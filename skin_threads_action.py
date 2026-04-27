# skin_threads_action.py
# GitHub Actions専用の自動投稿スクリプト（対話なし・全自動）
# 使い方: python3 skin_threads_action.py

import json                    # JSONファイルを扱う道具
import os                      # ファイル操作に使う道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime  # 今の日時を取得する道具

# 環境変数からAPIキーを読み込む（GitHub Actionsのsecretsから渡される）
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
THREADS_USER_ID      = os.environ["THREADS_USER_ID"]

# 投稿データと進捗ファイルのパス（相対パスでリポジトリ内に保存）
POSTS_FILE    = "skin_x_posts.json"
PROGRESS_FILE = "skin_threads_progress.json"

# 全投稿に自動でつけるハッシュタグ
HASHTAGS = "\n\n#肌荒れ #大人ニキビ #肌荒れ改善 #ニキビ改善 #内側から綺麗に"


def post_to_threads(text):
    """Threads APIを使って実際に投稿する"""

    # ステップ1: 投稿コンテナ（投稿の下書き）を作成する
    container_url = f"https://graph.threads.net/{THREADS_USER_ID}/threads"
    container_params = {
        "media_type": "TEXT",
        "text": text,
        "access_token": THREADS_ACCESS_TOKEN
    }
    response = requests.post(container_url, params=container_params)
    data = response.json()

    if "id" not in data:
        raise Exception(f"コンテナ作成失敗: {data}")

    creation_id = data["id"]

    # ステップ2: 下書きを実際に公開する
    publish_url = f"https://graph.threads.net/{THREADS_USER_ID}/threads_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": THREADS_ACCESS_TOKEN
    }
    publish_response = requests.post(publish_url, params=publish_params)
    publish_data = publish_response.json()

    if "id" not in publish_data:
        raise Exception(f"公開失敗: {publish_data}")

    return publish_data["id"]  # 投稿IDを返す


def load_posts():
    """投稿データをJSONから読み込む"""
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
    print(f"=== 自動投稿開始: {now} ===")

    posts    = load_posts()
    progress = load_progress()

    # 日常投稿をローテーションで選ぶ
    daily_posts = posts["daily_posts"]
    index = progress.get("daily_index", 0) % len(daily_posts)
    post  = daily_posts[index]

    full_text = post["content"] + HASHTAGS  # 投稿文＋ハッシュタグを合体させる

    print(f"投稿タイプ: {post['type']}")
    print(f"投稿内容:\n{full_text}\n")

    # Threads APIで投稿する
    post_id = post_to_threads(full_text)
    print(f"✅ 投稿成功！（投稿ID: {post_id}）")

    # 次の投稿番号に進める
    progress["daily_index"] = (index + 1) % len(daily_posts)
    next_post = daily_posts[progress["daily_index"]]
    print(f"次回: {next_post['type']}")

    # 履歴に記録する
    if "history" not in progress:
        progress["history"] = []
    progress["history"].append({
        "date": now,
        "type": post["type"],
        "post_id": post_id
    })

    save_progress(progress)  # 進捗を保存する
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
