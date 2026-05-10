# skin_threads_auto_post.py
# 肌荒れ改善プロジェクト用 Threads自動投稿スクリプト
# 使い方: python3 skin_threads_auto_post.py

import json                    # JSONファイルを扱う道具
import os                      # ファイル操作に使う道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime  # 今の日時を取得する道具
from dotenv import load_dotenv # .envファイルからAPIキーを読み込む道具

# .envファイルを読み込む（APIキーを安全に管理するため）
load_dotenv()

# Threads APIに必要なキーを.envから読み込む
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_USER_ID      = os.getenv("THREADS_USER_ID")

# 投稿データと進捗ファイルのパス
POSTS_FILE    = "/home/kenta_kamijyo/skin/skin_x_posts.json"  # 注意: このファイルはメニュー形式の手動投稿用。GitHub Actionsは skin_threads_action.py を使用
PROGRESS_FILE = "/home/kenta_kamijyo/skin/skin_threads_progress.json"

# 全投稿に自動でつけるハッシュタグ
HASHTAGS = "\n\n#肌荒れ #大人ニキビ #ニキビ改善 #腸活 #美肌習慣"

# 全投稿の末尾に追加するひとこと（フォロー誘導・押しつけがましくならない程度に）
CTA = "\n\n参考になったら保存しておくと◎\n毎日更新中なのでフォローもぜひ。"


def post_to_threads(text):
    """Threads APIを使って実際に投稿する"""

    # ステップ1: 投稿コンテナ（投稿の下書き）を作成する
    container_url = f"https://graph.threads.net/{THREADS_USER_ID}/threads"
    container_params = {
        "media_type": "TEXT",        # テスト形式の投稿
        "text": text,                # 投稿する文章
        "access_token": THREADS_ACCESS_TOKEN
    }
    container_response = requests.post(container_url, params=container_params)
    container_data = container_response.json()

    # コンテナ作成に失敗した場合はエラーを返す
    if "id" not in container_data:
        return False, f"コンテナ作成失敗: {container_data}"

    creation_id = container_data["id"]  # 下書きのID

    # ステップ2: 下書きを実際に公開する
    publish_url = f"https://graph.threads.net/{THREADS_USER_ID}/threads_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": THREADS_ACCESS_TOKEN
    }
    publish_response = requests.post(publish_url, params=publish_params)
    publish_data = publish_response.json()

    # 公開に失敗した場合はエラーを返す
    if "id" not in publish_data:
        return False, f"公開失敗: {publish_data}"

    return True, publish_data["id"]  # 成功したら投稿IDを返す


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
    print("  肌荒れ改善プロジェクト Threads自動投稿")
    print("="*50)
    print("1: 日常投稿（型①〜⑦をローテーション）")
    print("2: note販売用投稿（予告→ローンチ→終了）")
    print("3: 投稿一覧をプレビューする")
    print("4: 進捗をリセットする")
    print("0: 終了")
    print("="*50)
    return input("番号を入力してください: ").strip()


def post_and_record(post_type, content, progress, mode, index, posts):
    """投稿文を表示してAPIで投稿し、進捗を記録する"""

    # ローンチ投稿はURLが入っているのでハッシュタグを付けない
    if mode == "launch":
        full_text = content
    else:
        full_text = content + CTA + HASHTAGS  # 日常投稿は投稿文＋CTA＋ハッシュタグを合体させる

    # 投稿内容をプレビュー表示する
    print(f"\n{'='*50}")
    print(f"📋 投稿内容（{post_type}）")
    print(f"{'='*50}")
    print()
    print(full_text)
    print()
    print(f"{'='*50}")

    # 投稿前に確認する
    confirm = input("\nこの内容でThreadsに投稿しますか？(y/n): ").strip().lower()

    if confirm != "y":
        print("\n⏭ キャンセルしました")
        return

    # Threads APIで実際に投稿する
    print("\n投稿中...")
    success, result = post_to_threads(full_text)

    if success:
        print(f"✅ 投稿成功！（投稿ID: {result}）")

        # 投稿日時を記録する
        now = datetime.now().strftime("%Y/%m/%d %H:%M")

        if mode == "daily":
            daily_posts = posts["daily_posts"]
            progress["daily_index"] = (index + 1) % len(daily_posts)  # 次の番号に進める
            next_post = daily_posts[progress["daily_index"]]
            print(f"次回は「{next_post['type']}」の投稿です")

        elif mode == "launch":
            launch_posts = posts["launch_posts"]
            progress["launch_index"] = index + 1  # 次の番号に進める
            if index + 1 < len(launch_posts):
                next_post = launch_posts[index + 1]
                print(f"次回は「{next_post['type']}」の投稿です")
            else:
                print("販売用投稿がすべて完了しました！お疲れ様でした！")

        # 履歴に記録する
        if "history" not in progress:
            progress["history"] = []
        progress["history"].append({
            "date": now,
            "type": post_type,
            "mode": mode,
            "post_id": result
        })

        save_progress(progress)  # 進捗をファイルに保存する

    else:
        print(f"❌ 投稿失敗: {result}")


def daily_post(posts, progress):
    """日常投稿（型①〜⑦）を投稿する"""
    daily_posts = posts["daily_posts"]
    index = progress.get("daily_index", 0) % len(daily_posts)
    post  = daily_posts[index]

    post_and_record(
        post_type=post["type"],
        content=post["content"],
        progress=progress,
        mode="daily",
        index=index,
        posts=posts
    )


