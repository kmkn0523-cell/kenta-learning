# X(旧Twitter)自動投稿スクリプト
# 肌荒れ改善プロジェクト用
# 使い方: python3 skin_x_auto_post.py

import tweepy          # XのAPIを使うためのライブラリ
import json            # JSONファイルを読み込むためのライブラリ
import os              # ファイル操作に使うライブラリ
from dotenv import load_dotenv  # .envファイルからAPIキーを読み込むライブラリ
from datetime import datetime   # 現在時刻を取得するライブラリ

# .envファイルからAPIキーを読み込む
load_dotenv()

# XのAPIキーを.envから取得する
API_KEY             = os.getenv("X_API_KEY")
API_SECRET          = os.getenv("X_API_SECRET")
ACCESS_TOKEN        = os.getenv("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")

# 投稿データファイルのパス
POSTS_FILE    = "/home/kenta_kamijyo/skin_x_posts.json"

# どの投稿を次に送るかを記録するファイル
PROGRESS_FILE = "/home/kenta_kamijyo/skin_x_progress.json"


def connect_to_x():
    """XのAPIに接続する関数"""
    # OAuth1.0aという認証方式でXに接続する
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET
    )
    return client


def load_posts():
    """投稿データをJSONファイルから読み込む関数"""
    with open(POSTS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def load_progress():
    """どこまで投稿したか(進捗)を読み込む関数"""
    # 進捗ファイルがなければ最初から始める
    if not os.path.exists(PROGRESS_FILE):
        return {"daily_index": 0, "mode": "daily"}
    with open(PROGRESS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_progress(progress):
    """進捗をファイルに保存する関数"""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as file:
        json.dump(progress, file, ensure_ascii=False, indent=2)


def post_tweet(client, text):
    """ツイートを投稿する関数"""
    try:
        # Xに投稿する
        response = client.create_tweet(text=text)
        print(f"✅ 投稿成功！ ツイートID: {response.data['id']}")
        return True
    except Exception as error:
        # エラーが起きた場合はメッセージを表示する
        print(f"❌ 投稿失敗: {error}")
        return False


def show_menu():
    """メニューを表示する関数"""
    print("\n" + "="*50)
    print("  X自動投稿スクリプト 肌荒れ改善プロジェクト")
    print("="*50)
    print("1: 日常投稿(型①〜型⑦のローテーション)")
    print("2: 販売用投稿(note販売スケジュールに沿って)")
    print("3: 投稿内容をプレビューする(投稿はしない)")
    print("4: 進捗をリセットする")
    print("0: 終了")
    print("="*50)
    return input("番号を入力してください: ").strip()


def daily_post(client, posts, progress):
    """日常投稿(型①〜型⑦)を1件投稿する関数"""
    daily_posts = posts["daily_posts"]

    # 現在のインデックス(何番目か)を取得する
    index = progress.get("daily_index", 0)

    # インデックスが投稿数を超えたら最初に戻る(ループ)
    if index >= len(daily_posts):
        index = 0

    # 投稿する内容を選ぶ
    post = daily_posts[index]

    print(f"\n📝 投稿予定の内容({post['type']}):")
    print("-" * 40)
    print(post["content"])
    print("-" * 40)

    # 本当に投稿するか確認する
    confirm = input("\nこの内容で投稿しますか？(y/n): ").strip().lower()
    if confirm == "y":
        success = post_tweet(client, post["content"])
        if success:
            # 次の投稿番号に進める
            progress["daily_index"] = index + 1
            progress["mode"] = "daily"
            save_progress(progress)
            print(f"次回は「{daily_posts[(index + 1) % len(daily_posts)]['type']}」の投稿です")
    else:
        print("投稿をキャンセルしました")


def launch_post(client, posts, progress):
    """販売用投稿を1件投稿する関数"""
    launch_posts = posts["launch_posts"]

    # 現在のインデックスを取得する
    index = progress.get("launch_index", 0)

    # すべての販売投稿が終わっている場合
    if index >= len(launch_posts):
        print("✅ 販売用投稿はすべて完了しています！")
        return

    # 投稿する内容を選ぶ
    post = launch_posts[index]

    print(f"\n📢 投稿予定の内容({post['type']}):")
    print("-" * 40)
    print(post["content"])
    print("-" * 40)

    # 本当に投稿するか確認する
    confirm = input("\nこの内容で投稿しますか？(y/n): ").strip().lower()
    if confirm == "y":
        success = post_tweet(client, post["content"])
        if success:
            # 次の投稿番号に進める
            progress["launch_index"] = index + 1
            progress["mode"] = "launch"
            save_progress(progress)

            # 次の投稿があれば案内する
            if index + 1 < len(launch_posts):
                next_post = launch_posts[index + 1]
                print(f"次回は「{next_post['type']}」の投稿です")
            else:
                print("✅ 販売用投稿がすべて完了しました！")
    else:
        print("投稿をキャンセルしました")


def preview_posts(posts, progress):
    """投稿内容をプレビューする関数(実際には投稿しない)"""
    print("\n📋 日常投稿一覧:")
    for i, post in enumerate(posts["daily_posts"]):
        current = "← 次の投稿" if i == progress.get("daily_index", 0) % len(posts["daily_posts"]) else ""
        print(f"\n[{i+1}] {post['type']} {current}")
        print(post["content"][:50] + "...")  # 最初の50文字だけ表示する

    print("\n📢 販売用投稿一覧:")
    for i, post in enumerate(posts["launch_posts"]):
        current = "← 次の投稿" if i == progress.get("launch_index", 0) else ""
        status = "✅ 完了" if i < progress.get("launch_index", 0) else current if current else "待機中"
        print(f"\n[{i+1}] {post['type']} [{status}]")
        print(post["content"][:50] + "...")


def reset_progress():
    """進捗をリセットする関数"""
    confirm = input("進捗をリセットしますか？最初から始まります(y/n): ").strip().lower()
    if confirm == "y":
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        print("✅ 進捗をリセットしました")
    else:
        print("リセットをキャンセルしました")


def main():
    """メインの処理をまとめた関数"""
    print(f"\n現在時刻: {datetime.now().strftime('%Y/%m/%d %H:%M')}")

    # Xに接続する
    print("Xに接続中...")
    try:
        client = connect_to_x()
        print("✅ 接続成功！")
    except Exception as error:
        print(f"❌ 接続失敗: {error}")
        return

    # 投稿データと進捗を読み込む
    posts    = load_posts()
    progress = load_progress()

    # メインループ(0を選ぶまで繰り返す)
    while True:
        choice = show_menu()

        if choice == "1":
            daily_post(client, posts, progress)
        elif choice == "2":
            launch_post(client, posts, progress)
        elif choice == "3":
            preview_posts(posts, progress)
        elif choice == "4":
            reset_progress()
            progress = load_progress()
        elif choice == "0":
            print("終了します。お疲れ様でした！")
            break
        else:
            print("0〜4の番号を入力してください")


# このファイルを直接実行したときだけmain()を呼び出す
if __name__ == "__main__":
    main()
