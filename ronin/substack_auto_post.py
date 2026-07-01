# substack_auto_post.py
# 書道カード画像 + 諺テキストを Substack に自動投稿するスクリプト
# curl_cffi: Chrome の TLS フィンガープリントを完全に再現して Cloudflare を回避する
# 使い方: python3 substack_auto_post.py

import os           # パソコンの環境変数を読み込む道具
import re           # 文字列のパターン検索をする道具
import json         # JSONファイルを読み書きする道具
from urllib.parse import unquote         # URLエンコードを元に戻す道具
from datetime import datetime, timezone, timedelta  # 日時を扱う道具（timedeltaは時差計算用）

# 日本時間（JST）は世界標準時（UTC）より9時間進んでいる
JST = timezone(timedelta(hours=9))  # 「毎日きっちり1本」の判定を日本の日付で行うために使う
from dotenv import load_dotenv           # .envファイルからAPIキーを読み込む道具
from curl_cffi import requests as cf     # ChromeのTLSフィンガープリントを模倣してCloudflare回避
import base64                             # 画像データをBase64文字列に変換する道具

# .envファイルを読み込む
load_dotenv()

# =============================
# 設定
# =============================
SUBSTACK_SID     = os.getenv("SUBSTACK_SID")          # Substackのセッションクッキー
PUBLICATION_URL  = "https://roninwords.substack.com"  # パブリケーションのURL
SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR       = os.path.join(SCRIPT_DIR, "ronin_images")
CARDS_FILE       = os.path.join(SCRIPT_DIR, "generate_ronin_cards.py")   # 画像と1対1で対応するデータ
PROVERBS_FILE    = os.path.join(SCRIPT_DIR, "ronin_words_proverbs_100.md")  # 説明文を取得するために使う
PROGRESS_FILE    = os.path.join(SCRIPT_DIR, "substack", "substack_progress.json")
MAX_DAY          = 100  # 総日数


