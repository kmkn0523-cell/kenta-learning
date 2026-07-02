"""skin ヘッダー画像生成スクリプト

Threads用（1080x270）と Instagram用（1080x1080）の
ヘッダー画像を Pillow で自動生成する。
出力先: skin/profile/header_image_v2.png（Threads用）
        skin/profile/header_image_v2_ig.png（Instagram用）
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# フォントのパス（WSL から Windows のフォントを参照）
FONT_BOLD = "/mnt/c/Windows/Fonts/NotoSansJP-VF.ttf"

# 出力先フォルダ
OUTPUT_DIR = Path("/home/kenta_kamijyo/skin/profile")

# メインのキャッチコピー
MAIN_TEXT = "スキンケアでは、治らない。"
# サブテキスト（2行）
SUB_TEXT_1 = "大人ニキビと慢性肌荒れの内側改善"
SUB_TEXT_2 = "200万円の失敗で辿り着いた答え"

# 色（黒背景＋白文字）
COLOR_BG = (8, 8, 10)        # ほぼ黒・少しだけ青み
COLOR_MAIN = (255, 255, 255)  # 白
COLOR_SUB = (170, 170, 175)   # 薄いグレー
COLOR_LINE = (255, 255, 255)  # 白の細線


def measure_text(draw, text, font):
    """テキストの幅と高さを測る（中央寄せ用）"""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def generate_threads_header():
    """Threads用 横長バナー（1080x270）"""
    width, height = 1080, 270
    img = Image.new("RGB", (width, height), COLOR_BG)
    draw = ImageDraw.Draw(img)

    # フォントサイズ
    font_main = ImageFont.truetype(FONT_BOLD, 56)
    font_sub = ImageFont.truetype(FONT_BOLD, 20)

    # メインテキスト（中央上寄り）
    w_main, h_main = measure_text(draw, MAIN_TEXT, font_main)
    x_main = (width - w_main) // 2
    y_main = 60
    draw.text((x_main, y_main), MAIN_TEXT, font=font_main, fill=COLOR_MAIN)

    # 細い白の横線（メインとサブの間）
    line_y = y_main + h_main + 25
    line_w = 60
    draw.line(
        [((width - line_w) // 2, line_y), ((width + line_w) // 2, line_y)],
        fill=COLOR_LINE,
        width=1,
    )

    # サブテキスト1行目
    sub1 = f"{SUB_TEXT_1} / {SUB_TEXT_2}"
    w_sub, _ = measure_text(draw, sub1, font_sub)
    draw.text(
        ((width - w_sub) // 2, line_y + 15),
        sub1,
        font=font_sub,
        fill=COLOR_SUB,
    )

    output_path = OUTPUT_DIR / "header_image_v2.png"
    img.save(output_path, "PNG", quality=95)
    print(f"Threads用ヘッダー保存: {output_path}")
    return output_path


def generate_instagram_post():
    """Instagram用 正方形（1080x1080）"""
    width, height = 1080, 1080
    img = Image.new("RGB", (width, height), COLOR_BG)
    draw = ImageDraw.Draw(img)

    # フォントサイズ（正方形なので大きめ）
    font_main = ImageFont.truetype(FONT_BOLD, 88)
    font_sub_bold = ImageFont.truetype(FONT_BOLD, 38)
    font_sub_small = ImageFont.truetype(FONT_BOLD, 30)

    # メインテキスト（2行に分割して中央配置）
    main_line1 = "スキンケアでは、"
    main_line2 = "治らない。"

    w1, h1 = measure_text(draw, main_line1, font_main)
    w2, h2 = measure_text(draw, main_line2, font_main)

    # 縦方向のレイアウト中心を計算
    center_y = height // 2
    gap = 15
    total_h = h1 + h2 + gap
    start_y = center_y - total_h // 2 - 60  # 全体を少し上に

    draw.text(((width - w1) // 2, start_y), main_line1, font=font_main, fill=COLOR_MAIN)
    draw.text(
        ((width - w2) // 2, start_y + h1 + gap),
        main_line2,
        font=font_main,
        fill=COLOR_MAIN,
    )

    # 細い白の横線
    line_y = start_y + h1 + h2 + gap + 60
    line_w = 100
    draw.line(
        [((width - line_w) // 2, line_y), ((width + line_w) // 2, line_y)],
        fill=COLOR_LINE,
        width=2,
    )

    # サブテキスト1行目
    w_sub1, h_sub1 = measure_text(draw, SUB_TEXT_1, font_sub_bold)
    draw.text(
        ((width - w_sub1) // 2, line_y + 40),
        SUB_TEXT_1,
        font=font_sub_bold,
        fill=COLOR_SUB,
    )

    # サブテキスト2行目
    w_sub2, _ = measure_text(draw, SUB_TEXT_2, font_sub_small)
    draw.text(
        ((width - w_sub2) // 2, line_y + 40 + h_sub1 + 20),
        SUB_TEXT_2,
        font=font_sub_small,
        fill=COLOR_SUB,
    )

    output_path = OUTPUT_DIR / "header_image_v2_ig.png"
    img.save(output_path, "PNG", quality=95)
    print(f"Instagram用ヘッダー保存: {output_path}")
    return output_path


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generate_threads_header()
    generate_instagram_post()
    print("完了")
