# test_skin_reply_hunter.py
# skin_reply_hunter.py の純粋ロジック関数をテストする（ファイル操作・対話は対象外）
# 実行: pytest skin/tests/test_skin_reply_hunter.py

import sys
from datetime import date
from pathlib import Path

# skin/ フォルダをimportできる場所に加える（既存テストと同じやり方）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES  # テンプレ集
from skin_reply_hunter import (  # テストしたい純粋関数たち
    suggest_drafts,
    sort_round_list,
    record_reply,
    update_daily_log_text,
)

# =================================================
# suggest_drafts：投稿文 → 下書き3案 ＋ カテゴリ名
# =================================================

def test_suggest_drafts_腸活文は腸活カテゴリになる():
    drafts, category = suggest_drafts("腸活を始めて発酵食品を毎日食べてる")
    assert category == "腸活・食事系の投稿へ"
    assert len(drafts) == 3
    assert len(set(drafts)) == 3
    assert set(drafts).issubset(set(COMMENT_TEMPLATES["1"]["comments"]))

def test_suggest_drafts_ニキビ文はニキビカテゴリになる():
    drafts, category = suggest_drafts("繰り返すニキビと肌荒れがつらい")
    assert category == "ニキビ悩み・共感系の投稿へ"
    assert len(drafts) == 3
    assert set(drafts).issubset(set(COMMENT_TEMPLATES["4"]["comments"]))

def test_suggest_drafts_無該当は汎用テンプレになる():
    drafts, category = suggest_drafts("今日はいい天気で散歩しました")
    assert category == "汎用（どのカテゴリにも当てはまらない時）"
    assert len(drafts) == 3
    assert set(drafts).issubset(set(GENERIC_TEMPLATES))

def test_suggest_drafts_複数該当は当たり数が多い方を選ぶ():
    drafts, category = suggest_drafts("腸活で肌が変わった、ニキビも減った")
    assert category == "腸活・食事系の投稿へ"

def test_suggest_drafts_当たり数が同じなら番号が若い方を選ぶ():
    drafts, category = suggest_drafts("寝る前にスキンケア")
    assert category == "睡眠・生活習慣系の投稿へ"

# =================================================
# sort_round_list：巡回順（未リプ最優先 → 古い順、同点は元の並び）
# =================================================

def test_sort_round_list_未リプを先頭にして残りは古い順():
    targets = [{"handle": "@a"}, {"handle": "@b"}, {"handle": "@c"}]
    history = {
        "@a": {"last_replied_at": "2026-05-30", "total_replies": 1},
        "@c": {"last_replied_at": "2026-05-28", "total_replies": 2},
    }
    ordered = [t["handle"] for t in sort_round_list(targets, history)]
    assert ordered == ["@b", "@c", "@a"]

def test_sort_round_list_全員未リプなら元の並びを保つ():
    targets = [{"handle": "@x"}, {"handle": "@y"}, {"handle": "@z"}]
    ordered = [t["handle"] for t in sort_round_list(targets, {})]
    assert ordered == ["@x", "@y", "@z"]

def test_sort_round_list_リプ済み同士は古い順():
    targets = [{"handle": "@p"}, {"handle": "@q"}]
    history = {
        "@p": {"last_replied_at": "2026-06-01", "total_replies": 1},
        "@q": {"last_replied_at": "2026-05-20", "total_replies": 1},
    }
    ordered = [t["handle"] for t in sort_round_list(targets, history)]
    assert ordered == ["@q", "@p"]

# =================================================
# record_reply：履歴を更新して新しいdictを返す（元は壊さない）
# =================================================

def test_record_reply_新しいハンドルは件数1で登録される():
    history = {}
    result = record_reply(history, "@new", "2026-06-02")
    assert result["@new"] == {"last_replied_at": "2026-06-02", "total_replies": 1}

def test_record_reply_既存ハンドルは件数が増え日付が更新される():
    history = {"@x": {"last_replied_at": "2026-05-30", "total_replies": 3}}
    result = record_reply(history, "@x", "2026-06-02")
    assert result["@x"] == {"last_replied_at": "2026-06-02", "total_replies": 4}

def test_record_reply_元の履歴は書き換えない():
    history = {"@x": {"last_replied_at": "2026-05-30", "total_replies": 3}}
    record_reply(history, "@x", "2026-06-02")
    assert history["@x"] == {"last_replied_at": "2026-05-30", "total_replies": 3}

# =================================================
# update_daily_log_text：その日の枠に「リプ件数」だけ書き込む
# =================================================

def test_update_daily_log_text_今日の枠が無ければ追記する():
    existing = "# ログ\n\n## 2026-05-31（日）\n- リプ件数: 2\n- 手動投稿数: 1\n- 気づき: メモ\n"
    result = update_daily_log_text(existing, 5, date(2026, 6, 2))
    assert "## 2026-05-31（日）" in result
    assert "- リプ件数: 2" in result
    assert "## 2026-06-02（火）" in result
    assert "- リプ件数: 5" in result

def test_update_daily_log_text_今日の枠があれば件数行だけ更新する():
    existing = "## 2026-06-02（火）\n- リプ件数: 1\n- 手動投稿数: 3\n- 気づき: あさ\n"
    result = update_daily_log_text(existing, 7, date(2026, 6, 2))
    assert "- リプ件数: 7" in result
    assert "- リプ件数: 1" not in result
    assert "- 手動投稿数: 3" in result
    assert "- 気づき: あさ" in result
    assert result.count("## 2026-06-02（火）") == 1
