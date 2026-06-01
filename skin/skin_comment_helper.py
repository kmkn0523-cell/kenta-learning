# skin_comment_helper.py
# 他アカウントへのコメント候補を生成するツール
# 使い方: python3 skin/skin_comment_helper.py

import random  # ランダムにコメントを並べ替えるための道具

# テンプレ集は共通モジュールから読み込む。
# 直接実行（python3 skin/skin_comment_helper.py）でも、リポジトリ直下からでも動くように2通り試す
try:
    from skin_comment_templates import COMMENT_TEMPLATES  # skin/ が import パスにある時（直接実行・pytest）
except ImportError:
    from skin.skin_comment_templates import COMMENT_TEMPLATES  # リポジトリ直下から動かす時

# -----------------------------------------------
# メニュー表示
# -----------------------------------------------
def show_menu():
    """カテゴリー選択メニューを表示する"""
    print("\n" + "=" * 50)
    print("  コメント候補ジェネレーター")
    print("=" * 50)
    print("どの投稿にコメントしますか？\n")
    for key, value in COMMENT_TEMPLATES.items():
        print(f"  {key}: {value['name']}")
    print("\n  0: 終了")
    print("=" * 50)
    return input("番号を入力してください: ").strip()


# -----------------------------------------------
# コメント候補を表示する
# -----------------------------------------------
def show_comments(category_key):
    """選んだカテゴリーのコメント候補をランダムに5つ表示する"""
    category = COMMENT_TEMPLATES[category_key]
    print(f"\n【{category['name']}】コメント候補\n")

    # コメントをランダムに並べ替えて5つ選ぶ
    candidates = random.sample(category["comments"], min(5, len(category["comments"])))

    for i, comment in enumerate(candidates, 1):
        print(f"  [{i}] {comment}")
        print()

    print("-" * 50)
    choice = input("使いたい番号を入力（別の候補を見るならr、戻るなら0）: ").strip()

    if choice == "0":
        return
    elif choice == "r":
        # もう一度ランダムに出し直す
        show_comments(category_key)
        return

    # 選んだコメントを表示する
    try:
        selected_index = int(choice) - 1
        if 0 <= selected_index < len(candidates):
            selected_comment = candidates[selected_index]
            print("\n" + "=" * 50)
            print("✅ 選んだコメント（コピーして使ってください）")
            print("=" * 50)
            print()
            print(selected_comment)
            print()
            print("=" * 50)
            print("▶ Threadsで貼り付けてコメントしてください")
            input("\nEnterキーでメニューに戻る")
        else:
            print("番号が正しくありません")
    except ValueError:
        print("番号を入力してください")


# -----------------------------------------------
# メイン処理
# -----------------------------------------------
def main():
    """メイン処理：メニューを繰り返し表示する"""
    print("\n" + "=" * 50)
    print("  skin コメントヘルパー")
    print("  他アカウントへのコメント候補を生成します")
    print("=" * 50)
    print("使い方:")
    print("  1. Threadsで「#肌荒れ」などで投稿を検索する")
    print("  2. 投稿のテーマに合ったカテゴリーを選ぶ")
    print("  3. 気に入ったコメントをコピーして貼り付ける")
    print("  ※ 1日5〜10件が目安（やりすぎはスパムと思われる）")

    while True:
        choice = show_menu()

        if choice == "0":
            print("\n終了します。お疲れ様でした！")
            break
        elif choice in COMMENT_TEMPLATES:
            show_comments(choice)
        else:
            print("0〜6の番号を入力してください")


if __name__ == "__main__":
    main()
