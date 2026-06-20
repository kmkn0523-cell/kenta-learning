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


from unittest.mock import patch, MagicMock


def test_search_exa_posts_expected_payload():
    # Exaへ正しいエンドポイント・ヘッダー・本文で投げ、JSONを返すこと
    fake_response = MagicMock()
    fake_response.json.return_value = {"results": []}
    fake_response.raise_for_status.return_value = None
    with patch.object(digest.requests, "post", return_value=fake_response) as mock_post:
        result = digest.search_exa(
            "サントスネックレス", ["x.com", "twitter.com"], "2026-06-14T00:00:00Z", "KEY", 20
        )
    assert result == {"results": []}
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.exa.ai/search"          # エンドポイント
    assert kwargs["headers"]["x-api-key"] == "KEY"          # 認証ヘッダー
    assert kwargs["json"]["query"] == "サントスネックレス"  # クエリ
    assert kwargs["json"]["includeDomains"] == ["x.com", "twitter.com"]
    assert kwargs["json"]["numResults"] == 20


def test_search_exa_omits_domains_when_empty():
    # Web全般（ドメイン空）のときは includeDomains を送らないこと
    fake_response = MagicMock()
    fake_response.json.return_value = {"results": []}
    fake_response.raise_for_status.return_value = None
    with patch.object(digest.requests, "post", return_value=fake_response) as mock_post:
        digest.search_exa("テスト", [], "2026-06-14T00:00:00Z", "KEY", 20)
    _, kwargs = mock_post.call_args
    assert "includeDomains" not in kwargs["json"]


def test_collect_new_posts_aggregates_and_filters():
    # 全クエリの結果を集め、送信済みを除外して返すこと。1クエリ失敗でも止まらないこと
    def fake_search(query, domains, start, key, num):
        # X対象のときだけ1件返し、他は失敗させる
        if domains == ["x.com", "twitter.com"]:
            return {"results": [{"title": "t", "url": "https://x.com/seen", "text": "", "publishedDate": "2026-06-18"},
                                 {"title": "t2", "url": "https://x.com/fresh", "text": "", "publishedDate": "2026-06-18"}]}
        raise RuntimeError("boom")  # 他の対象は失敗

    with patch.object(digest, "search_exa", side_effect=fake_search):
        posts = digest.collect_new_posts("KEY", "2026-06-14T00:00:00Z", {"https://x.com/seen"})
    urls = [p["url"] for p in posts]
    # 送信済みのseenは除外、freshだけ残る（キーワード2つで同じURLが来るので重複も1件に）
    assert "https://x.com/fresh" in urls
    assert "https://x.com/seen" not in urls


def test_build_email_html_escapes_quotes_and_blocks_bad_url():
    # 引用符を含むタイトルで属性を抜け出せないこと、危険なスキームのURLが無効化されること
    posts = [
        {"keyword": "k", "title": '" onmouseover="alert(1)', "url": "javascript:alert(1)",
         "snippet": "s", "published_date": "2026-06-20", "platform": "Web"},
    ]
    html_out = digest.build_email_html(posts, "2026-06-21 07:30 JST")
    # 生の二重引用符＋onmouseover の属性注入が成立していないこと
    assert 'onmouseover="alert(1)"' not in html_out
    assert "&quot;" in html_out  # 引用符がエスケープされている
    assert 'href="javascript:alert(1)"' not in html_out  # 危険スキームは出さない
    assert 'href="#"' in html_out  # 無効リンクに置き換わっている


def test_search_exa_uses_auto_type():
    # SNS投稿を拾いやすい auto 検索を使うこと
    from unittest.mock import patch, MagicMock
    fake_response = MagicMock()
    fake_response.json.return_value = {"results": []}
    fake_response.raise_for_status.return_value = None
    with patch.object(digest.requests, "post", return_value=fake_response) as mock_post:
        digest.search_exa("テスト", ["x.com"], "2026-06-14T00:00:00Z", "KEY", 20)
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["type"] == "auto"


def test_search_exa_omits_date_when_none():
    # 日付がNoneのときは startPublishedDate を送らないこと（期間で絞らない）
    from unittest.mock import patch, MagicMock
    fake_response = MagicMock()
    fake_response.json.return_value = {"results": []}
    fake_response.raise_for_status.return_value = None
    with patch.object(digest.requests, "post", return_value=fake_response) as mock_post:
        digest.search_exa("テスト", ["x.com"], None, "KEY", 20)
    _, kwargs = mock_post.call_args
    assert "startPublishedDate" not in kwargs["json"]


def test_collect_new_posts_falls_back_without_date():
    # 期間付きで0件なら、日付なしで再検索して拾うこと
    from unittest.mock import patch
    calls = []

    def fake_search(query, domains, start, key, num):
        calls.append(start)  # start が None かどうかを記録
        if start is None:  # 日付なし（フォールバック）のときだけ1件返す
            return {"results": [{"title": "t", "url": "https://x.com/fresh", "text": "", "publishedDate": ""}]}
        return {"results": []}  # 期間付きは0件

    with patch.object(digest, "search_exa", side_effect=fake_search):
        posts = digest.collect_new_posts("KEY", "2026-06-14T00:00:00Z", set())
    assert [p["url"] for p in posts] == ["https://x.com/fresh"]
    assert None in calls  # フォールバック（日付なし）が呼ばれたこと


def test_is_promotional_detects_sales_words():
    # 宣伝・販売ワードを含む投稿は宣伝と判定し、普通の感想投稿は通すこと
    promo = {"title": "サントスネックレス 送料無料でセール中", "snippet": "", "url": "https://x.com/shop/1"}
    normal = {"title": "サントスネックレス つけてみた感想", "snippet": "毎日着けてる", "url": "https://x.com/u/1"}
    assert digest.is_promotional(promo) is True
    assert digest.is_promotional(normal) is False


def test_collect_new_posts_flags_promotional():
    # 検索結果は消さず全部残し、宣伝投稿には promotional の印が付くこと
    from unittest.mock import patch

    def fake_search(query, domains, start, key, num):
        return {"results": [
            {"title": "サントス 買取強化中", "url": "https://x.com/buy", "text": "", "publishedDate": "2026-06-20"},
            {"title": "サントス着けてみた", "url": "https://x.com/real", "text": "良い", "publishedDate": "2026-06-20"},
        ]}

    with patch.object(digest, "search_exa", side_effect=fake_search):
        posts = digest.collect_new_posts("KEY", "2026-06-14T00:00:00Z", set())
    by_url = {p["url"]: p for p in posts}
    assert "https://x.com/buy" in by_url and "https://x.com/real" in by_url  # 両方残る
    assert by_url["https://x.com/buy"]["promotional"] is True  # 宣伝に印
    assert by_url["https://x.com/real"]["promotional"] is False  # 感想は印なし
