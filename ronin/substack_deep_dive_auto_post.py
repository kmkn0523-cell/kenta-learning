#!/usr/bin/env python3
# substack_deep_dive_auto_post.py
# カード投稿（substack_auto_post.py）の直後に実行し、同じ諺の long-form 記事を Substack に投稿する
# 「今日のカード」を substack_progress.json から特定し、日本語テキストで deep-dive 記事を検索する
# 使い方: python3 substack_deep_dive_auto_post.py

import os                                # パソコンの環境変数を読み込む道具
import re                                # 文字列のパターン検索をする道具
import base64                            # 画像をBase64形式に変換する道具
import json                              # JSONファイルを読み書きする道具
from html.parser import HTMLParser       # HTMLを解析する標準ライブラリ
from urllib.parse import unquote         # URLエンコードを元に戻す道具
from datetime import datetime, timezone  # 日時を扱う道具
from dotenv import load_dotenv           # .envファイルからAPIキーを読み込む道具
from curl_cffi import requests as cf     # ChromeのTLSフィンガープリントを模倣してCloudflare回避

# .envファイルを読み込む
load_dotenv()

# =============================
# 設定
# =============================
SUBSTACK_SID      = os.getenv("SUBSTACK_SID")           # Substackのセッションクッキー
PUBLICATION_URL   = "https://roninwords.substack.com"   # パブリケーションのURL
SCRIPT_DIR        = os.path.dirname(os.path.abspath(__file__))
DEEP_DIVE_JSON    = os.path.join(SCRIPT_DIR, "substack", "substack_deep_dive.json")
PROGRESS_FILE     = os.path.join(SCRIPT_DIR, "substack", "deep_dive_progress.json")
CARD_PROGRESS     = os.path.join(SCRIPT_DIR, "substack", "substack_progress.json")
CARDS_FILE        = os.path.join(SCRIPT_DIR, "generate_ronin_cards.py")
IMAGES_DIR        = os.path.join(SCRIPT_DIR, "ronin_images")  # 書道カード画像フォルダ
MAX_DAY           = 100                                  # カード投稿の総日数


# =============================
# カード進捗ファイルの読み込み
# =============================
def load_card_progress():
    """カード投稿スクリプトが更新した進捗ファイルを読んで「今日のカードDay番号」を返す"""
    with open(CARD_PROGRESS, "r", encoding="utf-8") as f:
        return json.load(f)


