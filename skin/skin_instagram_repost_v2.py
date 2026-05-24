"""
skin Instagram v2.1 修正版 再投稿スクリプト（1回限り使用）
- carousel_content.json のテーマ id 1〜8（v2.1）を順番に8件投稿する
- 90分スキップチェックは行わない
- progress.json は変更しない（既に v2_index=8 のため）
- 投稿間隔は INTERVAL_SEC（デフォルト180秒=3分）

使い方:
  python3 skin/skin_instagram_repost_v2.py          # ドライラン（投稿しない）
  python3 skin/skin_instagram_repost_v2.py --yes    # 実投稿
"""
import os
import sys
import time

# 既存の投稿モジュールから関数を再利用する
sys.path.insert(0, os.path.dirname(__file__))
from skin_instagram_auto_post import (
    ACCESS_TOKEN,
    USER_ID,
    load_carousel_content,
    build_caption,
    build_carousel_image_urls,
    create_child_container,
    create_carousel_container,
    wait_for_container_ready,
    publish_media,
)

# 再投稿対象テーマID
TARGET_IDS = [1, 2, 3, 4, 5, 6, 7, 8]
INTERVAL_SEC = 180  # 投稿と投稿の間隔（秒）


def post_one_theme(theme: dict) -> bool:
    """1テーマを投稿する。成功で True"""
    theme_id = theme["id"]
    print(f"\n=== テーマ{theme_id:02d} 投稿開始 ===")

    caption = build_caption(
        theme_id=theme_id,
        hook=theme.get("hook", theme.get("slides", [{}])[0].get("title", "")),
        fixed=theme["fixed_hashtags"],
        theme=theme["theme_hashtags"],
        size_mix=theme["size_mix_hashtags"],
    )

    slide_count = theme.get("slide_count", 8)
    image_urls = build_carousel_image_urls(theme_id, slide_count)
    print(f"🖼️  スライド: {len(image_urls)}枚")

    # 子コンテナ作成
    child_ids = []
    for i, url in enumerate(image_urls, start=1):
        print(f"  子{i}: {os.path.basename(url)}")
        cid = create_child_container(url)
        if not cid:
            print(f"❌ 子コンテナ{i}失敗")
            return False
        child_ids.append(cid)
        time.sleep(2)

    # カルーセルコンテナ作成
    carousel_id = create_carousel_container(child_ids, caption)
    if not carousel_id:
        return False
    print(f"✅ カルーセルID: {carousel_id}")

    # 処理完了待ち
    if not wait_for_container_ready(carousel_id):
        return False

    # 公開
    result = publish_media(carousel_id)
    if "id" not in result:
        print(f"❌ 公開失敗: {result}")
        return False

    print(f"✅ テーマ{theme_id:02d} 投稿成功 投稿ID={result['id']}")
    return True


def main():
    do_post = "--yes" in sys.argv
    if not ACCESS_TOKEN or not USER_ID:
        print("❌ 環境変数なし")
        sys.exit(1)

    themes = load_carousel_content()
    targets = [t for t in themes if t["id"] in TARGET_IDS]
    targets.sort(key=lambda t: t["id"])

    print(f"=== 再投稿対象 {len(targets)} 件 ===")
    for t in targets:
        print(f"  id={t['id']:02d} {t.get('hook', '')[:50]}")

    if not do_post:
        print("\n（--yes 未指定のためドライラン終了）")
        return

    print(f"\n🚀 投稿開始（投稿間隔 {INTERVAL_SEC}秒）")
    success = 0
    for idx, theme in enumerate(targets, start=1):
        ok = post_one_theme(theme)
        if ok:
            success += 1
        else:
            print(f"⚠️ テーマ{theme['id']}失敗。続行します")

        # 最後以外はインターバル待機
        if idx < len(targets):
            print(f"\n⏸️  次の投稿まで {INTERVAL_SEC}秒待機...")
            time.sleep(INTERVAL_SEC)

    print(f"\n=== 完了: {success}/{len(targets)} 件成功 ===")


if __name__ == "__main__":
    main()
