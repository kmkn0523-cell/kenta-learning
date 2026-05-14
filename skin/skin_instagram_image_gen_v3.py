# skin_instagram_image_gen_v3.py
# カルーセル投稿用の画像をPIL方式で一括生成するスクリプト
# 使い方: python3 skin/skin_instagram_image_gen_v3.py
# ※ローカル環境でのみ実行する（GitHub Actionsでは不要）

import json   # JSONファイルを読み込む道具
import os     # ファイルパスを扱う道具
import textwrap  # 長いテキストを折り返す道具

from PIL import Image, ImageDraw, ImageFont  # 画像を作る道具


# =============================
# 設定
# =============================
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))               # このスクリプトの場所
CONTENT_FILE = os.path.join(SCRIPT_DIR, 'carousel_content.json')        # テーマ定義ファイル
OUTPUT_DIR   = os.path.join(SCRIPT_DIR, 'skin_instagram_carousels')     # 画像の出力先
FONT_PATH    = os.path.join(os.path.dirname(SCRIPT_DIR), 'fonts', 'NotoSerifJP.otf')  # 日本語フォント
IMAGE_SIZE   = 1080  # Instagram推奨サイズ（正方形）

# デザインカラー（RGB タプル形式）
COLOR_BG     = (15, 15, 15)     # 背景（ほぼ黒）
COLOR_TEXT   = (240, 237, 232)  # メインテキスト（温かみのある白）
COLOR_ACCENT = (200, 169, 126)  # アクセント（ゴールドベージュ）
COLOR_SUB    = (136, 136, 136)  # サブテキスト（グレー）
COLOR_CARD   = (30, 30, 30)     # カード背景色
COLOR_RED    = (255, 112, 112)  # 比較スライドのNG色
ACCOUNT_NAME = '@skin_reform_jp'  # アカウント名（必要に応じて変更）


# =============================
# フォント読み込み
# =============================

def get_font(size: int) -> ImageFont.FreeTypeFont:
    """指定サイズのフォントを返す"""
    return ImageFont.truetype(FONT_PATH, size)


# =============================
# 共通描画ヘルパー
# =============================

def make_base_image() -> tuple:
    """背景画像とDrawオブジェクトを作る"""
    img  = Image.new('RGB', (IMAGE_SIZE, IMAGE_SIZE), COLOR_BG)
    draw = ImageDraw.Draw(img)
    return img, draw


