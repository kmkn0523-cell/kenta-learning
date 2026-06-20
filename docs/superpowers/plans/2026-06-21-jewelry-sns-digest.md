# ジュエリーSNS週次ダイジェスト Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 毎週土曜7:30(JST)に「サントスネックレス」「ジュストアンクルブレスレット」の直近1週間のSNS言及をExa検索で集め、新規分だけをHTMLメールで自分宛に送る仕組みを作る。

**Architecture:** 既存の `price_watch/`（iPhone価格監視）と同じ GitHub Actions cron + Python + Gmail送信(`smtplib`) + 状態JSONコミット のパターンを流用する。本体 `jewelry_watch/jewelry_sns_digest.py` がExa APIで各SNSドメインを横断検索し、`jewelry_watch_state.json` で送信済みURLを管理して重複を防ぐ。

**Tech Stack:** Python 3.12 / `requests`（新規・Exa呼び出し）/ `python-dotenv`（既存）/ `smtplib`（標準）/ pytest / GitHub Actions

## Global Constraints

- コードは1行ごとに初心者向けの日本語コメントを付ける（既存 `iphone_price_watcher.py` と同じ密度）。
- 変数名・関数名は略さない分かりやすい英単語。
- 秘密情報は環境変数から読む（`.env` またはGitHub Secrets）。コードに直書きしない。
- 日本時間は `JST = timezone(timedelta(hours=9))` で扱う。
- 監視キーワード: `["サントスネックレス", "ジュストアンクルブレスレット"]`
- 検索対象と件数: キーワード × 検索対象（X / Instagram / Threads / Web全般）ごとに最大 **20件**。
- state保持: `first_seen` が60日より古いエントリは保存時に捨てる。
- 必要シークレット: `EXA_API_KEY`（新規）/ `GMAIL_ADDRESS`・`GMAIL_APP_PASSWORD`（既存流用）。
- 新規ゼロの週も1通送る（稼働確認を兼ねる）。
- 外部I/O（Exa API・メール送信）はテストでモックする。

---

## ファイル構成

- Create: `jewelry_watch/jewelry_sns_digest.py` — 本体（パース・重複除外・メール生成・Exa呼び出し・main）
- Create: `jewelry_watch/jewelry_watch_state.json` — 送信済みURL記録（初期は空 `{"seen": []}`）
- Create: `tests/test_jewelry_sns_digest.py` — pytest
- Create: `.github/workflows/jewelry_sns_weekly.yml` — 土曜7:30 JST cron

### 投稿データの形（全タスク共通）

1件の投稿は次のキーを持つ辞書で表す:

```python
{
    "keyword": "サントスネックレス",   # どのキーワードでヒットしたか
    "title": "...",                    # タイトル
    "url": "https://...",              # リンク
    "snippet": "...",                  # 抜粋（無ければ ""）
    "published_date": "2026-06-18",    # 投稿日（無ければ ""）
    "platform": "X",                   # X / Instagram / Threads / Web
}
```

---

### Task 1: プラットフォーム判定とExaレスポンスのパース

**Files:**
- Create: `jewelry_watch/jewelry_sns_digest.py`
- Test: `tests/test_jewelry_sns_digest.py`

