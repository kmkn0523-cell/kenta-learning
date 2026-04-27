# generate_ronin_cards.py
# @RoninWords用の書道カード画像を自動生成するスクリプト
# 使い方: python3 generate_ronin_cards.py

from PIL import Image, ImageDraw, ImageFont
import os

# カードのサイズ（Twitter推奨の正方形）
W, H = 1080, 1080

# 和紙風の背景色（日ごとに変わる）
PAPERS = ["#f0e6d0", "#ede0c8", "#f3e9d5", "#e8ddc8", "#f1e7d2"]

# ブランドカラー（赤）
RED = (158, 30, 14)

# フォントのパス
FONT_JP = "/home/kenta_kamijyo/fonts/NotoSerifJP.otf"

# 格言データ（Day01〜Day30）
proverbs = [
    {"day":  1, "jp": "一期一会",                   "roma": "Ichi go ichi e",                        "en": "This moment will never come again."},
    {"day":  2, "jp": "能ある鷹は爪を隠す",          "roma": "No aru taka wa tsume o kakusu",         "en": "A skilled hawk hides its talons."},
    {"day":  3, "jp": "七転び八起き",               "roma": "Nana korobi ya oki",                    "en": "Fall seven times. Rise eight."},
    {"day":  4, "jp": "背水の陣",                   "roma": "Haisui no jin",                         "en": "Fight with your back to the river."},
    {"day":  5, "jp": "諸行無常",                   "roma": "Shogyo mujo",                           "en": "Nothing in this world stays the same."},
    {"day":  6, "jp": "石の上にも三年",              "roma": "Ishi no ue ni mo san nen",              "en": "Even a cold stone warms."},
    {"day":  7, "jp": "虎穴に入らずんば虎子を得ず",  "roma": "Koketsu ni irazunba koji o ezu",        "en": "No reward without entering the den."},
    {"day":  8, "jp": "覚悟を決めた者は強い",        "roma": "Kakugo o kimeta mono wa tsuyoi",        "en": "One who has decided is unbreakable."},
    {"day":  9, "jp": "足るを知る",                 "roma": "Taru o shiru",                          "en": "Know when enough is enough."},
    {"day": 10, "jp": "実るほど頭を垂れる稲穂かな",  "roma": "Minoru hodo atama o tareru inaho kana", "en": "The richer the rice, the lower it bows."},
    {"day": 11, "jp": "初志貫徹",                   "roma": "Shoshi kantetsu",                       "en": "Stay true to what you set out to do."},
    {"day": 12, "jp": "急がば回れ",                 "roma": "Isogaba maware",                        "en": "The long way is often the shortest."},
    {"day": 13, "jp": "沈黙は金",                   "roma": "Chinmoku wa kin",                       "en": "Silence is gold."},
    {"day": 14, "jp": "継続は力なり",               "roma": "Keizoku wa chikara nari",               "en": "Consistency is strength."},
    {"day": 15, "jp": "以心伝心",                   "roma": "Ishin denshin",                         "en": "Heart speaks to heart without words."},
    {"day": 16, "jp": "千里の道も一歩から",          "roma": "Senri no michi mo ippo kara",           "en": "A thousand miles begins with one step."},
    {"day": 17, "jp": "出る杭は打たれる",            "roma": "Deru kui wa utareru",                   "en": "The nail that sticks up gets hammered."},
    {"day": 18, "jp": "好きこそものの上手なれ",      "roma": "Suki koso mono no jozu nare",           "en": "What you love, you'll master."},
    {"day": 19, "jp": "艱難汝を玉にす",             "roma": "Kannan nanji o tama ni su",             "en": "Hardship polishes you into a gem."},
    {"day": 20, "jp": "負けるが勝ち",               "roma": "Makeru ga kachi",                       "en": "Losing can be winning."},
    {"day": 21, "jp": "柔よく剛を制す",             "roma": "Ju yoku go o seisu",                    "en": "Softness overcomes hardness."},
    {"day": 22, "jp": "禍を転じて福となす",          "roma": "Wazawai o tenjite fuku to nasu",        "en": "Turn disaster into fortune."},
    {"day": 23, "jp": "窮すれば通ず",               "roma": "Kyu sureba tsuzu",                      "en": "When cornered, a way opens."},
    {"day": 24, "jp": "当たって砕けろ",              "roma": "Atatte kudakero",                       "en": "Charge in, even if you shatter."},
    {"day": 25, "jp": "情けは人の為ならず",          "roma": "Nasake wa hito no tame narazu",         "en": "Kindness to others is kindness to yourself."},
    {"day": 26, "jp": "型があるから型を破れる",      "roma": "Kata ga aru kara kata o yabureru",      "en": "Master the form, then break free."},
    {"day": 27, "jp": "一所懸命",                   "roma": "Isshoukenmei",                          "en": "Give everything to this one moment."},
    {"day": 28, "jp": "道を極めるには終わりがない",  "roma": "Michi o kiwameru ni wa owari ga nai",   "en": "The mastery of a path has no end."},
    {"day": 29, "jp": "武士は食わねど高楊枝",        "roma": "Bushi wa kuwanedo takayoji",            "en": "Dignity over comfort."},
    {"day": 30, "jp": "生き死に一如",               "roma": "Ikishi ni ichinyo",                     "en": "Life and death are one."},
]


