#!/usr/bin/env python3
# ronin_data_collector.py
# @RoninWords アカウント用 Threads API データ収集スクリプト
# 使い方: python3 ronin/ronin_data_collector.py または python3 ronin/ronin_data_collector.py --dry-run

import json                    # JSONファイルを扱う道具
import os                      # ファイル操作に使う道具
import sys                     # コマンドライン引数を取得する道具
import time                    # 待ち時間（リトライの間隔）に使う道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime  # 日時を扱う道具
from dotenv import load_dotenv # .envファイルからAPIキーを読み込む道具

# .envファイルを読み込む（APIキーを安全に管理するため）
load_dotenv()

# Threads APIに必要なキーを.envから読み込む
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_BUSINESS_ACCOUNT_ID_RONIN = os.getenv("THREADS_BUSINESS_ACCOUNT_ID_RONIN")

# ファイルパスの設定（スクリプトからの相対パスで指定 → GitHub Actionsでも動く）
_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_FILE     = os.path.join(_DIR, "threads_posts.json")       # 投稿テキストデータ
ANALYTICS_FILE = os.path.join(_DIR, "ronin_analytics.json")     # 分析データ保存先

# APIリクエストのタイムアウト時間（秒）— 混雑時に10秒では足りないことがあるため20秒に延長
API_TIMEOUT = 20
# タイムアウトやネットワークエラーのときに再挑戦する回数（一瞬の遅延で失敗しないようにするため）
API_MAX_RETRIES = 3
# 再挑戦するまでの待ち時間（秒）。回を追うごとに長くする（2秒→4秒→6秒…）
API_RETRY_WAIT_SECONDS = 2


def fetch_threads_data():
    """
    Threads APIからポスト情報を取得する関数
    APIキーが設定されているか確認し、エラーハンドリングを行う
    """

    # APIキーが設定されているか確認する（無ければ異常終了させてワークフローを赤くする）
    if not THREADS_ACCESS_TOKEN:
        print("❌ エラー: THREADS_ACCESS_TOKENが.envに設定されていません")
        sys.exit(1)

    if not THREADS_BUSINESS_ACCOUNT_ID_RONIN:
        print("❌ エラー: THREADS_BUSINESS_ACCOUNT_ID_RONINが.envに設定されていません")
        sys.exit(1)

    # Threads APIのエンドポイント
    api_url = f"https://graph.threads.net/v1.0/{THREADS_BUSINESS_ACCOUNT_ID_RONIN}/threads"

    # APIに送るパラメータ（取得したいデータフィールドを指定）
    # コメント数のメトリクス名は "comments" ではなく "replies"（API有効値: clicks/likes/quotes/replies/reposts/shares/views）
    # limit=100 を付けて過去分の取りこぼしを防ぐ（API上限100・デフォルト25）
    params = {
        "fields": "id,text,timestamp,insights.metric(likes,replies,shares,views)",
        "access_token": THREADS_ACCESS_TOKEN,
        "limit": 100,
    }

    # タイムアウトやネットワークエラーのときは、少し待ってから最大 API_MAX_RETRIES 回まで再挑戦する
    # （一瞬のAPI遅延だけでワークフローが赤くなってメールが飛ぶのを防ぐため）
    for attempt in range(1, API_MAX_RETRIES + 1):
        try:
            # APIにリクエストを送る（タイムアウト設定あり）
            response = requests.get(api_url, params=params, timeout=API_TIMEOUT)

            # HTTPステータスコードで結果を判定する（異常時は異常終了させてワークフローを赤くする）
            # 認証失敗やデータ不正は再挑戦しても直らないので、すぐに終了する
            if response.status_code == 401:
                print("❌ エラー: Threads API認証失敗 (401 Unauthorized)")
                sys.exit(1)
            elif response.status_code != 200:
                print(f"❌ エラー: APIリクエスト失敗 (ステータス: {response.status_code})")
                sys.exit(1)

            # JSON形式のレスポンスを取得する
            api_data = response.json()

            # APIレスポンスにデータが含まれているか確認する
            if "data" not in api_data:
                print("⚠️  警告: APIレスポンスにデータが含まれていません")
                return []

            return api_data.get("data", [])

        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as network_error:
            # タイムアウト・ネットワークエラーは一時的なことが多いので、待ってから再挑戦する
            # タイムアウトかどうかでメッセージを分かりやすく出し分ける
            if isinstance(network_error, requests.exceptions.Timeout):
                reason = f"APIリクエストがタイムアウトしました（{API_TIMEOUT}秒以上）"
            else:
                reason = f"ネットワークエラー {str(network_error)}"

            # まだ再挑戦できる回数が残っているなら、待ってからやり直す
            if attempt < API_MAX_RETRIES:
                wait_seconds = API_RETRY_WAIT_SECONDS * attempt  # 2秒→4秒→… と少しずつ長く待つ
                print(f"⏳ {reason}（{attempt}/{API_MAX_RETRIES}回目）→ {wait_seconds}秒待って再挑戦します")
                time.sleep(wait_seconds)
                continue

            # 最後の挑戦でも失敗したら、従来どおり異常終了させてワークフローを赤くする
            print(f"❌ エラー: {reason}（{API_MAX_RETRIES}回試して全て失敗）")
            sys.exit(1)

        except json.JSONDecodeError:
            # レスポンスがJSONとして壊れている場合は再挑戦しても直らないので、すぐに終了する
            print("❌ エラー: APIレスポンスのJSON解析に失敗しました")
            sys.exit(1)


