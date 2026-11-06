#!/usr/bin/env bash
set -euo pipefail

# macOS ships bash 3.2; this installer uses bash 4 features (associative arrays, ${var,,}).
if (( ${BASH_VERSINFO[0]:-0} < 4 )); then
  echo "Error: bash 4+ required (you have ${BASH_VERSION})." >&2
  echo "On macOS install a newer bash: brew install bash" >&2
  echo "Then re-run with: /opt/homebrew/bin/bash install.sh   (or /usr/local/bin/bash on Intel Macs)" >&2
  exit 1
fi

# SSOT Skill bundle installer.

REPO_URL="${SSOT_SKILL_REPO_URL:-https://github.com/huangpufan/SSOT-SKILL.git}"
# Branch or tag to install from (--ref / SSOT_REF). Tags pin a protocol
# generation, e.g. --ref v2-final keeps the v2 protocol after main moved on.
REPO_REF="main"
PRIMARY_SKILL="ssot-preflight"
BUNDLE_SKILLS=(
  "ssot-preflight"
  "ssot-bootstrap"
  "ssot-closeout"
  "ssot-audit"
  "ssot-doctor"
  "ssot-skill"
)
# Bundle-level companion files, installed only when the source ships them.
# Since 3.0 the bundle ships none (SKILL_STYLE.md moved into CONTRIBUTING.md);
# older sources installed with --ref still do. An installed companion the
# source no longer ships is removed if this installer owns it.
BUNDLE_ROOT_FILES=(
  "SKILL_STYLE.md"
)
# Compatibility names that route elsewhere; the instruction block need not
# mention them.
SHIM_SKILLS=("ssot-skill" "ssot-audit")
BUNDLE_COMPANION_MARKER='<!-- SSOT-SKILL bundle companion; owned by install.sh -->'

BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'
CHECK="${GREEN}✓${NC}"
ARROW="${CYAN}›${NC}"

# -----------------------------------------------------------------------------
# Globals populated by argument parsing
# -----------------------------------------------------------------------------
MODE="install"          # install | uninstall | upgrade
ARG_AGENT=""
ARG_SCOPE=""
ARG_LANG=""
ARG_YES=0
ARG_NONINTERACTIVE=0
ARG_UI_LANG=""
ARG_REF=""
SOURCE_DIR="${SOURCE_DIR:-}"
FETCHED_SOURCE_DIR=""
INSTALL_STAGE=""

# Will be filled by detect_agents
DETECTED_AGENTS=()
ARG_QUICKSTART=0

# Read VERSION as early as possible (best-effort; may be refreshed after ensure_source)
read_version_file() {
  local candidate
  if [[ -n "${SOURCE_DIR:-}" && -f "$SOURCE_DIR/VERSION" ]]; then
    candidate="$SOURCE_DIR/VERSION"
  elif [[ -f "$(dirname "${BASH_SOURCE[0]}")/VERSION" ]]; then
    candidate="$(dirname "${BASH_SOURCE[0]}")/VERSION"
  else
    echo "unknown"
    return
  fi
  tr -d '[:space:]' < "$candidate" || echo "unknown"
}
VERSION="$(read_version_file)"
[[ -z "$VERSION" ]] && VERSION="unknown"

# -----------------------------------------------------------------------------
# One cleanup owner for fetched source, staged copies, and the terminal cursor.
# -----------------------------------------------------------------------------
cleanup() {
  [[ -z "$INSTALL_STAGE" ]] || rm -rf -- "$INSTALL_STAGE"
  [[ -z "$FETCHED_SOURCE_DIR" ]] || rm -rf -- "$FETCHED_SOURCE_DIR"
  tput cnorm 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# -----------------------------------------------------------------------------
# Prompt FD setup (handles `curl | bash`)
# -----------------------------------------------------------------------------
PROMPT_FD=0
if [[ ! -t 0 ]]; then
  if { exec 3</dev/tty; } 2>/dev/null; then
    PROMPT_FD=3
  fi
fi

# -----------------------------------------------------------------------------
# UI language detection + string table
# -----------------------------------------------------------------------------
detect_ui_lang() {
  if [[ -n "$ARG_UI_LANG" ]]; then
    SSOT_UI_LANG="$ARG_UI_LANG"
  elif [[ -n "${SSOT_UI_LANG:-}" ]]; then
    : # already exported
  else
    case "${LANG:-}" in
      zh_CN*|zh_TW*|zh_HK*|zh_SG*) SSOT_UI_LANG="zh" ;;
      *) SSOT_UI_LANG="en" ;;
    esac
  fi
  case "$SSOT_UI_LANG" in
    en|zh) ;;
    *) SSOT_UI_LANG="en" ;;
  esac
}

t() {
  local key="$1"
  if [[ "${SSOT_UI_LANG:-en}" == "zh" ]]; then
    case "$key" in
      INSTALL_WHERE) echo "安装到哪里？" ;;
      GLOBAL_SCOPE) echo "全局安装（所有项目）" ;;
      PROJECT_SCOPE) echo "项目安装（当前项目）" ;;
      SELECT_AGENTS) echo "将 bundle 安装到哪些 Agent？" ;;
      SPACE_TOGGLE) echo "（空格切换，回车确认）" ;;
      WILL_INSTALL) echo "将安装以下 skill 作为一个 bundle:" ;;
      TARGETS) echo "目标:" ;;
      CONFIRM_INSTALL) echo "确认安装？" ;;
      YES_INSTALL) echo "是，安装" ;;
      NO_CANCEL) echo "否，取消" ;;
      CANCELLED) echo "已取消" ;;
      FETCHING) echo "正在拉取最新 SSOT Skill bundle..." ;;
      FETCHED) echo "拉取完成" ;;
      INSTALLED) echo "SSOT Skill bundle 已安装" ;;
      RESTART_TIP) echo "合并下方项目指令后，重启 Agent 会话以加载 Skill 和指令。" ;;
      PREFLIGHT_TIP) echo "之后照常提需求；Agent 会在实质性工作前自动使用 \$ssot-preflight。" ;;
      CLOSEOUT_TIP) echo "Agent 会在实质性变更批次的最终回复或提交前自动使用 \$ssot-closeout。" ;;
      UPGRADE_V3_NOTE) echo "这里原来装的是 SSOT Skill 2.x，现在换成 3.x：使用 v2 SSOT 的仓库在迁移前对 Agent 只读，调用 ssot-lint.sh 的脚本会失效。迁移方法见 https://github.com/huangpufan/SSOT-SKILL/blob/main/INSTALL.md#upgrading-from-2x-or-3x-to-40 ；想留在 v2，请带 --ref v2-final 重新运行。" ;;
      UPGRADE_V4_NOTE) echo "SSOT Skill 2.x / 3.x 现在升级到 4.x：旧 v2 / v3 SSOT 在经用户同意迁移前对 Agent 只读。安装技能不迁移项目文档；保留知识、规则状态与原有路径，迁移前将全部写入端升级为 v4。迁移说明：https://github.com/huangpufan/SSOT-SKILL/blob/main/INSTALL.md#upgrading-from-2x-or-3x-to-40 。" ;;
      PROJECT_NOTE) echo "项目级安装仅在 Agent 在该项目根启动时生效。" ;;
      ALSO_GLOBAL_HINT) echo "如需同时全局安装，重新跑命令并追加 --scope global。" ;;
      WIRE_HEADER) echo "下一步：让 Agent 将这段触发指令合并到本仓库的指令文件" ;;
      WIRE_TARGET_HINT) echo "目标文件：CLAUDE.md / AGENTS.md / .cursorrules / GEMINI.md / 等（按你用的 Agent 选）" ;;
      WIRE_SEE_README) echo "由 Agent 合并指令并验证安装：https://github.com/huangpufan/SSOT-SKILL/blob/main/INSTALL.md#4-wire-the-skills-into-the-repos-agent-instructions-file" ;;
      NO_AGENT_DETECTED) echo "未检测到已安装的 Agent" ;;
      SHOWING_ALL) echo "显示所有支持的目标" ;;
      NO_AGENT_SELECTED) echo "未选择任何 Agent" ;;
      LANG_PROMPT) echo "选择模板语言（写入消费仓库的 SSOT 模板）：" ;;
      LANG_EN) echo "English" ;;
      LANG_ZH) echo "中文" ;;
      UNINSTALL_HEADER) echo "将卸载下列目录:" ;;
      CONFIRM_UNINSTALL) echo "确认卸载？" ;;
      UNINSTALLED) echo "已卸载" ;;
      UPGRADE_SCANNING) echo "正在扫描已安装位置..." ;;
      UPGRADE_NONE_FOUND) echo "未找到 SSOT Skill 安装位置；请改用 install" ;;
      UPGRADE_TARGETS) echo "升级目标:" ;;
    esac
  else
    case "$key" in
      INSTALL_WHERE) echo "Install where?" ;;
      GLOBAL_SCOPE) echo "Global install (all projects)" ;;
      PROJECT_SCOPE) echo "Project install (current project)" ;;
      SELECT_AGENTS) echo "Install bundle to which Agents?" ;;
      SPACE_TOGGLE) echo "(space toggles, Enter confirms)" ;;
      WILL_INSTALL) echo "Will install these skills as one bundle:" ;;
      TARGETS) echo "Targets:" ;;
      CONFIRM_INSTALL) echo "Confirm install?" ;;
      YES_INSTALL) echo "Yes, install" ;;
      NO_CANCEL) echo "No, cancel" ;;
      CANCELLED) echo "Cancelled" ;;
      FETCHING) echo "Fetching latest SSOT Skill bundle..." ;;
      FETCHED) echo "Fetched source" ;;
      INSTALLED) echo "SSOT Skill bundle installed" ;;
      RESTART_TIP) echo "Merge the project instructions below, then restart the Agent session to load skills and instructions." ;;
      PREFLIGHT_TIP) echo "Then describe tasks normally; the Agent uses \$ssot-preflight automatically before substantive work." ;;
      CLOSEOUT_TIP) echo "The Agent uses \$ssot-closeout automatically before a substantive batch's final response or commit." ;;
      UPGRADE_V3_NOTE) echo "SSOT Skill 2.x was installed here and is now replaced by 3.x: repositories with a v2 SSOT are read-only for agents until migrated, and scripts that call ssot-lint.sh stop working. Migration: https://github.com/huangpufan/SSOT-SKILL/blob/main/INSTALL.md#upgrading-from-2x-or-3x-to-40 . To stay on v2, re-run with --ref v2-final." ;;
      UPGRADE_V4_NOTE) echo "SSOT Skill 2.x / 3.x is now replaced by 4.x: repositories with a v2 or v3 SSOT are read-only for agents until migrated with user agreement. Installing skills does not migrate project documents; preserve knowledge, rule statuses, and owner paths, and upgrade all writers to v4 first. Migration: https://github.com/huangpufan/SSOT-SKILL/blob/main/INSTALL.md#upgrading-from-2x-or-3x-to-40 ." ;;
      PROJECT_NOTE) echo "Project installs apply only when the Agent starts in this project root." ;;
      ALSO_GLOBAL_HINT) echo "To also install globally, re-run with --scope global appended." ;;
      WIRE_HEADER) echo "Next: ask your Agent to merge this trigger block into this repo's instructions" ;;
      WIRE_TARGET_HINT) echo "Target file: CLAUDE.md / AGENTS.md / .cursorrules / GEMINI.md / etc. (whichever your agent uses)" ;;
      WIRE_SEE_README) echo "Ask your agent to merge the instructions and verify setup: https://github.com/huangpufan/SSOT-SKILL/blob/main/INSTALL.md#4-wire-the-skills-into-the-repos-agent-instructions-file" ;;
      NO_AGENT_DETECTED) echo "No installed Agent detected" ;;
      SHOWING_ALL) echo "Showing all supported targets" ;;
      NO_AGENT_SELECTED) echo "No Agent selected" ;;
      LANG_PROMPT) echo "Select template language (written into consumer repos):" ;;
      LANG_EN) echo "English" ;;
      LANG_ZH) echo "Chinese (中文)" ;;
      UNINSTALL_HEADER) echo "Will remove these directories:" ;;
      CONFIRM_UNINSTALL) echo "Confirm uninstall?" ;;
      UNINSTALLED) echo "Uninstalled" ;;
      UPGRADE_SCANNING) echo "Scanning installed locations..." ;;
      UPGRADE_NONE_FOUND) echo "No SSOT Skill installation found; use install instead" ;;
      UPGRADE_TARGETS) echo "Upgrade targets:" ;;
    esac
  fi
}

