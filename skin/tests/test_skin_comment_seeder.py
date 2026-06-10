# test_skin_comment_seeder.py
# skin_comment_seeder.py（1コメ目シード生成）のテスト

import os
import sys

# skinフォルダをimportパスに追加する（テストからモジュールを読み込むため）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from skin_comment_seeder import (
    CTA_FOLLOW,
    CTA_NOTE,
    CTA_REPOST,
    CTA_SAVE,
    DEEP_DIVE_LEAD,
    GENERIC_SEED_QUESTIONS,
    MAX_LEN,
    build_seed_comment,
    cta_line_for_cycle,
    pick_generic_seed,
)


def test_pick_generic_seed_rotates():
    # カウント順に問いかけが回り、末尾を超えたら先頭に戻ること
    assert pick_generic_seed(0) == GENERIC_SEED_QUESTIONS[0]
    assert pick_generic_seed(len(GENERIC_SEED_QUESTIONS)) == GENERIC_SEED_QUESTIONS[0]


def test_cta_cycle_save_follow_note_repost():
    # 余り0=保存 / 1=フォロー / 2=note / 3=リポストの順であること
    url = "https://note.com/example/n/abc"
    assert cta_line_for_cycle(0, url) == CTA_SAVE
    assert cta_line_for_cycle(1, url) == CTA_FOLLOW
    assert cta_line_for_cycle(2, url) == CTA_NOTE.format(url=url)
    assert cta_line_for_cycle(3, url) == CTA_REPOST


def test_cta_note_cycle_falls_back_to_save_without_url():
    # note誘導の回でもURLが無ければ保存CTAにフォールバックすること
    assert cta_line_for_cycle(2, "") == CTA_SAVE


def test_cta_note_contains_url():
    # note誘導CTAに渡したURLが含まれていること
    url = "https://note.com/example/n/xyz"
    assert url in cta_line_for_cycle(2, url)


def test_build_seed_comment_deep_dive_adds_lead():
    # deep_dive=Trueでリード行が先頭に付くこと（分析の先頭50字一致を防ぐ）
    result = build_seed_comment("本文です", deep_dive=True)
    assert result.startswith(DEEP_DIVE_LEAD)
    assert "本文です" in result


def test_build_seed_comment_without_deep_dive_has_no_lead():
    # deep_dive=False（汎用問いかけ）ではリード行が付かないこと
    result = build_seed_comment("問いかけです")
    assert result == "問いかけです"


def test_build_seed_comment_appends_cta():
    # CTAを渡すと2行空けて末尾に付くこと
    result = build_seed_comment("本文", cta="CTA行")
    assert result == "本文\n\nCTA行"


def test_build_seed_comment_truncates_at_max_len():
    # 500字を超える場合は丸められること
    long_text = "あ" * 600
    result = build_seed_comment(long_text)
    assert len(result) == MAX_LEN
