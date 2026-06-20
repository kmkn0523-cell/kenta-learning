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
import html  # HTMLエスケープ用（引用符まで安全にする標準ライブラリ）
import requests  # Exa APIを叩くためのHTTPライブラリ
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
# 検索対象（名前・絞り込むドメイン・取得数）。SNSのみ。X中心でIG/Threadsは補助
SEARCH_TARGETS = [
    {"name": "X", "domains": ["x.com", "twitter.com"], "max_results": 20},  # 主軸
    {"name": "Instagram", "domains": ["instagram.com"], "max_results": 10},  # 補助
    {"name": "Threads", "domains": ["threads.net", "threads.com"], "max_results": 10},  # 補助
]
NUM_RESULTS = 20  # 取得数の既定値（個別指定が無いとき用）
SEARCH_WINDOW_DAYS = 14  # 何日前までの投稿を対象にするか
# 宣伝・販売っぽい投稿を除外するためのNGワード（含まれていたら落とす。後で調整可）
SALES_NG_WORDS = [
    "送料無料", "税込", "税抜", "通販", "在庫", "セール", "クーポン", "割引",
    "お買い得", "買取", "質屋", "メルカリ", "ラクマ", "楽天", "ヤフオク",
    "オンラインブティック", "公式通販", "ご予約", "入荷", "予約受付",
    "ポイント還元", "%off", "円引き", "値下げ", "新品未使用", "アフィリエイト",
    "for sale", "shop now", "buy now", "discount", "coupon", "在庫あり",
]
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


def now_jst_text() -> str:
    """今の日本時間を読みやすい文字列で返す。"""
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")


def _escape(text: str) -> str:
    """HTMLに埋め込むとき危ない文字をエスケープする（引用符 " ' も含む）。"""
    return html.escape(text or "", quote=True)  # quote=Trueで属性内も安全になる


def _safe_url(url: str) -> str:
    """href に出して安全なURLだけ通す。http/https以外は無効化する。"""
    scheme = urlparse(url or "").scheme.lower()  # URLのスキーム部分を取り出す
    if scheme not in ("http", "https"):  # javascript: などの危ないスキームを弾く
        return "#"  # 無効なリンク先に置き換える
    return url


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
                url = _escape(_safe_url(post["url"]))  # スキーム検証してから属性用にエスケープ
                parts.append(
                    f'<li><a href="{url}">{title}</a>'  # クリック可能なリンク
                    f"<br><small>{published}</small><br>{snippet}</li>"  # 日付と抜粋
                )
            parts.append("</ul>")  # 箇条書き終了
    return "\n".join(parts)


def search_exa(query, include_domains, start_published_date, api_key, num_results=NUM_RESULTS):
    """Exa（Web検索API）に問い合わせて、生のJSONレスポンスを返す。"""
    payload = {
        "query": query,  # 検索キーワード
        "type": "auto",  # Exaに検索方式を任せる（神経検索中心でSNS投稿を拾いやすい）
        "numResults": num_results,  # 取得件数
        "contents": {"text": True},  # 抜粋テキストも取得する
    }
    if start_published_date:  # 日付指定があるときだけ付ける（Noneなら期間で絞らない）
        payload["startPublishedDate"] = start_published_date
    if include_domains:  # ドメイン指定があるとき
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


def is_promotional(post: dict) -> bool:
    """宣伝・販売っぽい投稿かどうかを判定する（NGワードを含むか）。"""
    text = f"{post.get('title', '')} {post.get('snippet', '')} {post.get('url', '')}".lower()
    return any(word.lower() in text for word in SALES_NG_WORDS)  # 1つでも含めば宣伝とみなす


def _search_all_targets(api_key: str, start_published_date, already_seen: set[str]) -> list[dict]:
    """全キーワード×全対象を1周検索して、宣伝を除いたパース済み投稿のリストを返す（件数をログ出力）。"""
    all_posts = []  # 集めた投稿をためる
    for keyword in KEYWORDS:  # キーワードごと
        for target in SEARCH_TARGETS:  # 検索対象ごと
            try:
                response_json = search_exa(  # Exaに問い合わせる
                    keyword, target["domains"], start_published_date, api_key,
                    target.get("max_results", NUM_RESULTS)  # 対象ごとの取得数（Xは多め）
                )
                posts = parse_exa_results(response_json, keyword)  # 結果を変換
                kept = [p for p in posts if not is_promotional(p)]  # 宣伝っぽいものを除外
                dropped = len(posts) - len(kept)  # 落とした件数
                print(f"取得（{keyword} / {target['name']}）: {len(kept)}件（宣伝除外 {dropped}件）")
                all_posts.extend(kept)  # 残った分を足す
            except Exception as error:  # 1クエリ失敗しても止めない
                print(f"検索失敗（{keyword} / {target['name']}）: {error}")
    return all_posts


def collect_new_posts(api_key: str, start_published_date: str, already_seen: set[str]) -> list[dict]:
    """全キーワード×全対象を検索し、パースして新規投稿だけ返す。

    まず期間（直近N日）で検索し、1件も取れなければ期間条件を外して再検索する。
    SNSページは投稿日が取れず日付フィルタで全部落ちることがあるため。
    """
    all_posts = _search_all_targets(api_key, start_published_date, already_seen)  # まず期間付き
    new_posts = filter_new(all_posts, already_seen)  # 新規分だけ残す
    if not new_posts:  # 期間付きでゼロなら
        print("期間付き検索で0件 → 期間条件を外して再検索します")
        all_posts = _search_all_targets(api_key, None, already_seen)  # 日付なしで再検索
        new_posts = filter_new(all_posts, already_seen)
    return new_posts


def main() -> None:
    """全体の処理を実行する。"""
    api_key = os.environ["EXA_API_KEY"]  # Exaのキー（無ければ例外で止まる）
    today = datetime.now(JST).date()  # 今日（JST）
    # 直近N日より後の投稿だけを対象にする（UTC ISO8601文字列）
    start_published_date = (datetime.now(timezone.utc) - timedelta(days=SEARCH_WINDOW_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")

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
