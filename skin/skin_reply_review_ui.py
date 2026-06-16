# skin_reply_review_ui.py
# skin リプライ運用者ビュー（App Review スクリーンキャスト用・人が確認して送るUI）
# ねらい: keyword_search で集めた公開投稿を一覧表示し、運用者が関連性を確認したうえで
#         1件ずつ返信を送る「半自動」の画面。全自動cron（skin_reply_engine.py）とは別物。
# 使い方:
#   通常モード（実際にThreads APIで検索・送信する。トークンが必要）:
#       cd skin && python3 skin_reply_review_ui.py
#   デモモード（トークン不要。サンプル投稿でUIの流れだけ確認・録画できる）:
#       cd skin && python3 skin_reply_review_ui.py --demo
#   起動したらブラウザで http://127.0.0.1:8765 を開く。
# ★標準ライブラリだけで動く（新しいライブラリは入れない）。

import os        # 環境変数（トークン）を読む道具
import sys       # 起動オプション（--demo）を読む道具
import json      # フォーム送信値の受け渡しに使う道具
import random    # 返信文の合成に使う道具
import html      # 画面に出す文字を安全に整える（HTMLエスケープ）道具
import urllib.parse  # URLのクエリ・フォームデータを解く道具
from http.server import BaseHTTPRequestHandler, HTTPServer  # 簡易Webサーバの道具

# エンジン本体の純粋関数を再利用する（検索・分類・返信文合成）。本体は変更しない。
from skin_reply_engine import (
    search_recent_posts,   # keyword_search を叩いて投稿リストを取る
    classify_category,     # 投稿本文からテンプレのカテゴリを判定する
    compose_reply,         # カテゴリに合う返信文を合成する
    load_config,           # キーワード・上限などの設定を読む
)

# 起動オプション: --demo が付いていればデモモード（APIを叩かずサンプルで動く）
DEMO_MODE = "--demo" in sys.argv

# 画面を開くポート番号（他とかぶらない値）
PORT = 8765

# デモモード用のサンプル投稿（実際の検索結果に似せた形。トークン無しでUIを見せるため）
SAMPLE_POSTS = [
    {"id": "demo1", "text": "繰り返す大人ニキビが本当につらい。高い化粧品を試してもダメで心が折れそう。",
     "author": "user_aoi", "timestamp": "2026-06-16T11:20:00+0000"},
    {"id": "demo2", "text": "腸活を始めて2週間、発酵食品を毎日とるようにしたら便通も肌も変わってきた気がする。",
     "author": "user_haru", "timestamp": "2026-06-16T10:05:00+0000"},
    {"id": "demo3", "text": "睡眠を23時就寝に変えたら朝の肌の調子が違う。やっぱり生活習慣って大事なんだな。",
     "author": "user_mei", "timestamp": "2026-06-16T09:40:00+0000"},
    {"id": "demo4", "text": "今日はいい天気。散歩してきます。",  # わざと無関係（分類Noneの例）
     "author": "user_sora", "timestamp": "2026-06-16T08:00:00+0000"},
]


def fetch_posts(keyword):
    """キーワードで投稿を集めて返す。デモモードならサンプルを、通常モードならAPIを使う。"""
    if DEMO_MODE:
        # デモではキーワードに関係なく固定サンプルを返す（UIの流れを見せるのが目的）
        return list(SAMPLE_POSTS)
    # 通常モード: 環境変数のトークンで実際に keyword_search を叩く
    token = os.environ.get("THREADS_ACCESS_TOKEN")
    if not token:
        # トークンが無ければ空＋ヒントを呼び出し側で出す
        raise RuntimeError("THREADS_ACCESS_TOKEN が未設定です。.env を読み込んで起動してください。")
    return search_recent_posts(keyword, token)


