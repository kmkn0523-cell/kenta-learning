# substack_related_links.py
# @RoninWords用：Substack記事の末尾に足す「関連記事リンク＋購読誘導」を組み立てる（純粋関数のみ）
# 狙い: Threadsから来た読者に2〜3記事読んでもらい、購読まで運ぶサイト内回遊をつくる。
# 使う側: substack_auto_post.py / substack_deep_dive_auto_post.py

import json
import os

import ronin_theme_classifier  # 記事テキストのテーマ分類（関連記事のマッチングに使う）

# 記事カタログ（build_substack_catalog.py が生成する全公開記事の一覧）
_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_FILE = os.path.join(_DIR, "substack_article_catalog.json")

# 記事末尾のリンクに付ける計測パラメータ（どの導線が読まれたかを見分ける）
UTM_SUFFIX = "utm_source=substack&utm_medium=related&utm_campaign=article_footer"

# セクションの見出しと購読誘導文（英語・ブランドボイスに合わせる）
SECTION_HEADING = "Keep walking the path"
SUBSCRIBE_LINE = "One teaching like this lands in your inbox every week — free. Subscribe so you never miss one."


def load_catalog_articles(catalog_file=CATALOG_FILE):
    """記事カタログを読んで記事リストを返す（無い/壊れていたら空リスト＝挿入をあきらめるだけ）"""
    try:
        with open(catalog_file, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [a for a in data.get("articles", []) if a.get("title") and a.get("url")]


def pick_related_articles(current_title, article_text, articles, max_links=3):
    """今回の記事に合う関連記事を最大 max_links 件選ぶ。
    ① 同じテーマの記事を新しい順に優先
    ② 足りなければ最新記事で埋める
    自分自身（同タイトル）は除外する。"""
    theme = ronin_theme_classifier.classify_category(article_text or current_title)
    candidates = [a for a in articles if a["title"] != current_title]

    related = []
    if theme:
        # カタログは古い順に並んでいるので reversed() で新しい記事から見る
        for article in reversed(candidates):
            if article.get("theme") == theme:
                related.append(article)
            if len(related) >= max_links:
                return related

    # テーマ一致だけで埋まらなければ、最新記事で残りを埋める（重複は入れない）
    for article in reversed(candidates):
        if article not in related:
            related.append(article)
        if len(related) >= max_links:
            break
    return related


def _link_text_node(text, url):
    """ProseMirrorの「リンク付きテキスト」ノードを作る"""
    tracked_url = f"{url}{'&' if '?' in url else '?'}{UTM_SUFFIX}"
    return {
        "type": "text",
        "marks": [{"type": "link", "attrs": {"href": tracked_url}}],
        "text": text,
    }


def build_related_nodes(related_articles):
    """記事末尾に足すProseMirrorノードのリストを作る。
    関連記事が無ければ空リスト（何も足さない）。"""
    if not related_articles:
        return []

    nodes = [
        # 見出し（太字の1段落。特殊ノードは使わず安全なparagraphだけで組む）
        {
            "type": "paragraph",
            "attrs": {"textAlign": None},
            "content": [
                {"type": "text", "marks": [{"type": "strong"}], "text": f"{SECTION_HEADING}:"}
            ],
        }
    ]

    # 関連記事リンク（1記事1段落・矢印つき）
    for article in related_articles:
        nodes.append({
            "type": "paragraph",
            "attrs": {"textAlign": None},
            "content": [
                {"type": "text", "text": "→ "},
                _link_text_node(article["title"], article["url"]),
            ],
        })

    # 購読誘導文（斜体）
    nodes.append({
        "type": "paragraph",
        "attrs": {"textAlign": None},
        "content": [
            {"type": "text", "marks": [{"type": "em"}], "text": SUBSCRIBE_LINE}
        ],
    })
    return nodes


def build_footer_nodes(current_title, article_text, catalog_file=CATALOG_FILE, max_links=3):
    """「カタログ読込→関連記事選択→ノード組み立て」を一発でやる入口関数。
    どこかで失敗しても空リストを返して投稿自体は止めない。"""
    try:
        articles = load_catalog_articles(catalog_file)
        related = pick_related_articles(current_title, article_text, articles, max_links=max_links)
        return build_related_nodes(related)
    except Exception:
        return []
