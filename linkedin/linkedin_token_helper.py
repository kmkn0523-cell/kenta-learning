#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn OAuth 2.0 トークン取得ヘルパー

使い方:
  python3 linkedin_token_helper.py --get-auth-url
  python3 linkedin_token_helper.py --exchange-code CODE
  python3 linkedin_token_helper.py --get-person-urn TOKEN
"""

import os
import sys
import json
import requests
import argparse
import urllib.parse
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv


# .env ファイルから環境変数を読み込む
load_dotenv()

# LinkedInの API エンドポイント
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
LINKEDIN_OAUTH_BASE = "https://www.linkedin.com/oauth/v2"


def get_auth_url():
    """
    OAuth 2.0 認可URLを生成する

    このURLをブラウザで開くと、LinkedInのログイン画面が出ます
    """
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/callback")

    if not client_id:
        print("エラー: LINKEDIN_CLIENT_ID が .env に設定されていません")
        sys.exit(1)

    # URLエンコード処理（標準ライブラリを使用）
    scope = "w_member_social"
    redirect_uri_encoded = urllib.parse.quote(redirect_uri, safe="")

    auth_url = (
        f"{LINKEDIN_OAUTH_BASE}/authorization?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri_encoded}&"
        f"scope={scope}"
    )

    print("=" * 80)
    print("ステップ 4: OAuth 2.0 認可URLを開く")
    print("=" * 80)
    print("\n以下のURLをブラウザで開いてください:\n")
    print(auth_url)
    print("\n" + "=" * 80)
    print("LinkedInで認可すると、以下のようなURLにリダイレクトされます:")
    print("http://localhost:8000/callback?code=XXXXXXX&state=XXXXX")
    print("\nURLの 'code=' の後ろの部分（XXXXXXX）をコピーしてください。")
    print("=" * 80)


def exchange_code_for_token(code):
    """
    認可コードをアクセストークンに交換する

    Args:
        code (str): ステップ4で取得した認可コード
    """
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/callback")

    if not client_id or not client_secret:
        print("エラー: LINKEDIN_CLIENT_ID または LINKEDIN_CLIENT_SECRET が .env に設定されていません")
        sys.exit(1)

    print("=" * 80)
    print("ステップ 5: 認可コードをアクセストークンに交換")
    print("=" * 80)
    print(f"\n認可コード: {code[:20]}...")
    print("トークンを取得中...\n")

    # トークンエンドポイントにリクエスト
    url = f"{LINKEDIN_OAUTH_BASE}/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"エラー: {e}")
        print(f"レスポンス: {response.text if response else 'No response'}")
        sys.exit(1)

    result = response.json()

    # トークン情報を抽出
    access_token = result.get("access_token")
    refresh_token = result.get("refresh_token")
    expires_in = result.get("expires_in", 5184000)  # デフォルト: 60日

    # エラーハンドリング：access_tokenが存在しない場合
    if not access_token:
        print("エラー: access_token が取得できませんでした")
        print(f"レスポンス: {json.dumps(result, indent=2, ensure_ascii=False)}")
        sys.exit(1)

    # 期限日時を計算（UTC タイムゾーン使用）
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    expires_at_str = expires_at.strftime("%Y/%m/%d")

    print("✓ トークン取得成功！\n")
    print("=" * 80)
    print("以下の情報を linkedin/linkedin_config.json に入力してください:")
    print("=" * 80)
    print(f"\naccess_token: {access_token}")
    print(f"refresh_token: {refresh_token}")
    print(f"access_token_expires_at: {expires_at_str}")
    print("\n次のステップで person_urn を取得します")
    print("=" * 80)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "expires_at": expires_at_str
    }


def get_person_urn(access_token):
    """
    LinkedInの個人ユーザーURNを取得する

    Args:
        access_token (str): ステップ5で取得したアクセストークン
    """
    print("=" * 80)
    print("ステップ 6: LinkedInユーザーURNを取得")
    print("=" * 80)
    print("\nユーザー情報を取得中...\n")

    # LinkedIn API で自分の情報を取得
    url = f"{LINKEDIN_API_BASE}/me"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"エラー: {e}")
        print(f"レスポンス: {response.text if response else 'No response'}")
        print("\nトークンが有効か確認してください")
        sys.exit(1)

    result = response.json()
    user_id = result.get("id")
    first_name = result.get("localizedFirstName", "")
    last_name = result.get("localizedLastName", "")

    if not user_id:
        print(f"エラー: ユーザーIDが見つかりません")
        print(f"レスポンス: {json.dumps(result, indent=2, ensure_ascii=False)}")
        sys.exit(1)

    person_urn = f"urn:li:person:{user_id}"

    print("✓ ユーザー情報取得成功！\n")
    print("=" * 80)
    print("以下の情報を linkedin/linkedin_config.json に入力してください:")
    print("=" * 80)
    print(f"\n名前: {first_name} {last_name}")
    print(f"person_urn: {person_urn}")
    print("\n= linkedin_config.json の設定が完了しました =")
    print("=" * 80)

    return {
        "user_id": user_id,
        "person_urn": person_urn,
        "first_name": first_name,
        "last_name": last_name
    }


def main():
    # コマンドライン引数を解析
    parser = argparse.ArgumentParser(
        description="LinkedIn OAuth 2.0 トークン取得ヘルパー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使い方:
  1. 認可URLを取得:
     python3 linkedin_token_helper.py --get-auth-url

  2. 認可コードからトークンを取得:
     python3 linkedin_token_helper.py --exchange-code YOUR_CODE_HERE

  3. ユーザーURNを取得:
     python3 linkedin_token_helper.py --get-person-urn YOUR_ACCESS_TOKEN_HERE
        """
    )

    parser.add_argument(
        "--get-auth-url",
        action="store_true",
        help="OAuth 2.0 認可URLを生成して表示"
    )
    parser.add_argument(
        "--exchange-code",
        type=str,
        help="認可コードをアクセストークンに交換"
    )
    parser.add_argument(
        "--get-person-urn",
        type=str,
        help="LinkedInユーザーURNを取得"
    )

    args = parser.parse_args()

    # ユーザーが何も指定していない場合、使い方を表示
    if not any([args.get_auth_url, args.exchange_code, args.get_person_urn]):
        parser.print_help()
        sys.exit(1)

    # それぞれのアクション実行
    if args.get_auth_url:
        get_auth_url()

    if args.exchange_code:
        exchange_code_for_token(args.exchange_code)

    if args.get_person_urn:
        get_person_urn(args.get_person_urn)


if __name__ == "__main__":
    main()