# =============================
# カードデータの読み込み（generate_ronin_cards.py から）
# =============================
def load_cards():
    """generate_ronin_cards.py のproverbs定義を解析して day → 日本語諺 の辞書を作る"""
    with open(CARDS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = re.compile(r'\{"day":\s*(\d+),\s*"jp":\s*"([^"]+)"')
    return {int(m.group(1)): m.group(2).strip() for m in pattern.finditer(content)}


# =============================
# deep-dive 記事データの読み込み
# =============================
def load_articles_by_jp():
    """substack_deep_dive.json を読んで 日本語テキスト → 記事データ の辞書を作る"""
    with open(DEEP_DIVE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    # japanese フィールドをキーにする（day番号は使わない）
    return {article["japanese"]: article for article in data["articles"]}


# =============================
# deep-dive 進捗ファイルの読み書き
# =============================
def load_progress():
    """deep-dive 進捗ファイルを読み込む。なければ初期値を返す"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"history": []}


def save_progress(progress):
    """deep-dive 進捗ファイルを更新する"""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def fetch_published_titles(session):
    """Substackの公開記事一覧を全件取得し、公開済みタイトルの集合を返す

    deep-dive記事のタイトルは英語。progress.json（自動同期cron等で巻き戻ることがある）に
    頼らず、Substack本体という確実な情報源で「もう公開した記事」を確認する最終防壁。
    取得に失敗したら例外を投げる（呼び出し側で投稿を見送る判断をする）。
    """
    titles = set()
    offset = 0
    while True:
        resp = session.get(
            f"{PUBLICATION_URL}/api/v1/archive?sort=new&limit=50&offset={offset}"
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"公開記事一覧の取得失敗 [{resp.status_code}]: {resp.text[:200]}"
            )
        batch = resp.json()
        if not batch:
            break
        for post in batch:
            titles.add(post.get("title", "").strip())
        offset += len(batch)
        if len(batch) < 50:
            break
    return titles


# =============================
# 書道カード画像のアップロード
# =============================
def upload_image_to_substack(session, image_path):
    """ローカル画像をBase64でSubstack CDNにアップロードしてCDN URLを返す"""
    print(f"  画像をSubstack CDNにアップロード中: {image_path}", flush=True)

    # 画像ファイルをバイナリで読み込んでBase64文字列に変換する
    with open(image_path, "rb") as f:
        image_data = f.read()

    # "data:image/png;base64,<データ>" という形式に組み立てる
    image_b64 = base64.b64encode(image_data).decode()
    data_uri  = f"data:image/png;base64,{image_b64}"

    # JSONボディとして送る（multipartは不要）
    resp = session.post(
        "https://substack.com/api/v1/image",
        json={"image": data_uri},
    )

    print(f"  画像アップロードレスポンス: {resp.status_code}", flush=True)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"画像アップロード失敗 [{resp.status_code}]: {resp.text[:500]}")

    cdn_url = resp.json().get("url")
    if not cdn_url:
        raise RuntimeError(f"画像アップロード後にURLが取得できませんでした: {resp.text[:500]}")

    print(f"  CDN URL取得: {cdn_url}", flush=True)
    return cdn_url


# =============================
# HTML → ProseMirror JSON 変換
# =============================
class ProseMirrorBuilder(HTMLParser):
    """body_html の要素を Substack が受け取る ProseMirror JSON ノードに変換するパーサ
    対応タグ: h2, p, em, strong, a, hr
    """

    def __init__(self):
        super().__init__()
        self.nodes           = []   # 完成したトップレベルノードのリスト
        self._current_marks  = []   # 現在アクティブなインライン修飾（em / strong / link）
        self._current_inline = []   # 今いる段落内のインラインコンテンツ
        self._in_block       = None # 現在いるブロック要素の種類（"h2" / "p" など）

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "h2":
            self._in_block = "h2"
            self._current_inline = []
        elif tag == "p":
            self._in_block = "p"
            self._current_inline = []
        elif tag == "hr":
            self.nodes.append({"type": "horizontal_rule"})
        elif tag == "em":
            self._current_marks.append({"type": "em"})
        elif tag == "strong":
            self._current_marks.append({"type": "strong"})
        elif tag == "a":
            href = attrs_dict.get("href", "#")
            self._current_marks.append({"type": "link", "attrs": {"href": href}})

    def handle_endtag(self, tag):
        if tag in ("h2", "p"):
            if self._in_block == "h2":
                self.nodes.append({
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": list(self._current_inline)
                })
            elif self._in_block == "p" and self._current_inline:
                self.nodes.append({
                    "type": "paragraph",
                    "attrs": {"textAlign": None},
                    "content": list(self._current_inline)
                })
            self._in_block = None
            self._current_inline = []
        elif tag == "em":
            self._current_marks = [m for m in self._current_marks if m["type"] != "em"]
        elif tag == "strong":
            self._current_marks = [m for m in self._current_marks if m["type"] != "strong"]
        elif tag == "a":
            self._current_marks = [m for m in self._current_marks if m["type"] != "link"]

    def handle_data(self, data):
        if self._in_block and data:
            node = {"type": "text", "text": data}
            if self._current_marks:
                node["marks"] = list(self._current_marks)
            self._current_inline.append(node)


def html_to_prosemirror_nodes(body_html):
    """body_html → ProseMirror ノードリストに変換する（画像ノード追加前の状態）"""
    builder = ProseMirrorBuilder()
    builder.feed(body_html)
    return builder.nodes


# =============================
# Substack への投稿
# =============================
def create_and_publish_post(session, article, card_day):
    """curl_cffi（Chrome TLSフィンガープリント偽装）でドラフト作成 → 公開する"""
    title    = article["title"]
    subtitle = article["subtitle"]

    # 書道カード画像をトップに追加する
    image_path = os.path.join(IMAGES_DIR, f"day{card_day:02d}.png")
    content_nodes = html_to_prosemirror_nodes(article["body_html"])

    if os.path.exists(image_path):
        # 画像をSubstack CDNにアップロードしてCDN URLを取得する
        image_url = upload_image_to_substack(session, image_path)
        # 画像ノードをコンテンツの先頭に挿入する（今まで通り画像トップ）
        image_node = {
            "type": "image",
            "attrs": {
                "src":   image_url,
                "alt":   article.get("japanese", title),
                "title": article.get("japanese", title),
            }
        }
        content_nodes = [image_node] + content_nodes
    else:
        print(f"  画像ファイルが見つかりません（スキップ）: {image_path}", flush=True)

    body_json = json.dumps({"type": "doc", "content": content_nodes}, ensure_ascii=False)

    draft_payload = {
        "draft_title":      title,
        "draft_subtitle":   subtitle,
        "draft_body":       body_json,
        "type":             "newsletter",
        "draft_section_id": None,
        "audience":         "everyone",   # 無料公開
        "draft_bylines":    [{"id": 509075677, "is_guest": False}],
    }

    print(f"  ドラフト作成中...", flush=True)
    draft_resp = session.post(f"{PUBLICATION_URL}/api/v1/drafts", json=draft_payload)
    print(f"  ドラフト作成レスポンス: {draft_resp.status_code}", flush=True)
    if draft_resp.status_code not in (200, 201):
        raise RuntimeError(f"ドラフト作成失敗 [{draft_resp.status_code}]: {draft_resp.text[:500]}")

    post_id = draft_resp.json()["id"]
    print(f"  ドラフトID: {post_id}", flush=True)

    print(f"  公開処理中...", flush=True)
    publish_resp = session.post(
        f"{PUBLICATION_URL}/api/v1/drafts/{post_id}/publish",
        json={"audience": "everyone"},
    )
    print(f"  公開レスポンス: {publish_resp.status_code}", flush=True)
    if publish_resp.status_code not in (200, 201):
        raise RuntimeError(f"公開失敗 [{publish_resp.status_code}]: {publish_resp.text[:500]}")

    return post_id


# =============================
# メイン処理
# =============================
def main():
    # カード投稿の進捗から「今日投稿されたDay番号」を取得する
    # substack_auto_post.py が実行直後なので next_day はすでに +1 されている
    card_progress = load_card_progress()
    card_day = card_progress["next_day"] - 1

    if card_day < 1:
        print("カード投稿がまだ始まっていません。スキップ。", flush=True)
        return
    if card_day > MAX_DAY:
        print(f"全{MAX_DAY}日分のカード投稿が完了しています。deep-dive もスキップ。", flush=True)
        return

    # そのDay の日本語諺を取得する
    cards = load_cards()
    if card_day not in cards:
        print(f"[Card Day {card_day}] generate_ronin_cards.py にデータが見つかりません。スキップ。", flush=True)
        return

    japanese = cards[card_day]
    print(f"[Card Day {card_day}] 今日の諺: {japanese}", flush=True)

    # 対応する deep-dive 記事を日本語テキストで検索する
    articles_by_jp = load_articles_by_jp()
    if japanese not in articles_by_jp:
        print(f"[Card Day {card_day}] {japanese} のdeep-dive記事は存在しません。スキップ。", flush=True)
        return

    article = articles_by_jp[japanese]
    print(f"  タイトル: {article['title']}", flush=True)

    # 重複投稿防止（同じ card_day がすでに履歴にあればスキップ）
    progress = load_progress()
    if any(h.get("card_day") == card_day for h in progress.get("history", [])):
        print(f"[Card Day {card_day}] はすでに投稿済みのためスキップします。", flush=True)
        return

    # 内容ベースの重複防止（同じ諺の記事をすでに別 card_day で投稿していればスキップ）
    # データに同じ諺が別day番号で重複登録されている対策（day番号だけでは弾けないため）
    if any(h.get("japanese") == japanese for h in progress.get("history", [])):
        print(f"[Card Day {card_day}] 諺「{japanese}」は別dayで投稿済みのためスキップします。", flush=True)
        return

    if not SUBSTACK_SID:
        raise ValueError("SUBSTACK_SID が .env に設定されていません")

    sid_decoded = unquote(SUBSTACK_SID)
    session = cf.Session(impersonate="chrome131")
    session.cookies.set("substack.sid", sid_decoded, domain=".substack.com")
    session.headers.update({
        "Origin":  "https://substack.com",
        "Referer": "https://substack.com/publish/post",
    })

    # Substackの公開記事一覧（確実な情報源）で、この記事タイトルが既出ならスキップする
    # progress.jsonが巻き戻っても二重投稿しないための最終防壁。確認できなければ投稿を見送る
    try:
        published_titles = fetch_published_titles(session)
        if article["title"].strip() in published_titles:
            print(f"[Card Day {card_day}] 記事「{article['title']}」はSubstackに公開済みのためスキップします。", flush=True)
            return
    except Exception as error:
        print(f"公開記事一覧を確認できなかったため、今回は投稿を見送ります: {error}", flush=True)
        return

    post_id = create_and_publish_post(session, article, card_day)
    print(f"  公開完了! Post ID: {post_id}", flush=True)

    now = datetime.now(timezone.utc).strftime("%Y/%m/%d %H:%M")
    progress["history"].append({
        "date":     now,
        "card_day": card_day,
        "japanese": japanese,
        "post_id":  post_id,
        "title":    article["title"],
    })
    save_progress(progress)

    print(f"[Card Day {card_day}] 完了。", flush=True)


if __name__ == "__main__":
    main()
