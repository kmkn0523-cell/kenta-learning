#!/usr/bin/env python3
# skin_data_collector.py
# skinアカウント用 Threads API データ収集スクリプト
# 使い方: python3 skin/skin_data_collector.py または python3 skin/skin_data_collector.py --dry-run

import json                    # JSONファイルを扱う道具
import os                      # ファイル操作に使う道具
import sys                     # コマンドライン引数を取得する道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime  # 日時を扱う道具
from dotenv import load_dotenv # .envファイルからAPIキーを読み込む道具

# .envファイルを読み込む（APIキーを安全に管理するため）
load_dotenv()

# Threads APIに必要なキーを.envから読み込む
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_USER_ID = os.getenv("THREADS_USER_ID")

# ファイルパスの設定（スクリプトからの相対パスで指定 → GitHub Actionsでも動く）
_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_FILE     = os.path.join(_DIR, "skin_threads_posts.json")   # 投稿テキストデータ
ANALYTICS_FILE = os.path.join(_DIR, "skin_analytics.json")       # 分析データ保存先

# APIリクエストのタイムアウト時間（秒）
API_TIMEOUT = 10


def fetch_threads_data():
    """
    Threads APIからポスト情報を取得する関数
    APIキーが設定されているか確認し、エラーハンドリングを行う
    """

    # APIキーが設定されているか確認する
    if not THREADS_ACCESS_TOKEN:
        print("❌ エラー: THREADS_ACCESS_TOKENが.envに設定されていません")
        return []

    if not THREADS_USER_ID:
        print("❌ エラー: THREADS_USER_IDが.envに設定されていません")
        return []


    try:
        # Threads APIのエンドポイント
        api_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"

        # APIに送るパラメータ（取得したいデータフィールドを指定）
        params = build_fetch_params()

        # APIにリクエストを送る（タイムアウト設定あり）
        response = requests.get(api_url, params=params, timeout=API_TIMEOUT)

        # HTTPステータスコードで結果を判定する
        if response.status_code == 401:
            print("❌ エラー: Threads API認証失敗 (401 Unauthorized)")
            return []
        elif response.status_code != 200:
            print(f"❌ エラー: APIリクエスト失敗 (ステータス: {response.status_code})")
            return []

        # JSON形式のレスポンスを取得する
        api_data = response.json()

        # APIレスポンスにデータが含まれているか確認する
        if "data" not in api_data:
            print("⚠️  警告: APIレスポンスにデータが含まれていません")
            return []

        return api_data.get("data", [])

    except requests.exceptions.Timeout:
        print(f"❌ エラー: APIリクエストがタイムアウトしました（{API_TIMEOUT}秒以上）")
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ エラー: ネットワークエラー {str(e)}")
        return []
    except json.JSONDecodeError:
        print("❌ エラー: APIレスポンスのJSON解析に失敗しました")
        return []


def build_fetch_params():
    """
    Threads APIへ渡すリクエストパラメータを組み立てる純関数。
    limit=100 を付けて過去分の取りこぼしを防ぐ（API上限は100）。
    """
    # APIに要求するパラメータ一式を辞書で返す
    return {
        # 取得したいフィールド（既存と同じ。投稿ID・本文・日時・反応指標）
        "fields": "id,text,timestamp,insights.metric(likes,replies,shares,views)",
        # 認証用のアクセストークン
        "access_token": THREADS_ACCESS_TOKEN,
        # 1ページあたりの取得件数（API上限の100。デフォルト25だと過去分が届かない）
        "limit": 100,
    }


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


def match_day_and_type(posts_data, post_text):
    """投稿テキストを posts_data の投稿パターンと照合し (Day番号, テーマ, 朝夜) を返す純関数。
    threads_a と threads_b の両方を走査する（旧 threads キーは存在しないため全件スキップしていたバグの修正）。
    一致しなければ (None, None, None) を返す。
    """
    # threads_a と threads_b を1つのリストに連結して両方走査する
    all_threads = posts_data.get("threads_a", []) + posts_data.get("threads_b", [])

    # 比較対象テキストの最初の50文字を取り出す（正確な比較用）
    post_text_normalized = post_text[:50].strip()

    # 各投稿パターンを順番にチェックする
    for thread_info in all_threads:
        day_num = thread_info.get("id")            # このパターンのDay番号
        theme_name = thread_info.get("theme", "")  # このパターンのテーマ名
        post_texts = thread_info.get("posts", [])  # このパターンの投稿文リスト

        for index, stored_text in enumerate(post_texts):
            # 保存テキストの最初の50文字を取り出す
            stored_text_normalized = stored_text[:50].strip()

            # 最初の50文字が完全一致したら、その投稿に確定する
            if post_text_normalized == stored_text_normalized:
                # 投稿位置で朝夜を判定する（index 0,1 = 朝 / それ以降 = 夜）
                post_type = "morning" if index <= 1 else "evening"
                return (day_num, theme_name, post_type)

    # どのパターンにも一致しなかった場合
    return (None, None, None)


def identify_day_and_type(post_text):
    """
    投稿テキストをskin_threads_posts.jsonの投稿パターンと照合して
    Day番号とテーマを特定する関数（ファイル読み込み担当・照合は match_day_and_type に委譲）
    """

    try:
        # skin_threads_posts.jsonから投稿パターンを読み込む
        with open(POSTS_FILE, "r", encoding="utf-8") as f:
            posts_data = json.load(f)

        # 読み込んだデータを純関数に渡して照合する
        return match_day_and_type(posts_data, post_text)

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
    APIから取得したポストデータをskin_analytics.jsonに保存する関数
    エンゲージメント計算と日時判定を行ったうえで記録する
    """

    try:
        # 既存のskin_analytics.jsonを読み込む
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
                    metric_name = insight.get("name", "")
                    values = insight.get("values", [])

                    if len(values) > 0:
                        value = values[0].get("value", 0)

                        if metric_name == "likes":
                            likes = value
                        elif metric_name == "replies":
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
                    {"metric": "shares", "values": [{"value": 3}]},
                    {"metric": "views", "values": [{"value": 1200}]}
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
                    {"metric": "shares", "values": [{"value": 2}]},
                    {"metric": "views", "values": [{"value": 980}]}
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
