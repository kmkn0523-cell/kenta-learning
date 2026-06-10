# skin_threads_action.py
# GitHub Actions専用の自動投稿スクリプト（対話なし・全自動）
# ツリー構造（3本連鎖）でThreadsに投稿する

import json                    # JSONファイルを扱う道具
import os                      # 環境変数を読み込む道具
import random                  # ランダムに選ぶ道具（note宣伝の記事選択に使う）
import time                    # 待機処理に使う道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime, timezone, timedelta  # 今の日時・タイムゾーン・時間差を扱う道具

import skin_hashtags           # ハッシュタグ4セットローテーション（スパム判定回避）
import skin_comment_seeder     # 1コメ目シード生成（早期リプライでreachを伸ばす）

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

# ===== ボーナス投稿の設定（バズ追撃・案A クリーン加速） =====
BONUS_POSTS_FILE = "skin_threads_bonus_posts.json"  # ボーナス専用の弾プール（通常投稿と被らない）
BONUS_ANALYTICS_FILE = "skin_analytics.json"        # 反応データ履歴（収集スクリプトが更新）
BONUS_MIN_VIEWS = 15          # views 足切り（低viewでengagement_rateが暴れるのを排除）
BONUS_MIN_LIKES = 2           # likes 足切り（今の自己ベスト級）
BONUS_LOOKBACK_DAYS = 14      # 相対平均を取る期間（日）
BONUS_RATE_MULTIPLIER = 1.5   # 相対閾値の倍率（直近平均 × この値を超えたら発火）
BONUS_MAX_PER_DAY = 1         # 1日に撃つ上限本数（= +1本）

# ===== note宣伝投稿の設定 =====
# 何回に1回note宣伝を挟むか（4 = 1日4投稿中1回が宣伝になる）
NOTE_PROMO_INTERVAL = 2  # 2日に1回note宣伝を投稿する
# 宣伝対象のnote記事一覧ファイル（無料記事のみ・手動管理）
NOTE_PROMO_FILE = "note_promo_articles.json"

# ===== 有料note宣伝投稿の設定 =====
PAID_NOTE_PROMO_INTERVAL = 7  # 7日に1回（毎週）有料note宣伝を投稿する
PAID_NOTE_PROMO_FILE = "paid_note_promo_articles.json"  # 有料記事の一覧ファイル

# note宣伝投稿の本文テンプレート（毎回ランダムで1つ選ぶ → 同じ文面の繰り返しを防ぐ）
# ⚠️ 本文にURLを入れない設計：Threadsはリンク付き投稿の配信を抑制するため、
#     リンクは1コメ目（リプライ）に置く（roninで実証済みのreach施策）
NOTE_PROMO_TEMPLATES = [
    (
        "肌荒れの原因、意外なところにあるかも。\n\n"
        "『{title}』\n\n"
        "Threadsでは書ききれない部分まで、noteに全部まとめました。\n"
        "無料で読めます。\n\n"
        "リンクは1コメ目に置いてます👇"
    ),
    (
        "保存しておくと役立つやつ。\n\n"
        "『{title}』\n\n"
        "8年分の試行錯誤を、1本のnoteに整理しました。\n"
        "無料です。\n\n"
        "読みたい人は1コメ目からどうぞ👇"
    ),
    (
        "最近の投稿を読んでくれてる人に、もう1つ。\n\n"
        "『{title}』\n\n"
        "根本からケアしたい人向けに、noteで詳しく解説してます。\n"
        "完全無料。\n\n"
        "1コメ目にリンク貼っておきます👇"
    ),
    (
        "「なんで肌荒れが繰り返すんだろう？」\n\n"
        "その答えの1つが、ここにあります。\n\n"
        "『{title}』\n\n"
        "無料で公開中。\n\n"
        "気になる人は1コメ目をチェック👇"
    ),
    (
        "Threadsでは書ききれないことを、noteにまとめてます。\n\n"
        "『{title}』\n\n"
        "無料記事だけでもかなり読めます。\n\n"
        "リンクは1コメ目です👇"
    ),
]

# note宣伝の1コメ目（リンクはここに置く・本文には入れない）
NOTE_PROMO_COMMENT = (
    "📎 記事はこちら（無料で読めます）\n"
    "{url}\n\n"
    "本気で変えたい人向けの有料noteもプロフィールから読めます。"
)

