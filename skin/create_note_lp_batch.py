"""
記事06〜30のLP画像を一括生成するスクリプト
既存のcreate_note_lp_images.pyと同じデザイン・構造を使う
"""
import os, json
from PIL import Image, ImageDraw, ImageFont

_WIN_BOLD   = "/mnt/c/Windows/Fonts/BIZ-UDGothicB.ttc"
_NOTO_BOLD  = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
_WIN_NORMAL = "/mnt/c/Windows/Fonts/BIZ-UDGothicR.ttc"
_NOTO_REG   = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD   = _WIN_BOLD   if os.path.exists(_WIN_BOLD)   else _NOTO_BOLD
FONT_NORMAL = _WIN_NORMAL if os.path.exists(_WIN_NORMAL) else _NOTO_REG

WIDTH, HEIGHT = 1280, 670

# 記事06〜30のデザイン設定
notes = [
    {
        "filename": "lp_stress.png",
        "bg_color": (35, 8, 8),
        "accent_color": (220, 80, 80),
        "tag_text": "無料 note｜ストレス",
        "title_lines": ["ストレスで肌が荒れるのは、", "気のせいじゃ", "なかった。"],
        "sub_text": "コルチゾールが皮脂を増やす—内側から断つ方法",
    },
    {
        "filename": "lp_sugar.png",
        "bg_color": (38, 22, 5),
        "accent_color": (230, 150, 40),
        "tag_text": "無料 note｜砂糖・血糖値",
        "title_lines": ["「甘いもの食べると", "肌が荒れる」は", "本当だった。"],
        "sub_text": "血糖値スパイクが肌を壊すメカニズム",
    },
    {
        "filename": "lp_dairy.png",
        "bg_color": (8, 28, 38),
        "accent_color": (60, 180, 220),
        "tag_text": "無料 note｜乳製品",
        "title_lines": ["乳製品をやめたら", "肌荒れが治った。", "その理由。"],
        "sub_text": "牛乳のホルモンが皮脂を増やす科学的根拠",
    },
    {
        "filename": "lp_hydration.png",
        "bg_color": (5, 20, 40),
        "accent_color": (80, 160, 255),
        "tag_text": "無料 note｜水分補給",
        "title_lines": ["肌荒れの人の多くが、", "水をほとんど", "飲んでいなかった。"],
        "sub_text": "化粧水より「飲む水」が肌を変える理由",
    },
    {
        "filename": "lp_exercise.png",
        "bg_color": (8, 30, 12),
        "accent_color": (60, 200, 100),
        "tag_text": "無料 note｜運動",
        "title_lines": ["運動すると", "肌荒れが治る、", "は本当か？"],
        "sub_text": "有酸素運動が肌の炎症を抑えるしくみ",
    },
    {
        "filename": "lp_uv.png",
        "bg_color": (30, 25, 5),
        "accent_color": (240, 200, 50),
        "tag_text": "無料 note｜紫外線",
        "title_lines": ["「日焼けは肌荒れを", "悪化させる」を", "知らない人が多すぎる。"],
        "sub_text": "UVAが真皮を壊す—毎日の対策が必須な理由",
    },
    {
        "filename": "lp_probiotics.png",
        "bg_color": (18, 35, 10),
        "accent_color": (120, 200, 80),
        "tag_text": "無料 note｜腸内細菌",
        "title_lines": ["ヨーグルトを毎日", "食べても腸が", "整わない理由。"],
        "sub_text": "プロバイオティクスより「育てる」が先",
    },
    {
        "filename": "lp_vitamind.png",
        "bg_color": (35, 30, 5),
        "accent_color": (255, 200, 60),
        "tag_text": "無料 note｜ビタミンD",
        "title_lines": ["現代人のほとんどが", "ビタミンD不足。", "肌荒れの隠れた原因。"],
        "sub_text": "室内勤務・日焼け止めが招く慢性炎症",
    },
    {
        "filename": "lp_omega3.png",
        "bg_color": (5, 25, 38),
        "accent_color": (60, 180, 200),
        "tag_text": "無料 note｜オメガ3",
        "title_lines": ["肌の炎症が引かない人に", "共通していたのは、", "オメガ3不足だった。"],
        "sub_text": "脂質バランスを整えれば赤みが落ち着く",
    },
    {
        "filename": "lp_bloodsugar.png",
        "bg_color": (35, 10, 20),
        "accent_color": (220, 100, 140),
        "tag_text": "無料 note｜血糖値",
        "title_lines": ["毎食後に眠くなる人は、", "肌荒れも", "起きやすい。"],
        "sub_text": "血糖値スパイクを防ぐ食べ方3つ",
    },
    {
        "filename": "lp_leakygut.png",
        "bg_color": (12, 30, 25),
        "accent_color": (60, 200, 160),
        "tag_text": "無料 note｜腸漏れ",
        "title_lines": ["腸活してるのに", "肌が改善しない人に", "欠けている視点。"],
        "sub_text": "リーキーガットが慢性炎症を作るしくみ",
    },
    {
        "filename": "lp_hormone.png",
        "bg_color": (32, 8, 30),
        "accent_color": (200, 100, 220),
        "tag_text": "無料 note｜ホルモン",
        "title_lines": ["生理前に肌が荒れるのは", "「体質」じゃない。", "ホルモンと肌の関係。"],
        "sub_text": "プロゲステロンを知れば対策が変わる",
    },
    {
        "filename": "lp_cleansing.png",
        "bg_color": (8, 20, 38),
        "accent_color": (80, 140, 240),
        "tag_text": "無料 note｜洗顔",
        "title_lines": ["1日2回の洗顔が", "肌荒れを", "作っていた。"],
        "sub_text": "洗いすぎが皮脂を増やす悪循環を断つ",
    },
    {
        "filename": "lp_pillow.png",
        "bg_color": (20, 15, 35),
        "accent_color": (160, 140, 240),
        "tag_text": "無料 note｜生活習慣",
        "title_lines": ["肌荒れの原因が", "枕カバーだった。", "毎日触れるものを見直す。"],
        "sub_text": "スキンケア以前の「接触菌」対策",
    },
    {
        "filename": "lp_alcohol.png",
        "bg_color": (28, 10, 5),
        "accent_color": (220, 120, 60),
        "tag_text": "無料 note｜アルコール",
        "title_lines": ["お酒を飲んだ翌日、", "肌が荒れる理由。", "飲み方で変わる。"],
        "sub_text": "アセトアルデヒドと腸バリア—対策は飲み方にある",
    },
    {
        "filename": "lp_caffeine.png",
        "bg_color": (25, 18, 8),
        "accent_color": (200, 160, 80),
        "tag_text": "無料 note｜カフェイン",
        "title_lines": ["コーヒーを1日3杯以上", "飲んでいる人が", "肌荒れしやすい理由。"],
        "sub_text": "コルチゾール上昇・亜鉛流出—正しい飲み方",
    },
    {
        "filename": "lp_shampoo.png",
        "bg_color": (5, 30, 30),
        "accent_color": (60, 200, 180),
        "tag_text": "無料 note｜シャンプー",
        "title_lines": ["背中ニキビの9割は、", "シャンプーが", "原因だった。"],
        "sub_text": "お風呂の順番を変えるだけで改善する",
    },
    {
        "filename": "lp_nightfood.png",
        "bg_color": (8, 8, 30),
        "accent_color": (100, 100, 240),
        "tag_text": "無料 note｜食事時間",
        "title_lines": ["夜遅くに食べると", "肌が荒れる。", "「食べる時間」と肌の関係。"],
        "sub_text": "成長ホルモンを守る夜の食事ルール",
    },
    {
        "filename": "lp_gluten.png",
        "bg_color": (30, 25, 8),
        "accent_color": (200, 180, 60),
        "tag_text": "無料 note｜グルテン",
        "title_lines": ["「パンをやめたら", "肌が変わった」は", "本当か。"],
        "sub_text": "グルテン感受性と腸の炎症—2週間の除去で判断",
    },
    {
        "filename": "lp_bodytemp.png",
        "bg_color": (35, 12, 5),
        "accent_color": (240, 120, 60),
        "tag_text": "無料 note｜体温・血流",
        "title_lines": ["体温が低い人は、", "肌荒れが", "治りにくい。"],
        "sub_text": "温める習慣がターンオーバーを整える",
    },
    {
        "filename": "lp_additives.png",
        "bg_color": (15, 25, 8),
        "accent_color": (140, 200, 60),
        "tag_text": "無料 note｜添加物",
        "title_lines": ["コンビニ食が多い人の", "肌荒れが治りにくい、", "本当の理由。"],
        "sub_text": "乳化剤・人工甘味料が腸壁を傷める",
    },
    {
        "filename": "lp_sleepquality.png",
        "bg_color": (10, 8, 30),
        "accent_color": (120, 120, 255),
        "tag_text": "無料 note｜睡眠の質",
        "title_lines": ["7時間寝てるのに", "肌が回復しない人が", "見落としていること。"],
        "sub_text": "時間より「深さ」—成長ホルモンを最大化する",
    },
    {
        "filename": "lp_oral.png",
        "bg_color": (5, 28, 28),
        "accent_color": (60, 200, 200),
        "tag_text": "無料 note｜口腔ケア",
        "title_lines": ["歯周病がある人は、", "肌荒れも", "起きやすい。"],
        "sub_text": "口の慢性炎症が全身の炎症レベルを上げる",
    },
    {
        "filename": "lp_iron.png",
        "bg_color": (30, 8, 5),
        "accent_color": (220, 80, 60),
        "tag_text": "無料 note｜鉄分・貧血",
        "title_lines": ["「肌が回復しない」", "女性の多くが、", "隠れ貧血だった。"],
        "sub_text": "フェリチン不足がターンオーバーを止める",
    },
    {
        "filename": "lp_roadmap.png",
        "bg_color": (8, 20, 15),
        "accent_color": (60, 220, 140),
        "tag_text": "無料 note｜30日プログラム",
        "title_lines": ["内側から肌を整える", "30日ロードマップ。", "何から始めるかを決める。"],
        "sub_text": "引き算→食事→サプリ+習慣の順番で変わる",
    },
]