# =============================
# 進捗ファイルの読み書き
# =============================
def load_progress():
    """今日は何日目を投稿するか、進捗ファイルから読み込む"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # 初回実行時はゼロスタート
    return {"next_day": 1, "history": []}


def save_progress(progress):
    """投稿完了後に進捗ファイルを更新する"""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def posted_japanese_set(progress):
    """これまでに投稿した日本語の諺を集合（重複なしのまとまり）にして返す

    データ（generate_ronin_cards.py）には同じ諺が別のday番号で複数登録されている箇所がある。
    day番号だけで重複チェックすると、別day番号の同じ諺をはじけず二重投稿になる。
    そこで「諺の日本語そのもの」で投稿済みかを判定するために、過去の履歴から日本語を集める。
    """
    posted = set()
    for record in progress.get("history", []):
        # title は「日本語 — English」の形。最初の「 — 」より前が日本語の諺
        japanese = record.get("title", "").split(" — ")[0].strip()
        if japanese:
            posted.add(japanese)
    return posted


def find_next_unposted_day(progress, proverbs, also_posted=None):
    """next_day から順番に見ていき、まだ投稿していない諺の最初のday番号を返す

    過去に別のday番号で投稿済みの諺（データ重複）は飛ばす。
    also_posted には「progress.json以外で投稿済みと分かっている諺」（例: Substackの
    公開記事一覧から取得した諺）を渡せる。progress.jsonが巻き戻っても二重投稿しないための引数。
    これ以上投稿できる諺が無ければ None を返す。
    """
    posted = posted_japanese_set(progress)              # progress.json上で投稿済みの諺の集合
    if also_posted:
        posted = posted | set(also_posted)              # ライブ公開済みの諺も「投稿済み」に含める
    day = progress.get("next_day", 1)                   # どのday番号から探し始めるか
    while day <= MAX_DAY:
        proverb = proverbs.get(day)                     # そのday番号の諺データ
        # データがあって、まだその諺を投稿していなければ、それが次に投稿するday
        if proverb and proverb["japanese"] not in posted:
            return day
        day += 1                                        # 重複や欠番なら次のdayへ進む
    return None                                          # もう投稿できる諺が無い


def japanese_from_titles(titles):
    """記事タイトルのリストから、日本語の諺だけを取り出して集合で返す

    カード記事のタイトルは「日本語 — English」の形。最初の「 — 」より前を取り出し、
    そこに日本語（ひらがな・カタカナ・漢字）が含まれるものだけを諺として拾う。
    deep-dive記事は英語タイトルなので自然に除外される。
    """
    result = set()
    for title in titles:
        head = title.split(" — ")[0].strip()
        # ひらがな(3040-309F)・カタカナ(30A0-30FF)・漢字(4E00-9FFF)のいずれかを含むか
        if head and any("぀" <= c <= "鿿" for c in head):
            result.add(head)
    return result


def build_session():
    """Substackへリクエストする curl_cffi セッション（Chrome偽装）を作って返す"""
    if not SUBSTACK_SID:
        raise ValueError("SUBSTACK_SID が .env に設定されていません")
    sid_decoded = unquote(SUBSTACK_SID)                 # クッキーのURLエンコードを解除する
    session = cf.Session(impersonate="chrome131")       # ChromeのTLSフィンガープリントを偽装
    session.cookies.set("substack.sid", sid_decoded, domain=".substack.com")
    session.headers.update({                            # ブラウザ風ヘッダーでBot検知を回避
        "Origin":  "https://substack.com",
        "Referer": "https://substack.com/publish/post",
    })
    return session


def fetch_published_japanese(session):
    """Substackの公開記事一覧を全件取得し、投稿済みの日本語諺の集合を返す

    progress.json（自動同期cron等で巻き戻ることがある）に頼らず、Substack本体という
    確実な情報源で「もう公開した諺」を確認するための最終防壁。
    取得に失敗したら例外を投げる（呼び出し側で「確認できないなら投稿を見送る」判断をする）。
    """
    titles = []
    offset = 0
    while True:
        resp = session.get(
            f"{PUBLICATION_URL}/api/v1/archive?sort=new&limit=50&offset={offset}"
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"公開記事一覧の取得失敗 [{resp.status_code}]: {resp.text[:200]}"
            )
        batch = resp.json()
        if not batch:
            break
        titles.extend(post.get("title", "") for post in batch)
        offset += len(batch)
        if len(batch) < 50:                             # 50件未満なら最後のページ
            break
    return japanese_from_titles(titles)


# =============================
# 諺データの解析
# =============================
def parse_explanations():
    """ronin_words_proverbs_100.md から「日本語 → 説明文」の辞書を作る"""
    with open(PROVERBS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    explanations = {}
    # 行のパターン: 「1. **七転び八起き** *Nana korobi ya oki* — Fall seven times...」
    pattern = re.compile(r'^\d+\.\s+\*\*([^*]+)\*\*')

    for i, line in enumerate(lines):
        match = pattern.match(line.strip())
        if match:
            japanese = match.group(1).strip()
            # 次の行から説明文（> で始まる行）を探す
            for j in range(i + 1, min(i + 6, len(lines))):
                stripped = lines[j].strip()
                if stripped.startswith(">"):
                    explanations[japanese] = stripped[1:].strip()
                    break

    return explanations


def parse_proverbs():
    """generate_ronin_cards.py の proverbs リストを解析して day番号 → 諺データの辞書を返す

    このファイルが画像ファイル(dayXX.png)と1対1で対応している正しいマッピング。
    """
    with open(CARDS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Python辞書の各行を正規表現で抽出する
    # 例: {"day":  1, "jp": "一期一会", "roma": "Ichi go ichi e", "en": "..."}
    pattern = re.compile(
        r'\{"day":\s*(\d+),\s*"jp":\s*"([^"]+)",\s*"roma":\s*"([^"]+)",\s*"en":\s*"([^"]+)"\}'
    )

    # 説明文は ronin_words_proverbs_100.md から日本語テキストで引く
    explanations = parse_explanations()

    proverbs = {}
    for match in pattern.finditer(content):
        day      = int(match.group(1))
        japanese = match.group(2).strip()
        romanji  = match.group(3).strip()
        english  = match.group(4).strip()

        proverbs[day] = {
            "japanese":    japanese,
            "romanji":     romanji,
            "english":     english,
            "explanation": explanations.get(japanese, ""),  # 一致する説明文がなければ空欄
        }

    return proverbs


# =============================
# 記事本文の組み立て
# =============================
def build_post_body(proverb, image_url):
    """記事の本文をSubstack用のProseMirror JSON形式で組み立てる"""
    # Substack の draft_body は ProseMirror JSON（エディタの内部形式）を文字列で渡す必要がある
    # type="image" のノードに src/alt を設定すると画像として正しく表示される
    japanese    = proverb["japanese"]
    romanji     = proverb["romanji"]
    english     = proverb["english"]
    explanation = proverb["explanation"]

    doc = {
        "type": "doc",
        "content": [
            # 書道カード画像
            {
                "type": "image",
                "attrs": {
                    "src":   image_url,
                    "alt":   japanese,
                    "title": japanese,
                }
            },
            # 漢字（太字）＋ 読み方（斜体）
            {
                "type": "paragraph",
                "attrs": {"textAlign": None},
                "content": [
                    {"type": "text", "marks": [{"type": "strong"}], "text": japanese},
                    {"type": "hardBreak"},
                    {"type": "text", "marks": [{"type": "em"}],     "text": romanji},
                ]
            },
            # 英語訳
            {
                "type": "paragraph",
                "attrs": {"textAlign": None},
                "content": [{"type": "text", "text": english}]
            },
            # 説明文
            {
                "type": "paragraph",
                "attrs": {"textAlign": None},
                "content": [{"type": "text", "text": explanation}]
            },
            # 署名
            {
                "type": "paragraph",
                "attrs": {"textAlign": None},
                "content": [
                    {"type": "text", "marks": [{"type": "em"}], "text": "— RoninWords"}
                ]
            },
        ]
    }
    # ProseMirror JSON は文字列として渡す
    return json.dumps(doc, ensure_ascii=False)


# =============================
# curl_cffi で Substack に投稿
# =============================
def upload_image_to_substack(session, image_path):
    """ローカル画像ファイルをSubstack CDNにアップロードしてCDN URLを返す

    同じChrome偽装セッションを使うのでCloudflareに弾かれない。
    Substack の /api/v1/image は multipart ではなく data URI（Base64）形式のJSONを受け付ける。
    """
    print(f"  画像をSubstack CDNにアップロード中: {image_path}", flush=True)

    # 画像ファイルをバイナリで読み込んでBase64文字列に変換する
    with open(image_path, "rb") as f:
        image_data = f.read()

    # "data:image/png;base64,<データ>" という形式に組み立てる
    image_b64 = base64.b64encode(image_data).decode()
    data_uri   = f"data:image/png;base64,{image_b64}"

    # JSONボディとして送る（multipartは不要）
    resp = session.post(
        "https://substack.com/api/v1/image",
        json={"image": data_uri},
    )

    print(f"  画像アップロードレスポンス: {resp.status_code}", flush=True)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"画像アップロード失敗 [{resp.status_code}]: {resp.text[:500]}"
        )

    cdn_url = resp.json().get("url")
    if not cdn_url:
        raise RuntimeError(f"画像アップロード後にURLが取得できませんでした: {resp.text[:500]}")

    print(f"  CDN URL取得: {cdn_url}", flush=True)
    return cdn_url


def build_article_url(slug):
    """Substack記事のslugから公開URLを組み立てる。slugが無ければNoneを返す
    （CTAのテーマ連動で、この記事にリンクできるかどうかの判定に使う）。"""
    if not slug:
        return None
    return f"{PUBLICATION_URL}/p/{slug}"


def create_and_publish_post(proverb, image_path, session=None):
    """curl_cffi（Chrome TLSフィンガープリント偽装）でSubstackに記事を作成・公開する

    curl_cffi は requests ライクなAPIで curl-impersonate をバックエンドに使う。
    impersonate="chrome131" でTLSハンドシェイク・HTTP/2フレームをChromeと完全一致させ、
    Cloudflare のフィンガープリント検知を回避する。
    session を渡せば重複チェックで使ったものを再利用する（無ければここで作る）。
    """
    # セッションが渡されなければ新しく作る（archiveチェックで作ったものを使い回せる）
    if session is None:
        session = build_session()

    # 画像をSubstack CDNにアップロードしてCDN URLを取得する
    image_url = upload_image_to_substack(session, image_path)

    title     = f"{proverb['japanese']} — {proverb['english']}"
    body_json = build_post_body(proverb, image_url)

    # =============================
    # Step 1: ドラフトを作成する
    # =============================
    draft_payload = {
        "draft_title":      title,
        "draft_body":       body_json,
        "draft_subtitle":   "",
        "type":             "newsletter",
        "draft_section_id": None,
        "audience":         "everyone",  # 全員（無料）公開
        "draft_bylines":    [{"id": 509075677, "is_guest": False}],
    }

    print(f"  ドラフト作成中...", flush=True)
    draft_resp = session.post(
        f"{PUBLICATION_URL}/api/v1/drafts",
        json=draft_payload,
    )

    print(f"  ドラフト作成レスポンス: {draft_resp.status_code}", flush=True)
    if draft_resp.status_code not in (200, 201):
        raise RuntimeError(
            f"ドラフト作成失敗 [{draft_resp.status_code}]: {draft_resp.text[:500]}"
        )

    post    = draft_resp.json()
    post_id = post["id"]
    slug    = post.get("slug")
    print(f"  ドラフトID: {post_id}", flush=True)

    # =============================
    # Step 2: ドラフトを公開する
    # =============================
    print(f"  公開処理中...", flush=True)
    publish_resp = session.post(
        f"{PUBLICATION_URL}/api/v1/drafts/{post_id}/publish",
        json={"audience": "everyone"},
    )

    print(f"  公開レスポンス: {publish_resp.status_code}", flush=True)
    if publish_resp.status_code not in (200, 201):
        raise RuntimeError(
            f"公開失敗 [{publish_resp.status_code}]: {publish_resp.text[:500]}"
        )

    return post_id, slug


# =============================
# メイン処理
# =============================
def main():
    progress = load_progress()

    if progress.get("next_day", 1) > MAX_DAY:
        print(f"全{MAX_DAY}日分の投稿が完了しています。")
        return

    # 諺データを読み込む
    proverbs = parse_proverbs()

    # Substackの公開記事一覧（確実な情報源）から、すでに公開済みの諺を取得する
    # progress.jsonが自動同期cron等で巻き戻っても、ここで二重投稿を防ぐ最終防壁
    # 取得に失敗したら「確認できないので投稿を見送る」（重複を出すより安全側に倒す）
    session = build_session()
    try:
        live_posted = fetch_published_japanese(session)
        print(f"  ライブ公開済みの諺: {len(live_posted)}件 を確認", flush=True)
    except Exception as error:
        print(f"公開記事一覧を確認できなかったため、今回は投稿を見送ります: {error}", flush=True)
        return

    # next_day から順に見て、まだ投稿していない諺の最初のday番号を探す
    # （データ重複・progress.json巻き戻り・ライブ公開済みのいずれも飛ばして二重投稿を防ぐ）
    day = find_next_unposted_day(progress, proverbs, also_posted=live_posted)
    if day is None:
        print("まだ投稿していない諺がありません（全て投稿済み）。スキップします。")
        return

    proverb    = proverbs[day]
    image_path = os.path.join(IMAGES_DIR, f"day{day:02d}.png")

    if not os.path.exists(image_path):
        raise RuntimeError(f"画像ファイルが見つかりません: {image_path}")

    # すでに同じdayがhistoryに存在する場合は重複投稿を防ぐためスキップする
    # （runnerがシャットダウンしてprogress.jsonが巻き戻った場合の二重投稿対策）
    already_posted = any(h["day"] == day for h in progress.get("history", []))
    if already_posted:
        print(f"[Day {day}] はすでに投稿済みのためスキップします。", flush=True)
        return

    # 今日（日本時間）すでに1本投稿していれば何もしない（毎日きっちり1本にするためのガード）
    # ワークフローを1日に何回トリガーしても、最初の1回だけ投稿して残りはここでスキップされる
    today_jst = datetime.now(JST).strftime("%Y/%m/%d")  # 日本時間での今日の日付（例: 2026/06/11）
    posted_today = any(h.get("date", "").split(" ")[0] == today_jst for h in progress.get("history", []))
    if posted_today:
        print(f"本日（{today_jst} JST）はすでに投稿済みのためスキップします。", flush=True)
        return

    print(f"[Day {day}] 投稿開始: {proverb['japanese']}", flush=True)

    # 記事を作成して公開する（curl_cffi経由・画像はCDNにアップロード）
    title = f"{proverb['japanese']} — {proverb['english']}"
    print(f"  記事を公開中: {title}", flush=True)
    post_id, slug = create_and_publish_post(proverb, image_path, session=session)
    print(f"  公開完了! Post ID: {post_id}", flush=True)

    # 進捗を保存する（次回は day+1 から投稿する）
    now = datetime.now(JST).strftime("%Y/%m/%d %H:%M")  # 記録は日本時間で残す（当日ガードと日付を揃えるため）
    progress["history"].append({
        "date":    now,
        "day":     day,
        "post_id": post_id,
        "title":   title,
        "url":     build_article_url(slug),
    })
    progress["next_day"] = day + 1
    save_progress(progress)

    print(f"[Day {day}] 完了。次回は Day {day + 1} を投稿します。", flush=True)


if __name__ == "__main__":
    main()
