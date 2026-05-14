# skin_instagram_image_gen_v3.py
# カルーセル投稿用の画像をHTML→PNG方式で一括生成するスクリプト
# 使い方: python3 skin/skin_instagram_image_gen_v3.py
# ※ローカル環境でのみ実行する（GitHub Actionsでは不要）

import json  # JSONファイルを読み込む道具
import os    # ファイルパスを扱う道具

from playwright.sync_api import sync_playwright  # HTML→PNGに変換する道具


# =============================
# 設定
# =============================
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))              # このスクリプトの場所
CONTENT_FILE = os.path.join(SCRIPT_DIR, 'carousel_content.json')       # テーマ定義ファイル
OUTPUT_DIR   = os.path.join(SCRIPT_DIR, 'skin_instagram_carousels')    # 画像の出力先
IMAGE_SIZE   = 1080                                                      # Instagram推奨サイズ（正方形）

# デザインカラー
COLOR_BG     = '#0f0f0f'   # 背景（ほぼ黒）
COLOR_TEXT   = '#f0ede8'   # メインテキスト（温かみのある白）
COLOR_ACCENT = '#c8a97e'   # アクセント（ゴールドベージュ）
COLOR_SUB    = '#888888'   # サブテキスト（グレー）
ACCOUNT_NAME = '@skin_reform_jp'  # アカウント名（必要に応じて変更）


# =============================
# HTMLテンプレート生成
# =============================

def make_base_html(body_content: str) -> str:
    """全スライド共通のHTMLラッパーを作る"""
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      width: {IMAGE_SIZE}px;
      height: {IMAGE_SIZE}px;
      background: {COLOR_BG};
      font-family: 'Noto Sans JP', 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
      color: {COLOR_TEXT};
      overflow: hidden;
    }}
  </style>
</head>
<body>
{body_content}
</body>
</html>"""


def make_cover_html(title: str, subtitle: str) -> str:
    """カバー（1枚目）スライドのHTMLを作る"""
    title_html    = title.replace('\n', '<br>')
    subtitle_html = subtitle.replace('\n', '<br>')
    return make_base_html(f"""
<div style="width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:80px; position:relative;">
  <div style="width:60px; height:5px; background:{COLOR_ACCENT}; margin-bottom:50px;"></div>
  <h1 style="font-size:64px; font-weight:900; line-height:1.5; text-align:center; letter-spacing:2px;">{title_html}</h1>
  <p style="font-size:26px; color:{COLOR_SUB}; margin-top:40px; text-align:center; line-height:1.6;">{subtitle_html}</p>
  <div style="position:absolute; bottom:50px; display:flex; align-items:center; gap:12px;">
    <div style="width:40px; height:2px; background:{COLOR_ACCENT};"></div>
    <p style="color:{COLOR_ACCENT}; font-size:22px;">{ACCOUNT_NAME}</p>
    <div style="width:40px; height:2px; background:{COLOR_ACCENT};"></div>
  </div>
</div>""")


def make_list_html(slide_num: int, heading: str, items: list) -> str:
    """リスト形式スライドのHTMLを作る"""
    items_html = ''
    for item in items:
        item_html = item.replace('\n', '<br>')
        items_html += f"""
    <div style="display:flex; align-items:flex-start; margin-bottom:32px;">
      <span style="color:{COLOR_ACCENT}; font-size:26px; min-width:36px; margin-top:6px; flex-shrink:0;">▶</span>
      <p style="font-size:30px; line-height:1.65; color:{COLOR_TEXT};">{item_html}</p>
    </div>"""

    return make_base_html(f"""
<div style="width:100%; height:100%; padding:65px 75px; position:relative; display:flex; flex-direction:column; justify-content:center;">
  <p style="color:{COLOR_ACCENT}; font-size:22px; margin-bottom:20px;">{slide_num} / 5</p>
  <h2 style="font-size:36px; font-weight:700; border-left:5px solid {COLOR_ACCENT}; padding-left:20px; margin-bottom:45px; line-height:1.5;">{heading}</h2>
  <div>{items_html}</div>
  <p style="position:absolute; bottom:40px; right:75px; color:{COLOR_SUB}; font-size:20px;">{ACCOUNT_NAME}</p>
</div>""")


def make_comparison_html(slide_num: int, heading: str, left: str, right: str) -> str:
    """比較形式スライドのHTMLを作る"""
    left_html  = left.replace('\n', '<br>')
    right_html = right.replace('\n', '<br>')
    return make_base_html(f"""
