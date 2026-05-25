# notify_threads_of_note.py
# note記事が公開された直後にThreadsへ告知投稿するスクリプト
# skin_note_release.yml ワークフローから post_to_note.py の直後に呼ばれる
#
# 必要な環境変数:
#   - THREADS_ACCESS_TOKEN: Threads Graph API のアクセストークン
#   - THREADS_USER_ID: Threads ユーザーID
#   - NOTE_POST_STATUS (任意): "success" のときだけ告知する
#   - NOTE_DRAFT_MODE (任意): "true" のときはスキップ（下書きモードでは告知しない）

import os                            # 環境変数を読み取る道具
import re                            # 正規表現で文字列を切り出す道具
import sys                           # 異常終了用
import json                          # JSONファイルを読み書きする道具
import requests                      # HTTPリクエストを送る道具
from pathlib import Path             # ファイルパスを扱う道具

# Threads APIの認証情報を環境変数から読み込む
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_USER_ID = os.getenv("THREADS_USER_ID")

# 投稿履歴ファイルのパス
PROGRESS_FILE = Path(__file__).parent / "note_queue_progress.json"

# noteの公開URLを組み立てるためのユーザー名
NOTE_USERNAME = "neima"


def build_public_note_url(post_url: str) -> str:
    """投稿後URLからnote IDを抜き出して公開URLを組み立てる

    post_to_note.py が記録するURLは editor.note.com/notes/{id}/publish/ 形式。
    これを https://note.com/{username}/n/{id} 形式に変換する。
    """
    # /notes/{id} もしくは /n/{id} の id を取得する
    match = re.search(r"/(?:notes|n)/([A-Za-z0-9]+)", post_url)
    if not match:
        return post_url  # 形式が想定外ならそのまま返す
    note_id = match.group(1)
    return f"https://note.com/{NOTE_USERNAME}/n/{note_id}"


def load_latest_history():
    """note_queue_progress.json から最新の投稿履歴を取り出す"""
    if not PROGRESS_FILE.exists():
        print(f"❌ {PROGRESS_FILE} が見つかりません")
        sys.exit(1)
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        progress = json.load(f)
    history = progress.get("history", [])
    if not history:
        print("❌ historyが空です")
        sys.exit(1)
    return history[-1]  # 最後のエントリ＝今回公開した記事


def build_announcement_text(title: str, public_url: str) -> str:
    """Threads告知用の文章を組み立てる

    Threadsの本文上限は500文字。URLは末尾に置いて確実にプレビューさせる。
    """
    # タイトルが長すぎたら冒頭部分のみ使う（本文を圧迫しないため）
    short_title = title if len(title) <= 60 else title[:57] + "..."

    body = (
        f"📝 新しいnoteを公開しました\n\n"
        f"『{short_title}』\n\n"
        f"肌のことを根本から変えたい人向けに書いてます。\n"
        f"無料なので気軽に読んでみてください👇\n\n"
        f"{public_url}\n\n"
        f"#スキンケア #美肌 #note"
    )
    return body


def post_to_threads(text: str):
    """Threads Graph APIで投稿する（コンテナ作成→公開の2ステップ）"""
    # ステップ1: 投稿コンテナを作成する
    container_url = f"https://graph.threads.net/{THREADS_USER_ID}/threads"
    container_params = {
        "media_type": "TEXT",
        "text": text,
        "access_token": THREADS_ACCESS_TOKEN,
    }
    container_response = requests.post(container_url, params=container_params)
    container_data = container_response.json()
    if "id" not in container_data:
        return False, f"コンテナ作成失敗: {container_data}"

    creation_id = container_data["id"]

    # コンテナ作成直後に publish するとメディアIDが見つからないエラーになることがある
    # 5秒待ってから公開することで OAuthException 4279009 を防ぐ
    import time
    time.sleep(5)

    # ステップ2: コンテナを公開する
    publish_url = f"https://graph.threads.net/{THREADS_USER_ID}/threads_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": THREADS_ACCESS_TOKEN,
    }
    publish_response = requests.post(publish_url, params=publish_params)
    publish_data = publish_response.json()
    if "id" not in publish_data:
        return False, f"公開失敗: {publish_data}"

    return True, publish_data["id"]


def main():
    # 下書きモードでは告知しない
    if os.getenv("NOTE_DRAFT_MODE", "").lower() == "true":
        print("🧪 下書きモードのためThreads告知はスキップ")
        return

    # noteの投稿自体が失敗していたら告知しない
    note_status = os.getenv("NOTE_POST_STATUS", "")
    if note_status and note_status != "success":
        print(f"⚠️ note投稿が成功していないため告知スキップ (status={note_status})")
        return

    # 認証情報が無ければ何もしない（ローカル実行などで誤爆させない）
    if not THREADS_ACCESS_TOKEN or not THREADS_USER_ID:
        print("❌ THREADS_ACCESS_TOKEN / THREADS_USER_ID が未設定")
        sys.exit(1)

    # 最新の投稿履歴を取得する
    latest = load_latest_history()
    title = latest.get("title", "")
    post_url = latest.get("post_url", "")
    print(f"📌 告知対象: {title}")
    print(f"🔗 元URL: {post_url}")

    # editor URL → 公開URLに変換する
    public_url = build_public_note_url(post_url)
    print(f"🌐 公開URL: {public_url}")

    # 告知文を組み立ててThreadsに投稿する
    text = build_announcement_text(title, public_url)
    print(f"📝 投稿本文 ({len(text)}文字):\n{text}")

    success, result = post_to_threads(text)
    if success:
        print(f"✅ Threads告知投稿完了 (ID: {result})")
    else:
        print(f"❌ Threads告知失敗: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
