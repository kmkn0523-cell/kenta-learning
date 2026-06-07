# test_ronin_comment_seeder.py
# 1コメ目テキスト生成の純粋関数テスト
# 実行: pytest ronin/tests/test_ronin_comment_seeder.py -v
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ronin_comment_seeder import (
    build_seed_comment,
    pick_generic_seed,
    GENERIC_SEED_QUESTIONS,
)


def test_CTA無しならベースだけ返す():
    assert build_seed_comment("What hit hardest today?") == "What hit hardest today?"


def test_CTAありなら2行空けて連結():
    out = build_seed_comment("Base question.", cta="Link here")
    assert out == "Base question.\n\nLink here"


def test_500字に丸める():
    out = build_seed_comment("a" * 600)
    assert len(out) <= 500


def test_汎用シードをカウントで回す():
    first = pick_generic_seed(0)
    assert first == GENERIC_SEED_QUESTIONS[0]
    # 末尾を超えたら先頭へ
    assert pick_generic_seed(len(GENERIC_SEED_QUESTIONS)) == GENERIC_SEED_QUESTIONS[0]


def test_汎用シードは複数用意されている():
    assert len(GENERIC_SEED_QUESTIONS) >= 3
