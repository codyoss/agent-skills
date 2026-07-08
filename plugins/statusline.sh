#!/bin/bash
set -euo pipefail

# ─── Options & Configuration ──────────────────────────────────────────────────
USE_NERD_FONTS=${USE_NERD_FONTS:-true}
COLOR_MODE=${COLOR_MODE:-truecolor} # truecolor | 16
ICON_WIDTH_ADJUST=${ICON_WIDTH_ADJUST:-0} # Adjust if icons occupy double-width
MARGIN=8 # Terminal width margin safety

# Parse parameters (e.g. statusline.sh --no-nerd --classic)
for arg in "$@"; do
  case "$arg" in
    --no-nerd|--no-nerdfont) USE_NERD_FONTS=false ;;
    --classic|--16color)     COLOR_MODE=16 ;;
  esac
done

# Read JSON payload from stdin
INPUT_JSON=$(cat)
SANDBOX_LOG="$HOME/.gemini/antigravity-cli/cli.log"

# ─── Icons & Glyphs ──────────────────────────────────────────────────────────
if [ "$USE_NERD_FONTS" = "true" ]; then
  ICON_READY=""
  ICON_THINKING="󰟷"
  ICON_WORKING=""
  ICON_TOOL=""
  ICON_UNKNOWN=""
  
  ICON_FOLDER=""
  ICON_MODEL=""
  ICON_BRANCH=""
  ICON_CONV="󰍪"
  ICON_CTX="󱍏"
  ICON_TOK=""
  ICON_ART=""
  ICON_SUB="󱙺"
  ICON_BG=""
  
  ICON_SB_NET="󰒙"
  ICON_SB_NONET="󰴴"
  ICON_SB_OFF="󰦜"
  ICON_YOLO="⚠"
else
  ICON_READY="🟢"
  ICON_THINKING="💭"
  ICON_WORKING="⚙"
  ICON_TOOL="⚒"
  ICON_UNKNOWN="⏳"
  
  ICON_FOLDER="📁"
  ICON_MODEL="💡"
  ICON_BRANCH="⎇"
  ICON_CONV="💬"
  ICON_CTX="📊"
  ICON_TOK="🪙"
  ICON_ART="📄"
  ICON_SUB="🤖"
  ICON_BG="📋"
  
  ICON_SB_NET="📦"
  ICON_SB_NONET="📦🔒"
  ICON_SB_OFF="🚫"
  ICON_YOLO="⚠"
fi

