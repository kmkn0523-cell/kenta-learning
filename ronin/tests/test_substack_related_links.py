# test_substack_related_links.py
# 記事末尾の「関連記事リンク＋購読誘導」組み立ての純粋関数テスト

import json
import os
import sys

# ronin/ を import パスに足す（tests/ から1つ上の階層）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import substack_related_links as srl


# テスト用のカタログ（古い順に並んでいる想定）
CATALOG = [
    {"title": "Old Discipline Post", "url": "https://x.test/p/old-discipline", "theme": "1"},
    {"title": "Mastery Post", "url": "https://x.test/p/mastery", "theme": "5"},
    {"title": "New Discipline Post", "url": "https://x.test/p/new-discipline", "theme": "1"},
    {"title": "Latest Purpose Post", "url": "https://x.test/p/purpose", "theme": "6"},
]


def test_同じテーマの記事を新しい順に選ぶ():
    # discipline（テーマ1）の記事本文 → テーマ1の記事が新しい順で先頭に来る
    related = srl.pick_related_articles("Now", "discipline habit routine", CATALOG, max_links=2)
    assert related[0]["title"] == "New Discipline Post"
    assert related[1]["title"] == "Old Discipline Post"


def test_自分自身は除外される():
    related = srl.pick_related_articles("New Discipline Post", "discipline habit", CATALOG)
    titles = [a["title"] for a in related]
    assert "New Discipline Post" not in titles


def test_テーマ一致が足りなければ最新記事で埋める():
    # テーマ6は1件しかない → 残りは最新記事から補充され、指定件数に達する
    related = srl.pick_related_articles("Now", "purpose meaning why", CATALOG, max_links=3)
    assert len(related) == 3
    assert related[0]["title"] == "Latest Purpose Post"


def test_リンクノードにUTMパラメータが付く():
    nodes = srl.build_related_nodes([CATALOG[0]])
    # 見出し・リンク1件・購読誘導文の3ノード
    assert len(nodes) == 3
    link_mark = nodes[1]["content"][1]["marks"][0]
    assert link_mark["type"] == "link"
    assert "utm_source=substack" in link_mark["attrs"]["href"]


def test_関連記事ゼロなら何も足さない():
    assert srl.build_related_nodes([]) == []


def test_カタログが無くても例外を出さない():
    nodes = srl.build_footer_nodes("t", "text", catalog_file="/no/such/file.json")
    assert nodes == []


def test_全ノードがJSONとして直列化できる():
    nodes = srl.build_related_nodes(srl.pick_related_articles("Now", "mastery skill", CATALOG))
    json.dumps(nodes)  # 例外が出なければOK
