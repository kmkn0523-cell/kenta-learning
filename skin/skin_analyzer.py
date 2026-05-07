#!/usr/bin/env python3
# skin_analyzer.py
# skinアカウント用 Threads分析スクリプト
# 使い方: python3 skin/skin_analyzer.py
# 20日以上のデータが溜まった後、パターン別の成績を分析する

import json                    # JSONファイルを扱う道具
import os                      # ファイル操作に使う道具
from datetime import datetime  # 日時を扱う道具
from collections import defaultdict  # グループ分けを簡単にする道具

# ファイルパスの設定
ANALYTICS_FILE = "/home/kenta_kamijyo/skin/skin_analytics.json"


def load_analytics():
    """
    skin_analytics.jsonを読み込む関数
    ファイルが見つからない場合は空の辞書を返す
    """

    # ファイルが存在するか確認する
    if not os.path.exists(ANALYTICS_FILE):
        print(f"❌ エラー: {ANALYTICS_FILE}が見つかりません")
        return {}

    try:
        # JSONファイルを読み込む
        with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
            analytics = json.load(f)
        return analytics

    except json.JSONDecodeError:
        print(f"❌ エラー: {ANALYTICS_FILE}の読み込みに失敗しました")
        return {}
    except Exception as e:
        print(f"❌ エラー: 予期しないエラーが発生しました: {str(e)}")
        return {}


def should_analyze():
    """
    分析を実行すべきかを判定する関数
    最初の投稿から20日以上経過しているかをチェック
    20日以上なら True を返す、それ以外は False を返す
    """

    # まずanalyticsを読み込む
    analytics = load_analytics()

    # posts_historyが存在し、データがあるか確認する
    posts_history = analytics.get("posts_history", [])
    if not posts_history:
        print("⚠️  学習フェーズ: まだポスト記録がありません")
        return False

    try:
        # 最初の投稿（最も古い投稿）の日時を取得する
        first_post_datetime_str = posts_history[0]["posted_at"]

        # ISO 8601形式の文字列を日時オブジェクトに変換する
        # "+09:00" のようなタイムゾーン情報を処理するため fromisoformatを使う
        first_post_datetime = datetime.fromisoformat(first_post_datetime_str)

        # 現在の日時を取得する
        now = datetime.now(first_post_datetime.tzinfo)

        # 日数差分を計算する（小数点を落とした整数値）
        days_passed = (now - first_post_datetime).days

        # 日数に応じてメッセージを出力する
        if days_passed >= 20:
            print(f"✅ 分析準備完了: {days_passed}日のデータが蓄積されました")
            return True
        else:
            remaining_days = 20 - days_passed
            print(f"⚠️  学習フェーズ: あと{remaining_days}日でデータ分析を開始します（現在: {days_passed}日）")
            return False

    except (KeyError, ValueError, TypeError) as e:
        print(f"⚠️  警告: 日付の解析に失敗しました: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ エラー: 予期しないエラーが発生しました: {str(e)}")
        return False


