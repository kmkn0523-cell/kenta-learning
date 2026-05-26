"""
女性インナーケアnote記事用ヘッダー画像を生成するスクリプト
サイズ: 1920×1006px
既存のnote_header.pngと同じスタイル（ダーク背景＋ゴールドアクセント）
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# フォントのパス（Windows → Linux フォールバック）
_WIN_BOLD   = "/mnt/c/Windows/Fonts/BIZ-UDGothicB.ttc"
_WIN_NORMAL = "/mnt/c/Windows/Fonts/BIZ-UDGothicR.ttc"
_NOTO_BOLD  = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
_NOTO_REG   = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

FONT_BOLD   = _WIN_BOLD   if os.path.exists(_WIN_BOLD)   else _NOTO_BOLD
FONT_NORMAL = _WIN_NORMAL if os.path.exists(_WIN_NORMAL) else _NOTO_REG

# 出力サイズ
OUT_W = 1920
OUT_H = 1006

# 3倍で描画してから縮小（高画質化）
S = 3
W = OUT_W * S
H = OUT_H * S

# 色の定義（既存バナーと統一）
BG_COLOR     = (12, 8, 18)
ACCENT_COLOR = (212, 160, 80)
WHITE        = (255, 255, 255)
LIGHT_GOLD   = (240, 200, 130)


def draw_rounded_rect(draw, xy, radius, fill):
    """角丸の四角形を描く"""
    x1, y1, x2, y2 = xy
    draw.ellipse([x1, y1, x1 + radius*2, y1 + radius*2], fill=fill)
    draw.ellipse([x2 - radius*2, y1, x2, y1 + radius*2], fill=fill)
    draw.ellipse([x1, y2 - radius*2, x1 + radius*2, y2], fill=fill)
    draw.ellipse([x2 - radius*2, y2 - radius*2, x2, y2], fill=fill)
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)


def p(val):
    """座標値をS倍にする"""
    return int(val * S)


def create_header():
    img  = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    CENTER_Y = H // 2

    # ===== 背景装飾：右側の薄い円 =====
    draw.ellipse([p(900), p(50), p(2000), p(1150)], fill=(28, 18, 42))
    draw.ellipse([p(1100), p(200), p(1900), p(1000)], fill=(38, 25, 55))

    # ===== 左端のアクセントバー =====
    draw.rectangle([0, 0, p(10), H], fill=ACCENT_COLOR)

    # ===== フォント =====
    font_tag  = ImageFont.truetype(FONT_BOLD,   p(24))
    font_main = ImageFont.truetype(FONT_BOLD,   p(80))
    font_sub  = ImageFont.truetype(FONT_NORMAL, p(32))

    # ===== テキスト内容 =====
    tag_text  = "女性 × インナーケア"
    main_line1 = "PMS・ニキビ・貧血、"
    main_accent = "半年で卒業。"
    sub_text  = "28歳の彼女が実践した「女性のためのインナーケア完全マニュアル」"

    # ===== 高さを計測して縦中央に揃える =====
    tag_bbox  = draw.textbbox((0, 0), tag_text,    font=font_tag)
    main_bbox = draw.textbbox((0, 0), main_line1,  font=font_main)
    sub_bbox  = draw.textbbox((0, 0), sub_text,    font=font_sub)

    tag_h  = tag_bbox[3]  - tag_bbox[1]
    main_h = main_bbox[3] - main_bbox[1]
    sub_h  = sub_bbox[3]  - sub_bbox[1]

    tag_pad   = p(10)
    gap1      = p(14)
    gap2      = p(18)
    tag_total = tag_h + tag_pad

    total_h = tag_total + gap1 + main_h + gap2 + sub_h
    start_y = CENTER_Y - total_h // 2

    # ===== タグバッジ =====
    tag_w = tag_bbox[2] - tag_bbox[0]
    tag_x = p(80)
    draw_rounded_rect(
        draw,
        (tag_x, start_y, tag_x + tag_w + tag_pad * 2, start_y + tag_total),
        radius=p(6),
        fill=ACCENT_COLOR,
    )
    draw.text(
        (tag_x + tag_pad, start_y + tag_pad // 2),
        tag_text, font=font_tag, fill=(20, 15, 10),
    )

    # ===== メインコピー（白＋ゴールド強調） =====
    main_y = start_y + tag_total + gap1
    part1_bbox = draw.textbbox((0, 0), main_line1, font=font_main)
    part1_w    = part1_bbox[2] - part1_bbox[0]
    draw.text((p(80), main_y), main_line1, font=font_main, fill=WHITE)
    draw.text((p(80) + part1_w, main_y), main_accent, font=font_main, fill=ACCENT_COLOR)

    # ===== サブコピー =====
    sub_y = main_y + main_h + gap2
    draw.text((p(82), sub_y), sub_text, font=font_sub, fill=LIGHT_GOLD)

    # ===== 右端の薄い装飾テキスト =====
    font_num   = ImageFont.truetype(FONT_BOLD, p(110))
    font_num_s = ImageFont.truetype(FONT_BOLD, p(36))
    draw.text((p(1500), CENTER_Y - p(70)), "6ヶ月",      font=font_num,   fill=(45, 32, 62))
    draw.text((p(1540), CENTER_Y + p(52)), "で人生が変わる", font=font_num_s, fill=(60, 45, 80))

    # ===== 縮小（LANCZOS）+ シャープネス =====
    img = img.resize((OUT_W, OUT_H), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=0.8, percent=140, threshold=2))

    save_path = "/home/kenta_kamijyo/skin/womens_note_header.png"
    img.save(save_path, "PNG")
    print(f"保存しました: {save_path}")


if __name__ == "__main__":
    print("女性インナーケアnoteヘッダー画像を生成中...")
    create_header()
    print("完成！")
