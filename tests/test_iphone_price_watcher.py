"""iphone_price_watcher の価格抽出ロジックのテスト。

ネット接続やブラウザは使わず、テキストから最高買取価格を取り出す部分だけを確認する。
"""
from price_watch.iphone_price_watcher import parse_max_price


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