# -----------------------------------------------------------------------------
# Output helpers
# -----------------------------------------------------------------------------
banner() {
  local title="SSOT Skill Installer v${VERSION}"
  local sub="split lifecycle skill bundle"
  local title_len=${#title}
  local sub_len=${#sub}
  local inner=$title_len
  (( sub_len > inner )) && inner=$sub_len
  inner=$((inner + 4)) # padding on each side
  local line=""
  local i
  for ((i = 0; i < inner; i++)); do line+="─"; done

  local title_pad=$(((inner - title_len) / 2))
  local title_rpad=$((inner - title_len - title_pad))
  local sub_pad=$(((inner - sub_len) / 2))
  local sub_rpad=$((inner - sub_len - sub_pad))

  echo ""
  echo -e "  ${BOLD}┌${line}┐${NC}"
  printf "  ${BOLD}│%*s%s%*s│${NC}\n" "$title_pad" "" "$title" "$title_rpad" ""
  printf "  ${BOLD}│%*s%s%*s│${NC}\n" "$sub_pad" "" "$sub" "$sub_rpad" ""
  echo -e "  ${BOLD}└${line}┘${NC}"
  echo ""
}

info() { echo -e "  ${ARROW} $*"; }
ok()   { echo -e "  ${CHECK} $*"; }
warn() { echo -e "  ${YELLOW}!${NC} $*"; }
err()  { echo -e "  ${RED}✗${NC} $*" >&2; }
die()  { err "$@"; exit 1; }

# Print the trigger-directive block agents should merge into the repo's
# agent-instructions file. Switches on $1 = lang (en|zh).
print_wire_block() {
  local lang="${1:-en}"
  local block
  block="$(read_wire_block "$lang")" || return 1
  echo ""
  echo -e "  ${BOLD}${YELLOW}━━━ $(t WIRE_HEADER) ━━━${NC}"
  echo -e "  ${DIM}$(t WIRE_TARGET_HINT)${NC}"
  echo ""
  printf '%s\n' "$block"
  echo ""
  echo -e "  ${DIM}$(t WIRE_SEE_README)${NC}"
}

# -----------------------------------------------------------------------------
# Interactive widgets
# -----------------------------------------------------------------------------
read_key() {
  local __var="$1"
  local __count="${2:-1}"
  local __value
  IFS= read -rsn "$__count" -u "$PROMPT_FD" __value || __value=""
  printf -v "$__var" '%s' "$__value"
}

select_one() {
  local prompt="$1"
  shift
  local options=("$@")
  local count=${#options[@]}
  local cur=0
  local key

  echo -e "\n  ${BOLD}${prompt}${NC}\n"
  tput civis 2>/dev/null || true
  while true; do
    local i
    for i in "${!options[@]}"; do
      if [[ $i -eq $cur ]]; then
        echo -e "    ${CYAN}❯ ${options[$i]}${NC}"
      else
        echo -e "    ${DIM}  ${options[$i]}${NC}"
      fi
    done
    read_key key 1
    if [[ "$key" == $'\x1b' ]]; then
      read_key key 2
      case "$key" in
        '[A') ((cur > 0)) && cur=$((cur - 1)) ;;
        '[B') ((cur < count - 1)) && cur=$((cur + 1)) ;;
      esac
    elif [[ -z "$key" ]]; then
      break
    fi
    echo -en "\033[${count}A\r"
  done
  tput cnorm 2>/dev/null || true
  SELECTED_INDEX=$cur
}

select_agents() {
  # Dedicated agent picker. Preselects only DETECTED agents and starts in
  # "detected only" view. Press [t] to toggle to the full 70+ agent registry.
  #
  # Inputs (positional):
  #   $1  prompt header
  #   $2  scope ("global"|"project") — used to render the install path column
  #   $3+ agent keys (in registry order)
  # Outputs:
  #   SELECTED_AGENT_KEYS — array of chosen agent keys
  #
  # Keys: ↑/↓ move · space toggle · Enter confirm · / search · Esc clear search
  #       t toggle detected/all · a toggle visible · q clear all · PgUp/PgDn jump
  local prompt="$1" scope="$2"
  shift 2
  local agents=("$@")
  local count=${#agents[@]}
  local -a selected=() detected_mask=()
  local i key key2 key3 d
  # Build detection mask + initial selection (detected = preselected)
  for ((i = 0; i < count; i++)); do
    detected_mask+=("0"); selected+=("0")
    for d in "${DETECTED_AGENTS[@]}"; do
      if [[ "$d" == "${agents[$i]}" ]]; then
        detected_mask[i]="1"; selected[i]="1"; break
      fi
    done
  done

  # Mode: "detected" filters list to detected agents; "all" shows everything.
  # Default to detected if any detected; else all (with nothing preselected).
  local mode="detected"
  local any_detected=0
  for ((i = 0; i < count; i++)); do
    [[ "${detected_mask[$i]}" == "1" ]] && any_detected=1 && break
  done
  [[ $any_detected -eq 0 ]] && mode="all"

  # Viewport sizing
  local term_lines viewport
  term_lines="$(tput lines 2>/dev/null || echo 24)"
  viewport=$((term_lines - 10))
  (( viewport < 5 )) && viewport=5

  # Pre-format each row's right-hand path column for dim display
  local -a paths=()
  for ((i = 0; i < count; i++)); do
    local base
    base="$(agent_base_for "${agents[$i]}" "$scope")"
    if [[ -z "$base" ]]; then
      paths+=("(no ${scope} location)")
    elif [[ "$scope" == "global" && "$base" == "$HOME"* ]]; then
      paths+=("~${base#"$HOME"}")
    else
      paths+=("$base")
    fi
  done

  local cur=0 vstart=0
  local search_query=""
  local -a visible=()
  local drawn_lines=0

  rebuild_visible() {
    visible=()
    local lc_q=""
    [[ -n "$search_query" ]] && lc_q="$(printf '%s' "$search_query" | tr '[:upper:]' '[:lower:]')"
    for ((i = 0; i < count; i++)); do
      [[ "$mode" == "detected" && "${detected_mask[$i]}" != "1" ]] && continue
      if [[ -n "$lc_q" ]]; then
        local hay
        hay="$(printf '%s %s' "${agents[$i]}" "${AGENT_LABELS[${agents[$i]}]}" \
              | tr '[:upper:]' '[:lower:]')"
        [[ "$hay" != *"$lc_q"* ]] && continue
      fi
      visible+=("$i")
    done
    (( cur >= ${#visible[@]} )) && cur=$(( ${#visible[@]} - 1 ))
    (( cur < 0 )) && cur=0
    (( cur < vstart )) && vstart=$cur
    (( cur >= vstart + viewport )) && vstart=$(( cur - viewport + 1 ))
    (( vstart < 0 )) && vstart=0
  }

  render() {
    if (( drawn_lines > 0 )); then
      printf '\033[%dA\r' "$drawn_lines"
      local _n
      for ((_n = 0; _n < drawn_lines; _n++)); do printf '\033[2K\n'; done
      printf '\033[%dA\r' "$drawn_lines"
    fi
    drawn_lines=0

    local vis_count=${#visible[@]}
    local sel_count=0
    for ((i = 0; i < count; i++)); do
      [[ "${selected[$i]}" == "1" ]] && sel_count=$((sel_count + 1))
    done
    local end=$(( vstart + viewport ))
    (( end > vis_count )) && end=$vis_count

    local row idx marker dot label path_col line_color
    for ((row = vstart; row < end; row++)); do
      idx=${visible[$row]}
      if [[ "${selected[$idx]}" == "1" ]]; then
        marker="${GREEN}◼${NC}"
      else
        marker="◻"
      fi
      if [[ "${detected_mask[$idx]}" == "1" ]]; then
        dot="${GREEN}●${NC}"
      else
        dot=" "
      fi
      label="${AGENT_LABELS[${agents[$idx]}]}"
      path_col="${paths[$idx]}"
      if [[ $row -eq $cur ]]; then
        printf "    ${CYAN}❯${NC} %b %b %-26s ${DIM}%s${NC}\n" \
          "$marker" "$dot" "$label" "$path_col"
      else
        printf "      %b %b %-26s ${DIM}%s${NC}\n" \
          "$marker" "$dot" "$label" "$path_col"
      fi
      drawn_lines=$((drawn_lines + 1))
    done

    if [[ $vis_count -eq 0 ]]; then
      echo -e "      ${DIM}(no agents match — press / to search, t to show all)${NC}"
      drawn_lines=$((drawn_lines + 1))
    fi

    local mode_label
    if [[ "$mode" == "detected" ]]; then
      mode_label="detected only"
    else
      mode_label="all ${count}"
    fi
    local status_q=""
    [[ -n "$search_query" ]] && status_q=" · filter:'${search_query}'"
    echo -e "  ${DIM}── ${sel_count} selected · ${mode_label} (${vis_count})${status_q} ──${NC}"
    drawn_lines=$((drawn_lines + 1))
  }

  prompt_search() {
    printf '\033[1A\r\033[2K  /'
    local query=""
    IFS= read -r -u "$PROMPT_FD" query || query=""
    search_query="$query"
    cur=0; vstart=0
    rebuild_visible
  }

  echo -e "\n  ${BOLD}${prompt}${NC}"
  echo -e "  ${DIM}space=toggle  enter=confirm  t=detected/all  /=search  a=toggle visible  q=clear${NC}\n"
  tput civis 2>/dev/null || true
  rebuild_visible

  while true; do
    render
    read_key key 1
    if [[ "$key" == $'\x1b' ]]; then
      IFS= read -rsn 1 -u "$PROMPT_FD" -t 0.1 key2 || key2=""
      if [[ -z "$key2" ]]; then
        search_query=""
        rebuild_visible
        continue
      fi
      if [[ "$key2" == "[" ]]; then
        IFS= read -rsn 1 -u "$PROMPT_FD" key3 || key3=""
        case "$key3" in
          'A') (( cur > 0 )) && cur=$((cur - 1)) ;;
          'B') (( cur < ${#visible[@]} - 1 )) && cur=$((cur + 1)) ;;
          '5') IFS= read -rsn 1 -u "$PROMPT_FD" key3 || true
               cur=$((cur - viewport))
               (( cur < 0 )) && cur=0 ;;
          '6') IFS= read -rsn 1 -u "$PROMPT_FD" key3 || true
               cur=$((cur + viewport))
               (( cur >= ${#visible[@]} )) && cur=$(( ${#visible[@]} - 1 )) ;;
          'H') cur=0 ;;
          'F') cur=$(( ${#visible[@]} - 1 )) ;;
        esac
        (( cur < vstart )) && vstart=$cur
        (( cur >= vstart + viewport )) && vstart=$(( cur - viewport + 1 ))
      fi
    elif [[ "$key" == " " ]]; then
      [[ ${#visible[@]} -gt 0 ]] || continue
      local idx="${visible[$cur]}"
      if [[ "${selected[$idx]}" == "1" ]]; then
        selected[idx]="0"
      else
        selected[idx]="1"
      fi
    elif [[ "$key" == "t" || "$key" == "T" ]]; then
      if [[ "$mode" == "detected" ]]; then mode="all"; else mode="detected"; fi
      cur=0; vstart=0
      rebuild_visible
    elif [[ "$key" == "/" ]]; then
      tput cnorm 2>/dev/null || true
      prompt_search
      tput civis 2>/dev/null || true
    elif [[ "$key" == "a" ]]; then
      local end=$(( vstart + viewport ))
      (( end > ${#visible[@]} )) && end=${#visible[@]}
      local row idx any_unsel=0
      for ((row = vstart; row < end; row++)); do
        idx=${visible[$row]}
        [[ "${selected[$idx]}" != "1" ]] && any_unsel=1 && break
      done
      local target="1"
      [[ $any_unsel -eq 0 ]] && target="0"
      for ((row = vstart; row < end; row++)); do
        idx=${visible[$row]}
        selected[idx]="$target"
      done
    elif [[ "$key" == "q" ]]; then
      for ((i = 0; i < count; i++)); do selected[i]="0"; done
    elif [[ -z "$key" ]]; then
      break
    fi
  done
  tput cnorm 2>/dev/null || true

  SELECTED_AGENT_KEYS=()
  for ((i = 0; i < count; i++)); do
    [[ "${selected[$i]}" == "1" ]] && SELECTED_AGENT_KEYS+=("${agents[$i]}")
  done
}

# -----------------------------------------------------------------------------
# Agent registry — data-driven, aligned with vercel-labs/skills (skills.sh)
# -----------------------------------------------------------------------------
# AGENT_REGISTRY_RAW is a tab-separated table; one agent per line.
# Columns: KEY<TAB>LABEL<TAB>PROJECT_DIR<TAB>GLOBAL_SPEC<TAB>DETECT_EXPR
#
# Path placeholders (resolved by resolve_path_spec):
#   $HOME                       - user home
#   $XDG                        - ${XDG_CONFIG_HOME:-$HOME/.config}
#   $ENV:VARNAME                - value of env var VARNAME (empty if unset)
#   GLOBAL_SPEC may use ';alt:<path>' chains; the first alternative that
#   resolves to a non-empty path wins. Use 'none' for agents that have no
#   global install location (project-only).
#
# Detection expressions (DETECT_EXPR, semicolon-separated, OR-combined):
#   dir:<path>    directory exists
#   cmd:<name>    command available on PATH
#   env:<VAR>     env var is non-empty
#   file:<path>   file exists
#
# DO NOT REINDENT THE BLOCK BELOW — entries are split on real TAB characters.
declare -A AGENT_LABELS
declare -A AGENT_GLOBAL_BASES
declare -A AGENT_PROJECT_BASES
declare -A AGENT_DETECT
ALL_AGENTS=()

# Legacy / shorthand aliases. Users who typed --agent claude pre-2.20 still work.
declare -A AGENT_ALIASES=(
  [claude]=claude-code
  [codeium]=windsurf
  [copilot]=github-copilot
  [gemini]=gemini-cli
  [aider]=aider-desk
  [tabnine]=tabnine-cli
  [iflow]=iflow-cli
  [kimi]=kimi-code-cli
  [kiro]=kiro-cli
  [autohand]=autohand-code
  [hermes]=hermes-agent
  [codearts]=codearts-agent
  [antigravity-c]=antigravity-cli
)

# REGISTRY-START — tabs only between fields; do not reformat
# shellcheck disable=SC2016  # $HOME/$XDG/$ENV are placeholders resolved at runtime
AGENT_REGISTRY_RAW='aider-desk	AiderDesk	.aider-desk/skills	$HOME/.aider-desk/skills	dir:$HOME/.aider-desk
amp	Amp	.agents/skills	$XDG/agents/skills	dir:$XDG/amp
antigravity	Antigravity	.agents/skills	$HOME/.gemini/antigravity/skills	dir:$HOME/.gemini/antigravity
antigravity-cli	Antigravity CLI	.agents/skills	$HOME/.gemini/antigravity-cli/skills	dir:$HOME/.gemini/antigravity-cli
astrbot	AstrBot	data/skills	$HOME/.astrbot/data/skills	dir:$HOME/.astrbot;dir:./data/skills
autohand-code	Autohand Code CLI	.autohand/skills	$ENV:AUTOHAND_HOME/skills;alt:$HOME/.autohand/skills	env:AUTOHAND_HOME;dir:$HOME/.autohand
augment	Augment	.augment/skills	$HOME/.augment/skills	dir:$HOME/.augment
bob	IBM Bob	.bob/skills	$HOME/.bob/skills	dir:$HOME/.bob
claude-code	Claude Code	.claude/skills	$ENV:CLAUDE_CONFIG_DIR/skills;alt:$HOME/.claude/skills	dir:$HOME/.claude;cmd:claude;env:CLAUDE_CONFIG_DIR
cline	Cline	.agents/skills	$HOME/.agents/skills	dir:$HOME/.cline
codearts-agent	CodeArts Agent	.codeartsdoer/skills	$HOME/.codeartsdoer/skills	dir:$HOME/.codeartsdoer
codebuddy	CodeBuddy	.codebuddy/skills	$HOME/.codebuddy/skills	dir:$HOME/.codebuddy;dir:./.codebuddy
codemaker	Codemaker	.codemaker/skills	$HOME/.codemaker/skills	dir:$HOME/.codemaker
codestudio	Code Studio	.codestudio/skills	$HOME/.codestudio/skills	dir:$HOME/.codestudio
codex	Codex	.agents/skills	$ENV:CODEX_HOME/skills;alt:$HOME/.codex/skills	dir:$HOME/.codex;cmd:codex;env:CODEX_HOME
command-code	Command Code	.commandcode/skills	$HOME/.commandcode/skills	dir:$HOME/.commandcode
continue	Continue	.continue/skills	$HOME/.continue/skills	dir:$HOME/.continue;dir:./.continue
cortex	Cortex Code	.cortex/skills	$HOME/.snowflake/cortex/skills	dir:$HOME/.snowflake/cortex
crush	Crush	.crush/skills	$HOME/.config/crush/skills	dir:$HOME/.config/crush
cursor	Cursor	.agents/skills	$HOME/.cursor/skills	dir:$HOME/.cursor;cmd:cursor
deepagents	Deep Agents	.agents/skills	$HOME/.deepagents/agent/skills	dir:$HOME/.deepagents
devin	Devin for Terminal	.devin/skills	$XDG/devin/skills	dir:$XDG/devin
dexto	Dexto	.agents/skills	$HOME/.agents/skills	dir:$HOME/.dexto
droid	Droid	.factory/skills	$HOME/.factory/skills	dir:$HOME/.factory
firebender	Firebender	.agents/skills	$HOME/.firebender/skills	dir:$HOME/.firebender
forgecode	ForgeCode	.forge/skills	$HOME/.forge/skills	dir:$HOME/.forge
gemini-cli	Gemini CLI	.agents/skills	$HOME/.gemini/skills	dir:$HOME/.gemini
github-copilot	GitHub Copilot	.agents/skills	$HOME/.copilot/skills	dir:$HOME/.copilot
goose	Goose	.goose/skills	$XDG/goose/skills	dir:$XDG/goose
hermes-agent	Hermes Agent	.hermes/skills	$ENV:HERMES_HOME/skills;alt:$HOME/.hermes/skills	env:HERMES_HOME;dir:$HOME/.hermes
iflow-cli	iFlow CLI	.iflow/skills	$HOME/.iflow/skills	dir:$HOME/.iflow
inference-sh	inference.sh	.inferencesh/skills	$HOME/.inferencesh/skills	dir:$HOME/.inferencesh
jazz	Jazz	.jazz/skills	$HOME/.jazz/skills	dir:$HOME/.jazz;dir:./.jazz
junie	Junie	.junie/skills	$HOME/.junie/skills	dir:$HOME/.junie
kilo	Kilo Code	.kilocode/skills	$HOME/.kilocode/skills	dir:$HOME/.kilocode
kimi-code-cli	Kimi Code CLI	.agents/skills	$HOME/.agents/skills	dir:$HOME/.kimi-code;dir:$HOME/.kimi
kiro-cli	Kiro CLI	.kiro/skills	$HOME/.kiro/skills	dir:$HOME/.kiro
kode	Kode	.kode/skills	$HOME/.kode/skills	dir:$HOME/.kode
lingma	Lingma	.lingma/skills	$HOME/.lingma/skills	dir:$HOME/.lingma
loaf	Loaf	.agents/skills	$HOME/.agents/skills	dir:$HOME/.loaf
mcpjam	MCPJam	.mcpjam/skills	$HOME/.mcpjam/skills	dir:$HOME/.mcpjam
mistral-vibe	Mistral Vibe	.vibe/skills	$ENV:VIBE_HOME/skills;alt:$HOME/.vibe/skills	env:VIBE_HOME;dir:$HOME/.vibe
moxby	Moxby	.moxby/skills	$HOME/.moxby/skills	dir:$HOME/.moxby
mux	Mux	.mux/skills	$HOME/.mux/skills	dir:$HOME/.mux
neovate	Neovate	.neovate/skills	$HOME/.neovate/skills	dir:$HOME/.neovate
opencode	OpenCode	.agents/skills	$XDG/opencode/skills	dir:$XDG/opencode
openclaw	OpenClaw	.openclaw/skills	$HOME/.openclaw/skills;alt:$HOME/.clawdbot/skills;alt:$HOME/.moltbot/skills	dir:$HOME/.openclaw;dir:$HOME/.clawdbot;dir:$HOME/.moltbot
openhands	OpenHands	.openhands/skills	$HOME/.openhands/skills	dir:$HOME/.openhands
ona	Ona	.ona/skills	$HOME/.ona/skills	dir:$HOME/.ona
pi	Pi	.pi/skills	$HOME/.pi/agent/skills	dir:$HOME/.pi/agent
pochi	Pochi	.pochi/skills	$HOME/.pochi/skills	dir:$HOME/.pochi
promptscript	PromptScript	.agents/skills	none	dir:./.promptscript;file:./promptscript.yaml
qoder	Qoder	.qoder/skills	$HOME/.qoder/skills	dir:$HOME/.qoder
qoder-cn	Qoder CN	.qoder/skills	$HOME/.qoder-cn/skills	dir:$HOME/.qoder-cn
qwen-code	Qwen Code	.qwen/skills	$HOME/.qwen/skills	dir:$HOME/.qwen
reasonix	Reasonix	.reasonix/skills	$HOME/.reasonix/skills	dir:$HOME/.reasonix
replit	Replit	.agents/skills	$XDG/agents/skills	dir:./.replit
roo	Roo Code	.roo/skills	$HOME/.roo/skills	dir:$HOME/.roo
rovodev	Rovo Dev	.rovodev/skills	$HOME/.rovodev/skills	dir:$HOME/.rovodev
tabnine-cli	Tabnine CLI	.tabnine/agent/skills	$HOME/.tabnine/agent/skills	dir:$HOME/.tabnine
terramind	Terramind	.terramind/skills	$HOME/.terramind/skills	dir:$HOME/.terramind
tinycloud	Tinycloud	.tinycloud/skills	$HOME/.tinycloud/skills	dir:$HOME/.tinycloud
trae	Trae	.trae/skills	$HOME/.trae/skills	dir:$HOME/.trae
trae-cn	Trae CN	.trae/skills	$HOME/.trae-cn/skills	dir:$HOME/.trae-cn
warp	Warp	.agents/skills	$HOME/.agents/skills	dir:$HOME/.warp
windsurf	Windsurf	.windsurf/skills	$HOME/.codeium/windsurf/skills	dir:$HOME/.codeium;cmd:windsurf
zed	Zed	.agents/skills	$XDG/zed/skills	dir:$XDG/zed;env:APPDATA;env:FLATPAK_XDG_CONFIG_HOME
zencoder	Zencoder	.zencoder/skills	$HOME/.zencoder/skills	dir:$HOME/.zencoder
zenflow	Zenflow	.zencoder/skills	$HOME/.zencoder/skills	dir:$HOME/.zencoder
adal	AdaL	.adal/skills	$HOME/.adal/skills	dir:$HOME/.adal'
# REGISTRY-END

# Resolve $HOME / $XDG / $ENV:VARNAME placeholders in a single path string.
# Returns empty string if the chosen alternative cannot resolve (env unset).
expand_path_one() {
  local spec="$1"
  local xdg="${XDG_CONFIG_HOME:-$HOME/.config}"
  # $ENV:VARNAME — entire $ENV:NAME token is replaced by value, or "" if unset
  while [[ "$spec" =~ \$ENV:([A-Z_][A-Z0-9_]*) ]]; do
    local v="${BASH_REMATCH[1]}"
    local val="${!v:-}"
    [[ -z "$val" ]] && { echo ""; return; }
    spec="${spec//\$ENV:${v}/${val}}"
  done
  spec="${spec//\$XDG/${xdg}}"
  spec="${spec//\$HOME/${HOME}}"
  echo "$spec"
}

# Resolve a GLOBAL_SPEC of the form "$HOME/...[;alt:$ENV:.../...[;alt:...]]"
# Tries each alternative left-to-right; returns the first non-empty resolution.
# Returns empty string for the literal spec "none".
resolve_path_spec() {
  local spec="$1"
  [[ "$spec" == "none" ]] && { echo ""; return; }
  local IFS=';'
  local -a parts
  read -ra parts <<< "$spec"
  IFS=$' \t\n'
  local p first stripped resolved
  first=1
  for p in "${parts[@]}"; do
    if [[ $first -eq 1 ]]; then
      stripped="$p"
      first=0
    else
      stripped="${p#alt:}"
    fi
    resolved="$(expand_path_one "$stripped")"
    if [[ -n "$resolved" ]]; then
      echo "$resolved"
      return
    fi
  done
  echo ""
}

# Evaluate a DETECT_EXPR; returns 0 if any alternative matches.
detect_one_agent() {
  local expr="$1"
  [[ -z "$expr" ]] && return 1
  local IFS=';'
  local -a parts
  read -ra parts <<< "$expr"
  IFS=$' \t\n'
  local p kind value
  for p in "${parts[@]}"; do
    kind="${p%%:*}"
    value="${p#*:}"
    value="$(expand_path_one "$value")"
    case "$kind" in
      dir)  [[ -n "$value" && -d "$value" ]] && return 0 ;;
      cmd)  command -v "$value" >/dev/null 2>&1 && return 0 ;;
      env)  [[ -n "${!value:-}" ]] && return 0 ;;
      file) [[ -n "$value" && -f "$value" ]] && return 0 ;;
    esac
  done
  return 1
}

# Populate AGENT_LABELS / AGENT_PROJECT_BASES / AGENT_GLOBAL_BASES / AGENT_DETECT
# / ALL_AGENTS from AGENT_REGISTRY_RAW. Called once during main().
parse_agent_registry() {
  local line key label proj glob_spec detect_expr glob_resolved
  while IFS=$'\t' read -r key label proj glob_spec detect_expr; do
    [[ -z "$key" || "$key" == \#* ]] && continue
    glob_resolved="$(resolve_path_spec "$glob_spec")"
    AGENT_LABELS[$key]="$label"
    AGENT_PROJECT_BASES[$key]="$proj"
    AGENT_GLOBAL_BASES[$key]="$glob_resolved"  # may be "" for promptscript or unresolved env
    AGENT_DETECT[$key]="$detect_expr"
    ALL_AGENTS+=("$key")
  done <<< "$AGENT_REGISTRY_RAW"
}

# Sanity check after parsing — fail fast if the embedded table is malformed.
validate_registry() {
  local key missing=0
  [[ ${#ALL_AGENTS[@]} -lt 4 ]] && die "agent registry parsed too few entries (${#ALL_AGENTS[@]})"
  for key in "${ALL_AGENTS[@]}"; do
    [[ -z "${AGENT_LABELS[$key]:-}" ]] && { err "registry: missing label for $key"; missing=1; }
    [[ -z "${AGENT_PROJECT_BASES[$key]:-}" ]] && { err "registry: missing project_dir for $key"; missing=1; }
    # global may legitimately be "" (promptscript: none) — do not enforce
  done
  [[ $missing -eq 0 ]] || die "agent registry validation failed"
}

# Translate a user-provided agent token through AGENT_ALIASES.
# Unknown tokens are returned unchanged (caller validates with is_known_agent).
resolve_agent_key() {
  local input="$1"
  if [[ -n "${AGENT_ALIASES[$input]+x}" ]]; then
    echo "${AGENT_ALIASES[$input]}"
  else
    echo "$input"
  fi
}

detect_agents() {
  DETECTED_AGENTS=()
  local key
  for key in "${ALL_AGENTS[@]}"; do
    if detect_one_agent "${AGENT_DETECT[$key]}"; then
      DETECTED_AGENTS+=("$key")
    fi
  done
}

# Quickstart helper: pick a single canonical agent key.
# Priority: signature env vars → one detected agent; ambiguous detection fails.
autodetect_agent() {
  # (i) skip — caller already merged $SSOT_AGENT into ARG_AGENT earlier.
  # (ii) signature env detection (canonical keys, not aliases)
  if [[ -n "${CLAUDECODE:-}" ]]; then echo "claude-code"; return; fi
  local v
  for v in $(compgen -e | grep -E '^CLAUDE_CODE_' || true); do
    echo "claude-code"; return
  done
  if [[ -n "${CODEX_HOME:-}" ]]; then echo "codex"; return; fi
  for v in $(compgen -e | grep -E '^CODEX_' || true); do
    echo "codex"; return
  done
  if [[ -n "${CURSOR_TRACE_ID:-}" || "${TERM_PROGRAM:-}" == "cursor" ]]; then echo "cursor"; return; fi
  for v in $(compgen -e | grep -E '^WINDSURF_' || true); do
    echo "windsurf"; return
  done
  for v in $(compgen -e | grep -E '^GEMINI_CLI_' || true); do
    echo "gemini-cli"; return
  done
  for v in $(compgen -e | grep -E '^GITHUB_COPILOT_' || true); do
    echo "github-copilot"; return
  done
  for v in $(compgen -e | grep -E '^AIDER_' || true); do
    echo "aider-desk"; return
  done
  # (iii) fs-based fallback via existing detect_agents
  if [[ ${#DETECTED_AGENTS[@]} -eq 1 ]]; then
    echo "${DETECTED_AGENTS[0]}"
    return
  fi
  if [[ ${#DETECTED_AGENTS[@]} -gt 1 ]]; then
    err "multiple agents detected (${DETECTED_AGENTS[*]}): re-run with --agent <key>; see --list-agents"
    return 1
  fi
  # (iv) empty → caller decides to die
  echo ""
}

agent_base_for() {
  # echo the base path for agent+scope; may be "" for project-only agents at global scope
  local agent="$1" scope="$2"
  if [[ "$scope" == "global" ]]; then
    echo "${AGENT_GLOBAL_BASES[$agent]}"
  else
    echo "${AGENT_PROJECT_BASES[$agent]}"
  fi
}

is_known_agent() {
  local candidate
  candidate="$(resolve_agent_key "$1")"
  local a
  for a in "${ALL_AGENTS[@]}"; do
    [[ "$a" == "$candidate" ]] && return 0
  done
  return 1
}

# Remove duplicate (resolved base) entries from RESOLVED_AGENTS, warning when
# multiple agents share the same physical install path (e.g. cline/dexto/loaf
# all writing to ~/.agents/skills). Keeps the first occurrence.
dedup_targets() {
  local scope="$1"
  local -A seen=()
  local -a unique=()
  local agent base
  for agent in "${RESOLVED_AGENTS[@]}"; do
    base="$(agent_base_for "$agent" "$scope")"
    if [[ -z "$base" ]]; then
      # project-only agent selected at global scope — caller filters earlier
      continue
    fi
    if [[ -z "${seen[$base]+x}" ]]; then
      seen[$base]="$agent"
      unique+=("$agent")
    else
      warn "skipping ${AGENT_LABELS[$agent]} — same target as ${AGENT_LABELS[${seen[$base]}]} (${base})"
    fi
  done
  RESOLVED_AGENTS=("${unique[@]}")
}

# Print agent keys and resolved project/global paths; used by --list-agents.
# Assumes parse_agent_registry has already been called by main().
print_agent_list() {
  detect_agents
  printf "  %-20s %-26s %-7s %-28s %s\n" "KEY" "NAME" "DETECT" "PROJECT PATH" "GLOBAL PATH"
  printf "  %-20s %-26s %-7s %-28s %s\n" "----" "----" "------" "------------" "-----------"
  local key detected
  for key in "${ALL_AGENTS[@]}"; do
    detected=" "
    local d
    for d in "${DETECTED_AGENTS[@]}"; do
      [[ "$d" == "$key" ]] && detected="${GREEN}✓${NC}" && break
    done
    local g="${AGENT_GLOBAL_BASES[$key]}"
    [[ -z "$g" ]] && g="${DIM}(project-only)${NC}"
    # shellcheck disable=SC2059
    printf "  %-20s %-26s   %b    %-28s %b\n" "$key" "${AGENT_LABELS[$key]}" "$detected" "${AGENT_PROJECT_BASES[$key]}" "$g"
  done
  echo ""
  echo "  Total: ${#ALL_AGENTS[@]} agents (${#DETECTED_AGENTS[@]} detected on this system)"
}

# -----------------------------------------------------------------------------
# Source acquisition
# -----------------------------------------------------------------------------
clone_source() {
  # GNU timeout is optional: macOS ships neither timeout nor gtimeout.
  local -a limiter=()
  if command -v timeout >/dev/null 2>&1; then
    limiter=(timeout 15)
  elif command -v gtimeout >/dev/null 2>&1; then
    limiter=(gtimeout 15)
  fi
  GIT_TERMINAL_PROMPT=0 "${limiter[@]}" git -c http.lowSpeedLimit=1 -c http.lowSpeedTime=15 \
    clone --depth 1 --branch "$REPO_REF" "$1" "$SOURCE_DIR"
}

ensure_source() {
  # An explicit --ref must be fetched; a local checkout would silently install
  # whatever happens to be checked out instead.
  if [[ -n "$ARG_REF" && -n "${SOURCE_DIR:-}" ]]; then
    die "--ref cannot be combined with SOURCE_DIR; check out the ref in SOURCE_DIR instead"
  fi
  if [[ -n "${SOURCE_DIR:-}" ]] && [[ -f "$SOURCE_DIR/skills/$PRIMARY_SKILL/SKILL.md" ]]; then
    return 0
  fi

  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ -z "$ARG_REF" && -f "$script_dir/skills/$PRIMARY_SKILL/SKILL.md" ]]; then
    SOURCE_DIR="$script_dir"
    # refresh VERSION from local source if available
    if [[ -f "$SOURCE_DIR/VERSION" ]]; then
      VERSION="$(tr -d '[:space:]' < "$SOURCE_DIR/VERSION")"
      [[ -z "$VERSION" ]] && VERSION="unknown"
    fi
    return 0
  fi

  info "$(t FETCHING)"
  SOURCE_DIR="$(mktemp -d)"
  FETCHED_SOURCE_DIR="$SOURCE_DIR"

  local -a mirrors=()
  if [[ -n "${SSOT_SKILL_REPO_URL:-}" ]]; then
    mirrors=("$SSOT_SKILL_REPO_URL")
  else
    mirrors=(
      "https://github.com/huangpufan/SSOT-SKILL.git"
      "https://gh-proxy.com/https://github.com/huangpufan/SSOT-SKILL.git"
    )
  fi

  local url ok_clone=0 first=1 last_tried=""
  for url in "${mirrors[@]}"; do
    if [[ $first -eq 0 ]]; then
      warn "primary clone failed, retrying via $url" >&2
    fi
    first=0
    last_tried="$url"
    if clone_source "$url" >/dev/null 2>&1; then
      ok_clone=1
      break
    fi
    # clone leaves a partial dir on failure
    rm -rf "$SOURCE_DIR"
    SOURCE_DIR="$(mktemp -d)"
    FETCHED_SOURCE_DIR="$SOURCE_DIR"
  done

  if [[ $ok_clone -eq 0 && -z "${SSOT_SKILL_REPO_URL:-}" ]]; then
    # tar.gz fallbacks
    local -a tars=(
      "https://github.com/huangpufan/SSOT-SKILL/archive/${REPO_REF}.tar.gz"
      "https://gh-proxy.com/https://github.com/huangpufan/SSOT-SKILL/archive/${REPO_REF}.tar.gz"
    )
    local tar_url
    for tar_url in "${tars[@]}"; do
      warn "git clone failed for all mirrors, retrying via $tar_url" >&2
      last_tried="$tar_url"
      rm -rf "$SOURCE_DIR"
      SOURCE_DIR="$(mktemp -d)"
      FETCHED_SOURCE_DIR="$SOURCE_DIR"
      if curl -fsSL --max-time 30 "$tar_url" | tar -xz -C "$SOURCE_DIR" --strip-components=1 2>/dev/null; then
        ok_clone=1
        break
      fi
    done
  fi

  [[ $ok_clone -eq 1 ]] || die "failed to fetch ref '$REPO_REF' from all mirrors (last tried: $last_tried)"

  if [[ -f "$SOURCE_DIR/VERSION" ]]; then
    VERSION="$(tr -d '[:space:]' < "$SOURCE_DIR/VERSION")"
    [[ -z "$VERSION" ]] && VERSION="unknown"
  fi
  ok "$(t FETCHED)"
}

validate_bundle_source() {
  local skill source companion
  for skill in "${BUNDLE_SKILLS[@]}"; do
    source="$SOURCE_DIR/skills/$skill"
    [[ -f "$source/SKILL.md" ]] || die "missing bundled skill: $source"
    [[ -f "$source/agents/openai.yaml" ]] || die "missing Agent metadata: $source/agents/openai.yaml"
  done
  for companion in "${BUNDLE_ROOT_FILES[@]}"; do
    [[ -f "$SOURCE_DIR/skills/$companion" ]] || continue
    head -n 1 "$SOURCE_DIR/skills/$companion" | grep -qF "$BUNDLE_COMPANION_MARKER" ||
      die "bundle companion lacks ownership marker: $SOURCE_DIR/skills/$companion"
  done
}

bundle_companion_is_owned() {
  local path="$1"
  [[ -f "$path" ]] && head -n 1 "$path" | grep -qF "$BUNDLE_COMPANION_MARKER"
}

bundle_companion_is_legacy_owned() {
  local base="$1" path="$2" skill
  [[ "$(basename "$path")" == "SKILL_STYLE.md" ]] || return 1
  [[ -f "$path" ]] || return 1
  [[ "$(head -n 1 "$path")" == "# SKILL.md Style — the grill-me distillation" ]] || return 1
  grep -qF 'This file is the acceptance standard for the *prose body* of every `SKILL.md`' "$path" || return 1
  grep -qF 'in this bundle.' "$path" || return 1
  for skill in "${BUNDLE_SKILLS[@]}"; do
    [[ -f "$base/$skill/SKILL.md" ]] || return 1
  done
}

guard_bundle_root_files() {
  local base="$1" companion target
  for companion in "${BUNDLE_ROOT_FILES[@]}"; do
    [[ -f "$SOURCE_DIR/skills/$companion" ]] || continue
    target="$base/$companion"
    if [[ -e "$target" ]] && ! bundle_companion_is_owned "$target"; then
      if bundle_companion_is_legacy_owned "$base" "$target"; then
        warn "migrating legacy bundle companion ownership: $target"
      else
        die "refusing to overwrite unowned bundle companion: $target"
      fi
    fi
  done
}

# Resolve template language source directory. Echoes selected dir, or empty if
# falling back to flat layout. Exits non-zero on error.
resolve_template_lang_dir() {
  local lang="$1"
  local templates_root="$SOURCE_DIR/skills/ssot-bootstrap/assets/templates"
  local lang_dir="$templates_root/$lang"

  if [[ -d "$templates_root/en" || -d "$templates_root/zh" ]]; then
    [[ -d "$lang_dir" ]] || die "template language directory missing: $lang_dir"
    # ensure non-empty
    if ! find "$lang_dir" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
      die "template language directory is empty: $lang_dir"
    fi
    echo "$lang_dir"
    return
  fi

  # Fallback: flat layout (backwards compatible)
  if compgen -G "$templates_root/*.md" >/dev/null; then
    echo ""
    return
  fi
  die "no templates found under $templates_root"
}

# The marked template section is shared by installation and bootstrap.
# Validate before installing so a broken source cannot silently omit wiring.
read_wire_block() {
  local lang="$1" template_dir template block skill
  template_dir="$(resolve_template_lang_dir "$lang")" || return 1
  template="${template_dir:-$SOURCE_DIR/skills/ssot-bootstrap/assets/templates}/adapter-thin.md"
  [[ -f "$template" ]] || { err "missing SSOT instruction template: $template"; return 1; }
  block="$(awk '
    $0 == "<!-- SSOT-SKILL:BEGIN -->" { starts++; active = 1 }
    active { block = block $0 ORS }
    $0 == "<!-- SSOT-SKILL:END -->" { ends++; active = 0 }
    END {
      if (starts != 1 || ends != 1 || active) exit 1
      printf "%s", block
    }
  ' "$template")" || { err "invalid SSOT instruction block: $template"; return 1; }
  for skill in "${BUNDLE_SKILLS[@]}"; do
    [[ " ${SHIM_SKILLS[*]} " == *" $skill "* ]] && continue # Compatibility names are not lifecycle routes.
    [[ "$block" == *"\$$skill"* ]] || { err "missing $skill route in SSOT instruction block: $template"; return 1; }
  done
  printf '%s\n' "$block"
}

# Print the protocol_version a SKILL.md declares, or nothing if it has none.
skill_protocol_version() {
  [[ -f "$1" ]] || return 0
  sed -nE 's/^[[:space:]]*protocol_version:[[:space:]]*"?([0-9.]+).*/\1/p' "$1" | head -1 || true
}

# -----------------------------------------------------------------------------
# Install / copy
# -----------------------------------------------------------------------------
copy_bundle() {
  local base="$1"
  local lang="$2"
  local stage
  validate_bundle_source
  read_wire_block "$lang" >/dev/null
  mkdir -p "$base"
  guard_bundle_root_files "$base"
  stage="$(mktemp -d "$base/.ssot-skill-install.XXXXXX")"
  INSTALL_STAGE="$stage"

  local skill source companion
  for skill in "${BUNDLE_SKILLS[@]}"; do
    source="$SOURCE_DIR/skills/$skill"
    cp -R "$source" "$stage/$skill"
  done
  for companion in "${BUNDLE_ROOT_FILES[@]}"; do
    [[ -f "$SOURCE_DIR/skills/$companion" ]] || continue
    cp "$SOURCE_DIR/skills/$companion" "$stage/$companion"
  done

  # Apply template language selection to ssot-bootstrap staged copy
  local lang_dir
  lang_dir="$(resolve_template_lang_dir "$lang")"
  if [[ -n "$lang_dir" ]]; then
    local stage_templates="$stage/ssot-bootstrap/assets/templates"
    rm -rf "$stage_templates"
    mkdir -p "$stage_templates"
    # Flatten: copy contents of $lang_dir/* into $stage_templates/
    local item
    shopt -s dotglob nullglob
    for item in "$lang_dir"/*; do
      cp -R "$item" "$stage_templates/"
    done
    shopt -u dotglob nullglob
  fi

  # Generated caches are machine-local junk, never bundle content
  find "$stage" -type d -name "__pycache__" -prune -exec rm -rf {} +
  find "$stage" -type f \( -name "*.pyc" -o -name ".DS_Store" \) -delete

  # Cross-format replacements change how agents treat existing SSOT folders.
  local old_version="" new_version=""
  old_version="$(skill_protocol_version "$base/$PRIMARY_SKILL/SKILL.md")"
  new_version="$(skill_protocol_version "$stage/$PRIMARY_SKILL/SKILL.md")"
  if [[ ( "$old_version" == 2.* || "$old_version" == 3.* ) && "$new_version" == 4.* ]]; then
    warn "$(t UPGRADE_V4_NOTE)"
  elif [[ "$old_version" == 2.* && "$new_version" == 3.* ]]; then
    warn "$(t UPGRADE_V3_NOTE)"
  fi

  # Decide ownership of retired companions before the new skills land: the
  # legacy signature requires the *previous* bundle to be present.
  local -a retired=()
  for companion in "${BUNDLE_ROOT_FILES[@]}"; do
    [[ -f "$stage/$companion" ]] && continue
    if bundle_companion_is_owned "$base/$companion" || bundle_companion_is_legacy_owned "$base" "$base/$companion"; then
      retired+=("$base/$companion")
    fi
  done

  for skill in "${BUNDLE_SKILLS[@]}"; do
    local target="$base/$skill"
    [[ -d "$target" ]] && rm -rf "$target"
    mv "$stage/$skill" "$target"
  done
  for companion in "${BUNDLE_ROOT_FILES[@]}"; do
    [[ -f "$stage/$companion" ]] && mv "$stage/$companion" "$base/$companion"
  done
  local path
  for path in "${retired[@]+"${retired[@]}"}"; do  # empty-array safe under set -u on bash < 4.4
    rm -f "$path" # companion an older bundle installed and this one no longer ships
  done

  rm -rf "$stage"
  INSTALL_STAGE=""
}

install_to() {
  local label="$1" base="$2" lang="$3"
  copy_bundle "$base" "$lang"
  ok "${BOLD}${label}${NC} → ${DIM}${base}${NC}"
}

# -----------------------------------------------------------------------------
# Uninstall
# -----------------------------------------------------------------------------
remove_bundle() {
  local base="$1"
  local skill target companion
  for skill in "${BUNDLE_SKILLS[@]}"; do
    target="$base/$skill"
    [[ -e "$target" ]] && rm -rf "$target"
  done
  for companion in "${BUNDLE_ROOT_FILES[@]}"; do
    if bundle_companion_is_owned "$base/$companion"; then
      rm -f "$base/$companion"
    elif [[ -e "$base/$companion" ]]; then
      warn "preserving unowned bundle companion: $base/$companion"
    fi
  done
}

# -----------------------------------------------------------------------------
# Upgrade helpers
# -----------------------------------------------------------------------------
detect_installed_lang() {
  local base="$1"
  local probe
  for probe in "$base/ssot-bootstrap/assets/templates/ssot-readme.md" \
               "$base/ssot-bootstrap/assets/templates/architecture-readme.md"; do
    if [[ -f "$probe" ]]; then
      if LC_ALL=C grep -q $'[\xe4-\xe9][\x80-\xbf][\x80-\xbf]' "$probe"; then
        echo "zh"
        return
      else
        echo "en"
        return
      fi
    fi
  done
  echo "en"
}

scan_upgrade_targets() {
  # Emits lines: "agent|scope|base|label"
  # Skips bases that resolve to SOURCE_DIR/skills (would clobber the source repo).
  UPGRADE_ROWS=()
  local agent base scope
  local -A seen=()
  local -a agents=("${ALL_AGENTS[@]}")
  if [[ -n "$ARG_AGENT" && "$ARG_AGENT" != "all" ]]; then
    resolve_agent_list
    agents=("${RESOLVED_AGENTS[@]}")
  fi
  local source_skills=""
  if [[ -n "${SOURCE_DIR:-}" && -d "$SOURCE_DIR/skills" ]]; then
    source_skills="$(cd "$SOURCE_DIR/skills" && pwd -P)"
  fi
  local probe
  for agent in "${agents[@]}"; do
    for scope in global project; do
      [[ -z "$ARG_SCOPE" || "$ARG_SCOPE" == "$scope" ]] || continue
      base="$(agent_base_for "$agent" "$scope")"
      [[ -n "$base" ]] || continue
      [[ "$scope" != "project" ]] || base="$PWD/$base"
      [[ -d "$base/$PRIMARY_SKILL" ]] || continue
      probe="$(cd "$base" && pwd -P)"
      [[ "$probe" != "$source_skills" && -z "${seen[$probe]+x}" ]] || continue
      seen[$probe]=1
      UPGRADE_ROWS+=("${agent}|${scope}|${base}|${AGENT_LABELS[$agent]}")
    done
  done
}

# -----------------------------------------------------------------------------
# Argument parsing
# -----------------------------------------------------------------------------
usage() {
  cat <<'EOF'
SSOT Skill installer

USAGE:
  install.sh [OPTIONS]
  install.sh --uninstall [OPTIONS]
  install.sh --upgrade [--agent <list>] [--scope <global|project>]
  install.sh --list-agents

OPTIONS:
  --agent <list>            Comma-separated agent list, or 'all'.
                            Legacy short keys still work: claude, codeium,
                            copilot, gemini, aider, tabnine, iflow, kimi,
                            kiro, autohand, hermes, codearts.
                            Full canonical list: --list-agents
  --scope <global|project>  Install/uninstall scope; optional upgrade filter
  --lang <en|zh>            Template language (default: en)
  --ref <branch|tag>        Install from this branch or tag (default: main).
                            --ref v2-final keeps the frozen v2 protocol.
  --yes, -y                 Skip confirmation
  --non-interactive         Fail instead of prompting when args are missing
  --quickstart              Non-interactive project-local install with autodetect
  --uninstall               Remove installed bundle (requires --agent, --scope)
  --upgrade                 Re-install detected locations; respects --agent/--scope
  --list-agents             Print supported agents (KEY / NAME / DETECT / PATH)
  --ui-lang <en|zh>         Installer UI language (default: auto from $LANG)
  --version                 Print bundle version and exit
  --help, -h                Show this help

ENVIRONMENT:
  SSOT_AGENT, SSOT_SCOPE, SSOT_LANG, SSOT_UI_LANG, SSOT_REF
  SSOT_YES=1, SSOT_NONINTERACTIVE=1
  SOURCE_DIR                Local source checkout (skip git clone)

EXAMPLES:
  # Quickstart (recommended for agents) — project-local, autodetected:
  curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-SKILL/main/install.sh | bash -s -- --quickstart

  # Interactive (recommended): pick scope, agents, and language with arrow keys
  curl -fsSL <url>/install.sh | bash
  bash install.sh

  # Non-interactive (CI / scripted setups)
  bash install.sh --non-interactive --agent claude-code --scope project --lang en --yes
  bash install.sh --non-interactive --agent all --scope global --lang en --yes

  # Stay on the frozen v2 protocol instead of the current one:
  curl -fsSL <url>/install.sh | bash -s -- --quickstart --ref v2-final

  # Maintenance
  bash install.sh --upgrade --agent codex --scope project
  bash install.sh --upgrade
  bash install.sh --uninstall --agent claude-code --scope project --yes
  bash install.sh --list-agents
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --agent)
        [[ $# -ge 2 ]] || die "--agent requires a value"
        ARG_AGENT="$2"; shift 2 ;;
      --agent=*)
        ARG_AGENT="${1#*=}"; shift ;;
      --scope)
        [[ $# -ge 2 ]] || die "--scope requires a value"
        ARG_SCOPE="$2"; shift 2 ;;
      --scope=*)
        ARG_SCOPE="${1#*=}"; shift ;;
      --lang)
        [[ $# -ge 2 ]] || die "--lang requires a value"
        ARG_LANG="$2"; shift 2 ;;
      --lang=*)
        ARG_LANG="${1#*=}"; shift ;;
      --ref)
        [[ $# -ge 2 ]] || die "--ref requires a value"
        ARG_REF="$2"; shift 2 ;;
      --ref=*)
        ARG_REF="${1#*=}"; shift ;;
      --ui-lang)
        [[ $# -ge 2 ]] || die "--ui-lang requires a value"
        ARG_UI_LANG="$2"; shift 2 ;;
      --ui-lang=*)
        ARG_UI_LANG="${1#*=}"; shift ;;
      --yes|-y)
        ARG_YES=1; shift ;;
      --non-interactive)
        ARG_NONINTERACTIVE=1; shift ;;
      --quickstart)
        ARG_QUICKSTART=1
        ARG_NONINTERACTIVE=1
        ARG_YES=1
        shift ;;
      --uninstall)
        MODE="uninstall"; shift ;;
      --upgrade)
        MODE="upgrade"; shift ;;
      --list-agents)
        MODE="list-agents"; shift ;;
      --version)
        echo "$VERSION"; exit 0 ;;
      --help|-h)
        usage; exit 0 ;;
      *)
        die "unknown argument: $1 (try --help)" ;;
    esac
  done

  # Merge env vars (CLI flags win)
  [[ -z "$ARG_AGENT" && -n "${SSOT_AGENT:-}" ]] && ARG_AGENT="$SSOT_AGENT"
  [[ -z "$ARG_SCOPE" && -n "${SSOT_SCOPE:-}" ]] && ARG_SCOPE="$SSOT_SCOPE"
  [[ -z "$ARG_LANG"  && -n "${SSOT_LANG:-}"  ]] && ARG_LANG="$SSOT_LANG"
  [[ -z "$ARG_UI_LANG" && -n "${SSOT_UI_LANG:-}" ]] && ARG_UI_LANG="$SSOT_UI_LANG"
  [[ -z "$ARG_REF" && -n "${SSOT_REF:-}" ]] && ARG_REF="$SSOT_REF"
  if [[ -n "$ARG_REF" ]]; then
    # The ref is spliced into a URL and a git argument: allow ordinary
    # branch and tag names only. Commit SHAs are not accepted by clone --branch.
    [[ "$ARG_REF" =~ ^[A-Za-z0-9._][A-Za-z0-9._/-]*$ && "$ARG_REF" != *..* ]] ||
      die "invalid --ref '$ARG_REF': use a branch or tag name"
    REPO_REF="$ARG_REF"
  fi
  [[ "${SSOT_YES:-0}" == "1" ]] && ARG_YES=1
  [[ "${SSOT_NONINTERACTIVE:-0}" == "1" ]] && ARG_NONINTERACTIVE=1

  # Quickstart: fill defaults for fields the user did not pass.
  # Must run AFTER env merge so SSOT_* env values take precedence over autodetect.
  if [[ "$ARG_QUICKSTART" -eq 1 ]]; then
    [[ -z "$ARG_SCOPE" ]] && ARG_SCOPE="project"
    # Lang autodetect: respect LANG env when --lang not given
    if [[ -z "$ARG_LANG" ]]; then
      case "${LANG:-}" in
        zh_CN*|zh_TW*|zh_HK*|zh_SG*) ARG_LANG="zh" ;;
        *) ARG_LANG="en" ;;
      esac
    fi
    # ARG_AGENT autodetect runs later in run_install (after parse_agent_registry).
  fi

  # Upgrade implies non-interactive + yes
  if [[ "$MODE" == "upgrade" ]]; then
    ARG_NONINTERACTIVE=1
    ARG_YES=1
  fi

  # Validate scope / lang values if present
  if [[ -n "$ARG_SCOPE" ]]; then
    case "$ARG_SCOPE" in
      global|project) ;;
      *) die "--scope must be 'global' or 'project' (got: $ARG_SCOPE)" ;;
    esac
  fi
  if [[ -n "$ARG_LANG" ]]; then
    case "$ARG_LANG" in
      en|zh) ;;
      *) die "--lang must be 'en' or 'zh' (got: $ARG_LANG)" ;;
    esac
  fi
}

# -----------------------------------------------------------------------------
# Agent list resolution
# -----------------------------------------------------------------------------
resolve_agent_list() {
  # Sets RESOLVED_AGENTS array based on ARG_AGENT (or interactive selection)
  RESOLVED_AGENTS=()
  local input="$ARG_AGENT"

  if [[ -z "$input" ]]; then
    return  # caller will go interactive
  fi

  if [[ "$input" == "all" ]]; then
    if [[ ${#DETECTED_AGENTS[@]} -gt 0 ]]; then
      RESOLVED_AGENTS=("${DETECTED_AGENTS[@]}")
    else
      RESOLVED_AGENTS=("${ALL_AGENTS[@]}")
    fi
    return
  fi

  local IFS=','
  local raw
  read -ra raw <<< "$input"
  IFS=$' \t\n'
  local a trimmed canonical
  for a in "${raw[@]}"; do
    trimmed="${a// /}"
    [[ -z "$trimmed" ]] && continue
    canonical="$(resolve_agent_key "$trimmed")"
    is_known_agent "$canonical" || die "unknown agent: $trimmed (run --list-agents for full list)"
    RESOLVED_AGENTS+=("$canonical")
  done
  [[ ${#RESOLVED_AGENTS[@]} -gt 0 ]] || die "$(t NO_AGENT_SELECTED)"
}

# -----------------------------------------------------------------------------
# Modes
# -----------------------------------------------------------------------------
run_install() {
  detect_agents

  # Quickstart: autodetect agent if user gave no --agent and none came via env.
  if [[ "$ARG_QUICKSTART" -eq 1 && -z "$ARG_AGENT" ]]; then
    local autodetected
    autodetected="$(autodetect_agent)"
    [[ -z "$autodetected" ]] && die "agent autodetect failed: re-run with --agent <key>; see --list-agents"
    ARG_AGENT="$autodetected"
    info "autodetected agent: ${autodetected}"
  fi

  # Resolve scope
  local scope="$ARG_SCOPE"
  if [[ -z "$scope" ]]; then
    if [[ "$ARG_NONINTERACTIVE" -eq 1 ]]; then
      die "--scope required in non-interactive mode"
    fi
    if [[ "$PROMPT_FD" -eq 0 && ! -t 0 ]]; then
      die "no tty available for interactive picker. Re-run with --quickstart, or pass --non-interactive --scope <global|project> --agent <key> --yes"
    fi
    # Project-first ordering — most users running `curl | bash` want the
    # bundle in the current repo, not their global skills dir.
    local scope_options=("$(t PROJECT_SCOPE)" "$(t GLOBAL_SCOPE)")
    select_one "$(t INSTALL_WHERE)" "${scope_options[@]}"
    [[ $SELECTED_INDEX -eq 0 ]] && scope="project" || scope="global"
  fi

  # Resolve template language
  local lang="$ARG_LANG"
  if [[ -z "$lang" ]]; then
    if [[ "$ARG_NONINTERACTIVE" -eq 1 ]]; then
      lang="en"
    else
      if [[ "$PROMPT_FD" -eq 0 && ! -t 0 ]]; then
        die "no tty available for interactive picker. Re-run with --quickstart, or pass --non-interactive --scope <global|project> --agent <key> --yes"
      fi
      local lang_options=("$(t LANG_EN)" "$(t LANG_ZH)")
      select_one "$(t LANG_PROMPT)" "${lang_options[@]}"
      [[ $SELECTED_INDEX -eq 0 ]] && lang="en" || lang="zh"
    fi
  fi

  # Resolve agents
  resolve_agent_list
  if [[ ${#RESOLVED_AGENTS[@]} -eq 0 ]]; then
    if [[ "$ARG_NONINTERACTIVE" -eq 1 ]]; then
      die "--agent required in non-interactive mode"
    fi
    if [[ ${#DETECTED_AGENTS[@]} -eq 0 ]]; then
      warn "$(t NO_AGENT_DETECTED)"
      info "$(t SHOWING_ALL)"
    fi
    if [[ "$PROMPT_FD" -eq 0 && ! -t 0 ]]; then
      die "no tty available for interactive picker. Re-run with --quickstart, or pass --non-interactive --scope <global|project> --agent <key> --yes"
    fi
    select_agents "$(t SELECT_AGENTS)" "$scope" "${ALL_AGENTS[@]}"
    [[ ${#SELECTED_AGENT_KEYS[@]} -gt 0 ]] || die "$(t NO_AGENT_SELECTED)"
    RESOLVED_AGENTS=("${SELECTED_AGENT_KEYS[@]}")
  fi

  # Dedup agents that share the same physical install path under this scope
  dedup_targets "$scope"

  # Build target list, filtering out empty bases (e.g. promptscript at global scope)
  local -a targets=()
  local agent base
  for agent in "${RESOLVED_AGENTS[@]}"; do
    base="$(agent_base_for "$agent" "$scope")"
    if [[ -z "$base" ]]; then
      warn "${AGENT_LABELS[$agent]} has no ${scope} install location — skipped"
      continue
    fi
    targets+=("${AGENT_LABELS[$agent]}|$base")
  done

  if [[ ${#targets[@]} -eq 0 ]]; then
    die "no installable targets (all selected agents lack a ${scope} location)"
  fi

  echo ""
  info "$(t WILL_INSTALL)"
  local skill
  for skill in "${BUNDLE_SKILLS[@]}"; do
    echo -e "      ${DIM}${skill}${NC}"
  done
  echo ""
  info "$(t TARGETS)"
  local entry label
  for entry in "${targets[@]}"; do
    IFS='|' read -r label base <<< "$entry"
    echo -e "      ${label} → ${DIM}${base}${NC}"
  done

  # Confirm
  if [[ "$ARG_YES" -ne 1 ]]; then
    if [[ "$ARG_NONINTERACTIVE" -eq 1 ]]; then
      die "non-interactive without --yes: refusing to proceed"
    fi
    echo ""
    select_one "$(t CONFIRM_INSTALL)" "$(t YES_INSTALL)" "$(t NO_CANCEL)"
    if [[ $SELECTED_INDEX -eq 1 ]]; then
      info "$(t CANCELLED)"
      exit 0
    fi
  fi

  echo ""
  ensure_source
  echo ""

  for entry in "${targets[@]}"; do
    IFS='|' read -r label base <<< "$entry"
    install_to "$label" "$base" "$lang"
  done

  echo ""
  echo -e "  ${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "  ${CHECK} ${BOLD}$(t INSTALLED)${NC}  ${DIM}v${VERSION}${NC}"
  echo -e "  ${DIM}  $(t RESTART_TIP)${NC}"
  echo -e "  ${DIM}  $(t PREFLIGHT_TIP)${NC}"
  echo -e "  ${DIM}  $(t CLOSEOUT_TIP)${NC}"
  if [[ "$scope" == "project" ]]; then
    echo -e "  ${DIM}  $(t PROJECT_NOTE)${NC}"
    echo -e "  ${DIM}  $(t ALSO_GLOBAL_HINT)${NC}"
  fi
  echo -e "  ${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  print_wire_block "$lang"
  echo ""
}

run_uninstall() {
  # Required: --agent, --scope
  [[ -n "$ARG_AGENT" ]] || die "--uninstall requires --agent"
  [[ -n "$ARG_SCOPE" ]] || die "--uninstall requires --scope"

  detect_agents
  resolve_agent_list
  dedup_targets "$ARG_SCOPE"
  [[ ${#RESOLVED_AGENTS[@]} -gt 0 ]] || die "no uninstallable targets for scope: $ARG_SCOPE"

  local -a bases=()
  local agent base
  for agent in "${RESOLVED_AGENTS[@]}"; do
    base="$(agent_base_for "$agent" "$ARG_SCOPE")"
    bases+=("$base")
  done

  echo ""
  info "$(t UNINSTALL_HEADER)"
  local skill b
  for b in "${bases[@]}"; do
    for skill in "${BUNDLE_SKILLS[@]}"; do
      [[ -e "$b/$skill" ]] && echo -e "      ${DIM}${b}/${skill}${NC}"
    done
  done

  if [[ "$ARG_YES" -ne 1 ]]; then
    if [[ "$ARG_NONINTERACTIVE" -eq 1 ]]; then
      die "non-interactive without --yes: refusing to proceed"
    fi
    echo ""
    select_one "$(t CONFIRM_UNINSTALL)" "$(t YES_INSTALL)" "$(t NO_CANCEL)"
    if [[ $SELECTED_INDEX -eq 1 ]]; then
      info "$(t CANCELLED)"
      exit 0
    fi
  fi

  echo ""
  for b in "${bases[@]}"; do
    remove_bundle "$b"
    ok "${DIM}${b}${NC}"
  done

  echo ""
  echo -e "  ${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "  ${CHECK} ${BOLD}$(t UNINSTALLED)${NC}"
  echo -e "  ${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
}

run_upgrade() {
  info "$(t UPGRADE_SCANNING)"
  scan_upgrade_targets
  if [[ ${#UPGRADE_ROWS[@]} -eq 0 ]]; then
    die "$(t UPGRADE_NONE_FOUND)"
  fi

  echo ""
  info "$(t UPGRADE_TARGETS)"
  local row agent scope base label
  for row in "${UPGRADE_ROWS[@]}"; do
    IFS='|' read -r agent scope base label <<< "$row"
    echo -e "      ${label} [${scope}] → ${DIM}${base}${NC}"
  done

  ensure_source
  echo ""

  local lang
  for row in "${UPGRADE_ROWS[@]}"; do
    IFS='|' read -r agent scope base label <<< "$row"
    if [[ -n "$ARG_LANG" ]]; then
      lang="$ARG_LANG"
    else
      lang="$(detect_installed_lang "$base")"
    fi
    install_to "$label [${scope}, lang=${lang}]" "$base" "$lang"
  done

  echo ""
  echo -e "  ${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "  ${CHECK} ${BOLD}$(t INSTALLED)${NC}  ${DIM}v${VERSION}${NC}"
  echo -e "  ${DIM}  $(t RESTART_TIP)${NC}"
  echo -e "  ${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  print_wire_block "${lang:-en}"
  echo ""
}

# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
main() {
  parse_args "$@"
  detect_ui_lang
  parse_agent_registry
  validate_registry
  if [[ "$MODE" == "list-agents" ]]; then
    banner
    print_agent_list
    exit 0
  fi
  banner
  case "$MODE" in
    install)   run_install ;;
    uninstall) run_uninstall ;;
    upgrade)   run_upgrade ;;
    *) die "unknown mode: $MODE" ;;
  esac
}

main "$@"