# ─── Single-Pass JSON Parsing ─────────────────────────────────────────────────
{
  read -r STATE
  read -r USED_PCT
  read -r VCS_BRANCH
  read -r VCS_DIRTY
  read -r VCS_TYPE
  read -r VCS_CLIENT
  read -r SANDBOX
  read -r SANDBOX_NET
  read -r ARTIFACTS
  read -r SUBAGENTS
  read -r BG_TASKS
  read -r MODEL_ID
  read -r MODEL_NAME
  read -r COLS
  read -r CWD
  read -r CONV_ID
  read -r PRODUCT
  read -r INPUT_TOKENS
  read -r OUTPUT_TOKENS
  read -r CTX_LIMIT
  read -r CTX_USED
  read -r REM_PCT
  read -r QUOTA_5H_FRAC
  read -r QUOTA_5H_NAME
  read -r QUOTA_5H_RESET
} <<< "$(
  echo "$INPUT_JSON" | jq -r '
    (.agent_state // "idle"),
    (.context_window.used_percentage // 0),
    (.vcs.branch // ""),
    (.vcs.dirty // false),
    (.vcs.type // ""),
    (.vcs.client // ""),
    (.sandbox.enabled // false),
    (.sandbox.allow_network // false),
    (.artifact_count // 0),
    (if .subagents | type == "array" then (.subagents | length) else 0 end),
    (.task_count // 0),
    (.model.id // ""),
    (.model.display_name // ""),
    (.terminal_width // 80),
    (.cwd // ""),
    (.conversation_id // ""),
    (.product // ""),
    (.context_window.total_input_tokens // 0),
    (.context_window.total_output_tokens // 0),
    (.context_window.context_window_size // 0),
    ((.context_window.total_input_tokens // 0) + (.context_window.total_output_tokens // 0)),
    (.context_window.remaining_percentage // 100),
    (.model.display_name // .model.id // "") as $disp
    | [$disp | ascii_downcase | scan("[a-z0-9]+")] as $mt
    | ((.quota // {}) | to_entries | map(select(.value.remaining_fraction != null))) as $raw_entries
    | (if ($raw_entries | map(select(.key | ascii_downcase | contains("3p") | not)) | length) > 0 then
         $raw_entries | map(select(.key | ascii_downcase | contains("3p") | not))
       else
         $raw_entries
       end) as $entries
    | ($entries
        | map(. + {kt: [.key | scan("[a-z0-9]+")]})
        | map(. + {matched: ([.kt[] | select(. as $t | $mt | index($t))] | length)})) as $scored
    | ([$scored[] | select(.matched >= 2)]
        | sort_by((.matched * 100) + (.matched / (.kt | length))) | reverse | .[0]) as $bymatch
    | ($entries | sort_by(.value.remaining_fraction) | .[0]) as $bydepleted
    | ($bymatch // $bydepleted) as $q
    | ($q.value.remaining_fraction // -1),
    ($q.key // ""),
    ($q.value.reset_in_seconds // 0)
  ' 2>/dev/null || printf "idle\n0\n\nfalse\n\n\nfalse\nfalse\n0\n0\n0\n\n\n80\n\n\n\n0\n0\n0\n0\n100\n-1\n\n0\n"
)"

# ─── Live VCS Info ──────────────────────────────────────────────────────────
GIT_DIR="${CWD:-.}"
VCS_BRANCH=$(git -C "$GIT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "$VCS_BRANCH")
if [ -n "$VCS_BRANCH" ]; then
  VCS_TYPE="git"
  if git -C "$GIT_DIR" status --porcelain 2>/dev/null | grep -q .; then
    VCS_DIRTY="true"
  else
    VCS_DIRTY="false"
  fi
fi

# ─── Truecolor Pill Formatter ────────────────────────────────────────────────
pill() {
  local type=$1
  local status=$2
  local content=$3
  
  local bg fg
  if [ "$COLOR_MODE" = "truecolor" ]; then
    case "$type" in
      state)
        case "$status" in
          idle)     bg="16;185;129"; fg="17;24;39" ;;   # Emerald Green / Dark Slate
          thinking) bg="245;158;11"; fg="17;24;39" ;;   # Amber Orange / Dark Slate
          working)  bg="59;130;246"; fg="255;255;255" ;; # Royal Blue / White
          tool_use) bg="139;92;246"; fg="255;255;255" ;; # Purple / White
          yolo)     bg="239;68;68";  fg="255;255;255" ;; # Red / White
          *)        bg="107;114;128"; fg="255;255;255" ;;
        esac
        ;;
      cwd)          bg="55;65;81"; fg="243;244;246" ;;   # Steel Gray / Ice White
      branch)
        case "$status" in
          dirty)    bg="153;27;27"; fg="254;240;138" ;;  # Dark Maroon / Soft Yellow
          *)        bg="30;58;138"; fg="191;219;254" ;;  # Deep Blue / Light Blue
        esac
        ;;
      model)        bg="76;29;149"; fg="237;233;254" ;;  # Indigo / Soft Lavender
      sandbox)
        case "$status" in
          net)      bg="6;95;70"; fg="255;255;255" ;;    # Green / White
          nonet)    bg="3;105;161"; fg="255;255;255" ;;  # Teal / White
          *)        bg="127;29;29"; fg="209;213;219" ;;  # Maroon / Silver
        esac
        ;;
    esac
    
    local esc_bg="\033[48;2;${bg}m"
    local esc_fg="\033[38;2;${fg}m"
    local esc_bg_fg="\033[38;2;${bg}m"
    
    if [ "$USE_NERD_FONTS" = "true" ]; then
      echo -ne "\033[0m${esc_bg_fg}\033[0m${esc_bg}${esc_fg}${content}\033[0m${esc_bg_fg}\033[0m"
    else
      echo -ne "\033[0m${esc_bg}${esc_fg}[${content}]\033[0m"
    fi
  else
    # 16 Color Fallback
    local esc_bg esc_fg
    case "$type" in
      state)
        case "$status" in
          idle)     esc_bg="\033[42m"; esc_fg="\033[30m" ;;
          thinking) esc_bg="\033[43m"; esc_fg="\033[30m" ;;
          working)  esc_bg="\033[44m"; esc_fg="\033[37m" ;;
          tool_use) esc_bg="\033[45m"; esc_fg="\033[37m" ;;
          yolo)     esc_bg="\033[41m"; esc_fg="\033[37m" ;;
          *)        esc_bg="\033[47m"; esc_fg="\033[30m" ;;
        esac
        ;;
      cwd)          esc_bg="\033[40m"; esc_fg="\033[37m" ;;
      branch)
        case "$status" in
          dirty)    esc_bg="\033[41m"; esc_fg="\033[33m" ;;
          *)        esc_bg="\033[44m"; esc_fg="\033[36m" ;;
        esac
        ;;
      model)        esc_bg="\033[45m"; esc_fg="\033[37m" ;;
      sandbox)
        case "$status" in
          net)      esc_bg="\033[42m"; esc_fg="\033[37m" ;;
          nonet)    esc_bg="\033[46m"; esc_fg="\033[37m" ;;
          *)        esc_bg="\033[41m"; esc_fg="\033[37m" ;;
        esac
        ;;
    esac
    echo -ne "\033[0m${esc_bg}${esc_fg}[${content}]\033[0m"
  fi
}

