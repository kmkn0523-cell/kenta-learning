#!/usr/bin/env python3
# skin_weekly_report.py
# skin Threads の「今週どうだった？」を自動でまとめる週次レポート。
# 既存の分析データ（skin_analytics.json）とA/B判定（skin_ab_report.py）を束ねて、
# 直近7日の数字・伸びた投稿・次の打ち手を人間が読める形で出す。
# 使い方: python3 skin/skin_weekly_report.py
#   → 画面に表示しつつ skin/skin_weekly_report.md に書き出す。

import json     # JSONを読む道具
import os       # ファイルの場所を組み立てる道具
import re       # 日時の "+0000" を直す道具
import smtplib  # メールを送る道具（週次レポートをGmailで通知）
from datetime import datetime, timezone, timedelta  # 日時を扱う道具
from email.mime.text import MIMEText  # メール本文を作る道具

MAIL_ADDR = "kmkn0523@gmail.com"  # 送信元・送信先（どちらも自分のGmail）

# A/B判定は既存スクリプトの関数を再利用する（直接実行でもpytest経由でも動くよう2通り試す）
try:
    from skin_ab_report import judge_theme
except ImportError:
    from skin.skin_ab_report import judge_theme

# ファイルの場所（このスクリプトと同じ skin/ にある前提）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYTICS_PATH = os.path.join(BASE_DIR, "skin_analytics.json")
PROGRESS_PATH = os.path.join(BASE_DIR, "skin_threads_progress.json")
REPORT_PATH = os.path.join(BASE_DIR, "skin_weekly_report.md")
JST = timezone(timedelta(hours=9))  # 日本時間


def _parse_dt(text):
    """Threads APIの日時 "+0000"（コロン無し）を Python が読める形に直して datetime にする。"""
    text = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", text)  # 末尾 +0000 → +00:00
    return datetime.fromisoformat(text)


def recent_posts(history, today, days=7):
    """投稿履歴から、today を基準に直近 days 日ぶんの投稿だけを取り出す。"""
    cutoff = today - timedelta(days=days)  # この日時より新しい投稿だけ残す
    result = []
    for post in history:
        posted_at = post.get("posted_at")
        if not posted_at:  # 投稿日時が無いデータは飛ばす
            continue
        try:
            posted_dt = _parse_dt(posted_at)
        except ValueError:  # 日付が壊れていたら飛ばす（全体は止めない）
            continue
        if posted_dt >= cutoff:
            result.append(post)
    return result


def summarize(posts):
    """投稿リストから平均viewsなどの要約を作る。空なら全部0で返す。"""
    count = len(posts)
    if count == 0:
        return {"count": 0, "avg_views": 0.0, "avg_likes": 0.0, "avg_engagement": 0.0, "total_views": 0}
    total_views = sum(post.get("views", 0) for post in posts)
    total_likes = sum(post.get("likes", 0) for post in posts)
    total_engagement = sum(post.get("engagement_rate", 0) for post in posts)
    return {
        "count": count,
        "avg_views": total_views / count,
        "avg_likes": total_likes / count,
        "avg_engagement": total_engagement / count,
        "total_views": total_views,
    }


def top_posts(posts, n=5, key="views"):
    """指定キー（既定はviews）の大きい順に上位n件を返す。"""
    return sorted(posts, key=lambda post: post.get(key, 0), reverse=True)[:n]


def suggest_next_actions(summary):
    """要約の数字を見て、次にやるべきことをルールベースで提案する。"""
    if summary["count"] == 0:
        return ["直近7日の投稿データがありません。データ収集（skin_data_collector）が動いているか確認してください。"]
    actions = []
    if summary["avg_likes"] < 1:
        actions.append("いいねが極小です。1コメ目のテーマ連動シードと、保存・リポストCTAの頻度を見直してください。")
    if summary["avg_views"] < 100:
        actions.append("閲覧が伸びていません。リプライ・エンジンの有効化（他人投稿への自動返信→プロフィール流入）が最優先です。")
    if summary["avg_engagement"] < 2:
        actions.append("エンゲージ率が低めです。フック1行目の具体性（数字・逆張り）を強化してください（6/24以降の投稿刷新で）。")
    if not actions:
        actions.append("主要指標は安定しています。note誘導CTAのテーマ連動が効いているか、note流入を確認してください。")
    return actions


