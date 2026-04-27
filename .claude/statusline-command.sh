#!/bin/bash
# ステータスライン表示スクリプト
# 複数ターミナル間で使用量情報を共有するため、共有キャッシュファイルを利用する
# Linux(WSL2) と macOS の両方で動くように書かれている

input=$(cat)  # Claude Codeから送られてくるJSON情報を受け取る

# --- 共有キャッシュファイルの場所（$HOMEを使うことでLinux/Mac両対応）---
CACHE_FILE="$HOME/.claude/statusline-cache.json"

# ANSIカラーコード（ターミナルの色付け用）
GREEN=$'\033[32m'   # 緑色の開始
CYAN=$'\033[38;2;0;255;255m'    # 蛍光水色（RGB true color）
RESET=$'\033[0m'    # 色をリセット

# OS判定（LinuxとmacOSでコマンドが違う部分に使う）
OS=$(uname -s)  # Linux → "Linux"、Mac → "Darwin"

# ファイルの更新日時（Unixタイムスタンプ）を取得する関数
# Linux: stat -c %Y、macOS: stat -f %m と書き方が違うため関数で吸収する
get_mtime() {
  if [ "$OS" = "Darwin" ]; then
    stat -f %m "$1" 2>/dev/null || echo 0  # macOSの書き方
  else
    stat -c %Y "$1" 2>/dev/null || echo 0  # Linuxの書き方
  fi
}

# 日本時間で今日の日付を取得（例: 2026/4/7(Tue) 09:30:00）
# %-m・%-d はLinux専用のため、sedで先頭ゼロを除去する方法で両対応
today_raw=$(TZ=Asia/Tokyo date '+%Y/%m/%d(%a) %H:%M')
today=$(echo "$today_raw" | sed 's|/0\([0-9]\)|/\1|g')  # /04/ → /4/ のように変換

# --- 天気情報（1時間ごとに更新）---
# 都市を変えたい場合は CITY を変更（例: Osaka, Sapporo, Fukuoka）
WEATHER_CACHE="$HOME/.claude/weather-cache.json"
CITY="Tokyo"

# キャッシュが存在しない、または1時間（3600秒）以上古ければ wttr.in から再取得する
if [ ! -f "$WEATHER_CACHE" ] || [ $(($(date +%s) - $(get_mtime "$WEATHER_CACHE"))) -ge 3600 ]; then
  # JSON形式で取得（現在気温・最高・最低・天気コードをまとめて取れる）
  weather_json=$(curl -s --max-time 5 "wttr.in/${CITY}?format=j1" 2>/dev/null)
  # 正しいJSONが取得できた場合のみキャッシュを更新する
  if [ -n "$weather_json" ] && echo "$weather_json" | jq -e '.current_condition[0]' >/dev/null 2>&1; then
    echo "$weather_json" > "${WEATHER_CACHE}.tmp" && mv "${WEATHER_CACHE}.tmp" "$WEATHER_CACHE"
  fi
fi

# 天気コードから絵文字アイコンを返す関数
get_weather_icon() {
  local code=$1
  case $code in
    113) echo "☀️" ;;                                                          # 快晴
    116) echo "⛅" ;;                                                           # 一部曇り
    119|122) echo "☁️" ;;                                                      # 曇り
    143|248|260) echo "🌫️" ;;                                                 # 霧
    200|386|389|392|395) echo "⛈️" ;;                                         # 雷雨
    179|182|185|227|230|323|326|329|332|335|338|350|368|371) echo "❄️" ;;     # 雪
    *) echo "🌧️" ;;                                                           # その他（雨）
  esac
}

# キャッシュから天気情報を読み込む
weather_info=""
if [ -f "$WEATHER_CACHE" ] && [ -s "$WEATHER_CACHE" ]; then
  w=$(cat "$WEATHER_CACHE")
  if echo "$w" | jq -e '.current_condition[0]' >/dev/null 2>&1; then
    cur_temp=$(echo "$w" | jq -r '.current_condition[0].temp_C')
    max_temp=$(echo "$w" | jq -r '.weather[0].maxtempC')
    min_temp=$(echo "$w" | jq -r '.weather[0].mintempC')
    w_code=$(echo "$w"  | jq -r '.current_condition[0].weatherCode')
    icon=$(get_weather_icon "$w_code")
    # 例: ⛅18°C(↑22↓12)
    weather_info="${icon}${cur_temp}°C(↑${max_temp}↓${min_temp})"
  fi
fi

# モデル表示名（このセッション自身のモデルを使う）
model=$(echo "$input" | jq -r '.model.display_name // empty')

# --- 使用量データを共有キャッシュに書き出す（値がある場合のみ上書き）---
# rate_limits や context_window に値がある場合はキャッシュを更新する
new_five_used=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
new_five_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
new_week_used=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
new_week_reset=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')
new_ctx_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

