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
.btn-row { display: flex; gap: 8px; margin: 16px 0 12px; flex-wrap: wrap; }
.copy-btn {
  flex: 1; min-width: 200px; padding: 16px;
  font-size: 16px; font-weight: bold;
  background: #0066cc; color: white;
  border: none; border-radius: 10px;
  cursor: pointer; -webkit-tap-highlight-color: transparent;
}
.copy-btn:hover { background: #004499; }
.copy-btn.done { background: #28a745; }
.copy-btn.paid { background: #d97706; }
.copy-btn.paid:hover { background: #b45309; }
.copy-btn.paid.done { background: #28a745; }
.copy-btn.select-btn { background: #6b7280; flex: 0 0 auto; min-width: 160px; }
.copy-btn.select-btn:hover { background: #4b5563; }
.content-box { padding: 4px 0; border-left: 3px solid #eee; padding-left: 16px; }
.content-box.selected { border-left-color: #0066cc; background: #f0f8ff; }
.instruction {
  background: #fff8dc; padding: 14px; border-radius: 8px;
  font-size: 14px; margin-bottom: 20px; line-height: 1.7;
}
.tip {
  background: #e7f5e7; padding: 10px 14px; border-radius: 6px;
  font-size: 13px; margin: 8px 0 20px; color: #2d5a2d;
}
kbd {
  display: inline-block; padding: 2px 6px;
  background: #f4f4f5; border: 1px solid #d4d4d8;
  border-radius: 4px; font-size: 12px;
  font-family: monospace;
}
</style>
</head>
<body>

<div class="instruction">
📝 <strong>使い方</strong><br>
① noteで新規記事を作成<br>
② 下のセクションごとに「コピー」ボタンを押す（PC・スマホ両対応）<br>
③ noteに貼り付け（Ctrl+V / Cmd+V / 長押し → ペースト）<br>
④ noteで「ここから有料エリア」のラインを設定して、有料部分を貼る
</div>

<div class="tip">
💡 <strong>PCで使うコツ</strong>：コピーボタンが効かない場合は「<strong>範囲を選択</strong>」ボタンを押してから <kbd>Ctrl</kbd>+<kbd>C</kbd>（Macは <kbd>Cmd</kbd>+<kbd>C</kbd>）でコピーできます。
</div>

<div class="section-header">📖 無料プレビュー部分（購入前に表示される部分）</div>
<div class="btn-row">
  <button class="copy-btn" onclick="copySection('free', this)">📋 無料部分をコピー</button>
  <button class="copy-btn select-btn" onclick="selectSection('free', this)">🖱 範囲を選択</button>
</div>
<div id="free-content" class="content-box">FREE_HTML</div>

<div class="section-header">🔒 有料部分（購入後に表示される部分）</div>
<div class="btn-row">
  <button class="copy-btn paid" onclick="copySection('paid', this)">📋 有料部分をコピー</button>
  <button class="copy-btn select-btn" onclick="selectSection('paid', this)">🖱 範囲を選択</button>
</div>
<div id="paid-content" class="content-box">PAID_HTML</div>

<script>
function copySection(type, btn) {
  var el = document.getElementById(type + '-content');
  var html = el.innerHTML;
  var text = el.innerText;
  var originalText = btn.textContent;
  if (navigator.clipboard && window.ClipboardItem) {
    navigator.clipboard.write([
      new ClipboardItem({
        'text/html': new Blob([html], {type: 'text/html'}),
        'text/plain': new Blob([text], {type: 'text/plain'})
      })
    ]).then(function() {
      btn.textContent = '✅ コピー完了！noteに貼り付けてください';
      btn.classList.add('done');
      setTimeout(function(){ btn.textContent = originalText; btn.classList.remove('done'); }, 4000);
    }).catch(function() { fallbackCopy(el, btn, originalText); });
  } else {
    fallbackCopy(el, btn, originalText);
  }
}
function fallbackCopy(el, btn, originalText) {
  var range = document.createRange();
  range.selectNode(el);
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(range);
  var ok = false;
  try { ok = document.execCommand('copy'); } catch(e) {}
  window.getSelection().removeAllRanges();
  if (ok) {
    btn.textContent = '✅ コピー完了！noteに貼り付けてください';
    btn.classList.add('done');
    setTimeout(function(){ btn.textContent = originalText; btn.classList.remove('done'); }, 4000);
  } else {
    btn.textContent = '⚠ 自動コピー失敗。「範囲を選択」→ Ctrl+C を使ってください';
  }
}
function selectSection(type, btn) {
  // すべてのcontent-boxの選択状態をリセット
  document.querySelectorAll('.content-box').forEach(function(b){ b.classList.remove('selected'); });
  var el = document.getElementById(type + '-content');
  el.classList.add('selected');
  var range = document.createRange();
  range.selectNode(el);
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(range);
  // ユーザーへフィードバック
  btn.textContent = '✅ 選択中：Ctrl+C（Cmd+C）でコピー';
  setTimeout(function(){ btn.textContent = '🖱 範囲を選択'; }, 5000);
  // 範囲が見やすいよう、選択箇所までスクロール
  el.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
