import datetime  # 日付や時刻を扱うための道具を読み込む

# 曜日の名前リスト（月曜=0 〜 日曜=6 の順番）
WEEKDAY_NAMES = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]

# 今日の日付を取得する（例: 2026-04-25）
today = datetime.date.today()

# 曜日番号を取得する（月曜=0, 火曜=1, ... 日曜=6）
weekday_number = today.weekday()

# 番号を日本語の曜日名に変換する
weekday_name = WEEKDAY_NAMES[weekday_number]

# 結果を画面に表示する
print(f"今日は {today.year}年{today.month}月{today.day}日 {weekday_name} です。")
