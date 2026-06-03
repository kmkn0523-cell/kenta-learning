# ronin_instagram_auto_post.py
# Instagram Graph APIを使って書道カードを自動投稿するスクリプト
# 使い方: python3 ronin/ronin_instagram_auto_post.py

import os                    # 環境変数（秘密のキー）を読み込む道具
import sys                   # exit code を返す道具（失敗時に GitHub Actions を赤くする）
import json                  # JSONファイルを扱う道具
import time                  # 少し待つための道具
import requests              # インターネットにリクエストを送る道具
from datetime import datetime, timezone  # 今の日時とタイムゾーンを扱う道具
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


def save_progress(next_index, last_posted_at=None):
    """次に投稿するインデックスと投稿時刻をファイルに保存する
    last_posted_at: 投稿した日時（UTC ISO形式）。Noneのときは既存ファイルの値を引き継ぐ
    """
    try:
        existing_last = None
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                existing_last = existing.get("last_posted_at")
            except Exception:
                pass
        data = {
            "next_index": next_index,
            "last_posted_at": last_posted_at if last_posted_at is not None else existing_last,
        }
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 進捗保存エラー: {e}")


# =============================
# 投稿データの読み込み
# =============================

def load_posts():
    """
    threads_posts.jsonから全投稿データを読み込み、Dayごとに1件の配列に変換する
    同じDayのmorningとeveningはどちらも同じ格言テーマなので、
    朝の本文と夜の本文を1つの投稿にまとめる（同じ画像が2回出るのを防ぐ）
    （例: Day1→Day2→...→Day200）
    """
    try:
        with open(POSTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        flat = []
        for post in data["posts"]:
            # 1日分を1件にまとめる（morning本文とevening本文の両方を保持）
            flat.append({
                "day": post["day"],
                "morning": post["morning"],
                "evening": post["evening"],
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
# ヘルスチェック（重複防止）
# =============================

def get_last_post_time():
    """Instagram Graph APIで自分の最新投稿の時刻を取得する（フォールバック用）"""
    try:
        url = f"https://graph.facebook.com/v19.0/{USER_ID}/media"
        params = {
            "fields":       "id,timestamp",
            "limit":        1,
            "access_token": ACCESS_TOKEN,
        }
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        posts = data.get("data", [])
        if not posts:
            return None
        timestamp_str = posts[0].get("timestamp", "")
        if not timestamp_str:
            return None
        return datetime.fromisoformat(timestamp_str.replace("+0000", "+00:00"))
    except Exception as e:
        print(f"⚠️ 最新投稿時刻の取得に失敗しました: {e}")
        return None


def check_should_skip(skip_minutes=90):
    """直近 skip_minutes 分以内に投稿済みなら True を返す（スキップすべき状態）
    ① progress.json の last_posted_at を優先確認（git push 成功時に記録される）
    ② なければ Instagram API で最新投稿時刻を確認（フォールバック）
    """
    progress = load_progress()
    last_posted_at_str = progress.get("last_posted_at")
    if last_posted_at_str:
        try:
            last_dt = datetime.fromisoformat(last_posted_at_str)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            now_utc = datetime.now(timezone.utc)
            minutes_since_last = (now_utc - last_dt).total_seconds() / 60
            print(f"📊 ヘルスチェック（ファイル参照）: 最新投稿から {minutes_since_last:.1f} 分経過")
            if minutes_since_last < skip_minutes:
                print(f"✅ {skip_minutes}分以内に投稿済みのためスキップします（重複防止）")
                return True
            print(f"📢 {skip_minutes}分以上経過しています。投稿を実行します。")
            return False
        except Exception as e:
            print(f"⚠️ last_posted_at のパースに失敗しました: {e}（APIで確認します）")

    last_post_time = get_last_post_time()
    if last_post_time is None:
        print("⚠️ 最新投稿が確認できませんでした。念のため投稿を続行します。")
        return False
    now_utc = datetime.now(timezone.utc)
    minutes_since_last = (now_utc - last_post_time).total_seconds() / 60
    print(f"📊 ヘルスチェック（API参照）: 最新投稿から {minutes_since_last:.1f} 分経過")
    if minutes_since_last < skip_minutes:
        print(f"✅ {skip_minutes}分以内に投稿済みのためスキップします（重複防止）")
        return True
    print(f"📢 {skip_minutes}分以上経過しています。投稿を実行します。")
    return False


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
    print(f"=== Ronin Instagram自動投稿ヘルスチェック ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")

    # APIキーの確認
    if not ACCESS_TOKEN or not USER_ID:
        print("❌ INSTAGRAM_ACCESS_TOKEN または INSTAGRAM_USER_ID が設定されていません")
        sys.exit(1)

    # 直近90分以内に投稿済みならスキップ（重複防止）
    if check_should_skip(skip_minutes=90):
        return

    print(f"=== Ronin Instagram自動投稿開始 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")

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

    # 投稿テキストを組み立てる（朝本文 + 区切り線 + 夜本文 + フォロー誘導 + ハッシュタグ）
    # 同じDayの朝・夜は同じ格言テーマなので、1つの投稿にまとめる
    hashtags = " ".join(post.get("hashtags", []))
    caption = (
        post["morning"]            # 朝の本文（末尾にハッシュタグが入っていることが多い）
        + "\n\n· · ·\n\n"          # 朝と夜を分ける区切り線
        + post["evening"]          # 夜の本文（短い補足）
        + CTA                       # フォロー誘導文
        + "\n\n" + hashtags         # ハッシュタグ
    )

    # 画像URLを組み立てる（投稿のDay番号と画像のDay番号を一致させる）
    image_num = post["day"]
    image_filename = f"day{image_num:02d}.png"
    image_url = f"{GITHUB_RAW_BASE}/{image_filename}"

    print(f"📅 Day{day:02d} 投稿を準備中...")
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

    # 投稿完了時刻を UTC ISO 形式で記録する（重複防止の check_should_skip で使用）
    now_iso = datetime.now(timezone.utc).isoformat()

    if "id" not in publish_result:
        if publish_result.get("rate_limited"):
            # APIブロック（error code 4）でも進捗を1つ進める
            # 同じ投稿を何度もリトライすると「同じ内容が続く」問題が起きるため
            # last_posted_at も記録して、直後の重複実行をスキップさせる
            save_progress(current_index + 1, last_posted_at=now_iso)
            next_post = posts[(current_index + 1) % len(posts)]
            print("⏭️ InstagramのAPIブロックのためスキップ（進捗は次へ進めます）")
            print(f"📊 次回: Day{next_post['day']:02d} 投稿")
            sys.exit(0)  # 正常終了（GitHub Actionsを赤くしない）
        # その他の公開失敗でも進捗を1つ進めて last_posted_at を記録する
        # 進捗を進めないと次回も同じ内容が投稿されてしまうため
        save_progress(current_index + 1, last_posted_at=now_iso)
        next_post = posts[(current_index + 1) % len(posts)]
        print(f"❌ 投稿公開失敗: {publish_result}")
        print("⏭️ 同一内容の重複投稿を防ぐため進捗を次へ進めました")
        print(f"📊 次回: Day{next_post['day']:02d} 投稿")
        sys.exit(1)  # 失敗を GitHub Actions に伝える

    print(f"✅ 投稿成功！投稿ID: {publish_result['id']}")

    # 次回の進捗を保存（last_posted_at を記録して重複防止に使う）
    save_progress(current_index + 1, last_posted_at=now_iso)
    next_post = posts[(current_index + 1) % len(posts)]
    print(f"📊 次回: Day{next_post['day']:02d} 投稿")
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
