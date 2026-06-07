# test_ronin_engagement.py
# engagement在庫のロード/選択/検証の純粋関数テスト
# 実行: pytest ronin/tests/test_ronin_engagement.py -v
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ronin_engagement import pick_engagement_post, validate_engagement_posts, load_engagement_posts


SAMPLE = [
    {"id": "eng001", "archetype": "either_or", "theme": "x",
     "text": "a?", "seed_comment": "s1"},
    {"id": "eng002", "archetype": "fill_blank", "theme": "y",
     "text": "b ___", "seed_comment": "s2"},
]


def test_engagement_indexで順番に選ぶ():
    assert pick_engagement_post(SAMPLE, 0)["id"] == "eng001"
    assert pick_engagement_post(SAMPLE, 1)["id"] == "eng002"
    assert pick_engagement_post(SAMPLE, 2)["id"] == "eng001"  # 末尾を超えたら戻る


def test_検証_正常データはエラーなし():
    assert validate_engagement_posts(SAMPLE) == []


def test_検証_必須キー欠落を検出():
    broken = [{"id": "x", "archetype": "a", "theme": "t", "text": "t"}]  # seed_comment欠落
    errors = validate_engagement_posts(broken)
    assert any("seed_comment" in e for e in errors)


def test_検証_id重複を検出():
    dup = [
        {"id": "same", "archetype": "a", "theme": "t", "text": "1", "seed_comment": "s"},
        {"id": "same", "archetype": "a", "theme": "t", "text": "2", "seed_comment": "s"},
    ]
    errors = validate_engagement_posts(dup)
    assert any("重複" in e for e in errors)


def test_検証_本文500字超を検出():
    longp = [{"id": "x", "archetype": "a", "theme": "t",
              "text": "a" * 501, "seed_comment": "s"}]
    errors = validate_engagement_posts(longp)
    assert any("500" in e for e in errors)


def test_実ファイルが検証を通る():
    posts = load_engagement_posts()
    assert len(posts) >= 2
    assert validate_engagement_posts(posts) == []
