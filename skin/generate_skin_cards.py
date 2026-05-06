# generate_skin_cards.py
# skin 14テーマ分の投稿カード画像を一括生成するスクリプト
# 使い方: python3 skin/generate_skin_cards.py

from PIL import Image, ImageDraw, ImageFont
import os

W, H    = 1080, 1080
FONT_JP = "/home/kenta_kamijyo/fonts/NotoSerifJP.otf"

# =====================================================
# 14テーマ分のカードデータ＋カラーテーマ
# =====================================================
CARDS = [
    {
        "id": 1,
        "filename": "theme01.png",
        "dark":  (28, 42, 65),       # ネイビー
        "green": (70, 140, 190),     # スカイブルー
        "pale":  (228, 240, 250),
        "tag":   "肌荒れ原因チェック",
        "hook":  "肌荒れが治らない人\nこれ全員やってます",
        "title": "あなたの肌荒れ\n原因チェックリスト",
        "flow":  ["甘い飲み物を毎日飲んでいる", "就寝が深夜0時以降", "パン・麺が毎日の主食", "ストレスで食いしばり癖がある"],
        "actions": ["甘い飲み物をお茶に替える", "就寝を23時前にする", "パンを週3回以下にする"],
    },
    {
        "id": 2,
        "filename": "theme02.png",
        "dark":  (22, 48, 32),       # 深緑
        "green": (72, 160, 100),     # 緑
        "pale":  (232, 246, 236),
        "tag":   "腸と肌のつながり",
        "hook":  "「腸と肌はつながっている」\n科学的に証明されています",
        "title": "腸が荒れると\n肌に出る仕組み",
        "flow":  ["腸内の悪玉菌が増える", "腸壁に炎症が起きる（リーキーガット）", "有害物質が血液に漏れ出す", "肌に炎症として現れる"],
        "actions": ["発酵食品を毎日食べる", "甘い飲み物を水に替える", "食物繊維を意識して摂る"],
    },
    {
        "id": 3,
        "filename": "theme03.png",
        "dark":  (58, 22, 22),       # 深赤
        "green": (200, 80, 80),      # 赤
        "pale":  (252, 232, 232),
        "tag":   "砂糖とニキビ",
        "hook":  "ニキビが治らないのは\nスキンケアのせいじゃない",
        "title": "砂糖がニキビを\n作る仕組み",
        "flow":  ["糖質を摂りすぎる", "血糖値が急上昇する", "皮脂の分泌が増える", "毛穴が詰まりニキビになる"],
        "actions": ["ジュースをお茶に替える", "おやつをナッツに替える", "2週間だけ試してみる"],
    },
    {
        "id": 4,
        "filename": "theme04.png",
        "dark":  (22, 50, 55),       # ダークティール
        "green": (50, 160, 170),     # ティール
        "pale":  (228, 246, 248),
        "tag":   "洗顔のやりすぎ",
        "hook":  "念入りに洗顔してるのに\n肌が荒れる理由があります",
        "title": "洗いすぎると\n肌が荒れる仕組み",
        "flow":  ["洗いすぎで必要な皮脂まで落とす", "肌が皮脂不足を感じる", "皮脂を過剰に分泌する", "毛穴が詰まりニキビが悪化"],
        "actions": ["洗顔は1日2回まで", "朝は水かぬるま湯だけでもOK", "ゴシゴシこすらず泡で包む"],
    },
    {
        "id": 5,
        "filename": "theme05.png",
        "dark":  (30, 28, 60),       # ダークインディゴ
        "green": (110, 100, 200),    # パープル
        "pale":  (238, 236, 252),
        "tag":   "睡眠と肌",
        "hook":  "夜11時前に寝るだけで\n肌が変わります",
        "title": "睡眠中に起きている\n肌の修復",
        "flow":  ["眠ると成長ホルモンが分泌される", "就寝後30〜60分が最大分泌", "このホルモンが肌を再生する", "遅く寝るほど修復時間が短くなる"],
        "actions": ["就寝30分前にスマホをやめる", "夜8時以降のカフェインを避ける", "寝る前に白湯を飲む"],
    },
    {
        "id": 6,
        "filename": "theme06.png",
        "dark":  (52, 38, 18),       # ダークブラウン
        "green": (180, 130, 50),     # アンバー
        "pale":  (252, 244, 224),
        "tag":   "小麦とグルテン",
        "hook":  "毎日パンを食べている人に\n知ってほしいことがあります",
        "title": "グルテンが\n肌荒れを招く仕組み",
        "flow":  ["小麦のグルテンが腸壁を刺激する", "腸に穴が開きやすくなる", "有害物質が血液に漏れ出す", "全身で炎症→肌荒れになる"],
        "actions": ["2週間だけ小麦を減らしてみる", "白米・そば・芋類に置き換える", "変化を感じたら継続する"],
    },
    {
        "id": 7,
        "filename": "theme07.png",
        "dark":  (55, 32, 18),       # ダークオレンジ
        "green": (210, 110, 50),     # オレンジ
        "pale":  (252, 238, 224),
        "tag":   "ストレスと皮脂",
        "hook":  "「ストレスで肌が荒れる」は\n気のせいじゃありません",
        "title": "ストレスが\n肌を荒らす仕組み",
        "flow":  ["ストレスを受ける", "コルチゾールが増える", "皮脂の分泌が急増する", "腸のバリアも弱くなる"],
        "actions": ["1日10分、何もしない時間を作る", "深呼吸を1日3回行う", "好きなことを週1回以上やる"],
    },
    {
        "id": 8,
        "filename": "theme08.png",
        "dark":  (50, 28, 45),       # ダークワイン
        "green": (170, 80, 150),     # ピンク
        "pale":  (250, 232, 246),
        "tag":   "失敗談",
        "hook":  "8年間、全部間違えてた\n同じことしてた人いますか？",
        "title": "8年間やっていた\n間違いリスト",
        "flow":  ["1日3回の洗顔（逆効果）", "高い美容液の重ね塗り（意味なし）", "甘いヨーグルトを毎日（腸を荒らす）", "ニキビを触る・潰す（広がる）"],
        "actions": ["洗顔は夜1回だけにする", "化粧品をシンプルに減らす", "発酵食品を毎日食べる"],
    },
    {
        "id": 9,
        "filename": "theme09.png",
        "dark":  (30, 48, 22),       # オリーブグリーン
        "green": (120, 170, 60),     # ライムグリーン
        "pale":  (238, 248, 224),
        "tag":   "やめる習慣",
        "hook":  "やめたら肌が変わった\n7つの習慣",
        "title": "「足す」より「引く」\nが肌を変える",
        "flow":  ["1日3回以上の洗顔をやめる", "深夜0時以降の就寝をやめる", "甘いジュースを毎日飲むのをやめる", "ニキビを触る・潰すのをやめる"],
        "actions": ["まず1つだけやめてみる", "1週間続けて変化を観察する", "効果を感じたら次の1つへ"],
    },
    {
        "id": 10,
        "filename": "theme10.png",
        "dark":  (20, 46, 36),       # ダークミント
        "green": (50, 170, 120),     # エメラルドグリーン
        "pale":  (224, 246, 238),
        "tag":   "腸活食習慣",
        "hook":  "腸活で肌が変わった\n毎日の食事ルール",
        "title": "腸を整える\n食べ物と避ける食べ物",
        "flow":  ["発酵食品を毎日食べる（納豆・味噌）", "食物繊維を意識して摂る（野菜・きのこ）", "水を1日1.5L以上飲む", "砂糖・白小麦を減らす"],
        "actions": ["朝食に納豆か味噌汁を追加する", "間食をナッツや果物に替える", "甘い飲み物を水かお茶に替える"],
    },
    {
        "id": 11,
        "filename": "theme11.png",
        "dark":  (38, 36, 20),       # ダークゴールド
        "green": (180, 155, 50),     # ゴールド
        "pale":  (252, 248, 220),
        "tag":   "お金をかけない美肌",
        "hook":  "高い化粧品より\n先に変えるべきことがある",
        "title": "タダでできる\n最強の美肌習慣",
        "flow":  ["就寝を23時前にする（成長ホルモン）", "水を1日1.5L飲む（保湿）", "洗顔を1日2回に減らす", "砂糖・甘い飲み物をやめる"],
        "actions": ["今夜から23時前に寝る", "ペットボトルを水に替える", "洗顔料をシンプルなものに変える"],
    },
    {
        "id": 12,
        "filename": "theme12.png",
        "dark":  (38, 22, 58),       # ダークパープル
        "green": (130, 80, 200),     # バイオレット
        "pale":  (240, 232, 252),
        "tag":   "タイプ別診断",
        "hook":  "肌荒れのタイプを知ると\n対策が変わります",
        "title": "あなたはどのタイプ？\n肌荒れ3パターン",
        "flow":  ["皮脂が多い→糖質・脂質を見直す", "乾燥が強い→水分・睡眠を増やす", "赤み・炎症→腸活・ストレスを対策", "混合型→まず睡眠から整える"],
        "actions": ["自分のタイプを1つ決める", "そのタイプの対策を1つ試す", "2週間後に変化を確認する"],
    },
    {
        "id": 13,
        "filename": "theme13.png",
        "dark":  (18, 38, 58),       # ダークオーシャン
        "green": (50, 140, 200),     # オーシャンブルー
        "pale":  (224, 238, 252),
        "tag":   "水分と肌",
        "hook":  "肌の乾燥は外からじゃなく\n内側から治します",
        "title": "水を飲むだけで\n肌が変わる理由",
        "flow":  ["体内の水分が不足する", "皮膚への水分供給が減る", "肌が乾燥してバリアが弱まる", "外からの刺激で炎症が起きやすくなる"],
        "actions": ["朝起きたらコップ1杯の水を飲む", "甘い飲み物を水に替える", "1日1.5L目標で少しずつ増やす"],
    },
    {
        "id": 14,
        "filename": "theme14.png",
        "dark":  (32, 44, 28),       # ダークセージ
        "green": (100, 155, 80),     # セージグリーン
        "pale":  (234, 246, 228),
        "tag":   "亜鉛と皮脂",
        "hook":  "皮脂が多い人に\n足りていない栄養があります",
        "title": "亜鉛が皮脂を\nコントロールする仕組み",
        "flow":  ["亜鉛が不足する", "皮脂腺の調節ができなくなる", "皮脂が過剰に分泌される", "毛穴が詰まりニキビになる"],
        "actions": ["牡蠣・牛肉・納豆を意識して食べる", "精製食品（白米・白パン）を減らす", "まず食事から、次にサプリを検討"],
    },
]