if [ -n "$new_five_used" ] || [ -n "$new_week_used" ] || [ -n "$new_ctx_pct" ]; then
  # 新しい使用量データがある場合だけキャッシュを更新する
  if [ -f "$CACHE_FILE" ]; then
    old=$(cat "$CACHE_FILE")
  else
    old='{}'  # キャッシュがなければ空のJSONから始める
  fi

  # 古いキャッシュが有効なJSONでなければ空JSONから始める
  if ! echo "$old" | jq -e . >/dev/null 2>&1; then
    old='{}'
  fi

  # 新しい値があるものだけ上書きし、ないものは古い値をそのまま使う
  new_cache=$(echo "$old" | jq \
    --arg five_used "$new_five_used" \
    --arg five_reset "$new_five_reset" \
    --arg week_used "$new_week_used" \
    --arg week_reset "$new_week_reset" \
    --arg ctx_pct "$new_ctx_pct" \
    '
      if $five_used != "" then .five_used = ($five_used | tonumber) else . end |
      if $five_reset != "" then .five_reset = ($five_reset | tonumber) else . end |
      if $week_used  != "" then .week_used  = ($week_used  | tonumber) else . end |
      if $week_reset != "" then .week_reset = ($week_reset | tonumber) else . end |
      if $ctx_pct    != "" then .ctx_pct    = ($ctx_pct    | tonumber) else . end
    ')
  # キャッシュファイルに書き出す（一時ファイル経由で安全に上書き）
  echo "$new_cache" > "${CACHE_FILE}.tmp" && mv "${CACHE_FILE}.tmp" "$CACHE_FILE"
fi

# --- キャッシュから使用量データを読み込む（他のターミナルの最新データも反映される）---
cached=""
if [ -f "$CACHE_FILE" ] && [ -s "$CACHE_FILE" ]; then
  raw=$(cat "$CACHE_FILE")
  if echo "$raw" | jq -e . >/dev/null 2>&1; then
    cached="$raw"
  fi
fi

if [ -n "$cached" ]; then
  five_used=$(echo "$cached" | jq -r '.five_used // empty')
  five_reset=$(echo "$cached" | jq -r '.five_reset // empty')
  week_used=$(echo "$cached" | jq -r '.week_used // empty')
  week_reset=$(echo "$cached" | jq -r '.week_reset // empty')
  used_pct=$(echo "$cached" | jq -r '.ctx_pct // empty')
else
  # キャッシュがない・空・壊れている場合は現在のセッション値を直接使う
  five_used=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
  five_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
  week_used=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
  week_reset=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')
  used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
fi

# リセットまでの残り時間を「X時間Y分後」形式に変換する関数
format_reset() {
  local reset_epoch=$1  # Unixタイムスタンプ（秒単位の数字）
  [ -z "$reset_epoch" ] && echo "" && return
  local now_epoch=$(date +%s)
  local diff=$((reset_epoch - now_epoch))  # 現在時刻との差（秒）
  if [ $diff -le 0 ]; then
    echo "soon"
  elif [ $diff -lt 3600 ]; then
    echo "$((diff / 60))m"
  elif [ $diff -lt 86400 ]; then
    echo "$((diff / 3600))h$(( (diff % 3600) / 60 ))m"
  else
    echo "$((diff / 86400))d$(( (diff % 86400) / 3600 ))h"
  fi
}

# パーセントを緑色のメーターバーに変換する関数（例: 45 → 緑の█████░░░░░ 45%）
make_meter() {
  local pct=$1        # 使用率（0〜100の数字）
  local width=10      # メーターの幅（文字数）
  local filled=$(echo "$pct $width" | awk '{printf "%d", ($1/100*$2) + 0.5}')
  local empty=$((width - filled))
  local bar=""
  for i in $(seq 1 $filled); do bar="${bar}█"; done
  for i in $(seq 1 $empty); do bar="${bar}░"; done
  printf "${GREEN}%s %s%%${RESET}" "$bar" "$pct"
}

# プラン使用量を組み立てる
rate_info=""
if [ -n "$five_used" ]; then
  five_pct=$(echo "$five_used" | awk '{printf "%.0f", $1}')
  five_time=$(format_reset "$five_reset")
  five_meter=$(make_meter "$five_pct")
  five_str="5h:${five_meter}"
  [ -n "$five_time" ] && five_str="${five_str}(${five_time})"
  rate_info="$five_str"
fi
if [ -n "$week_used" ]; then
  week_pct=$(echo "$week_used" | awk '{printf "%.0f", $1}')
  week_time=$(format_reset "$week_reset")
  week_meter=$(make_meter "$week_pct")
  week_str="7d:${week_meter}"
  [ -n "$week_time" ] && week_str="${week_str}(${week_time})"
  [ -n "$rate_info" ] && rate_info="$rate_info  "
  rate_info="${rate_info}${week_str}"
fi

# コンテキスト情報
ctx_info=""
if [ -n "$used_pct" ]; then
  ctx_info="ctx:$(printf '%.0f' "$used_pct")%"
fi

# 出力を3行に分けて組み立てる
line1=""  # 1行目: 日時 + ユーザー名
line2=""  # 2行目: モデル・コンテキスト
line3=""  # 3行目: プラン使用量メーター

# --- 最終同期時刻をログから取得 ---
SYNC_LOG="$HOME/sync_log.txt"
last_sync=""
if [ -f "$SYNC_LOG" ]; then
  # grep -oP はmacOS非対応のため、-oE（拡張正規表現）で代替する
  last_sync=$(grep "同期完了" "$SYNC_LOG" | tail -1 | grep -oE '[0-9]{2}:[0-9]{2}' | tail -1)
fi

[ -n "$today" ] && line1="${CYAN}${today}${RESET}"
[ -n "$weather_info" ] && line1="$line1 | ${CITY}: ${weather_info}"
[ -n "$last_sync" ] && line1="$line1 | Sync: ${last_sync}"
line1="$line1 | 🦀 kmkn"

[ -n "$model" ] && line2="$model"
[ -n "$ctx_info" ] && line2="$line2 | $ctx_info"

[ -n "$rate_info" ] && line3="$rate_info"

printf "%s\n%s\n%s" "$line1" "$line2" "$line3"