def draw_text_wrapped(draw, text: str, x: int, y: int, max_width: int,
                      font: ImageFont.FreeTypeFont, color: tuple, line_spacing: int = 12,
                      dry_run: bool = False) -> int:
    """長いテキストを折り返して描画し、描画後のY座標を返す。dry_run=Trueなら描画せず高さだけ計算"""
    # 1文字あたりの幅を概算して折り返し文字数を決める
    bbox       = font.getbbox('あ')
    char_width = bbox[2] - bbox[0]
    wrap_chars = max(1, max_width // char_width)

    lines   = []
    for paragraph in text.split('\n'):
        wrapped = textwrap.wrap(paragraph, width=wrap_chars) if paragraph else ['']
        lines.extend(wrapped)

    current_y = y
    line_height = font.getbbox('あ')[3] - font.getbbox('あ')[1]
    for line in lines:
        if not dry_run:
            draw.text((x, current_y), line, font=font, fill=color)
        current_y += line_height + line_spacing
    return current_y


def draw_account_name(draw):
    """右下にアカウント名を描画する"""
    font = get_font(22)
    bbox = font.getbbox(ACCOUNT_NAME)
    w    = bbox[2] - bbox[0]
    draw.text((IMAGE_SIZE - w - 60, IMAGE_SIZE - 60), ACCOUNT_NAME, font=font, fill=COLOR_ACCENT)


# =============================
# スライドタイプ別画像生成
# =============================

def make_cover_image(title: str, subtitle: str) -> Image.Image:
    """カバー（1枚目）スライドを作る"""
    img, draw = make_base_image()

    # アクセントライン（上部中央）
    line_w = 60
    cx     = IMAGE_SIZE // 2
    draw.rectangle([cx - line_w // 2, 320, cx + line_w // 2, 325], fill=COLOR_ACCENT)

    # タイトル（大きく中央）
    font_title = get_font(62)
    y = 370
    for line in title.split('\n'):
        bbox = font_title.getbbox(line)
        tw   = bbox[2] - bbox[0]
        draw.text(((IMAGE_SIZE - tw) // 2, y), line, font=font_title, fill=COLOR_TEXT)
        y += (bbox[3] - bbox[1]) + 20

    # サブタイトル（中央）
    if subtitle:
        font_sub = get_font(26)
        y += 30
        for line in subtitle.split('\n'):
            bbox = font_sub.getbbox(line)
            sw   = bbox[2] - bbox[0]
            draw.text(((IMAGE_SIZE - sw) // 2, y), line, font=font_sub, fill=COLOR_SUB)
            y += (bbox[3] - bbox[1]) + 10

    # アカウント名（下部中央）
    font_acc = get_font(22)
    # 左右のライン
    draw.rectangle([cx - 120, IMAGE_SIZE - 75, cx - 60, IMAGE_SIZE - 72], fill=COLOR_ACCENT)
    draw.rectangle([cx + 60, IMAGE_SIZE - 75, cx + 120, IMAGE_SIZE - 72], fill=COLOR_ACCENT)
    bbox_acc = font_acc.getbbox(ACCOUNT_NAME)
    aw = bbox_acc[2] - bbox_acc[0]
    draw.text(((IMAGE_SIZE - aw) // 2, IMAGE_SIZE - 85), ACCOUNT_NAME, font=font_acc, fill=COLOR_ACCENT)

    return img


def make_list_image(slide_num: int, heading: str, items: list) -> Image.Image:
    """リスト形式スライドを作る"""
    img, draw = make_base_image()

    # スライド番号
    font_num = get_font(22)
    draw.text((75, 65), f"{slide_num} / 5", font=font_num, fill=COLOR_ACCENT)

    # 見出し（左にアクセントバー）
    font_head = get_font(36)
    draw.rectangle([75, 115, 80, 175], fill=COLOR_ACCENT)
    draw_text_wrapped(draw, heading, 100, 115, IMAGE_SIZE - 175, font_head, COLOR_TEXT, line_spacing=8)

    # リスト項目
    font_item = get_font(30)
    y = 230
    for item in items:
        # 矢印マーク
        draw.text((75, y), '▶', font=get_font(24), fill=COLOR_ACCENT)
        # 項目テキスト（折り返しあり）
        y = draw_text_wrapped(draw, item, 120, y, IMAGE_SIZE - 200, font_item, COLOR_TEXT, line_spacing=8)
        y += 20

    draw_account_name(draw)
    return img


def make_comparison_image(slide_num: int, heading: str, left: str, right: str) -> Image.Image:
    """比較形式スライドを作る"""
    img, draw = make_base_image()

    # スライド番号
    font_num = get_font(22)
    draw.text((75, 65), f"{slide_num} / 5", font=font_num, fill=COLOR_ACCENT)

    # 見出し
    font_head = get_font(36)
    draw.rectangle([75, 115, 80, 175], fill=COLOR_ACCENT)
    draw_text_wrapped(draw, heading, 100, 115, IMAGE_SIZE - 175, font_head, COLOR_TEXT, line_spacing=8)

    # 左カード（NG）
    card_top    = 240
    card_bottom = 860
    card_left   = 60
    card_mid    = 510
    card_right  = IMAGE_SIZE - 60

    draw.rounded_rectangle([card_left, card_top, card_mid - 15, card_bottom],
                           radius=16, fill=COLOR_CARD, outline=(51, 51, 51), width=2)
    draw.text((card_left + 30, card_top + 28), '❌ 以前', font=get_font(22), fill=COLOR_RED)
    draw_text_wrapped(draw, left, card_left + 30, card_top + 78, card_mid - card_left - 60,
                      get_font(28), COLOR_TEXT, line_spacing=10)

    # 中央のアクセントライン
    draw.rectangle([card_mid - 4, card_top + 40, card_mid + 4, card_bottom - 40], fill=COLOR_ACCENT)

    # 右カード（今）
    draw.rounded_rectangle([card_mid + 15, card_top, card_right, card_bottom],
                           radius=16, fill=COLOR_CARD, outline=COLOR_ACCENT, width=2)
    draw.text((card_mid + 45, card_top + 28), '✅ 今', font=get_font(22), fill=COLOR_ACCENT)
    draw_text_wrapped(draw, right, card_mid + 45, card_top + 78, card_right - card_mid - 60,
                      get_font(28), COLOR_TEXT, line_spacing=10)

    draw_account_name(draw)
    return img


def make_cta_image(text: str, sub: str) -> Image.Image:
    """CTA（最終スライド）を作る"""
    img, draw = make_base_image()
    cx        = IMAGE_SIZE // 2

    # 保存アイコン（テキストで代用）
    font_icon = get_font(60)
    icon_text = '[ 保存 ]'
    bbox_icon = font_icon.getbbox(icon_text)
    iw        = bbox_icon[2] - bbox_icon[0]
    draw.text(((IMAGE_SIZE - iw) // 2, 250), icon_text, font=font_icon, fill=COLOR_ACCENT)

    # メインテキスト
    font_main = get_font(52)
    y = 370
    for line in text.split('\n'):
        bbox = font_main.getbbox(line)
        tw   = bbox[2] - bbox[0]
        draw.text(((IMAGE_SIZE - tw) // 2, y), line, font=font_main, fill=COLOR_TEXT)
        y += (bbox[3] - bbox[1]) + 20

    # 区切り線
    y += 30
    draw.rectangle([cx - 40, y, cx + 40, y + 3], fill=COLOR_ACCENT)
    y += 30

    # サブテキスト
    font_sub = get_font(26)
    for line in sub.split('\n'):
        bbox = font_sub.getbbox(line)
        sw   = bbox[2] - bbox[0]
        draw.text(((IMAGE_SIZE - sw) // 2, y), line, font=font_sub, fill=COLOR_SUB)
        y += (bbox[3] - bbox[1]) + 10

    # アカウント名
    font_acc = get_font(22)
    bbox_acc = font_acc.getbbox(ACCOUNT_NAME)
    aw       = bbox_acc[2] - bbox_acc[0]
    draw.text(((IMAGE_SIZE - aw) // 2, IMAGE_SIZE - 80), ACCOUNT_NAME, font=font_acc, fill=COLOR_ACCENT)

    return img


def slide_to_image(slide: dict, slide_num: int) -> Image.Image:
    """スライドの種類に応じて画像を生成する"""
    slide_type = slide['type']
    if slide_type == 'cover':
        return make_cover_image(slide['title'], slide.get('subtitle', ''))
    elif slide_type == 'list':
        return make_list_image(slide_num, slide['heading'], slide['items'])
    elif slide_type == 'comparison':
        return make_comparison_image(slide_num, slide['heading'], slide['left'], slide['right'])
    elif slide_type == 'cta':
        return make_cta_image(slide['text'], slide.get('sub', ''))
    else:
        raise ValueError(f"未知のスライドタイプ: {slide_type}")


# =============================
# 画像生成メイン処理
# =============================

def generate_all_images():
    """全テーマのカルーセル画像を一括生成する"""
    # フォントの存在確認
    if not os.path.exists(FONT_PATH):
        print(f"❌ フォントが見つかりません: {FONT_PATH}")
        return

    # 出力ディレクトリを作る（なければ作成）
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # コンテンツ定義ファイルを読み込む
    with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    themes = data['themes']
    total  = len(themes) * 5
    print(f"=== カルーセル画像生成開始（{len(themes)}テーマ × 5枚 = {total}枚）===")

    for theme in themes:
        theme_id = theme['id']
        slides   = theme['slides']
        print(f"テーマ{theme_id:02d} 生成中...")

        for slide_num, slide in enumerate(slides, start=1):
            # 画像を生成する
            img = slide_to_image(slide, slide_num)

            # PNGとして保存する
            output_path = os.path.join(OUTPUT_DIR, f"theme{theme_id:02d}_slide{slide_num}.png")
            img.save(output_path, 'PNG')
            print(f"  ✅ slide{slide_num} → {os.path.basename(output_path)}")

    print(f"=== 完了: {OUTPUT_DIR} に {total}枚の画像を生成しました ===")


if __name__ == '__main__':
    generate_all_images()
