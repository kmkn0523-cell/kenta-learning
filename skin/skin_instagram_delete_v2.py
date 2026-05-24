"""
skin Instagram 投稿削除スクリプト（v2.1 カルーセル再投稿用）
- 最近の投稿一覧を取得し、CAROUSEL_ALBUM タイプのものだけを削除候補にする
- 削除前に確認表示、--yes 指定で実削除
使い方:
  python3 skin/skin_instagram_delete_v2.py           # 一覧のみ
  python3 skin/skin_instagram_delete_v2.py --yes     # 削除実行（直近8件のカルーセル）
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

ACCESS_TOKEN = os.getenv("SKIN_INSTAGRAM_ACCESS_TOKEN")
USER_ID      = os.getenv("SKIN_INSTAGRAM_USER_ID")
TARGET_COUNT = 8  # 削除する直近カルーセル数

def list_recent_media(limit=25):
    url = f"https://graph.facebook.com/v19.0/{USER_ID}/media"
    params = {
        "fields":       "id,media_type,timestamp,permalink,caption",
        "limit":        limit,
        "access_token": ACCESS_TOKEN,
    }
    r = requests.get(url, params=params, timeout=30)
    return r.json().get("data", [])

def delete_media(media_id: str):
    url = f"https://graph.facebook.com/v19.0/{media_id}"
    params = {"access_token": ACCESS_TOKEN}
    r = requests.delete(url, params=params, timeout=30)
    return r.status_code, r.json() if r.text else {}

def main():
    do_delete = "--yes" in sys.argv
    if not ACCESS_TOKEN or not USER_ID:
        print("❌ 環境変数なし")
        sys.exit(1)

    media = list_recent_media(limit=25)
    # v2 判定: キャプションに v2 専用 CTA フレーズが含まれる
    V2_MARKERS = (
        "3ヶ月で肌が変わります",
        "コメントで教えてください",
        "プロフィールのリンクから読めます",
        "明日の朝の投稿も一緒に",
    )
    def is_v2(m):
        cap = m.get("caption", "") or ""
        return m.get("media_type") == "CAROUSEL_ALBUM" and any(k in cap for k in V2_MARKERS)
    v2_posts = [m for m in media if is_v2(m)]
    targets = v2_posts[:TARGET_COUNT]

    print(f"=== 直近メディア {len(media)} 件中 v2 カルーセル {len(v2_posts)} 件 ===")
    for i, m in enumerate(targets, 1):
        cap = (m.get("caption", "") or "").replace("\n", " ")[:60]
        print(f"  {i:2d}. {m['timestamp']} id={m['id']} {cap}...")

    if not do_delete:
        print("\n（--yes 未指定のため削除は行いません）")
        return

    print(f"\n🗑️  削除実行 ({len(targets)} 件)...")
    success = 0
    for i, m in enumerate(targets, 1):
        code, body = delete_media(m["id"])
        ok = code == 200 and body.get("success") in (True, None)
        if ok and body.get("success", True):
            print(f"  ✅ {i}/{len(targets)} 削除 {m['id']}")
            success += 1
        else:
            print(f"  ❌ {i}/{len(targets)} 失敗 {m['id']}: status={code} body={body}")
    print(f"\n=== 完了: {success}/{len(targets)} 件削除 ===")

if __name__ == "__main__":
    main()
