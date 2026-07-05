from PIL import Image, ImageDraw, ImageFont
import os

notes = [
    {
        "filename": "lp_chokatsu.png",
        "bg_color": (34, 85, 34),
        "accent_color": (144, 238, 144),
        "tag_text": "無料 note｜腸活",
        "title_lines": [
            "腸を整えたら、",
            "肌荒れが",
            "止まった話。",
        ],
        "sub_text": "食事と腸内環境で肌が変わる理由",
    },
    {
        "filename": "lp_food.png",
        "bg_color": (101, 67, 33),
        "accent_color": (255, 218, 185),
        "tag_text": "無料 note｜食事",
        "title_lines": [
            "食べ物を変えたら、",
            "ニキビが",
            "消えていた。",
        ],
        "sub_text": "肌荒れを防ぐ食材と避けるべき食材",
    },
    {
        "filename": "lp_skincare.png",
        "bg_color": (70, 130, 180),
        "accent_color": (173, 216, 230),
        "tag_text": "無料 note｜スキンケア",
        "title_lines": [
            "スキンケアを",
            "シンプルにしたら、",
            "肌が回復した話。",
        ],
        "sub_text": "引き算スキンケアで肌バリアを守る方法",
    },
    {
        "filename": "lp_fasting.png",
        "bg_color": (72, 61, 139),
        "accent_color": (216, 191, 216),
        "tag_text": "無料 note｜断食",
        "title_lines": [
            "16時間断食で、",
            "肌が",
            "生まれ変わった。",
        ],
        "sub_text": "オートファジーが肌荒れを改善するしくみ",
    },
    {
        "filename": "lp_sleep.png",
        "bg_color": (25, 25, 112),
        "accent_color": (135, 206, 250),
        "tag_text": "無料 note｜睡眠",
        "title_lines": [
            "睡眠を変えたら、",
            "朝の肌が",
            "変わっていた。",
        ],
        "sub_text": "成長ホルモンと肌修復の深い関係",
    },
    {
        "filename": "lp_stress.png",
        "bg_color": (139, 60, 60),
        "accent_color": (255, 200, 180),
        "tag_text": "無料 note｜ストレスと肌",
        "title_lines": [
            "ストレスが",
            "肌を壊していた。",
            "気づいたのは退職後。",
        ],
        "sub_text": "コルチゾールと肌荒れの切れない関係",
    },
]


def create_image(note):
    width, height = 1200, 630
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
