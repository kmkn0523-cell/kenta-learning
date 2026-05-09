# skin_instagram_auto_post.py
# skinアカウント用のInstagram自動投稿スクリプト
# 使い方: python3 skin/skin_instagram_auto_post.py

import os          # 環境変数を読み込む道具
import sys         # 失敗時にGitHub Actionsを赤くする道具
import json        # JSONファイルを扱う道具
import time        # 少し待つための道具
import requests    # インターネットにリクエストを送る道具
from datetime import datetime   # 今の日時を取得する道具
from dotenv import load_dotenv  # .envファイルからAPIキーを読み込む道具

# .envファイルを読み込む（APIキーを安全に管理するため）
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# =============================
# 設定
# =============================
ACCESS_TOKEN = os.getenv("SKIN_INSTAGRAM_ACCESS_TOKEN")  # skinアカウントのアクセストークン
USER_ID      = os.getenv("SKIN_INSTAGRAM_USER_ID")        # skinアカウントのユーザーID

# GitHubに保存した画像へのURL（Threads自動投稿と同じ画像を流用）
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/kmkn0523-cell/kenta-learning/main/skin/skin_images"

# ファイルのパス
POSTS_FILE    = os.path.join(os.path.dirname(__file__), "skin_threads_posts.json")      # 投稿データ
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "skin_instagram_progress.json") # 進捗記録

# 投稿のキャプションに使うハッシュタグ
HASHTAGS = "\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善"

# 投稿の末尾に追加するCTA
CTA = "\n\n詳しくはプロフィールリンクのnoteで読めます✍️"


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

def load_threads():
    """skin_threads_posts.json から全テーマデータを読み込む"""
    try:
        with open(POSTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["threads"]
    except FileNotFoundError:
        print("❌ skin_threads_posts.jsonが見つかりません")
        return []
    except json.JSONDecodeError:
        print("❌ skin_threads_posts.jsonの形式が正しくありません")
        return []


# =============================
# Instagram Graph API 投稿処理
# =============================

def create_media_container(image_url, caption):
    """
    Step1: 投稿の「下書き」をAPIサーバーに送る
    Instagram APIは2段階で投稿する仕組み
    """
    url = f"https://graph.facebook.com/v19.0/{USER_ID}/media"
    params = {
        "image_url":    image_url,     # GitHubにホストされた画像のURL
        "caption":      caption,        # 投稿テキスト＋ハッシュタグ
        "access_token": ACCESS_TOKEN,   # 認証キー
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
    Step2: 下書きを実際にInstagramに公開する
    一時的なAPIエラーの場合は30秒待ってリトライ（最大3回）
    """
    url = f"https://graph.facebook.com/v19.0/{USER_ID}/media_publish"
    params = {
        "creation_id":  creation_id,   # Step1で作った下書きのID
        "access_token": ACCESS_TOKEN,   # 認証キー
    }
    for attempt in range(1, 4):
        try:
            response = requests.post(url, params=params, timeout=30)
            data = response.json()

            if "id" in data:
                return data  # 成功

            # is_transient=True（Meta側の一時障害）なら待ってリトライ
            error_info = data.get("error", {})
            if error_info.get("is_transient") and attempt < 3:
                print(f"  ⚠️ 一時的なAPIエラー（試行{attempt}/3）。30秒後にリトライします...")
                time.sleep(30)
            else:
                print(f"❌ 投稿公開失敗（試行{attempt}/3）: {data}")
                return {}

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
    print(f"=== skin Instagram自動投稿開始 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")

    # APIキーの確認
    if not ACCESS_TOKEN or not USER_ID:
        print("❌ SKIN_INSTAGRAM_ACCESS_TOKEN または SKIN_INSTAGRAM_USER_ID が設定されていません")
        print("   .env ファイルか GitHub Secrets を確認してください")
        sys.exit(1)

    # 投稿データを読み込む
    threads = load_threads()
    if not threads:
        print("❌ 投稿データが読み込めませんでした。終了します。")
        sys.exit(1)

    # 前回の進捗を読み込む（全テーマをループ）
    progress      = load_progress()
    current_index = progress["next_index"] % len(threads)
    thread        = threads[current_index]
    theme_id      = thread["id"]
    theme_name    = thread["theme"]

    # キャプションを組み立てる（フックテキスト + CTA + ハッシュタグ）
    hook_text = thread["posts"][0]                # 1投稿目（フック）をキャプションに使う
    caption   = hook_text + CTA + HASHTAGS

    # 画像URLを組み立てる（Threads自動投稿と同じ.jpg形式）
    image_filename = f"theme{theme_id:02d}.jpg"
    image_url      = f"{GITHUB_RAW_BASE}/{image_filename}"

    print(f"📌 テーマ: {theme_name}（index={current_index}）")
    print(f"🖼️  画像URL: {image_url}")
    print(f"📝 キャプション（先頭100文字）: {caption[:100]}...")

    # Step1: メディアコンテナを作成
    print("📤 Step1: メディアコンテナ作成中...")
    container_result = create_media_container(image_url, caption)

    if "id" not in container_result:
        print(f"❌ メディアコンテナ作成失敗: {container_result}")
        sys.exit(1)

    creation_id = container_result["id"]
    print(f"✅ コンテナID取得: {creation_id}")

    # 画像アップロードの処理待ち
    print("⏳ 30秒待機中（APIの処理時間）...")
    time.sleep(30)

    # Step2: 投稿を公開
    print("📤 Step2: 投稿を公開中...")
    publish_result = publish_media(creation_id)

    if "id" not in publish_result:
        print(f"❌ 投稿公開失敗: {publish_result}")
        sys.exit(1)

    print(f"✅ 投稿成功！投稿ID: {publish_result['id']}")

    # 次回の進捗を保存
    next_index = current_index + 1
    save_progress(next_index)
    next_theme = threads[next_index % len(threads)]["theme"]
    print(f"📊 次回: {next_theme}（index={next_index % len(threads)}）")
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