**Interfaces:**
- Produces:
  - `detect_platform(url: str) -> str` — URLのドメインから `"X"`/`"Instagram"`/`"Threads"`/`"Web"` を返す
  - `parse_exa_results(response_json: dict, keyword: str) -> list[dict]` — Exaの生JSONを投稿辞書のリストに変換（各辞書に `keyword` と `platform` を付与）

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_jewelry_sns_digest.py` を新規作成:

```python
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
```

- [ ] **Step 2: テストを実行して失敗を確認**

Run: `pytest tests/test_jewelry_sns_digest.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'jewelry_sns_digest'`）

- [ ] **Step 3: 本体に最小実装を書く**

`jewelry_watch/jewelry_sns_digest.py` を新規作成:

```python
"""「サントスネックレス」「ジュストアンクルブレスレット」のSNS言及を週1回集めてメールするスクリプト。

やること（おおまかな流れ）:
1. Exa（Web検索API）で各SNSドメインを直近7日で横断検索する
2. 結果からタイトル・URL・抜粋・投稿日・プラットフォームを取り出す
3. 送信済みURL（jewelry_watch_state.json）と照合して新規分だけ残す
4. キーワード別・プラットフォーム別にまとめたHTMLメールをGmailで自分宛に送る
5. 今回拾ったURLを記録ファイルに追記する

ローカルでもGitHub Actionsでも動く。秘密情報はすべて環境変数（.env または Secrets）から読む。
"""
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from urllib.parse import urlparse

# .env があれば読み込む（GitHub Actionsでは環境変数が直接入るので無くてもOK）
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ===== 設定 =====
# 監視するキーワード（この2つの言及を集める）
KEYWORDS = ["サントスネックレス", "ジュストアンクルブレスレット"]
# 検索対象（名前と、絞り込むドメイン。Web全般は空リスト＝ドメイン指定なし）
SEARCH_TARGETS = [
    {"name": "X", "domains": ["x.com", "twitter.com"]},
    {"name": "Instagram", "domains": ["instagram.com"]},
    {"name": "Threads", "domains": ["threads.net", "threads.com"]},
    {"name": "Web", "domains": []},
]
NUM_RESULTS = 20  # キーワード×対象ごとの最大取得件数
STATE_RETENTION_DAYS = 60  # 記録を残す日数（これより古いURL記録は捨てる）
STATE_FILE = Path(__file__).with_name("jewelry_watch_state.json")  # 送信済みURLの記録先
JST = timezone(timedelta(hours=9))  # 日本時間


def detect_platform(url: str) -> str:
    """URLのドメインを見て、どのSNSかを返す（該当しなければ Web）。"""
    host = urlparse(url).netloc.lower()  # URLからドメイン部分だけ取り出して小文字化
    if "x.com" in host or "twitter.com" in host:  # X（旧Twitter）
        return "X"
    if "instagram.com" in host:  # Instagram
        return "Instagram"
    if "threads.net" in host or "threads.com" in host:  # Threads
        return "Threads"
    return "Web"  # どれにも当てはまらなければWeb全般


def parse_exa_results(response_json: dict, keyword: str) -> list[dict]:
    """Exaの生レスポンスを、扱いやすい投稿辞書のリストに変換する。"""
    posts = []  # ここに結果をためる
    for item in response_json.get("results", []):  # results が無ければ空ループ
        url = item.get("url", "")  # リンク
        published = item.get("publishedDate", "") or ""  # 投稿日時（無ければ空）
        posts.append({
            "keyword": keyword,  # どのキーワードで見つけたか
            "title": item.get("title") or "",  # タイトル（無ければ空）
            "url": url,  # リンク
            "snippet": item.get("text") or "",  # 抜粋（無ければ空）
            "published_date": published[:10],  # 先頭10文字でYYYY-MM-DDだけ取る
            "platform": detect_platform(url),  # SNS種別を判定
        })
    return posts
