#!/usr/bin/env python3
# linkedin/linkedin_analytics.py
# @RoninWords LinkedIn エンゲージメント分析スクリプト
# 使い方: python3 linkedin/linkedin_analytics.py

import json                    # JSONファイルを扱う道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime  # 今の日時を取得する道具
import sys                     # プログラム終了時に使う道具
import os                      # ファイル操作に使う道具


def load_config():
    """LinkedIn設定ファイルを読み込む関数"""
    # linkedin_config.json から OAuth情報などを読み込む
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


def get_post_analytics(post_id):
    """LinkedIn投稿のメトリクスを取得する関数（いいね・コメント・シェア）"""
    # 設定ファイルから OAuth情報を取得
    config = load_config()
    access_token = config['oauth']['access_token']

    # LinkedIn Analytics API のエンドポイント
    url = f"https://api.linkedin.com/v2/socialMetadata?q=posts&posts=List({post_id})"

    # APIリクエストのヘッダー（「これは誰からのリクエストか」をAPIに伝える）
    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": "202404"
    }

    try:
        # LinkedIn Analytics APIにリクエストを送る
        response = requests.get(url, headers=headers, timeout=10)

        # ステータスコード200は「成功」という意味
        if response.status_code == 200:
            # JSON形式のレスポンスを解析
            data = response.json()

            # DEBUG: APIレスポンスの構造をログに出力する（最初の500文字まで）
            print(f"DEBUG: LinkedIn API レスポンス構造: {json.dumps(data, indent=2)[:500]}")

            # APIレスポンスから各メトリクスを抽出（存在しない場合は0）
            likes = data.get('likeCount', 0)
            comments = data.get('commentCount', 0)
            shares = data.get('shareCount', 0)

            # 検証: すべてのメトリクスが0の場合、APIが正しいデータを返しているか確認
            if likes == 0 and comments == 0 and shares == 0:
                print(f"警告: post_id {post_id} のメトリクスがすべて 0 です。API が正しい形式を返しているか確認してください。")

            # エンゲージメントスコアを計算する（いいね×1.0 + コメント×2.5 + シェア×5.0）
            engagement_score = (likes * 1.0) + (comments * 2.5) + (shares * 5.0)

            # メトリクスをまとめた辞書を作成
            metrics = {
                "post_id": post_id,
                "date": datetime.now().isoformat(),
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "engagement_score": engagement_score
            }

            return metrics
        else:
            # エラーが起きた場合、ステータスコードを表示する
            print(f"エラー: LinkedIn API が {response.status_code} を返しました")

            # よくあるエラーの説明を表示する
            if response.status_code == 401:
                print("認証エラー: アクセストークンを確認してください")
            elif response.status_code == 403:
                print("権限エラー: LinkedInのアクセス権限がありません")
            elif response.status_code == 404:
                print("エラー: 指定の投稿が見つかりません")

            return None

    except requests.exceptions.Timeout:
        # リクエストがタイムアウトした場合のエラーハンドリング
        print("エラー: LinkedIn APIへのリクエストがタイムアウトしました")
        return None
    except requests.exceptions.RequestException as e:
        # ネットワークエラーなど、リクエスト送信中のエラー
        print(f"ネットワークエラー: {e}")
        return None
    except json.JSONDecodeError as e:
        # レスポンスのJSON形式が不正な場合のエラーハンドリング
        print(f"エラー: APIレスポンスの解析に失敗しました - {e}")
        return None
    except Exception as e:
        # 予期しないエラーが起きた場合は出力する
        print(f"予期しないエラーが発生しました: {e}")
        return None


