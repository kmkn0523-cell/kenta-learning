"""
skin_instagram_image_gen_v2.py
参考デザインに合わせた4パネル・インフォグラフィック型Instagram画像（1080×1080）を生成
使い方: python3 skin/skin_instagram_image_gen_v2.py
"""

import json
import os
from PIL import Image, ImageDraw, ImageFont

THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
POSTS_FILE = os.path.join(THIS_DIR, "skin_threads_posts.json")
OUTPUT_DIR = os.path.join(THIS_DIR, "skin_instagram_images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

W, H = 1080, 1080

# ===== フォント =====
_LOCAL = "/home/kenta_kamijyo/fonts/NotoSerifJP.otf"
_BOLD  = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
_REG   = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_B = _LOCAL if os.path.exists(_LOCAL) else _BOLD
FONT_R = _REG   if os.path.exists(_REG)   else FONT_B

# ===== 固定カラー =====
BG         = (247, 250, 253)   # ほぼ白の薄いブルーグレー
HEADER_BG  = (20, 42, 84)      # 濃いネイビー
WHITE      = (255, 255, 255)
PANEL_BG   = (255, 255, 255)   # パネル白
TEXT_DARK  = (22, 30, 52)      # 濃いネイビーテキスト
TEXT_MID   = (90, 100, 125)    # 中間グレーテキスト
FOOTER_BG  = (232, 242, 255)   # 薄いブルーフッター
FOOTER_TXT = (20, 42, 84)

# ===== テーマ別アクセントカラー（20色ループ）=====
ACCENTS = [
    (74, 144, 217), (76, 175, 80),  (200, 80, 80),  (50, 160, 170),
    (110,100, 200), (180,130,  50), (180, 80, 180), (220, 70,  50),
    (60, 160, 240), (50, 200, 190), (160, 90, 220), (70, 180, 120),
    (210, 80, 140), (120,200,  80), (230,100,  70), (130,130, 210),
    (210,150,  40), (55, 175, 210), (200, 70, 110), (210,180,  40),
]

# ===== レイアウト定数 =====
HEADER_H   = 195          # ヘッダー高さ
PAD        = 18           # 外側余白
GAP        = 14           # パネル間の隙間
PW         = (W - PAD*2 - GAP) // 2   # パネル幅 = 515
PH         = 370          # パネル高さ
PY1        = HEADER_H + 16             # 上段パネルのY
PY2        = PY1 + PH + GAP           # 下段パネルのY
PX         = [PAD, PAD + PW + GAP]    # 左・右パネルのX
FOOTER_Y   = PY2 + PH + 16            # フッターY（= 1001）


# ========== ユーティリティ ==========

def fnt(path, size):
    try:    return ImageFont.truetype(path, size)
    except: return ImageFont.load_default()


def rr(draw, xy, r, fill=None, outline=None, ow=2):
    """角丸四角形を描く"""
    x1, y1, x2, y2 = xy
    for x, y in [(x1,y1),(x2-r*2,y1),(x1,y2-r*2),(x2-r*2,y2-r*2)]:
        draw.ellipse([x, y, x+r*2, y+r*2], fill=fill or outline)
    draw.rectangle([x1+r, y1, x2-r, y2], fill=fill or outline)
    draw.rectangle([x1, y1+r, x2, y2-r], fill=fill or outline)
    if outline and fill:
        # アウトラインだけ描き直す
        for a1, a2, ex, ey in [
            (180,270, x1,y1), (270,360, x2-r*2,y1),
            (90, 180, x1,y2-r*2), (0, 90, x2-r*2,y2-r*2)
        ]:
            draw.arc([ex, ey, ex+r*2, ey+r*2], a1, a2, fill=outline, width=ow)
        draw.line([x1+r, y1, x2-r, y1], fill=outline, width=ow)
        draw.line([x1+r, y2, x2-r, y2], fill=outline, width=ow)
        draw.line([x1, y1+r, x1, y2-r], fill=outline, width=ow)
        draw.line([x2, y1+r, x2, y2-r], fill=outline, width=ow)


def wrap(draw, text, font, max_w):
    """テキストを指定幅で折り返してリスト返却"""
    lines = []
    for para in text.split('\n'):
        para = para.strip()
        if not para:
            continue
        cur = ''
        for ch in para:
            if draw.textbbox((0,0), cur+ch, font=font)[2] > max_w and cur:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        if cur:
            lines.append(cur)
    return lines


def draw_lines(draw, lines, font, x, y, color, line_h, max_lines=99):
    """複数行テキストを描画して次のY座標を返す"""
    for i, line in enumerate(lines[:max_lines]):
        draw.text((x, y), line, font=font, fill=color)
        y += line_h
    return y


# ========== コンテンツ抽出 ==========

def extract_numbered(text):
    NUMS = '①②③④⑤⑥⑦⑧⑨'
    return [l.strip() for l in text.split('\n') if l.strip() and l.strip()[0] in NUMS]


def extract_bullets(text):
    return [l.strip() for l in text.split('\n') if l.strip().startswith('・')]


def get_contents(thread):
    """
    4パネル分のコンテンツを抽出する
    returns: hook, causes(list), actions(list), theme_name
    """
    p0 = thread['posts'][0]
    p1 = thread['posts'][1]

    # Panel 1: フック文（最初の段落の最初の文）
    first_para = next((p.strip() for p in p0.split('\n\n') if p.strip() and '□' not in p), '')
    hook = first_para.split('\n')[0].strip()

    # Panel 2: 原因（番号付きリスト）
    numbered = extract_numbered(p1)
    bullets  = extract_bullets(p1)

    if len(numbered) >= 5:
        # 原因が多い場合は前半を原因、後半を対策に分割
        mid     = len(numbered) // 2
        causes  = numbered[:mid]
        actions = numbered[mid:]
    elif len(numbered) >= 2:
        causes  = numbered
        actions = bullets[:4] if bullets else []
    else:
        # 番号なし→矢印チェーンから抽出
        arrow_lines = [l.strip() for l in p1.split('\n') if '→' in l and len(l.strip()) < 40]
        causes  = arrow_lines[:4] if arrow_lines else [numbered[0]] if numbered else []
        actions = bullets[:4] if bullets else numbered[:3]

    # Panel 3: 対策がまだ空なら bullets
    if not actions:
        actions = bullets[:4]

    return hook, causes[:4], actions[:4]


# ========== パネル描画 ==========

def draw_panel_base(draw, px, py, accent):
    """パネルの白背景＋左アクセントバー＋ドロップシャドウ風"""
    # シャドウ（少しオフセット）
    rr(draw, (px+4, py+4, px+PW+4, py+PH+4), r=14, fill=(210, 218, 230))
    # パネル本体
    rr(draw, (px, py, px+PW, py+PH), r=14, fill=PANEL_BG)
    # 左アクセントバー
    draw.rectangle([px, py+14, px+6, py+PH-14], fill=accent)


def draw_number_badge(draw, px, py, num_str, accent):
    """「1」「2」などの丸バッジを描く"""
    cx, cy, r = px+34, py+34, 18
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=accent)
    f = fnt(FONT_B, 26)
    bx = draw.textbbox((0,0), num_str, font=f)
    draw.text((cx - (bx[2]-bx[0])//2, cy - (bx[3]-bx[1])//2), num_str, font=f, fill=WHITE)


def draw_panel_title(draw, px, py, title, accent):
    """パネルタイトルを描く（バッジの右横）"""
    f = fnt(FONT_B, 28)
    draw.text((px + 62, py + 20), title, font=f, fill=TEXT_DARK)
    # タイトル下の区切り線
    draw.rectangle([px+16, py+60, px+PW-16, py+62], fill=(220, 228, 240))


def draw_panel1(draw, px, py, accent, hook, theme):
    """パネル1: こんな悩みありませんか？"""
    draw_panel_base(draw, px, py, accent)
    draw_number_badge(draw, px, py, '1', accent)
    draw_panel_title(draw, px, py, 'こんな悩みありませんか？', accent)

    # 吹き出し風の引用ボックス
    qx1, qy1 = px+16, py+72
    qx2, qy2 = px+PW-16, py+72+160
    rr(draw, (qx1, qy1, qx2, qy2), r=10,
       fill=(240, 246, 255), outline=(180, 200, 230), ow=2)

    # フックテキスト
    f = fnt(FONT_B, 32)
    lines = wrap(draw, hook, f, qx2-qx1-24)
    draw_lines(draw, lines, f, qx1+14, qy1+14, TEXT_DARK, 40, max_lines=3)

    # テーマ名バッジ（下部）
    f2 = fnt(FONT_R, 26)
    label = f'テーマ：{theme}'
    draw.text((px+20, py+248), label, font=f2, fill=TEXT_MID)

    # チェックボックス風の固定悩みリスト
    f3 = fnt(FONT_R, 27)
    items = ['ニキビ・赤みが続く', 'テカリ・毛穴が気になる', 'スキンケアしても治らない']
    cy = py + 286
    for item in items:
        # チェックボックス
        rr(draw, (px+20, cy, px+44, cy+24), r=4, fill=(235,242,255), outline=accent, ow=2)
        draw.text((px+52, cy), item, font=f3, fill=TEXT_DARK)
        cy += 34


def draw_panel2(draw, px, py, accent, causes, theme):
    """パネル2: 原因を知ろう"""
    draw_panel_base(draw, px, py, accent)
    draw_number_badge(draw, px, py, '2', accent)
    draw_panel_title(draw, px, py, f'原因は"{theme}"にあった！', accent)

    f = fnt(FONT_R, 28)
    cy = py + 74
    for i, cause in enumerate(causes[:4]):
        # 番号丸（小）
        cr = 12
        cx_badge = px + 28
        draw.ellipse([cx_badge-cr, cy+cr-2, cx_badge+cr, cy+cr*3-2], fill=accent)
        num_f = fnt(FONT_B, 18)
        n = str(i+1)
        nb = draw.textbbox((0,0), n, font=num_f)
        draw.text((cx_badge-(nb[2]-nb[0])//2, cy+cr-(nb[3]-nb[1])//2),
                  n, font=num_f, fill=WHITE)

        # 原因テキスト
        cause_clean = cause.lstrip('①②③④⑤').strip()
        lines = wrap(draw, cause_clean, f, PW-70)
        draw_lines(draw, lines, f, px+50, cy, TEXT_DARK, 34, max_lines=2)

        # 矢印（最後以外）
        if i < len(causes) - 1:
            arr_y = cy + 34 * min(len(lines),2)
            draw.text((px+22, arr_y), '↓', font=fnt(FONT_B, 22), fill=accent)

        cy += 34 * min(len(lines), 2) + 28


def draw_panel3(draw, px, py, accent, actions):
    """パネル3: 今日からできること"""
    draw_panel_base(draw, px, py, accent)
    draw_number_badge(draw, px, py, '3', accent)
    draw_panel_title(draw, px, py, '今日からできること', accent)

    f = fnt(FONT_R, 28)
    cy = py + 76
    for action in actions[:4]:
        action_clean = action.lstrip('①②③④⑤・').strip()
        # チェックマーク丸
        draw.ellipse([px+16, cy+2, px+38, cy+24], fill=accent)
        f_ck = fnt(FONT_B, 18)
        draw.text((px+20, cy+2), '✓', font=f_ck, fill=WHITE)
        # テキスト
        lines = wrap(draw, action_clean, f, PW-60)
        draw_lines(draw, lines, f, px+50, cy, TEXT_DARK, 34, max_lines=2)
        cy += 34 * min(len(lines), 2) + 26


def draw_panel4(draw, px, py, accent):
    """パネル4: 変わること"""
    draw_panel_base(draw, px, py, accent)
    draw_number_badge(draw, px, py, '4', accent)
    draw_panel_title(draw, px, py, '変わること', accent)

    # 「〇日続けると…」メッセージ
    f_msg = fnt(FONT_B, 30)
    msg = '続けると変わる！'
    draw.text((px+20, py+76), msg, font=f_msg, fill=accent)

    # 変化リスト
    f = fnt(FONT_R, 28)
    changes = [
        'ニキビ・赤みが減ってくる',
        '肌のテカリが落ち着く',
        '肌に透明感が出てくる',
        'スキンケアの効果が上がる',
        '自分の肌に自信が持てる',
    ]
    cy = py + 124
    for item in changes:
        # チェックマーク（アクセントカラー）
        f_ck = fnt(FONT_B, 26)
        draw.text((px+18, cy), '✓', font=f_ck, fill=accent)
        draw.text((px+52, cy), item, font=f, fill=TEXT_DARK)
        cy += 40


# ========== ヘッダー描画 ==========

def draw_header(draw, accent, theme):
    # 背景
    draw.rectangle([0, 0, W, HEADER_H], fill=HEADER_BG)

    # 装飾ライン（斜線パターン）
    for i in range(-5, 20):
        x = i * 80
        draw.line([(x, 0), (x+60, HEADER_H)], fill=(30,55,105), width=2)

    # アクセントカラーの細いボーダー（下）
    draw.rectangle([0, HEADER_H-6, W, HEADER_H], fill=accent)

    # ✦ キラキラ装飾（左右）
    f_sp = fnt(FONT_B, 32)
    draw.text((52, 28), '✦', font=f_sp, fill=accent)
    draw.text((W-90, 28), '✦', font=f_sp, fill=accent)
    draw.text((32, 70), '✧', font=fnt(FONT_R, 20), fill=(150,180,230))
    draw.text((W-60, 72), '✧', font=fnt(FONT_R, 20), fill=(150,180,230))

    # 上部小テキスト
    f_sub = fnt(FONT_R, 26)
    sub = '肌は"内側"から変わる！'
    sb  = draw.textbbox((0,0), sub, font=f_sub)
    draw.text(((W-(sb[2]-sb[0]))//2, 22), sub, font=f_sub, fill=(180,200,235))

    # メインタイトル
    f_title = fnt(FONT_B, 64)
    title   = f'✦ {theme} ✦'
    tb      = draw.textbbox((0,0), title, font=f_title)
    draw.text(((W-(tb[2]-tb[0]))//2, 60), title, font=f_title, fill=WHITE)

    # アクセントカラーの下線
    tx = (W-(tb[2]-tb[0]))//2
    draw.rectangle([tx, 138, tx+(tb[2]-tb[0]), 141], fill=accent)

    # サブタイトル
    f_sub2 = fnt(FONT_R, 28)
    sub2   = '肌荒れの原因と今日からできる対策'
    s2b    = draw.textbbox((0,0), sub2, font=f_sub2)
    draw.text(((W-(s2b[2]-s2b[0]))//2, 150), sub2, font=f_sub2, fill=(160,185,225))


# ========== フッター描画 ==========

def draw_footer(draw, accent):
    fh = H - FOOTER_Y
    draw.rectangle([0, FOOTER_Y, W, H], fill=FOOTER_BG)
    draw.rectangle([0, FOOTER_Y, W, FOOTER_Y+3], fill=accent)
    f   = fnt(FONT_R, 26)
    txt = '✦ 肌は、スキンケアだけじゃ変わらない。内側から整えて、理想の肌へ！ ✦'
    tb  = draw.textbbox((0,0), txt, font=f)
    draw.text(((W-(tb[2]-tb[0]))//2, FOOTER_Y+(fh-(tb[3]-tb[1]))//2),
              txt, font=f, fill=FOOTER_TXT)


# ========== メイン生成関数 ==========

def create_image(thread, index):
    accent     = ACCENTS[index % len(ACCENTS)]
    hook, causes, actions = get_contents(thread)
    theme      = thread['theme']

    img  = Image.new('RGB', (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw_header(draw, accent, theme)

    # 4つのパネル
    draw_panel1(draw, PX[0], PY1, accent, hook, theme)
    draw_panel2(draw, PX[1], PY1, accent, causes, theme)
    draw_panel3(draw, PX[0], PY2, accent, actions)
    draw_panel4(draw, PX[1], PY2, accent)

    draw_footer(draw, accent)

    filename  = f"theme{thread['id']:02d}.png"
    save_path = os.path.join(OUTPUT_DIR, filename)
    img.save(save_path)
    return filename


def main():
    print('=== Instagram画像生成 v2（4パネル型）===\n')
    with open(POSTS_FILE, encoding='utf-8') as f:
        threads = json.load(f)['threads']

    print(f'テーマ数: {len(threads)}件\n')
    for i, t in enumerate(threads):
        fn = create_image(t, i)
        print(f'✅ {fn}（{t["theme"]}）')

    print(f'\n🎉 完成！保存先: {OUTPUT_DIR}')


if __name__ == '__main__':
    main()
