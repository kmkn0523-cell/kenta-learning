# skin Instagram データ収集スクリプトの単体テスト
# 使い方: pytest skin/tests/test_skin_instagram_data_collector.py -v

import sys
from pathlib import Path
# skin ディレクトリをimportパスに追加（プロジェクトルートからの実行用）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skin_instagram_data_collector import calculate_save_rate


def test_calculate_save_rate_normal():
    """通常ケース: 保存数100/インプレッション5000 = 2.0%"""
    rate = calculate_save_rate(saved=100, impressions=5000)
    assert rate == 2.0


def test_calculate_save_rate_zero_impressions():
    """インプレッションがゼロのときはゼロ除算を避けて0.0を返す"""
    rate = calculate_save_rate(saved=10, impressions=0)
    assert rate == 0.0


def test_calculate_save_rate_zero_saved():
    """保存数がゼロのときは0.0を返す"""
    rate = calculate_save_rate(saved=0, impressions=1000)
    assert rate == 0.0


def test_calculate_save_rate_rounding():
    """小数第2位までで丸める（4.16666... → 4.17）"""
    rate = calculate_save_rate(saved=250, impressions=6000)
    assert rate == 4.17