<div style="width:100%; height:100%; padding:65px 75px; display:flex; flex-direction:column; justify-content:center; position:relative;">
  <p style="color:{COLOR_ACCENT}; font-size:22px; margin-bottom:20px;">{slide_num} / 5</p>
  <h2 style="font-size:36px; font-weight:700; border-left:5px solid {COLOR_ACCENT}; padding-left:20px; margin-bottom:45px;">{heading}</h2>
  <div style="display:flex; gap:24px; align-items:stretch;">
    <div style="flex:1; background:#1e1e1e; border-radius:16px; padding:35px; border:2px solid #333;">
      <p style="color:#ff7070; font-size:20px; margin-bottom:14px; font-weight:700;">❌ 以前</p>
      <p style="font-size:28px; line-height:1.65;">{left_html}</p>
    </div>
    <div style="width:4px; background:{COLOR_ACCENT}; border-radius:4px; align-self:stretch;"></div>
    <div style="flex:1; background:#1e1e1e; border-radius:16px; padding:35px; border:2px solid {COLOR_ACCENT};">
      <p style="color:{COLOR_ACCENT}; font-size:20px; margin-bottom:14px; font-weight:700;">✅ 今</p>
      <p style="font-size:28px; line-height:1.65;">{right_html}</p>
    </div>
  </div>
  <p style="position:absolute; bottom:40px; right:75px; color:{COLOR_SUB}; font-size:20px;">{ACCOUNT_NAME}</p>
</div>""")


def make_cta_html(text: str, sub: str) -> str:
    """CTA（最終スライド）のHTMLを作る"""
    text_html = text.replace('\n', '<br>')
    sub_html  = sub.replace('\n', '<br>')
    return make_base_html(f"""
<div style="width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:80px; text-align:center;">
  <p style="font-size:56px; margin-bottom:28px;">🔖</p>
  <h2 style="font-size:52px; font-weight:900; line-height:1.65; margin-bottom:36px;">{text_html}</h2>
  <div style="width:80px; height:3px; background:{COLOR_ACCENT}; margin-bottom:36px;"></div>
  <p style="font-size:26px; color:{COLOR_SUB}; line-height:1.8;">{sub_html}</p>
  <p style="font-size:22px; color:{COLOR_ACCENT}; margin-top:48px;">{ACCOUNT_NAME}</p>
</div>""")


def slide_to_html(slide: dict, slide_num: int) -> str:
    """スライドの種類に応じてHTMLを選ぶ"""
    slide_type = slide['type']
    if slide_type == 'cover':
        return make_cover_html(slide['title'], slide.get('subtitle', ''))
    elif slide_type == 'list':
        return make_list_html(slide_num, slide['heading'], slide['items'])
    elif slide_type == 'comparison':
        return make_comparison_html(slide_num, slide['heading'], slide['left'], slide['right'])
    elif slide_type == 'cta':
        return make_cta_html(slide['text'], slide.get('sub', ''))
    else:
        raise ValueError(f"未知のスライドタイプ: {slide_type}")


# =============================
# 画像生成メイン処理
# =============================

def generate_all_images():
    """全テーマのカルーセル画像を一括生成する"""
    # 出力ディレクトリを作る（なければ作成）
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # コンテンツ定義ファイルを読み込む
    with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    themes = data['themes']
    total  = len(themes) * 5
    print(f"=== カルーセル画像生成開始（{len(themes)}テーマ × 5枚 = {total}枚）===")

    # playwright でブラウザを起動する（画面なしのヘッドレスモード）
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page    = browser.new_page(viewport={'width': IMAGE_SIZE, 'height': IMAGE_SIZE})

        for theme in themes:
            theme_id = theme['id']
            slides   = theme['slides']
            print(f"テーマ{theme_id:02d} 生成中...")

            for slide_num, slide in enumerate(slides, start=1):
                # HTMLを生成してブラウザに読み込む
                html_content = slide_to_html(slide, slide_num)
                page.set_content(html_content, wait_until='networkidle')

                # PNGとして保存する
                output_path = os.path.join(OUTPUT_DIR, f"theme{theme_id:02d}_slide{slide_num}.png")
                page.screenshot(path=output_path, type='png')
                print(f"  ✅ slide{slide_num} → {os.path.basename(output_path)}")

        browser.close()

    print(f"=== 完了: {OUTPUT_DIR} に {total}枚の画像を生成しました ===")


if __name__ == '__main__':
    generate_all_images()
