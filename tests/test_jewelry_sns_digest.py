"""ジュエリーSNS週次ダイジェストのテスト。外部I/O（Exa API・メール送信）はモックする。"""
# テスト対象モジュールを読み込めるようにパスを通す
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "jewelry_watch"))

import jewelry_sns_digest as digest  # 本体モジュール


def test_detect_platform_judges_domain():
    # X系・Instagram・Threads・その他Webを正しく判定できること
    assert digest.detect_platform("https://x.com/user/status/1") == "X"
    assert digest.detect_platform("https://twitter.com/user/status/1") == "X"
    assert digest.detect_platform("https://www.instagram.com/p/abc/") == "Instagram"
    assert digest.detect_platform("https://www.threads.net/@user/post/1") == "Threads"
    assert digest.detect_platform("https://example.com/blog/123") == "Web"


def test_parse_exa_results_extracts_fields():
    # Exaの生レスポンスから必要な項目を取り出し、keywordとplatformを付けること
    response_json = {
        "results": [
            {
                "title": "サントスのネックレス買った",
                "url": "https://x.com/u/status/100",
                "text": "今日サントスネックレスを購入",
                "publishedDate": "2026-06-18T10:00:00.000Z",
            }
        ]
    }
    posts = digest.parse_exa_results(response_json, "サントスネックレス")
    assert len(posts) == 1
    post = posts[0]
    assert post["keyword"] == "サントスネックレス"
    assert post["title"] == "サントスのネックレス買った"
    assert post["url"] == "https://x.com/u/status/100"
    assert post["snippet"] == "今日サントスネックレスを購入"
    assert post["published_date"] == "2026-06-18"
    assert post["platform"] == "X"


def test_parse_exa_results_handles_missing_fields():
    # title/text/publishedDate が無い結果でも落ちず、空文字で埋めること
    response_json = {"results": [{"url": "https://example.com/x"}]}
    posts = digest.parse_exa_results(response_json, "テスト")
    assert posts[0]["title"] == ""
    assert posts[0]["snippet"] == ""
    assert posts[0]["published_date"] == ""
    assert posts[0]["platform"] == "Web"
