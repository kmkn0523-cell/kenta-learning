"""
skin_instagram_image_gen_v2.py
4パネル・インフォグラフィック型Instagram画像（1080×1080）を生成
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

# ===== カラー =====
BG         = (247, 250, 253)
HEADER_BG  = (20, 42, 84)
WHITE      = (255, 255, 255)
PANEL_BG   = (255, 255, 255)
TEXT_DARK  = (22, 30, 52)
TEXT_MID   = (90, 100, 125)
FOOTER_BG  = (232, 242, 255)
FOOTER_TXT = (20, 42, 84)

# ===== アクセントカラー（20色ループ）=====
ACCENTS = [
    (74, 144, 217), (76, 175, 80),  (200, 80,  80), (50, 160, 170),
    (110, 100, 200),(180, 130,  50),(180,  80, 180),(220,  70,  50),
    ( 60, 160, 240),( 50, 200, 190),(160,  90, 220),( 70, 180, 120),
    (210,  80, 140),(120, 200,  80),(230, 100,  70),(130, 130, 210),
    (210, 150,  40),( 55, 175, 210),(200,  70, 110),(210, 180,  40),
]

# ===== レイアウト定数 =====
HEADER_H = 192
PAD      = 18
GAP      = 14
PW       = (W - PAD*2 - GAP) // 2   # = 515
PH       = 372
PY1      = HEADER_H + 16
PY2      = PY1 + PH + GAP
PX       = [PAD, PAD + PW + GAP]
FOOTER_Y = PY2 + PH + 16             # = 1002


# ========== ユーティリティ ==========

def fnt(path, size):
    try:    return ImageFont.truetype(path, size)
    except: return ImageFont.load_default()


def rr(draw, xy, r, fill):
    """角丸四角形（塗りつぶし）"""
    x1, y1, x2, y2 = xy
    draw.ellipse([x1, y1, x1+r*2, y1+r*2], fill=fill)
    draw.ellipse([x2-r*2, y1, x2, y1+r*2], fill=fill)
    draw.ellipse([x1, y2-r*2, x1+r*2, y2], fill=fill)
    draw.ellipse([x2-r*2, y2-r*2, x2, y2], fill=fill)
    draw.rectangle([x1+r, y1, x2-r, y2], fill=fill)
    draw.rectangle([x1, y1+r, x2, y2-r], fill=fill)


def draw_checkmark(draw, cx, cy, r, color, lw=3):
    """円の中にチェックマークを描く（フォント不要）"""
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color)
    # チェックの2本線
    draw.line([(cx-r//2+1, cy+1), (cx-r//5, cy+r//2)],  fill=WHITE, width=lw)
    draw.line([(cx-r//5, cy+r//2), (cx+r//2, cy-r//3)], fill=WHITE, width=lw)


def draw_diamond(draw, cx, cy, r, color):
    """ひし形（ヘッダー装飾）"""
    draw.polygon([(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)], fill=color)


def wrap(draw, text, font, max_w):
    """テキストを指定幅で折り返してリスト返却"""
    lines = []
    for para in text.split('\n'):
        para = para.strip()
        if not para:
            continue
        cur = ''
        for ch in para:
            if draw.textbbox((0, 0), cur + ch, font=font)[2] > max_w and cur:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        if cur:
            lines.append(cur)
    return lines


def draw_lines(draw, lines, font, x, y, color, line_h, max_lines=99):
    for line in lines[:max_lines]:
        draw.text((x, y), line, font=font, fill=color)
        y += line_h
    return y


# ========== コンテンツ抽出 ==========

def extract_numbered(text):
    NUMS = '①②③④⑤⑥⑦⑧⑨'
    return [l.strip() for l in text.split('\n') if l.strip() and l.strip()[0] in NUMS]


def extract_bullets(text):
    return [l.strip() for l in text.split('\n') if l.strip().startswith('・')]


def extract_arrows(text):
    """→ で始まる行を抽出（原因チェーン）"""
    return [l.strip()[1:].strip() for l in text.split('\n')
            if l.strip().startswith('→') and len(l.strip()) > 4]


def get_contents(thread):
    p0 = thread['posts'][0]
    p1 = thread['posts'][1]

    # フック: posts[0] の最初の文（チェックリスト除く）
    paras = [p.strip() for p in p0.split('\n\n') if p.strip() and '□' not in p]
    hook  = paras[0].split('\n')[0].strip() if paras else p0.split('\n')[0]

    numbered = extract_numbered(p1)
    bullets  = extract_bullets(p1)
    arrows   = extract_arrows(p1)

    if arrows:
        # パターンA: →チェーンが原因、①②③が対策
        causes  = arrows[:4]
        actions = numbered[:4] if numbered else bullets[:4]
    elif bullets and len(numbered) >= 3:
        # パターンB: ①②③が原因チェーン、・が対策
        causes  = numbered[:4]
        actions = bullets[:4]
    elif len(numbered) >= 5:
        # パターンC: 番号が多い→前半が原因、後半が対策
        causes  = numbered[:3]
        actions = numbered[3:]
    else:
        causes  = numbered[:4]
        actions = bullets[:4] if bullets else []

    # actionsが空なら numbered の後半から
    if not actions and numbered:
        actions = numbered[-3:]

    return hook, causes[:4], actions[:4]


# ========== パネル共通部品 ==========

def draw_panel_base(draw, px, py, accent):
    """シャドウ + 白パネル + 左アクセントバー"""
    rr(draw, (px+5, py+5, px+PW+5, py+PH+5), r=14, fill=(208, 218, 232))
    rr(draw, (px,   py,   px+PW,   py+PH),   r=14, fill=PANEL_BG)
    draw.rectangle([px, py+14, px+6, py+PH-14], fill=accent)


def draw_badge_number(draw, px, py, num, accent):
    """丸付き番号バッジ"""
    cx, cy, r = px + 36, py + 36, 20
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=accent)
    f = fnt(FONT_B, 28)
    b = draw.textbbox((0, 0), num, font=f)
    draw.text((cx - (b[2]-b[0])//2, cy - (b[3]-b[1])//2 - 1), num, font=f, fill=WHITE)


def draw_panel_title(draw, px, py, title, max_chars=13):
    """パネルタイトルと区切り線"""
    if len(title) > max_chars:
        title = title[:max_chars] + '…'
    f = fnt(FONT_B, 28)
    draw.text((px + 66, py + 22), title, font=f, fill=TEXT_DARK)
    draw.rectangle([px + 16, py + 62, px + PW - 16, py + 64], fill=(215, 225, 242))


# ========== 各パネル ==========

def draw_panel1(draw, px, py, accent, hook, theme):
    """パネル1: こんな悩みありませんか？"""
    draw_panel_base(draw, px, py, accent)
    draw_badge_number(draw, px, py, '1', accent)
    draw_panel_title(draw, px, py, 'こんな悩み、ありませんか？')

    # 引用ボックス（薄い背景）
    qx1, qy1 = px + 16, py + 72
    qx2, qy2 = px + PW - 16, py + 72 + 152
    rr(draw, (qx1, qy1, qx2, qy2), r=10, fill=(238, 245, 255))
    # 左ライン
    draw.rectangle([qx1, qy1+10, qx1+4, qy2-10], fill=accent)

    # フックテキスト
    f = fnt(FONT_B, 30)
    lines = wrap(draw, hook, f, qx2 - qx1 - 28)
    draw_lines(draw, lines, f, qx1 + 14, qy1 + 12, TEXT_DARK, 38, max_lines=3)

    # テーマラベル
    f2 = fnt(FONT_R, 24)
    draw.text((px + 20, py + 238), f'テーマ: {theme[:10]}', font=f2, fill=TEXT_MID)

    # チェックボックスリスト（固定の悩み3項目）
    f3   = fnt(FONT_R, 26)
    items = ['ニキビ・赤みが続く', 'テカリ・毛穴が気になる', 'スキンケアしても改善しない']
    iy   = py + 272
    for item in items:
        rr(draw, (px + 18, iy, px + 42, iy + 24), r=4, fill=(228, 238, 255))
        draw.rectangle([px + 18, iy, px + 42, iy + 24], fill=None)
        # チェックボックス枠線
        for dx, dy, ex, ey in [
            (px+18,iy,px+42,iy),(px+42,iy,px+42,iy+24),
            (px+18,iy+24,px+42,iy+24),(px+18,iy,px+18,iy+24)
        ]:
            draw.line([(dx,dy),(ex,ey)], fill=accent, width=2)
        draw.text((px + 50, iy), item, font=f3, fill=TEXT_DARK)
        iy += 33


def draw_panel2(draw, px, py, accent, causes, theme):
    """パネル2: 原因"""
    draw_panel_base(draw, px, py, accent)
    draw_badge_number(draw, px, py, '2', accent)
    # テーマ名は短縮して表示
    short = theme[:7] + '…' if len(theme) > 7 else theme
    draw_panel_title(draw, px, py, f'原因: {short}')

    f  = fnt(FONT_R, 27)
    fb = fnt(FONT_B, 18)
    cy = py + 74

    for i, cause in enumerate(causes[:4]):
        # 番号の小丸
        r = 13
        bx, by = px + 28, cy + 7
        draw.ellipse([bx-r, by-r, bx+r, by+r], fill=accent)
        n = str(i + 1)
        nb = draw.textbbox((0, 0), n, font=fb)
        draw.text((bx - (nb[2]-nb[0])//2, by - (nb[3]-nb[1])//2 - 1), n, font=fb, fill=WHITE)

        # 原因テキスト
        clean = cause.lstrip('①②③④⑤').strip()
        lines = wrap(draw, clean, f, PW - 68)
        used  = draw_lines(draw, lines, f, px + 50, cy, TEXT_DARK, 32, max_lines=2)

        # 矢印（最後以外）
        if i < len(causes) - 1:
            draw.polygon([
                (px + 28, used + 2),
                (px + 22, used + 14),
                (px + 34, used + 14),
            ], fill=accent)

        cy = used + 22


def draw_panel3(draw, px, py, accent, actions):
    """パネル3: 今日からできること"""
    draw_panel_base(draw, px, py, accent)
    draw_badge_number(draw, px, py, '3', accent)
    draw_panel_title(draw, px, py, '今日からできること')

    f  = fnt(FONT_R, 27)
    cy = py + 76

    for action in actions[:4]:
        clean = action.lstrip('①②③④⑤・').strip()
        # チェックマーク（PILで描画）
        draw_checkmark(draw, px + 28, cy + 13, 14, accent, lw=3)
        lines = wrap(draw, clean, f, PW - 66)
        used  = draw_lines(draw, lines, f, px + 52, cy, TEXT_DARK, 32, max_lines=2)
        cy = used + 22


def draw_panel4(draw, px, py, accent):
    """パネル4: 変わること"""
    draw_panel_base(draw, px, py, accent)
    draw_badge_number(draw, px, py, '4', accent)
    draw_panel_title(draw, px, py, '変わること')

    # 「続けると変わる！」メッセージ
    f_msg = fnt(FONT_B, 30)
    rr(draw, (px + 16, py + 72, px + PW - 16, py + 108), r=8, fill=accent)
    msg = '続けると、こう変わります！'
    mb  = draw.textbbox((0, 0), msg, font=f_msg)
    draw.text(((px + 16 + px + PW - 16)//2 - (mb[2]-mb[0])//2, py + 76),
              msg, font=f_msg, fill=WHITE)

    # チェックリスト（変化）
    f      = fnt(FONT_R, 27)
    changes = [
        'ニキビ・赤みが減ってくる',
        '肌のテカリが落ち着く',
        '肌に透明感が出てくる',
        'スキンケアの効果が上がる',
        '自分の肌に自信が持てる',
    ]
    cy = py + 120
    for item in changes:
        draw_checkmark(draw, px + 28, cy + 13, 14, accent, lw=3)
        draw.text((px + 52, cy), item, font=f, fill=TEXT_DARK)
        cy += 42


# ========== ヘッダー ==========

def draw_header(draw, accent, theme):
    draw.rectangle([0, 0, W, HEADER_H], fill=HEADER_BG)

    # 斜線装飾
    for i in range(-5, 20):
        draw.line([(i*80, 0), (i*80+60, HEADER_H)], fill=(30, 55, 108), width=2)

    # 下ボーダー
    draw.rectangle([0, HEADER_H-6, W, HEADER_H], fill=accent)

    # ひし形装飾（フォント不要）
    draw_diamond(draw, 55,  40, 12, accent)
    draw_diamond(draw, W-55, 40, 12, accent)
    draw_diamond(draw, 35,  70,  6, (150, 180, 230))
    draw_diamond(draw, W-35, 70,  6, (150, 180, 230))

    # 上部サブテキスト
    f_sub = fnt(FONT_R, 25)
    sub   = '肌は"内側"から変わる！'
    sb    = draw.textbbox((0, 0), sub, font=f_sub)
    draw.text(((W - (sb[2]-sb[0]))//2, 18), sub, font=f_sub, fill=(175, 200, 235))

    # メインタイトル
    f_title = fnt(FONT_B, 66)
    title   = theme if len(theme) <= 10 else theme[:10] + '…'
    tb      = draw.textbbox((0, 0), title, font=f_title)
    tx      = (W - (tb[2]-tb[0])) // 2
    draw.text((tx, 55), title, font=f_title, fill=WHITE)

    # タイトル下線
    draw.rectangle([tx, 136, tx + (tb[2]-tb[0]), 139], fill=accent)

    # サブタイトル
    f_sub2 = fnt(FONT_R, 27)
    sub2   = '肌荒れの原因と今日からできる対策'
    s2b    = draw.textbbox((0, 0), sub2, font=f_sub2)
    draw.text(((W - (s2b[2]-s2b[0]))//2, 148), sub2, font=f_sub2, fill=(158, 185, 225))


# ========== フッター ==========

def draw_footer(draw, accent):
    fh = H - FOOTER_Y
    draw.rectangle([0, FOOTER_Y, W, H], fill=FOOTER_BG)
    draw.rectangle([0, FOOTER_Y, W, FOOTER_Y + 4], fill=accent)
    f   = fnt(FONT_R, 25)
    txt = '肌は、スキンケアだけじゃ変わらない。内側から整えて、理想の肌へ！'
    tb  = draw.textbbox((0, 0), txt, font=f)
    draw.text(((W - (tb[2]-tb[0]))//2, FOOTER_Y + (fh - (tb[3]-tb[1]))//2),
              txt, font=f, fill=FOOTER_TXT)


# ========== メイン ==========

def create_image(thread, index):
    accent              = ACCENTS[index % len(ACCENTS)]
    hook, causes, actions = get_contents(thread)

    img  = Image.new('RGB', (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw_header(draw, accent, thread['theme'])
    draw_panel1(draw, PX[0], PY1, accent, hook, thread['theme'])
    draw_panel2(draw, PX[1], PY1, accent, causes, thread['theme'])
    draw_panel3(draw, PX[0], PY2, accent, actions)
    draw_panel4(draw, PX[1], PY2, accent)
    draw_footer(draw, accent)

    fn   = f"theme{thread['id']:02d}.png"
    img.save(os.path.join(OUTPUT_DIR, fn))
    return fn


def main():
    print('=== Instagram画像生成 v2 ===\n')
    with open(POSTS_FILE, encoding='utf-8') as f:
        threads = json.load(f)['threads']
    print(f'テーマ数: {len(threads)}件\n')
    for i, t in enumerate(threads):
        print(f'✅ {create_image(t, i)}（{t["theme"]}）')
    print(f'\n完成！保存先: {OUTPUT_DIR}')


if __name__ == '__main__':
    main()
