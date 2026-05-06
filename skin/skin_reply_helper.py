# skin_reply_helper.py
# 自分の投稿にコメントしてくれた人への返信ヘルパー
# 使い方: python3 skin/skin_reply_helper.py

import os
import json
import random
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# .envからAPIキーを読み込む
load_dotenv("/home/kenta_kamijyo/.env")
TOKEN      = os.getenv("THREADS_ACCESS_TOKEN")
USER_ID    = os.getenv("THREADS_USER_ID")
MY_ACCOUNT = "skin_reset_jp"  # 自分のアカウント名（自分のコメントを除外するため）

JST = timezone(timedelta(hours=9))  # 日本時間に変換するための設定

# -----------------------------------------------
# 返信テンプレート集（コメント内容のキーワードで分類）
# -----------------------------------------------
REPLY_TEMPLATES = {

    "共感・体験談": [
        "同じ経験をしてきたので、すごく共感します。内側から変えると本当に変わりますよね。",
        "嬉しいコメントありがとうございます。一緒に改善していきましょう！",
        "コメントありがとうございます。同じ悩みを持つ方に届いて良かったです。",
        "体験を教えてくださってありがとうございます。実体験が一番の証拠ですよね。",
        "共感してもらえると励みになります。これからも役立つ情報を発信していきます！",
    ],

    "質問・相談": [
        "ご質問ありがとうございます。まず食事と睡眠の見直しから始めるのが一番効果を実感しやすいです。",
        "個人差はありますが、食事を変えてから2〜4週間で体感が出始める方が多いです。",
        "それぞれのタイプによって優先順位が変わります。まず自分のタイプを確認してみてください。",
        "コメントありがとうございます。詳しくはnoteにまとめているので、良ければ見てみてください。",
        "良い質問ですね。試してみた結果をまた教えてもらえると嬉しいです！",
    ],

    "試してみる・やってみる": [
        "ぜひ試してみてください！2週間続けると体感が出やすいです。",
        "まず1つだけ変えてみるのがコツです。全部一気にやると続かないので。",
        "試した結果をぜひコメントで教えてください。応援しています！",
        "小さな変化でも気づいたらまた教えてください。その積み重ねが大事です。",
        "継続が一番大切です。焦らずゆっくり変えていきましょう！",
    ],

    "変化・改善した": [
        "変化が出てきたんですね。それが一番嬉しいコメントです！",
        "続けてきた結果が出てきましたね。この調子で続けてください！",
        "変化を教えてくださってありがとうございます。本当に嬉しいです。",
        "肌が変わると気持ちも変わりますよね。このまま続けていきましょう！",
        "素晴らしいです。その調子で続けると、さらに変化が出てくるはずです。",
    ],

    "汎用（どのコメントにも使える）": [
        "コメントありがとうございます。参考になれば嬉しいです！",
        "読んでくださってありがとうございます。これからも役立つ情報を発信していきます。",
        "温かいコメントありがとうございます。励みになります！",
        "コメントありがとうございます。引き続きよろしくお願いします。",
        "ありがとうございます。ぜひ試してみて、変化を教えてもらえると嬉しいです。",
    ],
}

# -----------------------------------------------
# APIを使った処理
# -----------------------------------------------

def get_recent_posts(limit=10):
    """自分の最新投稿を取得する"""
    r = requests.get(
        f"https://graph.threads.net/v1.0/{USER_ID}/threads",
        params={"fields": "id,text,timestamp", "limit": limit, "access_token": TOKEN}
    )
    return r.json().get("data", [])


def get_replies(post_id):
    """指定した投稿へのコメントを取得する（自分の返信は除外）"""
    r = requests.get(
        f"https://graph.threads.net/v1.0/{post_id}/replies",
        params={"fields": "id,text,username,timestamp", "access_token": TOKEN}
    )
    all_replies = r.json().get("data", [])

    # 自分のアカウントのコメントは除外する（スレッド継続投稿など）
    other_replies = [rep for rep in all_replies if rep.get("username") != MY_ACCOUNT]
    return other_replies


def post_reply(reply_to_id, text):
    """指定したコメントIDに返信を送る（2段階）"""

    # ステップ1: 返信コンテナを作成
    r1 = requests.post(
        f"https://graph.threads.net/v1.0/{USER_ID}/threads",
        params={
            "media_type": "TEXT",
            "text": text,
            "reply_to_id": reply_to_id,
            "access_token": TOKEN
        }
    )
    data1 = r1.json()
    if "id" not in data1:
        return False, f"コンテナ作成失敗: {data1}"

    # ステップ2: コンテナを公開（実際に送信）
    r2 = requests.post(
        f"https://graph.threads.net/v1.0/{USER_ID}/threads_publish",
        params={"creation_id": data1["id"], "access_token": TOKEN}
    )
    data2 = r2.json()
    if "id" not in data2:
        return False, f"送信失敗: {data2}"

    return True, data2["id"]

# -----------------------------------------------
# 返信候補を生成する
# -----------------------------------------------