# 有料note宣伝の本文テンプレート（悩み→部分的な解決策→有料noteで全貌を、の構成）
# ⚠️ 本文にURLを入れない設計：リンクは1コメ目に置く（配信抑制の回避）
PAID_NOTE_PROMO_TEMPLATES = [
    (
        "洗顔を変えても、化粧水を変えても、肌荒れが繰り返す。\n\n"
        "それ、原因が「外側」じゃないからかもしれません。\n\n"
        "腸・食事・睡眠・ストレス。\n"
        "内側から整える順番と具体的なやり方を\n"
        "1本のnoteにまとめました。\n\n"
        "『{title}』（{price}）\n\n"
        "リンクは1コメ目に置いてます👇"
    ),
    (
        "「何から始めればいいかわからない」\n\n"
        "肌荒れに悩む人が一番つまずくのは、ここです。\n\n"
        "情報は山ほどある。でも順番がわからない。\n"
        "だから全部まとめて、1から順に実践できる形にしました。\n\n"
        "『{title}』（{price}）\n\n"
        "続きは1コメ目から👇"
    ),
    (
        "皮膚科に通っても繰り返す肌荒れ、ありませんか？\n\n"
        "塗り薬で一時的に抑えても、やめると再発する。\n"
        "それは体質の問題が残っているからです。\n\n"
        "体質から見直す具体的なステップを書きました。\n\n"
        "『{title}』（{price}）\n\n"
        "リンクは1コメ目です👇"
    ),
    (
        "Threadsでは毎日1つずつヒントを書いていますが、\n"
        "正直、断片的な情報だけでは変わりにくいです。\n\n"
        "全体像を1本で理解して、今日から順番に実践できる。\n"
        "そういうnoteを書きました。\n\n"
        "『{title}』（{price}）\n\n"
        "気になる人は1コメ目をチェック👇"
    ),
    (
        "8年間、肌荒れと向き合ってきた記録があります。\n\n"
        "何十万円も使って、何十種類も試して、\n"
        "最終的に「これだけでよかった」にたどり着いた。\n\n"
        "その全部をまとめました。\n\n"
        "『{title}』（{price}）\n\n"
        "リンクは1コメ目に置いてます👇"
    ),
    (
        "肌荒れの原因は1つじゃない。\n"
        "腸、食事、睡眠、ストレス、洗顔…全部つながっている。\n\n"
        "だから「○○だけ変えればいい」とは言えません。\n\n"
        "全部を正しい順番で整える方法を書きました。\n\n"
        "『{title}』（{price}）\n\n"
        "続きは1コメ目から👇"
    ),
    (
        "「サプリを飲んでるのに変わらない」\n"
        "「腸活してるのに肌が変わらない」\n\n"
        "やり方が間違っているんじゃなくて、\n"
        "順番が間違っている可能性があります。\n\n"
        "正しい順番、ここに書きました。\n\n"
        "『{title}』（{price}）\n\n"
        "リンクは1コメ目です👇"
    ),
    (
        "この投稿を保存してくれている人へ。\n\n"
        "保存だけで終わらせず、本気で変えたいなら\n"
        "体系的にまとめたnoteを読んでみてください。\n\n"
        "読んだその日から実践できる内容です。\n\n"
        "『{title}』（{price}）\n\n"
        "1コメ目にリンク貼っておきます👇"
    ),
    (
        "無料のnoteだけでも十分役に立ちます。\n\n"
        "でも「もう情報を探し回るのは疲れた」\n"
        "「全部まとめて一気に変えたい」という人には\n"
        "有料版を用意しています。\n\n"
        "『{title}』（{price}）\n\n"
        "リンクは1コメ目に置いてます👇"
    ),
    (
        "食事、腸活、睡眠、ストレス管理、正しい洗顔。\n\n"
        "「全部大事なのはわかった。でも具体的にどうすれば？」\n\n"
        "その疑問に全部答えるnoteを書きました。\n"
        "今日読んで、今日から始められます。\n\n"
        "『{title}』（{price}）\n\n"
        "続きは1コメ目から👇"
    ),
]

# 有料note宣伝の1コメ目（リンクはここに置く・本文には入れない）
PAID_NOTE_PROMO_COMMENT = (
    "📎 noteはこちら（{price}）\n"
    "{url}\n\n"
    "目次だけでも無料で見られます。"
)


# ==== A/Bテスト機構（2026-05-18 追加） ====

def pick_today_theme(daily_index: int, theme_count: int = 108) -> int:
    # daily_indexから今日のテーマ番号（1〜theme_count）を計算する
    # theme_countはthreads_aの件数を渡す（109〜128が死蔵されていたバグの修正）
    return daily_index % theme_count + 1


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


