# ronin_threads_setup.py
# @RoninWordsのThreads API用に「長期トークン」と「USER_ID」を取得するスクリプト
# 使い方: python3 ronin_threads_setup.py

import os                       # 環境変数を読み込む道具
import requests                 # インターネットにリクエストを送る道具
from dotenv import load_dotenv  # .envファイルからキーを読み込む道具

# .envファイルを読み込む
load_dotenv()

# .envから必要な情報を取り出す
SHORT_TOKEN = os.getenv("RONIN_THREADS_TOKEN_SHORT")  # さっき貼った短期トークン
APP_SECRET  = os.getenv("THREADS_APP_SECRET")          # skin用に取得済みのアプリシークレット（同じアプリなので使い回せる）


def exchange_to_long_lived_token(short_token, app_secret):
    """
    短期トークン（1時間有効）を長期トークン（60日有効）に変換する
    """
    url = "https://graph.threads.net/access_token"
    params = {
        "grant_type": "th_exchange_token",  # 「長期トークンに交換したい」という意思表示
        "client_secret": app_secret,         # アプリのシークレット（本人確認用）
        "access_token": short_token          # 変換したい短期トークン
    }
    response = requests.get(url, params=params)
    return response.json()


def get_user_id(access_token):
    """
    アクセストークンを使って、自分のThreadsアカウントのUSER_IDとユーザー名を取得する
    """
    url = "https://graph.threads.net/v1.0/me"
    params = {
        "fields": "id,username",       # IDとユーザー名を返してもらう
        "access_token": access_token   # 認証キー
    }
    response = requests.get(url, params=params)
    return response.json()


def main():
    print("=" * 50)
    print("@RoninWords Threads API セットアップ")
    print("=" * 50)

    # 必要な情報がそろっているか確認する
    if not SHORT_TOKEN:
        print("❌ エラー: .envに RONIN_THREADS_TOKEN_SHORT が見つかりません")
        return
    if not APP_SECRET:
        print("❌ エラー: .envに THREADS_APP_SECRET が見つかりません")
        return

    # ステップ1: 短期 → 長期トークンに変換する
    print("\n[1/2] 短期トークンを長期トークン（60日有効）に変換中...")
    long_token_data = exchange_to_long_lived_token(SHORT_TOKEN, APP_SECRET)

    if "access_token" not in long_token_data:
        print(f"❌ 変換失敗: {long_token_data}")
        return

    long_token = long_token_data["access_token"]
    expires_in = long_token_data.get("expires_in", "不明")
    print(f"✅ 長期トークン取得成功！（有効期限: {expires_in}秒 ≒ {int(expires_in)/86400:.0f}日）")

    # ステップ2: 長期トークンを使ってUSER_IDを取得する
    print("\n[2/2] @RoninWordsのUSER_IDを取得中...")
    user_data = get_user_id(long_token)

    if "id" not in user_data:
        print(f"❌ USER_ID取得失敗: {user_data}")
        return

    user_id  = user_data["id"]
    username = user_data.get("username", "不明")
    print(f"✅ USER_ID取得成功！")
    print(f"   ユーザー名: @{username}")
    print(f"   USER_ID: {user_id}")

    # 結果をまとめて表示する（.envに貼り付けるための文字列）
    print("\n" + "=" * 50)
    print("📋 .envに以下の2行を追記してください:")
    print("=" * 50)
    print(f"RONIN_THREADS_ACCESS_TOKEN={long_token}")
    print(f"RONIN_THREADS_USER_ID={user_id}")
    print("=" * 50)
    print("\n⚠️  追記後は RONIN_THREADS_TOKEN_SHORT の行は削除してOK（もう不要）")


if __name__ == "__main__":
    main()
