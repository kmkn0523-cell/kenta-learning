import time  # 時間関係の処理に使う
import sys   # 画面出力の制御に使う
from datetime import datetime  # 記録用の日時取得に使う

def main():
    # ---- 作業内容の入力 ----
    task = input("作業内容を入力してください → ").strip()
    if not task:
        task = "作業"

    # ---- 分数の入力 ----
    while True:  # 正しい数字が入力されるまで繰り返す
        try:
            minutes = int(input("何分のタイマーにしますか? → "))
            if minutes <= 0:
                print("1以上の数字を入力してください。")
                continue
            break  # 正しい数字が入ったのでループを抜ける
        except ValueError:
            # 数字以外が入力されたときのエラー処理
            print("数字を入力してください。")

    # 入力された分を秒に変換（例: 5分 → 300秒）
    total_seconds = minutes * 60

    print(f"\n{minutes}分のタイマーをスタートします！ Ctrl+C で中断できます。\n")

    # ---- カウントダウンのメインループ ----
    try:
        for remaining in range(total_seconds, 0, -1):  # total_secondsから1ずつ減らす
            mins, secs = divmod(remaining, 60)  # 残り秒を「分」と「秒」に分ける

            # \r でカーソルを行の先頭に戻すことで、同じ行を上書き表示する
            sys.stdout.write(f"\r残り {mins:2}分 {secs:02}秒")
            sys.stdout.flush()  # バッファを即座に画面に出力する

            time.sleep(1)  # 1秒待つ

    except KeyboardInterrupt:
        # Ctrl+C が押されたとき
        print("\n\nタイマーを中断しました。")
        sys.exit(0)

    # ---- 0秒になったとき ----
    sys.stdout.write("\r残り  0分 00秒\n")  # 最後に0:00を表示して改行
    print("\a")        # アラート音（ビープ音）を鳴らす
    print("時間です！")
    print(f"\n{task} を {minutes}分 やりました、お疲れさま!")

    # ---- 記録の確認 ----
    answer = input("\n記録しますか? (y/n) → ").strip().lower()
    if answer == "y":
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        log_entry = f"[{now}] {task} {minutes}分\n"
        with open("time_log.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)
        print("記録しました → time_log.txt")

if __name__ == "__main__":
    main()
