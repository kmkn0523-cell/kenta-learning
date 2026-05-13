# generate_paid_note_page.py
# skin_improvement_note.md からコピーボタン付きHTMLページを生成する
# 無料プレビュー部分と有料部分を別々にコピーできる2ボタン仕様
# 生成先: /paid_note.html（GitHub Pages で HTTPS 配信される）

import os
import re
import markdown

BASE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.join(BASE_DIR, "..")

# 有料noteのマークダウン全文を読み込む
with open(os.path.join(BASE_DIR, "skin_improvement_note.md"), "r", encoding="utf-8") as f:
    content = f.read()

# 「## 第1章」を境にして無料プレビューと有料部分を分割する
# 第1章の手前までが無料プレビュー（noteで購入前に表示される部分）
split_marker = "## 第1章 ―"

if split_marker in content:
    free_part, paid_part = content.split(split_marker, 1)
    # 有料部分の先頭に「## 第1章 ―」を戻す
    paid_part = split_marker + paid_part
else:
    free_part = content
    paid_part = ""


def md_to_html(md_text):
    """マークダウンをHTMLに変換し、noteで扱いやすい形に整形する"""
    html = markdown.markdown(md_text, extensions=["extra", "tables"])
    # h1〜h3を太字段落に変換（noteで大見出し扱いにならないようにする）
    html = re.sub(r'<h1>(.*?)</h1>', r'<p><strong>\1</strong></p>', html)
    html = re.sub(r'<h2>(.*?)</h2>', r'<p><strong>\1</strong></p>', html)
    html = re.sub(r'<h3>(.*?)</h3>', r'<p><strong>\1</strong></p>', html)
    html = re.sub(r'<h4>(.*?)</h4>', r'<p><strong>\1</strong></p>', html)
    return html


free_html = md_to_html(free_part)
paid_html = md_to_html(paid_part)

# コピーボタン付きHTMLページを生成する
html_template = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>有料note 編集ページ</title>
<style>
body { font-family: sans-serif; font-size: 16px; line-height: 1.9; max-width: 720px; margin: 0 auto; padding: 20px; color: #222; }
strong { font-weight: bold; }
hr { border: none; border-top: 1px solid #ddd; margin: 24px 0; }
blockquote { border-left: 4px solid #ccc; margin: 0; padding: 4px 16px; color: #555; }
table { border-collapse: collapse; margin: 12px 0; width: 100%; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background: #f6f6f6; }
.section-header {
  background: #f0f8ff; padding: 12px; border-radius: 8px;
  margin-top: 32px; margin-bottom: 16px;
  font-weight: bold; color: #0066cc;
}
.copy-btn {
  display: block; width: 100%; padding: 18px;
  font-size: 17px; font-weight: bold;
  background: #0066cc; color: white;
  border: none; border-radius: 12px;
  margin: 16px 0 28px; cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
.copy-btn.done { background: #28a745; }
.copy-btn.paid { background: #d97706; }
.copy-btn.paid.done { background: #28a745; }
.content-box { padding: 4px 0; border-left: 3px solid #eee; padding-left: 16px; }
.instruction {
  background: #fff8dc; padding: 12px; border-radius: 8px;
  font-size: 14px; margin-bottom: 20px;
}
</style>
</head>
<body>

<div class="instruction">
📝 <strong>使い方</strong><br>
① noteで新規記事を作成<br>
② 下の「無料部分をコピー」を押す<br>
③ noteに貼り付け<br>
④ 「ここから有料エリア」のラインを設定<br>
⑤ 「有料部分をコピー」を押す<br>
⑥ ラインの下に貼り付け
</div>

<div class="section-header">📖 無料プレビュー部分（購入前に表示される部分）</div>
<button class="copy-btn" onclick="copySection('free')">📋 無料部分をコピー</button>
<div id="free-content" class="content-box">FREE_HTML</div>

<div class="section-header">🔒 有料部分（購入後に表示される部分）</div>
<button class="copy-btn paid" onclick="copySection('paid')">📋 有料部分をコピー</button>
<div id="paid-content" class="content-box">PAID_HTML</div>

<script>
function copySection(type) {
  var el = document.getElementById(type + '-content');
  var btn = event.target;
  var html = el.innerHTML;
  var text = el.innerText;
  if (navigator.clipboard && window.ClipboardItem) {
    navigator.clipboard.write([
      new ClipboardItem({
        'text/html': new Blob([html], {type: 'text/html'}),
        'text/plain': new Blob([text], {type: 'text/plain'})
      })
    ]).then(function() {
      btn.textContent = '✅ コピー完了！noteに貼り付けてください';
      btn.classList.add('done');
    }).catch(function() { fallbackCopy(el, btn); });
  } else {
    fallbackCopy(el, btn);
  }
}
function fallbackCopy(el, btn) {
  var range = document.createRange();
  range.selectNode(el);
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(range);
  document.execCommand('copy');
  window.getSelection().removeAllRanges();
  btn.textContent = '✅ コピー完了！noteに貼り付けてください';
  btn.classList.add('done');
}
</script>
</body>
</html>"""

html_output = html_template.replace("FREE_HTML", free_html).replace("PAID_HTML", paid_html)

# リポジトリルートに保存する（GitHub Pages で配信される）
out_path = os.path.join(ROOT_DIR, "paid_note.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html_output)

print(f"✅ 生成完了: {out_path}")
print(f"📏 無料部分: 約{len(free_html)}文字")
print(f"📏 有料部分: 約{len(paid_html)}文字")
print("🌐 URL: https://kmkn0523-cell.github.io/kenta-learning/paid_note.html")
