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

# ファイルのパス
POSTS_FILE    = os.path.join(os.path.dirname(__file__), "skin_threads_posts.json")      # 投稿データ（旧）
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "skin_instagram_progress.json") # 進捗記録

# 投稿のキャプションに使うハッシュタグ
HASHTAGS = "\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善"

# 投稿の末尾に追加するCTA
CTA = "\n\n詳しくはプロフィールリンクのnoteで読めます✍️"


# =============================
# キャプション組み立てロジック（新設計 v2）
# =============================

CTA_TYPES = {
    1: "保存",       # id % 4 == 1
    2: "コメント",   # id % 4 == 2
    3: "note誘導",   # id % 4 == 3
    0: "フォロー",   # id % 4 == 0
}

CTA_BODIES = {
    "保存": (
        "肌荒れが長引く人の共通点は、内側にあります。\n"
        "8枚で「今日から変えられる習慣」をまとめました。\n\n"
        "保存して、1つずつ試してみてください。\n"
        "3ヶ月で肌が変わります。"
    ),
    "コメント": (
        "あなたの「これが効いた」を教えてください。\n"
        "コメント欄を読み返すと、実例の宝庫になっています。\n\n"
        "あなたが効いた習慣を1つだけ、コメントで教えてください。"
    ),
    "note誘導": (
        "カルーセル8枚で要点をまとめましたが、\n"
        "詳しい改善ステップは note に全部書きました。\n\n"
        "プロフィールのリンクから読めます。\n"
        "8枚で「何を」がわかり、note で「どう進めるか」がわかります。"
    ),
    "フォロー": (
        "このアカウントでは肌荒れを内側から治す習慣を毎日発信中。\n"
        "8年間試してまとめた、本当に効いた習慣だけを投稿しています。\n\n"
        "フォローして、明日の朝の投稿も一緒に。"
    ),
}


def select_cta_type(theme_id: int) -> str:
    """テーマIDから4軸ローテーションのCTA型を返す"""
    return CTA_TYPES[theme_id % 4]


def build_hashtag_block(fixed: list, theme: list, size_mix: list) -> str:
    """3層のハッシュタグを # 付き・半角スペース区切りで結合する"""
    tags = []
    for layer in (fixed, theme, size_mix):
        tags.extend(f"#{t}" for t in layer)
    return " ".join(tags)


def build_caption(
    theme_id: int,
    hook: str,
    fixed: list,
    theme: list,
    size_mix: list,
) -> str:
    """v2 キャプションを組み立てる: フック再掲 + CTA本文 + ハッシュタグ"""
    cta_type = select_cta_type(theme_id)
    cta_body = CTA_BODIES[cta_type]
    hashtags = build_hashtag_block(fixed, theme, size_mix)

    return f"{hook}\n\n{cta_body}\n\n{hashtags}"


# =============================
# 進捗ファイルの読み書き
# =============================

def load_progress():
    """前回までの投稿進捗を読み込む（v1/v2の交互投稿に対応）
    新フォーマット: {"v1_index": N, "v2_index": M, "post_count": K}
    旧フォーマット {"next_index": N} は自動マイグレーション（v2=4テーマ既出を前提）
    """
    if not os.path.exists(PROGRESS_FILE):
        return {"v1_index": 0, "v2_index": 0, "post_count": 0}
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"v1_index": 0, "v2_index": 0, "post_count": 0}

    # 新フォーマットならそのまま返す
    if "post_count" in data:
        return data
    # 旧フォーマット → マイグレーション（next_index個 全て連番で投稿済み前提）
    old_next = int(data.get("next_index", 0))
    v2_count = 4  # v2テーマ数（ID 1〜4）
    v2_done = min(old_next, v2_count)
    v1_done = max(0, old_next - v2_count)
    return {
        "v1_index": v1_done,
        "v2_index": v2_done,
        "post_count": old_next,
    }


def save_progress(v1_index: int, v2_index: int, post_count: int):
    """投稿進捗をファイルに保存する"""
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"v1_index": v1_index, "v2_index": v2_index, "post_count": post_count},
                f,
                ensure_ascii=False,
                indent=2,
            )
    except Exception as e:
        print(f"⚠️ 進捗保存エラー: {e}")


def select_next_theme(themes: list, progress: dict):
    """v1:v2 = 4:1 の比率で次のテーマを選ぶ（5投稿に1回 v2）
    戻り値: (theme, kind) — kind は "v1" or "v2"
    """
    # v2 / v2.1 はどちらも v2 系として扱う（caption ビルダー対応済み）
    v1_themes = [t for t in themes if t.get("version") not in ("v2", "v2.1")]
    v2_themes = [t for t in themes if t.get("version") in ("v2", "v2.1")]
    post_count = progress.get("post_count", 0)
    # 5投稿目（post_count=4, 9, 14, ...）を v2 に割り当てる
    use_v2 = ((post_count + 1) % 5 == 0) and len(v2_themes) > 0
    # v1 が枯渇している場合は v2 にフォールバック（全テーマ v2.1 化への対応）
    if use_v2 or len(v1_themes) == 0:
        idx = progress.get("v2_index", 0) % len(v2_themes)
        return v2_themes[idx], "v2"
    else:
        idx = progress.get("v1_index", 0) % len(v1_themes)
        return v1_themes[idx], "v1"


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


