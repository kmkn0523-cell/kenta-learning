#!/usr/bin/env python3
# skin_account_metrics_collector.py
# skinアカウント用 「アカウント全体」の閲覧数・フォロワー数を毎日記録するスクリプト
# 使い方: python3 skin/skin_account_metrics_collector.py または python3 skin/skin_account_metrics_collector.py --dry-run
#
# skin_data_collector.py が集めているのは「投稿1本ごと」の閲覧数だけで、
# Threadsアプリの「インサイト」画面に出るアカウント全体の閲覧数・フォロワー数の推移は
# どこにも記録が残っていなかった（過去の分析で判明した穴）。
# このスクリプトはその2つを毎日1件ずつ記録し、後で増減の原因分析に使えるようにする。

import json                    # JSONファイルを扱う道具
import os                      # ファイル操作に使う道具
import sys                     # コマンドライン引数を取得する道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime, timedelta, timezone  # 日時を扱う道具
from dotenv import load_dotenv # .envファイルからAPIキーを読み込む道具

# .envファイルを読み込む（APIキーを安全に管理するため）
load_dotenv()

# Threads APIに必要なキーを.envから読み込む
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_USER_ID = os.getenv("THREADS_USER_ID")

# ファイルパスの設定（スクリプトからの相対パスで指定 → GitHub Actionsでも動く）
_DIR = os.path.dirname(os.path.abspath(__file__))
METRICS_FILE = os.path.join(_DIR, "skin_account_metrics.json")  # アカウント全体の指標の保存先

# APIリクエストのタイムアウト時間（秒）
API_TIMEOUT = 10

# 日本時間（JST = UTC+9）を表すタイムゾーン
JST = timezone(timedelta(hours=9))


def compute_jst_yesterday_window(now_jst=None):
    """
    「昨日のJST 0時 〜 今日のJST 0時」のUnixタイムスタンプ範囲と、対象の日付文字列を返す関数。
    views は時系列データなので、この範囲を渡して「昨日1日分の閲覧数」を取得する。
    now_jst を渡すとテストしやすくなる（省略時は現在時刻を使う）。
    """

    # 基準時刻（省略時は現在のJST時刻）
    if now_jst is None:
        now_jst = datetime.now(JST)

    # 今日のJST 0時を求める
    today_start = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)

    # 昨日のJST 0時（今日の0時から24時間引く）
    yesterday_start = today_start - timedelta(days=1)

    # 対象日の日付文字列（この記録が「どの日の分」かを表す）
    date_str = yesterday_start.strftime("%Y-%m-%d")

    # Unixタイムスタンプ（整数秒）に変換して返す
    since_ts = int(yesterday_start.timestamp())
    until_ts = int(today_start.timestamp())

    return since_ts, until_ts, date_str


def fetch_views_total(since_ts, until_ts):
    """
    Threads APIから「指定した期間のアカウント全体の閲覧数合計」を取得する関数。
    views は時系列(day単位)で返ってくるので、範囲内の値を合計する。
    取得に失敗した場合は None を返す。
    """

    # APIキーが設定されているか確認する
    if not THREADS_ACCESS_TOKEN or not THREADS_USER_ID:
        print("❌ エラー: THREADS_ACCESS_TOKEN または THREADS_USER_ID が.envに設定されていません")
        return None

    try:
        # アカウントレベルのインサイトAPIエンドポイント
        api_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_insights"

        params = {
            "metric": "views",
            "since": since_ts,
            "until": until_ts,
            "access_token": THREADS_ACCESS_TOKEN,
        }

        response = requests.get(api_url, params=params, timeout=API_TIMEOUT)

        if response.status_code == 401:
            print("❌ エラー: Threads API認証失敗 (401 Unauthorized)")
            return None
        elif response.status_code != 200:
            print(f"❌ エラー: views取得リクエスト失敗 (ステータス: {response.status_code})")
            return None

        api_data = response.json()

        # レスポンス形式: {"data": [{"name": "views", "period": "day", "values": [{"value": 123, "end_time": "..."}, ...]}]}
        data_list = api_data.get("data", [])
        if not data_list:
            print("⚠️  警告: views のレスポンスにdataが含まれていません")
            return None

        values = data_list[0].get("values", [])

        # 範囲内の全日分を合計する（1日分だけの場合はその値がそのまま合計になる）
        total_views = sum(item.get("value", 0) for item in values)

        return total_views

    except requests.exceptions.Timeout:
        print(f"❌ エラー: views取得リクエストがタイムアウトしました（{API_TIMEOUT}秒以上）")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ エラー: ネットワークエラー {str(e)}")
        return None
    except json.JSONDecodeError:
        print("❌ エラー: views取得レスポンスのJSON解析に失敗しました")
        return None