# ─── Formatting Helpers ──────────────────────────────────────────────────────
human_format() {
  local num=$1
  if [ -z "$num" ] || [ "$num" -eq 0 ] 2>/dev/null; then
    echo "0"
    return
  fi
  if [ "$num" -ge 1000000 ] 2>/dev/null; then
    echo "$((num / 1000000)).$(((num % 1000000) / 100000))M"
  elif [ "$num" -ge 1000 ] 2>/dev/null; then
    echo "$((num / 1000)).$(((num % 1000) / 100))K"
  else
    echo "$num"
  fi
}

fmt_seconds() {
  local s=$1
  if [ -z "$s" ] || [ "$s" -le 0 ] 2>/dev/null; then
    echo "0s"
    return
  fi
  if [ "$s" -ge 3600 ]; then
    echo "$((s / 3600))h$(( (s % 3600) / 60 ))m"
  elif [ "$s" -ge 60 ]; then
    echo "$((s / 60))m"
  else
    echo "${s}s"
  fi
}

float_to_pct() {
  local val=$1
  if [ -z "$val" ] || [ "$val" = "-1" ]; then
    echo "-1"
    return
  fi
  if [[ "$val" =~ ^\.[0-9]+$ ]]; then
    val="0$val"
  fi
  if [[ "$val" =~ ^1(\.0+)?$ ]]; then
    echo "100"
    return
  fi
  if [[ "$val" =~ ^0(\.0+)?$ ]]; then
    echo "0"
    return
  fi
  if [[ "$val" =~ ^0\.([0-9]+)$ ]]; then
    local frac="${BASH_REMATCH[1]}"
    if [ "${#frac}" -eq 1 ]; then
      echo "${frac}0"
    else
      local pct="${frac:0:2}"
      if [[ "$pct" =~ ^0[1-9]$ ]]; then
        pct="${pct#0}"
      elif [ "$pct" = "00" ]; then
        pct="0"
      fi
      echo "$pct"
    fi
    return
  fi
  echo "-1"
}

shorten_path() {
  local path=$1
  local max_len=$2
  if [ -z "$path" ]; then
    echo ""
    return
  fi
  path="${path/#$HOME/\~}"
  if [ "$max_len" -eq 0 ]; then
    if [ "$path" = "~" ]; then
      echo "~"
    else
      basename "$path"
    fi
  elif [ "${#path}" -gt "$max_len" ]; then
    echo "...$(basename "$path")"
  else
    echo "$path"
  fi
}

