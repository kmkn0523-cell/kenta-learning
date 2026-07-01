# test_ronin_threads_action.py
# ronin_threads_action の純粋ロジック＋post_to_threadsのreply対応テスト（APIはモック）
# 実行: pytest ronin/tests/test_ronin_threads_action.py -v
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ronin_threads_action as action


# ------- Task 4: reply_to_id 対応 -------

def test_post_to_threads_replyはreply_to_idを送る():
    captured = {}

    def capture(url, params=None, **kwargs):
        captured.setdefault("calls", []).append(params)
        resp = MagicMock()
        resp.json.return_value = {"id": "999"}
        return resp

    with patch.object(action, "requests") as m, \
         patch.object(action.time, "sleep", return_value=None):  # 30秒待機を飛ばす
        m.post.side_effect = capture
        result = action.post_to_threads("hi", reply_to_id="parent123")

    # コンテナ作成のparamsにreply_to_idが入っている
    container_params = captured["calls"][0]
    assert container_params.get("reply_to_id") == "parent123"
    assert result == "999"


# ------- Task 6: 種別判定 -------

def test_4投稿に1回engagementを選ぶ():
    assert action.decide_post_kind(0) == "teaching"
    assert action.decide_post_kind(1) == "teaching"
    assert action.decide_post_kind(2) == "teaching"
    assert action.decide_post_kind(3) == "engagement"
    assert action.decide_post_kind(7) == "engagement"
    assert action.decide_post_kind(4) == "teaching"


# ------- Task 7: 本文ビルド・CTAサイクル -------

def test_本文はハッシュタグを末尾に付ける():
    out = action.build_full_text("Hello world", "#A #B #C")
    assert out == "Hello world\n\n#A #B #C"


def test_本文が500字を超えたら丸める():
    out = action.build_full_text("x" * 600, "#A #B #C")
    assert len(out) <= 500
    assert out.endswith("#A #B #C")  # ハッシュタグは必ず残す


def test_CTAサイクル_14ごとにGumroad_Substack():
    assert action.cta_line_for_cycle(0) == action.GUMROAD_LINE
    assert action.cta_line_for_cycle(7) == action.SUBSTACK_LINE
    assert action.cta_line_for_cycle(3) == ""  # 通常回はCTA無し


# ------- Task 8: dry-run 統合 -------

def test_dry_runは教え投稿の本文と1コメ目を組み立てAPIを呼ばない(capsys, tmp_path, monkeypatch):
    # 進捗ファイルをテンポラリに差し替え（history_count=0 → teaching, CTA=Gumroad）
    prog = tmp_path / "prog.json"
    prog.write_text('{"index": 0, "engagement_index": 0, "history": []}', encoding="utf-8")
    monkeypatch.setattr(action, "PROGRESS_FILE", str(prog))

    # 教え投稿の在庫はcwdに依存しないようモックする（threads_posts.jsonを読みに行かせない）
    monkeypatch.setattr(action, "flatten_posts",
                        lambda: [{"day": 1, "type": "morning", "content": "Be here now."}])

    called = {"post": False}

    def fail_post(*a, **k):
        called["post"] = True
        raise AssertionError("dry-runでAPIを呼んではいけない")

    monkeypatch.setattr(action, "post_to_threads", fail_post)
    action.post_once(dry_run=True)

    out = capsys.readouterr().out
    assert called["post"] is False          # APIは呼ばれない
    assert "DRY-RUN" in out                  # dry-run表示が出る
    assert "1コメ目" in out or "seed" in out.lower()  # 1コメ目も組み立てる


def test_dry_run_engagement回はengagement在庫から組み立てる(capsys, tmp_path, monkeypatch):
    # history_count=3 → decide_post_kindがengagementを返す
    prog = tmp_path / "prog.json"
    prog.write_text(
        '{"index": 0, "engagement_index": 0, "history": [{}, {}, {}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(action, "PROGRESS_FILE", str(prog))
    monkeypatch.setattr(action, "flatten_posts",
                        lambda: [{"day": 1, "type": "morning", "content": "fallback"}])
    # engagement在庫をモック
    monkeypatch.setattr(action.ronin_engagement, "load_engagement_posts",
                        lambda: [{"id": "engTEST", "archetype": "either_or", "theme": "t",
                                  "text": "Pick A or B?", "seed_comment": "Why A?"}])

    def fail_post(*a, **k):
        raise AssertionError("dry-runでAPIを呼んではいけない")

    monkeypatch.setattr(action, "post_to_threads", fail_post)
    action.post_once(dry_run=True)

    out = capsys.readouterr().out
    assert "engagement engTEST" in out      # engagement在庫が選ばれている
    assert "Pick A or B?" in out            # engagementの本文が組まれている


# ------- CTAのSubstackテーマ連動 -------

def test_CTAサイクル_テーマ一致する記事があればそのURLを使う():
    articles = [{"title": "The Discipline of Showing Up Every Day",
                 "url": "https://roninwords.substack.com/p/discipline-1"}]
    line = action.cta_line_for_cycle(7, theme_key="1", substack_articles=articles)
    assert "https://roninwords.substack.com/p/discipline-1" in line


def test_CTAサイクル_テーマ一致なしはプロフィールURLにフォールバック():
    articles = [{"title": "The Hawk Hides Its Talons",
                 "url": "https://roninwords.substack.com/p/hawk"}]
    line = action.cta_line_for_cycle(7, theme_key="1", substack_articles=articles)
    assert line == action.SUBSTACK_LINE


def test_CTAサイクル_theme_keyがNoneならプロフィールURL():
    line = action.cta_line_for_cycle(7, theme_key=None, substack_articles=[{"title": "x", "url": "y"}])
    assert line == action.SUBSTACK_LINE


def test_load_substack_articles_with_url_ファイル無しは空リスト(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert action.load_substack_articles_with_url() == []


def test_load_substack_articles_with_url_urlとtitleがある記事だけ拾う(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "substack").mkdir()
    (tmp_path / "substack" / "substack_progress.json").write_text(
        json.dumps({"history": [
            {"title": "A — B", "url": "https://x/p/a"},
            {"title": "C — D"},  # urlなし→対象外
        ]}), encoding="utf-8",
    )
    (tmp_path / "substack" / "deep_dive_progress.json").write_text(
        json.dumps({"history": [{"title": "E", "url": "https://x/p/e"}]}), encoding="utf-8",
    )
    articles = action.load_substack_articles_with_url()
    assert {"title": "A — B", "url": "https://x/p/a"} in articles
    assert {"title": "E", "url": "https://x/p/e"} in articles
    assert len(articles) == 2


# ------- 1コメ目シードのテーマ連動（post_once統合） -------

def test_dry_run_教え投稿は本文をテーマ分類してseedを組み立てる(capsys, tmp_path, monkeypatch):
    prog = tmp_path / "prog.json"
    prog.write_text('{"index": 0, "engagement_index": 0, "history": []}', encoding="utf-8")
    monkeypatch.setattr(action, "PROGRESS_FILE", str(prog))
    monkeypatch.setattr(
        action, "flatten_posts",
        lambda: [{"day": 1, "type": "morning", "content": "Discipline and a daily routine build consistency."}],
    )

    def fail_post(*a, **k):
        raise AssertionError("dry-runでAPIを呼んではいけない")

    monkeypatch.setattr(action, "post_to_threads", fail_post)
    action.post_once(dry_run=True)

    out = capsys.readouterr().out
    # テーマ1（規律）に分類され、THEME_SEED_QUESTIONS["1"]の先頭が使われる
    assert action.ronin_comment_seeder.THEME_SEED_QUESTIONS["1"][0][:30] in out
