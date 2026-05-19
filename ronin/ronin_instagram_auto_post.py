# ronin_instagram_auto_post.py
# Instagram Graph APIを使って書道カードを自動投稿するスクリプト
# 使い方: python3 ronin/ronin_instagram_auto_post.py

import os                    # 環境変数（秘密のキー）を読み込む道具
import sys                   # exit code を返す道具（失敗時に GitHub Actions を赤くする）
import json                  # JSONファイルを扱う道具
import time                  # 少し待つための道具
import requests              # インターネットにリクエストを送る道具
from datetime import datetime  # 今の日時を取得する道具
from dotenv import load_dotenv  # .envファイルからAPIキーを読み込む道具

# .envファイルを読み込む
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# =============================
# 設定
# =============================
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")  # Instagramのアクセストークン
USER_ID      = os.getenv("INSTAGRAM_USER_ID")        # InstagramのユーザーID

# GitHubリポジトリの画像URL（raw形式でアクセスできる）
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/kmkn0523-cell/kenta-learning/main/ronin/ronin_images"

# ファイルのパス設定
POSTS_FILE    = os.path.join(os.path.dirname(__file__), "threads_posts.json")   # 投稿データ
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "ronin_instagram_progress.json")  # 進捗記録

# 投稿の末尾に追加するフォロー誘導文
CTA = "\n\nFollow for one Japanese wisdom, every day."


# =============================
# 進捗ファイルの読み書き
# =============================

def load_progress():
    """前回どこまで投稿したかを読み込む（ファイルがなければ最初から）"""
    if not os.path.exists(PROGRESS_FILE):
        return {"next_index": 0}
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"next_index": 0}


