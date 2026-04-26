# ============================================================
# 天気取得プログラム（拡張版）- Open-Meteo API を使用
# APIキー不要で誰でも無料で使える天気APIです
# ============================================================

import requests   # インターネット通信をするためのライブラリ
import sys        # プログラムを途中で終了するために使います
from datetime import datetime  # 日付を扱うためのライブラリ

# === 都市データ定義 ===
# 都市名と緯度・経度の対応表（辞書型）
# 緯度(lat)は南北、経度(lon)は東西の位置を表します
CITIES = {
    "1":  {"name": "東京",        "lat": 35.6762,  "lon": 139.6503},
    "2":  {"name": "大阪",        "lat": 34.6937,  "lon": 135.5023},
    "3":  {"name": "札幌",        "lat": 43.0642,  "lon": 141.3469},
    "4":  {"name": "沖縄（那覇）", "lat": 26.2124,  "lon": 127.6809},
    "5":  {"name": "福岡",        "lat": 33.5904,  "lon": 130.4017},
    "6":  {"name": "名古屋",      "lat": 35.1815,  "lon": 136.9066},
    "7":  {"name": "仙台",        "lat": 38.2682,  "lon": 140.8694},
    "8":  {"name": "広島",        "lat": 34.3853,  "lon": 132.4553},
    "9":  {"name": "金沢",        "lat": 36.5613,  "lon": 136.6562},
    "10": {"name": "京都",        "lat": 35.0116,  "lon": 135.7681},
    "11": {"name": "横浜",        "lat": 35.4437,  "lon": 139.6380},
}

# === 天気コード定義 ===
# WMO（世界気象機関）が定めた数値コードで天気の種類を表します
# キー: 天気コード（整数）、値: (絵文字, 説明文) のタプル
WEATHER_CODES = {
    0:  ("☀️",  "快晴"),
    1:  ("🌤️", "ほぼ晴れ"),
    2:  ("⛅",  "一部曇り"),
    3:  ("☁️",  "曇り"),
    45: ("🌫️", "霧"),
    48: ("🌫️", "着氷性の霧"),
    51: ("🌦️", "霧雨（弱）"),
    53: ("🌦️", "霧雨（並）"),
    55: ("🌦️", "霧雨（強）"),
    61: ("🌧️", "雨（弱）"),
    63: ("🌧️", "雨（並）"),
    65: ("🌧️", "雨（強）"),
    71: ("❄️",  "雪（弱）"),
    73: ("❄️",  "雪（並）"),
    75: ("❄️",  "雪（強）"),
    77: ("🌨️", "細雪"),
    80: ("🌧️", "にわか雨（弱）"),
    81: ("🌧️", "にわか雨（並）"),
    82: ("🌧️", "にわか雨（強）"),
    85: ("🌨️", "にわか雪（弱）"),
    86: ("🌨️", "にわか雪（強）"),
    95: ("⛈️",  "雷雨"),
    96: ("⛈️",  "雹を伴う雷雨（弱）"),
    99: ("⛈️",  "雹を伴う雷雨（強）"),
}

# 曜日を日本語に変換するためのリスト（0=月曜日、6=日曜日）
WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]


# === 都市選択 ===
def select_city():
    """ユーザーに都市を選んでもらう関数"""

    # タイトルと選択肢を画面に表示します
    print()
    print("╔══════════════════════════════════════════╗")
    print("║      🗾  お天気情報  -  都市を選択      ║")
    print("╠══════════════════════════════════════════╣")

    # CITIES辞書を2列で表示するために、キーのリストを作ります
    keys = list(CITIES.keys())  # ["1", "2", ..., "11"] のリスト
    # 2つずつペアにして並べます（6行になる）
    for i in range(0, len(keys), 2):
        left_key = keys[i]                        # 左列のキー
        left_name = CITIES[left_key]["name"]      # 左列の都市名
        left_str = f"  {left_key:>2}. {left_name}"  # 右揃えで番号を表示

        if i + 1 < len(keys):                     # 右列がある場合だけ表示
            right_key = keys[i + 1]
            right_name = CITIES[right_key]["name"]
            right_str = f"{right_key:>2}. {right_name}"
            # 左列を25文字幅に揃えて右列を続けます
            print(f"║ {left_str:<24}  {right_str:<16} ║")
        else:
            # 右列がない（11番目）場合は左列だけ表示
            print(f"║ {left_str:<42} ║")

    print("╚══════════════════════════════════════════╝")

    # ユーザーの入力を受け取ります（input関数で画面からキー入力を取得）
    choice = input("番号を入力して Enter を押してください: ").strip()

    # 入力された番号が選択肢にない場合はエラーメッセージを出して終了します
    if choice not in CITIES:
        print(f"❌ 無効な番号です。1〜{len(CITIES)} を入力してください。")
        sys.exit(1)  # 引数 1 は「エラーで終了」を意味します

    # 選ばれた都市の情報（辞書）を返します
    return CITIES[choice]