```

- [ ] **Step 4: テストを実行して成功を確認**

Run: `pytest tests/test_jewelry_sns_digest.py -v`
Expected: PASS（3件）

- [ ] **Step 5: コミット**

```bash
git add jewelry_watch/jewelry_sns_digest.py tests/test_jewelry_sns_digest.py
git commit -m "feat: ジュエリーSNS digest - パースとプラットフォーム判定"
```

---

### Task 2: 重複除外とstate管理

**Files:**
- Modify: `jewelry_watch/jewelry_sns_digest.py`
- Create: `jewelry_watch/jewelry_watch_state.json`
- Test: `tests/test_jewelry_sns_digest.py`

**Interfaces:**
- Consumes: なし
- Produces:
  - `load_state(state_file: Path) -> dict` — 記録ファイルを読み、`{"seen": [...]}` を返す（無ければ空）
  - `seen_urls(state: dict) -> set[str]` — state内の送信済みURL集合を返す
  - `filter_new(posts: list[dict], already_seen: set[str]) -> list[dict]` — 未送信のURLだけ残す（同一実行内のURL重複も1件に）
  - `prune_old(seen_entries: list[dict], today: date, retention_days: int) -> list[dict]` — `first_seen` が古いエントリを捨てる
  - `save_state(state_file: Path, seen_entries: list[dict]) -> None` — 記録ファイルに書き出す

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_jewelry_sns_digest.py` に追記:

```python
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
```

- [ ] **Step 2: テストを実行して失敗を確認**

Run: `pytest tests/test_jewelry_sns_digest.py -k "filter_new or prune_old or load_state or roundtrip" -v`
Expected: FAIL（`AttributeError: module ... has no attribute 'filter_new'`）

- [ ] **Step 3: 本体に最小実装を追記**

`jewelry_watch/jewelry_sns_digest.py` の末尾に追記:

```python
def load_state(state_file: Path) -> dict:
    """記録ファイルを読む。無ければ空のseenを返す。"""
    if not state_file.exists():  # ファイルがまだ無いとき
        return {"seen": []}
    try:
        data = json.loads(state_file.read_text())  # JSONを読み込む
        if "seen" not in data:  # 想定キーが無ければ補う
            data["seen"] = []
        return data
    except Exception:
        return {"seen": []}  # 壊れていても落ちないよう空で返す


def seen_urls(state: dict) -> set[str]:
    """state内の送信済みURLの集合を返す。"""
    return {entry.get("url", "") for entry in state.get("seen", [])}


def filter_new(posts: list[dict], already_seen: set[str]) -> list[dict]:
    """送信済みでなく、まだ出ていないURLの投稿だけを残す。"""
    new_posts = []  # 残すものをためる
    seen_in_this_run = set()  # この実行内で既に拾ったURL
    for post in posts:
        url = post.get("url", "")  # この投稿のURL
        if not url:  # URLが無いものは捨てる
            continue
        if url in already_seen:  # 過去に送信済み
            continue
        if url in seen_in_this_run:  # 同じ実行内で重複
            continue
        seen_in_this_run.add(url)  # 拾ったと記録
        new_posts.append(post)  # 残す
    return new_posts


def prune_old(seen_entries: list[dict], today: date, retention_days: int) -> list[dict]:
    """first_seen が保持日数より古い記録を捨てる。"""
    kept = []  # 残すものをためる
    for entry in seen_entries:
        first_seen_text = entry.get("first_seen", "")  # 最初に見た日
        try:
            first_seen = date.fromisoformat(first_seen_text)  # 文字列を日付に変換
        except ValueError:
            kept.append(entry)  # 日付が読めないものは念のため残す
            continue
        age_days = (today - first_seen).days  # 何日前か
        if age_days <= retention_days:  # 保持日数以内なら残す
            kept.append(entry)
    return kept


def save_state(state_file: Path, seen_entries: list[dict]) -> None:
    """送信済みURL記録をファイルに書き出す。"""
    data = {"seen": seen_entries}  # 保存する形に整える
    state_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
```

- [ ] **Step 4: 初期state ファイルを作成**

`jewelry_watch/jewelry_watch_state.json` を新規作成:

```json
{
  "seen": []
}
```

- [ ] **Step 5: テストを実行して成功を確認**

Run: `pytest tests/test_jewelry_sns_digest.py -v`
Expected: PASS（全件）

- [ ] **Step 6: コミット**

```bash
git add jewelry_watch/jewelry_sns_digest.py jewelry_watch/jewelry_watch_state.json tests/test_jewelry_sns_digest.py
git commit -m "feat: ジュエリーSNS digest - 重複除外とstate管理"
```

