#!/usr/bin/env python3
# skin_optimizer.py
# skinアカウント用 最適化インデックス生成スクリプト
# 使い方: python3 skin/skin_optimizer.py
# 分析済みのデータをもとに、投稿パターンのランキングと次の投稿予定を生成する

import json                    # JSONファイルを扱う道具
import os                      # ファイル操作に使う道具
from datetime import datetime  # 日時を扱う道具

# ファイルパスの設定
ANALYTICS_FILE = "/home/kenta_kamijyo/skin/ronin_analytics.json"
OPTIMIZATION_FILE = "/home/kenta_kamijyo/skin/ronin_optimization_index.json"


def load_analytics():
    """
    ronin_analytics.jsonを読み込む関数
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


def generate_pattern_ranking(pattern_performance):
    """
    パターン成績をもとに、Day別のランキングを生成する関数
    各Dayについて朝夜の平均エンゲージメントスコアを計算し、スコア順に優先度を割り当てる
    """

    # ランキング用の空のリストを作成する
    ranking_list = []

    # pattern_performanceの各Day を処理する
    for day_key, day_data in pattern_performance.items():
        try:
            # "day_3" のような形式から数字を抽出する
            day_number = int(day_key.split("_")[1])

            # morning（朝）のエンゲージメントスコアを取得する
            morning_data = day_data.get("問いかけ型", {})  # 問いかけ型をデフォルトにする
            morning_score = morning_data.get("avg_engagement_score", 0)

            # evening（夜）のエンゲージメントスコアを取得する
            # もし複数のタイプがある場合は全て平均して使う
            evening_score = 0
            type_count = 0
            for post_type, data in day_data.items():
                evening_score += data.get("avg_engagement_score", 0)
                type_count += 1

            # 複数タイプがある場合は平均を取る
            if type_count > 0:
                evening_score = evening_score / type_count

            # 朝と夜の平均を計算して、小数第1位で四捨五入する
            day_avg = round((morning_score + evening_score) / 2, 1)

            # このDayの情報をリストに追加する
            ranking_list.append({
                "day": day_number,
                "score": day_avg,
                "priority": None  # 後で優先度を割り当てる
            })

        except (ValueError, KeyError, TypeError) as e:
            print(f"⚠️  警告: {day_key}の処理中にエラーが発生しました: {str(e)}")
            continue
        except Exception as e:
            print(f"❌ エラー: 予期しないエラーが発生しました: {str(e)}")
            continue

    # スコアが高い順に並べ替える（降順）
    ranking_list.sort(key=lambda x: x["score"], reverse=True)

    # 優先度を割り当てる（1位から順に1, 2, 3...）
    for index, item in enumerate(ranking_list):
        item["priority"] = index + 1

    return ranking_list


def generate_next_post_queue(pattern_ranking):
    """
    パターンランキングをもとに、次の投稿キューを生成する関数
    優先度の高いパターンほど多く投稿するように調整して、2週間分（14日分）のキューを作成
    """

    # 投稿キュー用の空のリストを作成する
    queue_list = []

    # ランキングの各パターンに対して処理する
    for ranking_item in pattern_ranking:
        try:
            # 優先度と投稿日を取得する
            day = ranking_item["day"]
            priority = ranking_item["priority"]
            score = ranking_item["score"]

            # この優先度で何回投稿するかを計算する
            # 優先度が低いほど（数字が小さいほど）回数が多い
            # 優先度1 → 2回、優先度2 → 2回、優先度3以降 → 1回
            times_to_add = 2 if priority <= 2 else 1

            # 計算した回数分、キューにDayを追加する
            for _ in range(times_to_add):
                # 優先度に応じた理由文を作成する
                if priority == 1:
                    reason = "優先度1：高反応パターン"
                elif priority == 2:
                    reason = "優先度2：次点パターン"
                elif priority == 3:
                    reason = "優先度3：中程度パターン"
                else:
                    reason = f"優先度{priority}：参考パターン"

                # キューに追加する
                queue_list.append({
                    "day": day,
                    "priority": priority,
                    "reason": reason
                })

        except (KeyError, TypeError) as e:
            print(f"⚠️  警告: ランキング処理中にエラーが発生しました: {str(e)}")
            continue
        except Exception as e:
            print(f"❌ エラー: 予期しないエラーが発生しました: {str(e)}")
            continue

    # 最初の14項目（2週間分）だけを返す
    return queue_list[:14]


def update_optimization_index(pattern_ranking, next_post_queue):
    """
    生成したランキングとキューをronin_optimization_index.jsonに保存する関数
    分析日時、分析フェーズ、ステータスメッセージも記録する
    """

    try:
        # 既存のoptimization_indexファイルを読み込む
        if os.path.exists(OPTIMIZATION_FILE):
            with open(OPTIMIZATION_FILE, "r", encoding="utf-8") as f:
                optimization = json.load(f)
        else:
            # ファイルが無い場合は空の辞書を作成する
            optimization = {}

        # 現在の日時をISO 8601形式で記録する
        optimization["last_analyzed"] = datetime.now().isoformat()

        # パターンランキングを保存する
        optimization["pattern_ranking"] = pattern_ranking

        # 次の投稿キューを保存する
        optimization["next_post_queue"] = next_post_queue

        # analyticsを読み込んで、データ蓄積日数を取得する
        analytics = load_analytics()
        posts_history = analytics.get("posts_history", [])
        days_accumulated = len(posts_history)

        # 分析フェーズを判定する
        # 20日以上のデータが蓄積されていれば「最適化」フェーズ
        if days_accumulated >= 20:
            optimization["analysis_phase"] = "optimizing"
            optimization["status"] = f"最適化フェーズ：{days_accumulated}日分のデータをもとに投稿パターンを最適化しています"
        else:
            # 20日未満なら「学習」フェーズ
            optimization["analysis_phase"] = "learning"
            remaining_days = 20 - days_accumulated
            optimization["status"] = f"データ蓄積中。あと{remaining_days}日でDay21以降に最適化を開始します（現在：{days_accumulated}日）"

        # 更新内容をJSONファイルに保存する
        with open(OPTIMIZATION_FILE, "w", encoding="utf-8") as f:
            json.dump(optimization, f, ensure_ascii=False, indent=2)

        print(f"✅ 最適化インデックス更新完了: {len(pattern_ranking)}個のパターンをランキング化しました")
        print(f"   分析フェーズ: {optimization['analysis_phase']}")
        print(f"   次の投稿キュー: {len(next_post_queue)}日分を生成しました")

    except Exception as e:
        print(f"❌ エラー: optimization_indexの更新に失敗しました: {str(e)}")


def main():
    """
    メイン処理
    分析データを読込 → ランキング生成 → キュー生成 → インデックス更新
    """

    print("🚀 最適化インデックス生成を開始します...")

    # ronin_analytics.jsonを読み込む
    analytics = load_analytics()

    # pattern_performanceを取得する
    pattern_performance = analytics.get("pattern_performance", {})

    # パターン成績が空の場合は処理を終了する
    if not pattern_performance:
        print("⚠️  情報: 分析対象のパターンがありません")
        return

    # パターンランキングを生成する
    print("📈 パターンランキングを生成中...")
    pattern_ranking = generate_pattern_ranking(pattern_performance)

    # 生成したランキングが空の場合は処理を終了する
    if not pattern_ranking:
        print("⚠️  警告: ランキングの生成に失敗しました")
        return

    # 次の投稿キューを生成する
    print("📅 次の投稿キューを生成中...")
    next_post_queue = generate_next_post_queue(pattern_ranking)

    # インデックスを更新する
    print("💾 最適化インデックスを更新中...")
    update_optimization_index(pattern_ranking, next_post_queue)

    print("✨ 最適化インデックス生成が完了しました！")


if __name__ == "__main__":
    main()
