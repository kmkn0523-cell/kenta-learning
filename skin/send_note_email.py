# send_note_email.py
# GitHub Pages URLをリンクしたメールを送信するスクリプト
# GitHub Actions から呼び出される

import smtplib, os, json, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# note_ready.md を読み込む
with open("skin/note_ready.md", "r", encoding="utf-8") as f:
    content = f.read()

# 1行目のコメントから記事ファイル名を取得する
match = re.search(r'<!--.*?\|\s*(article_\d+\.md)', content)
article_filename = match.group(1) if match else ""

# コメント行を除いた記事本文を取得する
lines = content.split("\n")
body_lines = [l for l in lines if not l.startswith("<!--")]
article_body = "\n".join(body_lines).strip()

# 記事タイトルを取得する
title = next((l.lstrip("# ") for l in body_lines if l.startswith("# ")), "今週の記事")

# マッピングファイルからLP画像を特定する
lp_path = None
try:
    with open("skin/note_lp_map.json", "r", encoding="utf-8") as f:
        lp_map = json.load(f)
    lp_filename = lp_map.get(article_filename)
    if lp_filename:
        lp_path = f"skin/{lp_filename}"
except Exception:
    pass

# GitHub Pages の URL（コピーボタン付きページ）
pages_url = "https://kmkn0523-cell.github.io/kenta-learning/note_article.html"

# メール本文HTML
image_note = ""
if lp_path:
    image_note = "<p>📎 <strong>ヘッダー画像も添付しています。</strong>noteにアップロードしてください。</p>"

mail_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
body {{ font-family: sans-serif; font-size: 16px; line-height: 1.8; max-width: 680px; margin: 0 auto; padding: 16px; }}
.step-box {{ background: #e8f4ff; border-radius: 12px; padding: 18px; margin-bottom: 16px; }}
.step-box p {{ margin: 8px 0; font-size: 15px; }}
.step-box a {{ color: #0066cc; font-weight: bold; font-size: 17px; }}
</style>
</head>
<body>
<div class="step-box">
<p><strong>📋 太字をそのままnoteに貼る手順</strong></p>
<p>① 下のリンクをタップ（Brave / Safari どちらでもOK）</p>
<p><a href="{pages_url}">▶ 記事ページを開く</a></p>
<p>② 青いボタン「📋 記事をコピーする」をタップ</p>
<p>③ noteアプリで新規記事 → 貼り付け</p>
<p style="color:#888;font-size:13px;">※ 太字・見出しがそのまま入ります</p>
</div>
{image_note}
</body>
</html>"""

# メールを組み立てる
msg = MIMEMultipart("mixed")
msg["From"] = "kmkn0523@gmail.com"
msg["To"] = "kmkn0523@gmail.com"
msg["Subject"] = f"【skin note】{title}"

# メール本文
plain = f"記事ページを開く: {pages_url}\n青いボタンをタップ → noteに貼り付け"
msg_body = MIMEMultipart("alternative")
msg_body.attach(MIMEText(plain, "plain", "utf-8"))
msg_body.attach(MIMEText(mail_html, "html", "utf-8"))
msg.attach(msg_body)

# LP画像を添付する（存在する場合のみ）
if lp_path and os.path.exists(lp_path):
    with open(lp_path, "rb") as f:
        img = MIMEImage(f.read(), name=os.path.basename(lp_path))
    msg.attach(img)
    print(f"📎 画像を添付: {lp_path}")

# Gmailに接続して送信する
password = os.environ["GMAIL_APP_PASSWORD"]
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login("kmkn0523@gmail.com", password)
    server.send_message(msg)

print("✅ メール送信完了")