---

### Task 3: メール件名・HTML本文の生成

**Files:**
- Modify: `jewelry_watch/jewelry_sns_digest.py`
- Test: `tests/test_jewelry_sns_digest.py`

**Interfaces:**
- Consumes: Task1の投稿辞書
- Produces:
  - `now_jst_text() -> str` — 現在のJSTを `"YYYY-MM-DD HH:MM JST"` で返す
  - `group_for_email(posts: list[dict]) -> dict` — `{keyword: {platform: [posts]}}` にまとめる
  - `build_subject(new_count: int, today_text: str) -> str` — 件名を返す
  - `build_email_html(posts: list[dict], generated_at: str) -> str` — HTML本文を返す（新規ゼロにも対応）

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_jewelry_sns_digest.py` に追記:

```python
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
```

- [ ] **Step 2: テストを実行して失敗を確認**

Run: `pytest tests/test_jewelry_sns_digest.py -k "subject or email_html" -v`
Expected: FAIL（`AttributeError: ... 'build_subject'`）

- [ ] **Step 3: 本体に最小実装を追記**

`jewelry_watch/jewelry_sns_digest.py` の末尾に追記:

```python
def now_jst_text() -> str:
    """今の日本時間を読みやすい文字列で返す。"""
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")


def _escape(text: str) -> str:
    """HTMLに埋め込むとき危ない文字をエスケープする。"""
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def group_for_email(posts: list[dict]) -> dict:
    """投稿を {キーワード: {プラットフォーム: [投稿...]}} の形にまとめる。"""
    grouped = {}  # まとめ先
    for post in posts:
        keyword = post["keyword"]  # キーワード
        platform = post["platform"]  # プラットフォーム
        grouped.setdefault(keyword, {})  # キーワードの箱を用意
        grouped[keyword].setdefault(platform, [])  # プラットフォームの箱を用意
        grouped[keyword][platform].append(post)  # 投稿を入れる
    return grouped


def build_subject(new_count: int, today_text: str) -> str:
    """メール件名を作る。"""
    return f"【ジュエリーSNS週報】{today_text} 新規{new_count}件"


def build_email_html(posts: list[dict], generated_at: str) -> str:
    """投稿一覧からHTMLメール本文を作る。新規ゼロにも対応する。"""
    parts = []  # HTMLの断片をためる
    parts.append(f"<p>生成日時: {_escape(generated_at)}</p>")  # いつ作ったか
    if not posts:  # 新規が1件も無いとき
        parts.append("<p>今週は新しい言及はありませんでした。</p>")
        return "\n".join(parts)
    grouped = group_for_email(posts)  # キーワード→プラットフォームでまとめる
    for keyword, by_platform in grouped.items():  # キーワードごと
        parts.append(f"<h2>{_escape(keyword)}</h2>")  # キーワード見出し
        for platform, items in by_platform.items():  # プラットフォームごと
            parts.append(f"<h3>{_escape(platform)}（{len(items)}件）</h3>")  # 小見出し
            parts.append("<ul>")  # 箇条書き開始
            for post in items:  # 投稿1件ずつ
                title = _escape(post["title"] or post["url"])  # タイトル（無ければURL）
                snippet = _escape(post["snippet"])  # 抜粋
                published = _escape(post["published_date"])  # 投稿日
                url = _escape(post["url"])  # リンク（属性用にエスケープ）
                parts.append(
                    f'<li><a href="{url}">{title}</a>'  # クリック可能なリンク
                    f"<br><small>{published}</small><br>{snippet}</li>"  # 日付と抜粋
                )
            parts.append("</ul>")  # 箇条書き終了
    return "\n".join(parts)