# ─── Dynamic Progress Bar ────────────────────────────────────────────────────
make_progress_bar() {
  local len=$1
  local pct=${2%.*}
  pct=${pct:-0}
  local filled=$((pct * len / 100))
  local remainder=$(( (pct * len) % 100 ))
  
  local r g b
  if [ "$pct" -ge 85 ]; then
    r=239; g=68; b=68      # Red
  elif [ "$pct" -ge 60 ]; then
    r=245; g=158; b=11     # Amber
  else
    r=16; g=185; b=129     # Emerald
  fi
  
  local bar=""
  for ((i=0; i<len; i++)); do
    if [ "$i" -lt "$filled" ]; then
      if [ "$COLOR_MODE" = "truecolor" ]; then
        bar="${bar}\033[38;2;${r};${g};${b}m█"
      else
        bar="${bar}\033[33m█"
      fi
    elif [ "$i" -eq "$filled" ] && [ "$remainder" -gt 0 ]; then
      local block="░"
      if [ "$remainder" -ge 75 ]; then block="▓"; fi
      if [ "$remainder" -ge 50 ]; then block="▒"; fi
      
      if [ "$COLOR_MODE" = "truecolor" ]; then
        bar="${bar}\033[38;2;${r};${g};${b}m${block}"
      else
        bar="${bar}\033[33m${block}"
      fi
    else
      if [ "$COLOR_MODE" = "truecolor" ]; then
        bar="${bar}\033[38;2;107;114;128m░"
      else
        bar="${bar}\033[90m░"
      fi
    fi
  done
  echo -ne "${bar}\033[0m"
}

# ─── Visible Length Estimator ────────────────────────────────────────────────
visible_len() {
  local clean_str
  clean_str=$(echo -e "$1" | sed 's/\x1b\[[0-9;]*m//g')
  local base_len=${#clean_str}
  local only_icons="${clean_str//[^󰟷󰒙󰴴󰦜󱍏󱙺󰍪🟢💭⚙⚒⏳📁💡⎇💬📦🔒🚫📊📄🤖📋🪙⚠]/}"
  local icon_count=${#only_icons}
  echo $((base_len + icon_count * ICON_WIDTH_ADJUST))
}

# ─── Right-Align Printer ─────────────────────────────────────────────────────
print_right_aligned() {
  local left="$1"
  local right="$2"
  local total_cols="$3"
  
  local left_vis right_vis pad
  left_vis=$(visible_len "$left")
  right_vis=$(visible_len "$right")
  
  pad=$(( total_cols - left_vis - right_vis ))
  [ "$pad" -lt 1 ] && pad=1
  
  printf "%b%*s%b\n" "$left" "$pad" "" "$right"
}

# ─── Component Builders ──────────────────────────────────────────────────────
# CWD
CWD_WIDE_VAL=$(shorten_path "$CWD" 25)
DIR_WIDE=""
[ -n "$CWD_WIDE_VAL" ] && DIR_WIDE=$(pill cwd default "$ICON_FOLDER $CWD_WIDE_VAL")
CWD_MED_VAL=$(shorten_path "$CWD" 15)
DIR_MED=""
[ -n "$CWD_MED_VAL" ] && DIR_MED=$(pill cwd default "$ICON_FOLDER $CWD_MED_VAL")
CWD_NARROW_VAL=$(shorten_path "$CWD" 0)
DIR_NARROW=""
[ -n "$CWD_NARROW_VAL" ] && DIR_NARROW=$(pill cwd default "$ICON_FOLDER $CWD_NARROW_VAL")

# Model
MODEL_RAW="${MODEL_NAME:-$MODEL_ID}"
MODEL_CLEAN=$(echo "$MODEL_RAW" | sed -E 's/^Gemini //; s/ \([^)]+\)//' || echo "")
M_WIDE=""
[ -n "$MODEL_RAW" ] && M_WIDE=$(pill model default "$ICON_MODEL $MODEL_RAW")
M_MED=""
[ -n "$MODEL_CLEAN" ] && M_MED=$(pill model default "$ICON_MODEL $MODEL_CLEAN")
M_NARROW=""
[ -n "$MODEL_CLEAN" ] && M_NARROW=$(pill model default "$ICON_MODEL ${MODEL_CLEAN:0:10}")

# VCS Branch
if [ -n "$VCS_BRANCH" ]; then
  V_DIRTY="clean"
  [ "$VCS_DIRTY" = "true" ] && V_DIRTY="dirty"
  
  branch_txt_wide="$ICON_BRANCH $VCS_BRANCH"
  [ "$VCS_DIRTY" = "true" ] && branch_txt_wide="$ICON_BRANCH $VCS_BRANCH*"
  V_WIDE=$(pill branch "$V_DIRTY" "$branch_txt_wide")
  
  branch_txt_med="$ICON_BRANCH ${VCS_BRANCH:0:10}"
  [ "$VCS_DIRTY" = "true" ] && branch_txt_med="$ICON_BRANCH ${VCS_BRANCH:0:10}*"
  V_MED=$(pill branch "$V_DIRTY" "$branch_txt_med")
  
  branch_txt_narrow="$ICON_BRANCH ${VCS_BRANCH:0:6}"
  [ "$VCS_DIRTY" = "true" ] && branch_txt_narrow="$ICON_BRANCH ${VCS_BRANCH:0:6}*"
  V_NARROW=$(pill branch "$V_DIRTY" "$branch_txt_narrow")
else
  V_WIDE=""
  V_MED=""
  V_NARROW=""
fi

# Conversation ID
CONV_WIDE=""
[ -n "$CONV_ID" ] && CONV_WIDE="\033[90m${ICON_CONV} ${CONV_ID:0:8}\033[0m"
CONV_MED=""
[ -n "$CONV_ID" ] && CONV_MED="\033[90m${ICON_CONV} ${CONV_ID:0:4}\033[0m"

# Sandbox
format_sandbox() {
  local mode=$1
  if [ "$SANDBOX" != "true" ]; then
    if [ -r "$SANDBOX_LOG" ] && grep -q 'enabling terminal sandbox' "$SANDBOX_LOG" 2>/dev/null; then
      SANDBOX="true"
    fi
  fi
  if [ "$SANDBOX_NET" != "true" ]; then
    local settings_file="$HOME/.gemini/antigravity-cli/settings.json"
    if [ -r "$settings_file" ] && jq -e '.sandboxAllowNetwork == true' "$settings_file" >/dev/null 2>&1; then
      SANDBOX_NET="true"
    fi
  fi

  if [ "$SANDBOX" = "true" ]; then
    local icon="$ICON_SB_NET"
    local status="net"
    [ "$SANDBOX_NET" = "false" ] && icon="$ICON_SB_NONET" && status="nonet"
    
    if [ "$mode" = "wide" ]; then
      pill sandbox "$status" "$icon ON (${status})"
    elif [ "$mode" = "med" ]; then
      pill sandbox "$status" "$icon ON"
    else
      pill sandbox "$status" "$icon"
    fi
  else
    if [ "$mode" = "wide" ] || [ "$mode" = "med" ]; then
      pill sandbox "off" "$ICON_SB_OFF OFF"
    else
      pill sandbox "off" "$ICON_SB_OFF"
    fi
  fi
}
SB_WIDE=$(format_sandbox "wide")
SB_MED=$(format_sandbox "med")
SB_NARROW=$(format_sandbox "narrow")

# Agent State & YOLO check
case "$STATE" in
  idle)     STATE_VAL="idle"; STATE_TXT="READY" ;;
  thinking) STATE_VAL="thinking"; STATE_TXT="THINKING" ;;
  working)  STATE_VAL="working"; STATE_TXT="WORKING" ;;
  tool_use) STATE_VAL="tool_use"; STATE_TXT="TOOL USE" ;;
  *)        STATE_VAL="unknown"; STATE_TXT=$(echo "$STATE" | tr '[:lower:]' '[:upper:]') ;;
