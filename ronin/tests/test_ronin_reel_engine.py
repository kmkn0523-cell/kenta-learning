# ronin_reel_engine.py の純粋関数をテストする（IOやffmpegは対象外）
import sys
from pathlib import Path

# ronin/ をimportパスに追加する（テストをどこから実行しても通るように）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ronin_reel_engine as engine  # テスト対象


def test_next_proverb_index_wraps_to_zero_at_end():
    # 最後(99)の次は先頭(0)に戻る
    assert engine.next_proverb_index({"reel_index": 99}, 100) == 0


def test_next_proverb_index_increments():
    # 5の次は6
    assert engine.next_proverb_index({"reel_index": 5}, 100) == 6


def test_next_proverb_index_starts_at_zero_when_empty():
    # 進捗が無ければ最初は0（-1の次）
    assert engine.next_proverb_index({}, 100) == 0


def test_frame_reveal_plan_is_cumulative_four_frames():
    plan = engine.frame_reveal_plan()
    assert len(plan) == 4
    # 1枚目は背景のみ、最後は全要素
    assert plan[0] == {"jp": False, "roma": False, "en": False}
    assert plan[3] == {"jp": True, "roma": True, "en": True}
    # 累積表示：jpは2枚目以降ずっとTrue
    assert [f["jp"] for f in plan] == [False, True, True, True]
    assert [f["roma"] for f in plan] == [False, False, True, True]
    assert [f["en"] for f in plan] == [False, False, False, True]


def test_build_caption_contains_all_parts():
    proverb = {"jp": "一期一会", "roma": "Ichi go ichi e", "en": "This moment will never come again."}
    caption = engine.build_caption(proverb, "#JapaneseWisdom #Bushido #Zen")
    assert "一期一会" in caption
    assert "Ichi go ichi e" in caption
    assert "This moment will never come again." in caption
    assert "Follow for one Japanese wisdom, every day." in caption
    assert "#JapaneseWisdom #Bushido #Zen" in caption


def test_build_raw_video_url():
    url = engine.build_raw_video_url("https://raw.example.com/ronin/ronin_instagram_reels", "latest_reel.mp4")
    assert url == "https://raw.example.com/ronin/ronin_instagram_reels/latest_reel.mp4"


def test_build_ffmpeg_command_structure():
    images = ["f1.png", "f2.png", "f3.png", "f4.png"]
    cmd = engine.build_ffmpeg_command(images, "bgm.mp3", "out.mp4", 2.6, 30, 1080, 1920, 0.5)
    # 先頭は ffmpeg -y（上書き）
    assert cmd[0] == "ffmpeg"
    assert "-y" in cmd
    # 画像4枚それぞれが -loop 1 で入力される
    assert cmd.count("-loop") == 4
    # 各画像が入力として渡る
    for image in images:
        assert image in cmd
    # 音源も入力に含まれる
    assert "bgm.mp3" in cmd
    # H.264 / yuv420p / aac を指定している（Reels要件）
    assert "libx264" in cmd
    assert "yuv420p" in cmd
    assert "aac" in cmd
    # fade フィルタが含まれる（リビール感）
    filter_complex = cmd[cmd.index("-filter_complex") + 1]
    assert "fade=t=in" in filter_complex
    assert "concat=n=4" in filter_complex
    # 1枚目だけは黒フェードを掛けない（冒頭とサムネが真っ黒になるのを防ぐ）
    first_segment = filter_complex.split(";")[0]
    assert "fade=t=in" not in first_segment
    # 2枚目以降にはフェードが残る（リビール感を維持）
    assert "fade=t=in" in filter_complex.split(";")[1]
    # 出力パスは最後
    assert cmd[-1] == "out.mp4"
    # 音源は動画長に合わせて切る
    assert "-shortest" in cmd


def test_cover_thumb_offset_points_to_last_frame():
    # 4フレーム・1枚2.6秒なら、最終フレーム中央(7.8+1.3=9.1秒)=9100msを指す
    offset = engine.cover_thumb_offset_ms({"seconds_per_frame": 2.6})
    assert offset == 9100


def test_create_reels_container_sends_thumb_offset(monkeypatch):
    captured = {}

    class FakeResponse:
        def json(self):
            return {"id": "creation_456"}

    def fake_post(url, params, timeout):
        captured["params"] = params
        return FakeResponse()

    monkeypatch.setattr(engine.requests, "post", fake_post)
    engine.create_reels_container(
        "https://raw.example.com/latest_reel.mp4", "caption", "USER1", "TOKEN1", 9100
    )
    # カバー位置(thumb_offset)が送られる
    assert captured["params"]["thumb_offset"] == 9100


def test_create_reels_container_sends_reels_params(monkeypatch):
    captured = {}

    class FakeResponse:
        def json(self):
            return {"id": "creation_123"}

    def fake_post(url, params, timeout):
        captured["url"] = url
        captured["params"] = params
        return FakeResponse()

    monkeypatch.setattr(engine.requests, "post", fake_post)
    creation_id = engine.create_reels_container(
        "https://raw.example.com/latest_reel.mp4", "caption text", "USER1", "TOKEN1"
    )
    assert creation_id == "creation_123"
    assert captured["params"]["media_type"] == "REELS"
    assert captured["params"]["video_url"] == "https://raw.example.com/latest_reel.mp4"
    assert captured["params"]["access_token"] == "TOKEN1"
    assert "USER1" in captured["url"]