```

- [ ] **Step 4: テストを実行して成功を確認**

Run: `pytest tests/test_jewelry_sns_digest.py -v`
Expected: PASS（全件）

- [ ] **Step 5: コミット**

```bash
git add jewelry_watch/jewelry_sns_digest.py tests/test_jewelry_sns_digest.py
git commit -m "feat: ジュエリーSNS digest - メール件名とHTML本文の生成"
```

---

### Task 4: Exa API 呼び出しとメール送信

**Files:**
- Modify: `jewelry_watch/jewelry_sns_digest.py`
- Test: `tests/test_jewelry_sns_digest.py`

**Interfaces:**
- Consumes: なし
- Produces:
  - `search_exa(query: str, include_domains: list[str], start_published_date: str, api_key: str, num_results: int = NUM_RESULTS) -> dict` — Exaに問い合わせて生JSONを返す（`requests` 使用）
  - `send_email(subject: str, html_body: str) -> None` — Gmailで自分宛にHTMLメールを送る

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_jewelry_sns_digest.py` に追記（`requests` をモック）:

```python
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
```

- [ ] **Step 2: テストを実行して失敗を確認**

Run: `pytest tests/test_jewelry_sns_digest.py -k "search_exa" -v`
Expected: FAIL（`AttributeError: ... 'search_exa'` または `requests` 未import）

- [ ] **Step 3: 本体に最小実装を追記**

`jewelry_watch/jewelry_sns_digest.py` の冒頭importに `requests` を足す（`import json` の下あたり）:

```python
import requests  # Exa APIを叩くためのHTTPライブラリ
```

末尾に追記:

```python
def search_exa(query, include_domains, start_published_date, api_key, num_results=NUM_RESULTS):
    """Exa（Web検索API）に問い合わせて、生のJSONレスポンスを返す。"""
    payload = {
        "query": query,  # 検索キーワード
        "numResults": num_results,  # 取得件数
        "startPublishedDate": start_published_date,  # この日時より後の投稿だけ
        "contents": {"text": True},  # 抜粋テキストも取得する
    }
    if include_domains:  # ドメイン指定があるとき（Web全般のときは付けない）
        payload["includeDomains"] = include_domains
    headers = {"x-api-key": api_key}  # 認証ヘッダー
    response = requests.post(  # ExaにPOSTする
        "https://api.exa.ai/search",
        json=payload,
        headers=headers,
        timeout=30,  # 30秒で諦める
    )
    response.raise_for_status()  # エラーなら例外を投げる（握りつぶさない）
    return response.json()  # JSONを辞書にして返す


def send_email(subject: str, html_body: str) -> None:
    """GmailでHTMLメールを自分宛に送る（アプリパスワードを使う）。"""
    gmail_address = os.environ["GMAIL_ADDRESS"]  # 送信元Gmail
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]  # アプリパスワード
    notify_to = os.environ.get("NOTIFY_TO", gmail_address)  # 通知先（既定は自分宛）

    message = MIMEText(html_body, "html", "utf-8")  # HTMLメールとして作る
    message["Subject"] = Header(subject, "utf-8")  # 件名
    message["From"] = gmail_address  # 差出人
    message["To"] = notify_to  # 宛先

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:  # GmailにSSL接続
        server.login(gmail_address, gmail_app_password)  # ログイン
        server.sendmail(gmail_address, [notify_to], message.as_string())  # 送信
```

- [ ] **Step 4: テストを実行して成功を確認**

Run: `pytest tests/test_jewelry_sns_digest.py -v`
Expected: PASS（全件）

- [ ] **Step 5: コミット**

```bash
git add jewelry_watch/jewelry_sns_digest.py tests/test_jewelry_sns_digest.py
git commit -m "feat: ジュエリーSNS digest - Exa呼び出しとメール送信"
```

---

### Task 5: main() で全体を統合

**Files:**
- Modify: `jewelry_watch/jewelry_sns_digest.py`
- Test: `tests/test_jewelry_sns_digest.py`

