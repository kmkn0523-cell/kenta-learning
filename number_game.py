import random  # ランダムな数字を生成するためのモジュール

# ===== 難易度の設定 =====
# 難易度ごとの数字の範囲をまとめた辞書
DIFFICULTY_SETTINGS = {
    "1": {"name": "簡単", "min": 1, "max": 30},
    "2": {"name": "普通", "min": 1, "max": 100},
    "3": {"name": "難しい", "min": 1, "max": 500},
}


def show_title():
    """ゲームのタイトルを装飾して表示する"""
    print()
    print("=" * 40)
    print("         🎯  数当てゲーム  🎯")
    print("=" * 40)
    print("  コンピューターが決めた数字を当てよう！")
    print("=" * 40)
    print()


def show_stats(total_plays, best_score):
    """通算成績を表示する"""
    print()
    print("-" * 30)
    print("  📊 通算成績")
    print(f"  プレイ回数  : {total_plays} 回")
    # best_score が None のときはまだ記録なし
    if best_score is None:
        print("  最少回数記録: まだ記録なし")
    else:
        print(f"  最少回数記録: {best_score} 回")
    print("-" * 30)
    print()


def choose_difficulty():
    """難易度を選択してもらう。正しい入力があるまでループする"""
    print("【難易度を選んでください】")
    print("  1: 簡単   (1 〜 30)")
    print("  2: 普通   (1 〜 100)")
    print("  3: 難しい (1 〜 500)")
    print()

    while True:
        choice = input("番号を入力してください (1/2/3): ").strip()

        # 入力が辞書のキーに含まれているか確認
        if choice in DIFFICULTY_SETTINGS:
            setting = DIFFICULTY_SETTINGS[choice]
            print(f"\n「{setting['name']}」を選びました！ (範囲: {setting['min']} 〜 {setting['max']})\n")
            return setting
        else:
            # 無効な入力の場合はエラーメッセージを表示して再入力を促す
            print("❌ 1、2、3 のいずれかを入力してください。\n")


def get_player_input(min_num, max_num):
    """プレイヤーに数字を入力してもらう。無効な値はエラーにして再入力させる"""
    while True:
        raw = input(f"数字を入力してください ({min_num} 〜 {max_num}): ").strip()

        # 数字かどうかチェック（マイナス符号も含めて整数かどうか判定）
        try:
            guess = int(raw)
        except ValueError:
            # 数字以外が入力された場合
            print("❌ 数字を入力してください。\n")
            continue

        # 入力された数字が指定範囲内かチェック
        if guess < min_num or guess > max_num:
            print(f"❌ {min_num} 〜 {max_num} の範囲で入力してください。\n")
            continue

        # 問題なければその数字を返す
        return guess


def play_game(setting):
    """1ゲームを実行して、クリアするまでにかかった回数を返す"""
    min_num = setting["min"]
    max_num = setting["max"]

    # コンピューターがランダムに答えを決める
    answer = random.randint(min_num, max_num)

    # 試行回数のカウンター
    attempts = 0

    print(f"スタート！{min_num} 〜 {max_num} の数字を当ててください。\n")

    while True:
        # プレイヤーの入力を受け取る
        guess = get_player_input(min_num, max_num)
        attempts += 1  # 入力のたびに試行回数を1増やす

        if guess < answer:
            # 入力した数字が答えより小さい場合
            print(f"  👆 もっと大きい！  (あなた: {guess})\n")
        elif guess > answer:
            # 入力した数字が答えより大きい場合
            print(f"  👇 もっと小さい！  (あなた: {guess})\n")
        else:
            # 正解した場合 ─ 派手に演出する
            print()
            print("🎉✨🎊  正解!!!  🎊✨🎉")
            print(f"  答えは {answer} でした！")
            print(f"  {attempts} 回で当てました！")

            # 試行回数に応じてコメントを変える
            if attempts <= 3:
                print("  🏆 すごい！天才的な閃き！")
            elif attempts <= 7:
                print("  👍 なかなかやるね！")
            else:
                print("  😅 惜しかった！次はもっと少ない回数で！")
            print()

            # クリアするまでの試行回数を返す
            return attempts


def ask_replay():
    """もう一度遊ぶかどうかをプレイヤーに確認する"""
    while True:
        answer = input("もう一度遊ぶ？ (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        elif answer in ("n", "no"):
            return False
        else:
            # y か n 以外が入力された場合
            print("❌ y または n を入力してください。")


def main():
    """ゲーム全体の流れを管理するメイン関数"""
    show_title()  # タイトルを表示

    # 通算成績を管理する変数
    total_plays = 0       # 総プレイ回数
    best_score = None     # 最少試行回数の記録（最初はまだ記録なし）

    # メインループ: プレイヤーが終了を選ぶまで繰り返す
    while True:
        # 難易度を選ばせる
        setting = choose_difficulty()

        # 1ゲームを実行して試行回数を受け取る
        attempts = play_game(setting)

        # プレイ回数を増やす
        total_plays += 1

        # 最少回数記録を更新するかチェック
        if best_score is None or attempts < best_score:
            best_score = attempts
            print("  🥇 自己ベスト更新！おめでとう！\n")

        # 通算成績を表示する
        show_stats(total_plays, best_score)

        # 再プレイするか確認する
        if not ask_replay():
            # 遊ばない場合はループを抜けて終了
            break
        print()  # 次のゲームとの間に空行を入れる

    # 終了メッセージ
    print()
    print("=" * 40)
    print("  遊んでくれてありがとう！またね！👋")
    show_stats(total_plays, best_score)
    print("=" * 40)
    print()


# このファイルが直接実行されたときだけ main() を呼ぶ
if __name__ == "__main__":
    main()
