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


def load_analytics() -> dict:
    """analyticsファイルを読み込む（なければ空の辞書を返す）"""
    if not ANALYTICS_FILE.exists():
        return {"posts": {}, "follower_history": []}
    try:
        return json.loads(ANALYTICS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"posts": {}, "follower_history": []}


def save_analytics(data: dict) -> None:
    """analyticsファイルに書き込む（インデント2、UTF-8）"""
    ANALYTICS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def fetch_recent_posts(limit: int = 30) -> list:
    """
    最新の投稿 limit 件を取得する（ID と timestamp のみ）。
    取得失敗時は空リストを返す。
    """
    if not ACCESS_TOKEN or not USER_ID:
        print("❌ SKIN_INSTAGRAM_ACCESS_TOKEN または SKIN_INSTAGRAM_USER_ID が未設定")
        return []

    url = f"https://graph.facebook.com/v19.0/{USER_ID}/media"
    params = {
        "fields":       "id,timestamp,caption",
        "limit":        limit,
        "access_token": ACCESS_TOKEN,
    }
    try:
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"⚠️ 投稿一覧取得エラー: {e}")
        return []


def fetch_post_insights(post_id: str) -> dict:
    """
    1投稿の insights（saved, impressions, reach 等）を取得する。
    取得失敗時は空辞書を返す。
    """
    url = f"https://graph.facebook.com/v19.0/{post_id}/insights"
    params = {
        "metric":       "saved,impressions,reach",
        "access_token": ACCESS_TOKEN,
    }
    try:
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        data = response.json()
        result = {}
        for item in data.get("data", []):
            name   = item.get("name")
            values = item.get("values", [])
            if values:
                result[name] = values[0].get("value", 0)
        return result
    except Exception as e:
        print(f"⚠️ insights取得エラー ({post_id}): {e}")
        return {}


def fetch_account_followers() -> int:
    """アカウントの現在フォロワー数を取得する（失敗時は -1）"""
    url = f"https://graph.facebook.com/v19.0/{USER_ID}"
    params = {
        "fields":       "followers_count",
        "access_token": ACCESS_TOKEN,
    }
    try:
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        data = response.json()
        return int(data.get("followers_count", -1))
    except Exception as e:
        print(f"⚠️ フォロワー数取得エラー: {e}")
        return -1


def collect_once(backfill_days: int = 0) -> None:
    """
    投稿のinsightsとフォロワー数を取得して analytics に追記する。
    backfill_days が指定された場合、その日数前までの投稿を遡って取得する。
    """
    analytics = load_analytics()
    posts = fetch_recent_posts(limit=50 if backfill_days > 0 else 10)

    if backfill_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=backfill_days)
        posts = [p for p in posts if datetime.fromisoformat(p["timestamp"].replace("+0000", "+00:00")) >= cutoff]

    today_iso = datetime.now(timezone.utc).date().isoformat()
    updated_count = 0

    for post in posts:
        post_id   = post["id"]
        insights  = fetch_post_insights(post_id)
        if not insights:
            continue

        saved       = insights.get("saved", 0)
        impressions = insights.get("impressions", 0)
        reach       = insights.get("reach", 0)
        save_rate   = calculate_save_rate(saved, impressions)

        # 投稿ごとに最新値を上書き保存（累積データ）
        analytics["posts"][post_id] = {
            "timestamp":   post["timestamp"],
            "caption":     post.get("caption", "")[:120],
            "saved":       saved,
            "impressions": impressions,
            "reach":       reach,
            "save_rate":   save_rate,
            "last_updated": today_iso,
        }
        updated_count += 1

    # フォロワー数を履歴として記録
    follower_count = fetch_account_followers()
    if follower_count >= 0:
        analytics["follower_history"].append({
            "date":   today_iso,
            "count":  follower_count,
        })

    save_analytics(analytics)
    print(f"✅ 更新完了: 投稿 {updated_count} 件, フォロワー {follower_count} 人")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backfill", type=int, default=0, help="過去N日分を遡って取得")
    args = parser.parse_args()

    print(f"=== skin Instagram データ収集 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")
    if not ACCESS_TOKEN or not USER_ID:
        print("❌ APIキーが未設定。終了します。")
        sys.exit(1)

    collect_once(backfill_days=args.backfill)
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
