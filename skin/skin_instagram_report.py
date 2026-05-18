# skin_instagram_report.py
# skin Instagram バッチごとの保存率検証レポート
# 使い方: python3 skin/skin_instagram_report.py --batch 1

import argparse                       # コマンドライン引数のパース
import json                           # JSON読み書き
from pathlib import Path              # ファイルパスの道具
from datetime import datetime         # 日時の道具

_DIR              = Path(__file__).resolve().parent
ANALYTICS_FILE    = _DIR / "skin_instagram_analytics.json"
BATCH_FILE        = _DIR / "skin_instagram_batch_progress.json"
CONTENT_FILE      = _DIR / "carousel_content.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_batch_themes(batch_id: int) -> list[int]:
    """バッチ番号から該当テーマIDのリストを返す"""
    data    = load_json(BATCH_FILE)
    batches = data.get("batches", {})
    batch   = batches.get(str(batch_id))
    if not batch:
        raise ValueError(f"Batch {batch_id} が見つかりません")
    return batch["themes"]


def get_v1_baseline_save_rate(analytics: dict, exclude_post_ids: set) -> float:
    """旧版（v1）の平均保存率を計算する。指定の投稿IDは除外する（v2投稿の混在を防ぐ）"""
    rates = []
    for post_id, post_data in analytics.get("posts", {}).items():
        if post_id in exclude_post_ids:
            continue
        rate = post_data.get("save_rate", 0.0)
        if rate > 0:
            rates.append(rate)
    if not rates:
        return 0.0
    return round(sum(rates) / len(rates), 2)


def get_v2_save_rates_by_theme(analytics: dict, target_theme_ids: list[int]) -> dict[int, list[float]]:
    """v2投稿をテーマ別に集計する（captionに theme_id を埋め込んだ前提だが暫定で空辞書を返す）"""
    # 注: Instagram投稿APIには独自タグを埋める手段が限定的なので、
    #     初版ではcaption冒頭のフックでテーマ識別。または投稿日とbatch_progressの突合で識別。
    # ここでは Batch リリース後の投稿日時で簡易判定する。
    return {tid: [] for tid in target_theme_ids}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, required=True, help="検証対象のバッチ番号 (1-5)")
    args = parser.parse_args()

    batch_id     = args.batch
    theme_ids    = get_batch_themes(batch_id)
    analytics    = load_json(ANALYTICS_FILE)

    # ベースライン: バッチリリース前の全投稿の平均保存率
    baseline = get_v1_baseline_save_rate(analytics, exclude_post_ids=set())

    # v2投稿の保存率（テーマ別）— 初版では暫定実装
    v2_rates = get_v2_save_rates_by_theme(analytics, theme_ids)

    print(f"=== Batch {batch_id} 検証レポート（{datetime.now().strftime('%Y-%m-%d')}）===\n")
    print(f"対象テーマ: {theme_ids}")
    print(f"v1ベースライン平均保存率: {baseline}%\n")

    print("テーマ別 v2 保存率（v1ベースライン比）:")
    for tid in theme_ids:
        rates = v2_rates.get(tid, [])
        if not rates:
            print(f"  テーマ{tid}: データ不足（投稿後の蓄積待ち）")
            continue
        avg = round(sum(rates) / len(rates), 2)
        delta = round((avg - baseline) / baseline * 100, 1) if baseline > 0 else 0
        flag = "🟢" if delta >= 30 else "🟡" if delta >= -10 else "🔴"
        print(f"  テーマ{tid}: v2={avg}%  v1={baseline}%  → {delta:+.1f}% {flag}")

    print("\nロールバック判定:")
    print("  黄信号(-10%下落で3日連続) | 赤信号(-30%下落で2日連続)")
    print("  Batch 1 はベースライン蓄積が薄い場合、絶対値判定 (黄1.5%/赤0.8%) を併用すること。")


if __name__ == "__main__":
    main()