**Interfaces:**
- Consumes: Task1〜4の全関数
- Produces:
  - `collect_new_posts(api_key: str, start_published_date: str, already_seen: set[str]) -> list[dict]` — 全キーワード×全対象を検索し、パース・新規除外して返す（1クエリ失敗は警告して続行）
  - `main() -> None` — 収集→メール送信→state更新までを実行

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_jewelry_sns_digest.py` に追記:

```python
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
```

- [ ] **Step 2: テストを実行して失敗を確認**

Run: `pytest tests/test_jewelry_sns_digest.py -k "collect_new_posts" -v`
Expected: FAIL（`AttributeError: ... 'collect_new_posts'`）

- [ ] **Step 3: 本体に最小実装を追記**

`jewelry_watch/jewelry_sns_digest.py` の末尾に追記:

```python
def collect_new_posts(api_key: str, start_published_date: str, already_seen: set[str]) -> list[dict]:
    """全キーワード×全対象を検索し、パースして新規投稿だけ返す。"""
    all_posts = []  # 集めた投稿をためる
    for keyword in KEYWORDS:  # キーワードごと
        for target in SEARCH_TARGETS:  # 検索対象ごと
            try:
                response_json = search_exa(  # Exaに問い合わせる
                    keyword, target["domains"], start_published_date, api_key, NUM_RESULTS
                )
                all_posts.extend(parse_exa_results(response_json, keyword))  # 結果を足す
            except Exception as error:  # 1クエリ失敗しても止めない
                print(f"検索失敗（{keyword} / {target['name']}）: {error}")
    return filter_new(all_posts, already_seen)  # 新規分だけ残す


def main() -> None:
    """全体の処理を実行する。"""
    api_key = os.environ["EXA_API_KEY"]  # Exaのキー（無ければ例外で止まる）
    today = datetime.now(JST).date()  # 今日（JST）
    # 直近7日より後の投稿だけを対象にする（UTC ISO8601文字列）
    start_published_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    state = load_state(STATE_FILE)  # 過去の送信済み記録を読む
    already_seen = seen_urls(state)  # 送信済みURL集合

    new_posts = collect_new_posts(api_key, start_published_date, already_seen)  # 新規収集

    today_text = today.strftime("%Y-%m-%d")  # 件名用の日付
    subject = build_subject(len(new_posts), today_text)  # 件名
    html_body = build_email_html(new_posts, now_jst_text())  # 本文
    send_email(subject, html_body)  # 送信
    print(f"送信完了: 新規{len(new_posts)}件")

    # state更新: 今回の新規URLを first_seen 付きで追加し、古い記録は掃除して保存
    new_entries = [{"url": post["url"], "first_seen": today_text} for post in new_posts]
    merged = state.get("seen", []) + new_entries  # 既存＋今回
    kept = prune_old(merged, today, STATE_RETENTION_DAYS)  # 古いものを捨てる
    save_state(STATE_FILE, kept)  # 保存


if __name__ == "__main__":
    main()  # スクリプトとして実行されたらmainを動かす
```

- [ ] **Step 4: テストを実行して成功を確認**

Run: `pytest tests/test_jewelry_sns_digest.py -v`
Expected: PASS（全件）

- [ ] **Step 5: 全体テストを実行**

Run: `pytest tests/ skin/tests/`
Expected: 既存テストを壊していないこと（全PASS）

- [ ] **Step 6: コミット**

```bash
git add jewelry_watch/jewelry_sns_digest.py tests/test_jewelry_sns_digest.py
git commit -m "feat: ジュエリーSNS digest - main統合"
```

---

### Task 6: GitHub Actions ワークフロー

**Files:**
- Create: `.github/workflows/jewelry_sns_weekly.yml`

**Interfaces:**
- Consumes: `jewelry_watch/jewelry_sns_digest.py`、Secrets（`EXA_API_KEY` / `GMAIL_ADDRESS` / `GMAIL_APP_PASSWORD`）

- [ ] **Step 1: ワークフローを作成**

`.github/workflows/jewelry_sns_weekly.yml` を新規作成:

```yaml
# jewelry_sns_weekly.yml
# 「サントスネックレス」「ジュストアンクルブレスレット」のSNS言及を週1回集めてメールするワークフロー。
# 毎週土曜 JST 7:30 に実行する。

