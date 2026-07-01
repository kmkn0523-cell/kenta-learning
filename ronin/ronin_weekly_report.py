#!/usr/bin/env python3
# ronin_weekly_report.py
# @RoninWords Threads の「今週どうだった？」を自動でまとめる週次レポート。
# 既存の分析データ（ronin_analytics.json）と最適化ランキング（ronin_optimization_index.json）を
# 束ねて、直近7日の数字・伸びた投稿・次の打ち手を人間が読める形で出す。
# 使い方: python3 ronin/ronin_weekly_report.py
#   → 画面に表示しつつ ronin/ronin_weekly_report.md に書き出す。

import json     # JSONを読む道具
import os       # ファイルの場所を組み立てる道具
import re       # 日時の "+0000" を直す道具
import smtplib  # メールを送る道具（週次レポートをGmailで通知）
from datetime import datetime, timezone, timedelta  # 日時を扱う道具
from email.mime.text import MIMEText  # メール本文を作る道具

MAIL_ADDR = "kmkn0523@gmail.com"  # 送信元・送信先（どちらも自分のGmail）

# ファイルの場所（このスクリプトと同じ ronin/ にある前提）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYTICS_PATH = os.path.join(BASE_DIR, "ronin_analytics.json")
OPTIMIZATION_PATH = os.path.join(BASE_DIR, "ronin_optimization_index.json")
REPORT_PATH = os.path.join(BASE_DIR, "ronin_weekly_report.md")
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
        return ["直近7日の投稿データがありません。ronin_analytics_daily.ymlが動いているか確認してください。"]
    actions = []
    if summary["avg_likes"] < 1:
        actions.append("いいねが極小です。1コメ目のテーマ連動シード（ronin_comment_seeder）とengagement投稿の比率を見直してください。")
    if summary["avg_views"] < 30:
        actions.append("閲覧が伸びていません。reply_hunter.pyでの手動リプ巡回（reachの最強手段）を今週やってみてください。")
    if summary["avg_engagement"] < 5:
        actions.append("エンゲージ率が低めです。ハッシュタグセットのローテと配信時刻（ET基準）が効いているか確認してください。")
    if not actions:
        actions.append("主要指標は安定しています。CTAのSubstackテーマ連動が実際にクリックされているか確認してください。")
    return actions


def build_report(history, today, pattern_ranking=None):
    """週次レポートの本文（文字列）を組み立てる。"""
    recent = recent_posts(history, today)
    summary = summarize(recent)
    lines = []
    lines.append(f"# ronin Threads 週次レポート（{today.strftime('%Y-%m-%d')}）")
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
                f" / {post.get('type', '不明')}"
            )
    else:
        lines.append("- （対象投稿なし）")
    lines.append("")
    if pattern_ranking:
        lines.append("## 高反応パターン Top5（優先度順）")
        for entry in pattern_ranking[:5]:
            lines.append(f"- Day{entry.get('day')} / score {entry.get('score')} / 優先度{entry.get('priority')}")
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
    msg["Subject"] = f"【ronin週次レポート】{today.strftime('%Y-%m-%d')}"
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:  # Gmailの安全な送信口
        server.login(MAIL_ADDR, password)
        server.send_message(msg)
    print("週次レポートをメール送信しました。")


def main():
    """実データを読んでレポートを画面とファイルに出す。"""
    with open(ANALYTICS_PATH, encoding="utf-8") as f:
        history = json.load(f).get("posts_history", [])
    pattern_ranking = []
    try:  # 最適化インデックスは大きいが pattern_ranking キーだけ使う（読むだけ・書き換えない）
        with open(OPTIMIZATION_PATH, encoding="utf-8") as f:
            pattern_ranking = json.load(f).get("pattern_ranking", [])
    except (FileNotFoundError, json.JSONDecodeError):
        pattern_ranking = []
    today = datetime.now(JST)
    report = build_report(history, today, pattern_ranking)
    print(report)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(f"\n→ 書き出し: {REPORT_PATH}")
    send_report_email(report, today)  # GMAIL_APP_PASSWORD があればメール通知


if __name__ == "__main__":
    main()