def hex_to_rgb(hex_color):
    """16進数カラーコードをRGBに変換する"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def draw_vertical_text(draw, text, x, y, font, fill, char_spacing=8):
    """文字を1つずつ縦に並べて描画する"""
    current_y = y
    for char in text:
        draw.text((x, current_y), char, font=font, fill=fill)
        bbox = font.getbbox(char)
        char_h = bbox[3] - bbox[1]
        current_y += char_h + char_spacing
    # 最終的なY座標を返す（描画した高さがわかる）
    return current_y


def wrap_text(text, max_width, font, draw):
    """テキストを指定幅で折り返す"""
    words = text.split(' ')
    lines = []
    current_line = ''
    for word in words:
        test_line = current_line + (' ' if current_line else '') + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def generate_card(proverb, output_dir):
    """1枚の書道カード画像を生成する"""
    day = proverb["day"]
    paper_color = hex_to_rgb(PAPERS[(day - 1) % len(PAPERS)])

    # 画像を作成する
    img = Image.new('RGB', (W, H), paper_color)
    draw = ImageDraw.Draw(img)

    # ---- フォントを読み込む ----
    try:
        font_jp_large  = ImageFont.truetype(FONT_JP, 90)   # 漢字（大）
        font_jp_medium = ImageFont.truetype(FONT_JP, 60)   # 漢字（中）
        font_jp_small  = ImageFont.truetype(FONT_JP, 36)   # 漢字（小）
        font_en_large  = ImageFont.truetype(FONT_JP, 32)   # 英語
        font_en_medium = ImageFont.truetype(FONT_JP, 26)   # ローマ字
        font_en_small  = ImageFont.truetype(FONT_JP, 22)   # 小さい文字
    except Exception as e:
        print(f"フォントエラー: {e}")
        return

    # ---- 装飾的な外枠を描く ----
    margin = 40
    draw.rectangle([margin, margin, W - margin, H - margin],
                   outline=(*RED, 180), width=2)

    # 内側の細い線
    inner = margin + 12
    draw.rectangle([inner, inner, W - inner, H - inner],
                   outline=(*RED, 80), width=1)

    # ---- 上部：@RoninWords ブランド ----
    brand_text = "@RoninWords"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_en_small)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text(((W - brand_w) // 2, 68), brand_text, font=font_en_small,
              fill=(*RED, 200))

    # 区切り線
    draw.line([(inner + 20, 105), (W - inner - 20, 105)],
              fill=(*RED, 60), width=1)

    # ---- DAY番号 ----
    day_text = f"DAY {day:02d}"
    day_bbox = draw.textbbox((0, 0), day_text, font=font_en_small)
    day_w = day_bbox[2] - day_bbox[0]
    draw.text(((W - day_w) // 2, 118), day_text, font=font_en_small,
              fill=(80, 50, 20, 150))

    # ---- 日本語テキスト（縦書き） ----
    jp_text = proverb["jp"]

    # 文字数に応じてフォントサイズを選ぶ
    if len(jp_text) <= 5:
        jp_font = font_jp_large
        char_size = 95
    elif len(jp_text) <= 8:
        jp_font = font_jp_medium
        char_size = 68
    else:
        jp_font = font_jp_small
        char_size = 44

    # 縦書きの開始位置を計算する（中央に配置）
    total_height = len(jp_text) * (char_size + 6)
    start_y = (H - total_height) // 2 - 30
    # X位置（中央より少し右）
    start_x = W // 2 - char_size // 2 + 20

    # 日本語を縦に描画する
    draw_vertical_text(draw, jp_text, start_x, start_y, jp_font,
                       fill=(15, 8, 2), char_spacing=6)

    # ---- ローマ字（縦書き、左側） ----
    roma_x = start_x - (char_size // 2) - 50
    roma_y = start_y + 20
    draw_vertical_text(draw, proverb["roma"], roma_x, roma_y,
                       font=font_en_medium,
                       fill=(80, 50, 20, 160),
                       char_spacing=2)

    # ---- 区切り線（下） ----
    draw.line([(inner + 20, H - 180), (W - inner - 20, H - 180)],
              fill=(*RED, 60), width=1)

    # ---- 英語訳 ----
    en_text = f'"{proverb["en"]}"'
    lines = wrap_text(en_text, W - 160, font_en_large, draw)
    line_h = 44
    total_en_h = len(lines) * line_h
    en_start_y = H - 160 - total_en_h // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_en_large)
        line_w = bbox[2] - bbox[0]
        draw.text(((W - line_w) // 2, en_start_y + i * line_h),
                  line, font=font_en_large,
                  fill=(30, 15, 5, 200))

    # ---- 下部装飾 ----
    draw.line([(inner + 20, H - 90), (W - inner - 20, H - 90)],
              fill=(*RED, 40), width=1)

    sword = "⚔"
    try:
        sw_bbox = draw.textbbox((0, 0), sword, font=font_en_small)
        sw_w = sw_bbox[2] - sw_bbox[0]
        draw.text(((W - sw_w) // 2, H - 76), sword, font=font_en_small,
                  fill=(*RED, 120))
    except Exception:
        pass

    # ---- ファイルとして保存する ----
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"day{day:02d}.png")
    img.save(output_path, "PNG", quality=95)
    print(f"✅ Day{day:02d} 生成完了: {output_path}")


def main():
    output_dir = "/home/kenta_kamijyo/ronin_images"
    print(f"書道カード画像を生成します（{len(proverbs)}枚）...\n")
    for proverb in proverbs:
        generate_card(proverb, output_dir)
    print(f"\n🎉 全{len(proverbs)}枚の生成が完了しました！")
    print(f"保存先: {output_dir}/")


if __name__ == "__main__":
    main()