def launch_post(posts, progress):
    """note販売用投稿を投稿する"""
    launch_posts = posts["launch_posts"]
    index = progress.get("launch_index", 0)

    if index >= len(launch_posts):
        print("\n✅ 販売用投稿はすべて完了しています！")
        return

    post = launch_posts[index]

    post_and_record(
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


def should_use_optimization():
    """Day21 以降かチェック（最適化投稿を使うか判定）"""
    # skin_optimization_index.json から analysis_phase を確認
    try:
        optimization_file = "/home/kenta_kamijyo/skin/skin_optimization_index.json"
        with open(optimization_file, 'r', encoding='utf-8') as f:
            opt_index = json.load(f)

        # analysis_phase が "optimizing" なら True（最適化投稿を使う）
        return opt_index.get('analysis_phase') == 'optimizing'
    except:
        # ファイルがない場合は False（従来の均等投稿）
        return False


def post_sequential():
    """Day21までの均等投稿（従来のロジック）"""
    print("=" * 50)
    print(f"  実行日時: {datetime.now().strftime('%Y/%m/%d %H:%M')}")
    print("=" * 50)

    # APIキーが設定されているか確認する
    if not THREADS_ACCESS_TOKEN or not THREADS_USER_ID:
        print("❌ .envファイルにTHREADS_ACCESS_TOKENとTHREADS_USER_IDを設定してください")
        return

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


def check_is_morning():
    """現在時刻が朝か夜かを判定（簡易版）"""
    # 朝は 6:00〜18:00、夜はそれ以外と判定する
    hour = datetime.now().hour
    # 6時以上18時未満なら朝、それ以外は夜と判定する
    return 6 <= hour < 18


def post_optimized():
    """Day21以降の最適化投稿"""
    print("=" * 50)
    print(f"  実行日時: {datetime.now().strftime('%Y/%m/%d %H:%M')}")
    print("  [最適化投稿モード有効]")
    print("=" * 50)

    # APIキーが設定されているか確認する
    if not THREADS_ACCESS_TOKEN or not THREADS_USER_ID:
        print("❌ .envファイルにTHREADS_ACCESS_TOKENとTHREADS_USER_IDを設定してください")
        return

    # 最適化インデックスを読む
    try:
        optimization_file = "/home/kenta_kamijyo/skin/skin_optimization_index.json"
        with open(optimization_file, 'r', encoding='utf-8') as f:
            opt_index = json.load(f)
    except Exception as e:
        print(f"❌ 最適化インデックスの読み込みに失敗しました: {e}")
        return

    # posts データを読む
    try:
        posts = load_posts()
    except Exception as e:
        print(f"❌ 投稿データの読み込みに失敗しました: {e}")
        return

    # next_post_queue から次の投稿を取得
    queue = opt_index.get('next_post_queue', [])
    if not queue:
        print("Queue is empty. No posts to publish.")
        return

    # キューの最初の投稿を取得
    next_post_info = queue[0]
    day = next_post_info.get('day')

    # posts を辞書化して O(1) で検索できるようにする（Day検索の効率化）
    # 通常は posts_dict を一度だけロード時に作るが、ここでは関数内で必要時に作成
    posts_dict = {p['id']: p for p in posts['daily_posts']}

    # posts_dict.get() で効率的に Day を取得
    post = posts_dict.get(day)
    if not post:
        print(f"❌ Day {day} の投稿データが見つかりません")
        return

    # 朝夜の判定
    # 朝は 6:00〜18:00、夜はそれ以外
    is_morning = check_is_morning()
    post_type = 'morning' if is_morning else 'evening'

    # 投稿内容を取得（朝夜別があれば使う、なければ type で統一）
    post_text = post['content']

    # 最適ハッシュタグセットを取得
    # デフォルトは hashtags_set_A
    hashtag_optimization = opt_index.get('hashtag_optimization', {})
    hashtag_set_key = hashtag_optimization.get(f"day_{day}", "hashtags_set_A")

    # hashtags_set_A 等がない場合は、デフォルトハッシュタグを使う
    hashtags = HASHTAGS

    # 投稿テキスト + CTA + ハッシュタグを結合
    full_text = post_text + CTA + hashtags

    # Threads API で投稿
    try:
        print("\n投稿中...")
        success, result = post_to_threads(full_text)

        if success:
            print(f"✅ 投稿成功！（Day {day} / {post_type} / {hashtag_set_key}）")

            # キューから削除
            opt_index['next_post_queue'].pop(0)

            # 最適化インデックスを更新
            with open(optimization_file, 'w', encoding='utf-8') as f:
                json.dump(opt_index, f, indent=2, ensure_ascii=False)

            # 投稿履歴を記録（sequential と同じフォーマットで統一）
            progress = load_progress()
            now = datetime.now().strftime("%Y/%m/%d %H:%M")
            if "history" not in progress:
                progress["history"] = []
            progress["history"].append({
                "date": now,
                "type": post['type'],
                "mode": "optimized",
                "post_id": result
            })
            save_progress(progress)

        else:
            print(f"❌ 投稿失敗: {result}")

    except Exception as e:
        print(f"❌ 投稿処理エラー: {e}")


def main():
    """メイン処理"""
    # Day21 後に最適化を使用するか判定
    if should_use_optimization():
        # Task 9 で実装（Day21以降の最適化投稿）
        post_optimized()
    else:
        # Day21 までは従来の均等投稿
        post_sequential()


if __name__ == "__main__":
    main()
