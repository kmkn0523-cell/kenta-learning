"""send_note_email.py のメール種別判定のテスト。"""
# 「成功メール／失敗メール／送らない」を決める純粋関数のテストファイル
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from send_note_email import decide_mail_kind

# テスト用のダミー履歴エントリ（最新の投稿1件分）
LATEST = {"date": "2026/06/10 09:01", "article": "article_08.md", "title": "テスト記事"}


def test_success_with_history_sends_success_mail():
    # 投稿成功＋履歴あり → 成功メールを送る
    assert decide_mail_kind("success", "posted", LATEST) == "success"


def test_skipped_run_sends_no_mail():
    # 重複投稿ガードでスキップした実行 → メールは送らない（2通届く不具合の修正）
    assert decide_mail_kind("success", "skipped", LATEST) is None


def test_failure_sends_failure_mail():
    # 投稿失敗 → 失敗メールを送る
    assert decide_mail_kind("failure", "", LATEST) == "failure"


def test_success_without_history_sends_failure_mail():
    # ステータスは成功でも履歴が無い → 何かおかしいので失敗メール
    assert decide_mail_kind("success", "posted", None) == "failure"


def test_old_workflow_without_result_keeps_current_behavior():
    # 結果シグナルが無い（昔のワークフローやローカル実行）→ 従来どおり成功メール
    assert decide_mail_kind("success", "", LATEST) == "success"
