# test_release_note.py
# release_note.py の純粋ロジックをテストする（ファイルI/O・対話は対象外）
# 実行: pytest skin/tests/test_release_note.py

import sys
from pathlib import Path

# skin/ フォルダをimportできる場所に加える（既存テストと同じやり方）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from release_note import append_threads_footer


def test_append_threads_footer_フッターを追加する():
    content = "本文テキスト"
    result = append_threads_footer(content)
    assert content in result
    assert "threads.net/@skin_reset_jp" in result


def test_append_threads_footer_既に含まれていれば追加しない():
    content = "本文テキスト\nThreadsはこちら threads.net/@skin_reset_jp"
    result = append_threads_footer(content)
    assert result == content  # 二重付与しない