def build_carousel_image_urls(theme_id: int, slide_count: int) -> list:
    """テーマIDとスライド枚数からカルーセル画像のURL一覧を作る"""
    return [
        f"{GITHUB_CAROUSEL_BASE}/theme{theme_id:02d}_slide{i}.png"
        for i in range(1, slide_count + 1)
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
                # FINISHED直後でもInstagram内部処理が終わっていないことがある
                # 30秒待ってから publish することで OAuthException 9007 を防ぐ
                print("  ✅ FINISHED確認。30秒待機してから公開します...")
                time.sleep(30)
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

            error_info = data.get("error", {})
            error_code = error_info.get("code")

            # レート制限（アカウントブロック）: is_transient=False かつ code=4 → リトライ不要
            if not error_info.get("is_transient", False):
                print(f"❌ 投稿公開失敗（試行{attempt}/3）: {data}")
                if error_code == 4:
                    return {"rate_limited": True}  # 上位処理に「ブロック中」と伝える
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

    # 前回の進捗を読み込んで次のテーマを選ぶ（v1:v2 = 4:1 で交互投稿）
    progress       = load_progress()
    theme, kind    = select_next_theme(themes, progress)
    theme_id       = theme["id"]

    # v2 ならビルダーで組み立て、v1 なら既存の caption をそのまま使う（後方互換）
    if theme.get("version") in ("v2", "v2.1"):
        caption = build_caption(
            theme_id=theme_id,
            hook=theme.get("hook", theme.get("slides", [{}])[0].get("title", "")),
            fixed=theme["fixed_hashtags"],
            theme=theme["theme_hashtags"],
            size_mix=theme["size_mix_hashtags"],
        )
    else:
        caption = theme["caption"]

    print(f"📌 テーマ{theme_id:02d}（{kind}・post_count={progress.get('post_count', 0)}）")

    # カルーセル画像のURLを slide_count 分作る（v1=5, v2=8）
    slide_count = theme.get("slide_count", 5)
    image_urls  = build_carousel_image_urls(theme_id, slide_count)
    print(f"🖼️  スライド画像: {len(image_urls)}枚 (version={theme.get('version', 'v1')})")

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
    # 進捗を1つ進めるための新しい値を計算
    new_v1 = progress.get("v1_index", 0) + (1 if kind == "v1" else 0)
    new_v2 = progress.get("v2_index", 0) + (1 if kind == "v2" else 0)
    new_count = progress.get("post_count", 0) + 1

    if "id" not in publish_result:
        if publish_result.get("rate_limited"):
            # APIブロック（error code 4）でも進捗を1つ進める
            # 同じ投稿を何度もリトライすると「同じ内容が続く」問題が起きるため
            save_progress(new_v1, new_v2, new_count)
            next_theme, next_kind = select_next_theme(
                themes,
                {"v1_index": new_v1, "v2_index": new_v2, "post_count": new_count},
            )
            print("⏭️ InstagramのAPIブロックのためスキップ（進捗は次へ進めます）")
            print(f"📊 次回テーマ: {next_theme['id']:02d}（{next_kind}）")
            sys.exit(0)  # 正常終了（GitHub Actionsを赤くしない）
        # その他の公開失敗（OAuthException 9007 など）でも進捗を1つ進める
        # 進捗を進めないと次回も同じテーマが選ばれ、同一内容が2重投稿される恐れがある
        save_progress(new_v1, new_v2, new_count)
        next_theme, next_kind = select_next_theme(
            themes,
            {"v1_index": new_v1, "v2_index": new_v2, "post_count": new_count},
        )
        print(f"❌ 投稿公開失敗: {publish_result}")
        print("⏭️ 同一内容の重複投稿を防ぐため進捗を次へ進めました")
        print(f"📊 次回テーマ: {next_theme['id']:02d}（{next_kind}）")
        sys.exit(1)

    print(f"✅ カルーセル投稿成功！投稿ID: {publish_result['id']}")

    # 次回の進捗を保存する
    save_progress(new_v1, new_v2, new_count)
    next_theme, next_kind = select_next_theme(
        themes,
        {"v1_index": new_v1, "v2_index": new_v2, "post_count": new_count},
    )
    print(f"📊 次回テーマ: {next_theme['id']:02d}（{next_kind}・post_count={new_count}）")
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