def _parse_posted_at_to_jst_date(posted_at):
    """UTCの投稿時刻文字列（例 "2026-05-15T04:01:07+0000"）をJSTの日付に変換する。"""
    # Threads APIは "+0000" 形式で返すが、fromisoformat は "+00:00" を求めるので直す
    normalized = posted_at.replace("+0000", "+00:00")
    dt_utc = datetime.fromisoformat(normalized)  # UTCの日時に変換
    dt_jst = dt_utc + timedelta(hours=9)          # 日本時間は +9時間
    return dt_jst.date()                          # 日付の部分だけ取り出す


def should_fire_bonus(posts_history, today):
    """ボーナス投稿を撃つべきか判定する純関数。

    JST前日の投稿のうち、3条件（views/likes/相対engagement_rate）を
    すべて満たすものが1本でもあれば True。それ以外は False（安全側＝撃たない）。
    """
    yesterday = today - timedelta(days=1)  # 判定対象は「JST前日」
    dated_posts = []                       # (JST日付, 投稿) のペアを貯める箱
    for post in posts_history:
        posted_at = post.get("posted_at", "")  # 投稿時刻の文字列
        if not posted_at:
            continue                            # 時刻が無い投稿は無視
        try:
            jst_date = _parse_posted_at_to_jst_date(posted_at)  # JST日付へ変換
        except (ValueError, TypeError):
            continue                            # 変換できない壊れた値は無視
        dated_posts.append((jst_date, post))
    # 前日に投稿したものだけ抜き出す
    yesterday_posts = [post for (jst_date, post) in dated_posts if jst_date == yesterday]
    if not yesterday_posts:
        return False                            # 前日に投稿が無ければ撃たない
    # 直近14日の engagement_rate を集めて平均を出す（views=0/rate=0も母集団に含める）
    window_start = today - timedelta(days=BONUS_LOOKBACK_DAYS)
    recent_rates = [
        post.get("engagement_rate", 0)
        for (jst_date, post) in dated_posts
        if window_start <= jst_date <= today
    ]
    if not recent_rates:
        return False                            # 直近データが無ければ撃たない
    average_rate = sum(recent_rates) / len(recent_rates)      # 直近平均
    relative_threshold = average_rate * BONUS_RATE_MULTIPLIER  # 相対閾値
    # 前日の投稿で3条件すべて満たすものが1本でもあれば発火
    for post in yesterday_posts:
        views = post.get("views", 0)
        likes = post.get("likes", 0)
        rate = post.get("engagement_rate", 0)
        if views >= BONUS_MIN_VIEWS and likes >= BONUS_MIN_LIKES and rate >= relative_threshold:
            return True
    return False                                # どれも届かなければ撃たない


