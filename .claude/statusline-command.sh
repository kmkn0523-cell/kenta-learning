#!/bin/bash
# ステータスライン表示スクリプト（クリーン版・2026-06-26 全面書き直し）
# 複数ターミナル間で使用量情報を共有するため、共有キャッシュファイルを利用する
# Linux(WSL2) と macOS の両方で動くように書かれている

input=$(cat)  # Claude Codeから送られてくるJSON情報を受け取る

# --- 共有キャッシュファイルの場所（$HOMEを使うことでLinux/Mac両対応）---
CACHE_FILE="$HOME/.claude/statusline-cache.json"
OAUTH_CACHE="$HOME/.claude/oauth-usage-cache.json"   # OAuth APIの正確な使用量キャッシュ
OAUTH_CACHE_TTL=60                                    # 60秒キャッシュ（無駄なAPI呼び出しを防ぐ）
CREDENTIALS="$HOME/.claude/.credentials.json"

# ANSIカラーコード（標準16色のみ。true colorは端末で崩れるため使わない）
GREEN=$'\033[32m'   # 緑色
CYAN=$'\033[36m'    # シアン
RESET=$'\033[0m'    # 色リセット

OS=$(uname -s)  # Linux → "Linux"、Mac → "Darwin"

# ファイルの更新日時（Unixタイムスタンプ）を取得する関数（Linux/Mac両対応）
get_mtime() {
  if [ "$OS" = "Darwin" ]; then
    stat -f %m "$1" 2>/dev/null || echo 0
  else
    stat -c %Y "$1" 2>/dev/null || echo 0
  fi
}

# 日本時間で今日の日付（例: 2026/6/26(Fri) 09:30）。先頭ゼロはsedで除去
today_raw=$(TZ=Asia/Tokyo date '+%Y/%m/%d(%a) %H:%M')
today=$(echo "$today_raw" | sed 's|/0\([0-9]\)|/\1|g')

# --- stdinのJSONを1回のjqでまとめて解析する ---
parsed=$(echo "$input" | jq -r '[
  .model.display_name // "",
  .effort.level // "",
  .rate_limits.five_hour.used_percentage // "",
  .rate_limits.five_hour.resets_at // "",
  .rate_limits.seven_day.used_percentage // "",
  .rate_limits.seven_day.resets_at // "",
  .context_window.used_percentage // ""
] | @tsv')
IFS=$'\t' read -r model effort new_five_used new_five_reset new_week_used new_week_reset new_ctx_pct <<< "$parsed"

# --- 使用量データを共有キャッシュに書き出す（値がある場合のみ上書き）---
if [ -n "$new_five_used" ] || [ -n "$new_week_used" ] || [ -n "$new_ctx_pct" ]; then
  if [ -f "$CACHE_FILE" ]; then
    old=$(cat "$CACHE_FILE")
  else
    old='{}'
  fi
  if ! echo "$old" | jq -e . >/dev/null 2>&1; then
    old='{}'
  fi
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
  echo "$new_cache" > "${CACHE_FILE}.tmp" && mv "${CACHE_FILE}.tmp" "$CACHE_FILE"
fi

# ISO 8601 形式の日時を Unix epoch に変換する関数（取得時のみ呼ぶ）
iso_to_epoch() {
  python3 -c "import datetime,sys; s=sys.argv[1].replace('Z','+00:00'); print(int(datetime.datetime.fromisoformat(s).timestamp()))" "$1" 2>/dev/null
}

# --- OAuth APIから正確な使用量データを取得（claude.aiと同じ値）---
oauth_data=""
oauth_age=99999
if [ -f "$OAUTH_CACHE" ] && [ -s "$OAUTH_CACHE" ]; then
  oauth_age=$(($(date +%s) - $(get_mtime "$OAUTH_CACHE")))
fi

if [ "$oauth_age" -lt "$OAUTH_CACHE_TTL" ]; then
  oauth_data=$(cat "$OAUTH_CACHE")
