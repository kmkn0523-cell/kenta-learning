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
