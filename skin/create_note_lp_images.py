"""
Note用LP画像を3枚生成するスクリプト
サイズ: 1280×670px（Note.com標準サイズ）
スタイル: 濃い背景＋白文字のインパクト重視デザイン
"""

import os  # ファイルの存在確認に使う
from PIL import Image, ImageDraw, ImageFont  # 画像を作るためのライブラリ

# ===== フォントの設定 =====
# Windows（WSL2）にフォントがあればそれを使い、なければLinux用フォントを使う
_WIN_BOLD   = "/mnt/c/Windows/Fonts/BIZ-UDGothicB.ttc"
_WIN_NORMAL = "/mnt/c/Windows/Fonts/BIZ-UDGothicR.ttc"
_NOTO_BOLD  = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"    # Linux用日本語フォント
_NOTO_REG   = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc" # Linux用日本語フォント

FONT_BOLD   = _WIN_BOLD   if os.path.exists(_WIN_BOLD)   else _NOTO_BOLD
FONT_NORMAL = _WIN_NORMAL if os.path.exists(_WIN_NORMAL) else _NOTO_REG

# ===== 画像サイズ =====
WIDTH  = 1280  # 横幅（ピクセル）
HEIGHT = 670   # 縦幅（ピクセル）

# ===== 3枚分のデザイン設定 =====
notes = [
    {
        "filename": "lp_chokatsu.png",           # 保存するファイル名
        "bg_color": (18, 52, 38),                # 背景色（濃い緑）
        "accent_color": (76, 175, 80),           # アクセントカラー（明るい緑）
        "tag_text": "無料 note｜腸活",            # 上部タグの文字
        "title_lines": [                         # タイトルを行ごとに分割
            "肌荒れは",
            "腸から治す。",
            "今日からできる腸活3ステップ",
        ],
        "sub_text": "発酵食品・食物繊維・水分補給　この3つだけでOK",  # サブテキスト
    },
    {
        "filename": "lp_food.png",               # 保存するファイル名
        "bg_color": (45, 22, 8),                 # 背景色（濃いこげ茶）
        "accent_color": (231, 111, 81),          # アクセントカラー（オレンジ）
        "tag_text": "無料 note｜食べ物",          # 上部タグの文字
        "title_lines": [                         # タイトルを行ごとに分割
            "肌荒れを悪化させる",
            "食べ物5選と、",
            "代わりに食べるべきもの",
        ],
        "sub_text": "スキンケアより先に「食」を見直せば、肌は変わる",  # サブテキスト
    },
    {
        "filename": "lp_skincare.png",           # 保存するファイル名
        "bg_color": (10, 25, 47),                # 背景色（濃いネイビー）
        "accent_color": (72, 202, 228),          # アクセントカラー（水色）
        "tag_text": "無料 note｜スキンケア",      # 上部タグの文字
        "title_lines": [                         # タイトルを行ごとに分割
            "肌荒れを悪化させる",
            "洗顔・保湿の",
            "間違い",
        ],
        "sub_text": "頑張るほど悪化する？NG習慣を今すぐチェック",  # サブテキスト
    },
    {
        "filename": "lp_fasting.png",            # 保存するファイル名
        "bg_color": (18, 10, 38),                # 背景色（深い紫黒）
        "accent_color": (160, 100, 240),         # アクセントカラー（明るい紫）
        "tag_text": "無料 note｜ファスティング",  # 上部タグの文字
        "title_lines": [                         # タイトルを行ごとに分割
            "16時間食べないだけで、",
            "肌荒れが治る？",
            "ファスティングと肌の関係",
        ],
        "sub_text": "腸・オートファジー・血糖値　3つのしくみで肌が変わる",  # サブテキスト
    },
    {
        "filename": "lp_sleep.png",              # 保存するファイル名
        "bg_color": (8, 15, 35),                 # 背景色（深い夜空色）
        "accent_color": (100, 160, 255),         # アクセントカラー（月明かりの青白）
        "tag_text": "無料 note｜睡眠",            # 上部タグの文字
        "title_lines": [                         # タイトルを行ごとに分割
            "肌荒れの原因、",
            "夜にあった。",
            "睡眠と肌の深い関係",
        ],
        "sub_text": "スキンケアより先に「眠り方」を変えると肌が変わる",  # サブテキスト
    },
]


def draw_rounded_rect(draw, xy, radius, fill):
    """
    角丸の四角形を描く関数
    xy     : (左, 上, 右, 下) の座標
    radius : 角の丸み（ピクセル）
    fill   : 塗りつぶしの色
    """
    x1, y1, x2, y2 = xy
    # 角丸を4つの円 + 長方形で表現する
    draw.ellipse([x1, y1, x1 + radius*2, y1 + radius*2], fill=fill)         # 左上
    draw.ellipse([x2 - radius*2, y1, x2, y1 + radius*2], fill=fill)         # 右上
    draw.ellipse([x1, y2 - radius*2, x1 + radius*2, y2], fill=fill)         # 左下
    draw.ellipse([x2 - radius*2, y2 - radius*2, x2, y2], fill=fill)         # 右下
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)           # 横の長方形
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)           # 縦の長方形


