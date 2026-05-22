# skin_instagram_image_gen_v4.py
# skin Instagram 用 8枚カルーセル画像生成スクリプト（v2 テンプレ）
# 使い方:
#   python3 skin/skin_instagram_image_gen_v4.py              # 全 v2 テーマを生成
#   python3 skin/skin_instagram_image_gen_v4.py --theme 1    # theme01 のみ生成

import os                                              # ファイル操作の道具
import json                                            # JSON 読み書きの道具
import argparse                                        # コマンドライン引数のパース
from pathlib import Path                               # ファイルパスの道具
from PIL import Image, ImageDraw, ImageFont            # 画像描画の道具

W, H        = 1080, 1080
FONT_JP     = "/home/kenta_kamijyo/fonts/NotoSerifJP.otf"
_DIR        = Path(__file__).resolve().parent
CONTENT     = _DIR / "carousel_content.json"
OUTPUT_DIR  = _DIR / "skin_instagram_carousels"
PAD_X       = 80
PAD_Y       = 120
LINE_GAP    = 10


# =====================================================
# 描画ユーティリティ
# =====================================================

def text_width(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def text_height(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


def draw_center_lines(draw, text, font, fill, y, gap=LINE_GAP):
    """改行で区切ったテキストを中央寄せで描く"""
    lines = text.split("\n")
    line_h = text_height(draw, "あ", font) + gap
    for i, line in enumerate(lines):
        x = (W - text_width(draw, line, font)) // 2
        draw.text((x, y + i * line_h), line, font=font, fill=fill)
    return y + len(lines) * line_h


def draw_left_aligned(draw, text, font, fill, x, y, gap=LINE_GAP, max_width=None):
    """テキストを左寄せで描く（長文用、行送りあり）"""
    lines = text.split("\n")
    line_h = text_height(draw, "あ", font) + gap
    for i, line in enumerate(lines):
        draw.text((x, y + i * line_h), line, font=font, fill=fill)
    return y + len(lines) * line_h


def draw_footer_bar(draw, dark_color):
    """全スライド共通のフッターバー（細いダーク帯＋ブランドコピー）"""
    bar_h = 50
    draw.rectangle([0, H - bar_h, W, H], fill=dark_color)
    font  = ImageFont.truetype(FONT_JP, 22)
    brand = "@skin_reset_jp ｜ 毎日肌改善のヒントを投稿中"
    bb    = draw.textbbox((0, 0), brand, font=font)
    bw    = bb[2] - bb[0]
    bh    = bb[3] - bb[1]
    light = tuple(min(c + 130, 255) for c in dark_color)
    draw.text(((W - bw) // 2, H - bar_h + (bar_h - bh) // 2), brand, font=font, fill=light)


# =====================================================
# スライド描画関数（役割別）
# =====================================================

def draw_cover(slide, colors, output_path):
    """スライド1: カバー（クラスタータグ＋フック＋著者）"""
    dark, accent, pale = colors
    img  = Image.new("RGB", (W, H), dark)
    draw = ImageDraw.Draw(img)

    font_cluster = ImageFont.truetype(FONT_JP, 28)
    cluster_tag  = slide.get("cluster_tag", "")
    if cluster_tag:
        bb = draw.textbbox((0, 0), cluster_tag, font=font_cluster)
        cw = bb[2] - bb[0]
        draw.text(((W - cw) // 2, 120), cluster_tag, font=font_cluster, fill=accent)

    font_title = ImageFont.truetype(FONT_JP, 72)
    font_sub   = ImageFont.truetype(FONT_JP, 30)

    title  = slide["title"]
    bottom = draw_center_lines(draw, title, font_title, pale, y=H // 2 - 220, gap=20)

    draw.rectangle([(W - 80) // 2, bottom + 30, (W + 80) // 2, bottom + 34], fill=accent)

    if slide.get("subtitle"):
        draw_center_lines(draw, slide["subtitle"], font_sub, pale, y=bottom + 60, gap=8)

    draw_footer_bar(draw, dark)
    img.save(output_path, "PNG")


def draw_hook(slide, colors, output_path):
    """スライド2: 共感フック（問題提起）"""
    dark, accent, pale = colors
    img  = Image.new("RGB", (W, H), (250, 249, 246))
    draw = ImageDraw.Draw(img)

    # 上部のアクセント帯
    draw.rectangle([0, 0, W, 120], fill=accent)
    font_label = ImageFont.truetype(FONT_JP, 28)
    label = "こんな悩みはありませんか？"
    bb = draw.textbbox((0, 0), label, font=font_label)
    draw.text((PAD_X, 120 // 2 - (bb[3] - bb[1]) // 2), label, font=font_label, fill=(255, 255, 255))

    # 本文
    font_body = ImageFont.truetype(FONT_JP, 40)
    body = slide.get("body", "")
    draw_left_aligned(draw, body, font_body, (28, 34, 28), x=PAD_X, y=200, gap=16)

    draw_footer_bar(draw, dark)
    img.save(output_path, "PNG")


def draw_point(slide, colors, output_path, point_number):
    """スライド3〜7: ポイントスライド（1枚1要点、4文構造）"""
    dark, accent, pale = colors
    img  = Image.new("RGB", (W, H), (250, 249, 246))
    draw = ImageDraw.Draw(img)

    # 番号バッジ
    badge_size = 90
    badge_x    = PAD_X
    badge_y    = PAD_Y
    draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size], fill=accent)
    font_num = ImageFont.truetype(FONT_JP, 48)
    num_text = f"{point_number}"
    bb = draw.textbbox((0, 0), num_text, font=font_num)
    nw, nh = bb[2] - bb[0], bb[3] - bb[1]
    draw.text((badge_x + (badge_size - nw) // 2, badge_y + (badge_size - nh) // 2 - 5), num_text, font=font_num, fill=(255, 255, 255))

    # 見出し
    font_heading = ImageFont.truetype(FONT_JP, 56)
    heading      = slide.get("heading", "")
    draw_left_aligned(draw, heading, font_heading, dark, x=badge_x + badge_size + 30, y=badge_y + 15, gap=10)

    # 本文（事実→具体例→数字→意味の4文）
    font_body = ImageFont.truetype(FONT_JP, 32)
    body      = slide.get("body", "")
    draw_left_aligned(draw, body, font_body, (28, 34, 28), x=PAD_X, y=badge_y + badge_size + 80, gap=14)

    draw_footer_bar(draw, dark)
    img.save(output_path, "PNG")


def draw_check(slide, colors, output_path, check_number):
    """スライド3〜7: 診断チェック項目（事実→影響→打ち手の3段構造）"""
    dark, accent, pale = colors
    img  = Image.new("RGB", (W, H), (250, 249, 246))
    draw = ImageDraw.Draw(img)

    badge_size = 90
    badge_x    = PAD_X
    badge_y    = PAD_Y
    draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size], fill=accent)
    font_num = ImageFont.truetype(FONT_JP, 36)
    num_text = f"{check_number}/5"
    bb = draw.textbbox((0, 0), num_text, font=font_num)
    nw, nh = bb[2] - bb[0], bb[3] - bb[1]
    draw.text((badge_x + (badge_size - nw) // 2, badge_y + (badge_size - nh) // 2 - 5), num_text, font=font_num, fill=(255, 255, 255))

    font_item = ImageFont.truetype(FONT_JP, 50)
    item_text = "□ " + slide.get("item", "")
    draw_left_aligned(draw, item_text, font_item, dark, x=PAD_X, y=badge_y + badge_size + 40, gap=12)

    font_label = ImageFont.truetype(FONT_JP, 24)
    font_body  = ImageFont.truetype(FONT_JP, 30)
    y_cursor = badge_y + badge_size + 200

    for label, key, color in [
        ("▼ なぜダメか (事実)", "fact",   (90, 90, 90)),
        ("▼ どうなるか (影響)", "impact", (90, 90, 90)),
        ("▼ 今夜の打ち手",      "action", accent),
    ]:
        draw.text((PAD_X, y_cursor), label, font=font_label, fill=color)
        y_cursor += 36
        body = slide.get(key, "")
        y_cursor = draw_left_aligned(draw, body, font_body, (28, 34, 28), x=PAD_X, y=y_cursor, gap=10)
        y_cursor += 28

    draw_footer_bar(draw, dark)
    img.save(output_path, "PNG")


def draw_cta(slide, colors, output_path):
    """スライド8: CTA（4軸ローテーション）"""
    dark, accent, pale = colors
    img  = Image.new("RGB", (W, H), dark)
    draw = ImageDraw.Draw(img)

    font_main = ImageFont.truetype(FONT_JP, 80)
    font_sub  = ImageFont.truetype(FONT_JP, 32)

    main_text = slide.get("text", "")
    bottom    = draw_center_lines(draw, main_text, font_main, pale, y=H // 2 - 200, gap=20)

    draw.rectangle([(W - 80) // 2, bottom + 30, (W + 80) // 2, bottom + 34], fill=accent)

    sub_text = slide.get("sub", "")
    if sub_text:
        draw_center_lines(draw, sub_text, font_sub, pale, y=bottom + 60, gap=10)

    draw_footer_bar(draw, dark)
    img.save(output_path, "PNG")


def draw_score_cta(slide, colors, output_path):
    """スライド8: スコア判定 + CTA"""
    dark, accent, pale = colors
    img  = Image.new("RGB", (W, H), dark)
    draw = ImageDraw.Draw(img)

    font_score_title = ImageFont.truetype(FONT_JP, 36)
    font_score_count = ImageFont.truetype(FONT_JP, 44)
    font_score_label = ImageFont.truetype(FONT_JP, 32)
    font_score_note  = ImageFont.truetype(FONT_JP, 24)

    draw.text((PAD_X, 100), "【あなたの当てはまり度】", font=font_score_title, fill=pale)

    y = 170
    for level in slide.get("score_levels", []):
        count_text = f"{level.get('count', '')} 個"
        label_text = level.get("label", "")
        note_text  = level.get("comment", "")
        draw.text((PAD_X,        y),      count_text, font=font_score_count, fill=accent)
        draw.text((PAD_X + 200,  y + 6),  label_text, font=font_score_label, fill=pale)
        draw.text((PAD_X + 200,  y + 50), note_text,  font=font_score_note,  fill=pale)
        y += 110

    draw.rectangle([PAD_X, y + 20, W - PAD_X, y + 24], fill=accent)

    font_cta_main = ImageFont.truetype(FONT_JP, 60)
    font_cta_sub  = ImageFont.truetype(FONT_JP, 28)
    cta_text = slide.get("cta_text", "")
    bottom   = draw_center_lines(draw, cta_text, font_cta_main, pale, y=y + 60, gap=14)
    cta_sub  = slide.get("cta_sub", "")
    if cta_sub:
        draw_center_lines(draw, cta_sub, font_cta_sub, pale, y=bottom + 30, gap=8)

    draw_footer_bar(draw, dark)
    img.save(output_path, "PNG")


# =====================================================
# テーマ別配色（generate_skin_cards.py の CARDS から流用）
# =====================================================

# theme_id -> (dark, accent, pale)
THEME_COLORS = {
    1:  ((28, 42, 65),   (70, 140, 190),  (228, 240, 250)),
    2:  ((22, 48, 32),   (72, 160, 100),  (232, 246, 236)),
    3:  ((58, 22, 22),   (200, 80, 80),   (252, 232, 232)),
    4:  ((22, 50, 55),   (50, 160, 170),  (228, 246, 248)),
    5:  ((30, 28, 60),   (110, 100, 200), (238, 236, 252)),
    6:  ((52, 38, 18),   (180, 130, 50),  (252, 244, 224)),
    7:  ((55, 32, 18),   (210, 110, 50),  (252, 238, 224)),
    8:  ((50, 28, 45),   (170, 80, 150),  (250, 232, 246)),
    9:  ((30, 48, 22),   (120, 170, 60),  (238, 248, 224)),
    10: ((20, 46, 36),   (50, 170, 120),  (224, 246, 238)),
    11: ((38, 36, 20),   (180, 155, 50),  (252, 248, 220)),
    12: ((38, 22, 58),   (130, 80, 200),  (240, 232, 252)),
    13: ((18, 38, 58),   (50, 140, 200),  (224, 238, 252)),
    14: ((32, 44, 28),   (100, 155, 80),  (234, 246, 228)),
    15: ((30, 50, 40),   (60, 170, 110),  (220, 248, 234)),
    16: ((28, 40, 58),   (70, 130, 195),  (224, 238, 252)),
    17: ((50, 35, 55),   (160, 90, 180),  (244, 232, 250)),
    18: ((18, 46, 54),   (45, 155, 175),  (220, 245, 250)),
    19: ((55, 28, 28),   (190, 80, 80),   (252, 228, 228)),
    20: ((26, 44, 30),   (80, 165, 95),   (228, 248, 232)),
    21: ((58, 22, 22),   (200, 80, 80),   (252, 232, 232)),  # cluster4 - エピソード
    22: ((22, 50, 55),   (50, 160, 170),  (228, 246, 248)),  # cluster4 - 数字
    23: ((30, 28, 60),   (110, 100, 200), (238, 236, 252)),  # cluster4 - 逆張り
    24: ((52, 38, 18),   (180, 130, 50),  (252, 244, 224)),  # cluster4 - エピソード
    25: ((55, 32, 18),   (210, 110, 50),  (252, 238, 224)),  # cluster5 - 数字
    26: ((50, 28, 45),   (170, 80, 150),  (250, 232, 246)),  # cluster5 - 逆張り
    27: ((30, 48, 22),   (120, 170, 60),  (238, 248, 224)),  # cluster5 - エピソード
    28: ((20, 46, 36),   (50, 170, 120),  (224, 246, 238)),  # cluster5 - 数字
    29: ((38, 36, 20),   (180, 155, 50),  (252, 248, 220)),  # cluster5 - 逆張り
    30: ((38, 22, 58),   (130, 80, 200),  (240, 232, 252)),  # cluster5 - エピソード
}


# =====================================================
# テーマ生成
# =====================================================

def generate_theme(theme: dict) -> None:
    """1テーマ分の8枚を生成する"""
    theme_id    = theme["id"]
    slides      = theme["slides"]
    slide_count = theme.get("slide_count", 5)

    if theme.get("version") != "v2":
        print(f"  ⏭️  theme{theme_id:02d}: v1 のためスキップ")
        return

    colors = THEME_COLORS.get(theme_id)
    if not colors:
        print(f"❌ theme{theme_id:02d}: 配色未定義")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    point_number = 0
    check_number = 0
    for i, slide in enumerate(slides, start=1):
        output = OUTPUT_DIR / f"theme{theme_id:02d}_slide{i}.png"
        slide_type = slide.get("type")

        if slide_type == "cover":
            draw_cover(slide, colors, output)
        elif slide_type == "hook":
            draw_hook(slide, colors, output)
        elif slide_type == "check":
            check_number += 1
            draw_check(slide, colors, output, check_number)
        elif slide_type == "point":
            point_number += 1
            draw_point(slide, colors, output, point_number)
        elif slide_type == "score" or slide_type == "cta":
            if "score_levels" in slide:
                draw_score_cta(slide, colors, output)
            else:
                draw_cta(slide, colors, output)
        else:
            print(f"  ⚠️ theme{theme_id:02d} slide{i}: 未対応タイプ '{slide_type}'")
            continue

        print(f"  ✅ theme{theme_id:02d}_slide{i}.png ({slide_type})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", type=int, help="指定テーマだけ生成（省略時は全 v2 を生成）")
    args = parser.parse_args()

    data   = json.loads(CONTENT.read_text(encoding="utf-8"))
    themes = data["themes"]

    if args.theme:
        themes = [t for t in themes if t["id"] == args.theme]
        if not themes:
            print(f"❌ theme{args.theme:02d} が見つかりません")
            return

    print(f"🎨 画像生成開始: {len(themes)} テーマ")
    for theme in themes:
        generate_theme(theme)
    print("🎉 完了")


if __name__ == "__main__":
    main()
