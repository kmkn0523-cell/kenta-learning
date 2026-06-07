# test_ronin_threads_action.py
# ronin_threads_action の純粋ロジック＋post_to_threadsのreply対応テスト（APIはモック）
# 実行: pytest ronin/tests/test_ronin_threads_action.py -v
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ronin_threads_action as action


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