def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.ellipse([x1, y1, x1+radius*2, y1+radius*2], fill=fill)
    draw.ellipse([x2-radius*2, y1, x2, y1+radius*2], fill=fill)
    draw.ellipse([x1, y2-radius*2, x1+radius*2, y2], fill=fill)
    draw.ellipse([x2-radius*2, y2-radius*2, x2, y2], fill=fill)
    draw.rectangle([x1+radius, y1, x2-radius, y2], fill=fill)
    draw.rectangle([x1, y1+radius, x2, y2-radius], fill=fill)


def create_image(note_data):
    img  = Image.new("RGB", (WIDTH, HEIGHT), note_data["bg_color"])
    draw = ImageDraw.Draw(img)
    bg_r, bg_g, bg_b = note_data["bg_color"]
    accent_r, accent_g, accent_b = note_data["accent_color"]

    circle_outer = (min(bg_r+18,255), min(bg_g+18,255), min(bg_b+18,255))
    circle_inner = (min(bg_r+28,255), min(bg_g+28,255), min(bg_b+28,255))
    draw.ellipse([780, 200, 1480, 900], fill=circle_outer)
    draw.ellipse([900, 280, 1480, 870], fill=circle_inner)
    draw.rectangle([0, 0, 8, HEIGHT], fill=note_data["accent_color"])

    font_tag = ImageFont.truetype(FONT_BOLD, 28)
    tag_text = note_data["tag_text"]
    tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
    tag_w, tag_h = tag_bbox[2]-tag_bbox[0], tag_bbox[3]-tag_bbox[1]
    tag_pad, tag_x, tag_y = 16, 60, 55
    draw_rounded_rect(draw, (tag_x, tag_y, tag_x+tag_w+tag_pad*2, tag_y+tag_h+tag_pad), 10, note_data["accent_color"])
    draw.text((tag_x+tag_pad, tag_y+tag_pad//2), tag_text, font=font_tag, fill=(20,20,20))

    font_big   = ImageFont.truetype(FONT_BOLD, 88)
    font_small = ImageFont.truetype(FONT_BOLD, 62)
    current_y = 155
    for i, line in enumerate(note_data["title_lines"]):
        font = font_small if i == 2 else font_big
        draw.text((60, current_y), line, font=font, fill=(255,255,255))
        bbox = draw.textbbox((0, 0), line, font=font)
        current_y += (bbox[3]-bbox[1]) + 18

    font_sub = ImageFont.truetype(FONT_NORMAL, 32)
    sub_color = (min(accent_r+80,255), min(accent_g+80,255), min(accent_b+80,255))
    draw.text((62, current_y+20), note_data["sub_text"], font=font_sub, fill=sub_color)
    draw.rectangle([0, HEIGHT-8, WIDTH, HEIGHT], fill=note_data["accent_color"])

    save_path = f"/home/kenta_kamijyo/skin/{note_data['filename']}"
    img.save(save_path)
    print(f"✅ {save_path}")


if __name__ == "__main__":
    print("LP画像を一括生成中...\n")
    for note in notes:
        create_image(note)
    print(f"\n🎉 {len(notes)}枚生成完了")
