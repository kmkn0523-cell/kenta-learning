# preview_card.py
# skinカードのデザインプレビュー用スクリプト（1枚だけ生成して確認する）
# 使い方: python3 skin/preview_card.py

from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1080, 1080

DARK       = (22, 48, 32)
GREEN      = (72, 160, 100)
PALE_GREEN = (232, 246, 236)
WHITE      = (255, 255, 255)
OFF_WHITE  = (250, 249, 246)
TEXT_DARK  = (22, 30, 24)
TEXT_GRAY  = (150, 160, 152)

FONT_JP = "/home/kenta_kamijyo/fonts/NotoSerifJP.otf"

SAMPLE = {
    "tag":   "砂糖とニキビ",
    "hook":  "ニキビが治らないのは\nスキンケアのせいじゃない",
    "title": "砂糖がニキビを\n作る仕組み",
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


def text_w(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]

def text_h(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]

def center_x(draw, text, font):
    return (W - text_w(draw, text, font)) // 2

def draw_lines_center(draw, text, font, fill, y, gap=6):
    """改行含むテキストを中央揃えで描画。終端Yを返す"""
    lines = text.split("\n")
    lh = text_h(draw, "あ", font) + gap
    for i, line in enumerate(lines):
        draw.text((center_x(draw, line, font), y + i * lh), line, font=font, fill=fill)
    return y + len(lines) * lh


def draw_card(data, output_path):
    img  = Image.new("RGB", (W, H), OFF_WHITE)
    draw = ImageDraw.Draw(img)

    # フォント（サイズを慎重に設定）
    f = {
        "tag":    ImageFont.truetype(FONT_JP, 24),
        "title":  ImageFont.truetype(FONT_JP, 64),
        "hook":   ImageFont.truetype(FONT_JP, 32),
        "flow":   ImageFont.truetype(FONT_JP, 36),
        "num":    ImageFont.truetype(FONT_JP, 28),
        "alabel": ImageFont.truetype(FONT_JP, 22),
        "action": ImageFont.truetype(FONT_JP, 30),
        "brand":  ImageFont.truetype(FONT_JP, 22),
    }

    PAD     = 68
    SPLIT_Y = 460     # ダーク/ホワイトの分割ライン

    # =====================================================
    # 上半分：ダーク背景
    # =====================================================
    draw.rectangle([0, 0, W, SPLIT_Y], fill=DARK)

    # タグバッジ
    tag_text = f"# {data['tag']}"
    tag_y    = 48
    tw = text_w(draw, tag_text, f["tag"])
    tp = 14
    draw.rounded_rectangle(
        [PAD - tp, tag_y - 8, PAD + tw + tp, tag_y + text_h(draw, tag_text, f["tag"]) + 8],
        radius=20, fill=GREEN
    )
    draw.text((PAD, tag_y), tag_text, font=f["tag"], fill=WHITE)

    # タイトル
    title_y      = 105
    title_bottom = draw_lines_center(draw, data["title"], f["title"], WHITE, title_y, gap=8)

    # 緑の細い区切り線
    div_y = title_bottom + 22
    draw.rectangle([(W - 60) // 2, div_y, (W + 60) // 2, div_y + 3], fill=GREEN)

    # フック文
    hook_y = div_y + 20
    draw_lines_center(draw, data["hook"], f["hook"], (185, 210, 192), hook_y, gap=6)

    # =====================================================
    # 下半分：ホワイト背景
    # =====================================================

    # --- レイアウト寸法を事前計算 ---
    BRAND_H    = 50      # 下部ブランドバーの高さ
    ACTION_H   = 190     # アクションボックスの高さ
    ACTION_GAP = 16      # フローとアクションボックスの間隔
    FLOW_TOP   = SPLIT_Y + 36

    action_top = H - BRAND_H - ACTION_H
    flow_bot   = action_top - ACTION_GAP

    # フロー図
    flow  = data["flow"]
    n     = len(flow)
    item_h = 64
    gap_h  = 22
    flow_total = item_h * n + gap_h * (n - 1)
    flow_avail = flow_bot - FLOW_TOP
    flow_start = FLOW_TOP + (flow_avail - flow_total) // 2  # 縦中央に配置

    for i, step in enumerate(flow):
        cy = flow_start + i * (item_h + gap_h) + item_h // 2

        # 角丸バッジ（薄緑）
        bs = 42
        bx = PAD
        by = cy - bs // 2
        draw.rounded_rectangle([bx, by, bx + bs, by + bs], radius=10, fill=PALE_GREEN)

        num = str(i + 1)
        nb  = draw.textbbox((0, 0), num, font=f["num"])
        draw.text(
            (bx + bs // 2 - (nb[0] + nb[2]) / 2,
             cy           - (nb[1] + nb[3]) / 2),
            num, font=f["num"], fill=GREEN
        )

        # テキスト
        tb = draw.textbbox((0, 0), step, font=f["flow"])
        draw.text(
            (bx + bs + 22, cy - (tb[1] + tb[3]) / 2),
            step, font=f["flow"], fill=TEXT_DARK
        )

        # 矢印（最後以外）
        if i < n - 1:
            ax    = bx + bs // 2
            ay_t  = flow_start + i * (item_h + gap_h) + item_h + 3
            ay_b  = ay_t + gap_h - 8
            draw.rectangle([ax - 2, ay_t, ax + 2, ay_b], fill=(180, 200, 184))
            draw.polygon([(ax - 8, ay_b), (ax + 8, ay_b), (ax, ay_b + 9)],
                         fill=(180, 200, 184))

    # --- アクションボックス ---
    abox_top = action_top
    abox_bot = action_top + ACTION_H
    draw.rounded_rectangle(
        [PAD, abox_top, W - PAD, abox_bot],
        radius=16, fill=PALE_GREEN
    )
    draw.rounded_rectangle(
        [PAD, abox_top, PAD + 6, abox_bot],
        radius=16, fill=GREEN
    )

    lbl_y = abox_top + 18
    draw.text((PAD + 24, lbl_y), "今すぐできること", font=f["alabel"], fill=GREEN)

    act_y = lbl_y + text_h(draw, "あ", f["alabel"]) + 14
    for action in data["actions"]:
        draw.text((PAD + 24, act_y), f"→  {action}", font=f["action"], fill=TEXT_DARK)
        act_y += text_h(draw, "あ", f["action"]) + 10

    # --- ブランドバー ---
    draw.rectangle([0, H - BRAND_H, W, H], fill=DARK)
    brand = "毎日1つ、肌荒れ改善のヒントを投稿中"
    bbb   = draw.textbbox((0, 0), brand, font=f["brand"])
    draw.text(
        ((W - (bbb[2] - bbb[0])) // 2, H - BRAND_H + (BRAND_H - (bbb[3] - bbb[1])) // 2),
        brand, font=f["brand"], fill=(155, 185, 162)
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"✅ 保存しました: {output_path}")


if __name__ == "__main__":
    output = "/home/kenta_kamijyo/skin/skin_images/preview.png"
    draw_card(SAMPLE, output)
    print(f"確認: code {output}")
