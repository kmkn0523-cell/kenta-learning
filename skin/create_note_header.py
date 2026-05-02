"""
noteプロフィール用ヘッダー画像を生成するスクリプト
サイズ: 1280×670px（note.com標準サイズ）
テーマ: 肌荒れを「内側から治す」アカウントのコンセプトを伝える
"""

from PIL import Image, ImageDraw, ImageFont  # 画像を作るためのライブラリ

# ===== フォントの設定 =====
FONT_BOLD   = "/mnt/c/Windows/Fonts/BIZ-UDGothicB.ttc"  # 太字フォント
FONT_NORMAL = "/mnt/c/Windows/Fonts/BIZ-UDGothicR.ttc"  # 通常フォント

# ===== 画像サイズ =====
WIDTH  = 1280  # 横幅（ピクセル）
HEIGHT = 670   # 縦幅（ピクセル）

# ===== カラー設定 =====
BG_COLOR     = (12, 8, 18)         # 背景色（ほぼ黒・深い紫みがかった暗色）
ACCENT_COLOR = (212, 160, 80)      # アクセント（ゴールド）
WHITE        = (255, 255, 255)     # 白
LIGHT_GOLD   = (240, 200, 130)     # 明るいゴールド（サブテキスト用）
DARK_GOLD    = (120, 85, 30)       # 暗めゴールド（装飾用）


def draw_rounded_rect(draw, xy, radius, fill):
    """
    角丸の四角形を描く関数
    xy     : (左, 上, 右, 下) の座標
    radius : 角の丸み（ピクセル）
    fill   : 塗りつぶしの色
    """
    x1, y1, x2, y2 = xy
    draw.ellipse([x1, y1, x1 + radius*2, y1 + radius*2], fill=fill)
    draw.ellipse([x2 - radius*2, y1, x2, y1 + radius*2], fill=fill)
    draw.ellipse([x1, y2 - radius*2, x1 + radius*2, y2], fill=fill)
    draw.ellipse([x2 - radius*2, y2 - radius*2, x2, y2], fill=fill)
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)


def create_header():
    """
    noteヘッダー画像を1枚作る関数
    """

    # ===== 背景を作る =====
    img  = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # ===== 背景の装飾：右側に大きな薄い円（奥行き感）=====
    circle_color_1 = (28, 18, 42)   # 背景よりほんの少し明るい紫
    circle_color_2 = (38, 25, 55)   # さらに少し明るい
    draw.ellipse([700, -100, 1550, 750], fill=circle_color_1)
    draw.ellipse([850, 50, 1450, 650], fill=circle_color_2)

    # ===== 左端のアクセントバー（縦のゴールドライン）=====
    draw.rectangle([0, 0, 7, HEIGHT], fill=ACCENT_COLOR)

    # ===== 下部のアクセントライン =====
    draw.rectangle([0, HEIGHT - 7, WIDTH, HEIGHT], fill=ACCENT_COLOR)

    # ===== 上部タグ：「肌荒れ 内側改善」=====
    font_tag = ImageFont.truetype(FONT_BOLD, 26)
    tag_text = "肌荒れ ✕ 内側改善"
    tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
    tag_w    = tag_bbox[2] - tag_bbox[0]
    tag_h    = tag_bbox[3] - tag_bbox[1]
    tag_pad  = 14
    tag_x    = 55
    tag_y    = 52

    # タグの背景（ゴールドの角丸バッジ）
    draw_rounded_rect(
        draw,
        (tag_x, tag_y, tag_x + tag_w + tag_pad * 2, tag_y + tag_h + tag_pad),
        radius=8,
        fill=ACCENT_COLOR,
    )
    # タグのテキスト（黒文字）
    draw.text(
        (tag_x + tag_pad, tag_y + tag_pad // 2),
        tag_text,
        font=font_tag,
        fill=(20, 15, 10),
    )

    # ===== メインキャッチコピー（2行）=====
    font_main = ImageFont.truetype(FONT_BOLD, 92)

    line1 = "スキンケアでは、"
    line2 = "治らない。"

    # 1行目
    draw.text((55, 148), line1, font=font_main, fill=WHITE)
    bbox1 = draw.textbbox((0, 0), line1, font=font_main)
    h1 = bbox1[3] - bbox1[1]

    # 2行目（ゴールド色で強調）
    draw.text((55, 148 + h1 + 10), line2, font=font_main, fill=ACCENT_COLOR)
    bbox2 = draw.textbbox((0, 0), line2, font=font_main)
    h2 = bbox2[3] - bbox2[1]

    # ===== サブコピー（小さめ・明るいゴールド）=====
    font_sub = ImageFont.truetype(FONT_NORMAL, 36)
    sub_y = 148 + h1 + 10 + h2 + 32

    draw.text(
        (58, sub_y),
        "200万円の失敗で辿り着いた「食事・腸・睡眠の整え方」",
        font=font_sub,
        fill=LIGHT_GOLD,
    )

    # ===== 下部の小さい説明文 =====
    font_small = ImageFont.truetype(FONT_NORMAL, 27)
    draw.text(
        (58, HEIGHT - 62),
        "外側ケアをやめた日から、肌は変わり始めた。",
        font=font_small,
        fill=(160, 140, 110),
    )

    # ===== 右側の数字インパクト装飾 =====
    font_num_big   = ImageFont.truetype(FONT_BOLD, 130)
    font_num_small = ImageFont.truetype(FONT_BOLD, 38)

    # 「200万」を薄く大きく右側に配置
    draw.text((870, 160), "200万円", font=font_num_big, fill=(45, 32, 62))   # ほぼ背景と同化する暗さ
    draw.text((910, 310), "の失敗と答え", font=font_num_small, fill=(65, 48, 85))

    # ===== 保存 =====
    save_path = "/home/kenta_kamijyo/skin/note_header.png"
    img.save(save_path)
    print(f"✅ 保存しました: {save_path}")


# ===== メイン処理 =====
if __name__ == "__main__":
    print("noteヘッダー画像を生成中...")
    create_header()
    print("完成！")