def save_progress(next_index):
    """次に投稿するインデックスをファイルに保存する"""
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump({"next_index": next_index}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 進捗保存エラー: {e}")


# =============================
# 投稿データの読み込み
# =============================

def load_posts():
    """
    threads_posts.jsonから全投稿データを読み込み、フラットな配列に変換する
    朝投稿と夜投稿を交互に並べることで120種類の投稿を確保する
    （例: Day1朝→Day1夜→Day2朝→Day2夜→...→Day60夜）
    """
    try:
        with open(POSTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        flat = []
        for post in data["posts"]:
            # 朝投稿を追加
            flat.append({
                "day": post["day"],
                "type": "morning",
                "content": post["morning"],
                "hashtags": post.get("hashtags_set_A", [])
            })
            # 夜投稿を追加（短めのテキスト）
            flat.append({
                "day": post["day"],
                "type": "evening",
                "content": post["evening"],
                "hashtags": post.get("hashtags_set_A", [])
            })
        return flat
    except FileNotFoundError:
        print("❌ threads_posts.jsonが見つかりません")
        return []
    except json.JSONDecodeError:
        print("❌ threads_posts.jsonの形式が正しくありません")
        return []


# =============================
# Instagram Graph API 投稿処理
# =============================

def create_media_container(image_url, caption):
    """
    Step 1: 投稿の「下書き」をAPIサーバーに送る
    Instagram APIは2段階で投稿する仕組み（ThreadsAPIと同じ）
    """
    url = f"https://graph.facebook.com/v19.0/{USER_ID}/media"
    params = {
        "image_url": image_url,    # GitHubにホストされた画像のURL
        "caption": caption,         # 投稿テキスト
        "access_token": ACCESS_TOKEN  # 認証キー
    }
    try:
        response = requests.post(url, params=params, timeout=30)
        return response.json()
    except requests.exceptions.Timeout:
        print("❌ タイムアウト: メディアコンテナ作成に失敗しました")
        return {}
    except Exception as e:
        print(f"❌ メディアコンテナ作成エラー: {e}")
        return {}


def publish_media(creation_id):
    """
    Step 2: 下書きを「公開」する
    Step 1で作ったIDを使って、実際にInstagramに投稿する
    一時的なAPIエラーの場合は30秒待ってリトライする（最大3回）
    """
    url = f"https://graph.facebook.com/v19.0/{USER_ID}/media_publish"
    params = {
        "creation_id": creation_id,  # Step 1で作った下書きのID
        "access_token": ACCESS_TOKEN  # 認証キー
    }
    for attempt in range(1, 4):
        try:
            response = requests.post(url, params=params, timeout=30)
            data = response.json()

            if "id" in data:
                return data  # 成功

            error_info = data.get("error", {})
            error_code = error_info.get("code")

            # レート制限（1日50投稿の上限）: リトライしても意味がないので即終了
            # is_transient=False かつ code=4 がその目印
            if not error_info.get("is_transient", False):
                print(f"❌ 投稿公開失敗（試行{attempt}/3）: {data}")
                if error_code == 4:
                    # 特別なキーを入れてmainに「レート制限」と伝える
                    return {"rate_limited": True}
                return {}

            # is_transient=True（Meta側の一時障害）なら待ってリトライ
            if attempt < 3:
                print(f"  ⚠️ 一時的なAPIエラー（試行{attempt}/3）。30秒後にリトライします...")
                time.sleep(30)

        except requests.exceptions.Timeout:
            print(f"❌ タイムアウト（試行{attempt}/3）: 投稿公開に失敗しました")
            if attempt < 3:
                time.sleep(30)
        except Exception as e:
            print(f"❌ 投稿公開エラー（試行{attempt}/3）: {e}")
            return {}
    return {}


# =============================
# メイン処理
# =============================

def main():
    print(f"=== Instagram自動投稿開始 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")

    # 投稿データを読み込む
    posts = load_posts()
    if not posts:
        print("❌ 投稿データが読み込めませんでした。終了します。")
        return

    # 前回の進捗を読み込む（Day1〜60をループ）
    progress = load_progress()
    current_index = progress["next_index"] % len(posts)
    post = posts[current_index]
    day = post["day"]

    # 投稿テキストを組み立てる（本文 + フォロー誘導 + ハッシュタグ）
    hashtags = " ".join(post.get("hashtags", []))
    caption = post["content"] + CTA + "\n\n" + hashtags

    # 画像URLを組み立てる（投稿のDay番号と画像のDay番号を一致させる）
    # 同じDayの朝・夜投稿は同じ画像を使う（内容が同じ格言を扱っているため）
    image_num = post["day"]
    image_filename = f"day{image_num:02d}.png"
    image_url = f"{GITHUB_RAW_BASE}/{image_filename}"

    time_label = "朝" if post["type"] == "morning" else "夜"
    print(f"📅 Day{day:02d} {time_label}投稿を準備中...")
    print(f"🖼️  画像URL: {image_url}")
    print(f"📝 テキスト（先頭100文字）: {caption[:100]}...")

    # Step 1: メディアコンテナを作成
    print("📤 Step 1: メディアコンテナ作成中...")
    container_result = create_media_container(image_url, caption)

    if "id" not in container_result:
        print(f"❌ メディアコンテナ作成失敗: {container_result}")
        sys.exit(1)  # 失敗を GitHub Actions に伝える

    creation_id = container_result["id"]
    print(f"✅ コンテナID取得: {creation_id}")

    # APIの処理待ち（画像のアップロードには最大30秒かかることがある）
    time.sleep(30)

    # Step 2: 投稿を公開
    print("📤 Step 2: 投稿を公開中...")
    publish_result = publish_media(creation_id)

    if "id" not in publish_result:
        if publish_result.get("rate_limited"):
            # APIブロック（error code 4）でも進捗を1つ進める
            # 同じ投稿を何度もリトライすると「同じ内容が続く」問題が起きるため
            save_progress(current_index + 1)
            next_post = posts[(current_index + 1) % len(posts)]
            next_label = "朝" if next_post["type"] == "morning" else "夜"
            print("⏭️ InstagramのAPIブロックのためスキップ（進捗は次へ進めます）")
            print(f"📊 次回: Day{next_post['day']:02d} {next_label}投稿")
            sys.exit(0)  # 正常終了（GitHub Actionsを赤くしない）
        print(f"❌ 投稿公開失敗: {publish_result}")
        sys.exit(1)  # 失敗を GitHub Actions に伝える

    print(f"✅ 投稿成功！投稿ID: {publish_result['id']}")

    # 次回の進捗を保存
    save_progress(current_index + 1)
    next_post = posts[(current_index + 1) % len(posts)]
    next_label = "朝" if next_post["type"] == "morning" else "夜"
    print(f"📊 次回: Day{next_post['day']:02d} {next_label}投稿")
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
