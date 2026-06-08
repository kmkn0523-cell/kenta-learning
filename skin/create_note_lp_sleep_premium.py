"""
有料Note用LP画像を生成するスクリプト（睡眠×肌・夜のうちに治す編）
サイズ: 1280×670px
スタイル: 深いネイビー（夜）×ゴールドの高級感デザイン＋月と星
出力: lp_sleep_premium.png
（create_note_lp_men_premium.py をベースに、夜テーマへ色とモチーフを差し替え）
"""
from PIL import Image, ImageDraw, ImageFont  # 画像を作るためのライブラリ

# ===== フォントの設定 =====
FONT_BOLD   = "/mnt/c/Windows/Fonts/BIZ-UDGothicB.ttc"   # 太字フォント
FONT_NORMAL = "/mnt/c/Windows/Fonts/BIZ-UDGothicR.ttc"   # 普通フォント

# ===== 画像サイズ =====
WIDTH  = 1280   # 横の大きさ（ピクセル）
HEIGHT = 670    # 縦の大きさ（ピクセル）

# ===== カラー定義 =====
BG_DARK    = (8, 10, 22)        # 深い夜の紺（左側・ほぼ黒）
BG_MID     = (20, 26, 52)       # 少し明るい夜の紺（右側グラデーション用）
GOLD       = (212, 175, 55)     # ゴールド（ラインナップ統一の差し色）
GOLD_LIGHT = (240, 210, 100)    # 明るいゴールド（ハイライト用）
GOLD_DARK  = (140, 110, 30)     # 暗いゴールド（影用）
WHITE      = (255, 255, 255)    # 白
OFF_WHITE  = (222, 226, 240)    # 少し青みのある白（サブテキスト用）
MOON       = (236, 239, 250)    # 月の色（やわらかい白）
STAR       = (210, 218, 245)    # 星の色（淡い銀青）


def lerp_color(c1, c2, t):
    """2色の間を補間して中間色を返す関数（グラデーション作成用）"""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_gradient_bg(img):
    """背景に横方向のグラデーションを描く（左=深い紺、右=少し明るい紺）"""
    draw = ImageDraw.Draw(img)
    for x in range(WIDTH):
        t = x / WIDTH                            # 0.0（左）〜 1.0（右）の比率
        color = lerp_color(BG_DARK, BG_MID, t)   # 左右で色を少しずつ変える
        draw.line([(x, 0), (x, HEIGHT)], fill=color)


def draw_moon(draw):
    """右上に月（やわらかい光の輪つき）を描く"""
    cx, cy = 1060, 235     # 月の中心座標（右上）
    radius = 92            # 月の半径

    # まわりのやわらかい光（外側ほど薄い同心円）
    for r in range(radius + 6, radius + 130, 7):
        fade = max(8, 46 - (r - radius) // 3)      # 外側ほど薄くする
        glow = (
            MOON[0] * fade // 100,
            MOON[1] * fade // 100,
            MOON[2] * fade // 100,
        )
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=glow, width=1)

    # 月本体（塗りつぶしの円）
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=MOON)

    # 月の表面の薄いクレーター（少し暗い円を3つ）
    crater = lerp_color(MOON, BG_MID, 0.18)        # 月よりほんの少し暗い色
    for dx, dy, cr in [(-30, -22, 16), (24, 10, 22), (-8, 36, 11)]:
        draw.ellipse([cx + dx - cr, cy + dy - cr, cx + dx + cr, cy + dy + cr], fill=crater)


def draw_sparkle(draw, x, y, size, color):
    """4方向にのびる星（きらめき）を描く"""
    # 縦線・横線
    draw.line([(x, y - size), (x, y + size)], fill=color, width=2)
    draw.line([(x - size, y), (x + size, y)], fill=color, width=2)
    # 中心の小さな点
    draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=color)


def draw_stars(draw):
    """夜空の星を固定位置に散らす（毎回同じ絵になるよう座標は固定）"""
    # (x, y, size) のリスト
    stars = [
        (905, 120, 9), (1190, 150, 7), (1135, 320, 8),
        (980, 400, 6), (1215, 430, 9), (880, 300, 6),
        (1060, 470, 7), (940, 520, 8),
    ]
    for x, y, size in stars:
        draw_sparkle(draw, x, y, size, STAR)
    # 小さな点の星も少し散らす
    dots = [(960, 200, 2), (1110, 90, 2), (1240, 270, 2),
            (900, 440, 2), (1180, 360, 2), (1020, 150, 2)]
    for x, y, r in dots:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=STAR)


