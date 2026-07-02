# test_ronin_x_action.py
# ronin_x_action の純粋ロジックのテスト（APIは呼ばない・呼んだら失敗させる）
# 実行: cd ronin && python3 -m pytest tests/test_ronin_x_action.py -v
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ronin_x_action as action


# ------- 認証情報チェック -------

def test_4つ全部そろっていればTrue(monkeypatch):
    monkeypatch.setattr(action, "API_KEY", "k")
    monkeypatch.setattr(action, "API_SECRET", "s")
    monkeypatch.setattr(action, "ACCESS_TOKEN", "t")
    monkeypatch.setattr(action, "ACCESS_TOKEN_SECRET", "ts")
    assert action.has_all_credentials() is True


def test_1つでも欠けていればFalse(monkeypatch):
    monkeypatch.setattr(action, "API_KEY", "k")
    monkeypatch.setattr(action, "API_SECRET", None)
    monkeypatch.setattr(action, "ACCESS_TOKEN", "t")
    monkeypatch.setattr(action, "ACCESS_TOKEN_SECRET", "ts")
    assert action.has_all_credentials() is False


def test_全部未設定ならFalse(monkeypatch):
    monkeypatch.setattr(action, "API_KEY", None)
    monkeypatch.setattr(action, "API_SECRET", None)
    monkeypatch.setattr(action, "ACCESS_TOKEN", None)
    monkeypatch.setattr(action, "ACCESS_TOKEN_SECRET", None)
    assert action.has_all_credentials() is False


# ------- 本文＋ハッシュタグの組み立て -------

def test_280字以内ならハッシュタグを付ける():
    out = action.build_full_text("short post", hashtags="\n\n#Tag")
    assert out == "short post\n\n#Tag"


def test_280字を超えたらハッシュタグなしにする():
    long_content = "x" * 275
    out = action.build_full_text(long_content, hashtags="\n\n#Bushido #SamuraiWisdom")
    assert out == long_content
    assert "#Bushido" not in out


def test_タグ込みでちょうど280字は付けたままにする():
    hashtags = "\n\n#Tag"
    content = "x" * (280 - len(hashtags))
    out = action.build_full_text(content, hashtags=hashtags)
    assert len(out) == 280
    assert out.endswith("#Tag")


# ------- ローテーション -------

def test_pick_postは指定indexの投稿を返す():
    daily_posts = [{"id": 1}, {"id": 2}, {"id": 3}]
    index, post = action.pick_post(daily_posts, 1)
    assert index == 1
    assert post == {"id": 2}


def test_pick_postはindexが配列の外でも循環する():
    daily_posts = [{"id": 1}, {"id": 2}, {"id": 3}]
    index, post = action.pick_post(daily_posts, 5)
    assert index == 2
    assert post == {"id": 3}


def test_next_daily_indexは末尾で0に戻る():
    assert action.next_daily_index(0, 3) == 1
    assert action.next_daily_index(1, 3) == 2
    assert action.next_daily_index(2, 3) == 0


# ------- 進捗ファイル -------

def test_load_progressはファイルが無ければ初期値(tmp_path, monkeypatch):
    monkeypatch.setattr(action, "PROGRESS_FILE", str(tmp_path / "no_such_file.json"))
    progress = action.load_progress()
    assert progress == {"daily_index": 0, "history": []}


def test_save_progressで書いた内容をload_progressで読み戻せる(tmp_path, monkeypatch):
    prog_file = tmp_path / "prog.json"
    monkeypatch.setattr(action, "PROGRESS_FILE", str(prog_file))
    action.save_progress({"daily_index": 2, "history": [{"date": "x"}]})
    loaded = action.load_progress()
    assert loaded == {"daily_index": 2, "history": [{"date": "x"}]}


# ------- 投稿データJSONの整合性 -------

def test_ronin_x_posts_jsonは全件280字以内():
    posts_path = Path(__file__).resolve().parents[1] / "ronin_x_posts.json"
    with open(posts_path, encoding="utf-8") as f:
        data = json.load(f)
    daily_posts = data["daily_posts"]
    assert len(daily_posts) > 0
    for post in daily_posts:
        full_text = action.build_full_text(post["content"])
        assert len(full_text) <= 280, f"id={post['id']} が280字を超えています"
        assert len(post["content"]) <= 280, f"id={post['id']} は本文だけでも280字を超えています"


# ------- 未設定時のスキップ（main統合） -------

def test_mainは認証情報が無いとAPIに触れずスキップする(capsys, monkeypatch):
    monkeypatch.setattr(action, "API_KEY", None)
    monkeypatch.setattr(action, "API_SECRET", None)
    monkeypatch.setattr(action, "ACCESS_TOKEN", None)
    monkeypatch.setattr(action, "ACCESS_TOKEN_SECRET", None)

    def fail_connect():
        raise AssertionError("シークレット未設定なのにXへ接続しようとした")

    monkeypatch.setattr(action, "connect_to_x", fail_connect)
    action.main()

    out = capsys.readouterr().out
    assert "スキップ" in out


def test_mainは認証情報がそろっていれば投稿処理に進む(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(action, "API_KEY", "k")
    monkeypatch.setattr(action, "API_SECRET", "s")
    monkeypatch.setattr(action, "ACCESS_TOKEN", "t")
    monkeypatch.setattr(action, "ACCESS_TOKEN_SECRET", "ts")

    prog_file = tmp_path / "prog.json"
    monkeypatch.setattr(action, "PROGRESS_FILE", str(prog_file))
    monkeypatch.setattr(action, "load_posts",
                        lambda: {"daily_posts": [{"id": 1, "type": "テスト型", "content": "hello"}]})

    class FakeResponse:
        data = {"id": "999"}

    class FakeClient:
        def create_tweet(self, text):
            assert text == "hello\n\n#Bushido #SamuraiWisdom"
            return FakeResponse()

    monkeypatch.setattr(action, "connect_to_x", lambda: FakeClient())
    action.main()

    out = capsys.readouterr().out
    assert "投稿成功" in out

    progress = action.load_progress()
    assert progress["daily_index"] == 0  # 投稿1件しかないので0に戻る
    assert progress["history"][-1]["tweet_id"] == "999"