esac

S=$(pill state "$STATE_VAL" "$ICON_READY $STATE_TXT")
if [ -r "$SANDBOX_LOG" ] && grep -q 'dangerously-skip-permissions: auto-approving' "$SANDBOX_LOG" 2>/dev/null; then
  S="$(pill state yolo "${ICON_YOLO} YOLO") $S"
fi

# Counts
C_COLOR_A="\033[38;2;59;130;246m" # blue
C_COLOR_S="\033[38;2;6;182;212m"  # cyan
C_COLOR_B="\033[38;2;217;70;239m" # magenta
[ "$COLOR_MODE" != "truecolor" ] && C_COLOR_A="\033[34m" && C_COLOR_S="\033[36m" && C_COLOR_B="\033[35m"

ART_WIDE="${C_COLOR_A}${ICON_ART}\033[0m \033[1m${ARTIFACTS}\033[0m"
SUB_WIDE="${C_COLOR_S}${ICON_SUB}\033[0m \033[1m${SUBAGENTS}\033[0m"
BG_WIDE="${C_COLOR_B}${ICON_BG}\033[0m \033[1m${BG_TASKS}\033[0m"

ART_MED="$ART_WIDE"
SUB_MED="$SUB_WIDE"
BG_MED="$BG_WIDE"

ART_NARROW="${C_COLOR_A}${ICON_ART}\033[0m\033[1m${ARTIFACTS}\033[0m"
SUB_NARROW="${C_COLOR_S}${ICON_SUB}\033[0m\033[1m${SUBAGENTS}\033[0m"
BG_NARROW="${C_COLOR_B}${ICON_BG}\033[0m\033[1m${BG_TASKS}\033[0m"

