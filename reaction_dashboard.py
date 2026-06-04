# -*- coding: utf-8 -*-
"""
reaction_dashboard.py

すべてのSNS自動投稿（skin / ronin の Threads・Instagram・note・Substack）の
「投稿数」と「反応（いいね等）」を1枚の dashboard.md にまとめるスクリプト。

特徴:
- 各プラットフォームの分析JSONを「読むだけ」。既存ファイルは一切書き換えません。
- 標準ライブラリ（json / pathlib / datetime）だけで動きます。追加インストール不要。

使い方（このファイルのある場所で実行）:
    python3 reaction_dashboard.py
すると同じフォルダに dashboard.md ができます。
"""

import json  # JSONファイルを読むための標準ライブラリ
from pathlib import Path  # ファイルの場所を扱う標準ライブラリ
from datetime import datetime, timezone, timedelta  # 日時を扱う標準ライブラリ

# このスクリプトが置いてあるフォルダ（＝プロジェクトのルート）を基準にする
BASE = Path(__file__).resolve().parent

# 日本時間（JST）は世界標準時(UTC)より9時間進んでいる
JST = timezone(timedelta(hours=9))


def load_json(relative_path):
    """JSONファイルを安全に読み込む。無ければ・壊れていれば None を返す。"""
    file_path = BASE / relative_path  # ルートからの相対パスで場所を決める
    if not file_path.exists():  # ファイルが存在しないとき
        return None
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))  # 中身を辞書として読む
    except Exception:
        # 中身が壊れていても全体を止めないように None を返す
        return None


def parse_datetime(text):
    """いろいろな形式の日時文字列を datetime に変換する。失敗したら None。"""
    if not text or not isinstance(text, str):  # 空や文字列でないものは諦める
        return None
    # 形式1: ISO形式（例 2026-06-04T03:01:14.467037+00:00）
    try:
        return datetime.fromisoformat(text)
    except Exception:
        pass
    # 形式2: スラッシュ区切りなど（例 2026/05/23 08:51）→ 日本時間として扱う
    for fmt in ("%Y/%m/%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            naive_datetime = datetime.strptime(text, fmt)  # まず時間帯なしで読む
            return naive_datetime.replace(tzinfo=JST)  # 日本時間の情報を付ける
        except Exception:
            continue
    return None  # どれにも当てはまらなければ None


def to_jst_text(text):
    """日時文字列を「2026-06-04 12:01 JST」の形にして返す。"""
    parsed = parse_datetime(text)
    if parsed is None:
        return "（不明）"
    if parsed.tzinfo is None:  # 時間帯情報が無ければUTC扱いにしておく
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(JST).strftime("%Y-%m-%d %H:%M JST")  # 日本時間に直して整形


def hours_since(text):
    """その日時から今までに何時間たったかを返す。わからなければ None。"""
    parsed = parse_datetime(text)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)  # 今の時刻（世界標準時）
    return (now - parsed).total_seconds() / 3600  # 差を「時間」に直す


def summarize_reactions(posts_history):
    """投稿ごとの反応リストから、合計（いいね等）と平均反応率をまとめる。"""
    total = {"likes": 0, "comments": 0, "shares": 0, "views": 0}  # 合計の入れ物
    rates = []  # 反応率を集める入れ物
    for post in posts_history:
        # 反応の各数値を足す。値が無い・None のときは0として扱う
        total["likes"] += post.get("likes", 0) or 0
        total["comments"] += post.get("comments", 0) or 0
        total["shares"] += post.get("shares", 0) or 0
        total["views"] += post.get("views", 0) or 0
        rates.append(post.get("engagement_rate", 0) or 0)
    average_rate = sum(rates) / len(rates) if rates else 0  # 平均反応率（0件なら0）
    return total, average_rate


def real_reactions(post):
    """その投稿の「実際についた反応数」＝いいね＋コメント＋シェア を返す。"""
    return (post.get("likes", 0) or 0) + (post.get("comments", 0) or 0) + (post.get("shares", 0) or 0)


def top_posts(posts_history, count=3):
    """実際の反応数が多い順に上位 count 件を返す。実反応0の投稿は除く。"""
    # 表示回数だけ多くて反応ゼロの投稿は「伸びた」とは言えないので除外する
    scored = [p for p in posts_history if real_reactions(p) > 0]
    scored.sort(key=real_reactions, reverse=True)  # 反応が多い順に並べる
    return scored[:count]


# ここから下が「ダッシュボードの本文」を組み立てる部分 ---------------------------

lines = []  # 出力する行をためていく入れ物
alerts = []  # 「気づき・注意」をためていく入れ物


def add(text=""):
    """1行ぶんを本文に追加する小さな道具。"""
    lines.append(text)


