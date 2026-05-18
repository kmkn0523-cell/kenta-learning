"""
有料Note用LP画像を生成するスクリプト（男性特化編）
サイズ: 1280×670px
スタイル: 黒×ゴールドの高級感デザイン
出力: lp_men_premium.png
"""

from PIL import Image, ImageDraw, ImageFont  # 画像を作るためのライブラリ
import math  # 円の計算に使う

# ===== フォントの設定 =====
FONT_BOLD   = "/mnt/c/Windows/Fonts/BIZ-UDGothicB.ttc"
FONT_NORMAL = "/mnt/c/Windows/Fonts/BIZ-UDGothicR.ttc"

# ===== 画像サイズ =====
WIDTH  = 1280
HEIGHT = 670

# ===== カラー定義 =====
BG_DARK      = (10, 10, 12)          # ほぼ黒の背景
BG_MID       = (22, 18, 14)          # 少し暖かい黒（右側グラデーション用）
GOLD         = (212, 175, 55)        # ゴールド
GOLD_LIGHT   = (240, 210, 100)       # 明るいゴールド（ハイライト用）
GOLD_DARK    = (140, 110, 30)        # 暗いゴールド（影用）
WHITE        = (255, 255, 255)       # 白
OFF_WHITE    = (230, 225, 215)       # クリーム白（サブテキスト用）
GRAY_DARK    = (60, 55, 50)          # 暗いグレー（装飾用）


def lerp_color(c1, c2, t):
    """2色の間を補間して中間色を返す関数（グラデーション作成用）"""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_gradient_bg(img):
    """背景に横方向のグラデーションを描く（左=黒、右=暖かい黒）"""
    draw = ImageDraw.Draw(img)
    for x in range(WIDTH):
        t = x / WIDTH                               # 0.0（左）〜 1.0（右）の比率
        color = lerp_color(BG_DARK, BG_MID, t)     # 左右で色を少しずつ変える
        draw.line([(x, 0), (x, HEIGHT)], fill=color)


def draw_gold_circle_pattern(draw):
    """右側に薄いゴールドの同心円を描いて高級感を出す"""
    cx, cy = 1050, 335   # 円の中心座標（右寄り中央）
    for r in range(60, 400, 55):        # 半径60〜400まで55刻みで円を描く
        # 円を描くが、薄く見せるためにアルファ値相当の暗い色を使う
        opacity = max(15, 60 - r // 10)  # 外側ほど薄くなるよう透明度を調整
        color = (
            GOLD[0] * opacity // 100,
            GOLD[1] * opacity // 100,
            GOLD[2] * opacity // 100,
        )
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            outline=color,
            width=1,
        )


def draw_decorative_lines(draw):
    """ゴールドの水平装飾ラインを上下に描く"""
    # 上部：太いゴールドライン
    draw.rectangle([0, 0, WIDTH, 5], fill=GOLD)

    # 上部：細いゴールドライン（少し下）
    draw.rectangle([0, 12, WIDTH, 14], fill=GOLD_DARK)

    # 下部：太いゴールドライン
    draw.rectangle([0, HEIGHT - 5, WIDTH, HEIGHT], fill=GOLD)

    # 下部：細いゴールドライン（少し上）
    draw.rectangle([0, HEIGHT - 14, WIDTH, HEIGHT - 12], fill=GOLD_DARK)


def draw_inner_frame(draw):
    """内側に細いゴールドの枠線を描いて額縁感を出す"""
    margin = 22    # 外枠からの距離（ピクセル）
    draw.rectangle(
        [margin, margin, WIDTH - margin, HEIGHT - margin],
        outline=GOLD_DARK,
        width=1,
    )


def draw_corner_ornaments(draw):
    """4隅にゴールドの装飾（L字ライン）を描く"""
    size   = 40    # L字の長さ
    thick  = 3     # 線の太さ
    margin = 28    # 角からの距離

    corners = [
        # (x基点, y基点, x方向, y方向)
        (margin, margin, 1, 1),            # 左上
        (WIDTH - margin, margin, -1, 1),   # 右上
        (margin, HEIGHT - margin, 1, -1),  # 左下
        (WIDTH - margin, HEIGHT - margin, -1, -1),  # 右下
    ]
    for cx, cy, dx, dy in corners:
        # 横線（座標の大小を揃えてからrectangleに渡す）
        hx0, hx1 = sorted([cx, cx + dx * size])
        hy0, hy1 = sorted([cy, cy + dy * thick])
        draw.rectangle([hx0, hy0, hx1, hy1], fill=GOLD)
        # 縦線
        vx0, vx1 = sorted([cx, cx + dx * thick])
        vy0, vy1 = sorted([cy, cy + dy * size])
        draw.rectangle([vx0, vy0, vx1, vy1], fill=GOLD)


def draw_diamond(draw, x, y, size, color):
    """ひし形（◆）を描く装飾用関数"""
    points = [
        (x, y - size),     # 上
        (x + size, y),     # 右
        (x, y + size),     # 下
        (x - size, y),     # 左
    ]
    draw.polygon(points, fill=color)


