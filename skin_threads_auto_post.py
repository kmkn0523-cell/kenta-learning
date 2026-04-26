# skin_threads_auto_post.py
# 肌荒れ改善プロジェクト用 Threads投稿管理スクリプト
# 使い方: python3 skin_threads_auto_post.py

import json                    # JSONファイルを扱う道具
import os                      # ファイル操作に使う道具
from datetime import datetime  # 今の日時を取得する道具

# 投稿データと進捗ファイルのパス
POSTS_FILE    = "/home/kenta_kamijyo/skin_x_posts.json"
PROGRESS_FILE = "/home/kenta_kamijyo/skin_threads_progress.json"

# 全投稿に自動でつけるハッシュタグ
HASHTAGS = "\n\n#肌荒れ #大人ニキビ #肌荒れ改善 #ニキビ改善 #内側から綺麗に"


def load_posts():
    """投稿データをJSONから読み込む"""
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_progress():
    """進捗ファイルを読み込む（なければ初期値で始める）"""
    if not os.path.exists(PROGRESS_FILE):
        return {"daily_index": 0, "launch_index": 0, "history": []}
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(progress):
    """進捗をファイルに保存する"""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def show_menu():
    """メニューを表示する"""
    print("\n" + "="*50)
    print("  肌荒れ改善プロジェクト Threads投稿管理")
    print("="*50)
    print("1: 日常投稿（型①〜⑦をローテーション）")
    print("2: note販売用投稿（予告→ローンチ→終了）")
    print("3: 投稿一覧をプレビューする")
    print("4: 進捗をリセットする")
    print("0: 終了")
    print("="*50)
    return input("番号を入力してください: ").strip()


def show_post_and_confirm(post_type, content, progress, mode, index, posts):
    """投稿文を表示して、コピペ後に完了確認する"""
    print(f"\n{'='*50}")
    print(f"📋 投稿文（{post_type}）")
    print(f"{'='*50}")
    print()
    print(content + HASHTAGS)  # 投稿文＋ハッシュタグを表示する
    print()
    print(f"{'='*50}")
    print("👆 上の文をコピーしてThreadsに貼り付けてください")
    print(f"{'='*50}")

    # 投稿できたか確認する
    confirm = input("\nThreadsに投稿できましたか？(y/n): ").strip().lower()

    if confirm == "y":
        # 進捗を更新する
        now = datetime.now().strftime("%Y/%m/%d %H:%M")

        if mode == "daily":
            daily_posts = posts["daily_posts"]
            progress["daily_index"] = (index + 1) % len(daily_posts)
            next_post = daily_posts[progress["daily_index"]]
            print(f"\n✅ 記録しました！次回は「{next_post['type']}」の投稿です")

        elif mode == "launch":
            launch_posts = posts["launch_posts"]
            progress["launch_index"] = index + 1
            if index + 1 < len(launch_posts):
                next_post = launch_posts[index + 1]
                print(f"\n✅ 記録しました！次回は「{next_post['type']}」の投稿です")
            else:
                print("\n✅ 販売用投稿がすべて完了しました！お疲れ様でした！")

        # 履歴に記録する
        if "history" not in progress:
            progress["history"] = []
        progress["history"].append({
            "date": now,
            "type": post_type,
            "mode": mode
        })

        save_progress(progress)
    else:
        print("\n⏭ スキップしました。次回また表示されます")


def daily_post(posts, progress):
    """日常投稿（型①〜⑦）を表示する"""
    daily_posts = posts["daily_posts"]
    index = progress.get("daily_index", 0) % len(daily_posts)
    post  = daily_posts[index]

    show_post_and_confirm(
        post_type=post["type"],
        content=post["content"],
        progress=progress,
        mode="daily",
        index=index,
        posts=posts
    )


def launch_post(posts, progress):
    """note販売用投稿を表示する"""
    launch_posts = posts["launch_posts"]
    index = progress.get("launch_index", 0)

    if index >= len(launch_posts):
        print("\n✅ 販売用投稿はすべて完了しています！")
        return

    post = launch_posts[index]

    show_post_and_confirm(
        post_type=post["type"],
        content=post["content"],
        progress=progress,
        mode="launch",
        index=index,
        posts=posts
    )


def preview_posts(posts, progress):
    """投稿一覧をプレビューする"""
    daily_posts  = posts["daily_posts"]
    launch_posts = posts["launch_posts"]
    daily_index  = progress.get("daily_index", 0) % len(daily_posts)
    launch_index = progress.get("launch_index", 0)

    print("\n📋 日常投稿一覧（型①〜⑦）:")
    for i, post in enumerate(daily_posts):
        marker = " ← 次の投稿" if i == daily_index else ""
        print(f"  [{i+1}] {post['type']}{marker}")

    print("\n📢 note販売用投稿一覧:")
    for i, post in enumerate(launch_posts):
        if i < launch_index:
            status = "✅ 投稿済み"
        elif i == launch_index:
            status = "← 次の投稿"
        else:
            status = "待機中"
        print(f"  [{i+1}] {post['type']} [{status}]")

    # 投稿履歴を表示する
    history = progress.get("history", [])
    if history:
        print(f"\n📅 最近の投稿履歴（直近5件）:")
        for record in history[-5:]:
            print(f"  {record['date']} | {record['type']}")


def reset_progress():
    """進捗をリセットする"""
    confirm = input("進捗をリセットしますか？最初から始まります(y/n): ").strip().lower()
    if confirm == "y":
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        print("✅ 進捗をリセットしました")
    else:
        print("リセットをキャンセルしました")


def main():
    """メイン処理"""
    print("=" * 50)
    print(f"  実行日時: {datetime.now().strftime('%Y/%m/%d %H:%M')}")
    print("=" * 50)

    posts    = load_posts()
    progress = load_progress()

    while True:
        choice = show_menu()

        if choice == "1":
            daily_post(posts, progress)
        elif choice == "2":
            launch_post(posts, progress)
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


if __name__ == "__main__":
    main()
