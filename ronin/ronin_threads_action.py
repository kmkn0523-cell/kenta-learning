# ronin_threads_action.py
# @RoninWords用 GitHub Actions専用の自動投稿スクリプト（対話なし・全自動）
# 使い方: python3 ronin_threads_action.py
# threads_posts.jsonの投稿を順番にローテーションで投稿する

import json                    # JSONファイルを扱う道具
import os                      # 環境変数を読み込む道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime  # 今の日時を取得する道具

# 環境変数からAPIキーを読み込む（GitHub Actionsのsecretsから渡される）
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
THREADS_USER_ID      = os.environ["THREADS_USER_ID"]

# 投稿データと進捗ファイルのパス
POSTS_FILE    = "threads_posts.json"            # 60投稿（30日×朝夜）が入っているファイル
PROGRESS_FILE = "ronin_threads_progress.json"   # 「次は何番目を投稿するか」を覚えておくファイル

# 全投稿に自動でつける共通ハッシュタグ（英語アカウント向け）
HASHTAGS = "\n\n#JapaneseWisdom #Bushido #Zen #Samurai #Wisdom"


def post_to_threads(text):
    """Threads APIを使って実際に投稿する（2段階APIコール）"""

    # ステップ1: 投稿コンテナ（投稿の下書き）を作成する
    container_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    container_params = {
        "media_type": "TEXT",                 # テキスト投稿（画像なし）
        "text": text,                         # 投稿する文章
        "access_token": THREADS_ACCESS_TOKEN  # 認証キー
    }
    response = requests.post(container_url, params=container_params)
    data = response.json()

    if "id" not in data:
        raise Exception(f"コンテナ作成失敗: {data}")

    creation_id = data["id"]

    # ステップ2: 下書きを実際に公開する
    publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": THREADS_ACCESS_TOKEN
    }
    publish_response = requests.post(publish_url, params=publish_params)
    publish_data = publish_response.json()

    if "id" not in publish_data:
        raise Exception(f"公開失敗: {publish_data}")

    return publish_data["id"]  # 投稿IDを返す


def flatten_posts():
    """
    threads_posts.jsonの「Day×朝夜」構造を、フラットな配列に変換する
    これで0番目→1番目→...と順番に消費しやすくなる
    """
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    flat_posts = []
    for post in data["posts"]:
        # 朝投稿を追加
        flat_posts.append({
            "day": post["day"],
            "type": "morning",
            "content": post["morning"]
        })
        # 夜投稿を追加
        flat_posts.append({
            "day": post["day"],
            "type": "evening",
            "content": post["evening"]
        })
    return flat_posts


def load_progress():
    """進捗ファイルを読み込む（なければ初期値で始める）"""
    if not os.path.exists(PROGRESS_FILE):
        return {"index": 0, "history": []}
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(progress):
    """進捗をファイルに保存する"""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def main():
    """メイン処理（全自動・対話なし）"""
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    print(f"=== Ronin自動投稿開始: {now} ===")

    # 投稿データと進捗を読み込む
    posts    = flatten_posts()
    progress = load_progress()

    # 順番にローテーション（60投稿を超えたら最初に戻る）
    index = progress.get("index", 0) % len(posts)
    post  = posts[index]

    # 本文に共通ハッシュタグを追加
    # Threads APIの上限は500文字なので、超える場合は末尾を「…」でカットする
    content = post["content"]
    if len(content + HASHTAGS) > 500:
        content = content[:500 - len(HASHTAGS) - 1] + "…"
    full_text = content + HASHTAGS

    print(f"投稿番号: {index + 1}/{len(posts)}")
    print(f"投稿タイプ: Day{post['day']:02d} {post['type']}")
    print(f"投稿内容（先頭100文字）:\n{full_text[:100]}...\n")

    # Threads APIで投稿する
    post_id = post_to_threads(full_text)
    print(f"✅ 投稿成功！（投稿ID: {post_id}）")

    # 次の投稿番号に進める（60を超えたら0に戻る）
    progress["index"] = (index + 1) % len(posts)
    next_post = posts[progress["index"]]
    print(f"次回: Day{next_post['day']:02d} {next_post['type']}")

    # 履歴に記録する
    if "history" not in progress:
        progress["history"] = []
    progress["history"].append({
        "date": now,
        "day": post["day"],
        "type": post["type"],
        "post_id": post_id
    })

    save_progress(progress)  # 進捗を保存する
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
