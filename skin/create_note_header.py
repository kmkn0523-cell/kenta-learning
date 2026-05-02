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
WIDTH  = 1920  # 横幅（ピクセル）
HEIGHT = 1006  # 縦幅（ピクセル）

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

    # noteのヘッダーは「縦中央の約200px帯」だけが表示される
    # 全要素をその範囲に収めるため、高さを事前に計算して中央揃えする

    CENTER_Y = HEIGHT // 2  # 縦中央 = 503px

    # ===== 背景装飾：右側の薄い円 =====
    draw.ellipse([900, 100, 2000, 1200], fill=(28, 18, 42))
    draw.ellipse([1100, 250, 1900, 1050], fill=(38, 25, 55))

    # ===== 左端のアクセントバー =====
    draw.rectangle([0, 0, 10, HEIGHT], fill=ACCENT_COLOR)

    # ===== フォントを準備 =====
    font_tag  = ImageFont.truetype(FONT_BOLD,   24)   # タグ
    font_main = ImageFont.truetype(FONT_BOLD,   96)   # メインコピー（1行にまとめる）
    font_sub  = ImageFont.truetype(FONT_NORMAL, 34)   # サブコピー

    tag_text  = "肌荒れ × 内側改善"
    main_text = "スキンケアでは、治らない。"
    sub_text  = "200万円の失敗で辿り着いた「食事・腸・睡眠の整え方」"

    # ===== 各行の高さを計算 =====
    tag_bbox  = draw.textbbox((0, 0), tag_text,  font=font_tag)
    main_bbox = draw.textbbox((0, 0), main_text, font=font_main)
    sub_bbox  = draw.textbbox((0, 0), sub_text,  font=font_sub)

    tag_h  = tag_bbox[3]  - tag_bbox[1]
    main_h = main_bbox[3] - main_bbox[1]
    sub_h  = sub_bbox[3]  - sub_bbox[1]

    tag_pad   = 10
    gap1      = 14   # タグ〜メインの間
    gap2      = 18   # メイン〜サブの間
    tag_total = tag_h + tag_pad  # タグバッジ全体の高さ

    # 全体の高さ → 縦中央になる開始Y座標を求める
    total_h = tag_total + gap1 + main_h + gap2 + sub_h
    start_y = CENTER_Y - total_h // 2

    # ===== タグバッジを描く =====
    tag_w   = tag_bbox[2] - tag_bbox[0]
    tag_x   = 80
    tag_y   = start_y
    draw_rounded_rect(
        draw,
        (tag_x, tag_y, tag_x + tag_w + tag_pad * 2, tag_y + tag_total),
        radius=6,
        fill=ACCENT_COLOR,
    )
    draw.text((tag_x + tag_pad, tag_y + tag_pad // 2), tag_text, font=font_tag, fill=(20, 15, 10))

    # ===== メインコピー（白 + 末尾「治らない。」だけゴールド）=====
    main_y = start_y + tag_total + gap1

    # 「スキンケアでは、」を白で描く
    part1      = "スキンケアでは、"
    part1_bbox = draw.textbbox((0, 0), part1, font=font_main)
    part1_w    = part1_bbox[2] - part1_bbox[0]
    draw.text((80, main_y), part1, font=font_main, fill=WHITE)

    # 「治らない。」をゴールドで続けて描く
    draw.text((80 + part1_w, main_y), "治らない。", font=font_main, fill=ACCENT_COLOR)

    # ===== サブコピー =====
    sub_y = main_y + main_h + gap2
    draw.text((82, sub_y), sub_text, font=font_sub, fill=LIGHT_GOLD)

    # ===== 右端に薄い「200万円」装飾 =====
    font_num = ImageFont.truetype(FONT_BOLD, 110)
    draw.text((1480, CENTER_Y - 70), "200万円", font=font_num, fill=(45, 32, 62))
    font_num_s = ImageFont.truetype(FONT_BOLD, 36)
    draw.text((1560, CENTER_Y + 52), "の失敗と答え", font=font_num_s, fill=(60, 45, 80))

    # ===== 保存 =====
    save_path = "/home/kenta_kamijyo/skin/note_header.png"
    img.save(save_path)
    print(f"✅ 保存しました: {save_path}")


# ===== メイン処理 =====
if __name__ == "__main__":
    print("noteヘッダー画像を生成中...")
    create_header()
    print("完成！")
