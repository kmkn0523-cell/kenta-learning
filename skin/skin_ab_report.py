"""skin Threads A/B検証レポート生成スクリプト。

使い方:
    python3 skin_ab_report.py [--batch N]

batchを省略すると skin_threads_batch_progress.json の current_batch を読む。
"""
# A/B結果から勝者を判定してレポートを出力するファイル
import argparse
import json
from pathlib import Path
from typing import Iterable

# プロジェクトルート（このファイルが skin/ 直下にある前提）
ROOT = Path(__file__).resolve().parent
PROGRESS_PATH = ROOT / "skin_threads_progress.json"
BATCH_PATH = ROOT / "skin_threads_batch_progress.json"
ANALYTICS_PATH = ROOT / "skin_analytics.json"


def judge_theme(
    theme_id: int,
    a_score: float,
    b_score: float,
    a_posts: int,
    b_posts: int,
    min_posts: int = 3,
) -> dict:
    # 1テーマのA/B結果から勝者を判定する
    if a_posts < min_posts or b_posts < min_posts:
        return {
            "theme_id": theme_id,
            "verdict": "insufficient_data",
            "a_avg": 0.0,
            "b_avg": 0.0,
            "lead_pct": 0.0,
        }

    a_avg = a_score / a_posts
    b_avg = b_score / b_posts
    larger = max(a_avg, b_avg)
    if larger == 0:
        return {
            "theme_id": theme_id,
            "verdict": "no_significant_diff",
            "a_avg": 0.0,
            "b_avg": 0.0,
            "lead_pct": 0.0,
        }

    lead_pct = abs(a_avg - b_avg) / larger
    if lead_pct < 0.2:
        verdict = "no_significant_diff"
    elif a_avg > b_avg:
        verdict = "A_wins"
    else:
        verdict = "B_wins"

    return {
        "theme_id": theme_id,
        "verdict": verdict,
        "a_avg": a_avg,
        "b_avg": b_avg,
        "lead_pct": lead_pct,
    }


def aggregate_ab_scores(history: Iterable[dict], posts_history: Iterable[dict]) -> dict:
    # 投稿履歴(history)と反応データ(posts_history)を突き合わせてA/Bスコアを集計する
    # post_id ごとのエンゲージメント率を引けるように辞書を作る
    rate_by_id = {
        str(p["post_id"]): p.get("engagement_rate", 0.0)
        for p in posts_history
        if p.get("post_id") is not None
    }

    results = {}
    for entry in history:
        post_id = entry.get("post_id")
        theme_id = entry.get("theme_id")
        variant = entry.get("variant")
        # 必須項目が欠けている履歴は集計しない
        if post_id is None or theme_id is None or variant not in ("A", "B"):
            continue
        # 反応データが取れていない投稿（API未反映）は集計対象外にする
        if str(post_id) not in rate_by_id:
            continue

        rate = rate_by_id[str(post_id)]
        theme_key = str(theme_id)
        bucket = results.setdefault(
            theme_key, {"a_score": 0.0, "b_score": 0.0, "a_posts": 0, "b_posts": 0}
        )
        if variant == "A":
            bucket["a_score"] += rate
            bucket["a_posts"] += 1
        else:
            bucket["b_score"] += rate
            bucket["b_posts"] += 1

    return results


def generate_report(progress: dict, themes: Iterable[int]) -> str:
    # テーマ一覧からレポート文字列を生成する
    lines = ["=== A/B検証レポート ==="]
    counts = {"A_wins": 0, "B_wins": 0, "no_significant_diff": 0, "insufficient_data": 0}
    results = progress.get("ab_results", {})

    for theme_id in themes:
        entry = results.get(str(theme_id), {})
        judgement = judge_theme(
            theme_id=theme_id,
            a_score=entry.get("a_score", 0.0),
            b_score=entry.get("b_score", 0.0),
            a_posts=entry.get("a_posts", 0),
            b_posts=entry.get("b_posts", 0),
        )
        counts[judgement["verdict"]] += 1
        label = {
            "A_wins": "A勝ち",
            "B_wins": "B勝ち",
            "no_significant_diff": "差なし",
            "insufficient_data": "データ不足",
        }[judgement["verdict"]]
        lines.append(
            f"テーマ{theme_id}: A={judgement['a_avg']:.1f} B={judgement['b_avg']:.1f} "
            f"→ {label}（差{judgement['lead_pct']*100:.1f}%）"
        )

    lines.append("")
    lines.append(
        f"集計: A勝ち {counts['A_wins']} / B勝ち {counts['B_wins']} / "
        f"差なし {counts['no_significant_diff']} / データ不足 {counts['insufficient_data']}"
    )
    return "\n".join(lines)


def parse_theme_range(themes_str: str) -> list:
    # "1-20" のような文字列をテーマID配列に展開する
    start_str, end_str = themes_str.split("-")
    return list(range(int(start_str), int(end_str) + 1))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=None)
    args = parser.parse_args()

    progress = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    batch_data = json.loads(BATCH_PATH.read_text(encoding="utf-8"))

    # 反応データ(skin_analytics.json)を読む。無ければ空で続行する
    try:
        analytics = json.loads(ANALYTICS_PATH.read_text(encoding="utf-8"))
        posts_history = analytics.get("posts_history", [])
    except FileNotFoundError:
        print("⚠️ skin_analytics.json が見つかりません。反応データ無しで集計します")
        posts_history = []

    # 投稿履歴(history)×反応データ(posts_history)から毎回フレッシュにスコアを集計する
    # progressには書き戻さない（投稿スクリプトのカウントと衝突させないため）
    fresh_results = aggregate_ab_scores(progress.get("history", []), posts_history)
    report_source = {"ab_results": fresh_results}

    batch_id = args.batch or batch_data["current_batch"]
    themes_str = batch_data["batches"][str(batch_id)]["themes"]
    themes = parse_theme_range(themes_str)

    print(f"Batch {batch_id} (テーマ{themes_str}) のレポート:")
    print(generate_report(report_source, themes))


if __name__ == "__main__":
    main()
