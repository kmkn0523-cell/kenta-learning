# build_substack_catalog.py
# @RoninWords用：Substackの公開記事一覧（アーカイブAPI）から記事カタログを作る
# 使い方: cd ronin && python3 build_substack_catalog.py
#
# なぜ必要か:
#   過去に公開した記事はprogress.jsonにURLが記録されていない（slug取得バグのため）。
#   このスクリプトで「タイトル → 公開URL」のカタログを作り直せば、
#   ronin_threads_action.py のCTAテーマ連動が過去記事にもリンクできるようになる。
#   新しい記事が増えたら再実行すればカタログが最新になる。

import json                               # JSONファイルを扱う道具
import re                                 # HTMLタグを取り除くのに使う道具
from curl_cffi import requests as cf      # ChromeのTLSフィンガープリントを模倣してCloudflare回避

import ronin_theme_classifier             # 記事本文のテーマ分類（CTA連動のマッチングに使う）

# パブリケーション（RoninWordsのSubstack）のURL
PUBLICATION_URL = "https://roninwords.substack.com"

# カタログの保存先（ronin_threads_action.py が読み込む）
CATALOG_FILE = "substack_article_catalog.json"

# テーマ分類の上書きファイル（{記事URL: テーマキー"1"〜"6"} の辞書）
# キーワード分類では諺エッセイの74/92がNoneになるため、
# 人（またはAI）が意味で分類した結果をここに保存しておき、再生成時も必ず優先する
OVERRIDES_FILE = "substack_theme_overrides.json"


def strip_html(html_text):
    """HTMLからタグを取り除いて、ただの文章にする（テーマ分類に使うため）"""
    if not html_text:
        return ""
    return re.sub(r"<[^>]+>", " ", html_text)


def classify_article_theme(post):
    """記事のタイトル・説明・本文冒頭を合わせてテーマ（"1"〜"6"）を判定する。
    タイトルだけだと詩的すぎてキーワードに当たらないため、本文まで見るのがポイント。"""
    parts = [
        post.get("title", ""),
        post.get("subtitle") or "",
        post.get("description") or "",
        strip_html(post.get("body_html"))[:2000],  # 本文は冒頭2000字だけで十分
    ]
    return ronin_theme_classifier.classify_category(" ".join(parts))


def fetch_all_articles():
    """アーカイブAPIを50件ずつめくって、公開済み記事の一覧を全部取ってくる"""
    session = cf.Session(impersonate="chrome131")  # Chromeのふりをする通信セッション
    articles = []
    offset = 0
    while True:
        resp = session.get(
            f"{PUBLICATION_URL}/api/v1/archive?sort=new&limit=50&offset={offset}"
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"アーカイブ取得失敗 [{resp.status_code}]: {resp.text[:200]}"
            )
        batch = resp.json()
        if not batch:
            break  # 空のページが返ってきたら本当に終わり
        for post in batch:
            title = post.get("title", "")
            # canonical_urlが記事の正式な公開URL。無ければslugから組み立てる
            url = post.get("canonical_url")
            if not url and post.get("slug"):
                url = f"{PUBLICATION_URL}/p/{post['slug']}"
            if title and url:
                articles.append({
                    "title": title,
                    "url": url,
                    "theme": classify_article_theme(post),
                    "post_date": post.get("post_date", ""),
                })
        offset += len(batch)
        # 注意: 「len(batch) < limit なら最終ページ」と判定してはいけない。
        # SubstackのアーカイブAPIは最初のページでも50件未満を返すことがある（実測23件）。
        # 空ページが返るまでめくり続けるのが正しい終了条件。
    return articles


def load_theme_overrides():
    """テーマ上書きファイルを読む（無ければ空の辞書を返す）"""
    try:
        with open(OVERRIDES_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main():
    print("Substackアーカイブから記事一覧を取得中...", flush=True)
    articles = fetch_all_articles()
    # 意味ベースの分類（上書きファイル）があればキーワード分類より優先する
    overrides = load_theme_overrides()
    for article in articles:
        if article["url"] in overrides:
            article["theme"] = overrides[article["url"]]
    # 古い記事が先・新しい記事が後の順に並べる
    # （ronin_threads_action.pyはreversed()で新しい記事を優先して探すため）
    articles.sort(key=lambda a: a.get("post_date", ""))
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump({"articles": articles}, f, ensure_ascii=False, indent=2)
    themed = sum(1 for a in articles if a.get("theme"))
    print(f"カタログ保存完了: {CATALOG_FILE}（{len(articles)}記事・テーマ付き{themed}件）")


if __name__ == "__main__":
    main()
