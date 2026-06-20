#!/bin/bash
# ステータスライン表示スクリプト
# 複数ターミナル間で使用量情報を共有するため、共有キャッシュファイルを利用する
# Linux(WSL2) と macOS の両方で動くように書かれている

input=$(cat)  # Claude Codeから送られてくるJSON情報を受け取る

# --- 共有キャッシュファイルの場所（$HOMEを使うことでLinux/Mac両対応）---
CACHE_FILE="$HOME/.claude/statusline-cache.json"
# OAuth API（claude.aiと同じ正確な使用量データ）のキャッシュ
OAUTH_CACHE="$HOME/.claude/oauth-usage-cache.json"
OAUTH_CACHE_TTL=60  # 60秒キャッシュ（無駄なAPI呼び出しを防ぐ）
CREDENTIALS="$HOME/.claude/.credentials.json"

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
  # キャッシュは複数ターミナル間共有用。入力値はそのまま信頼して書き込む（このターミナルの最新値だから）
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

# --- OAuth APIから正確な使用量データを取得（claude.aiと同じ値）---
# Claude Codeのstdin経由のrate_limitsはズレがあるため、本家APIから直接取得する
oauth_data=""
oauth_age=99999

if [ -f "$OAUTH_CACHE" ] && [ -s "$OAUTH_CACHE" ]; then
  oauth_age=$(($(date +%s) - $(get_mtime "$OAUTH_CACHE")))
fi

# キャッシュが新鮮ならそのまま使う、古ければ再取得
if [ $oauth_age -lt $OAUTH_CACHE_TTL ]; then
  oauth_data=$(cat "$OAUTH_CACHE")
elif [ -f "$CREDENTIALS" ]; then
  # OAuth トークンを取り出してAPIを叩く
  oauth_token=$(jq -r '.claudeAiOauth.accessToken // empty' "$CREDENTIALS" 2>/dev/null)
  if [ -n "$oauth_token" ]; then
    fresh=$(curl -s --max-time 4 \
      -H "Authorization: Bearer $oauth_token" \
      -H "anthropic-version: 2023-06-01" \
      -H "anthropic-beta: oauth-2025-04-20" \
      -H "User-Agent: claude-cli/2.1.119 (external, cli)" \
      "https://api.anthropic.com/api/oauth/usage" 2>/dev/null)
    # 正しいJSONが取れた場合のみキャッシュに保存
    if [ -n "$fresh" ] && echo "$fresh" | jq -e '.five_hour' >/dev/null 2>&1; then
      echo "$fresh" > "${OAUTH_CACHE}.tmp" && mv "${OAUTH_CACHE}.tmp" "$OAUTH_CACHE"
      oauth_data="$fresh"
    elif [ -f "$OAUTH_CACHE" ]; then
      # 取得失敗 → 古いキャッシュをそのまま使う
      oauth_data=$(cat "$OAUTH_CACHE")
    fi
  fi
fi

# ISO 8601 形式の日時を Unix epoch に変換する関数（Linux/macOS 両対応）
iso_to_epoch() {
  python3 -c "import datetime,sys; s=sys.argv[1].replace('Z','+00:00'); print(int(datetime.datetime.fromisoformat(s).timestamp()))" "$1" 2>/dev/null
}

# --- 表示用の値を決定 ---
# 優先順位: OAuth API（claude.ai同等の正確な値） > stdin入力 > キャッシュ
cached=""
if [ -f "$CACHE_FILE" ] && [ -s "$CACHE_FILE" ]; then
  raw=$(cat "$CACHE_FILE")
  if echo "$raw" | jq -e . >/dev/null 2>&1; then
    cached="$raw"
  fi
fi

# OAuth APIの値があればそれを使う（最優先）
five_used=""
five_reset=""
week_used=""
week_reset=""
if [ -n "$oauth_data" ] && echo "$oauth_data" | jq -e '.five_hour' >/dev/null 2>&1; then
  five_used=$(echo "$oauth_data" | jq -r '.five_hour.utilization // empty')
  five_reset_iso=$(echo "$oauth_data" | jq -r '.five_hour.resets_at // empty')
  [ -n "$five_reset_iso" ] && five_reset=$(iso_to_epoch "$five_reset_iso")
  week_used=$(echo "$oauth_data" | jq -r '.seven_day.utilization // empty')
  week_reset_iso=$(echo "$oauth_data" | jq -r '.seven_day.resets_at // empty')
  [ -n "$week_reset_iso" ] && week_reset=$(iso_to_epoch "$week_reset_iso")
fi

# OAuth取得できなかった項目は stdin入力 → キャッシュの順でフォールバック
pick() {
  local input_val="$1"
  local cache_key="$2"
  if [ -n "$input_val" ]; then
    echo "$input_val"
  elif [ -n "$cached" ]; then
    echo "$cached" | jq -r ".${cache_key} // empty"
  fi
}

[ -z "$five_used" ]  && five_used=$(pick "$new_five_used"   "five_used")
[ -z "$five_reset" ] && five_reset=$(pick "$new_five_reset" "five_reset")
[ -z "$week_used" ]  && week_used=$(pick "$new_week_used"   "week_used")
[ -z "$week_reset" ] && week_reset=$(pick "$new_week_reset" "week_reset")
used_pct=$(pick "$new_ctx_pct" "ctx_pct")

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
[ -n "$last_sync" ] && line1="$line1 | Sync: ${last_sync}"

[ -n "$model" ] && line2="$model"
[ -n "$ctx_info" ] && line2="$line2 | $ctx_info"

[ -n "$rate_info" ] && line3="$rate_info"

printf "%s\n%s\n%s" "$line1" "$line2" "$line3"
