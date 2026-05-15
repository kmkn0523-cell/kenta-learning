# substack_auto_post.py
# 書道カード画像 + 諺テキストを Substack に自動投稿するスクリプト
# 使い方: python3 substack_auto_post.py

import os           # パソコンの環境変数を読み込む道具
import re           # 文字列のパターン検索をする道具
import json         # JSONファイルを読み書きする道具
import requests     # インターネットにリクエストを送る道具
from datetime import datetime, timezone  # 日時を扱う道具
from dotenv import load_dotenv           # .envファイルからAPIキーを読み込む道具

# .envファイルを読み込む
load_dotenv()

# =============================
# 設定
# =============================
SUBSTACK_SID     = os.getenv("SUBSTACK_SID")       # Substackのセッションクッキー
PUBLICATION_URL  = "https://roninwords.substack.com"  # パブリケーションのURL
SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR       = os.path.join(SCRIPT_DIR, "ronin_images")
PROVERBS_FILE    = os.path.join(SCRIPT_DIR, "ronin_words_proverbs_100.md")
PROGRESS_FILE    = os.path.join(SCRIPT_DIR, "substack", "substack_progress.json")
MAX_DAY          = 100  # 総日数


# =============================
# 進捗ファイルの読み書き
# =============================
def load_progress():
    """今日は何日目を投稿するか、進捗ファイルから読み込む"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # 初回実行時はゼロスタート
    return {"next_day": 1, "history": []}


def save_progress(progress):
    """投稿完了後に進捗ファイルを更新する"""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# =============================
# 諺データの解析
# =============================
def parse_proverbs():
    """ronin_words_proverbs_100.md から全諺データを辞書として返す"""
    with open(PROVERBS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    proverbs = {}
    # 行のパターン: 「1. **七転び八起き** *Nana korobi ya oki* — Fall seven times...」
    pattern = re.compile(r'^(\d+)\.\s+\*\*([^*]+)\*\*\s+\*([^*]+)\*\s+—\s+(.+)$')

    for i, line in enumerate(lines):
        match = pattern.match(line.strip())
        if match:
            num        = int(match.group(1))
            japanese   = match.group(2).strip()
            romanji    = match.group(3).strip()
            english    = match.group(4).strip()

            # 次の行から説明文（> で始まる行）を探す
            explanation = ""
            for j in range(i + 1, min(i + 6, len(lines))):
                stripped = lines[j].strip()
                if stripped.startswith(">"):
                    explanation = stripped[1:].strip()
                    break

            proverbs[num] = {
                "japanese":    japanese,
                "romanji":     romanji,
                "english":     english,
                "explanation": explanation,
            }

    return proverbs


# =============================
# Substack API 操作
# =============================
def get_session():
    """Substackの認証情報を持ったセッションを作る"""
    if not SUBSTACK_SID:
        raise ValueError("SUBSTACK_SID が .env に設定されていません")

    session = requests.Session()
    # substack.sid クッキーをセットして認証する
    session.cookies.set("substack.sid", SUBSTACK_SID, domain=".substack.com")
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Origin":     "https://substack.com",
        "Referer":    "https://substack.com/",
    })
    return session


def upload_image(session, image_path):
    """画像を Substack の CDN にアップロードして URL を返す"""
    with open(image_path, "rb") as f:
        response = session.post(
            "https://substack.com/api/v1/image",
            files={"image": ("image.png", f, "image/png")},
        )

    if response.status_code != 200:
        raise RuntimeError(f"画像アップロード失敗 [{response.status_code}]: {response.text}")

    data = response.json()
    # レスポンスの形式に応じてURLを取り出す
    url = data.get("url") or data.get("image_url") or data.get("uri")
    if not url:
        raise RuntimeError(f"画像URLが取得できませんでした: {data}")
    return url


def build_post_html(proverb, image_url):
    """記事のHTML本文を組み立てる"""
    japanese    = proverb["japanese"]
    romanji     = proverb["romanji"]
    english     = proverb["english"]
    explanation = proverb["explanation"]

    html = (
        f'<div class="captioned-image-container">'
        f'<figure><img src="{image_url}" alt="{japanese}"></figure>'
        f'</div>'
        f'<p><strong>{japanese}</strong><br>'
        f'<em>{romanji}</em></p>'
        f'<p>{english}</p>'
        f'<p>{explanation}</p>'
        f'<p>— <em>RoninWords</em></p>'
    )
    return html


def create_and_publish_post(session, title, body_html):
    """Substack に記事を作成して無料公開する（2ステップ）"""
    # Step 1: ドラフトを作成する
    draft_payload = {
        "draft_title":      title,
        "draft_body":       body_html,
        "draft_subtitle":   "",
        "type":             "newsletter",
        "draft_section_id": None,
        "audience":         "everyone",  # 全員（無料）公開
    }
    resp = session.post(
        f"{PUBLICATION_URL}/api/v1/posts",
        json=draft_payload,
        headers={"Content-Type": "application/json"},
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"ドラフト作成失敗 [{resp.status_code}]: {resp.text}")

    post     = resp.json()
    post_id  = post["id"]

    # Step 2: ドラフトを公開する
    publish_payload = {
        "draft":    False,
        "audience": "everyone",
    }
    resp2 = session.put(
        f"{PUBLICATION_URL}/api/v1/posts/{post_id}",
        json=publish_payload,
        headers={"Content-Type": "application/json"},
    )
    if resp2.status_code not in (200, 201):
        raise RuntimeError(f"公開失敗 [{resp2.status_code}]: {resp2.text}")

    return post_id


# =============================
# メイン処理
# =============================
def main():
    progress = load_progress()
    day = progress["next_day"]

    if day > MAX_DAY:
        print(f"全{MAX_DAY}日分の投稿が完了しています。")
        return

    # 諺データを読み込む
    proverbs = parse_proverbs()
    if day not in proverbs:
        raise RuntimeError(f"Day {day} のデータが見つかりません")

    proverb    = proverbs[day]
    image_path = os.path.join(IMAGES_DIR, f"day{day:02d}.png")

    if not os.path.exists(image_path):
        raise RuntimeError(f"画像ファイルが見つかりません: {image_path}")

    print(f"[Day {day}] 投稿開始: {proverb['japanese']}")

    # セッションを作る
    session = get_session()

    # 画像をアップロードする
    print(f"  画像をアップロード中: {image_path}")
    image_url = upload_image(session, image_path)
    print(f"  アップロード完了: {image_url}")

    # 記事タイトルと本文を組み立てる
    title     = f"{proverb['japanese']} — {proverb['english']}"
    body_html = build_post_html(proverb, image_url)

    # 記事を作成して公開する
    print(f"  記事を公開中: {title}")
    post_id = create_and_publish_post(session, title, body_html)
    print(f"  公開完了! Post ID: {post_id}")

    # 進捗を保存する（次回は day+1 から投稿する）
    now = datetime.now(timezone.utc).strftime("%Y/%m/%d %H:%M")
    progress["history"].append({
        "date":    now,
        "day":     day,
        "post_id": post_id,
        "title":   title,
    })
    progress["next_day"] = day + 1
    save_progress(progress)

    print(f"[Day {day}] 完了。次回は Day {day + 1} を投稿します。")


if __name__ == "__main__":
    main()
