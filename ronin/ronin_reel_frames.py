# ronin_reel_frames.py
# @RoninWords用：1つの格言から「縦型リール」の段階リビール用フレーム画像(1080×1920)を作る。
# 配色・フォントは既存の格言カード(generate_ronin_cards.py)と統一してブランド感を保つ。

from pathlib import Path  # フォントの場所を組み立てる道具
from PIL import Image, ImageDraw, ImageFont  # 画像を描く道具

# このファイルと同じ ronin/ の中の fonts フォルダからフォントを読む（CIでも解決できるように）
FONTS_DIR = Path(__file__).resolve().parent / "fonts"
FONT_JP_PATH = str(FONTS_DIR / "YujiSyuku.ttf")                 # 筆書き風かな漢字
FONT_ROMAN_PATH = str(FONTS_DIR / "CormorantGaramond-Italic.ttf")  # エレガントな欧文
FONT_SERIF_PATH = str(FONTS_DIR / "NotoSerifJP.otf")           # 英語本文用

# 和紙風の背景色とブランドカラー（既存カードと同じ）
PAPER = (240, 230, 208)   # 和紙色 #f0e6d0
RED = (158, 30, 14)       # 朱（シール・アクセント）
INK = (18, 10, 4)         # 墨色（ほぼ黒）
SEPIA = (80, 50, 20)      # セピア（ローマ字・英語）


def _draw_seal(draw, width):
    """右上にRWシール（朱の角印風）を描く。"""
    size = 150           # シールの一辺
    margin = 70          # 端からの距離
    x1 = width - margin  # 右端
    x0 = x1 - size       # 左端
    y0 = margin          # 上端
    y1 = y0 + size       # 下端
    draw.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=RED)  # 朱の角印
    seal_font = ImageFont.truetype(FONT_SERIF_PATH, 60)           # 中の文字
    draw.text(((x0 + x1) // 2, (y0 + y1) // 2), "RW", font=seal_font,
              fill=PAPER, anchor="mm")  # 中央に白抜きでRW


def _draw_centered(draw, text, font, fill, center_x, center_y):
    """指定フォントでテキストを中央寄せで描く（複数行は改行で分ける）。"""
    draw.multiline_text((center_x, center_y), text, font=font, fill=fill,
                        anchor="mm", align="center", spacing=18)


def render_reveal_frames(proverb, plan, out_dir, width, height):
    """格言とリビール計画から4フレームPNGを描き、絶対パスのリストを返す。"""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)  # 出力先を用意

    # フォントを準備（日本語格言は大きめ、ローマ字・英語は中くらい）
    font_jp = ImageFont.truetype(FONT_JP_PATH, 110)      # 日本語格言
    font_roma = ImageFont.truetype(FONT_ROMAN_PATH, 64)  # ローマ字読み
    font_en = ImageFont.truetype(FONT_SERIF_PATH, 52)    # 英語の意味
    font_cta = ImageFont.truetype(FONT_SERIF_PATH, 34)   # フォロー誘導

    paths = []
    for frame_number, parts in enumerate(plan, start=1):
        image = Image.new("RGB", (width, height), PAPER)  # 和紙色のキャンバス
        draw = ImageDraw.Draw(image)
        _draw_seal(draw, width)  # どのフレームにもシールは出す

        center_x = width // 2
        if parts["jp"]:
            # 日本語格言は画面中央やや上に大きく
            _draw_centered(draw, proverb["jp"], font_jp, INK, center_x, height // 2 - 120)
        if parts["roma"]:
            # ローマ字は格言の下にセピアで
            _draw_centered(draw, proverb["roma"], font_roma, SEPIA, center_x, height // 2 + 60)
        if parts["en"]:
            # 英語の意味はさらに下に
            _draw_centered(draw, proverb["en"], font_en, INK, center_x, height // 2 + 220)
            # CTAは最下部
            _draw_centered(draw, "Follow for one Japanese wisdom, every day.",
                           font_cta, SEPIA, center_x, height - 180)

        frame_path = str(out_path / f"frame{frame_number}.png")
        image.save(frame_path, "PNG")
        paths.append(frame_path)
    return paths