def suggest_replies(comment_text):
    """コメントの内容を見てカテゴリーを選び、返信候補を5つ返す"""

    text = comment_text.lower()

    # キーワードでカテゴリーを判定する
    if any(w in text for w in ["?", "？", "どうすれば", "教えて", "なぜ", "いつ", "どのくらい", "何を"]):
        category = "質問・相談"
    elif any(w in text for w in ["変わった", "変わってき", "改善", "治った", "良くなった", "減った", "消えた", "効果出"]):
        category = "変化・改善した"
    elif any(w in text for w in ["試して", "やってみ", "始め", "挑戦"]):
        category = "試してみる・やってみる"
    elif any(w in text for w in ["同じ", "わかる", "共感", "そうです", "まさに"]):
        category = "共感・体験談"
    else:
        category = "汎用（どのコメントにも使える）"

    templates = REPLY_TEMPLATES[category]
    candidates = random.sample(templates, min(5, len(templates)))

    # 他カテゴリーから1〜2個追加してバリエーションを増やす
    other_categories = [k for k in REPLY_TEMPLATES if k != category]
    for cat in random.sample(other_categories, min(2, len(other_categories))):
        if len(candidates) < 5:
            extra = random.choice(REPLY_TEMPLATES[cat])
            if extra not in candidates:
                candidates.append(extra)

    return candidates[:5], category

# -----------------------------------------------
# 表示ヘルパー
# -----------------------------------------------

def format_time(timestamp_str):
    """ISO形式の時刻を日本時間で読みやすく変換する"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("+0000", "+00:00"))
        jst_dt = dt.astimezone(JST)
        return jst_dt.strftime("%m/%d %H:%M")
    except Exception:
        return timestamp_str

# -----------------------------------------------
# メイン処理
# -----------------------------------------------

def main():
    print("\n" + "=" * 55)
    print("  skin 返信ヘルパー")
    print("  コメントしてくれた人への返信を半自動化します")
    print("=" * 55)

    if not TOKEN or not USER_ID:
        print("❌ .envにTHREADS_ACCESS_TOKENとTHREADS_USER_IDを設定してください")
        return

    # 最新投稿を取得する
    print("\n最新投稿を取得中...")
    posts = get_recent_posts(limit=10)

    if not posts:
        print("投稿が見つかりませんでした")
        return

    # コメントがある投稿だけを集める
    posts_with_comments = []
    print("コメントを確認中...", end="", flush=True)
    for post in posts:
        replies = get_replies(post["id"])
        if replies:
            posts_with_comments.append({"post": post, "replies": replies})
        print(".", end="", flush=True)
    print()

    if not posts_with_comments:
        print("\n📭 他のユーザーからのコメントはまだありません")
        print("投稿を続けて、コメントが来たらまた実行してください。")
        return

    # コメントがある投稿を一覧表示する
    print(f"\n💬 コメントがある投稿: {len(posts_with_comments)} 件\n")
    for i, item in enumerate(posts_with_comments, 1):
        post    = item["post"]
        replies = item["replies"]
        print(f"  [{i}] {post['text'][:40]}...")
        print(f"       コメント数: {len(replies)}件")
        print()

    print("  [0] 終了")

    # 投稿を選択してコメントに返信する
    while True:
        choice = input("\n返信したい投稿番号を入力: ").strip()

        if choice == "0":
            print("終了します。お疲れ様でした！")
            break

        try:
            idx = int(choice) - 1
            if not (0 <= idx < len(posts_with_comments)):
                print("番号が正しくありません")
                continue
        except ValueError:
            print("番号を入力してください")
            continue

        item    = posts_with_comments[idx]
        post    = item["post"]
        replies = item["replies"]

        print(f"\n📝 投稿: {post['text'][:60]}...")
        print("-" * 55)

        # コメントを一覧表示する
        for j, rep in enumerate(replies, 1):
            print(f"\n  [{j}] @{rep['username']} ({format_time(rep['timestamp'])})")
            print(f"      {rep['text']}")

        comment_choice = input("\n返信するコメント番号（戻るなら0）: ").strip()

        if comment_choice == "0":
            continue

        try:
            cidx = int(comment_choice) - 1
            if not (0 <= cidx < len(replies)):
                print("番号が正しくありません")
                continue
        except ValueError:
            print("番号を入力してください")
            continue

        selected_comment = replies[cidx]

        # 返信候補を生成する
        candidates, detected_category = suggest_replies(selected_comment["text"])

        print(f"\n🤖 検出カテゴリー: {detected_category}")
        print("返信候補:\n")
        for k, candidate in enumerate(candidates, 1):
            print(f"  [{k}] {candidate}")
        print(f"\n  [c] 自分で入力する")
        print(f"  [r] 別の候補を出す")
        print(f"  [0] 戻る")

        while True:
            reply_choice = input("\n使う返信の番号: ").strip()

            if reply_choice == "0":
                break
            elif reply_choice == "r":
                candidates, detected_category = suggest_replies(selected_comment["text"])
                print("\n新しい返信候補:\n")
                for k, candidate in enumerate(candidates, 1):
                    print(f"  [{k}] {candidate}")
                continue
            elif reply_choice == "c":
                custom = input("返信内容を入力してください: ").strip()
                if not custom:
                    print("内容が空です")
                    continue
                reply_text = custom
            else:
                try:
                    ridx = int(reply_choice) - 1
                    if not (0 <= ridx < len(candidates)):
                        print("番号が正しくありません")
                        continue
                    reply_text = candidates[ridx]
                except ValueError:
                    print("番号を入力してください")
                    continue

            # 送信確認
            print(f"\n送信内容: {reply_text}")
            confirm = input("この内容で返信しますか？(y/n): ").strip().lower()

            if confirm != "y":
                print("キャンセルしました")
                break

            # 実際に返信を送る
            print("送信中...")
            success, result = post_reply(selected_comment["id"], reply_text)

            if success:
                print(f"✅ 返信しました！（ID: {result}）")
            else:
                print(f"❌ 失敗: {result}")

            break


if __name__ == "__main__":
    main()