def calculate_engagement_rate(likes, comments, shares, views):
    """
    いいね・コメント・シェア・閲覧数からエンゲージメント率(%)を計算する関数
    エンゲージメント率 = (いいね + コメント + シェア) ÷ 閲覧数 × 100
    閲覧数が0の場合は0を返す（ゼロ除算を防ぐため）
    """

    # 閲覧数が0または未取得の場合はエンゲージメント率を計算できない
    if not views or views <= 0:
        return 0.0

    # エンゲージメント率(%) = 反応の合計 ÷ 閲覧数 × 100
    rate = (likes + comments + shares) / views * 100

    # 小数第2位まで四捨五入して返す
    return round(rate, 2)


def identify_day_and_type(post_text):
    """
    投稿テキストを ronin/threads_posts.json の投稿パターンと照合して
    Day番号と朝夜（morning/evening）を特定する関数。
    roninの構造は {day, morning, evening, ...} なので、朝と夜の本文それぞれと照合する。
    返り値: (Day番号, タイプ=朝夜, post_type=朝夜)。一致しなければ (None, None, None)。
    """

    try:
        # ronin/threads_posts.jsonから投稿パターンを読み込む
        with open(POSTS_FILE, "r", encoding="utf-8") as f:
            posts_data = json.load(f)

        # 比較対象テキストの最初の50文字を取り出す（正確な比較用）
        post_text_normalized = post_text[:50].strip()

        # posts リスト（1日ぶんのパターン）を順番にチェックする
        for day_pattern in posts_data.get("posts", []):
            day_num = day_pattern.get("day")  # この日のDay番号

            # 朝（morning）と夜（evening）の2投稿それぞれと照合する
            for time_type in ("morning", "evening"):
                stored_text = day_pattern.get(time_type, "")
                stored_text_normalized = stored_text[:50].strip()

                # 最初の50文字が完全一致したら、その投稿に確定する
                if post_text_normalized and post_text_normalized == stored_text_normalized:
                    return (day_num, time_type, time_type)

        # どのパターンにも一致しなかった場合
        return (None, None, None)

    except FileNotFoundError:
        print(f"⚠️  警告: {POSTS_FILE}が見つかりません")
        return (None, None, None)
    except json.JSONDecodeError:
        print(f"⚠️  警告: {POSTS_FILE}のJSON解析に失敗しました")
        return (None, None, None)
    except Exception as e:
        print(f"⚠️  警告: identify_day_and_type実行中にエラーが発生しました: {str(e)}")
        return (None, None, None)