def ab_summary(ab_results, min_posts=3):
    """ab_results（テーマ別A/Bスコア）を判定して、勝敗の集計を返す。"""
    counts = {"A_wins": 0, "B_wins": 0, "no_significant_diff": 0, "insufficient_data": 0}
    for theme_key, entry in ab_results.items():
        try:
            theme_id = int(theme_key)
        except (TypeError, ValueError):
            continue
        verdict = judge_theme(
            theme_id,
            entry.get("a_score", 0.0),
            entry.get("b_score", 0.0),
            entry.get("a_posts", 0),
            entry.get("b_posts", 0),
            min_posts,
        )["verdict"]
        counts[verdict] += 1
    return counts


def build_report(history, today, ab_results=None):
    """週次レポートの本文（文字列）を組み立てる。"""
    recent = recent_posts(history, today)
    summary = summarize(recent)
    lines = []
    lines.append(f"# skin Threads 週次レポート（{today.strftime('%Y-%m-%d')}）")
    lines.append("")
    lines.append("## 直近7日のサマリー")
    lines.append(f"- 投稿数: {summary['count']}件")
    lines.append(f"- 平均閲覧（views）: {summary['avg_views']:.1f}")
    lines.append(f"- 平均いいね: {summary['avg_likes']:.2f}")
    lines.append(f"- 平均エンゲージ率: {summary['avg_engagement']:.2f}%")
    lines.append(f"- 合計閲覧: {summary['total_views']}")
    lines.append("")
    lines.append("## 伸びた投稿 Top5（views順）")
    if recent:
        for post in top_posts(recent):
            lines.append(
                f"- views {post.get('views', 0)} / いいね {post.get('likes', 0)}"
                f" / {post.get('type', post.get('theme', '不明'))}"
            )
    else:
        lines.append("- （対象投稿なし）")
    lines.append("")
    if ab_results:
        ab = ab_summary(ab_results)
        lines.append("## A/B判定の状況")
        lines.append(
            f"- A勝ち {ab['A_wins']} / B勝ち {ab['B_wins']} / "
            f"差なし {ab['no_significant_diff']} / データ不足 {ab['insufficient_data']}"
        )
        lines.append("")
    lines.append("## 次の打ち手")
    for action in suggest_next_actions(summary):
        lines.append(f"- {action}")
    return "\n".join(lines)


def send_report_email(report_text, today):
    """週次レポートをGmailで自分宛に送る。パスワード未設定なら静かにスキップ。"""
    password = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not password:  # ローカル実行時はパスワードが無いので送らない（既存スクリプトと同じ作法）
        print("GMAIL_APP_PASSWORD が未設定のため、メール送信はスキップします。")
        return
    msg = MIMEText(report_text, "plain", "utf-8")  # レポート本文をそのままメールにする
    msg["From"] = MAIL_ADDR
    msg["To"] = MAIL_ADDR
    msg["Subject"] = f"【skin週次レポート】{today.strftime('%Y-%m-%d')}"
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:  # Gmailの安全な送信口
        server.login(MAIL_ADDR, password)
        server.send_message(msg)
    print("週次レポートをメール送信しました。")


def main():
    """実データを読んでレポートを画面とファイルに出す。"""
    with open(ANALYTICS_PATH, encoding="utf-8") as f:
        history = json.load(f).get("posts_history", [])
    ab_results = {}
    try:  # 進捗ファイルは大きいが ab_results キーだけ使う（読むだけ・書き換えない）
        with open(PROGRESS_PATH, encoding="utf-8") as f:
            ab_results = json.load(f).get("ab_results", {})
    except (FileNotFoundError, json.JSONDecodeError):
        ab_results = {}
    today = datetime.now(JST)
    report = build_report(history, today, ab_results)
    print(report)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(f"\n→ 書き出し: {REPORT_PATH}")
    send_report_email(report, today)  # GMAIL_APP_PASSWORD があればメール通知


if __name__ == "__main__":
    main()
