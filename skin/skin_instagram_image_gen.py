"""
skin_instagram_image_gen.py
skin_threads_posts.json の全テーマ分のInstagram用画像（1080×1080）を生成するスクリプト
使い方: python3 skin/skin_instagram_image_gen.py
"""

import json        # JSONファイルを読み込む道具
import os          # ファイル操作に使う道具
from PIL import Image, ImageDraw, ImageFont  # 画像を作るためのライブラリ

# ===== パス設定 =====
THIS_DIR   = os.path.dirname(__file__)                              # このスクリプトのフォルダ
POSTS_FILE = os.path.join(THIS_DIR, "skin_threads_posts.json")     # 投稿データ
OUTPUT_DIR = os.path.join(THIS_DIR, "skin_instagram_images")       # 画像の保存先
os.makedirs(OUTPUT_DIR, exist_ok=True)                             # フォルダがなければ作る

# ===== 画像サイズ =====
W, H = 1080, 1080  # Instagramの正方形サイズ

# ===== フォント =====
# ローカル環境のNotoSerifJP、なければNotoSansCJKを使う
_LOCAL_SERIF = "/home/kenta_kamijyo/fonts/NotoSerifJP.otf"
_NOTO_BOLD   = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
_NOTO_REG    = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

FONT_BOLD_PATH = _LOCAL_SERIF if os.path.exists(_LOCAL_SERIF) else _NOTO_BOLD
FONT_REG_PATH  = _NOTO_REG if os.path.exists(_NOTO_REG) else FONT_BOLD_PATH

# ===== 20色のカラーパレット（52テーマで循環して使う）=====
# (背景色, アクセントカラー)
PALETTE = [
    ((10, 25, 47),   (72, 202, 228)),   # ネイビー
    ((18, 52, 38),   (76, 175, 80)),    # 深緑
    ((58, 22, 22),   (200, 80, 80)),    # 深赤
    ((22, 50, 55),   (50, 160, 170)),   # ティール
    ((30, 28, 60),   (110, 100, 200)),  # インディゴ
    ((52, 38, 18),   (180, 130, 50)),   # アンバー
    ((45, 15, 45),   (180, 80, 180)),   # パープル
    ((40, 10, 10),   (220, 70, 50)),    # レッド
    ((10, 35, 55),   (60, 160, 240)),   # スカイ
    ((8, 40, 40),    (50, 200, 190)),   # シアン
    ((35, 15, 50),   (160, 90, 220)),   # バイオレット
    ((15, 45, 30),   (70, 180, 120)),   # エメラルド
    ((42, 12, 30),   (210, 80, 140)),   # ローズ
    ((20, 50, 15),   (120, 200, 80)),   # ライム
    ((50, 20, 15),   (230, 100, 70)),   # コーラル
    ((28, 28, 50),   (130, 130, 210)),  # ラベンダー
    ((48, 28, 5),    (210, 150, 40)),   # マスタード
    ((8, 35, 48),    (55, 175, 210)),   # セルリアン
    ((45, 10, 25),   (200, 70, 110)),   # クリムゾン
    ((50, 40, 5),    (210, 180, 40)),   # オリーブ
]


def draw_rounded_rect(draw, xy, radius, fill):
    """角丸の四角形を描く（バッジ用）"""
    x1, y1, x2, y2 = xy
    draw.ellipse([x1, y1, x1 + radius*2, y1 + radius*2], fill=fill)
    draw.ellipse([x2 - radius*2, y1, x2, y1 + radius*2], fill=fill)
    draw.ellipse([x1, y2 - radius*2, x1 + radius*2, y2], fill=fill)
    draw.ellipse([x2 - radius*2, y2 - radius*2, x2, y2], fill=fill)
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)


def wrap_text(draw, text, font, max_width):
    """テキストを指定幅で折り返してリストで返す"""
    lines = []
    for paragraph in text.split('\n'):
        if not paragraph.strip():
            continue
        current = ""
        for char in paragraph:
            test = current + char
            w = draw.textbbox((0, 0), test, font=font)[2]
            if w > max_width and current:
                lines.append(current)
                current = char
            else:
                current = test
        if current:
            lines.append(current)
    return lines


def get_hook_text(post_text):
    """投稿テキストの冒頭部分（最初の2段落まで）を抽出する"""
    paragraphs = [p.strip() for p in post_text.split('\n\n') if p.strip()]
    # チェックリスト（□）が含まれる段落は除外して前の段落だけ使う
    result = []
    for p in paragraphs[:2]:
        if '□' in p or p.startswith('□'):
            break
        result.append(p)
    return '\n'.join(result) if result else paragraphs[0] if paragraphs else ""


