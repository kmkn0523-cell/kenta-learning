"""ジュエリーSNS週次ダイジェストのテスト。外部I/O（Exa API・メール送信）はモックする。"""
# テスト対象モジュールを読み込めるようにパスを通す
import sys
from pathlib import Path
from datetime import date  # prune_old のテストで日付を作るために使う
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


def test_filter_new_removes_seen_and_dedupes():
    # 送信済みURLは除外し、同一実行内の重複URLも1件にすること
    posts = [
        {"url": "https://x.com/a", "keyword": "k", "title": "", "snippet": "", "published_date": "", "platform": "X"},
        {"url": "https://x.com/a", "keyword": "k", "title": "", "snippet": "", "published_date": "", "platform": "X"},
        {"url": "https://x.com/b", "keyword": "k", "title": "", "snippet": "", "published_date": "", "platform": "X"},
    ]
    new_posts = digest.filter_new(posts, {"https://x.com/b"})
    urls = [p["url"] for p in new_posts]
    assert urls == ["https://x.com/a"]  # bは送信済みで除外、aは1件だけ


def test_prune_old_drops_entries_older_than_retention():
    # first_seen が保持日数より古いエントリだけ捨てること
    today = date(2026, 6, 21)
    seen = [
        {"url": "https://x.com/old", "first_seen": "2026-04-01"},  # 81日前 → 捨てる
        {"url": "https://x.com/new", "first_seen": "2026-06-10"},  # 11日前 → 残す
    ]
    kept = digest.prune_old(seen, today, 60)
    kept_urls = [e["url"] for e in kept]
    assert kept_urls == ["https://x.com/new"]


def test_load_state_returns_empty_when_missing(tmp_path):
    # ファイルが無いときは空のseenを返すこと
    missing = tmp_path / "nope.json"
    assert digest.load_state(missing) == {"seen": []}


def test_save_and_load_state_roundtrip(tmp_path):
    # 保存したものを読み戻せること
    state_file = tmp_path / "state.json"
    entries = [{"url": "https://x.com/a", "first_seen": "2026-06-21"}]
    digest.save_state(state_file, entries)
    loaded = digest.load_state(state_file)
    assert loaded["seen"] == entries


def test_build_subject_shows_count():
    # 件名に新規件数が入ること
    subject = digest.build_subject(3, "2026-06-21")
    assert "3" in subject
    assert "2026-06-21" in subject


def test_build_email_html_groups_and_links():
    # キーワード見出し・プラットフォーム見出し・クリック可能なリンクが入ること
    posts = [
        {"keyword": "サントスネックレス", "title": "投稿A", "url": "https://x.com/a",
         "snippet": "抜粋A", "published_date": "2026-06-18", "platform": "X"},
        {"keyword": "サントスネックレス", "title": "投稿B", "url": "https://www.instagram.com/p/b",
         "snippet": "抜粋B", "published_date": "2026-06-19", "platform": "Instagram"},
    ]
    html = digest.build_email_html(posts, "2026-06-21 07:30 JST")
    assert "サントスネックレス" in html       # キーワード見出し
    assert "X" in html and "Instagram" in html  # プラットフォーム見出し
    assert 'href="https://x.com/a"' in html      # クリック可能なリンク
    assert "投稿A" in html and "抜粋A" in html   # タイトルと抜粋


def test_build_email_html_handles_zero():
    # 新規ゼロのときは「新しい言及なし」の文面になること
    html = digest.build_email_html([], "2026-06-21 07:30 JST")
    assert "新しい言及" in html