# =====================================================
# 描画ユーティリティ
# =====================================================

def tw(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]

def th(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]

def cx(draw, text, font):
    return (W - tw(draw, text, font)) // 2

def draw_center_lines(draw, text, font, fill, y, gap=6):
    lines = text.split("\n")
    lh = th(draw, "あ", font) + gap
    for i, line in enumerate(lines):
        draw.text((cx(draw, line, font), y + i * lh), line, font=font, fill=fill)
    return y + len(lines) * lh


# =====================================================
# カード生成
# =====================================================

def draw_card(card, output_path):
    DARK  = card["dark"]
    GREEN = card["green"]
    PALE  = card["pale"]

    WHITE     = (255, 255, 255)
    OFF_WHITE = (250, 249, 246)
    TEXT_DARK = (28, 34, 28)

    img  = Image.new("RGB", (W, H), OFF_WHITE)
    draw = ImageDraw.Draw(img)

    f = {
        "tag":    ImageFont.truetype(FONT_JP, 24),
        "title":  ImageFont.truetype(FONT_JP, 62),
        "hook":   ImageFont.truetype(FONT_JP, 32),
        "flow":   ImageFont.truetype(FONT_JP, 36),
        "num":    ImageFont.truetype(FONT_JP, 28),
        "alabel": ImageFont.truetype(FONT_JP, 22),
        "action": ImageFont.truetype(FONT_JP, 30),
        "brand":  ImageFont.truetype(FONT_JP, 22),
    }

    PAD     = 68
    SPLIT_Y = 460

    # ---- 上半分：ダーク背景 ----
    draw.rectangle([0, 0, W, SPLIT_Y], fill=DARK)

    # タグバッジ
    tag_text = f"# {card['tag']}"
    tag_y    = 48
    tw_ = tw(draw, tag_text, f["tag"])
    tp  = 14
    draw.rounded_rectangle(
        [PAD - tp, tag_y - 8, PAD + tw_ + tp, tag_y + th(draw, tag_text, f["tag"]) + 8],
        radius=20, fill=GREEN
    )
    draw.text((PAD, tag_y), tag_text, font=f["tag"], fill=WHITE)

    # タイトル
    title_bottom = draw_center_lines(draw, card["title"], f["title"], WHITE, 105, gap=8)

    # 緑の区切り線
    div_y = title_bottom + 22
    draw.rectangle([(W - 60) // 2, div_y, (W + 60) // 2, div_y + 3], fill=GREEN)

    # フック文
    draw_center_lines(draw, card["hook"], f["hook"], (*PALE, 220) if len(PALE) == 3 else PALE, div_y + 20, gap=6)

    # ---- 下半分：ホワイト背景 ----
    BRAND_H  = 50
    ACTION_H = 188
    GAP      = 16
    FLOW_TOP = SPLIT_Y + 36
    action_top = H - BRAND_H - ACTION_H
    flow_bot   = action_top - GAP

    # フロー図
    flow   = card["flow"]
    n      = len(flow)
    item_h = 64
    gap_h  = 22
    total  = item_h * n + gap_h * (n - 1)
    avail  = flow_bot - FLOW_TOP
    start  = FLOW_TOP + (avail - total) // 2

    for i, step in enumerate(flow):
        cy_ = start + i * (item_h + gap_h) + item_h // 2

        bs = 42
        bx = PAD
        by = cy_ - bs // 2
        draw.rounded_rectangle([bx, by, bx + bs, by + bs], radius=10, fill=PALE)

        num = str(i + 1)
        nb  = draw.textbbox((0, 0), num, font=f["num"])
        draw.text(
            (bx + bs // 2 - (nb[0] + nb[2]) / 2,
             cy_           - (nb[1] + nb[3]) / 2),
            num, font=f["num"], fill=GREEN
        )

        tb = draw.textbbox((0, 0), step, font=f["flow"])
        draw.text(
            (bx + bs + 22, cy_ - (tb[1] + tb[3]) / 2),
            step, font=f["flow"], fill=TEXT_DARK
        )

        if i < n - 1:
            ax   = bx + bs // 2
            at   = start + i * (item_h + gap_h) + item_h + 3
            ab   = at + gap_h - 8
            draw.rectangle([ax - 2, at, ax + 2, ab], fill=(*PALE[:3],))
            draw.polygon([(ax - 8, ab), (ax + 8, ab), (ax, ab + 9)], fill=PALE)

    # アクションボックス
    abt = action_top
    abb = action_top + ACTION_H
    draw.rounded_rectangle([PAD, abt, W - PAD, abb], radius=16, fill=PALE)
    draw.rounded_rectangle([PAD, abt, PAD + 6, abb], radius=16, fill=GREEN)

    lbl_y = abt + 18
    draw.text((PAD + 24, lbl_y), "今すぐできること", font=f["alabel"], fill=GREEN)

    act_y = lbl_y + th(draw, "あ", f["alabel"]) + 14
    for action in card["actions"]:
        draw.text((PAD + 24, act_y), f"→  {action}", font=f["action"], fill=TEXT_DARK)
        act_y += th(draw, "あ", f["action"]) + 10

    # ブランドバー
    draw.rectangle([0, H - BRAND_H, W, H], fill=DARK)
    brand = "毎日1つ、肌荒れ改善のヒントを投稿中"
    bbb   = draw.textbbox((0, 0), brand, font=f["brand"])
    bw_   = bbb[2] - bbb[0]
    bh_   = bbb[3] - bbb[1]
    draw.text(
        ((W - bw_) // 2, H - BRAND_H + (BRAND_H - bh_) // 2),
        brand, font=f["brand"], fill=(*[min(c + 130, 255) for c in DARK],)
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")


def main():
    output_dir = "/home/kenta_kamijyo/skin/skin_images"
    print(f"14枚のカードを生成します...\n")
    for card in CARDS:
        path = os.path.join(output_dir, card["filename"])
        draw_card(card, path)
        print(f"✅ theme{card['id']:02d} ({card['tag']}) → {card['filename']}")
    print(f"\n🎉 全14枚の生成が完了しました！")
    print(f"保存先: {output_dir}/")


if __name__ == "__main__":
    main()