def build_suggestion(post_text):
    """投稿本文を見て、テンプレから返信文の下書きを1件作って返す。"""
    rng = random.Random()                      # 返信文をランダムに選ぶための道具
    category = classify_category(post_text)    # どのテーマの投稿かを判定
    reply = compose_reply(category, [], rng)   # そのテーマに合う返信文を合成
    # カテゴリ名（人が読める形）も一緒に返す。Noneなら「汎用」と表示
    category_name = "汎用（テーマ判定なし）" if category is None else f"カテゴリ{category}"
    return category_name, reply


def render_page(keyword="", posts=None, message=""):
    """検索フォームと結果一覧のHTMLを組み立てて文字列で返す。"""
    posts = posts or []  # postsがNoneなら空リストにする

    # 1件ごとのカード（投稿＋下書き返信＋送信ボタン）を作る
    cards = ""
    for post in posts:
        category_name, suggestion = build_suggestion(post.get("text", ""))
        # 画面に出す値はすべてHTMLエスケープして安全にする
        safe_author = html.escape(post.get("author") or "（不明）")
        safe_text = html.escape(post.get("text") or "")
        safe_time = html.escape(post.get("timestamp") or "")
        safe_id = html.escape(post.get("id") or "")
        safe_reply = html.escape(suggestion)
        safe_cat = html.escape(category_name)
        # 1枚のカードHTML。返信文はtextareaで編集できる。送信は /send にPOSTする。
        cards += f"""
        <div class="card">
          <div class="meta">@{safe_author} ・ <span class="time">{safe_time}</span> ・ <span class="tag">{safe_cat}</span></div>
          <div class="post">{safe_text}</div>
          <form method="POST" action="/send">
            <input type="hidden" name="post_id" value="{safe_id}">
            <input type="hidden" name="author" value="{safe_author}">
            <label class="lbl">返信（送信前に確認・編集できます）</label>
            <textarea name="reply_text" rows="3">{safe_reply}</textarea>
            <button type="submit">この内容で返信を送る</button>
          </form>
        </div>"""

    if not posts:
        cards = '<p class="empty">検索するとここに公開投稿が並びます。</p>'

    # 画面上部に出すお知らせ（送信結果など）
    banner = f'<div class="banner">{html.escape(message)}</div>' if message else ""
    # デモモードの注意書き
    demo_note = '<div class="demo">DEMOモード: サンプル投稿を表示しています（API送信は実行されません）</div>' if DEMO_MODE else ""

    safe_keyword = html.escape(keyword)
    # 全体のHTML。スクリーンキャストで見やすいよう最低限のCSSを入れる。
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>skin リプライ運用者ビュー</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", sans-serif; max-width: 720px; margin: 0 auto; padding: 24px; color: #222; background: #fafafa; }}
  h1 {{ font-size: 20px; }}
  .demo {{ background: #fff3cd; border: 1px solid #ffe69c; padding: 8px 12px; border-radius: 8px; margin-bottom: 12px; font-size: 13px; }}
  .banner {{ background: #d1e7dd; border: 1px solid #a3cfbb; padding: 10px 12px; border-radius: 8px; margin-bottom: 12px; }}
  form.search {{ display: flex; gap: 8px; margin-bottom: 20px; }}
  form.search input[type=text] {{ flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 8px; font-size: 15px; }}
  form.search button {{ padding: 10px 16px; border: 0; border-radius: 8px; background: #0d6efd; color: #fff; font-size: 15px; cursor: pointer; }}
  .card {{ background: #fff; border: 1px solid #e5e5e5; border-radius: 12px; padding: 16px; margin-bottom: 14px; }}
  .meta {{ font-size: 12px; color: #666; margin-bottom: 6px; }}
  .tag {{ background: #eef; color: #335; padding: 1px 8px; border-radius: 6px; }}
  .post {{ font-size: 15px; line-height: 1.6; margin-bottom: 10px; white-space: pre-wrap; }}
  .lbl {{ font-size: 12px; color: #666; display: block; margin-bottom: 4px; }}
  textarea {{ width: 100%; box-sizing: border-box; padding: 8px; border: 1px solid #ccc; border-radius: 8px; font-size: 14px; }}
  .card button {{ margin-top: 8px; padding: 8px 14px; border: 0; border-radius: 8px; background: #198754; color: #fff; cursor: pointer; }}
  .empty {{ color: #888; }}
  .time {{ color: #999; }}
</style>
</head>
<body>
  <h1>skin リプライ運用者ビュー</h1>
  {demo_note}
  {banner}
  <form class="search" method="GET" action="/">
    <input type="text" name="q" value="{safe_keyword}" placeholder="キーワード（例: 腸活 / 大人ニキビ / インナーケア）">
    <button type="submit">検索</button>
  </form>
  {cards}
</body>
</html>"""


class ReviewHandler(BaseHTTPRequestHandler):
    """ブラウザからのアクセスを処理する係。検索(GET)と送信(POST)を担当する。"""

    def _write_html(self, body, status=200):
        """HTML文字列をブラウザに返す共通処理。"""
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        """検索フォームの表示と、キーワード検索の結果表示。"""
        parsed = urllib.parse.urlparse(self.path)
        # トップ以外（favicon等）は空応答で軽くいなす
        if parsed.path != "/":
            self._write_html("<p>not found</p>", status=404)
            return
        query = urllib.parse.parse_qs(parsed.query)  # ?q=... を辞書にする
        keyword = (query.get("q", [""])[0]).strip()
        posts = []
        message = ""
        if keyword:
            try:
                posts = fetch_posts(keyword)
            except Exception as error:
                # 検索に失敗（トークン無し・権限不足など）したら画面に理由を出す
                message = f"検索できませんでした: {error}"
        self._write_html(render_page(keyword=keyword, posts=posts, message=message))

    def do_POST(self):
        """返信送信ボタンが押されたときの処理。確認後に1件だけ送る。"""
        if self.path != "/send":
            self._write_html("<p>not found</p>", status=404)
            return
        length = int(self.headers.get("Content-Length", 0))         # 本文の長さ
        raw = self.rfile.read(length).decode("utf-8")               # フォーム本文を読む
        form = urllib.parse.parse_qs(raw)                           # 値を辞書にする
        post_id = (form.get("post_id", [""])[0]).strip()
        reply_text = (form.get("reply_text", [""])[0]).strip()
        author = (form.get("author", [""])[0]).strip()

        if DEMO_MODE:
            # デモでは実際に送らず、送ったつもりのメッセージだけ出す
            message = f"[DEMO] @{author} への返信を送信したつもりです（実送信なし）: {reply_text[:30]}…"
        elif not reply_text or not post_id:
            message = "返信文または対象IDが空です。送信を中止しました。"
        else:
            try:
                # 実送信は既存スクリプトを再利用（env必須なので遅延import）
                from skin_threads_action import post_to_threads
                post_to_threads(reply_text, reply_to_id=post_id)
                message = f"@{author} に返信を送信しました。"
            except Exception as error:
                message = f"送信に失敗しました: {error}"

        # 送信後はトップに結果メッセージ付きで戻す
        self._write_html(render_page(message=message))

    def log_message(self, *args):
        """標準のアクセスログは出さない（画面がうるさくならないように）。"""
        return


def main():
    """サーバを起動する。Ctrl+C で止める。"""
    mode = "DEMOモード（API送信なし）" if DEMO_MODE else "通常モード（実際にThreads APIを使用）"
    print(f"skin リプライ運用者ビューを起動しました [{mode}]")
    print(f"ブラウザで http://127.0.0.1:{PORT} を開いてください（停止: Ctrl+C）")
    if not DEMO_MODE:
        # 通常モードで使う設定が読めるか軽く確認（キーワード候補を案内）
        try:
            config = load_config()
            print("検索キーワード候補:", " / ".join(config.get("keywords", [])))
        except Exception as error:
            print(f"設定の読み込み注意: {error}")
    server = HTTPServer(("127.0.0.1", PORT), ReviewHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止しました。")
        server.server_close()


if __name__ == "__main__":
    main()
