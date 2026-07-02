# ronin_x_action.py
# @RoninWords用 GitHub Actions専用の X（旧Twitter）自動投稿スクリプト（対話なし・全自動）
# 使い方: python3 ronin_x_action.py（GitHub Actionsから自動実行される）
#
# ⚠️ 現在は「準備実装」のみ。X APIの有料クレジットをユーザーがチャージするまで
#    実際の投稿は行わない。RONIN_X_* のAPIキーが1つでも未設定なら、
#    APIに一切触れずスキップして正常終了する（exit 0）。

import json        # JSONファイルを扱う道具
import os          # 環境変数を読み込む道具
from datetime import datetime  # 今の日時を取得する道具

# ローカル実行時は .env ファイルからAPIキーを読み込む（GitHub Actionsでは不要）
try:
    from dotenv import load_dotenv
    load_dotenv("/home/kenta_kamijyo/.env")
except ImportError:
    pass  # dotenvがなくても動くようにする

# 環境変数からXのAPIキーを読み込む（GitHub Actionsのsecretsから渡される）
# 4つとも揃っていない間は has_all_credentials() がFalseを返し、投稿処理に進まない
API_KEY             = os.environ.get("RONIN_X_API_KEY")
API_SECRET          = os.environ.get("RONIN_X_API_SECRET")
ACCESS_TOKEN        = os.environ.get("RONIN_X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("RONIN_X_ACCESS_SECRET")

# 投稿データと進捗ファイルのパス（GitHub Actionsはroninフォルダで実行する）
POSTS_FILE    = "ronin_x_posts.json"
PROGRESS_FILE = "ronin_x_progress.json"

# 全投稿の末尾に追加するハッシュタグ（英語アカウントなので英語タグ）
HASHTAGS = "\n\n#Bushido #SamuraiWisdom"


def has_all_credentials():
    """XのAPIキー4つが全部そろっているか確認する（1つでも欠けていたらFalse）"""
    return all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET])


def connect_to_x():
    """XのAPIに接続してクライアントを返す
    tweepyはここで初めてimportする（未インストールの環境でもスキップ経路が壊れないように）"""
    import tweepy  # XのAPIを使うための道具
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET
    )
    return client


def load_posts():
    """投稿データをJSONファイルから読み込む"""
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_progress():
    """進捗ファイルを読み込む（なければ初期値で始める）"""
    if not os.path.exists(PROGRESS_FILE):
        return {"daily_index": 0, "history": []}
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(progress):
    """進捗をファイルに保存する"""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def pick_post(daily_posts, index):
    """ローテーションで今回投稿する1件を選ぶ（indexが配列の外でも安全に循環する）
    戻り値は (実際に使ったindex, 選ばれた投稿) のタプル"""
    safe_index = index % len(daily_posts)
    return safe_index, daily_posts[safe_index]


def next_daily_index(index, total):
    """次回のdaily_indexを計算する（末尾まで行ったら0に戻る）"""
    return (index + 1) % total


def build_full_text(content, hashtags=HASHTAGS):
    """投稿本文の末尾にハッシュタグを付ける。
    280字（Xの文字数上限）を超える場合はハッシュタグ無しの本文だけを返す"""
    full_text = content + hashtags
    if len(full_text) > 280:
        return content
    return full_text


def main():
    """メイン処理（全自動・対話なし）
    APIキーが未設定ならAPIに一切触れず正常終了する（クレジットチャージ前の安全装置）"""
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    print(f"=== ronin X自動投稿開始: {now} ===")

    if not has_all_credentials():
        print("⚠️ RONIN_X_* のAPIキーが未設定のためスキップします（未設定のためスキップ）")
        print("   X APIの有料クレジットをチャージし、GitHub SecretsにRONIN_X_*を登録すると有効化されます")
        print("=== 完了（スキップ） ===")
        return  # 呼び出し元（GitHub Actions）から見ると正常終了（exit 0）

    # Xに接続する
    print("Xに接続中...")
    client = connect_to_x()
    print("✅ 接続成功！")

    # 投稿データと進捗を読み込む
    posts    = load_posts()
    progress = load_progress()

    daily_posts = posts["daily_posts"]

    # ローテーションで今回の投稿を選ぶ（20種を繰り返す）
    index, post = pick_post(daily_posts, progress.get("daily_index", 0))

    print(f"投稿: {index + 1}/{len(daily_posts)} ({post['type']})")

    # 投稿テキストを組み立てる（280字を超えたらハッシュタグなしになる）
    full_text = build_full_text(post["content"])
    if full_text == post["content"]:
        print("  ※ 文字数オーバーのためハッシュタグなしで投稿します")

    print(f"\n投稿内容（先頭50文字）: {full_text[:50]}...")

    # Xに投稿する
    response = client.create_tweet(text=full_text)
    tweet_id = response.data["id"]
    print(f"✅ 投稿成功！（ツイートID: {tweet_id}）")

    # 次の投稿番号に進める（20種を超えたら0に戻る）
    progress["daily_index"] = next_daily_index(index, len(daily_posts))
    next_post = daily_posts[progress["daily_index"]]
    print(f"次回: {next_post['type']}")

    # 履歴に記録する
    progress.setdefault("history", [])
    progress["history"].append({
        "date": now,
        "type": post["type"],
        "tweet_id": tweet_id
    })

    save_progress(progress)
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
