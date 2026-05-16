# substack_auto_post.py
# 書道カード画像 + 諺テキストを Substack に自動投稿するスクリプト
# curl_cffi: Chrome の TLS フィンガープリントを完全に再現して Cloudflare を回避する
# 使い方: python3 substack_auto_post.py

import os           # パソコンの環境変数を読み込む道具
import re           # 文字列のパターン検索をする道具
import json         # JSONファイルを読み書きする道具
from urllib.parse import unquote         # URLエンコードを元に戻す道具
from datetime import datetime, timezone  # 日時を扱う道具
from dotenv import load_dotenv           # .envファイルからAPIキーを読み込む道具
from curl_cffi import requests as cf     # ChromeのTLSフィンガープリントを模倣してCloudflare回避

# .envファイルを読み込む
load_dotenv()

# =============================
# 設定
# =============================
SUBSTACK_SID     = os.getenv("SUBSTACK_SID")          # Substackのセッションクッキー
PUBLICATION_URL  = "https://roninwords.substack.com"  # パブリケーションのURL
# GitHub Pages の画像ベースURL（Substack CDNへのアップロードはCloudflareでブロックされるため）
GITHUB_PAGES_BASE = "https://kmkn0523-cell.github.io/kenta-learning/ronin/ronin_images"
SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR       = os.path.join(SCRIPT_DIR, "ronin_images")
CARDS_FILE       = os.path.join(SCRIPT_DIR, "generate_ronin_cards.py")   # 画像と1対1で対応するデータ
PROVERBS_FILE    = os.path.join(SCRIPT_DIR, "ronin_words_proverbs_100.md")  # 説明文を取得するために使う
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
def parse_explanations():
    """ronin_words_proverbs_100.md から「日本語 → 説明文」の辞書を作る"""
    with open(PROVERBS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    explanations = {}
    # 行のパターン: 「1. **七転び八起き** *Nana korobi ya oki* — Fall seven times...」
    pattern = re.compile(r'^\d+\.\s+\*\*([^*]+)\*\*')

    for i, line in enumerate(lines):
        match = pattern.match(line.strip())
        if match:
            japanese = match.group(1).strip()
            # 次の行から説明文（> で始まる行）を探す
            for j in range(i + 1, min(i + 6, len(lines))):
                stripped = lines[j].strip()
                if stripped.startswith(">"):
                    explanations[japanese] = stripped[1:].strip()
                    break

    return explanations


def parse_proverbs():
    """generate_ronin_cards.py の proverbs リストを解析して day番号 → 諺データの辞書を返す

    このファイルが画像ファイル(dayXX.png)と1対1で対応している正しいマッピング。
    """
    with open(CARDS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Python辞書の各行を正規表現で抽出する
    # 例: {"day":  1, "jp": "一期一会", "roma": "Ichi go ichi e", "en": "..."}
    pattern = re.compile(
        r'\{"day":\s*(\d+),\s*"jp":\s*"([^"]+)",\s*"roma":\s*"([^"]+)",\s*"en":\s*"([^"]+)"\}'
    )

    # 説明文は ronin_words_proverbs_100.md から日本語テキストで引く
    explanations = parse_explanations()

    proverbs = {}
    for match in pattern.finditer(content):
        day      = int(match.group(1))
        japanese = match.group(2).strip()
        romanji  = match.group(3).strip()
        english  = match.group(4).strip()

        proverbs[day] = {
            "japanese":    japanese,
            "romanji":     romanji,
            "english":     english,
            "explanation": explanations.get(japanese, ""),  # 一致する説明文がなければ空欄
        }

    return proverbs


# =============================
# 記事本文の組み立て
# =============================
def build_post_body(proverb, image_url):
    """記事の本文をSubstack用のProseMirror JSON形式で組み立てる"""
    # Substack の draft_body は ProseMirror JSON（エディタの内部形式）を文字列で渡す必要がある
    # type="image" のノードに src/alt を設定すると画像として正しく表示される
    japanese    = proverb["japanese"]
    romanji     = proverb["romanji"]
    english     = proverb["english"]
    explanation = proverb["explanation"]

    doc = {
        "type": "doc",
        "content": [
            # 書道カード画像
            {
                "type": "image",
                "attrs": {
                    "src":   image_url,
                    "alt":   japanese,
                    "title": japanese,
                }
            },
            # 漢字（太字）＋ 読み方（斜体）
            {
                "type": "paragraph",
                "attrs": {"textAlign": None},
                "content": [
                    {"type": "text", "marks": [{"type": "strong"}], "text": japanese},
                    {"type": "hardBreak"},
                    {"type": "text", "marks": [{"type": "em"}],     "text": romanji},
                ]
            },
            # 英語訳
            {
                "type": "paragraph",
                "attrs": {"textAlign": None},
                "content": [{"type": "text", "text": english}]
            },
            # 説明文
            {
                "type": "paragraph",
                "attrs": {"textAlign": None},
                "content": [{"type": "text", "text": explanation}]
            },
            # 署名
            {
                "type": "paragraph",
                "attrs": {"textAlign": None},
                "content": [
                    {"type": "text", "marks": [{"type": "em"}], "text": "— RoninWords"}
                ]
            },
        ]
    }
    # ProseMirror JSON は文字列として渡す
    return json.dumps(doc, ensure_ascii=False)


# =============================
# curl_cffi で Substack に投稿
# =============================
def create_and_publish_post(proverb, image_url):
    """curl_cffi（Chrome TLSフィンガープリント偽装）でSubstackに記事を作成・公開する

    curl_cffi は requests ライクなAPIで curl-impersonate をバックエンドに使う。
    impersonate="chrome124" でTLSハンドシェイク・HTTP/2フレームをChromeと完全一致させ、
    Cloudflare のフィンガープリント検知を回避する。
    """
    if not SUBSTACK_SID:
        raise ValueError("SUBSTACK_SID が .env に設定されていません")

    title     = f"{proverb['japanese']} — {proverb['english']}"
    body_json = build_post_body(proverb, image_url)

    # substack.sid クッキーのURLエンコードを解除する
    sid_decoded = unquote(SUBSTACK_SID)

    # ChromeのTLSフィンガープリントを使ってリクエストを送るセッションを作る
    session = cf.Session(impersonate="chrome124")

    # substack.sid クッキーをセットする
    session.cookies.set("substack.sid", sid_decoded, domain=".substack.com")

    # =============================
    # Step 1: ドラフトを作成する
    # =============================
    draft_payload = {
        "draft_title":      title,
        "draft_body":       body_json,
        "draft_subtitle":   "",
        "type":             "newsletter",
        "draft_section_id": None,
        "audience":         "everyone",  # 全員（無料）公開
        "draft_bylines":    [{"id": 509075677, "is_guest": False}],
    }

    print(f"  ドラフト作成中...", flush=True)
    draft_resp = session.post(
        f"{PUBLICATION_URL}/api/v1/drafts",
        json=draft_payload,
    )

    print(f"  ドラフト作成レスポンス: {draft_resp.status_code}", flush=True)
    if draft_resp.status_code not in (200, 201):
        raise RuntimeError(
            f"ドラフト作成失敗 [{draft_resp.status_code}]: {draft_resp.text[:500]}"
        )

    post    = draft_resp.json()
    post_id = post["id"]
    print(f"  ドラフトID: {post_id}", flush=True)

    # =============================
    # Step 2: ドラフトを公開する
    # =============================
    print(f"  公開処理中...", flush=True)
    publish_resp = session.post(
        f"{PUBLICATION_URL}/api/v1/drafts/{post_id}/publish",
        json={"audience": "everyone"},
    )

    print(f"  公開レスポンス: {publish_resp.status_code}", flush=True)
    if publish_resp.status_code not in (200, 201):
        raise RuntimeError(
            f"公開失敗 [{publish_resp.status_code}]: {publish_resp.text[:500]}"
        )

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

    print(f"[Day {day}] 投稿開始: {proverb['japanese']}", flush=True)

    # GitHub Pages の画像URL を直接使う（Substack CDNへのアップロードはCloudflareでブロックされるため）
    image_url = f"{GITHUB_PAGES_BASE}/day{day:02d}.png"
    print(f"  画像URL: {image_url}", flush=True)

    # 記事を作成して公開する（curl_cffi経由）
    title = f"{proverb['japanese']} — {proverb['english']}"
    print(f"  記事を公開中: {title}", flush=True)
    post_id = create_and_publish_post(proverb, image_url)
    print(f"  公開完了! Post ID: {post_id}", flush=True)

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

    print(f"[Day {day}] 完了。次回は Day {day + 1} を投稿します。", flush=True)


if __name__ == "__main__":
    main()