# === APIデータ取得 ===
def fetch_weather(lat, lon):
    """
    Open-Meteo API に HTTP リクエストを送り、7日間の天気データを取得する関数
    lat: 緯度（南北の位置）
    lon: 経度（東西の位置）
    """

    # APIのURL（どのサーバーに問い合わせるか）
    url = "https://api.open-meteo.com/v1/forecast"

    # 「クエリパラメータ」と呼ばれる、APIへの要求条件をまとめた辞書
    # URLの末尾に ?latitude=35.6&longitude=139.6&... の形で付加されます
    params = {
        "latitude":  lat,          # 緯度を指定
        "longitude": lon,          # 経度を指定
        "daily": [                 # 「日単位」で取得したいデータ項目のリスト
            "weathercode",             # 天気コード（WMO形式の数値）
            "temperature_2m_max",      # 地上2mの最高気温（℃）
            "temperature_2m_min",      # 地上2mの最低気温（℃）
            "precipitation_probability_max",  # 降水確率の最大値（%）
        ],
        "timezone":     "Asia/Tokyo",  # 日本時間（JST）で結果を返してもらう
        "forecast_days": 7,            # 今日から7日分を取得する
    }

    try:
        # ---------------------------------------------------
        # ★ ここがAPIからデータを取得する中心部分 ★
        # requests.get() でサーバーにデータを「取りに行く」（GETリクエスト）
        # timeout=10 は「10秒以内に応答がなければあきらめる」設定
        # ---------------------------------------------------
        response = requests.get(url, params=params, timeout=10)

        # HTTPステータスコードが 4xx/5xx（エラー）なら例外を発生させます
        # 200 OK 以外のときに自動で例外を投げてくれる便利なメソッドです
        response.raise_for_status()

        # サーバーから返ってきた JSON 形式のテキストを Python の辞書に変換します
        # JSON は { "key": value } という形式のデータ表現です
        data = response.json()

        # 取得成功したデータを呼び出し元に返します
        return data

    except requests.exceptions.ConnectionError:
        # インターネットに繋がっていない、またはサーバーに届かないとき
        print("❌ ネットワークエラー：インターネット接続を確認してください。")
        sys.exit(1)

    except requests.exceptions.Timeout:
        # 指定した秒数（10秒）以内にサーバーが応答しなかったとき
        print("❌ タイムアウト：サーバーの応答が遅すぎます。しばらく待ってから再試行してください。")
        sys.exit(1)

    except requests.exceptions.HTTPError as e:
        # サーバーが 4xx や 5xx のエラーコードを返してきたとき
        print(f"❌ HTTPエラー：{e}")
        sys.exit(1)

    except requests.exceptions.RequestException as e:
        # 上記以外の通信に関するすべてのエラーをまとめて受け取ります
        print(f"❌ 通信エラー：{e}")
        sys.exit(1)


# === データ解析 ===
def parse_weather(data):
    """APIから受け取ったデータの中から7日分の値を取り出す関数"""

    # "daily" キーの中に日単位のデータが入っています
    daily = data["daily"]

    # 7日分の天気をまとめたリストを作ります
    forecast_list = []  # 空のリストを用意します

    # zip() は複数のリストを同時に1要素ずつ取り出す関数です
    for date_str, code, t_max, t_min, precip in zip(
        daily["time"],                              # 日付（YYYY-MM-DD形式）
        daily["weathercode"],                       # 天気コード
        daily["temperature_2m_max"],                # 最高気温
        daily["temperature_2m_min"],                # 最低気温
        daily["precipitation_probability_max"],     # 降水確率
    ):
        # 日付文字列 "2024-04-24" を datetime オブジェクトに変換します
        dt = datetime.strptime(date_str, "%Y-%m-%d")

        # 月/日（曜日）の形式に整形します（例: 4/24(木)）
        weekday = WEEKDAYS[dt.weekday()]  # weekday()は0=月〜6=日を返します
        date_label = f"{dt.month}/{dt.day}({weekday})"

        # 天気コードに対応する絵文字と説明を辞書から取得します
        # get() の第2引数は、コードが辞書にない場合のデフォルト値です
        emoji, description = WEATHER_CODES.get(code, ("🌡️", "不明"))

        # 1日分の情報を辞書にまとめてリストに追加します
        forecast_list.append({
            "date":        date_label,   # 例: 4/24(木)
            "emoji":       emoji,        # 天気絵文字
            "description": description,  # 天気の説明
            "temp_max":    t_max,        # 最高気温（℃）
            "temp_min":    t_min,        # 最低気温（℃）
            "precip_prob": precip,       # 降水確率（%）
            "weather_code": code,        # 天気コード（服装判定に使います）
        })

    # 7日分のリストを返します
    return forecast_list


