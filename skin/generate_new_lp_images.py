from PIL import Image, ImageDraw, ImageFont
import os

notes = [
    {
        "filename": "lp_inflammation.png",
        "bg_color": (160, 90, 20),
        "accent_color": (255, 210, 100),
        "tag_text": "無料 note｜炎症と肌",
        "title_lines": [
            "活性酸素が",
            "肌を壊していた。",
            "気づいたのは食後。",
        ],
        "sub_text": "慢性炎症と活性酸素が肌荒れを作るしくみ",
    },
    {
        "filename": "lp_mens_skin.png",
        "bg_color": (20, 100, 110),
        "accent_color": (160, 240, 240),
        "tag_text": "無料 note｜男性の肌",
        "title_lines": [
            "テカり・ニキビは",
            "テストステロンの",
            "せいだった。",
        ],
        "sub_text": "20〜40代男性の皮脂過剰を内側から改善する",
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