# Context Bar
PCT_FMT=$(printf "%.1f" "$USED_PCT")
PCT_INT=${USED_PCT%.*}; PCT_INT=${PCT_INT:-0}
BAR_WIDE=$(make_progress_bar 10 "$PCT_INT")
BAR_MED=$(make_progress_bar 6 "$PCT_INT")
BAR_NARROW=$(make_progress_bar 4 "$PCT_INT")

CTX_COLOR="\033[38;2;245;158;11m"
[ "$COLOR_MODE" != "truecolor" ] && CTX_COLOR="\033[33m"

CTX_BAR_WIDE="${CTX_COLOR}${ICON_CTX}\033[0m ${BAR_WIDE} \033[1m${PCT_FMT}%\033[0m"
CTX_BAR_MED="${CTX_COLOR}${ICON_CTX}\033[0m ${BAR_MED} \033[1m${PCT_INT}%\033[0m"
CTX_BAR_NARROW="${CTX_COLOR}${ICON_CTX}\033[0m ${BAR_NARROW} \033[1m${PCT_INT}%\033[0m"

INPUT_TOK_FMT=$(human_format "$INPUT_TOKENS")
OUTPUT_TOK_FMT=$(human_format "$OUTPUT_TOKENS")
CTX_LIMIT_FMT=$(human_format "$CTX_LIMIT")
CTX_USED_FMT=$(human_format "$CTX_USED")

TOK_DETAILS_WIDE=""
if [ "$CTX_USED" -gt 0 ] 2>/dev/null; then
  TOK_DETAILS_WIDE=" \033[90m(${CTX_USED_FMT}/${CTX_LIMIT_FMT})\033[0m \033[90m| ${CTX_COLOR}${ICON_TOK}\033[0m \033[90m(${INPUT_TOK_FMT} in/${OUTPUT_TOK_FMT} out)\033[0m"
fi
TOK_DETAILS_MED=""
if [ "$CTX_USED" -gt 0 ] 2>/dev/null; then
  TOK_DETAILS_MED=" \033[90m(${CTX_USED_FMT})\033[0m"
fi

# Quota
format_quota() {
  local mode=$1
  local pct
  pct=$(float_to_pct "$QUOTA_5H_FRAC")
  if [ "$pct" = "-1" ] || [ -z "$pct" ]; then
    echo ""
    return
  fi
  
  local q_reset
  q_reset=$(fmt_seconds "$QUOTA_5H_RESET")
  local q_label="${QUOTA_5H_NAME#gemini-}"
  
  local r g b
  if [ "$pct" -le 15 ]; then
    r=239; g=68; b=68
  elif [ "$pct" -le 45 ]; then
    r=6; g=182; b=212
  else
    r=16; g=185; b=129
  fi
  
  local q_color="\033[38;2;6;182;212m"
  local pct_color="\033[1;38;2;${r};${g};${b}m"
  [ "$COLOR_MODE" != "truecolor" ] && q_color="\033[36m" && pct_color="\033[1m"
  
  if [ "$mode" = "narrow" ]; then
    echo -e "${q_color}${ICON_UNKNOWN}\033[0m ${pct_color}${pct}%\033[0m \033[90m${q_reset}\033[0m"
    return
  fi
  
  local len=10
  [ "$mode" = "med" ] && len=6
  local bar
  bar=$(make_progress_bar "$len" "$pct")
  local label_part=""
  [ -n "$q_label" ] && label_part=" \033[90m${q_label}\033[0m"
  
  echo -e "${q_color}${ICON_UNKNOWN}\033[0m ${bar} ${pct_color}${pct}%\033[0m${label_part} \033[90m${q_reset}\033[0m"
}
QUOTA_WIDE=$(format_quota "wide")
QUOTA_MED=$(format_quota "med")
QUOTA_NARROW=$(format_quota "narrow")

# ─── Joining Separators ──────────────────────────────────────────────────────
DOT=" \033[90m|\033[0m "

join_with_dot() {
  local result=""
  local item
  for item in "$@"; do
    if [ -n "$item" ]; then
      if [ -z "$result" ]; then
        result="$item"
      else
        result="${result}${DOT}${item}"
      fi
    fi
  done
  echo -e "$result"
}

