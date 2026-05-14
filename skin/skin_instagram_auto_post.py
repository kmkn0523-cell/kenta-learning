# skin_instagram_auto_post.py
# skinアカウント用のInstagram自動投稿スクリプト
# 使い方: python3 skin/skin_instagram_auto_post.py

import os          # 環境変数を読み込む道具
import sys         # 失敗時にGitHub Actionsを赤くする道具
import json        # JSONファイルを扱う道具
import time        # 少し待つための道具
import requests    # インターネットにリクエストを送る道具
from datetime import datetime, timezone  # 今の日時とタイムゾーンを扱う道具
from dotenv import load_dotenv           # .envファイルからAPIキーを読み込む道具

# .envファイルを読み込む（APIキーを安全に管理するため）
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# =============================
# 設定
# =============================
ACCESS_TOKEN = os.getenv("SKIN_INSTAGRAM_ACCESS_TOKEN")  # skinアカウントのアクセストークン
USER_ID      = os.getenv("SKIN_INSTAGRAM_USER_ID")        # skinアカウントのユーザーID

# GitHubに保存した画像へのURL
GITHUB_RAW_BASE       = "https://raw.githubusercontent.com/kmkn0523-cell/kenta-learning/main/skin/skin_images"
GITHUB_CAROUSEL_BASE  = "https://raw.githubusercontent.com/kmkn0523-cell/kenta-learning/main/skin/skin_instagram_carousels"
CAROUSEL_CONTENT_FILE = os.path.join(os.path.dirname(__file__), "carousel_content.json")
SLIDES_PER_CAROUSEL   = 5  # 1投稿あたりのスライド枚数

# ファイルのパス
POSTS_FILE    = os.path.join(os.path.dirname(__file__), "skin_threads_posts.json")      # 投稿データ（旧）
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
# カルーセルコンテンツの読み込み
# =============================