def load_bonus_posts():
    """ボーナス専用の弾プール（skin_threads_bonus_posts.json）を読み込む。"""
    if not os.path.exists(BONUS_POSTS_FILE):
        return []                               # ファイルが無ければ弾なし扱い
    with open(BONUS_POSTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("bonus_posts", [])          # 弾のリストを取り出す


def bonus_main():
    """ボーナス投稿モードの本体（通常4枠とは完全独立・A/Bに触れない）。"""
    # 今のJST日付を出す（UTC+9時間）
    now_jst = datetime.now(timezone.utc) + timedelta(hours=9)
    today_jst = now_jst.date()
    today_str = today_jst.isoformat()           # "YYYY-MM-DD" の文字列
    progress = load_progress()                  # 進捗を読む
    # 今日すでにボーナスを撃っていたら二重投稿防止で終了
    if progress.get("last_bonus_date") == today_str:
        print(f"⏭️  本日({today_str})は既にボーナス投稿済みのため終了します")
        return
    # 反応データファイルが無ければ判定できないのでスキップ
    if not os.path.exists(BONUS_ANALYTICS_FILE):
        print(f"⚠️  {BONUS_ANALYTICS_FILE} が見つかりません。ボーナス判定をスキップします")
        return
    with open(BONUS_ANALYTICS_FILE, "r", encoding="utf-8") as f:
        analytics = json.load(f)
    posts_history = analytics.get("posts_history", [])  # 反応データ履歴
    # 発火条件を満たさなければ撃たずに終了（安全側）
    if not should_fire_bonus(posts_history, today_jst):
        print(f"📊 本日({today_str})はボーナス発火条件を満たしません。投稿せず終了します")
        return
    bonus_posts = load_bonus_posts()            # 弾を読み込む
    if not bonus_posts:
        print("⚠️  ボーナス弾プールが空です。投稿せず終了します（弾の補充が必要）")
        return
    bonus_index = progress.get("bonus_index", 0)  # 次に使う弾の番号
    if bonus_index >= len(bonus_posts):
        print(f"⚠️  ボーナス弾を撃ち尽くしました(bonus_index={bonus_index})。補充するまでスキップします")
        return
    chosen = bonus_posts[bonus_index]           # 今回撃つ弾
    post_text = chosen.get("text", "")
    if not post_text:
        print(f"⚠️  bonus_index={bonus_index} の弾にテキストがありません。スキップします")
        return
    full_text = post_text + HASHTAGS            # 本文＋ハッシュタグ
    print(f"🚀 ボーナス投稿を実行します（bonus_index={bonus_index}）")
    post_id = post_to_threads(full_text)        # Threadsへ投稿
    print(f"✅ ボーナス投稿完了: post_id={post_id}")
    # 進捗の専用キーだけ更新（last_posted_at は絶対に触らない）
    progress["bonus_index"] = bonus_index + 1
    progress["last_bonus_date"] = today_str
    save_progress(progress)                     # last_posted_at を渡さず保存
    print(f"💾 進捗を更新しました: bonus_index={bonus_index + 1}, last_bonus_date={today_str}")


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


# ===== note宣伝投稿の関数 =====

def should_post_note_promo(progress):
    """前回のnote宣伝から2日以上経っていればTrueを返す"""
    last_date_str = progress.get("last_note_promo_date", "")
    if not last_date_str:
        return True  # 初回は必ず投稿する
    try:
        last_date = datetime.strptime(last_date_str, "%Y/%m/%d").date()
        today = datetime.now().date()
        return (today - last_date).days >= NOTE_PROMO_INTERVAL
    except ValueError:
        return True  # 日付の形式が壊れていたら投稿する


def pick_random_note(progress):
    """公開済みnoteの中からランダムに1つ選ぶ（直前と同じ記事は避ける）"""
    try:
        with open(NOTE_PROMO_FILE, "r", encoding="utf-8") as f:
            note_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"⚠️ note一覧の読み込みに失敗: {e}")
        return None

    articles = note_data.get("articles", [])
    if not articles:
        return None

    # 直前に宣伝した記事を除外する（同じ記事が連続するのを防ぐ）
    last_promo = progress.get("last_note_promo_article", "")
    candidates = [a for a in articles if a.get("url") != last_promo]
    if not candidates:
        candidates = articles  # 1記事しかない場合はそのまま使う

    return random.choice(candidates)


def build_note_promo_text(title, url):
    """note宣伝投稿の文面をテンプレートからランダムに生成する"""
    template = random.choice(NOTE_PROMO_TEMPLATES)
    # タイトルが長すぎる場合は先頭部分だけ使う（Threadsの500文字制限対策）
    short_title = title if len(title) <= 60 else title[:57] + "..."
    return template.format(title=short_title, url=url)


def post_note_promo(progress, now):
    """note宣伝投稿を実行する。成功でTrue、失敗でFalse（通常投稿にフォールバック）"""
    note = pick_random_note(progress)
    if note is None:
        print("⚠️ 公開済みnoteが見つからないため、通常投稿に切り替えます")
        return False

    title = note.get("title", "")
    url = note.get("url", "")
    promo_text = build_note_promo_text(title, url)

    print(f"📢 note宣伝投稿: 『{title}』")
    print(f"🔗 URL: {url}")
    print(f"📝 文字数: {len(promo_text)}")

    # テキストのみで投稿する（画像なし）
    print("\n投稿中（note宣伝・テキストのみ）...")
    post_id = post_to_threads(promo_text)
    print(f"  ✅ note宣伝投稿成功！（ID: {post_id}）")

    # 進捗を更新する（投稿成功後のみ）
    progress["last_note_promo_article"] = note.get("url", "")
    progress["last_note_promo_date"] = datetime.now().strftime("%Y/%m/%d")

    if "history" not in progress:
        progress["history"] = []
    progress["history"].append({
        "date": now,
        "theme": f"note宣伝: {title[:30]}",
        "theme_id": 0,
        "variant": "note_promo",
        "post_id": post_id
    })

    now_iso = datetime.now(timezone.utc).isoformat()
    save_progress(progress, last_posted_at=now_iso)
    print("=== 完了（note宣伝） ===")
    return True


def main():
    """メイン処理（全自動・対話なし）"""
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    print(f"=== skin自動投稿ヘルスチェック: {now} ===")

    # 深夜帯（JST 0:00〜6:59）は投稿しない（Threadsアルゴリズム最適化）
    jst_now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=9)))
    if jst_now.hour < 7:
        print(f"⏸ 深夜帯（JST {jst_now.hour}時）のためスキップします")
        return

    # 直近240分（4時間）以内に投稿済みならスキップする（1日4回ペースを維持）
    if check_should_skip(skip_minutes=240):
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


