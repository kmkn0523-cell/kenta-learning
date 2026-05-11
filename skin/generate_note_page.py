# generate_note_page.py
# note_ready.md からコピーボタン付きHTMLページを生成する
# 生成先: /note_article.html（GitHub Pages で HTTPS 配信される）

import re, os
import markdown

BASE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.join(BASE_DIR, "..")

# note_ready.md を読み込む
with open(os.path.join(BASE_DIR, "note_ready.md"), "r", encoding="utf-8") as f:
    content = f.read()

# コメント行を除いた記事本文を取得する
lines = content.split("\n")
body_lines = [l for l in lines if not l.startswith("<!--")]
article_body = "\n".join(body_lines).strip()

# MarkdownをHTMLに変換する（見出しを太字段落に変換してnoteで大文字にならないようにする）
html_body = markdown.markdown(article_body, extensions=["extra"])

# h1・h2タグを太字の段落に置き換える（noteが大きな見出しとして扱うのを防ぐ）
import re as _re
html_body = _re.sub(r'<h1>(.*?)</h1>', r'<p><strong>\1</strong></p>', html_body)
html_body = _re.sub(r'<h2>(.*?)</h2>', r'<p><strong>\1</strong></p>', html_body)
html_body = _re.sub(r'<h3>(.*?)</h3>', r'<p><strong>\1</strong></p>', html_body)

# コピーボタン付きHTMLページを生成する
html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>note 記事</title>
<style>
body { font-family: sans-serif; font-size: 16px; line-height: 1.9; max-width: 720px; margin: 0 auto; padding: 20px; color: #222; }
h1 { font-size: 22px; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
h2 { font-size: 18px; margin-top: 28px; }
strong { font-weight: bold; }
hr { border: none; border-top: 1px solid #ddd; margin: 24px 0; }
blockquote { border-left: 4px solid #ccc; margin: 0; padding: 4px 16px; color: #555; }
#copy-btn {
  display: block; width: 100%; padding: 18px;
  font-size: 18px; font-weight: bold;
  background: #0066cc; color: white;
  border: none; border-radius: 12px;
  margin-bottom: 28px; cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
#copy-btn.done { background: #28a745; }
#article { padding: 4px 0; }
</style>
</head>
<body>
<button id="copy-btn" onclick="copyArticle()">📋 記事をコピーする</button>
<div id="article">ARTICLE_HTML</div>
<script>
function copyArticle() {
  var el = document.getElementById('article');
  var html = el.innerHTML;
  var text = el.innerText;
  var btn = document.getElementById('copy-btn');
  if (navigator.clipboard && window.ClipboardItem) {
    navigator.clipboard.write([
      new ClipboardItem({
        'text/html': new Blob([html], {type: 'text/html'}),
        'text/plain': new Blob([text], {type: 'text/plain'})
      })
    ]).then(function() {
      btn.textContent = '✅ コピーしました！noteに貼り付けてください';
      btn.className = 'done';
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
  btn.textContent = '✅ コピーしました！noteに貼り付けてください';
  btn.className = 'done';
}
</script>
</body>
</html>""".replace("ARTICLE_HTML", html_body)

# リポジトリルートに保存する（GitHub Pages で配信される）
out_path = os.path.join(ROOT_DIR, "note_article.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ 生成完了: {out_path}")
print("🌐 URL: https://kmkn0523-cell.github.io/kenta-learning/note_article.html")
