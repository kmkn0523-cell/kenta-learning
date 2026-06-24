"""iphone_price_watcher の価格抽出ロジックのテスト。

ネット接続やブラウザは使わず、テキストから最高買取価格を取り出す部分だけを確認する。
"""
from price_watch.iphone_price_watcher import (
    parse_prices,
    parse_max_price,
    parse_list_price,
    format_vs_list_price,
    short_vs_list,
)


def test_対象行の店舗価格をすべてリストで返す():
    # 店舗価格3つを順に返す。差額(+1,000円)や定価(¥)は店舗価格ではないので除外
    model = "iPhone 17 Pro Max 512GB シルバー"
    text = "228,000 円 (+1,000円) 230,000 円 229,000 円 定価: ¥229,800"
    assert parse_prices(model, text) == [228000, 230000, 229000]


def test_色違いディープブルーは除外する():
    # 機種・容量は合うが色がシルバーでないので対象外
    model = "iPhone 17 Pro Max 512GB ディープブルー"
    text = "231,000 円"
    assert parse_prices(model, text) == []
    assert parse_max_price(model, text) is None
    assert parse_list_price(model, text) is None


def test_定価差を短く表す():
    assert short_vs_list(210000, 229800) == "定価-19,800"
    assert short_vs_list(230000, None) == "定価不明"


def test_買取が定価ぴったりなら同額表記():
    assert short_vs_list(229800, 229800) == "定価ぴったり"
    assert format_vs_list_price(229800, 229800) == "定価 ¥229,800 と同額"


def test_対象機種なら店舗価格の最高値を返す():
    # 店舗価格3つ（円の前に空白あり）。差額(+1,000円)や定価(¥)は最大値に影響しない
    model = "iPhone 17 Pro Max 512GB シルバー"
    text = "228,000 円 (+1,000円) 230,000 円 (+1,000円) 229,000 円 定価: ¥229,800"
    assert parse_max_price(model, text) == 230000


def test_無印ProはMaxではないので除外する():
    model = "iPhone 17 Pro 512GB シルバー"
    text = "215,000 円"
    assert parse_max_price(model, text) is None


def test_容量違い256GBは除外する():
    model = "iPhone 17 Pro Max 256GB シルバー"
    text = "200,000 円"
    assert parse_max_price(model, text) is None


def test_価格が無い行はNoneを返す():
    model = "iPhone 17 Pro Max 512GB シルバー"
    text = "在庫切れ"
    assert parse_max_price(model, text) is None


def test_定価のみで店舗価格が無ければNone():
    # ¥ 記号の定価は店舗価格として拾わない
    model = "iPhone 17 Pro Max 512GB シルバー"
    text = "定価: ¥229,800"
    assert parse_max_price(model, text) is None


def test_定価を円記号付きで取り出す():
    model = "iPhone 17 Pro Max 512GB シルバー"
    text = "228,000 円 (+1,000円) 230,000 円 定価: ¥229,800"
    assert parse_list_price(model, text) == 229800


def test_対象外機種は定価を取らない():
    model = "iPhone 17 Pro 512GB シルバー"
    text = "定価: ¥219,800"
    assert parse_list_price(model, text) is None


def test_定価が無ければNone():
    model = "iPhone 17 Pro Max 512GB シルバー"
    text = "230,000 円"
    assert parse_list_price(model, text) is None


def test_定価より安い買取はマイナス表記():
    assert format_vs_list_price(230000, 229800) == "定価 ¥229,800 から +200円"
    assert format_vs_list_price(210000, 229800) == "定価 ¥229,800 から -19,800円"


def test_定価不明なら不明と返す():
    assert format_vs_list_price(230000, None) == "定価: 不明"
