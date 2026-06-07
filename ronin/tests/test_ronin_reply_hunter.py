# test_ronin_reply_hunter.py
# ronin_reply_hunter.py の純粋ロジック関数をテストする（ファイル操作・対話・ブラウザは対象外）
# 実行: pytest ronin/tests/test_ronin_reply_hunter.py -v
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # ronin/ をimport可能にする

from ronin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES
from ronin_reply_hunter import (
    suggest_drafts,
    sort_round_list,
    record_reply,
    update_daily_log_text,
    GENERIC_CATEGORY_NAME,
)


# =================================================
# suggest_drafts：投稿文 → 下書き3案 ＋ カテゴリ名
# =================================================

def test_規律の投稿は規律カテゴリになる():
    drafts, category = suggest_drafts("I'm building a new morning routine with real discipline.")
    assert category == COMMENT_TEMPLATES["1"]["name"]
    assert len(drafts) == 3
    # 返ってきた3案はそのカテゴリのテンプレに含まれる
    for d in drafts:
        assert d in COMMENT_TEMPLATES["1"]["comments"]


def test_逆境の投稿は逆境カテゴリになる():
    drafts, category = suggest_drafts("I keep failing and it's a real struggle after this setback.")
    assert category == COMMENT_TEMPLATES["2"]["name"]
    assert len(drafts) == 3


def test_目的の投稿は目的カテゴリになる():
    drafts, category = suggest_drafts("Still searching for purpose and a clear direction in life.")
    assert category == COMMENT_TEMPLATES["6"]["name"]


def test_どのキーワードも無ければ汎用カテゴリ():
    drafts, category = suggest_drafts("Just had a great cup of coffee this morning.")
    assert category == GENERIC_CATEGORY_NAME
    assert len(drafts) == 3
    for d in drafts:
        assert d in GENERIC_TEMPLATES


def test_同点なら若い番号のカテゴリが勝つ():
    # category1(discipline) と category4(mindset) を1個ずつ含む → 若い"1"が勝つ
    drafts, category = suggest_drafts("discipline and mindset, both matter.")
    assert category == COMMENT_TEMPLATES["1"]["name"]


# =================================================
# sort_round_list：未リプ最優先 → 前回が古い順
# =================================================

def test_未リプが先_次に古い順():
    targets = [
        {"handle": "@a"},
        {"handle": "@b"},
        {"handle": "@c"},
    ]
    history = {
        "@a": {"last_replied_at": "2026-06-05", "total_replies": 2},
        "@c": {"last_replied_at": "2026-06-01", "total_replies": 1},
        # @b は履歴なし＝未リプ
    }
    ordered = [t["handle"] for t in sort_round_list(targets, history)]
    assert ordered[0] == "@b"           # 未リプが先頭
    assert ordered[1] == "@c"           # 次に前回が古い方
    assert ordered[2] == "@a"           # 前回が新しい方は最後


def test_元リストを壊さない():
    targets = [{"handle": "@a"}, {"handle": "@b"}]
    before = list(targets)
    sort_round_list(targets, {})
    assert targets == before


# =================================================
# record_reply：履歴の追加・更新（元を壊さない）
# =================================================

def test_新規ハンドルは件数1で登録():
    history = {}
    new = record_reply(history, "@new", "2026-06-07")
    assert new["@new"] == {"last_replied_at": "2026-06-07", "total_replies": 1}
    assert history == {}  # 元は壊れていない


def test_既存ハンドルは件数加算と日付更新():
    history = {"@x": {"last_replied_at": "2026-06-01", "total_replies": 3}}
    new = record_reply(history, "@x", "2026-06-07")
    assert new["@x"]["total_replies"] == 4
    assert new["@x"]["last_replied_at"] == "2026-06-07"
    assert history["@x"]["total_replies"] == 3  # 元は壊れていない


# =================================================
# update_daily_log_text：日次ログの件数追記・差し替え
# =================================================

def test_新しい日は見出しブロックを追記():
    out = update_daily_log_text("# ronin 日次ログ\n", 5, date(2026, 6, 7))
    assert "## 2026-06-07（日）" in out
    assert "- リプ件数: 5" in out
    assert "- 手動投稿数:" in out


def test_同じ日は件数行だけ差し替える():
    existing = "# ronin 日次ログ\n\n## 2026-06-07（日）\n- リプ件数: 2\n- 手動投稿数: 1\n- 気づき: メモ\n"
    out = update_daily_log_text(existing, 7, date(2026, 6, 7))
    assert "- リプ件数: 7" in out
    assert "- リプ件数: 2" not in out      # 古い件数は消える
    assert "- 手動投稿数: 1" in out         # 手書き分は残る
    assert "- 気づき: メモ" in out
    assert out.count("## 2026-06-07（日）") == 1  # 見出しは増えない
