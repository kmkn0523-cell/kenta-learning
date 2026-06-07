# test_ronin_threads_action.py
# ronin_threads_action の純粋ロジック＋post_to_threadsのreply対応テスト（APIはモック）
# 実行: pytest ronin/tests/test_ronin_threads_action.py -v
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