def save_analytics(posts_data):
    """
    APIから取得したポストデータをronin_analytics.jsonに保存する関数
    エンゲージメント計算と日時判定を行ったうえで記録する
    """

    try:
        # 既存のronin_analytics.jsonを読み込む
        if os.path.exists(ANALYTICS_FILE):
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
                analytics = json.load(f)
        else:
            # ファイルがなければ初期化する
            analytics = {
                "last_updated": None,
                "posts_history": []
            }

        # APIから取得した各ポストを処理する
        for post in posts_data:
            try:
                # ポストIDとテキストを取得する
                post_id = post.get("id")
                post_text = post.get("text", "")
                posted_at = post.get("timestamp", "")

                # insightsからいいね・コメント・シェア数を抽出する
                insights_data = post.get("insights", {}).get("data", [])

                likes = 0
                comments = 0
                shares = 0
                views = 0

                # insightsの各メトリクスを解析する
                for insight in insights_data:
                    metric_name = insight.get("name", "")   # APIのキーは "metric" ではなく "name"
                    values = insight.get("values", [])

                    if len(values) > 0:
                        value = values[0].get("value", 0)

                        if metric_name == "likes":
                            likes = value
                        elif metric_name == "replies":   # コメント数は "replies" という名前で届く
                            comments = value
                        elif metric_name == "shares":
                            shares = value
                        elif metric_name == "views":
                            views = value

                # エンゲージメント率を計算する（閲覧数ベース）
                engagement_rate = calculate_engagement_rate(likes, comments, shares, views)

                # 投稿テキストから日付とタイプを特定する
                day, theme, post_type = identify_day_and_type(post_text)

                # 特定に失敗した場合はスキップする
                if day is None:
                    print(f"⚠️  警告: ポスト({post_id})の日付特定に失敗しました。スキップします。")
                    continue

                # ポストレコードを作成する
                post_record = {
                    "day": day,
                    "type": theme,
                    "post_id": post_id,
                    "posted_at": posted_at,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "views": views,
                    "engagement_rate": engagement_rate
                }

                # 重複チェック（同じ post_id が既に存在するか確認）
                existing_ids = [p['post_id'] for p in analytics['posts_history']]
                if post_record['post_id'] in existing_ids:
                    print(f"⏭️  スキップ: post_id {post_record['post_id']} は既に記録済みです")
                    continue

                # posts_historyに追加する
                analytics["posts_history"].append(post_record)

            except Exception as e:
                print(f"⚠️  警告: ポスト処理中にエラーが発生しました: {str(e)}")
                continue

        # 最終更新時刻を記録する（ISO 8601形式）
        now_iso = datetime.now().isoformat()
        analytics["last_updated"] = now_iso

        # JSONファイルに保存する
        with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
            json.dump(analytics, f, ensure_ascii=False, indent=2)

        print(f"✅ データ保存完了: {len(posts_data)}件のポストを処理しました")

    except Exception as e:
        print(f"❌ エラー: analyticsの保存に失敗しました: {str(e)}")


def dry_run():
    """
    APIを呼び出さずにテストデータで動作確認する関数
    --dry-runオプション指定時に実行される
    """

    # テスト用のダミーポストデータを作成する（実際のデータベースから取得したテキストを使用）
    test_posts = [
        {
            "id": "test_post_001",
            "text": "肌荒れが治らない人、これ全員やってます。\n\n□ 甘い飲み物を毎日飲んでる\n□ 就寝が深夜0時以降\n□ パン・麺が毎日の主食\n□ ストレスで食いしばり癖がある\n□ 便秘または下痢がち\n\n何個当てはまりましたか？\n\n3個以上なら、スキンケアより先に変えるべきことがあります。",
            "timestamp": "2026-05-07T07:30:00+09:00",
            "insights": {
                "data": [
                    {"metric": "likes", "values": [{"value": 45}]},
                    {"metric": "comments", "values": [{"value": 12}]},
                    {"metric": "shares", "values": [{"value": 3}]}
                ]
            }
        },
        {
            "id": "test_post_002",
            "text": "3個以上当てはまった人へ。\n\nそれらは全部「腸の炎症」を引き起こす習慣です。\n\n腸が荒れる\n→ 有害物質が血液に漏れ出す\n→ 全身で炎症が起きる\n→ 肌に出る",
            "timestamp": "2026-05-07T22:30:00+09:00",
            "insights": {
                "data": [
                    {"metric": "likes", "values": [{"value": 52}]},
                    {"metric": "comments", "values": [{"value": 15}]},
                    {"metric": "shares", "values": [{"value": 2}]}
                ]
            }
        }
    ]

    # テストデータを処理して保存する
    save_analytics(test_posts)

    print("✅ ドライラン完了")


def main():
    """
    メイン処理（APIからデータ取得→分析→保存）
    """

    # コマンドライン引数を確認する
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        # --dry-runオプションが指定されている場合
        print("🧪 ドライラン モード開始...")
        dry_run()
    else:
        # 通常モード：APIからデータ取得→分析→保存
        print("📊 Threads API データ収集開始...")
        posts = fetch_threads_data()

        if posts:
            save_analytics(posts)
        else:
            print("⚠️  取得できるポストがありません")


if __name__ == "__main__":
    main()
