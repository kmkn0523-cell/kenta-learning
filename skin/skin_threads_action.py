# skin_threads_action.py
# GitHub Actions専用の自動投稿スクリプト（対話なし・全自動）
# ツリー構造（3本連鎖）でThreadsに投稿する

import json                    # JSONファイルを扱う道具
import os                      # 環境変数を読み込む道具
import time                    # 待機処理に使う道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime, timezone  # 今の日時とタイムゾーンを扱う道具

# ローカル実行時は .env ファイルからAPIキーを読み込む（GitHub Actionsでは不要）
try:
    from dotenv import load_dotenv
    load_dotenv("/home/kenta_kamijyo/.env")
except ImportError:
    pass

# 環境変数からAPIキーを読み込む（GitHub Actionsのsecretsから渡される）
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
THREADS_USER_ID      = os.environ["THREADS_USER_ID"]

# GitHub Pagesの画像ベースURL
GITHUB_BASE = "https://kmkn0523-cell.github.io/kenta-learning/skin/skin_images"


def get_image_url(thread_id):
    """スレッドIDに対応するカード画像のURLを返す（GitHub Pages）"""
    # 画像は theme01〜theme108 の108枚あり、各テーマと画像が1対1で対応する
    # 範囲外のIDが来てもURLが壊れないよう、安全側で1〜108に丸める
    IMAGE_COUNT = 108
    image_id = ((thread_id - 1) % IMAGE_COUNT) + 1
    return f"{GITHUB_BASE}/theme{image_id:02d}.jpg"

# 投稿データと進捗ファイルのパス
POSTS_FILE    = "skin_threads_posts.json"      # ツリー用の新しい投稿データ
PROGRESS_FILE = "skin_threads_progress.json"  # 次に投稿する番号を覚えておくファイル

# 3本目の投稿につけるハッシュタグ
HASHTAGS = "\n\n#肌荒れ #大人ニキビ #ニキビ改善 #腸活 #美肌習慣"


# ==== A/Bテスト機構（2026-05-18 追加） ====

def pick_today_theme(daily_index: int) -> int:
    # daily_indexから今日のテーマ番号（1〜108）を計算する
    return daily_index % 108 + 1


def select_ab_variant(progress: dict, theme_id: int) -> str:
    # progressから指定テーマのA/B選択状態を取得（無ければA）
    table = progress.get("ab_index_per_theme", {})
    return table.get(str(theme_id), "A")


def flip_ab_variant(progress: dict, theme_id: int) -> None:
    # 指定テーマのA/B選択状態を反転（投稿後に呼ぶ）
    table = progress.setdefault("ab_index_per_theme", {})
    current = table.get(str(theme_id), "A")
    table[str(theme_id)] = "B" if current == "A" else "A"


def load_posts_for_variant(data: dict, theme_id: int, variant: str) -> dict:
    # data["threads_a"] or data["threads_b"] から該当セットを返す
    # 指定variantが空 or テーマ未投入なら反対側にフォールバック
    key_primary = "threads_a" if variant == "A" else "threads_b"
    key_fallback = "threads_b" if variant == "A" else "threads_a"
    for arr_key in (key_primary, key_fallback):
        for entry in data.get(arr_key, []):
            if entry.get("id") == theme_id:
                return entry
    raise ValueError(f"テーマ{theme_id}が両配列に見つからない")


def post_to_threads(text, reply_to_id=None, image_url=None):
    """
    Threads APIを使って投稿する（2段階APIコール）
    reply_to_id を渡すとリプライ投稿になる（ツリーの2本目・3本目に使う）
    image_url を渡すと画像付き投稿になる（本1のみ使用）
    """

    # ステップ1: 投稿コンテナ（投稿の下書き）を作成する
    container_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"

    if image_url:
        # 画像付き投稿（media_type=IMAGE）
        container_params = {
            "media_type": "IMAGE",
            "image_url": image_url,
            "text": text,
            "access_token": THREADS_ACCESS_TOKEN
        }
        print(f"  画像URL: {image_url}")
    else:
        # テキストのみ投稿
        container_params = {
            "media_type": "TEXT",
            "text": text,
            "access_token": THREADS_ACCESS_TOKEN
        }

    # リプライ投稿の場合は「どの投稿への返信か」を追加する
    if reply_to_id:
        container_params["reply_to_id"] = reply_to_id

    response = requests.post(container_url, params=container_params, timeout=30)
    data = response.json()

    if "id" not in data:
        raise Exception(f"コンテナ作成失敗: {data}")

    creation_id = data["id"]  # 下書きのID

    # Threads APIはコンテナ作成後すぐに公開するとエラーになるため30秒待つ
    print("  コンテナ作成完了。30秒待機中...")
    time.sleep(30)

    # ステップ2: 下書きを実際に公開する
    publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": THREADS_ACCESS_TOKEN
    }
    # 一時的なAPIエラーに備えてリトライする（最大3回、30秒ずつ待つ）
    for attempt in range(1, 4):
        publish_response = requests.post(publish_url, params=publish_params)
        publish_data = publish_response.json()

        if "id" in publish_data:
            break  # 成功したらループを抜ける

        # is_transient=True（Meta側の一時障害）なら待ってリトライ
        error_info = publish_data.get("error", {})
        if error_info.get("is_transient") and attempt < 3:
            print(f"  ⚠️ 一時的なAPIエラー（試行{attempt}/3）。30秒後にリトライします...")
            time.sleep(30)
        else:
            raise Exception(f"公開失敗（試行{attempt}/3）: {publish_data}")

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