# 見出しと生成時刻
now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
add("# 📊 反応ダッシュボード（自動生成）")
add()
add(f"生成日時: {now_jst}")
add()
add("> 各SNSの「投稿数」と「反応」を1枚にまとめたものです。`reaction_dashboard.py` が自動で作成します。")
add()

# 横断サマリー表のための入れ物（あとで上に差し込む）
summary_rows = []


def register_summary(account, platform, total_posts, last_posted_text, reaction_note):
    """横断サマリー表に1行ぶんのデータを登録する。"""
    last_text = to_jst_text(last_posted_text) if last_posted_text else "（不明）"
    summary_rows.append((account, platform, total_posts, last_text, reaction_note))
    # 最終投稿から時間が経ちすぎていたら注意リストに入れる（Threads/Instagram用）
    elapsed = hours_since(last_posted_text) if last_posted_text else None
    if elapsed is not None and elapsed >= 24:
        alerts.append(
            f"⚠️ **{account} {platform}** は最終投稿から約{int(elapsed)}時間経過（投稿が止まっている可能性）"
        )


# ===== skin（肌荒れ改善）=====================================================
add("## 🧴 skin（肌荒れ改善note）")
add()

# --- skin Threads ---
skin_threads_progress = load_json("skin/skin_threads_progress.json") or {}
skin_analytics = load_json("skin/skin_analytics.json") or {}
skin_history = skin_threads_progress.get("history", [])
skin_posts_history = skin_analytics.get("posts_history", [])
skin_total, skin_avg_rate = summarize_reactions(skin_posts_history)
skin_reaction_sum = sum(skin_total.values())  # 反応の総数（0なら反応まだ無し）

add("### Threads")
add(f"- 累計投稿ログ: **{len(skin_history)}件**")
add(f"- 最終投稿: {to_jst_text(skin_threads_progress.get('last_posted_at'))}")
add(
    f"- 反応合計: いいね {skin_total['likes']} / コメント {skin_total['comments']} "
    f"/ シェア {skin_total['shares']} / 表示 {skin_total['views']}"
)
add(f"- 平均反応率: {skin_avg_rate:.2f}%（計測対象 {len(skin_posts_history)}件）")
if skin_threads_progress.get("last_note_promo_date"):
    add(f"- 最終note誘導: {skin_threads_progress.get('last_note_promo_date')}")
# 伸びた投稿トップ3（反応がある場合だけ）
skin_top = top_posts(skin_posts_history)
if skin_top:
    add("- 🏆 反応が良かった投稿 TOP3:")
    for rank, post in enumerate(skin_top, start=1):
        add(
            f"  {rank}. Day{post.get('day','?')}「{post.get('type','')}」"
            f" — いいね {post.get('likes',0)} / コメント {post.get('comments',0)}"
            f" / 表示 {post.get('views',0)}"
        )
else:
    add("- 🏆 反応が良かった投稿: まだ反応データがありません（蓄積中）")
add()
register_summary("skin", "Threads", len(skin_history),
                 skin_threads_progress.get("last_posted_at"),
                 f"反応計 {skin_reaction_sum}")

# --- skin Instagram ---
skin_ig_progress = load_json("skin/skin_instagram_progress.json") or {}
skin_ig_analytics = load_json("skin/skin_instagram_analytics.json") or {}
follower_history = skin_ig_analytics.get("follower_history", [])
latest_followers = follower_history[-1]["count"] if follower_history else 0

add("### Instagram")
add(f"- 累計投稿数: **{skin_ig_progress.get('post_count', 0)}件**")
add(f"- 最終投稿: {to_jst_text(skin_ig_progress.get('last_posted_at'))}")
add(f"- 最新フォロワー数: {latest_followers}（記録 {len(follower_history)}日分）")
add()
register_summary("skin", "Instagram", skin_ig_progress.get("post_count", 0),
                 skin_ig_progress.get("last_posted_at"),
                 f"フォロワー {latest_followers}")

# --- skin note ---
note_progress = load_json("skin/note_queue_progress.json") or {}
note_history = note_progress.get("history", [])
add("### note")
add(f"- 投稿済み記事: **{len(note_history)}件**")
if note_history:
    latest_note = note_history[-1]
    add(f"- 最新: {latest_note.get('date','')}「{latest_note.get('title','')}」")
add()
register_summary("skin", "note", len(note_history),
                 None, "—")

# ===== ronin（@RoninWords）===================================================
add("## ✍️ ronin（@RoninWords）")
add()

# --- ronin Threads ---
ronin_threads_progress = load_json("ronin/ronin_threads_progress.json") or {}
ronin_analytics = load_json("ronin/ronin_analytics.json") or {}
ronin_history = ronin_threads_progress.get("history", [])
ronin_posts_history = ronin_analytics.get("posts_history", [])
ronin_total, ronin_avg_rate = summarize_reactions(ronin_posts_history)
ronin_reaction_sum = sum(ronin_total.values())