name: ジュエリーSNS週次ダイジェスト

on:
  schedule:
    # GitHub Actionsのcronは数分〜数十分遅れることがある（多少前後してOK）
    # JST 土曜7:30 = UTC 金曜22:30（JST = UTC+9 なので9時間引く）
    - cron: '30 22 * * 5'
  workflow_dispatch:  # 手動でも実行できるようにする（テスト用）

# 同じグループ名のジョブは同時に1つだけ動かす（push競合を防ぐ）
concurrency:
  group: jewelry-sns-weekly
  cancel-in-progress: false

jobs:
  digest:
    runs-on: ubuntu-latest  # GitHubのサーバーで動かす
    permissions:
      contents: write  # 状態ファイルのコミットに必要

    steps:
      # Step 1: リポジトリのファイルをダウンロードする
      - name: リポジトリをチェックアウト
        uses: actions/checkout@v4

      # Step 2: Pythonをセットアップする
      - name: Python 3.12 をセットアップ
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # Step 3: 必要なライブラリをインストールする
      - name: ライブラリをインストール
        run: pip install requests python-dotenv

      # Step 4: SNS言及を集めてメール送信する
      - name: ダイジェスト実行
        env:
          EXA_API_KEY: ${{ secrets.EXA_API_KEY }}
          GMAIL_ADDRESS: ${{ secrets.GMAIL_ADDRESS }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
        run: python jewelry_watch/jewelry_sns_digest.py

      # Step 5: 更新した状態ファイルをGitにコミット＆プッシュする
      - name: 状態ファイルをGitにコミット＆プッシュ
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add jewelry_watch/jewelry_watch_state.json
          if ! git diff --staged --quiet; then
            git commit -m "自動同期: ジュエリーSNS送信済みURL更新"
            for i in 1 2 3; do
              git pull --rebase origin main && git push && break
              echo "push失敗 リトライ $i/3..."
              sleep 5
            done
          fi
```

- [ ] **Step 2: YAML構文を確認**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/jewelry_sns_weekly.yml'))"`
Expected: エラーなし（何も出力されない）

- [ ] **Step 3: コミット**

```bash
git add .github/workflows/jewelry_sns_weekly.yml
git commit -m "feat: ジュエリーSNS週次ダイジェストのワークフロー追加"
```

---

## 実装後の手動セットアップ（ユーザー作業・要案内）

実装完了後、Kentaに以下を案内する（コードでは完結しない）:

1. **Exa APIキー取得**: `exa.ai` で無料登録 → API Keyを発行
2. **GitHub Secrets登録**: リポジトリの Settings → Secrets and variables → Actions に
   - `EXA_API_KEY` を新規追加（`GMAIL_ADDRESS`・`GMAIL_APP_PASSWORD` は既存を流用）
3. **手動テスト実行**: `gh workflow run jewelry_sns_weekly.yml` で1度動かし、メールが届くか確認

---

## Self-Review（記入済み）

- **Spec coverage**: 検索対象4種=Task1/5、Exa呼び出し=Task4、重複防止+60日掃除=Task2、HTML/件数/ゼロ件=Task3、エラーハンドリング(1クエリ失敗継続)=Task5、cron土曜7:30=Task6、テスト=各タスク。全要件にタスクあり。
- **Placeholder scan**: TBD/TODO等なし。各コードステップに実コードあり。
- **Type consistency**: 投稿辞書のキー（keyword/title/url/snippet/published_date/platform）は全タスクで一致。`search_exa`/`filter_new`/`build_email_html`/`collect_new_posts` の呼び出しシグネチャはTask間で一致。