def fetch_followers_total():
    """
    Threads APIから「現在のフォロワー総数」を取得する関数。
    followers_count は since/until に対応していない「現在の累計値」なので、期間指定なしで呼ぶ。
    取得に失敗した場合は None を返す。
    """

    # APIキーが設定されているか確認する
    if not THREADS_ACCESS_TOKEN or not THREADS_USER_ID:
        print("❌ エラー: THREADS_ACCESS_TOKEN または THREADS_USER_ID が.envに設定されていません")
        return None

    try:
        api_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_insights"

        params = {
            "metric": "followers_count",
            "access_token": THREADS_ACCESS_TOKEN,
        }

        response = requests.get(api_url, params=params, timeout=API_TIMEOUT)

        if response.status_code == 401:
            print("❌ エラー: Threads API認証失敗 (401 Unauthorized)")
            return None
        elif response.status_code != 200:
            print(f"❌ エラー: followers_count取得リクエスト失敗 (ステータス: {response.status_code})")
            return None

        api_data = response.json()

        # レスポンス形式: {"data": [{"name": "followers_count", "total_value": {"value": 123}}]}
        data_list = api_data.get("data", [])
        if not data_list:
            print("⚠️  警告: followers_count のレスポンスにdataが含まれていません")
            return None

        total_value = data_list[0].get("total_value", {})
        followers_total = total_value.get("value")

        return followers_total

    except requests.exceptions.Timeout:
        print(f"❌ エラー: followers_count取得リクエストがタイムアウトしました（{API_TIMEOUT}秒以上）")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ エラー: ネットワークエラー {str(e)}")
        return None
    except json.JSONDecodeError:
        print("❌ エラー: followers_count取得レスポンスのJSON解析に失敗しました")
        return None


def build_metric_record(date_str, views_total, followers_total):
    """
    保存用の1件分のレコード（辞書）を組み立てる純関数。
    値が取得できなかった項目は None のまま記録する（欠損を隠さない）。
    """
    return {
        "date": date_str,
        "views_total": views_total,
        "followers_total": followers_total,
        "collected_at": datetime.now(JST).isoformat(),
    }


def save_metric_record(record):
    """
    skin_account_metrics.json に1件のレコードを追記する関数。
    同じ date が既に記録済みなら上書きする（同日の再実行で重複が増えないようにする）。
    """

    try:
        # 既存ファイルを読み込む（なければ初期化する）
        if os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                metrics = json.load(f)
        else:
            metrics = {"history": []}

        history = metrics.setdefault("history", [])

        # 同じ日付の既存レコードを探す
        existing_index = None
        for index, item in enumerate(history):
            if item.get("date") == record["date"]:
                existing_index = index
                break

        if existing_index is not None:
            # 同日分は上書きする（再実行対策）
            history[existing_index] = record
            print(f"🔁 上書き: {record['date']} の記録を更新しました")
        else:
            # 新しい日付なら追加する
            history.append(record)
            print(f"✅ 追加: {record['date']} の記録を保存しました")

        with open(METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"❌ エラー: 記録の保存に失敗しました: {str(e)}")


def dry_run():
    """
    APIを呼び出さずにテストデータで動作確認する関数
    --dry-runオプション指定時に実行される
    """
    since_ts, until_ts, date_str = compute_jst_yesterday_window()
    record = build_metric_record(date_str, views_total=12345, followers_total=678)
    save_metric_record(record)
    print("✅ ドライラン完了")


def main():
    """
    メイン処理（昨日1日分のアカウント全体閲覧数・現在のフォロワー総数を取得→保存）
    """

    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        print("🧪 ドライラン モード開始...")
        dry_run()
        return

    print("📊 skin アカウント指標の収集開始...")

    since_ts, until_ts, date_str = compute_jst_yesterday_window()

    views_total = fetch_views_total(since_ts, until_ts)
    followers_total = fetch_followers_total()

    if views_total is None and followers_total is None:
        print("⚠️  取得できた指標がありません。保存をスキップします")
        return

    record = build_metric_record(date_str, views_total, followers_total)
    save_metric_record(record)


if __name__ == "__main__":
    main()