elif [ -f "$CREDENTIALS" ]; then
  oauth_token=$(jq -r '.claudeAiOauth.accessToken // empty' "$CREDENTIALS" 2>/dev/null)
  if [ -n "$oauth_token" ]; then
    fresh=$(curl -s --max-time 4 \
      -H "Authorization: Bearer $oauth_token" \
      -H "anthropic-version: 2023-06-01" \
      -H "anthropic-beta: oauth-2025-04-20" \
      -H "User-Agent: claude-cli/2.1.119 (external, cli)" \
      "https://api.anthropic.com/api/oauth/usage" 2>/dev/null)
    if [ -n "$fresh" ] && echo "$fresh" | jq -e '.five_hour' >/dev/null 2>&1; then
      fh_iso=$(echo "$fresh" | jq -r '.five_hour.resets_at // empty')
      sd_iso=$(echo "$fresh" | jq -r '.seven_day.resets_at // empty')
      fh_ep=""; sd_ep=""
      [ -n "$fh_iso" ] && fh_ep=$(iso_to_epoch "$fh_iso")
      [ -n "$sd_iso" ] && sd_ep=$(iso_to_epoch "$sd_iso")
      fresh=$(echo "$fresh" | jq \
        --arg fh "$fh_ep" --arg sd "$sd_ep" '
          (if $fh != "" then .five_hour.resets_epoch = ($fh | tonumber) else . end) |
          (if $sd != "" then .seven_day.resets_epoch = ($sd | tonumber) else . end)')
      echo "$fresh" > "${OAUTH_CACHE}.tmp" && mv "${OAUTH_CACHE}.tmp" "$OAUTH_CACHE"
      oauth_data="$fresh"
    elif [ -f "$OAUTH_CACHE" ]; then
      oauth_data=$(cat "$OAUTH_CACHE")
    fi
  fi
fi

# --- 表示用キャッシュの読み込み（OAuth取得失敗時のフォールバック用）---
cached=""
if [ -f "$CACHE_FILE" ] && [ -s "$CACHE_FILE" ]; then
  raw=$(cat "$CACHE_FILE")
  if echo "$raw" | jq -e . >/dev/null 2>&1; then
    cached="$raw"
  fi
fi

# --- 表示する値を決定（優先順位: OAuth API > stdin入力 > キャッシュ）---
five_used=""; five_reset=""; week_used=""; week_reset=""
if [ -n "$oauth_data" ] && echo "$oauth_data" | jq -e '.five_hour' >/dev/null 2>&1; then
  IFS=$'\t' read -r five_used five_reset week_used week_reset <<< "$(echo "$oauth_data" | jq -r '[
    .five_hour.utilization // "",
    .five_hour.resets_epoch // "",
    .seven_day.utilization // "",
    .seven_day.resets_epoch // ""
  ] | @tsv')"
fi

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
  local reset_epoch=$1
  [ -z "$reset_epoch" ] && echo "" && return
  local now_epoch
  now_epoch=$(date +%s)
  local diff=$((reset_epoch - now_epoch))
  if [ "$diff" -le 0 ]; then
    echo "soon"
  elif [ "$diff" -lt 3600 ]; then
    echo "$((diff / 60))m"
  elif [ "$diff" -lt 86400 ]; then
    echo "$((diff / 3600))h$(((diff % 3600) / 60))m"
  else
    echo "$((diff / 86400))d$(((diff % 86400) / 3600))h"
  fi
}

# パーセント(0〜100)を半角メーターに変換する関数（例: 40 → ####------ 40%）
# 半角ASCII記号(#と-)のみ使用。█░は日本語端末で全角幅になり行が崩れるため使わない
make_meter() {
  local pct="$1"
  local width=10
  # pctを0〜100にそろえて整数化（空文字や異常値でも崩れない）
  local p
  p=$(awk -v x="$pct" 'BEGIN{ if(x=="") x=0; if(x<0) x=0; if(x>100) x=100; printf "%d", x+0.5 }')
  # 塗りつぶす個数（幅10のうち何個か）
  local filled
  filled=$(awk -v p="$p" -v w="$width" 'BEGIN{ printf "%d", p/100*w + 0.5 }')
  local empty=$((width - filled))
  # ループで1文字ずつ確実に組み立てる
  local bar=""
  local i=0
  while [ "$i" -lt "$filled" ]; do bar="${bar}#"; i=$((i + 1)); done
  i=0
  while [ "$i" -lt "$empty" ]; do bar="${bar}-"; i=$((i + 1)); done
  printf "%s%s %s%%%s" "$GREEN" "$bar" "$p" "$RESET"
}

# --- 各メーター文字列を組み立てる ---
five_str=""
if [ -n "$five_used" ]; then
  five_meter=$(make_meter "$five_used")
  five_time=$(format_reset "$five_reset")
  five_str="5h:${five_meter}"
  [ -n "$five_time" ] && five_str="${five_str}(${five_time})"
fi

week_str=""
if [ -n "$week_used" ]; then
  week_meter=$(make_meter "$week_used")
  week_time=$(format_reset "$week_reset")
  week_str="7d:${week_meter}"
  [ -n "$week_time" ] && week_str="${week_str}(${week_time})"
fi

# コンテキスト使用率
ctx_info=""
if [ -n "$used_pct" ]; then
  ctx_info="ctx:$(printf '%.0f' "$used_pct")%"
fi

# --- 最終同期時刻をログから取得 ---
SYNC_LOG="$HOME/sync_log.txt"
last_sync=""
if [ -f "$SYNC_LOG" ]; then
  last_sync=$(grep -E '^\[[0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{2}:[0-9]{2}\]' "$SYNC_LOG" | tail -1 | grep -oE '[0-9]{2}:[0-9]{2}' | head -1)
fi

# --- 出力を3行に組み立てる ---
# 1行目: 日時 + 同期時刻
line1=""
[ -n "$today" ] && line1="${CYAN}${today}${RESET}"
[ -n "$last_sync" ] && line1="${line1} | Sync: ${last_sync}"

# 2行目: モデル + effort + コンテキスト
line2=""
[ -n "$model" ] && line2="$model"
[ -n "$effort" ] && line2="${line2} | ${effort}"
[ -n "$ctx_info" ] && line2="${line2} | ${ctx_info}"

# 3行目: 7d(週間) と 5h(5時間) を1行に。7dを左、5hを右。先頭スペースなしで左端そろえ
line3=""
[ -n "$week_str" ] && line3="$week_str"
[ -n "$five_str" ] && line3="${line3:+$line3  }$five_str"

# 日時 → モデル → 使用量メーター の順で3行出力（末尾改行なし）
printf "%s\n%s\n%s" "$line1" "$line2" "$line3"
