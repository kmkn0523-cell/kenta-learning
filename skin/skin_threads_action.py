# skin_threads_action.py
# GitHub Actions専用の自動投稿スクリプト（対話なし・全自動）
# ツリー構造（3本連鎖）でThreadsに投稿する

import json                    # JSONファイルを扱う道具
import os                      # 環境変数を読み込む道具
import time                    # 待機処理に使う道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime  # 今の日時を取得する道具

# 環境変数からAPIキーを読み込む（GitHub Actionsのsecretsから渡される）
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
THREADS_USER_ID      = os.environ["THREADS_USER_ID"]

# 投稿データと進捗ファイルのパス
POSTS_FILE    = "skin_threads_posts.json"      # ツリー用の新しい投稿データ
PROGRESS_FILE = "skin_threads_progress.json"  # 次に投稿する番号を覚えておくファイル

# 3本目の投稿につけるハッシュタグ
HASHTAGS = "\n\n#肌荒れ #大人ニキビ #ニキビ改善 #腸活 #美肌習慣"


def post_to_threads(text, reply_to_id=None):
    """
    Threads APIを使って投稿する（2段階APIコール）
    reply_to_id を渡すとリプライ投稿になる（ツリーの2本目・3本目に使う）
    """

    # ステップ1: 投稿コンテナ（投稿の下書き）を作成する
    container_url = f"https://graph.threads.net/{THREADS_USER_ID}/threads"
    container_params = {
        "media_type": "TEXT",                 # テキスト投稿
        "text": text,                         # 投稿する文章
        "access_token": THREADS_ACCESS_TOKEN  # 認証キー
    }

    # リプライ投稿の場合は「どの投稿への返信か」を追加する
    if reply_to_id:
        container_params["reply_to_id"] = reply_to_id

    response = requests.post(container_url, params=container_params)
    data = response.json()

    if "id" not in data:
        raise Exception(f"コンテナ作成失敗: {data}")

    creation_id = data["id"]  # 下書きのID

    # Threads APIはコンテナ作成後すぐに公開するとエラーになるため30秒待つ
    print("  コンテナ作成完了。30秒待機中...")
    time.sleep(30)

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

    return publish_data["id"]  # 投稿IDを返す（次のリプライ先として使う）


def load_posts():
    """ツリー投稿データをJSONから読み込む"""
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
    print(f"=== skin自動投稿開始: {now} ===")

    # 投稿データと進捗を読み込む
    posts    = load_posts()
    progress = load_progress()

    # ローテーションで今回のセットを選ぶ（14セットを繰り返す）
    threads_list = posts["threads"]
    index        = progress.get("daily_index", 0) % len(threads_list)
    thread_set   = threads_list[index]

    print(f"投稿セット: {index + 1}/{len(threads_list)} ({thread_set['theme']})")

    # 3本の投稿テキストを準備する（3本目にハッシュタグを追加する）
    text_1 = thread_set["posts"][0]
    text_2 = thread_set["posts"][1]
    text_3 = thread_set["posts"][2] + HASHTAGS

    # 本1を投稿する（新規投稿・ツリーの起点）
    print("\n本1を投稿中（フック）...")
    post_id_1 = post_to_threads(text_1)
    print(f"  ✅ 本1投稿成功！（ID: {post_id_1}）")

    # 本2を本1にリプライする（ツリーの2本目）
    print("\n本2を投稿中（本題）...")
    post_id_2 = post_to_threads(text_2, reply_to_id=post_id_1)
    print(f"  ✅ 本2投稿成功！（ID: {post_id_2}）")

    # 本3を本2にリプライする（ツリーの3本目）
    print("\n本3を投稿中（CTA）...")
    post_id_3 = post_to_threads(text_3, reply_to_id=post_id_2)
    print(f"  ✅ 本3投稿成功！（ID: {post_id_3}）")

    # 次の投稿番号に進める（14セットを超えたら0に戻る）
    progress["daily_index"] = (index + 1) % len(threads_list)
    next_thread = threads_list[progress["daily_index"]]
    print(f"\n次回: {next_thread['theme']}")

    # 履歴に記録する
    if "history" not in progress:
        progress["history"] = []
    progress["history"].append({
        "date": now,
        "theme": thread_set["theme"],
        "post_id_1": post_id_1,
        "post_id_2": post_id_2,
        "post_id_3": post_id_3
    })

    save_progress(progress)  # 進捗を保存する
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