def should_post_paid_note_promo(progress):
    """前回の有料note宣伝から7日以上経っていればTrueを返す"""
    last_date_str = progress.get("last_paid_note_promo_date", "")
    if not last_date_str:
        return True
    try:
        last_date = datetime.strptime(last_date_str, "%Y/%m/%d").date()
        today = datetime.now().date()
        return (today - last_date).days >= PAID_NOTE_PROMO_INTERVAL
    except ValueError:
        return True


def pick_random_paid_note(progress):
    """有料noteの中からランダムに1つ選ぶ（直前と同じ記事は避ける）"""
    try:
        with open(PAID_NOTE_PROMO_FILE, "r", encoding="utf-8") as f:
            note_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"⚠️ 有料note一覧の読み込みに失敗: {e}")
        return None

    articles = note_data.get("articles", [])
    if not articles:
        return None

    last_promo = progress.get("last_paid_note_promo_article", "")
    candidates = [a for a in articles if a.get("url") != last_promo]
    if not candidates:
        candidates = articles

    return random.choice(candidates)


def build_paid_note_promo_text(title, url, price):
    """有料note宣伝投稿の文面をテンプレートからランダムに生成する"""
    template = random.choice(PAID_NOTE_PROMO_TEMPLATES)
    short_title = title if len(title) <= 60 else title[:57] + "..."
    return template.format(title=short_title, url=url, price=price)


def post_paid_note_promo(progress, now):
    """有料note宣伝投稿を実行する"""
    note = pick_random_paid_note(progress)
    if note is None:
        print("⚠️ 有料noteが見つからないためスキップ")
        return False

    title = note.get("title", "")
    url = note.get("url", "")
    price = note.get("price", "")
    promo_text = build_paid_note_promo_text(title, url, price)

    print(f"📢 有料note宣伝投稿: 『{title}』（{price}）")
    print(f"🔗 URL: {url}")
    print(f"📝 文字数: {len(promo_text)}")

    print("\n投稿中（有料note宣伝・テキストのみ）...")
    post_id = post_to_threads(promo_text)
    print(f"  ✅ 有料note宣伝投稿成功！（ID: {post_id}）")

    progress["last_paid_note_promo_article"] = url
    progress["last_paid_note_promo_date"] = datetime.now().strftime("%Y/%m/%d")

    if "history" not in progress:
        progress["history"] = []
    progress["history"].append({
        "date": now,
        "theme": f"有料note宣伝: {title[:30]}",
        "theme_id": 0,
        "variant": "paid_note_promo",
        "post_id": post_id
    })

    now_iso = datetime.now(timezone.utc).isoformat()
    save_progress(progress, last_posted_at=now_iso)
    print("=== 完了（有料note宣伝） ===")
    return True


def paid_note_promo_main():
    """有料note宣伝専用のエントリポイント（別ワークフローから呼ばれる）"""
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    print(f"=== 有料note宣伝チェック: {now} ===")

    progress = load_progress()

    if not should_post_paid_note_promo(progress):
        print("⏭️ 前回の宣伝から7日経っていないためスキップ")
        return

    print("📢 有料note宣伝投稿を開始します")
    if post_paid_note_promo(progress, now):
        print("=== 有料note宣伝完了 ===")
    else:
        print("⚠️ 有料note宣伝投稿に失敗しました（次回リトライ）")


def note_promo_main():
    """note宣伝専用のエントリポイント（別ワークフローから呼ばれる）"""
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    print(f"=== note宣伝チェック: {now} ===")

    progress = load_progress()

    if not should_post_note_promo(progress):
        print("⏭️ 前回の宣伝から2日経っていないためスキップ")
        return

    print("📢 note宣伝投稿を開始します")
    if post_note_promo(progress, now):
        now_iso = datetime.now(timezone.utc).isoformat()
        save_progress(progress, last_posted_at=now_iso)
        print("=== note宣伝完了 ===")
    else:
        print("⚠️ note宣伝投稿に失敗しました（次回リトライ）")


if __name__ == "__main__":
    import sys
    if "--bonus" in sys.argv:
        # ボーナス投稿モード（通常4枠とは完全独立・A/Bに触れない）
        bonus_main()
    elif "--paid-note-promo" in sys.argv:
        paid_note_promo_main()
    elif "--note-promo" in sys.argv:
        note_promo_main()
    else:
        main()