join_with_space() {
  local result=""
  local item
  for item in "$@"; do
    if [ -n "$item" ]; then
      if [ -z "$result" ]; then
        result="$item"
      else
        result="${result}  ${item}"
      fi
    fi
  done
  echo -e "$result"
}

# ─── Layout Assembly ─────────────────────────────────────────────────────────
if ! [[ "$COLS" =~ ^[0-9]+$ ]] 2>/dev/null; then
  COLS=80
fi

# Define rows
LINE1_WIDE=$(join_with_dot "$S" "$M_WIDE" "$DIR_WIDE" "$V_WIDE" "$CONV_WIDE")
LINE2_WIDE=$(join_with_dot "$ART_WIDE" "$SUB_WIDE" "$BG_WIDE" "$SB_WIDE" "${CTX_BAR_WIDE}${TOK_DETAILS_WIDE}" "$QUOTA_WIDE")

LINE1_MED=$(join_with_dot "$S" "$M_MED" "$DIR_MED" "$V_MED")
LINE2_MED=$(join_with_dot "$ART_MED" "$SUB_MED" "$BG_MED" "$SB_MED" "${CTX_BAR_MED}${TOK_DETAILS_MED}" "$QUOTA_MED")

# Check visibility sizes
LEN1_WIDE=$(visible_len "$LINE1_WIDE")
LEN2_WIDE=$(visible_len "$LINE2_WIDE")

if [ "$COLS" -ge 135 ] && [ "$COLS" -ge $((LEN1_WIDE + LEN2_WIDE + MARGIN)) ]; then
  # 1. Single-Row Wide truecolor pill layout
  print_right_aligned "$LINE1_WIDE" "$LINE2_WIDE" "$COLS"
   elif [ "$COLS" -ge 100 ]; then
  # 2. Double-Row Parallel Wide Layout
  R1_LEFT=$(join_with_dot "$S" "$M_WIDE")
  R1_RIGHT=$(join_with_dot "$ART_WIDE" "$SUB_WIDE" "$BG_WIDE" "$SB_WIDE")
  R2_LEFT=$(join_with_dot "$DIR_WIDE" "$V_WIDE" "$CONV_WIDE")
  R2_RIGHT=$(join_with_dot "${CTX_BAR_WIDE}${TOK_DETAILS_WIDE}" "$QUOTA_WIDE")
  print_right_aligned "$R1_LEFT" "$R1_RIGHT" "$COLS"
  print_right_aligned "$R2_LEFT" "$R2_RIGHT" "$COLS"
elif [ "$COLS" -ge 75 ]; then
  # 3. Double-Row Parallel Medium Layout
  R1_LEFT=$(join_with_dot "$S" "$M_MED")
  R1_RIGHT=$(join_with_dot "$ART_MED" "$SUB_MED" "$BG_MED" "$SB_MED")
  R2_LEFT=$(join_with_dot "$DIR_MED" "$V_MED" "$CONV_MED")
  R2_RIGHT=$(join_with_dot "${CTX_BAR_MED}${TOK_DETAILS_MED}" "$QUOTA_MED")
  print_right_aligned "$R1_LEFT" "$R1_RIGHT" "$COLS"
  print_right_aligned "$R2_LEFT" "$R2_RIGHT" "$COLS"
elif [ "$COLS" -ge 50 ]; then
  # 4. Double-Row Parallel Narrow Layout
  R1_LEFT=$(join_with_dot "$S" "$M_NARROW")
  R1_RIGHT=$(join_with_space "$ART_NARROW" "$SUB_NARROW" "$BG_NARROW" "$SB_NARROW")
  R2_LEFT=$(join_with_dot "$DIR_NARROW" "$V_NARROW")
  R2_RIGHT=$(join_with_dot "${CTX_BAR_NARROW}" "$QUOTA_NARROW")
  print_right_aligned "$R1_LEFT" "$R1_RIGHT" "$COLS"
  print_right_aligned "$R2_LEFT" "$R2_RIGHT" "$COLS"
else
  # 5. Extreme Minimal Fallback
  M_SHORT=""
  [ -n "$MODEL_CLEAN" ] && M_SHORT=" ╱ ${M_NARROW}"
  echo -e "${S}${M_SHORT}"
  echo -e "${CTX_BAR_NARROW}"
fi