def create_image(thread_data, index):
    """
    1テーマ分の画像を作る
    thread_data: skin_threads_posts.json の1要素
    index: 0始まりのインデックス（色を決めるのに使う）
    """
    bg_color, accent_color = PALETTE[index % len(PALETTE)]
    bg_r, bg_g, bg_b       = bg_color
    acc_r, acc_g, acc_b    = accent_color

    # ===== 背景 =====
    img  = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    # ===== 右下に薄い装飾円（奥行き感）=====
    circle_outer = (min(bg_r+20, 255), min(bg_g+20, 255), min(bg_b+20, 255))
    circle_inner = (min(bg_r+32, 255), min(bg_g+32, 255), min(bg_b+32, 255))
    draw.ellipse([600, 480, 1230, 1110], fill=circle_outer)
    draw.ellipse([720, 580, 1200, 1080], fill=circle_inner)

    # ===== 左端のアクセントバー =====
    draw.rectangle([0, 0, 8, H], fill=accent_color)

    # ===== 上部バッジ「無料 note｜テーマ名」=====
    font_badge = ImageFont.truetype(FONT_BOLD_PATH, 30)
    badge_text = f"無料 note｜{thread_data['theme']}"
    bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 18
    bx, by = 60, 60
    draw_rounded_rect(draw, (bx, by, bx + bw + pad*2, by + bh + pad), radius=10, fill=accent_color)
    draw.text((bx + pad, by + pad // 2), badge_text, font=font_badge, fill=(15, 15, 15))

    # ===== メインのフックテキスト =====
    hook_raw = get_hook_text(thread_data['posts'][0])
    font_hook = ImageFont.truetype(FONT_BOLD_PATH, 76)
    max_text_w = W - 80 - 60  # 左パディング80 + 右パディング60
    hook_lines = wrap_text(draw, hook_raw, font_hook, max_text_w)

    # 最大4行まで（はみ出す場合は省略）
    if len(hook_lines) > 4:
        hook_lines = hook_lines[:4]

    hook_y = 180
    line_height = 88
    for line in hook_lines:
        draw.text((68, hook_y), line, font=font_hook, fill=(255, 255, 255))
        hook_y += line_height

    # ===== 仕切り線 =====
    divider_y = hook_y + 30
    draw.rectangle([68, divider_y, W - 60, divider_y + 3], fill=accent_color)

    # ===== 2投稿目から「今日からできること」を抜き出してサブテキスト表示 =====
    font_sub = ImageFont.truetype(FONT_REG_PATH, 36)
    sub_color = (min(acc_r+80, 255), min(acc_g+80, 255), min(acc_b+80, 255))

    # 2投稿目の最後3行（アクション項目）を抽出
    post2_lines = [l.strip() for l in thread_data['posts'][1].split('\n') if l.strip()]
    # 「①②③・」など行頭が記号の行を優先
    action_lines = [l for l in post2_lines if l and (l[0] in '①②③④⑤・・')]
    if not action_lines:
        action_lines = post2_lines[-3:]  # なければ末尾3行

    sub_y = divider_y + 28
    for line in action_lines[:3]:
        wrapped = wrap_text(draw, line, font_sub, max_text_w)
        for wl in wrapped[:1]:  # 1行ずつ
            draw.text((68, sub_y), wl, font=font_sub, fill=sub_color)
            sub_y += 50

    # ===== 下部のCTA =====
    font_cta = ImageFont.truetype(FONT_REG_PATH, 32)
    cta_text = "詳しくはプロフィールリンクのnoteで"
    cta_y = H - 100
    draw.text((68, cta_y), cta_text, font=font_cta, fill=(200, 200, 200))

    # ===== 下部アクセントバー =====
    draw.rectangle([0, H - 8, W, H], fill=accent_color)

    # ===== 保存 =====
    filename = f"theme{thread_data['id']:02d}.png"
    save_path = os.path.join(OUTPUT_DIR, filename)
    img.save(save_path)
    return filename


def main():
    print("=== Instagram用画像生成開始 ===\n")

    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    threads = data["threads"]
    print(f"テーマ数: {len(threads)}件\n")

    for i, thread in enumerate(threads):
        filename = create_image(thread, i)
        print(f"✅ {filename}（{thread['theme']}）")

    print(f"\n🎉 完成！保存先: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