def create_image(note_data):
    """
    1枚分のLP画像を作る関数
    note_data: 上のnotesリストの1要素
    """
    # ===== 背景を作る =====
    img  = Image.new("RGB", (WIDTH, HEIGHT), note_data["bg_color"])  # 単色の背景
    draw = ImageDraw.Draw(img)                                        # 描画ツールを準備

    bg_r, bg_g, bg_b = note_data["bg_color"]

    # ===== 右側に薄いグラデーション風の丸を置いて奥行き感を出す =====
    # （半透明は難しいので、少し明るくした同系色で代用する）
    accent_r, accent_g, accent_b = note_data["accent_color"]
    # 大きな円（右下）
    circle_color_outer = (
        min(bg_r + 18, 255),
        min(bg_g + 18, 255),
        min(bg_b + 18, 255),
    )
    draw.ellipse([780, 200, 1480, 900], fill=circle_color_outer)

    # 中くらいの円（右下）
    circle_color_inner = (
        min(bg_r + 28, 255),
        min(bg_g + 28, 255),
        min(bg_b + 28, 255),
    )
    draw.ellipse([900, 280, 1480, 870], fill=circle_color_inner)

    # ===== 左端のアクセントバー（縦線）=====
    draw.rectangle([0, 0, 8, HEIGHT], fill=note_data["accent_color"])

    # ===== 上部タグ（角丸の小さいバッジ）=====
    font_tag = ImageFont.truetype(FONT_BOLD, 28)         # タグ用フォント（小さめ）
    tag_text = note_data["tag_text"]
    tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)   # テキストの大きさを測る
    tag_w    = tag_bbox[2] - tag_bbox[0]                         # タグの横幅
    tag_h    = tag_bbox[3] - tag_bbox[1]                         # タグの縦幅
    tag_pad  = 16                                                # 内側の余白
    tag_x    = 60   # タグの左端X座標
    tag_y    = 55   # タグの上端Y座標

    # タグの背景（アクセントカラーの角丸四角形）
    draw_rounded_rect(
        draw,
        (tag_x, tag_y, tag_x + tag_w + tag_pad * 2, tag_y + tag_h + tag_pad),
        radius=10,
        fill=note_data["accent_color"],
    )
    # タグのテキスト（黒文字）
    draw.text((tag_x + tag_pad, tag_y + tag_pad // 2), tag_text, font=font_tag, fill=(20, 20, 20))

    # ===== メインタイトル =====
    font_title_big   = ImageFont.truetype(FONT_BOLD, 88)   # 1・2行目：大きいフォント
    font_title_small = ImageFont.truetype(FONT_BOLD, 62)   # 3行目：少し小さいフォント

    title_start_y = 155   # タイトルの開始Y座標
    line_gap      = 18    # 行間の追加余白

    current_y = title_start_y
    for i, line in enumerate(note_data["title_lines"]):
        # 3行目だけ少し小さくする
        font = font_title_small if i == 2 else font_title_big
        draw.text((60, current_y), line, font=font, fill=(255, 255, 255))  # 白文字で描く
        # 次の行の位置 = 現在Y + フォントの高さ + 行間
        bbox = draw.textbbox((0, 0), line, font=font)
        current_y += (bbox[3] - bbox[1]) + line_gap

    # ===== サブテキスト（小さい説明文）=====
    font_sub = ImageFont.truetype(FONT_NORMAL, 32)    # サブテキスト用フォント
    sub_color = (
        min(accent_r + 80, 255),
        min(accent_g + 80, 255),
        min(accent_b + 80, 255),
    )  # アクセントカラーより少し明るい色
    draw.text((62, current_y + 20), note_data["sub_text"], font=font_sub, fill=sub_color)

    # ===== 下部アクセントライン =====
    draw.rectangle([0, HEIGHT - 8, WIDTH, HEIGHT], fill=note_data["accent_color"])

    # ===== 保存 =====
    save_path = f"/home/kenta_kamijyo/skin/{note_data['filename']}"
    img.save(save_path)
    print(f"✅ 保存しました: {save_path}")


# ===== メイン処理（3枚分ループ）=====
if __name__ == "__main__":
    print("LP画像を生成中...\n")
    for note in notes:
        create_image(note)
    print("\n🎉 3枚すべて完成しました！")
    print("保存先: /home/kenta_kamijyo/skin/")
