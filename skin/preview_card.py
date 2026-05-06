# preview_card.py
# skinカードのデザインプレビュー用スクリプト（1枚だけ生成して確認する）
# 使い方: python3 preview_card.py

from PIL import Image, ImageDraw, ImageFont
import os

# カードサイズ（正方形 1080×1080）
W, H = 1080, 1080

# カラー定義
BG_COLOR    = (252, 250, 245)   # 背景：ほんのり温かみのあるホワイト
GREEN       = (72, 153, 96)     # アクセント：落ち着いた緑
DARK_GREEN  = (45, 100, 62)     # タイトル文字：濃い緑
TEXT_DARK   = (40, 40, 40)      # 本文：ほぼ黒
TEXT_LIGHT  = (120, 120, 120)   # サブテキスト：グレー
WHITE       = (255, 255, 255)   # 白

# フォントパス
FONT_JP = "/home/kenta_kamijyo/fonts/NotoSerifJP.otf"  # 日本語フォント

# サンプルデータ（砂糖とニキビ）
SAMPLE = {
    "title": "砂糖がニキビを作る仕組み",
    "points": [
        "糖質を摂りすぎる",
        "血糖値が急上昇する",
        "皮脂の分泌が増える",
        "毛穴が詰まりニキビになる",
    ]
}


def draw_card(data, output_path):
    """カード画像を1枚生成する"""

    # ---- ベース画像 ----
    img  = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # ---- 上部アクセントバー ----
    bar_h = 14
    draw.rectangle([0, 0, W, bar_h], fill=GREEN)

    # ---- フォント読み込み ----
    try:
        font_title  = ImageFont.truetype(FONT_JP, 64)   # タイトル
        font_point  = ImageFont.truetype(FONT_JP, 42)   # ポイント本文
        font_arrow  = ImageFont.truetype(FONT_JP, 38)   # 矢印
        font_brand  = ImageFont.truetype(FONT_JP, 34)   # ブランド名
        font_label  = ImageFont.truetype(FONT_JP, 28)   # ラベル
    except Exception as e:
        print(f"フォントエラー: {e}")
        return

    # ---- テーマラベル（小さめ・緑） ----
    label_y = 60
    draw.text((72, label_y), "肌荒れ改善のヒント", font=font_label, fill=GREEN)

    # ---- タイトル ----
    title_y = 130
    draw.text((72, title_y), data["title"], font=font_title, fill=DARK_GREEN)

    # ---- 区切り線（上） ----
    line_y1 = 240
    draw.rectangle([72, line_y1, W - 72, line_y1 + 2], fill=GREEN)

    # ---- ポイントリスト（フロー図風・矢印つなぎ） ----
    points = data["points"]
    n = len(points)

    # ポイント全体を縦方向に中央揃えするためにY開始位置を計算する
    point_h   = 80    # 1ポイントの高さ
    arrow_h   = 40    # 矢印の高さ
    block_h   = point_h * n + arrow_h * (n - 1)  # 全体の高さ
    area_top  = line_y1 + 30
    area_bot  = H - 160
    area_h    = area_bot - area_top
    start_y   = area_top + (area_h - block_h) // 2

    current_y = start_y
    for i, point in enumerate(points):
        # 番号バッジ（緑丸に白数字）
        badge_r  = 26   # バッジの半径
        badge_cx = 72 + badge_r
        badge_cy = current_y + point_h // 2

        draw.ellipse(
            [badge_cx - badge_r, badge_cy - badge_r,
             badge_cx + badge_r, badge_cy + badge_r],
            fill=GREEN
        )
        num_font = ImageFont.truetype(FONT_JP, 28)
        num_text = str(i + 1)
        nb = draw.textbbox((0, 0), num_text, font=num_font)
        nx = badge_cx - (nb[2] - nb[0]) // 2
        ny = badge_cy - (nb[3] - nb[1]) // 2
        draw.text((nx, ny), num_text, font=num_font, fill=WHITE)

        # ポイントテキスト
        text_x = badge_cx + badge_r + 24
        text_y = badge_cy - (draw.textbbox((0, 0), point, font=font_point)[3]) // 2
        draw.text((text_x, text_y), point, font=font_point, fill=TEXT_DARK)

        # 矢印（最後のポイントには入れない）
        if i < n - 1:
            arrow_x = badge_cx
            arrow_top = current_y + point_h + 4
            arrow_bot = arrow_top + arrow_h - 8
            # 縦線
            draw.rectangle([arrow_x - 2, arrow_top, arrow_x + 2, arrow_bot], fill=GREEN)
            # 三角矢印
            draw.polygon(
                [(arrow_x - 10, arrow_bot),
                 (arrow_x + 10, arrow_bot),
                 (arrow_x, arrow_bot + 12)],
                fill=GREEN
            )
            current_y += point_h + arrow_h
        else:
            current_y += point_h

    # ---- 区切り線（下） ----
    line_y2 = H - 130
    draw.rectangle([72, line_y2, W - 72, line_y2 + 2], fill=GREEN)

    # ---- ブランド名 ----
    brand_y = H - 100
    brand_text = "毎日1つ、肌荒れ改善のヒントを投稿中"
    bb = draw.textbbox((0, 0), brand_text, font=font_brand)
    brand_x = (W - (bb[2] - bb[0])) // 2   # 中央揃え
    draw.text((brand_x, brand_y), brand_text, font=font_brand, fill=TEXT_LIGHT)

    # ---- 下部アクセントバー ----
    draw.rectangle([0, H - bar_h, W, H], fill=GREEN)

    # ---- 保存 ----
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"✅ 保存しました: {output_path}")


if __name__ == "__main__":
    output = "/home/kenta_kamijyo/skin/skin_images/preview.png"
    draw_card(SAMPLE, output)
    print(f"\nVS Codeで確認してください: {output}")
