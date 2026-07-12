from PIL import Image, ImageDraw, ImageFont
import os

notes = [
    {
        "filename": "lp_ketsuryu.png",
        "bg_color": (120, 20, 80),
        "accent_color": (255, 180, 220),
        "tag_text": "無料 note｜血流と肌",
        "title_lines": [
            "血流が止まると、",
            "肌への栄養も",
            "止まっていた。",
        ],
        "sub_text": "自律神経と血流が肌荒れを作るしくみ",
    },
    {
        "filename": "lp_alcohol.png",
        "bg_color": (60, 75, 20),
        "accent_color": (200, 220, 100),
        "tag_text": "無料 note｜飲酒と肌",
        "title_lines": [
            "飲み会翌日に",
            "肌が荒れるのは、",
            "必然だった。",
        ],
        "sub_text": "アルコールが肌を壊す3つのしくみ",
    },
]


def create_image(note):
    width, height = 1280, 670
    img = Image.new("RGB", (width, height), note["bg_color"])
    draw = ImageDraw.Draw(img)

    font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJKjp-Bold.otf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]

    def get_font(size):
        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    tag_font = get_font(28)
    title_font = get_font(72)
    sub_font = get_font(32)

    # Tag
    tag_x, tag_y = 60, 60
    tag_w = draw.textlength(note["tag_text"], font=tag_font) + 30
    draw.rounded_rectangle([tag_x, tag_y, tag_x + tag_w, tag_y + 46], radius=8, fill=note["accent_color"])
    draw.text((tag_x + 15, tag_y + 8), note["tag_text"], font=tag_font, fill=note["bg_color"])

    # Title
    line_h = 90
    start_y = 160
    for i, line in enumerate(note["title_lines"]):
        draw.text((60, start_y + i * line_h), line, font=title_font, fill=(255, 255, 255))

    # Sub text
    draw.text((60, height - 80), note["sub_text"], font=sub_font, fill=note["accent_color"])

    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, note["filename"])
    img.save(output_path)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    for note in notes:
        create_image(note)
    print("全画像の生成が完了しました。")
