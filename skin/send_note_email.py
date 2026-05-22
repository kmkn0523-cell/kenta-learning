# send_note_email.py
# note.com への自動投稿の結果をメールで通知するスクリプト
# GitHub Actions の post_to_note.py のあとに呼び出される。
#
# 成功時: 公開URL・タイトル・記事番号をメールで通知
# 失敗時: エラー内容と「スクリーンショットを確認してください」案内を通知
#
# 必要な環境変数:
#   - GMAIL_APP_PASSWORD: Gmailアプリパスワード（GitHub Secrets）

import os                                  # 環境変数を読み取る道具
import json                                # 進捗JSONを読む道具
import smtplib                             # メール送信する道具
from email.mime.text import MIMEText       # メール本文を作る道具
from email.mime.multipart import MIMEMultipart  # メール全体を組み立てる道具

# ファイルパスを定義する
BASE_DIR = os.path.dirname(__file__)                                       # skinフォルダ
PROGRESS_FILE = os.path.join(BASE_DIR, "note_queue_progress.json")        # 進捗ファイル

# 送信先と差出人（どちらも自分のGmail）
MAIL_FROM = "kmkn0523@gmail.com"
MAIL_TO = "kmkn0523@gmail.com"


def load_latest_history():
    """note_queue_progress.json の history 配列の最新エントリを返す（無ければNone）"""
    if not os.path.exists(PROGRESS_FILE):
        return None
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            progress = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

    history = progress.get("history", [])
    if not history:
        return None
    # 配列の末尾が最新（post_to_note.py が append しているため）
    return history[-1]


def build_success_mail(latest):
    """投稿成功時のメール件名・本文を組み立てる"""
    title = latest.get("title", "(タイトル不明)")
    article = latest.get("article", "(記事ファイル不明)")
    post_url = latest.get("post_url", "(URL不明)")
    date = latest.get("date", "")

    subject = f"【skin note 自動投稿成功】{title}"

    plain_body = (
        f"note.com への自動投稿が完了しました。\n\n"
        f"記事: {article}\n"
        f"タイトル: {title}\n"
        f"投稿日時: {date}\n"
        f"公開URL: {post_url}\n"
    )

    html_body = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ font-family: sans-serif; font-size: 16px; line-height: 1.8; max-width: 680px; margin: 0 auto; padding: 16px; }}
.box {{ background: #e8ffe8; border-radius: 12px; padding: 18px; margin-bottom: 16px; }}
.box a {{ color: #0066cc; font-weight: bold; font-size: 17px; word-break: break-all; }}
.label {{ color: #666; font-size: 13px; }}
</style></head><body>
<div class="box">
<p><strong>✅ note.com 自動投稿成功</strong></p>
<p><span class="label">記事:</span> {article}</p>
<p><span class="label">タイトル:</span> {title}</p>
<p><span class="label">投稿日時:</span> {date}</p>
<p><span class="label">公開URL:</span><br><a href="{post_url}">{post_url}</a></p>
</div>
</body></html>"""

    return subject, plain_body, html_body


def build_failure_mail():
    """投稿失敗時のメール件名・本文を組み立てる"""
    subject = "【skin note 自動投稿 失敗】要確認"

    plain_body = (
        "note.com への自動投稿に失敗しました。\n\n"
        "確認事項:\n"
        "1. GitHub Actions の実行ログを確認\n"
        "   https://github.com/kmkn0523-cell/kenta-learning/actions\n"
        "2. アーティファクト『note-screenshots』をダウンロードして失敗時の画面を確認\n"
        "3. NOTE_SESSION_V5 クッキーが期限切れの場合は再取得して GitHub Secrets を更新\n"
        "   手順: docs/note_cookie_setup.md\n"
    )

    html_body = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body { font-family: sans-serif; font-size: 16px; line-height: 1.8; max-width: 680px; margin: 0 auto; padding: 16px; }
.box { background: #ffe8e8; border-radius: 12px; padding: 18px; margin-bottom: 16px; }
.box a { color: #0066cc; word-break: break-all; }
ol { padding-left: 20px; }
</style></head><body>
<div class="box">
<p><strong>❌ note.com 自動投稿 失敗</strong></p>
<p>以下を確認してください：</p>
<ol>
<li>GitHub Actions の実行ログを確認<br>
<a href="https://github.com/kmkn0523-cell/kenta-learning/actions">github.com/kmkn0523-cell/kenta-learning/actions</a></li>
<li>アーティファクト『note-screenshots』をダウンロードして失敗時の画面を確認</li>
<li>NOTE_SESSION_V5 クッキーが期限切れの場合は再取得して GitHub Secrets を更新（手順: docs/note_cookie_setup.md）</li>
</ol>
</div>
</body></html>"""

    return subject, plain_body, html_body


def send_mail(subject, plain_body, html_body):
    """Gmail SMTP で送信する"""
    password = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not password:
        print("⚠️ GMAIL_APP_PASSWORD が未設定です。メール送信をスキップします。")
        return

    msg = MIMEMultipart("alternative")
    msg["From"] = MAIL_FROM
    msg["To"] = MAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MAIL_FROM, password)
        server.send_message(msg)
    print("✅ 通知メール送信完了")


def main():
    """成功 or 失敗を判定してメールを送る"""
    # NOTE_POST_STATUS 環境変数で成否を受け取る（GitHub Actions側でセット）
    # "success" 以外（空・"failure" 等）はすべて失敗扱い
    status = os.environ.get("NOTE_POST_STATUS", "").strip().lower()

    latest = load_latest_history()

    # 成功判定: ステータスが success かつ history に最新エントリがある
    if status == "success" and latest:
        subject, plain, html = build_success_mail(latest)
        print(f"📧 成功通知を送信: {latest.get('title', '')}")
    else:
        subject, plain, html = build_failure_mail()
        print(f"📧 失敗通知を送信（status={status!r}, latest={'あり' if latest else 'なし'}）")

    send_mail(subject, plain, html)


if __name__ == "__main__":
    main()
