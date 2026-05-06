# preview_card.py
# skinカードのデザインプレビュー用スクリプト（1枚だけ生成して確認する）
# 使い方: python3 skin/preview_card.py

from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1080, 1080

# カラーパレット
DARK       = (22, 48, 32)      # 深緑ほぼ黒（上半分の背景）
GREEN      = (72, 160, 100)    # 明るい緑（アクセント）
PALE_GREEN = (235, 248, 238)   # 薄い緑（アクションボックス背景）
WHITE      = (255, 255, 255)
OFF_WHITE  = (250, 249, 246)   # 下半分の背景
TEXT_DARK  = (22, 30, 24)      # 本文ほぼ黒
TEXT_GRAY  = (130, 140, 132)   # 薄いテキスト
NUM_BG     = (235, 248, 238)   # 番号バッジ背景

FONT_JP = "/home/kenta_kamijyo/fonts/NotoSerifJP.otf"

SAMPLE = {
    "tag":     "砂糖とニキビ",
    "hook":    "ニキビが治らないのは\nスキンケアのせいじゃない",
    "title":   "砂糖がニキビを\n作る仕組み",
    "flow": [
        "糖質を摂りすぎる",
        "血糖値が急上昇する",
        "皮脂の分泌が増える",
        "毛穴が詰まりニキビになる",
    ],
    "actions": [
        "ジュースをお茶に替える",
        "おやつをナッツに替える",
        "2週間だけ試してみる",
    ]
}


def load_fonts():
    return {
        "tag":    ImageFont.truetype(FONT_JP, 26),
        "hook":   ImageFont.truetype(FONT_JP, 36),
        "title":  ImageFont.truetype(FONT_JP, 62),
        "flow":   ImageFont.truetype(FONT_JP, 38),
        "num":    ImageFont.truetype(FONT_JP, 32),
        "action": ImageFont.truetype(FONT_JP, 34),
        "label":  ImageFont.truetype(FONT_JP, 24),
        "brand":  ImageFont.truetype(FONT_JP, 24),
    }


def text_center_x(draw, text, font, width):
    """テキストを横中央に配置するX座標を返す"""
    bb = draw.textbbox((0, 0), text, font=font)
    return (width - (bb[2] - bb[0])) // 2


def draw_multiline_center(draw, text, font, fill, y, width, line_gap=8):
    """改行含むテキストを中央揃えで描画。描画後のY座標を返す"""
    lines = text.split("\n")
    lh = draw.textbbox((0, 0), "あ", font=font)[3] + line_gap
    for i, line in enumerate(lines):
        x = text_center_x(draw, line, font, width)
        draw.text((x, y + i * lh), line, font=font, fill=fill)
    return y + len(lines) * lh


def draw_card(data, output_path):
    img  = Image.new("RGB", (W, H), OFF_WHITE)
    draw = ImageDraw.Draw(img)
    f    = load_fonts()
    PAD  = 68

    # =====================================================
    # 上半分：ダーク背景エリア
    # =====================================================
    SPLIT_Y = 430
    draw.rectangle([0, 0, W, SPLIT_Y], fill=DARK)

    # タグ（小さな緑ラベル）
    tag_y = 52
    tag_text = f"# {data['tag']}"
    bb = draw.textbbox((0, 0), tag_text, font=f["tag"])
    tag_w = bb[2] - bb[0]
    tag_pad = 16
    tag_x = PAD
    draw.rounded_rectangle(
        [tag_x - tag_pad, tag_y - 8,
         tag_x + tag_w + tag_pad, tag_y + bb[3] + 8],
        radius=20, fill=GREEN
    )
    draw.text((tag_x, tag_y), tag_text, font=f["tag"], fill=WHITE)

    # タイトル（大きく・中央）
    title_y = 130
    title_bottom = draw_multiline_center(draw, data["title"], f["title"], WHITE, title_y, W, line_gap=10)

    # 緑の区切り線（細くシャープ）
    line_y = title_bottom + 28
    line_w = 80
    draw.rectangle([(W - line_w) // 2, line_y, (W + line_w) // 2, line_y + 3], fill=GREEN)

    # フック文（小さめ・グレーがかった白）
    hook_y = line_y + 24
    draw_multiline_center(draw, data["hook"], f["hook"], (190, 210, 195), hook_y, W, line_gap=6)

    # =====================================================
    # 下半分：ホワイトエリア
    # =====================================================

    # --- フロー図 ---
    flow   = data["flow"]
    n      = len(flow)
    item_h = 72
    gap_h  = 28
    flow_total = item_h * n + gap_h * (n - 1)
    flow_top   = SPLIT_Y + 36
    flow_avail = H - 200 - flow_top    # アクションボックス分を引く

    # フロー全体を縦中央に
    flow_start = flow_top + (flow_avail - flow_total) // 2

    for i, step in enumerate(flow):
        cy = flow_start + i * (item_h + gap_h) + item_h // 2

        # 番号バッジ（角丸正方形・薄緑）
        badge_s  = 44
        badge_x  = PAD
        badge_y  = cy - badge_s // 2
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_s, badge_y + badge_s],
            radius=10, fill=NUM_BG
        )
        num_text = str(i + 1)
        nb = draw.textbbox((0, 0), num_text, font=f["num"])
        draw.text(
            (badge_x + badge_s // 2 - (nb[0] + nb[2]) / 2,
             cy - (nb[1] + nb[3]) / 2),
            num_text, font=f["num"], fill=GREEN
        )

        # ステップテキスト
        tb = draw.textbbox((0, 0), step, font=f["flow"])
        draw.text(
            (badge_x + badge_s + 24, cy - (tb[1] + tb[3]) / 2),
            step, font=f["flow"], fill=TEXT_DARK
        )

        # 細いドット区切り線（最後以外）
        if i < n - 1:
            dot_y = flow_start + i * (item_h + gap_h) + item_h + gap_h // 2
            for dx in range(badge_x + badge_s // 2 - 1, badge_x + badge_s // 2 + 2):
                draw.rectangle([dx, flow_start + i*(item_h+gap_h) + item_h + 4,
                                 dx + 1, dot_y], fill=(180, 200, 182))

    # =====================================================
    # アクションボックス（下部固定）
    # =====================================================
    box_top = H - 210
    box_bot = H - 58
    draw.rounded_rectangle(
        [PAD, box_top, W - PAD, box_bot],
        radius=16, fill=PALE_GREEN
    )
    # 左の緑ライン
    draw.rounded_rectangle(
        [PAD, box_top, PAD + 6, box_bot],
        radius=16, fill=GREEN
    )

    # ラベル
    draw.text((PAD + 26, box_top + 18), "今すぐできること", font=f["label"], fill=GREEN)

    # アクション
    action_y = box_top + 52
    for action in data["actions"]:
        draw.text((PAD + 26, action_y), f"→  {action}", font=f["action"], fill=TEXT_DARK)
        action_y += draw.textbbox((0, 0), "あ", font=f["action"])[3] + 10

    # =====================================================
    # 最下部：ブランドバー
    # =====================================================
    draw.rectangle([0, H - 46, W, H], fill=DARK)
    brand = "毎日1つ、肌荒れ改善のヒントを投稿中"
    bb = draw.textbbox((0, 0), brand, font=f["brand"])
    draw.text(
        ((W - (bb[2] - bb[0])) // 2, H - 38),
        brand, font=f["brand"], fill=(160, 190, 165)
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"✅ 保存しました: {output_path}")


if __name__ == "__main__":
    output = "/home/kenta_kamijyo/skin/skin_images/preview.png"
    draw_card(SAMPLE, output)
    print(f"確認: code {output}")
