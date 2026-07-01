# release_note.py
# note_queueフォルダから次の記事を取り出して note_ready.md に書き出すスクリプト
# GitHub Actions が毎週月曜 9:00 JST に自動実行する

import os        # ファイルの存在確認に使う道具
import json      # JSONファイルを読み書きする道具
import sys       # エラー時に終了コードを返す道具
from datetime import datetime  # 今日の日付を取得する道具
from note_dedup import already_posted_today  # 今日すでに投稿済みかを判定する共通関数

# ファイルのパス設定（このスクリプトがある場所を基準にする）
BASE_DIR      = os.path.dirname(__file__)                           # skinフォルダ
QUEUE_DIR     = os.path.join(BASE_DIR, "note_queue")               # 記事ストックフォルダ
PROGRESS_FILE = os.path.join(BASE_DIR, "note_queue_progress.json") # 進捗記録
READY_FILE    = os.path.join(BASE_DIR, "note_ready.md")            # 今週の記事


def load_progress():
    """進捗ファイルを読み込む（なければ0から開始）"""
    if not os.path.exists(PROGRESS_FILE):
        return {"next_index": 0}
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"next_index": 0}


def save_progress(next_index):
    """次に出す記事番号をファイルに保存する（既存のhistory配列は保持する）"""
    # 既存ファイルを読み込んでhistory配列を引き継ぐ（post_to_note.pyが書いた履歴を消さない）
    existing = load_progress()
    existing["next_index"] = next_index
    # history キーが無ければ空配列を入れておく（あれば中身は触らない）
    if "history" not in existing:
        existing["history"] = []
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


# note記事の末尾に足す、Threadsへの相互送客の一文。
# note読者をThreadsフォローにも誘導し、noteとThreads両方の流入を相互に増やす。
THREADS_FOOTER = "\n\n---\n\n📱 毎日の肌ケアのヒントはThreadsでも発信しています。よければ [@skin_reset_jp](https://www.threads.net/@skin_reset_jp) もフォローしてみてください。"


def append_threads_footer(article_content):
    """記事本文の末尾にThreads誘導の一文を足す純関数。二重付与を防ぐため、既に含まれていれば何もしない。"""
    if "threads.net/@skin_reset_jp" in article_content:
        return article_content
    return article_content + THREADS_FOOTER


def get_article_files():
    """note_queueフォルダにある記事ファイルを番号順で取得する"""
    if not os.path.exists(QUEUE_DIR):
        return []
    files = sorted([
        f for f in os.listdir(QUEUE_DIR)
        if f.startswith("article_") and f.endswith(".md")
    ])
    return files


def main():
    today = datetime.now().strftime("%Y/%m/%d")
    print(f"=== note週次リリース開始 ({today}) ===")

    # 記事ファイル一覧を取得する
    article_files = get_article_files()

    if not article_files:
        print("⚠️  note_queueフォルダに記事がありません。スキップします。")
        return  # エラーにはしない（GitHub Actionsを失敗させない）

    # 進捗を読み込む
    progress = load_progress()

    # 本日すでに投稿済みならスキップ（重複投稿防止）
    # GitHub ActionsのcronはキューにいたときのHEADをpinするため、
    # 別のジョブが先に動いても古いprogress.jsonを読むことがある。
    # ワークフロー側で最新mainを取り込んだ上で、historyに今日の投稿が
    # 1件でもあれば重複と判断してスキップする（末尾だけでなく全件を走査）。
    history = progress.get("history", [])
    if already_posted_today(history, today):
        print(f"✅ 本日（{today}）はすでに投稿済みのためスキップします（重複投稿防止）")
        todays = [entry for entry in history if entry.get("date", "").startswith(today)]
        if todays:
            last = todays[-1]
            print(f"   → 本日の投稿: {last.get('article')} ({last.get('date')})")
        return

    # 次の記事を決める（30本使い切ったら最初に戻る）
    next_index = progress["next_index"] % len(article_files)
    article_filename = article_files[next_index]
    article_path = os.path.join(QUEUE_DIR, article_filename)

    print(f"📄 今週の記事: {article_filename} ({next_index + 1}/{len(article_files)})")

    # 記事ファイルを読み込む
    try:
        with open(article_path, "r", encoding="utf-8") as f:
            article_content = f.read()
    except FileNotFoundError:
        print(f"❌ 記事ファイルが見つかりません: {article_path}")
        sys.exit(1)

    # note_ready.md に書き出す（日付ヘッダーとThreads誘導フッターを付加する）
    header = f"<!-- 自動生成: {today} | {article_filename} -->\n\n"
    output_content = header + append_threads_footer(article_content)

    with open(READY_FILE, "w", encoding="utf-8") as f:
        f.write(output_content)

    print(f"✅ note_ready.md を更新しました")
    print(f"   → 次のステップで post_to_note.py が自動投稿します")

    # 進捗を更新する（次回は次の記事）
    save_progress(next_index + 1)

    # 次回の記事を予告する
    next_next_index = (next_index + 1) % len(article_files)
    next_article = article_files[next_next_index]
    print(f"📅 来週の記事: {next_article}")
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
