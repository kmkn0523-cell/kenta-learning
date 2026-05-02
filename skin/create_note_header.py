"""
noteプロフィール用ヘッダー画像を生成するスクリプト
サイズ: 1920×1006px
高画質化: 3倍サイズで描いてLANCZOS縮小 + アンシャープマスクで輪郭強調
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_BOLD   = "/mnt/c/Windows/Fonts/BIZ-UDGothicB.ttc"
FONT_NORMAL = "/mnt/c/Windows/Fonts/BIZ-UDGothicR.ttc"

OUT_W = 1920
OUT_H = 1006

# 3倍で描いてから縮小する（座標・フォントサイズはすべてS倍する）
S = 3
W = OUT_W * S
H = OUT_H * S

BG_COLOR     = (12, 8, 18)
ACCENT_COLOR = (212, 160, 80)
WHITE        = (255, 255, 255)
LIGHT_GOLD   = (240, 200, 130)


def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.ellipse([x1, y1, x1 + radius*2, y1 + radius*2], fill=fill)
    draw.ellipse([x2 - radius*2, y1, x2, y1 + radius*2], fill=fill)
    draw.ellipse([x1, y2 - radius*2, x1 + radius*2, y2], fill=fill)
    draw.ellipse([x2 - radius*2, y2 - radius*2, x2, y2], fill=fill)
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)


def p(val):
    """座標値をSCLE倍にする（px = pixel の略）"""
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
    font_main = ImageFont.truetype(FONT_BOLD,   p(96))
    font_sub  = ImageFont.truetype(FONT_NORMAL, p(34))

    tag_text  = "肌荒れ × 内側改善"
    main_text = "スキンケアでは、治らない。"
    sub_text  = "200万円の失敗で辿り着いた「食事・腸・睡眠の整え方」"

    # ===== 高さを計測して縦中央に揃える =====
    tag_bbox  = draw.textbbox((0, 0), tag_text,  font=font_tag)
    main_bbox = draw.textbbox((0, 0), main_text, font=font_main)
    sub_bbox  = draw.textbbox((0, 0), sub_text,  font=font_sub)

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
    draw.text((tag_x + tag_pad, start_y + tag_pad // 2), tag_text, font=font_tag, fill=(20, 15, 10))

    # ===== メインコピー =====
    main_y = start_y + tag_total + gap1
    part1      = "スキンケアでは、"
    part1_bbox = draw.textbbox((0, 0), part1, font=font_main)
    part1_w    = part1_bbox[2] - part1_bbox[0]
    draw.text((p(80), main_y), part1, font=font_main, fill=WHITE)
    draw.text((p(80) + part1_w, main_y), "治らない。", font=font_main, fill=ACCENT_COLOR)

    # ===== サブコピー =====
    sub_y = main_y + main_h + gap2
    draw.text((p(82), sub_y), sub_text, font=font_sub, fill=LIGHT_GOLD)

    # ===== 右端の薄い装飾 =====
    font_num   = ImageFont.truetype(FONT_BOLD, p(110))
    font_num_s = ImageFont.truetype(FONT_BOLD, p(36))
    draw.text((p(1480), CENTER_Y - p(70)), "200万円",    font=font_num,   fill=(45, 32, 62))
    draw.text((p(1560), CENTER_Y + p(52)), "の失敗と答え", font=font_num_s, fill=(60, 45, 80))

    # ===== 縮小（LANCZOS）+ シャープネス =====
    img = img.resize((OUT_W, OUT_H), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=0.8, percent=140, threshold=2))

    save_path = "/home/kenta_kamijyo/skin/note_header.png"
    img.save(save_path, "PNG")
    print(f"✅ 保存しました: {save_path}")


if __name__ == "__main__":
    print("noteヘッダー画像を生成中...")
    create_header()
    print("完成！")
