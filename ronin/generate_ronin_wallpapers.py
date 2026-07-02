# generate_ronin_wallpapers.py
# @RoninWords用：スマホ壁紙（1080x1920）版の書道カードを生成する
# Gumroad販売パック用。generate_ronin_cards.py のデザインをそのまま流用し、
# レイアウト定数だけ縦長画面向けに上書きして描画する。
# 使い方: cd ronin && python3 generate_ronin_wallpapers.py

import os                       # フォルダ作成・ファイル名変更に使う道具
import re                       # ローマ字をファイル名向けに整える道具
import shutil                   # zipファイルを作る道具

import generate_ronin_cards as cards  # カード描画のデザイン・関数を丸ごと再利用する

# 壁紙のサイズ（スマホ標準の9:16）
WALLPAPER_WIDTH = 1080
WALLPAPER_HEIGHT = 1920

# Vol.2に入れる日付範囲（2026-07制作の「六つの道」シリーズ）
VOL2_FIRST_DAY = 201
VOL2_LAST_DAY = 230

# 出力先（⚠️リポジトリ外に置くこと！）
# このリポジトリはPUBLICなので、商品zipをリポジトリ内に置くと誰でも無料で
# ダウンロードできてしまう。WindowsのホームフォルダREADME直下に出力する。
OUTPUT_BASE = "/mnt/c/Users/kenta kamijyo/RoninWords_Gumroad"
PACK_DIR = os.path.join(OUTPUT_BASE, "RoninWords_Wallpaper_Pack_Vol2")
ZIP_PATH = os.path.join(OUTPUT_BASE, "RoninWords_Wallpaper_Pack_Vol2")  # .zipは自動で付く


def apply_wallpaper_layout():
    """generate_ronin_cards のレイアウト定数を縦長（1080x1920）向けに上書きする。
    描画関数はモジュールの定数を毎回読むので、ここで書き換えるだけで縦長になる。"""
    cards.W = WALLPAPER_WIDTH
    cards.H = WALLPAPER_HEIGHT
    cards.SEAL_PAD = 90        # シールは時計と重なりにくいよう少し内側へ
    cards.TOP_RULE_Y = 380     # 上の区切り線（スマホの時計エリアより下）
    cards.BOT_RULE_Y = 1520    # 下の区切り線（英語引用はこの下に入る）


def make_filename(index, roma):
    """「01_tetsu-wa-atsui-uchi-ni-ute.png」形式のファイル名を作る"""
    slug = re.sub(r"[^a-z0-9]+", "-", roma.lower()).strip("-")
    return f"{index:02d}_{slug}.png"


def main():
    os.makedirs(PACK_DIR, exist_ok=True)
    apply_wallpaper_layout()

    # Vol.2対象の格言だけ取り出す（day201〜230）
    targets = [p for p in cards.proverbs if VOL2_FIRST_DAY <= p["day"] <= VOL2_LAST_DAY]
    print(f"壁紙を生成します（{len(targets)}枚・{WALLPAPER_WIDTH}x{WALLPAPER_HEIGHT}）...")

    for index, proverb in enumerate(targets, start=1):
        # generate_card は dayNNN.png という名前で保存するので、生成後に商品用の名前に変える
        cards.generate_card(proverb, PACK_DIR)
        generated = os.path.join(PACK_DIR, f"day{proverb['day']:02d}.png")
        renamed = os.path.join(PACK_DIR, make_filename(index, proverb["roma"]))
        os.replace(generated, renamed)

    # 購入者向けの説明テキストを同梱する
    readme_path = os.path.join(PACK_DIR, "README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            "RoninWords Wallpaper Pack Vol.2 — The Six Paths Collection\n"
            "30 Japanese calligraphy wallpapers (1080x1920, for any phone)\n\n"
            "Six paths, five teachings each:\n"
            "The Forge / The Tea Room / Nature / The Craftsman / Zen / Strategy\n\n"
            "Personal use only. Please do not redistribute or resell.\n"
            "More teachings: https://roninwords.substack.com\n"
        )

    # zipにまとめる（Gumroadにはこの1ファイルをアップロードする）
    zip_file = shutil.make_archive(ZIP_PATH, "zip", PACK_DIR)
    print(f"✅ 完成: {zip_file}")


if __name__ == "__main__":
    main()
