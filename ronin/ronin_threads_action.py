# ronin_threads_action.py
# @RoninWords用 GitHub Actions専用の自動投稿スクリプト（対話なし・全自動）
# 使い方: python3 ronin_threads_action.py
# threads_posts.jsonの投稿を順番にローテーションで投稿する

import json                    # JSONファイルを扱う道具
import os                      # 環境変数を読み込む道具
import time                    # 待機処理に使う道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime, timezone  # 今の日時とタイムゾーンを扱う道具

# ronin専用モジュール（同じ ronin/ フォルダ内・cd ronin で実行されるためベアimport）
import ronin_hashtags          # ハッシュタグ・ローテーション
import ronin_engagement        # engagement在庫（コメント誘発投稿）
import ronin_comment_seeder    # 1コメ目テキスト生成
import ronin_theme_classifier  # 投稿本文のテーマ分類（1コメ目・CTA連動に使う）

# ローカル実行時は .env ファイルからAPIキーを読み込む（GitHub Actionsでは不要）
try:
    from dotenv import load_dotenv
    load_dotenv("/home/kenta_kamijyo/.env")
except ImportError:
    pass  # dotenvがなくても動くようにする

# 環境変数からAPIキーを読み込む
# GitHub Actions時: THREADS_ACCESS_TOKEN（secretsから渡される）
# ローカル実行時: RONIN_THREADS_ACCESS_TOKEN（.envから読み込む）
THREADS_ACCESS_TOKEN = os.environ.get("RONIN_THREADS_ACCESS_TOKEN") or os.environ.get("THREADS_ACCESS_TOKEN")
THREADS_USER_ID      = os.environ.get("RONIN_THREADS_USER_ID")      or os.environ.get("THREADS_USER_ID")

# 投稿データと進捗ファイルのパス
POSTS_FILE    = "threads_posts.json"            # 投稿データが入っているファイル
PROGRESS_FILE = "ronin_threads_progress.json"   # 「次は何番目を投稿するか」を覚えておくファイル

# GitHubリポジトリのRAW画像URL（画像はここから取得される）
# GitHubにpushされた画像ファイルを直接URLで参照する
GITHUB_RAW_BASE = "https://kmkn0523-cell.github.io/kenta-learning/ronin/ronin_images"

# マネタイズ導線は本文ではなく「1コメ目」に載せる（本文をクリーンに保ち配信抑制を避ける）
GUMROAD_URL = "https://kmknova8.gumroad.com/l/mowuxf"
SUBSTACK_URL = "https://substack.com/@roninwords"
GUMROAD_LINE = f"🖌 Get the calligraphy wallpaper pack → {GUMROAD_URL}"
SUBSTACK_LINE = f"📖 Full deep dive on this teaching → {SUBSTACK_URL}"


def get_image_url(day):
    """指定したDayの書道カード画像URLを返す（GitHub Raw URL）"""
    return f"{GITHUB_RAW_BASE}/day{day:02d}.png"


def post_to_threads(text, image_url=None, reply_to_id=None):
    """
    Threads APIを使って実際に投稿する（2段階APIコール）
    - image_url を渡すと画像付き投稿
    - reply_to_id を渡すと、その投稿への返信になる（1コメ目シーディング用）
    - どちらも無ければテキスト投稿
    """

    # ステップ1: 投稿コンテナ（投稿の下書き）を作成する
    container_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"

    if reply_to_id:
        # 返信投稿（テキストのみ・親投稿IDを指定）
        container_params = {
            "media_type": "TEXT",                 # 返信はテキスト
            "text": text,                         # 返信文
            "reply_to_id": reply_to_id,           # 返信先の投稿ID
            "access_token": THREADS_ACCESS_TOKEN  # 認証キー
        }
        print(f"  返信先ID: {reply_to_id}")
    elif image_url:
        # 画像付き投稿（media_type=IMAGE、テキストはキャプションとして添付）
        container_params = {
            "media_type": "IMAGE",                # 画像投稿
            "image_url": image_url,               # 書道カード画像のURL
            "text": text,                         # キャプション（投稿文）
            "access_token": THREADS_ACCESS_TOKEN  # 認証キー
        }
        print(f"  画像URL: {image_url}")
    else:
        # テキストのみ投稿（画像なし・フォールバック）
        container_params = {
            "media_type": "TEXT",                 # テキスト投稿
            "text": text,                         # 投稿する文章
            "access_token": THREADS_ACCESS_TOKEN  # 認証キー
        }

    # 一時的なAPIエラー（GitHub Pagesのデプロイ遅延など）に備えてリトライする（最大2回、30秒待つ）
    for attempt in range(1, 3):
        response = requests.post(container_url, params=container_params)
        data = response.json()

        if "id" in data:
            break  # 成功したらループを抜ける

        # メディア取得失敗（subcode 2207052）など一過性エラーは1回だけリトライ
        error_info = data.get("error", {})
        error_subcode = error_info.get("error_subcode")
        is_transient = error_info.get("is_transient") or error_subcode == 2207052
        if is_transient and attempt < 2:
            print(f"  ⚠️ コンテナ作成エラー（試行{attempt}/2）。30秒後にリトライします: {error_info.get('message', '')}")
            time.sleep(30)
        else:
            raise Exception(f"コンテナ作成失敗（試行{attempt}/2）: {data}")

    creation_id = data["id"]

    # Threads APIはコンテナ作成後すぐに公開するとエラーになるため30秒待つ
    print("コンテナ作成完了。30秒待機中...")
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

        error_info = publish_data.get("error", {})
        if error_info.get("is_transient") and attempt < 3:
            print(f"  ⚠️ 一時的なAPIエラー（試行{attempt}/3）。30秒後にリトライします...")
            time.sleep(30)
        else:
            raise Exception(f"公開失敗（試行{attempt}/3）: {publish_data}")

    return publish_data["id"]  # 投稿IDを返す