def save_analytics(metrics):
    """メトリクスを linkedin_analytics.json に保存する関数"""
    # 既存のanalytics.jsonを読み込む（なければ新規作成）
    analytics_file = '/home/kenta_kamijyo/linkedin/linkedin_analytics.json'

    try:
        # 既存ファイルを読み込む
        with open(analytics_file, 'r', encoding='utf-8') as f:
            analytics = json.load(f)
    except FileNotFoundError:
        # ファイルがない場合は新規作成する
        analytics = {
            "last_updated": datetime.now().isoformat(),
            "posts_history": [],
            "summary": {}
        }
    except json.JSONDecodeError:
        # JSONファイルが破損している場合は初期化する
        print("警告: analytics ファイルが破損しています。再初期化します")
        analytics = {
            "last_updated": datetime.now().isoformat(),
            "posts_history": [],
            "summary": {}
        }

    # 既に分析済みの post_id をチェックする（重複検出）
    existing_index = None
    for i, entry in enumerate(analytics['posts_history']):
        if entry['post_id'] == metrics['post_id']:
            existing_index = i
            break

    # 既に分析済みの場合は更新、そうでなければ新規追加
    if existing_index is not None:
        # 既存エントリを新しいメトリクスに更新
        print(f"警告: post_id {metrics['post_id']} は既に分析されています。メトリクスを更新します。")
        analytics['posts_history'][existing_index] = metrics
    else:
        # メトリクスをhistoryに追加する
        analytics['posts_history'].append(metrics)

    # 最終更新時刻を今の時刻に更新
    analytics['last_updated'] = datetime.now().isoformat()

    # ファイルに保存する
    try:
        with open(analytics_file, 'w', encoding='utf-8') as f:
            # indent=2は見やすくするためのインデント、ensure_ascii=Falseは日本語対応
            json.dump(analytics, f, indent=2, ensure_ascii=False)
        print(f"✓ Analytics 保存完了: {metrics['post_id']}")
        return True  # 成功を示す
    except Exception as e:
        # ファイル保存時のエラーハンドリング
        print(f"エラー: Analytics を保存できませんでした - {e}")
        return False  # 失敗を示す


def get_latest_post_id():
    """進捗ファイルから最新投稿IDを取得する関数"""
    # linkedin_posting_progress.json から最新投稿IDを取得
    progress_file = '/home/kenta_kamijyo/linkedin/linkedin_posting_progress.json'

    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)

        # history が存在して空でない場合は最新のIDを取得
        if 'history' in progress and len(progress['history']) > 0:
            # history リスト内で最後の要素が最新の投稿
            latest_post = progress['history'][-1]
            if 'post_id' in latest_post:
                return latest_post['post_id']

        # history がない場合、または post_id がない場合は警告
        print("警告: 投稿 ID が記録されていません")
        return None

    except FileNotFoundError:
        # ファイルが見つからない場合のエラーハンドリング
        print("エラー: linkedin_posting_progress.json が見つかりません")
        return None
    except json.JSONDecodeError:
        # JSONが破損している場合のエラーハンドリング
        print("エラー: linkedin_posting_progress.json が破損しています")
        return None
    except Exception as e:
        # 予期しないエラーのハンドリング
        print(f"エラー: {e}")
        return None


def main():
    """メイン処理：最新投稿のメトリクスを取得・保存する"""
    print("LinkedIn Analytics を開始します")

    # 最新投稿の ID を取得
    post_id = get_latest_post_id()

    if not post_id:
        print("失敗: 投稿 ID を取得できませんでした")
        return False

    # 投稿のメトリクスを取得
    print(f"投稿 {post_id} のメトリクスを取得中...")
    metrics = get_post_analytics(post_id)

    if metrics:
        # メトリクスを analytics.json に保存（戻り値をチェック）
        success = save_analytics(metrics)

        if success:
            # 保存成功
            print(f"成功: {post_id} のメトリクスを保存しました")
            print(f"  - いいね: {metrics['likes']}")
            print(f"  - コメント: {metrics['comments']}")
            print(f"  - シェア: {metrics['shares']}")
            print(f"  - スコア: {metrics['engagement_score']}")
            return True
        else:
            # 保存失敗
            print(f"失敗: {post_id} のメトリクスを保存できませんでした")
            return False
    else:
        # メトリクス取得失敗
        print("失敗: メトリクスを取得できませんでした")
        return False


# このファイルが直接実行されたときだけ main() を実行する
if __name__ == '__main__':
    main()
