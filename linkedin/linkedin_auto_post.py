# linkedin/linkedin_auto_post.py
# @RoninWords LinkedIn自動投稿スクリプト
# 使い方: python3 linkedin/linkedin_auto_post.py

import json                    # JSONファイルを扱う道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime  # 今の日時を取得する道具
import os                      # ファイル操作に使う道具
import sys                     # プログラム終了時に使う道具


def load_config():
    """LinkedIn設定ファイルを読み込む"""
    # linkedin_config.json から設定を読み込む
    try:
        with open('/home/kenta_kamijyo/linkedin/linkedin_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        # JSONの形式が壊れている場合のエラーハンドリング
        print(f"エラー: linkedin_config.json が破損しています - {e}")
        sys.exit(1)
    except FileNotFoundError:
        # ファイルが見つからない場合のエラーハンドリング
        print("エラー: linkedin_config.json が見つかりません")
        sys.exit(1)


def load_threads_posts():
    """Threads投稿データを読み込む（LinkedInでも流用する）"""
    # ronin/threads_posts.json から投稿データを読み込む
    try:
        with open('/home/kenta_kamijyo/ronin/threads_posts.json', 'r', encoding='utf-8') as f:
            # JSON形式: {"posts": [...]} または リストそのもの
            data = json.load(f)
            # どちらの形式にも対応
            if isinstance(data, dict) and "posts" in data:
                return data["posts"]
            else:
                return data
    except json.JSONDecodeError as e:
        # JSONの形式が壊れている場合のエラーハンドリング
        print(f"エラー: threads_posts.json が破損しています - {e}")
        sys.exit(1)
    except FileNotFoundError:
        # ファイルが見つからない場合のエラーハンドリング
        print("エラー: threads_posts.json が見つかりません")
        sys.exit(1)


def post_to_linkedin(text):
    """LinkedIn APIを使って実際に投稿する"""
    # 設定を読み込む
    config = load_config()

    # LinkedIn APIに必要な情報を取得する
    access_token = config['oauth']['access_token']
    person_urn = config['profile']['person_urn']

    # LinkedIn UGC Posts APIのエンドポイント
    url = "https://api.linkedin.com/v2/ugcPosts"

    # リクエストのヘッダー（APIに「これは誰からのリクエストか」「どんな形式か」を伝える）
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202404"
    }

    # LinkedInに送るデータを作成する
    payload = {
        "author": person_urn,                          # 投稿者のID
        "lifecycleState": "PUBLISHED",                 # すぐに公開する
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": text                        # 投稿文
                },
                "shareMediaCategory": "NONE"           # 画像や動画は使わない
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"  # 誰でも見られるように
        }
    }

    try:
        # LinkedInに投稿リクエストを送る
        response = requests.post(url, json=payload, headers=headers)

        # ステータスコード201は「投稿が成功した」という意味
        if response.status_code == 201:
            try:
                # レスポンスから投稿IDを取得する
                post_id = response.json()['id']
                print(f"LinkedIn投稿成功: {post_id}")
                return post_id
            except (json.JSONDecodeError, KeyError) as e:
                # レスポンスの形式が想定と異なる場合
                print(f"警告: レスポンスの形式が不正です - {e}")
                return None
        else:
            # エラーが起きた場合、安全なエラー情報を出力する（トークンを隠す）
            print(f"エラー: LinkedIn API が {response.status_code} を返しました")
            if response.status_code == 401:
                print("認証エラー: アクセストークンを確認してください")
            elif response.status_code == 403:
                print("権限エラー: LinkedInのアクセス権限がありません")
            elif response.status_code == 400:
                print("リクエストエラー: 送信データの形式が不正です")
            return None

    except requests.RequestException as e:
        # ネットワークエラーなど、リクエスト送信中のエラー
        print(f"ネットワークエラー: {e}")
        return None
    except Exception as e:
        # 予期しないエラーが起きた場合は出力する
        print(f"予期しないエラーが発生しました: {e}")
        return None


def select_post_for_linkedin():
    """Threads投稿から1つを選んでLinkedInに投稿する内容を作る"""
    # ronin/threads_posts.json から投稿データを読み込む
    posts = load_threads_posts()

    # 投稿データが空でないかを確認する（データ検証①）
    if not posts or len(posts) == 0:
        print("エラー: 投稿データが見つかりません")
        sys.exit(1)

    # 進捗ファイルを読み込む（どこまで投稿したか記録）
    progress_file = '/home/kenta_kamijyo/linkedin/linkedin_posting_progress.json'
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
    except json.JSONDecodeError:
        # JSONファイルが破損している場合は初期化する
        print("警告: 進捗ファイルが破損しています。初期化します。")
        progress = {'index': 0, 'history': []}
    except FileNotFoundError:
        # ファイルがない場合は初期値で始める
        progress = {'index': 0, 'history': []}

    # 現在の投稿インデックスを計算する（60日ローテーション）
    day_index = progress['index'] % len(posts)

    # Day01から順にローテーションする
    post = posts[day_index]

    # 朝の投稿を確認する（データ検証②：朝の投稿が存在するか）
    if 'morning' not in post:
        print(f"エラー: Day {post.get('day', '?')} に 'morning' フィールドがありません")
        sys.exit(1)

    # 朝の投稿を選ぶ（朝の方が詳しい内容）
    text = post['morning']

    # ハッシュタグセットA（基本的なハッシュタグ）を取得
    hashtags = post.get('hashtags_set_A', [])

    # 次の投稿用にインデックスを1つ進める
    progress['index'] += 1

    # 進捗をファイルに保存する
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)

    return text, hashtags


def main():
    """メイン処理：投稿を選んでLinkedInに送信する"""
    print("LinkedIn自動投稿を開始します")

    try:
        # Threads投稿データからLinkedIn投稿用テキストを選ぶ
        text, hashtags = select_post_for_linkedin()

        # テキストとハッシュタグを組み合わせて最終的な投稿文を作る
        full_text = text + '\n\n' + ' '.join(hashtags)

        # LinkedInの文字数制限（3000文字以内）をチェックする（データ検証③）
        if len(full_text) > 3000:
            print(f"警告: テキストが長すぎます ({len(full_text)} > 3000 文字)")
            print("一部を短縮します")
            # 2980文字で切って "..." を付ける（合計3000文字以内）
            full_text = full_text[:2980] + "..."

        # LinkedInに投稿する
        post_id = post_to_linkedin(full_text)

        # 結果を表示
        if post_id:
            print(f"✓ LinkedIn投稿成功: {post_id}")
        else:
            print("✗ LinkedIn投稿に失敗しました")

    except SystemExit:
        # sys.exit() で意図的に終了した場合は、そのまま終了
        pass
    except Exception as e:
        # 予期しないエラーが起きた場合は出力する
        print(f"予期しないエラーが発生しました: {e}")


# このファイルが直接実行されたときだけ main() を実行する
if __name__ == '__main__':
    main()