add("### Threads")
add(f"- 累計投稿ログ: **{len(ronin_history)}件**")
add(f"- 最終投稿: {to_jst_text(ronin_threads_progress.get('last_posted_at'))}")
if ronin_posts_history:
    add(
        f"- 反応合計: いいね {ronin_total['likes']} / コメント {ronin_total['comments']} "
        f"/ シェア {ronin_total['shares']} / 表示 {ronin_total['views']}"
    )
    add(f"- 平均反応率: {ronin_avg_rate:.2f}%（計測対象 {len(ronin_posts_history)}件）")
else:
    add("- 反応データ: まだ取得されていません（`ronin_data_collector.py` の蓄積待ち）")
add()
register_summary("ronin", "Threads", len(ronin_history),
                 ronin_threads_progress.get("last_posted_at"),
                 f"反応計 {ronin_reaction_sum}" if ronin_posts_history else "データ未取得")

# --- ronin Instagram ---
ronin_ig_progress = load_json("ronin/ronin_instagram_progress.json") or {}
add("### Instagram")
add(f"- 投稿インデックス: **{ronin_ig_progress.get('next_index', 0)}**（次に投稿する番号）")
add(f"- 最終投稿: {to_jst_text(ronin_ig_progress.get('last_posted_at'))}")
add()
register_summary("ronin", "Instagram", ronin_ig_progress.get("next_index", 0),
                 ronin_ig_progress.get("last_posted_at"), "—")

# --- ronin Substack ---
substack_progress = load_json("ronin/substack/substack_progress.json") or {}
deep_dive_progress = load_json("ronin/substack/deep_dive_progress.json") or {}
substack_history = substack_progress.get("history", [])
deep_dive_history = deep_dive_progress.get("history", [])
add("### Substack")
add(f"- 通常投稿: **{len(substack_history)}件**")
if substack_history:
    add(f"  - 最新: {substack_history[-1].get('date','')}「{substack_history[-1].get('title','')}」")
add(f"- Deep Dive: **{len(deep_dive_history)}件**")
if deep_dive_history:
    add(f"  - 最新: {deep_dive_history[-1].get('date','')}「{deep_dive_history[-1].get('title','')}」")
add()

# ===== 最適化フェーズの状況 =================================================
add("## ⚙️ 最適化エンジンの状況")
add()
for account, path in (("skin", "skin/skin_optimization_index.json"),
                      ("ronin", "ronin/ronin_optimization_index.json")):
    index_data = load_json(path) or {}
    phase = index_data.get("analysis_phase", "不明")
    status = index_data.get("status", "")
    ranking_count = len(index_data.get("pattern_ranking", []))
    add(f"- **{account}**: フェーズ `{phase}` / 高反応パターン {ranking_count}件 — {status}")
add()

# ===== 気づき・注意（自動判定）==============================================
# 反応がずっと0のものを注意に入れる
if skin_reaction_sum == 0 and len(skin_posts_history) > 0:
    alerts.append("ℹ️ skin Threads は計測中だが反応がまだ0（フォロワー増加フェーズ）")
if not ronin_posts_history:
    alerts.append("ℹ️ ronin Threads は反応データ未取得（`ronin_data_collector.py` が動いているか確認）")
if latest_followers == 0:
    alerts.append("ℹ️ skin Instagram のフォロワー記録が0（insights権限の申請待ちが影響している可能性）")

add("## 💡 気づき・注意")
add()
if alerts:
    for alert in alerts:
        add(f"- {alert}")
else:
    add("- 特になし（全プラットフォーム正常に稼働中）")
add()

# ===== 横断サマリー表を本文の先頭近くに差し込む =============================
table_lines = []
table_lines.append("## 📋 横断サマリー")
table_lines.append("")
table_lines.append("| アカウント | プラットフォーム | 累計投稿 | 最終投稿 | 反応/フォロワー |")
table_lines.append("|---|---|---|---|---|")
for account, platform, posts, last_text, reaction_note in summary_rows:
    table_lines.append(f"| {account} | {platform} | {posts} | {last_text} | {reaction_note} |")
table_lines.append("")

# 「生成日時」の説明文の後ろ（先頭の見出しブロックの直後）に表を入れる
insert_at = 6  # タイトル+空行+生成日時+空行+説明+空行 の後ろ（skin見出しの直前）
final_lines = lines[:insert_at] + table_lines + lines[insert_at:]

# ===== ファイルに書き出す ====================================================
output_path = BASE / "dashboard.md"
output_path.write_text("\n".join(final_lines) + "\n", encoding="utf-8")

# 実行した人にも結果を一言知らせる
print(f"✅ dashboard.md を作成しました → {output_path}")
print(f"   プラットフォーム {len(summary_rows)}件 / 気づき {len(alerts)}件")