def decide_post_kind(history_count):
    """投稿履歴の件数から、今回が教えの投稿かengagement投稿かを決める。
    4投稿に1回(余り3)をengagementにする。"""
    return "engagement" if history_count % 4 == 3 else "teaching"


def build_full_text(content, hashtags):
    """本文＋ハッシュタグを組み立てる。500字を超える場合は本文側を丸める（タグは必ず残す）。"""
    suffix = f"\n\n{hashtags}"
    if len(content) + len(suffix) > 500:
        content = content[:500 - len(suffix) - 1] + "…"
    return content + suffix


def load_substack_articles_with_url():
    """Substackの進捗履歴（カード・deep-dive両方）から、公開URLを持つ記事の一覧を返す。
    各要素は {"title": str, "url": str}。ファイルが無い/壊れていても空リストを返す（投稿は止めない）。"""
    articles = []
    for filename in ("substack/substack_progress.json", "substack/deep_dive_progress.json"):
        try:
            with open(filename, encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            continue
        for entry in data.get("history", []):
            title = entry.get("title")
            url = entry.get("url")
            if title and url:
                articles.append({"title": title, "url": url})
    return articles


def pick_theme_substack_line(theme_key, articles):
    """テーマに合うSubstack記事のURLでCTA行を作る。無ければ既存のプロフィールURLにフォールバック。"""
    for article in articles:
        if ronin_theme_classifier.classify_category(article["title"]) == theme_key:
            return f"📖 Full deep dive on this teaching → {article['url']}"
    return SUBSTACK_LINE


def cta_line_for_cycle(history_count, theme_key=None, substack_articles=None):
    """14投稿サイクルで、1コメ目に載せるCTAリンク行を返す（通常回は空文字）。
    余り0=Gumroad / 余り7=Substack（従来の本文CTAと同じ周期）。
    余り7のときは theme_key に合う公開済みSubstack記事があればそのURLを使い、
    無ければプロフィールURL（SUBSTACK_LINE）にフォールバックする。"""
    cycle = history_count % 14
    if cycle == 0:
        return GUMROAD_LINE
    if cycle == 7:
        if theme_key is None:
            return SUBSTACK_LINE
        articles = substack_articles if substack_articles is not None else load_substack_articles_with_url()
        return pick_theme_substack_line(theme_key, articles)
    return ""


def flatten_posts():
    """
    threads_posts.jsonの「Day×朝夜」構造を、フラットな配列に変換する
    これで0番目→1番目→...と順番に消費しやすくなる
    """
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    flat_posts = []
    for post in data["posts"]:
        # 朝投稿を追加
        flat_posts.append({
            "day": post["day"],
            "type": "morning",
            "content": post["morning"]
        })
        # 夜投稿を追加
        flat_posts.append({
            "day": post["day"],
            "type": "evening",
            "content": post["evening"]
        })
    return flat_posts


def load_progress():
    """進捗ファイルを読み込む（なければ初期値で始める）"""
    if not os.path.exists(PROGRESS_FILE):
        return {"index": 0, "history": []}
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


# NOTE: 旧データ駆動の最適化パス（should_use_optimization / post_optimized）は休止のため削除した。
#       反応データが有意になったら、型別ランキング選択を git 履歴から戻して main に組み込む。


def get_last_post_time():
    """
    Threads APIで自分の最新投稿の時刻を取得する
    成功したらdatetimeオブジェクト（UTC）を返す、失敗したらNoneを返す
    """
    try:
        url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
        params = {
            "fields": "id,timestamp",  # 投稿IDと投稿時刻だけ取得（必要最小限）
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


def post_once(dry_run=False):
    """1回分の投稿を行う。
    - 4投稿に1回はengagement投稿、それ以外は教えの投稿
    - 本文にCTAリンクは入れず、公開直後に「1コメ目」を自動返信する
    - dry_run=True なら組み立て結果を表示するだけでAPIも保存もしない
    """
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    print(f"=== Ronin自動投稿: {now}{' [DRY-RUN]' if dry_run else ''} ===")

    progress = load_progress()
    teaching_posts = flatten_posts()
    history_count = len(progress.get("history", []))

    # 今回の種別・ハッシュタグ・CTAを決める
    kind = decide_post_kind(history_count)
    hashtags = ronin_hashtags.pick_hashtag_set(history_count)

    image_url = None  # engagementは画像なし、teachingは後で設定
    theme_key = None  # 投稿本文のテーマ分類（1コメ目・CTA連動に使う）

    if kind == "engagement":
        eng_posts = ronin_engagement.load_engagement_posts()
        if eng_posts:
            eng_index = progress.get("engagement_index", 0)
            eng = ronin_engagement.pick_engagement_post(eng_posts, eng_index)
            content = eng["text"]
            theme_key = ronin_theme_classifier.classify_category(content)
            seed_base = eng["seed_comment"]
            label = f"engagement {eng['id']}"
        else:
            # 在庫が無ければ教えの投稿にフォールバック
            print("⚠️ engagement在庫が空。教えの投稿にフォールバックします。")
            kind = "teaching"

    if kind == "teaching":
        index = progress.get("index", 0) % len(teaching_posts)
        post = teaching_posts[index]
        content = post["content"]
        theme_key = ronin_theme_classifier.classify_category(content)
        seed_base = ronin_comment_seeder.pick_seed_question(history_count, theme_key)
        image_url = get_image_url(post["day"])
        label = f"Day{post['day']:02d} {post['type']}"

    cta_line = cta_line_for_cycle(history_count, theme_key=theme_key)

    # 本文（CTA無し・ハッシュタグ付き）と1コメ目を組み立てる
    full_text = build_full_text(content, hashtags)
    seed_text = ronin_comment_seeder.build_seed_comment(seed_base, cta=cta_line)

    print(f"種別: {kind} / {label} / タグ: {hashtags}")
    print(f"本文(先頭80字): {full_text[:80]}...")
    print(f"1コメ目(seed): {seed_text[:80]}...")

    if dry_run:
        print("=== DRY-RUN 完了（投稿も保存もしていません）===")
        return

    # 本投稿
    post_id = post_to_threads(full_text, image_url=image_url)
    print(f"✅ 本投稿成功（ID: {post_id}）")

    # 1コメ目を自動返信（失敗しても本投稿は成功扱い）
    try:
        reply_id = post_to_threads(seed_text, reply_to_id=post_id)
        print(f"✅ 1コメ目シード成功（ID: {reply_id}）")
    except Exception as e:
        print(f"⚠️ 1コメ目シード失敗（本投稿は成功済み・スキップ）: {e}")

    # 進捗を進める（種別ごとにインデックスを別管理）
    if kind == "engagement":
        progress["engagement_index"] = progress.get("engagement_index", 0) + 1
    else:
        progress["index"] = (progress.get("index", 0) + 1) % len(teaching_posts)

    progress.setdefault("history", []).append({
        "date": now,
        "kind": kind,
        "label": label,
        "post_id": post_id,
    })
    now_iso = datetime.now(timezone.utc).isoformat()
    save_progress(progress, last_posted_at=now_iso)
    print("=== 完了 ===")


def main():
    """メイン処理: 90分以内に投稿済みならスキップ。--dry-runで実投稿せず確認。"""
    import sys
    dry_run = "--dry-run" in sys.argv

    print(f"=== Ronin自動投稿ヘルスチェック: {datetime.now().strftime('%Y/%m/%d %H:%M')} ===")

    if not dry_run and check_should_skip(skip_minutes=90):
        return  # 直近に投稿済み（重複防止）

    post_once(dry_run=dry_run)


if __name__ == "__main__":
    main()