def draw_decorative_lines(draw):
    """ゴールドの水平装飾ラインを上下に描く"""
    draw.rectangle([0, 0, WIDTH, 5], fill=GOLD)                       # 上部：太いライン
    draw.rectangle([0, 12, WIDTH, 14], fill=GOLD_DARK)               # 上部：細いライン
    draw.rectangle([0, HEIGHT - 5, WIDTH, HEIGHT], fill=GOLD)        # 下部：太いライン
    draw.rectangle([0, HEIGHT - 14, WIDTH, HEIGHT - 12], fill=GOLD_DARK)  # 下部：細いライン


def draw_inner_frame(draw):
    """内側に細いゴールドの枠線を描いて額縁感を出す"""
    margin = 22
    draw.rectangle([margin, margin, WIDTH - margin, HEIGHT - margin], outline=GOLD_DARK, width=1)


def draw_corner_ornaments(draw):
    """4隅にゴールドの装飾（L字ライン）を描く"""
    size, thick, margin = 40, 3, 28
    corners = [
        (margin, margin, 1, 1),
        (WIDTH - margin, margin, -1, 1),
        (margin, HEIGHT - margin, 1, -1),
        (WIDTH - margin, HEIGHT - margin, -1, -1),
    ]
    for cx, cy, dx, dy in corners:
        hx0, hx1 = sorted([cx, cx + dx * size])
        hy0, hy1 = sorted([cy, cy + dy * thick])
        draw.rectangle([hx0, hy0, hx1, hy1], fill=GOLD)
        vx0, vx1 = sorted([cx, cx + dx * thick])
        vy0, vy1 = sorted([cy, cy + dy * size])
        draw.rectangle([vx0, vy0, vx1, vy1], fill=GOLD)


def draw_diamond(draw, x, y, size, color):
    """ひし形（◆）を描く装飾用関数"""
    points = [(x, y - size), (x + size, y), (x, y + size), (x - size, y)]
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

    # ===== 右側の夜空（星→月の順で重ねる）=====
    draw_stars(draw)
    draw_moon(draw)

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
    tag_x, tag_y, tag_pad = 65, 48, 14
    draw_rounded_rect(
        draw,
        (tag_x, tag_y, tag_x + tag_w + tag_pad * 2, tag_y + tag_h + tag_pad),
        radius=8, fill=BG_DARK, outline=GOLD, outline_width=2,
    )
    draw.text((tag_x + tag_pad, tag_y + tag_pad // 2), tag_text, font=font_tag, fill=GOLD)

    # ===== 区切り線（バッジ下）=====
    line_y = tag_y + tag_h + tag_pad + 18
    draw.rectangle([65, line_y, 65 + tag_w + tag_pad * 2, line_y + 1], fill=GOLD_DARK)

    # ===== メインキャッチコピー（小） =====
    font_catch = ImageFont.truetype(FONT_BOLD, 30)
    catch_text = "本当は、夜に治っている。"
    draw.text((68, line_y + 18), catch_text, font=font_catch, fill=GOLD_LIGHT)

    # ===== メインタイトル（大） =====
    font_title = ImageFont.truetype(FONT_BOLD, 78)
    title_line1 = "肌が生まれ変わる"
    title_line2 = "夜の過ごし方"
    draw.text((65, line_y + 62),  title_line1, font=font_title, fill=WHITE)
    draw.text((65, line_y + 152), title_line2, font=font_title, fill=WHITE)

    # ===== サブタイトル =====
    font_sub = ImageFont.truetype(FONT_NORMAL, 25)
    sub_text = "成長ホルモン・深睡眠・夜のルーティンで肌を内側から変える完全ガイド"
    draw.text((68, line_y + 252), sub_text, font=font_sub, fill=OFF_WHITE)

    # ===== ひし形の装飾（サブタイトル下に3つ並べる）=====
    diamond_y = line_y + 340
    for i, color in enumerate([GOLD_DARK, GOLD, GOLD_DARK]):
        draw_diamond(draw, 78 + i * 22, diamond_y, 5, color)

    # ===== 特典テキスト =====
    font_point = ImageFont.truetype(FONT_BOLD, 26)
    points = [
        "◆  肌が治る睡眠の仕組み",
        "◆  夜を壊す3大要因と対策",
        "◆  今夜からの夜ルーティン＋7日チャレンジ",
    ]
    for i, text in enumerate(points):
        draw.text((68, diamond_y + 18 + i * 38), text, font=font_point, fill=GOLD_LIGHT)

    # ===== 保存 =====
    save_path = "/home/kenta_kamijyo/skin/lp_sleep_premium.png"
    img.save(save_path)
    print(f"✅ 保存しました: {save_path}")


# ===== メイン処理 =====
if __name__ == "__main__":
    print("睡眠×肌プレミアムLP画像を生成中...\n")
    create_premium_image()
    print("\n🎉 完成しました！")
    print("保存先: /home/kenta_kamijyo/skin/lp_sleep_premium.png")