def load_carousel_content():
    """carousel_content.json からカルーセルテーマ定義を読み込む"""
    try:
        with open(CAROUSEL_CONTENT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['themes']
    except FileNotFoundError:
        print("❌ carousel_content.json が見つかりません")
        return []
    except json.JSONDecodeError:
        print("❌ carousel_content.json の形式が正しくありません")
        return []


def build_carousel_image_urls(theme_id: int) -> list:
    """テーマIDからカルーセル画像のURL一覧を作る（5枚分）"""
    return [
        f"{GITHUB_CAROUSEL_BASE}/theme{theme_id:02d}_slide{i}.png"
        for i in range(1, SLIDES_PER_CAROUSEL + 1)
    ]


# =============================
# カルーセル投稿API処理
# =============================

def create_child_container(image_url: str) -> str:
    """
    カルーセルの子コンテナを作る（1枚ずつ登録する）
    カルーセルは: 子コンテナ×N枚 → カルーセルコンテナ → 公開 の順で処理する
    """
    url    = f"https://graph.facebook.com/v19.0/{USER_ID}/media"
    params = {
        "image_url":        image_url,
        "is_carousel_item": "true",
        "access_token":     ACCESS_TOKEN,
    }
    try:
        response = requests.post(url, params=params, timeout=30)
        data     = response.json()
        if "id" in data:
            return data["id"]
        print(f"❌ 子コンテナ作成失敗: {data}")
        return ""
    except Exception as e:
        print(f"❌ 子コンテナ作成エラー: {e}")
        return ""


def create_carousel_container(child_ids: list, caption: str) -> str:
    """カルーセルコンテナを作る（子コンテナIDをまとめて渡す）"""
    url    = f"https://graph.facebook.com/v19.0/{USER_ID}/media"
    params = {
        "media_type":   "CAROUSEL",
        "children":     ",".join(child_ids),
        "caption":      caption,
        "access_token": ACCESS_TOKEN,
    }
    try:
        response = requests.post(url, params=params, timeout=30)
        data     = response.json()
        if "id" in data:
            return data["id"]
        print(f"❌ カルーセルコンテナ作成失敗: {data}")
        return ""
    except Exception as e:
        print(f"❌ カルーセルコンテナ作成エラー: {e}")
        return ""


# =============================
# 投稿データの読み込み（旧・参照用に残す）
# =============================

def load_threads():
    """
    skin_threads_posts.json から全テーマデータを読み込む
    skin_images に .jpg 画像がないテーマ（theme45以降）は除外する
    """
    try:
        with open(POSTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        script_dir = os.path.dirname(__file__)
        images_dir = os.path.join(script_dir, "skin_images")
        result = []
        for thread in data["threads"]:
            image_path = os.path.join(images_dir, f"theme{thread['id']:02d}.jpg")
            if os.path.exists(image_path):  # 画像ファイルがある場合だけ追加
                result.append(thread)
        return result
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


def wait_for_container_ready(creation_id, max_wait=120):
    """
    コンテナの処理完了を確認する（最大120秒まで待つ）
    Instagramは画像を受け取った後、サーバーで処理が完了するまで公開できない
    """
    url = f"https://graph.facebook.com/v19.0/{creation_id}"
    params = {
        "fields":       "status_code",  # 処理状態を取得
        "access_token": ACCESS_TOKEN,
    }
    waited = 0
    while waited < max_wait:
        try:
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            status = data.get("status_code", "UNKNOWN")
            print(f"  ⏳ コンテナ状態: {status}（{waited}秒経過）")
            if status == "FINISHED":
                return True   # 処理完了
            if status == "ERROR":
                print(f"❌ コンテナ処理エラー: {data}")
                return False  # 失敗
        except Exception as e:
            print(f"  ⚠️ 状態確認エラー: {e}")
        time.sleep(10)
        waited += 10
    print(f"❌ {max_wait}秒待っても処理が完了しませんでした")
    return False


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
# ヘルスチェック（重複防止・自動修復）
# =============================

def get_last_post_time():
    """
    Instagram Graph APIで自分の最新投稿の時刻を取得する
    成功したらdatetimeオブジェクト（UTC）、失敗したらNoneを返す
    """
    try:
        # Instagram Graph API: ユーザーのメディア一覧を取得するエンドポイント
        url = f"https://graph.facebook.com/v19.0/{USER_ID}/media"
        params = {
            "fields":       "id,timestamp",  # 投稿IDと投稿時刻だけ取得
            "limit":        1,               # 最新の1件だけ取得
            "access_token": ACCESS_TOKEN
        }
        response = requests.get(url, params=params, timeout=15)
        data = response.json()

        posts = data.get("data", [])
        if not posts:
            print("⚠️ 投稿履歴が見つかりませんでした（初回投稿の可能性）")
            return None

        # タイムスタンプは "2024-01-01T00:00:00+0000" 形式で返ってくる
        timestamp_str = posts[0].get("timestamp", "")
        if not timestamp_str:
            return None

        # Pythonが読めるUTC日時に変換する
        last_post_dt = datetime.fromisoformat(timestamp_str.replace("+0000", "+00:00"))
        return last_post_dt

    except Exception as e:
        print(f"⚠️ 最新投稿時刻の取得に失敗しました: {e}")
        return None


def check_should_skip(skip_minutes=90):
    """
    直近 skip_minutes 分以内に投稿済みなら True を返す（スキップすべき状態）
    APIエラーのときは False を返す（念のため投稿を続行する）

    - 90分以内に投稿あり → スキップ（重複防止）
    - 90分以上たっている → 投稿する（自動修復）
    - API取得失敗 → 投稿する（フェイルセーフ）
    """
    last_post_time = get_last_post_time()
    if last_post_time is None:
        print("⚠️ 最新投稿が確認できませんでした。念のため投稿を続行します。")
        return False

    now_utc = datetime.now(timezone.utc)
    minutes_since_last = (now_utc - last_post_time).total_seconds() / 60

    print(f"📊 ヘルスチェック: 最新投稿から {minutes_since_last:.1f} 分経過")

    if minutes_since_last < skip_minutes:
        print(f"✅ {skip_minutes}分以内に投稿済みのためスキップします（重複防止）")
        return True

    print(f"📢 {skip_minutes}分以上経過しています。投稿を実行します。")
    return False


# =============================
# メイン処理
# =============================

def main():
    print(f"=== skin Instagram自動投稿ヘルスチェック ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")

    # APIキーの確認
    if not ACCESS_TOKEN or not USER_ID:
        print("❌ SKIN_INSTAGRAM_ACCESS_TOKEN または SKIN_INSTAGRAM_USER_ID が設定されていません")
        print("   .env ファイルか GitHub Secrets を確認してください")
        sys.exit(1)

    # 直近90分以内に投稿済みならスキップ（重複防止・自動修復の起点）
    if check_should_skip(skip_minutes=90):
        return  # 投稿済みなので何もしない

    print(f"=== skin Instagram自動投稿開始 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")

    # カルーセルコンテンツを読み込む
    themes = load_carousel_content()
    if not themes:
        print("❌ carousel_content.json が読み込めませんでした。終了します。")
        sys.exit(1)

    # 前回の進捗を読み込む（全テーマをループ）
    progress      = load_progress()
    current_index = progress["next_index"] % len(themes)
    theme         = themes[current_index]
    theme_id      = theme["id"]
    caption       = theme["caption"]

    print(f"📌 テーマ{theme_id:02d}（index={current_index}）")

    # カルーセル画像のURLを5枚分作る
    image_urls = build_carousel_image_urls(theme_id)
    print(f"🖼️  スライド画像: {len(image_urls)}枚")

    # Step1: 各スライドの子コンテナを作る
    print("📤 Step1: 子コンテナを作成中...")
    child_ids = []
    for i, url in enumerate(image_urls, start=1):
        print(f"  スライド{i}: {os.path.basename(url)}")
        child_id = create_child_container(url)
        if not child_id:
            print(f"❌ スライド{i}の子コンテナ作成に失敗しました")
            sys.exit(1)
        child_ids.append(child_id)
        time.sleep(2)  # API制限を避けるため少し待つ

    print(f"✅ 子コンテナ{len(child_ids)}件 作成完了")

    # Step2: カルーセルコンテナを作る
    print("📤 Step2: カルーセルコンテナを作成中...")
    carousel_id = create_carousel_container(child_ids, caption)
    if not carousel_id:
        print("❌ カルーセルコンテナ作成に失敗しました")
        sys.exit(1)
    print(f"✅ カルーセルコンテナID: {carousel_id}")

    # カルーセルの処理完了を待つ
    print("⏳ カルーセル処理完了を確認中...")
    if not wait_for_container_ready(carousel_id):
        print("❌ カルーセルが処理完了しなかったため投稿を中止します")
        sys.exit(1)

    # Step3: 投稿を公開する
    print("📤 Step3: 投稿を公開中...")
    publish_result = publish_media(carousel_id)
    if "id" not in publish_result:
        print(f"❌ 投稿公開失敗: {publish_result}")
        sys.exit(1)

    print(f"✅ カルーセル投稿成功！投稿ID: {publish_result['id']}")

    # 次回の進捗を保存する
    next_index = current_index + 1
    save_progress(next_index)
    print(f"📊 次回テーマ: {themes[next_index % len(themes)]['id']:02d}（index={next_index % len(themes)}）")
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
