# ronin_reply_review_ui.py
# ronin リプライ運用者ビュー（App Review スクリーンキャスト用・人が確認して送るUI）
# ねらい: keyword_search で集めた英語の公開投稿を一覧表示し、運用者が関連性を確認したうえで
#         1件ずつ返信を送る「半自動」の画面。全自動cron（ronin_reply_engine.py）とは別物。
# ★skin_reply_review_ui.py の @RoninWords 版（英語アカウント・別トークン・別ポート）。
# 使い方:
#   通常モード（実際にThreads APIで検索・送信する。トークンが必要）:
#       cd ronin && python3 ronin_reply_review_ui.py
#   デモモード（トークン不要。サンプル投稿でUIの流れだけ確認・録画できる）:
#       cd ronin && python3 ronin_reply_review_ui.py --demo
#   起動したらブラウザで http://127.0.0.1:8766 を開く。
# ★標準ライブラリだけで動く（新しいライブラリは入れない）。

import os        # 環境変数（トークン）を読む道具
import sys       # 起動オプション（--demo）を読む道具
import random    # 返信文の合成に使う道具
import html      # 画面に出す文字を安全に整える（HTMLエスケープ）道具
import urllib.parse  # URLのクエリ・フォームデータを解く道具
from http.server import BaseHTTPRequestHandler, HTTPServer  # 簡易Webサーバの道具

# エンジン本体の純粋関数を再利用する（検索・分類・返信文合成）。本体は変更しない。
from ronin_reply_engine import (
    search_recent_posts,   # keyword_search を叩いて投稿リストを取る
    classify_category,     # 投稿本文からテンプレのカテゴリを判定する
    compose_reply,         # カテゴリに合う返信文を合成する
    load_config,           # キーワード・上限などの設定を読む
)

# 起動オプション: --demo が付いていればデモモード（APIを叩かずサンプルで動く）
DEMO_MODE = "--demo" in sys.argv

# 画面を開くポート番号（skin版=8765 とかぶらないように 8766）
PORT = 8766

# デモモード用のサンプル投稿（英語・stoic/disciplineテーマ。トークン無しでUIを見せるため）
SAMPLE_POSTS = [
    {"id": "demo1", "text": "I keep failing to stay consistent. Every time I build a routine I quit after a week. How do you keep discipline?",
     "author": "user_marcus", "timestamp": "2026-06-16T11:20:00+0000"},
    {"id": "demo2", "text": "Stoicism changed how I handle anxiety. Focusing only on what I can control made me calmer.",
     "author": "user_sen", "timestamp": "2026-06-16T10:05:00+0000"},
    {"id": "demo3", "text": "Still searching for my purpose. Some days the lack of direction feels heavy.",
     "author": "user_kai", "timestamp": "2026-06-16T09:40:00+0000"},
    {"id": "demo4", "text": "Nice weather today, going for a walk.",  # わざと無関係（分類Noneの例）
     "author": "user_sky", "timestamp": "2026-06-16T08:00:00+0000"},
]


def fetch_posts(keyword):
    """キーワードで投稿を集めて返す。デモモードならサンプルを、通常モードならAPIを使う。"""
    if DEMO_MODE:
        # デモではキーワードに関係なく固定サンプルを返す（UIの流れを見せるのが目的）
        return list(SAMPLE_POSTS)
    # 通常モード: ronin専用トークンで実際に keyword_search を叩く
    token = os.environ.get("RONIN_THREADS_ACCESS_TOKEN") or os.environ.get("THREADS_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("RONIN_THREADS_ACCESS_TOKEN が未設定です。.env を読み込んで起動してください。")
    return search_recent_posts(keyword, token)


def build_suggestion(post_text):
    """投稿本文を見て、テンプレから返信文の下書きを1件作って返す。"""
    rng = random.Random()                      # 返信文をランダムに選ぶための道具
    category = classify_category(post_text)    # どのテーマの投稿かを判定
    reply = compose_reply(category, [], rng)   # そのテーマに合う返信文を合成
    category_name = "汎用（テーマ判定なし）" if category is None else f"カテゴリ{category}"
    return category_name, reply


def render_page(keyword="", posts=None, message=""):
    """検索フォームと結果一覧のHTMLを組み立てて文字列で返す。"""
    posts = posts or []  # postsがNoneなら空リストにする

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

    banner = f'<div class="banner">{html.escape(message)}</div>' if message else ""
    demo_note = '<div class="demo">DEMOモード: サンプル投稿を表示しています（API送信は実行されません）</div>' if DEMO_MODE else ""
    safe_keyword = html.escape(keyword)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ronin リプライ運用者ビュー</title>
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
  <h1>ronin リプライ運用者ビュー（@RoninWords）</h1>
  {demo_note}
  {banner}
  <form class="search" method="GET" action="/">
    <input type="text" name="q" value="{safe_keyword}" placeholder="keyword (e.g. discipline / stoicism / purpose)">
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
        if parsed.path != "/":
            self._write_html("<p>not found</p>", status=404)
            return
        query = urllib.parse.parse_qs(parsed.query)
        keyword = (query.get("q", [""])[0]).strip()
        posts = []
        message = ""
        if keyword:
            try:
                posts = fetch_posts(keyword)
            except Exception as error:
                message = f"検索できませんでした: {error}"
        self._write_html(render_page(keyword=keyword, posts=posts, message=message))

    def do_POST(self):
        """返信送信ボタンが押されたときの処理。確認後に1件だけ送る。"""
        if self.path != "/send":
            self._write_html("<p>not found</p>", status=404)
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")
        form = urllib.parse.parse_qs(raw)
        post_id = (form.get("post_id", [""])[0]).strip()
        reply_text = (form.get("reply_text", [""])[0]).strip()
        author = (form.get("author", [""])[0]).strip()

        if DEMO_MODE:
            message = f"[DEMO] @{author} への返信を送信したつもりです（実送信なし）: {reply_text[:30]}…"
        elif not reply_text or not post_id:
            message = "返信文または対象IDが空です。送信を中止しました。"
        else:
            try:
                # 実送信は既存スクリプトを再利用（env必須なので遅延import）
                from ronin_threads_action import post_to_threads
                post_to_threads(reply_text, reply_to_id=post_id)
                message = f"@{author} に返信を送信しました。"
            except Exception as error:
                message = f"送信に失敗しました: {error}"

        self._write_html(render_page(message=message))

    def log_message(self, *args):
        """標準のアクセスログは出さない（画面がうるさくならないように）。"""
        return


def main():
    """サーバを起動する。Ctrl+C で止める。"""
    mode = "DEMOモード（API送信なし）" if DEMO_MODE else "通常モード（実際にThreads APIを使用）"
    print(f"ronin リプライ運用者ビューを起動しました [{mode}]")
    print(f"ブラウザで http://127.0.0.1:{PORT} を開いてください（停止: Ctrl+C）")
    if not DEMO_MODE:
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
