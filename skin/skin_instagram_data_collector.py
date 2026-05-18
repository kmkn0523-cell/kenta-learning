# skin_instagram_data_collector.py
# skin Instagram用 データ収集スクリプト
# 使い方: python3 skin/skin_instagram_data_collector.py
#         python3 skin/skin_instagram_data_collector.py --backfill 30   （過去30日遡り）

import os                    # 環境変数を扱う道具
import sys                   # コマンドライン引数を扱う道具
import json                  # JSONを読み書きする道具
import argparse              # コマンドライン引数のパース
from pathlib import Path     # ファイルパスを扱う道具
from datetime import datetime, timezone, timedelta  # 日時を扱う道具
import requests              # インターネット通信用の道具
from dotenv import load_dotenv  # .envからAPIキーを読み込む道具

# .envファイルを読み込む（APIキーは安全に管理）
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Instagram Graph API用のキー
ACCESS_TOKEN = os.getenv("SKIN_INSTAGRAM_ACCESS_TOKEN")
USER_ID      = os.getenv("SKIN_INSTAGRAM_USER_ID")

# ファイルパス（プロジェクトルートからの相対が安定）
_DIR           = Path(__file__).resolve().parent
ANALYTICS_FILE = _DIR / "skin_instagram_analytics.json"

# APIリクエストのタイムアウト時間（秒）
API_TIMEOUT = 15


def calculate_save_rate(saved: int, impressions: int) -> float:
    """
    保存率（％）を計算する。
    - インプレッションがゼロのときは 0.0 を返す（ゼロ除算回避）
    - 小数第2位で四捨五入する
    """
    if impressions <= 0:
        return 0.0
    rate = (saved / impressions) * 100.0
    return round(rate, 2)
