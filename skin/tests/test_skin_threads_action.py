"""skin_threads_action.py の A/B選択ロジックの単体テスト。"""
# pytestを使って関数の挙動を確認するファイル
import sys
from pathlib import Path

# skin/ 配下を import path に追加
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_threads_action import (
    pick_today_theme,
    select_ab_variant,
    flip_ab_variant,
    load_posts_for_variant,
    build_note_promo_texts,
    build_paid_note_promo_texts,
)


def test_pick_today_theme_returns_1_when_index_0():
    # daily_index=0 のとき テーマ1 が返ることを確認
    assert pick_today_theme(0) == 1


def test_pick_today_theme_wraps_at_108():
    # daily_index=108 のとき テーマ1 にループすることを確認
    assert pick_today_theme(108) == 1


def test_pick_today_theme_returns_108():
    # daily_index=107 のとき テーマ108 が返ることを確認
    assert pick_today_theme(107) == 108


def test_pick_today_theme_uses_theme_count_128():
    # theme_count=128 のとき テーマ109〜128 も回ることを確認（死蔵バグの修正）
    assert pick_today_theme(108, theme_count=128) == 109
    assert pick_today_theme(127, theme_count=128) == 128
    assert pick_today_theme(128, theme_count=128) == 1


def test_note_promo_body_has_no_url_and_comment_has_url():
    # 本文にはURLが入らず、1コメ目にURLが入ることを確認（配信抑制の回避）
    url = "https://note.com/example/n/abc123"
    body, comment = build_note_promo_texts("テスト記事タイトル", url)
    assert url not in body
    assert url in comment
    assert "テスト記事タイトル" in body
    assert len(body) <= 500


def test_paid_note_promo_body_has_no_url_and_comment_has_url():
    # 有料note宣伝も本文にURLが入らず、1コメ目にURLと価格が入ることを確認
    url = "https://note.com/example/n/xyz789"
    body, comment = build_paid_note_promo_texts("有料記事タイトル", url, "2,980円")
    assert url not in body
    assert url in comment
    assert "2,980円" in body
    assert "2,980円" in comment
    assert len(body) <= 500


def test_select_ab_variant_returns_stored_value():
    # progress に B が記録されていれば B を返す
    progress = {"ab_index_per_theme": {"5": "B"}}
    assert select_ab_variant(progress, 5) == "B"


def test_select_ab_variant_defaults_to_A_when_missing():
    # キーが無いテーマは A をデフォルトで返す
    progress = {"ab_index_per_theme": {}}
    assert select_ab_variant(progress, 99) == "A"


def test_flip_ab_variant_A_to_B():
    progress = {"ab_index_per_theme": {"3": "A"}}
    flip_ab_variant(progress, 3)
    assert progress["ab_index_per_theme"]["3"] == "B"


def test_flip_ab_variant_B_to_A():
    progress = {"ab_index_per_theme": {"3": "B"}}
    flip_ab_variant(progress, 3)
    assert progress["ab_index_per_theme"]["3"] == "A"


def test_load_posts_for_variant_returns_A_post():
    data = {
        "threads_a": [{"id": 1, "theme": "A1", "posts": ["a1", "a2", "a3"]}],
        "threads_b": [],
    }
    result = load_posts_for_variant(data, theme_id=1, variant="A")
    assert result["theme"] == "A1"


def test_load_posts_for_variant_falls_back_to_A_when_B_empty():
    # B側が空のテーマは A にフォールバック
    data = {
        "threads_a": [{"id": 1, "theme": "A1", "posts": ["a1", "a2", "a3"]}],
        "threads_b": [],
    }
    result = load_posts_for_variant(data, theme_id=1, variant="B")
    assert result["theme"] == "A1"


def test_load_posts_for_variant_returns_B_post_when_available():
    data = {
        "threads_a": [{"id": 1, "theme": "A1", "posts": ["a1", "a2", "a3"]}],
        "threads_b": [{"id": 1, "theme": "B1", "posts": ["b1", "b2", "b3"]}],
    }
    result = load_posts_for_variant(data, theme_id=1, variant="B")
    assert result["theme"] == "B1"