def save_progress(progress, last_posted_at=None):
    """進捗をファイルに保存する
    last_posted_at: 投稿した日時（UTC ISO形式）。渡したときだけ progress に追記する
    """
    if last_posted_at is not None:
        progress["last_posted_at"] = last_posted_at  # 投稿時刻を記録（重複防止に使う）
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def get_last_post_time():
    """
    Threads APIで自分の最新投稿の時刻を取得する
    成功したらdatetimeオブジェクト（UTC）、失敗したらNoneを返す
    """
    try:
        url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
        params = {
            "fields": "id,timestamp",  # 投稿IDと投稿時刻だけ取得
            "limit": 1,                # 最新の1件だけ取得
            "access_token": THREADS_ACCESS_TOKEN
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

    ① まず progress.json の last_posted_at を確認する（APIキャッシュ遅延を回避するため）
    ② last_posted_at がなければ Threads API で確認する（フォールバック）
    - 90分以内に投稿あり → スキップ（重複防止）
    - 90分以上たっている → 投稿する（自動修復）
    - API取得失敗 → 投稿する（フェイルセーフ）
    """
    # ① progress.json から前回投稿時刻を確認する（APIより確実・遅延なし）
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

    # ② フォールバック: Threads API で最新投稿時刻を確認する
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


def pick_ab_thread(threads_list, progress):
    """
    A/Bテスト用の投稿セットを選ぶ
    ab_next が "B" なら B型（新フォーマット）、"A" なら A型（既存）を返す
    それぞれ独立したインデックスで管理する
    """
    ab_next = progress.get("ab_next", "A")

    # A型とB型に分ける
    a_posts = [p for p in threads_list if not p.get("ab_group") == "B"]
    b_posts = [p for p in threads_list if p.get("ab_group") == "B"]

    if ab_next == "B" and b_posts:
        # B型を選ぶ
        index = progress.get("ab_b_index", 0) % len(b_posts)
        thread_set = b_posts[index]
        progress["ab_b_index"] = (index + 1) % len(b_posts)
        progress["ab_next"] = "A"  # 次回はAに戻す
        print(f"  📊 ABテスト: B型 ({index + 1}/{len(b_posts)})")
    else:
        # A型を選ぶ（デフォルト・B型がなければAにフォールバック）
        index = progress.get("daily_index", 0) % len(a_posts)
        thread_set = a_posts[index]
        progress["daily_index"] = (index + 1) % len(a_posts)
        progress["ab_next"] = "B" if b_posts else "A"  # 次回はBへ
        print(f"  📊 ABテスト: A型 ({index + 1}/{len(a_posts)})")

    return thread_set


def main():
    """メイン処理（全自動・対話なし）"""
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    print(f"=== skin自動投稿ヘルスチェック: {now} ===")

    # 直近90分以内に投稿済みならスキップする（重複防止・自動修復の起点）
    if check_should_skip(skip_minutes=90):
        return  # 投稿済みなので何もしない

    print(f"=== skin自動投稿開始: {now} ===")

    # 投稿データと進捗を読み込む
    posts    = load_posts()
    progress = load_progress()

    # 今日のテーマ番号とA/Bバリアントを決めて投稿セットを選ぶ
    theme_id   = pick_today_theme(progress["daily_index"])
    variant    = select_ab_variant(progress, theme_id)
    thread_set = load_posts_for_variant(posts, theme_id, variant)

    print(f"投稿セット: {thread_set['theme']}")

    # human_post があればそれを優先（人間っぽい短い完結型）
    # なければ従来通り posts[0]+posts[1]+固定ハッシュタグ
    if thread_set.get("human_post"):
        post_text = thread_set["human_post"]
        print("  📝 human_post を使用")
    else:
        post_text = thread_set["posts"][0] + "\n\n" + thread_set["posts"][1] + HASHTAGS
        print("  📝 従来版（posts[0]+posts[1]）を使用")

    # 画像付きか・テキストのみかを決める（skip_imageフラグで切り替え）
    if thread_set.get("skip_image"):
        print("\n投稿中（テキストのみ）...")
        post_id = post_to_threads(post_text)
    else:
        print("\n投稿中（画像付き）...")
        image_url = get_image_url(thread_set["id"])
        post_id = post_to_threads(post_text, image_url=image_url)
    print(f"  ✅ 投稿成功！（ID: {post_id}）")

    # A/B選択状態を反転して次回に備える
    flip_ab_variant(progress, theme_id)
    # A/B結果集計用のpost数カウントもインクリメント
    results = progress.setdefault("ab_results", {})
    theme_key = str(theme_id)
    results.setdefault(theme_key, {"a_score": 0.0, "b_score": 0.0, "a_posts": 0, "b_posts": 0})
    results[theme_key]["a_posts" if variant == "A" else "b_posts"] += 1
    progress["daily_index"] += 1  # 次回の投稿番号を進める

    # 履歴に記録する（variant と theme_id を含めて後で比較できるようにする）
    if "history" not in progress:
        progress["history"] = []
    progress["history"].append({
        "date": now,
        "theme": thread_set["theme"],
        "theme_id": theme_id,
        "variant": variant,
        "post_id": post_id
    })

    now_iso = datetime.now(timezone.utc).isoformat()  # 投稿した日時（UTC）を記録
    save_progress(progress, last_posted_at=now_iso)  # 進捗と投稿時刻を保存する
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
