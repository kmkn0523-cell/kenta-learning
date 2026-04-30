# threads_auto_post.py
# Threads APIを使って自動投稿するスクリプト
# 使い方: python3 threads_auto_post.py

import os                    # パソコンの環境変数（秘密のキー）を読み込むための道具
import json                  # JSONファイル（データの保存形式）を扱う道具
import time                  # 少し待つための道具（APIの制限対策）
import requests              # インターネットにリクエストを送る道具
from datetime import datetime  # 今の日時を取得する道具
from dotenv import load_dotenv  # .envファイルからAPIキーを読み込む道具

# .envファイルを読み込む（APIキーなどの秘密情報はここに書いてある）
load_dotenv()

# =============================
# 設定（.envファイルから読み込む）
# =============================
ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")  # Threads APIのアクセストークン
USER_ID      = os.getenv("THREADS_USER_ID")        # ThreadsのユーザーID

# ファイルのパス設定
POSTS_FILE = os.path.join(os.path.dirname(__file__), "threads_posts.json")  # 投稿データ
LOG_FILE   = os.path.join(os.path.dirname(__file__), "threads_post_log.json")  # 進捗ログ

# 全投稿の末尾に追加するひとこと（フォロー誘導・押しつけがましくならない程度に）
CTA = "\n\nFollow for one Japanese wisdom, every day."


# =============================
# Threads APIへの投稿処理
# =============================

def create_post_container(text):
    """
    Step 1: 投稿の「下書き」をAPIサーバーに送る
    Threads APIは2段階で投稿する仕組みになっている
    """
    url = f"https://graph.threads.net/v1.0/{USER_ID}/threads"
    params = {
        "media_type": "TEXT",   # テキスト投稿（画像なし）
        "text": text,           # 投稿する文章
        "access_token": ACCESS_TOKEN  # 認証キー
    }
    response = requests.post(url, params=params)
    return response.json()  # APIからの返答をJSONで返す


def publish_post(creation_id):
    """
    Step 2: 下書きを「公開」する
    Step 1で作ったIDを使って、実際に投稿する
    """
    url = f"https://graph.threads.net/v1.0/{USER_ID}/threads_publish"
    params = {
        "creation_id": creation_id,  # Step 1で作った下書きのID
        "access_token": ACCESS_TOKEN  # 認証キー
    }
    response = requests.post(url, params=params)
    return response.json()


def post_to_threads(text):
    """
    テキストをThreadsに投稿する（Step 1 と Step 2 をまとめた処理）
    成功したら True、失敗したら False を返す
    """
    # Step 1: 下書きを作る
    print("  → Step 1: 投稿を準備中...")
    container = create_post_container(text)

    # エラーチェック
    if "id" not in container:
        print(f"  ✗ エラー: 準備に失敗しました → {container}")
        return False

    creation_id = container["id"]

    # APIの制限に引っかからないよう少し待つ（推奨: 30秒）
    print("  → 30秒待機中（APIの制限対策）...")
    time.sleep(30)

    # Step 2: 投稿を公開する
    print("  → Step 2: 投稿を公開中...")
    result = publish_post(creation_id)

    if "id" not in result:
        print(f"  ✗ エラー: 公開に失敗しました → {result}")
        return False

    print(f"  ✓ 投稿成功！ 投稿ID: {result['id']}")
    return True


# =============================
# 投稿データの管理
# =============================

def load_posts():
    """threads_posts.json から30日分の投稿データを読み込む"""
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_log():
    """
    ログファイルを読み込む
    ログには「今日はDay何か」「朝か夜か」が記録されている
    ログがなければ初期状態（Day1の朝）で始める
    """
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # 初回起動時: Day1の朝から始める
    return {
        "current_day": 1,
        "time_of_day": "morning",
        "last_posted": None,
        "total_posts": 0
    }


def save_log(log):
    """ログファイルを保存する"""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def get_current_post():
    """
    今回投稿すべき内容をログと投稿データから取得する
    返り値: (投稿文, Day番号, 朝夜の区分) のセット
    """
    posts = load_posts()
    log = load_log()

    current_day  = log["current_day"]
    time_of_day  = log["time_of_day"]  # "morning" または "evening"

    # 30日分を超えたら終了
    if current_day > 30:
        return None, None, None

    # 該当Dayの投稿文を検索する
    for post in posts["posts"]:
        if post["day"] == current_day:
            text = post[time_of_day]
            return text, current_day, time_of_day

    return None, None, None


def advance_log(current_day, time_of_day):
    """
    投稿成功後にログを次に進める
    朝投稿 → 夜投稿 → 次のDayの朝投稿 という順番で進む
    """
    log = load_log()
    log["last_posted"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log["total_posts"] = log.get("total_posts", 0) + 1

    if time_of_day == "morning":
        # 朝投稿が終わったら次は夜投稿
        log["time_of_day"] = "evening"
    else:
        # 夜投稿が終わったら次のDayの朝投稿へ
        log["current_day"] = current_day + 1
        log["time_of_day"] = "morning"

    save_log(log)


# =============================
# メイン処理
# =============================

def main():
    """
    スクリプトを実行したときに呼ばれる処理
    1. 今日の投稿文を取得
    2. Threadsに投稿
    3. ログを更新
    """
    print("=" * 40)
    print(f"RoninWords 自動投稿スクリプト")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)

    # APIキーの確認
    if not ACCESS_TOKEN or not USER_ID:
        print("✗ エラー: .envファイルにAPIキーが設定されていません")
        print("  THREADS_ACCESS_TOKEN と THREADS_USER_ID を設定してください")
        return

    # 今回の投稿内容を取得
    text, day, time_of_day = get_current_post()

    if text is None:
        print("✓ 30日分の投稿がすべて完了しています！")
        return

    time_label = "朝" if time_of_day == "morning" else "夜"
    print(f"\n投稿内容: Day{day:02d} {time_label}投稿")
    print("-" * 40)
    print(text[:100] + "..." if len(text) > 100 else text)  # 先頭100文字だけ表示
    print("-" * 40)

    # Threadsに投稿する（末尾にCTAを追加）
    success = post_to_threads(text + CTA)

    if success:
        advance_log(day, time_of_day)
        print(f"\n✓ Day{day:02d} {time_label}投稿が完了しました！")
    else:
        print(f"\n✗ Day{day:02d} {time_label}投稿に失敗しました。ログは更新しません。")


# このファイルを直接実行したときだけ main() を呼ぶ
if __name__ == "__main__":
    main()