def draw_rounded_rect(draw, xy, radius, fill, outline=None, outline_width=1):
    """角丸の四角形を描く関数"""
    x1, y1, x2, y2 = xy
    draw.ellipse([x1, y1, x1 + radius*2, y1 + radius*2], fill=fill)
    draw.ellipse([x2 - radius*2, y1, x2, y1 + radius*2], fill=fill)
    draw.ellipse([x1, y2 - radius*2, x1 + radius*2, y2], fill=fill)
    draw.ellipse([x2 - radius*2, y2 - radius*2, x2, y2], fill=fill)
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    if outline:
        draw.arc([x1, y1, x1 + radius*2, y1 + radius*2], 180, 270, fill=outline, width=outline_width)
        draw.arc([x2 - radius*2, y1, x2, y1 + radius*2], 270, 360, fill=outline, width=outline_width)
        draw.arc([x1, y2 - radius*2, x1 + radius*2, y2], 90, 180,  fill=outline, width=outline_width)
        draw.arc([x2 - radius*2, y2 - radius*2, x2, y2], 0, 90,    fill=outline, width=outline_width)
        draw.line([x1 + radius, y1, x2 - radius, y1], fill=outline, width=outline_width)
        draw.line([x1 + radius, y2, x2 - radius, y2], fill=outline, width=outline_width)
        draw.line([x1, y1 + radius, x1, y2 - radius], fill=outline, width=outline_width)
        draw.line([x2, y1 + radius, x2, y2 - radius], fill=outline, width=outline_width)


def create_premium_image():
    """プレミアムLP画像を1枚作る関数"""

    # ===== 背景（グラデーション）=====
    img  = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw_gradient_bg(img)
    draw = ImageDraw.Draw(img)

    # ===== 右側の円形装飾 =====
    draw_gold_circle_pattern(draw)

    # ===== 上下のゴールドライン =====
    draw_decorative_lines(draw)

    # ===== 内側の枠線 =====
    draw_inner_frame(draw)

    # ===== 4隅の角装飾 =====
    draw_corner_ornaments(draw)

    # ===== 左端のゴールドアクセントバー =====
    draw.rectangle([0, 0, 6, HEIGHT], fill=GOLD)

    # ===== 「有料 note｜完全保存版」バッジ =====
    font_tag = ImageFont.truetype(FONT_BOLD, 26)
    tag_text = "有料 note ｜ 完全保存版"
    tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
    tag_w    = tag_bbox[2] - tag_bbox[0]
    tag_h    = tag_bbox[3] - tag_bbox[1]
    tag_x    = 65
    tag_y    = 48
    tag_pad  = 14
    # バッジ背景：ゴールドの枠線付き角丸四角形
    draw_rounded_rect(
        draw,
        (tag_x, tag_y, tag_x + tag_w + tag_pad * 2, tag_y + tag_h + tag_pad),
        radius=8,
        fill=BG_DARK,
        outline=GOLD,
        outline_width=2,
    )
    draw.text((tag_x + tag_pad, tag_y + tag_pad // 2), tag_text, font=font_tag, fill=GOLD)

    # ===== 区切り線（バッジ下）=====
    line_y = tag_y + tag_h + tag_pad + 18
    draw.rectangle([65, line_y, 65 + tag_w + tag_pad * 2, line_y + 1], fill=GOLD_DARK)

    # ===== メインキャッチコピー（小） =====
    font_catch = ImageFont.truetype(FONT_BOLD, 30)
    catch_text = "男の肌は、変えた人だけが得をする。"
    draw.text((68, line_y + 18), catch_text, font=font_catch, fill=GOLD_LIGHT)

    # ===== メインタイトル（大） =====
    font_title = ImageFont.truetype(FONT_BOLD, 80)
    title_line1 = "男のための"
    title_line2 = "肌荒れ完全攻略"
    draw.text((65, line_y + 62),  title_line1, font=font_title, fill=WHITE)
    draw.text((65, line_y + 152), title_line2, font=font_title, fill=WHITE)

    # ===== サブタイトル =====
    font_sub = ImageFont.truetype(FONT_NORMAL, 26)
    sub_text = "ヒゲ剃り・テカリ・毛穴・ニキビ・乾燥を全部リセットする完全ロードマップ"
    draw.text((68, line_y + 252), sub_text, font=font_sub, fill=OFF_WHITE)

    # ===== ひし形の装飾（サブタイトル左端に3つ並べる）=====
    diamond_y = line_y + 340
    for i, color in enumerate([GOLD_DARK, GOLD, GOLD_DARK]):
        draw_diamond(draw, 78 + i * 22, diamond_y, 5, color)

    # ===== 特典テキスト =====
    font_point = ImageFont.truetype(FONT_BOLD, 26)
    points = [
        "◆  男の肌荒れ5大悩み別の処方箋",
        "◆  ヒゲ剃り・スキンケアの正しい順番",
        "◆  食事・睡眠・運動まで総合ロードマップ",
    ]
    for i, text in enumerate(points):
        draw.text((68, diamond_y + 18 + i * 38), text, font=font_point, fill=GOLD_LIGHT)

    # ===== 保存 =====
    save_path = "/home/kenta_kamijyo/skin/lp_men_premium.png"
    img.save(save_path)
    print(f"✅ 保存しました: {save_path}")


# ===== メイン処理 =====
if __name__ == "__main__":
    print("男性特化プレミアムLP画像を生成中...\n")
    create_premium_image()
    print("\n🎉 完成しました！")
    print("保存先: /home/kenta_kamijyo/skin/lp_men_premium.png")