def calculate_pattern_performance(posts_history):
    """
    投稿記録をDay と投稿タイプ（朝・夜）でグループ化して成績を計算する関数
    各グループについて、いいね・コメント・エンゲージメントスコアの平均値を算出
    """

    # Day と投稿タイプでグループ化するための空の辞書を作成する
    # 例: grouped_data[(1, "morning")] = [post1, post2, post3...]
    grouped_data = defaultdict(list)

    # posts_historyの各投稿レコードを処理する
    for post in posts_history:
        try:
            # 投稿レコードから Day番号を取得する
            day = post.get("day")

            # 投稿タイプ（例: "問いかけ型"など）を取得する
            post_type = post.get("type")

            # Day や type が不正な場合はスキップする
            if day is None or post_type is None:
                print(f"⚠️  警告: Day または type が不正な投稿をスキップしました")
                continue

            # このグループに投稿を追加する
            grouped_data[(day, post_type)].append(post)

        except Exception as e:
            print(f"⚠️  警告: 投稿の処理中にエラーが発生しました: {str(e)}")
            continue

    # グループごとに統計量を計算して、最終的な結果を作成する
    performance = {}

    # 各グループについて計算を実行する
    for (day, post_type), posts in grouped_data.items():
        try:
            # グループ内のいいね数をすべて抽出する
            likes_list = [p.get("likes", 0) for p in posts]

            # グループ内のコメント数をすべて抽出する
            comments_list = [p.get("comments", 0) for p in posts]

            # グループ内の閲覧数をすべて抽出する
            views_list = [p.get("views", 0) for p in posts]

            # グループ内のエンゲージメント率をすべて抽出する
            engagement_rates = [p.get("engagement_rate", 0) for p in posts]

            # 投稿時刻（時間）を抽出して、最も多く投稿された時間を見つける
            hours = []
            for p in posts:
                posted_at = p.get("posted_at", "")
                if posted_at:
                    try:
                        # ISO 8601形式の文字列から時間を取り出す
                        dt = datetime.fromisoformat(posted_at)
                        hours.append(dt.hour)
                    except (ValueError, TypeError):
                        pass

            # 平均値を計算する
            avg_likes = sum(likes_list) / len(likes_list) if likes_list else 0
            avg_comments = sum(comments_list) / len(comments_list) if comments_list else 0
            avg_views = sum(views_list) / len(views_list) if views_list else 0
            avg_engagement_rate = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0

            # 最も多く投稿された時間（ベストアワー）を見つける
            best_hour = max(set(hours), key=hours.count) if hours else None

            # Day と投稿タイプをキーとして、結果を保存する
            day_key = f"day_{day}"
            if day_key not in performance:
                performance[day_key] = {}

            # このタイプ（朝・夜など）の統計情報を記録する
            performance[day_key][post_type] = {
                "total_posts": len(posts),  # グループ内の投稿数
                "avg_likes": round(avg_likes, 1),  # 平均いいね数（小数第1位まで）
                "avg_comments": round(avg_comments, 1),  # 平均コメント数（小数第1位まで）
                "avg_engagement_score": round(avg_engagement_score, 1),  # 平均エンゲージメント
                "best_hour": best_hour,  # 最も多く投稿された時間
                "best_hashtag_set": "A"  # デフォルト値（後でoptimizer.pyで更新される）
            }

        except Exception as e:
            print(f"⚠️  警告: パターン({day}, {post_type})の計算中にエラーが発生しました: {str(e)}")
            continue

    return performance


def update_analytics(performance):
    """
    計算したパターン成績をskin_analytics.jsonに反映して保存する関数
    既存のデータを保持しつつ、pattern_performanceセクションを更新
    """

    try:
        # 既存のanalyticsファイルを読み込む
        analytics = load_analytics()

        # pattern_performanceキーが存在しなければ作成する
        if "pattern_performance" not in analytics:
            analytics["pattern_performance"] = {}

        # 計算した各Day の成績を既存データにマージする
        for day_key, day_data in performance.items():
            # 既存のDay データをすべて上書きする
            analytics["pattern_performance"][day_key] = day_data

        # 更新日時を記録する（ISO 8601形式）
        analytics["last_updated"] = datetime.now().isoformat()

        # 更新内容をJSONファイルに保存する
        with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
            json.dump(analytics, f, ensure_ascii=False, indent=2)

        print(f"✅ 分析完了: {len(performance)}個のDay パターンを分析・保存しました")

    except Exception as e:
        print(f"❌ エラー: analyticsの更新に失敗しました: {str(e)}")


def main():
    """
    メイン処理
    分析の実行判定 → データ読込 → パターン計算 → ファイル保存
    """

    # 分析を実行すべきかを判定する
    if not should_analyze():
        # 20日以上のデータが無い場合は処理を終了する
        return

    # skin_analytics.jsonを読み込む
    analytics = load_analytics()

    # posts_historyを取得する
    posts_history = analytics.get("posts_history", [])
    if not posts_history:
        print("❌ エラー: posts_historyが空です")
        return

    # 投稿記録をパターン別に分析する
    print("📊 パターン成績の計算を開始します...")
    performance = calculate_pattern_performance(posts_history)

    # 計算結果がない場合は処理を終了する
    if not performance:
        print("⚠️  警告: 分析対象のパターンがありません")
        return

    # 分析結果をファイルに保存する
    update_analytics(performance)


if __name__ == "__main__":
    main()