# === 服装・持ち物提案ロジック ===
def suggest_outfit(today):
    """
    今日の気温と天気を元に服装・持ち物を提案する関数
    today: parse_weather() が返すリストの先頭要素（今日の天気辞書）
    """

    # 今日の最高気温を取り出します（服装の基準にします）
    temp = today["temp_max"]
    code = today["weather_code"]     # 天気コード（雨・雪の判定に使います）
    precip = today["precip_prob"]    # 降水確率（%）

    # --- 気温別の服装提案 ---
    if temp >= 30:
        # 真夏レベルの暑さ
        clothes = ["👕 Tシャツ・短パン", "🧴 日焼け止め", "💧 水分を多めに"]
    elif temp >= 20:
        # 過ごしやすい暖かさ
        clothes = ["👔 半袖か薄手の長袖"]
    elif temp >= 10:
        # 肌寒い季節
        clothes = ["🧥 長袖 + 上着"]
    elif temp >= 0:
        # 冬の寒さ
        clothes = ["🧣 セーター + コート"]
    else:
        # 極寒レベル
        clothes = ["🧥 厚手のコート", "🧣 マフラー", "🧤 手袋"]

    # --- 天気コード別の追加アイテム ---
    # 雨・霧雨コードのリスト（Open-Meteoの定義に合わせています）
    rain_codes = {51, 53, 55, 61, 63, 65, 80, 81, 82}
    # 雪コードのリスト
    snow_codes = {71, 73, 75, 77, 85, 86}

    if code in rain_codes or code in {45, 48}:
        # 雨または霧のとき傘を追加します
        clothes.append("☂️ 傘を忘れずに！")
    elif code in snow_codes:
        # 雪のとき滑り止めと防寒強化を追加します
        clothes.append("👢 滑り止めの靴")
        clothes.append("🧤 防寒を強化して！")

    # --- 降水確率が高い場合の追加提案 ---
    if precip is not None and precip >= 50:
        # 降水確率50%以上なら折りたたみ傘を勧めます
        clothes.append("🌂 折りたたみ傘があると安心")

    # 提案アイテムのリストを返します
    return clothes


# === 表示処理 ===
def display_weather(city_name, forecast_list):
    """天気情報を見やすく画面に表示する関数"""

    # --- タイトル表示 ---
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print(f"║          🌈  {city_name} のお天気情報（7日間）{'':>{15 - len(city_name)}}   ║")
    print("╠══════════════════════════════════════════════════════════╣")

    # --- 週間予報テーブルのヘッダー ---
    # 列幅を揃えて見やすく表示します
    print("║  日付       天気          最高  最低  降水確率         ║")
    print("╠══════════════════════════════════════════════════════════╣")

    # --- 週間予報の各行を表示 ---
    for i, day in enumerate(forecast_list):
        # 今日だけ「★今日」マークを付けて目立たせます
        label = "★今日" if i == 0 else "      "

        # 降水確率が None（データなし）のときは "--" と表示します
        precip_str = f"{day['precip_prob']:>3}%" if day["precip_prob"] is not None else " --%"

        # 各列を固定幅で揃えて1行分の文字列を作ります
        # :>8 は「右揃えで8文字分」という意味です
        date_col  = f"{day['date']:<10}"           # 日付（左揃え10文字）
        emoji_col = f"{day['emoji']} {day['description']:<10}"  # 絵文字+説明
        max_col   = f"{day['temp_max']:>4.1f}℃"   # 最高気温（小数点1桁）
        min_col   = f"{day['temp_min']:>4.1f}℃"   # 最低気温（小数点1桁）

        print(f"║ {label} {date_col} {emoji_col} {max_col} {min_col}  {precip_str}       ║")

    print("╚══════════════════════════════════════════════════════════╝")

    # --- 服装・持ち物提案の表示 ---
    print()
    print("┌──────────────────────────────────────────────────────────┐")
    print("│  👗 今日の服装・持ち物アドバイス                        │")
    print("├──────────────────────────────────────────────────────────┤")

    # 今日の天気を元に服装を提案します
    today = forecast_list[0]  # リストの先頭が今日の天気です
    suggestions = suggest_outfit(today)  # 提案リストを取得

    for item in suggestions:
        # 各提案を1行ずつ表示します（幅56文字に揃えます）
        print(f"│  {item:<56}│")

    print("└──────────────────────────────────────────────────────────┘")
    print()


# === メイン処理 ===
def main():
    """プログラムのメイン処理。各関数を順番に呼び出します"""

    # タイトルバナーを表示します
    print()
    print("══════════════════════════════════════")
    print("  🌤️  お天気情報チェッカー  🌤️")
    print("══════════════════════════════════════")

    # ① 都市を選ばせる
    city = select_city()

    # ② 選んだ都市の緯度・経度でAPIを呼び出す
    print(f"\n⏳ {city['name']} の7日間予報を取得中...")
    data = fetch_weather(city["lat"], city["lon"])

    # ③ 取得したデータから7日分の情報を取り出す
    forecast_list = parse_weather(data)

    # ④ 結果を表示する
    display_weather(city["name"], forecast_list)


# このファイルが直接実行されたときだけ main() を呼び出します
# （他のファイルから import されたときは実行されません）
if __name__ == "__main__":
    main()
