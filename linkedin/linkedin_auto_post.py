# linkedin/linkedin_auto_post.py
# @RoninWords LinkedIn自動投稿スクリプト
# 使い方: python3 linkedin/linkedin_auto_post.py

import json                    # JSONファイルを扱う道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime  # 今の日時を取得する道具
import os                      # ファイル操作に使う道具


def load_config():
    """LinkedIn設定ファイルを読み込む"""
    # linkedin_config.json から設定を読み込む
    with open('/home/kenta_kamijyo/linkedin/linkedin_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def load_threads_posts():
    """Threads投稿データを読み込む（LinkedInでも流用する）"""
    # ronin/threads_posts.json から投稿データを読み込む
    with open('/home/kenta_kamijyo/ronin/threads_posts.json', 'r', encoding='utf-8') as f:
        # JSON形式: {"posts": [...]} または リストそのもの
        data = json.load(f)
        # どちらの形式にも対応
        if isinstance(data, dict) and "posts" in data:
            return data["posts"]
        else:
            return data


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
            post_id = response.json()['id']
            print(f"LinkedIn投稿成功: {post_id}")
            return post_id
        else:
            # エラーが起きた場合、エラー内容を出力する
            print(f"LinkedIn投稿エラー: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        # 予期しないエラーが起きた場合は出力する
        print(f"例外エラー: {e}")
        return None


def select_post_for_linkedin():
    """Threads投稿から1つを選んでLinkedInに投稿する内容を作る"""
    # ronin/threads_posts.json から投稿データを読み込む
    posts = load_threads_posts()

    # 進捗ファイルを読み込む（どこまで投稿したか記録）
    progress_file = '/home/kenta_kamijyo/linkedin/linkedin_posting_progress.json'
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
    except FileNotFoundError:
        # ファイルがない場合は初期値で始める
        progress = {'index': 0, 'history': []}

    # 現在の投稿インデックスを計算する（60日ローテーション）
    day_index = progress['index'] % len(posts)

    # Day01から順にローテーションする
    post = posts[day_index]

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

        # LinkedInに投稿する
        post_id = post_to_linkedin(full_text)

        # 結果を表示
        if post_id:
            print(f"✓ LinkedIn投稿成功: {post_id}")
        else:
            print("✗ LinkedIn投稿に失敗しました")

    except Exception as e:
        # エラーが起きた場合は出力
        print(f"エラーが発生しました: {e}")


# このファイルが直接実行されたときだけ main() を実行する
if __name__ == '__main__':
    main()
