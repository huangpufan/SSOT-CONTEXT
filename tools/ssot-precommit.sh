#!/usr/bin/env bash
# Opt-in host-agnostic Git pre-commit guard for SSOT-CONTEXT.
# Lives outside skills/ (zero protocol words, zero model tokens).
# Skips immediately when staged changes stay outside SSOT/, Markdown owners,
# and file deletions/renames; otherwise runs ssot-check.py before commit.
set -euo pipefail

resolve_script_dir() {
  local path="${BASH_SOURCE[0]}" hops=0 dir link
  while [[ -L "$path" ]]; do
    hops=$((hops + 1))
    (( hops <= 20 )) || break
    link="$(readlink "$path")" || break
    if [[ "$link" == /* ]]; then
      path="$link"
    else
      dir="$(cd "$(dirname "$path")" && pwd -P)" || break
      path="$dir/$link"
    fi
  done
  cd "$(dirname "$path")" && pwd -P
}

# Resolve before changing directories so relative invocations from subdirectories still work.
SCRIPT_DIR="$(resolve_script_dir 2>/dev/null || true)"

SSOT_TARGET="${SSOT_DIR:-SSOT}"
while [[ "$SSOT_TARGET" != "/" && "$SSOT_TARGET" == */ ]]; do
  SSOT_TARGET="${SSOT_TARGET%/}"
done
while [[ "$SSOT_TARGET" == ./* && "$SSOT_TARGET" != "./" ]]; do
  SSOT_TARGET="${SSOT_TARGET#./}"
done
STRICT="${SSOT_PRECOMMIT_STRICT:-0}"
ALWAYS="${SSOT_PRECOMMIT_ALWAYS:-0}"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$REPO_ROOT" ]] || exit 0
cd "$REPO_ROOT" || exit 0

has_head=0
if git rev-parse --verify --quiet HEAD >/dev/null 2>&1; then
  has_head=1
fi

head_has_target=0
if [[ "$has_head" -eq 1 ]] && git cat-file -e "HEAD:$SSOT_TARGET" 2>/dev/null; then
  head_has_target=1
fi

if [[ ! -e "$SSOT_TARGET" && "$head_has_target" -eq 0 ]]; then
  if ! git ls-files --cached --error-unmatch -- "$SSOT_TARGET" >/dev/null 2>&1; then
    exit 0
  fi
fi

should_check=0
staged_del_on_disk=0
if [[ "$ALWAYS" == "1" ]]; then
  should_check=1
fi

# Inspect staged changes: trigger on SSOT/ paths, any .md file, or any delete/rename/typechange.
# git diff --cached works on both normal commits and unborn HEAD (initial commit).
while IFS= read -r -d '' status; do
  IFS= read -r -d '' path1 || break
  path2=""
  if [[ "$status" == R* || "$status" == C* ]]; then
    IFS= read -r -d '' path2 || break
  fi
  if [[ "$status" == D* || "$status" == R* ]]; then
    should_check=1
    if [[ -n "$path1" && ( -e "$path1" || -L "$path1" ) ]]; then
      staged_del_on_disk=1
    fi
  elif [[ "$status" == T* ]]; then
    should_check=1
  fi
  if [[ "$should_check" -eq 0 ]]; then
    for p in "$path1" "$path2"; do
      [[ -n "$p" ]] || continue
      if [[ "$p" == "$SSOT_TARGET" || "$p" == "$SSOT_TARGET/"* || "$p" == *.md || "$p" == *.MD ]]; then
        should_check=1
        break
      fi
    done
  fi
done < <(git diff --cached --name-status -z -M -- 2>/dev/null || true)

[[ "$should_check" -eq 1 ]] || exit 0

find_checker() {
  if [[ -n "${SSOT_CHECKER:-}" ]]; then
    [[ -f "$SSOT_CHECKER" ]] && { printf '%s\n' "$SSOT_CHECKER"; return 0; }
    return 1
  fi
  local cand rel="ssot-doctor/assets/scripts/ssot-check.py"
  local -a candidates=(
    "$REPO_ROOT/.agents/skills/$rel"
    "$REPO_ROOT/.claude/skills/$rel"
    "$REPO_ROOT/.windsurf/skills/$rel"
  )
  [[ -n "$SCRIPT_DIR" ]] && candidates+=("$SCRIPT_DIR/../skills/$rel")
  [[ -n "${CODEX_HOME:-}" ]] && candidates+=("$CODEX_HOME/skills/$rel")
  [[ -n "${CLAUDE_CONFIG_DIR:-}" ]] && candidates+=("$CLAUDE_CONFIG_DIR/skills/$rel")
  if [[ -n "${HOME:-}" ]]; then
    candidates+=(
      "$HOME/.agents/skills/$rel"
      "$HOME/.codex/skills/$rel"
      "$HOME/.claude/skills/$rel"
      "$HOME/.cursor/skills/$rel"
      "$HOME/.gemini/config/skills/$rel"
      "$HOME/.gemini/skills/$rel"
      "$HOME/.gemini/antigravity/skills/$rel"
      "$HOME/.codeium/windsurf/skills/$rel"
    )
  fi
  for cand in "${candidates[@]}"; do
    [[ -f "$cand" ]] && { printf '%s\n' "$cand"; return 0; }
  done
  return 1
}

if ! CHECKER="$(find_checker)"; then
  if [[ "$STRICT" == "1" ]]; then
    echo "ssot-precommit: ssot-check.py not found (set SSOT_CHECKER or install SSOT-CONTEXT)" >&2
    exit 2
  fi
  echo "ssot-precommit: ssot-check.py not found; skipping (set SSOT_PRECOMMIT_STRICT=1 to require)" >&2
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  if [[ "$STRICT" == "1" ]]; then
    echo "ssot-precommit: python3 not found (install python3 to run ssot-check.py)" >&2
    exit 2
  fi
  echo "ssot-precommit: python3 not found; skipping (set SSOT_PRECOMMIT_STRICT=1 to require)" >&2
  exit 0
fi

git_clean() {
  env -u GIT_DIR -u GIT_WORK_TREE -u GIT_COMMON_DIR -u GIT_INDEX_FILE \
      -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES \
      -u GIT_SHALLOW_FILE -u GIT_PREFIX -u GIT_IMPLICIT_WORK_TREE \
      git "$@"
}

resolve_abs_path() {
  local p="$1" d
  if [[ "$p" == /* ]]; then
    d="$(cd "$(dirname "$p")" 2>/dev/null && pwd -P)" || { printf '%s\n' "$p"; return 0; }
    printf '%s/%s\n' "$d" "$(basename "$p")"
  else
    d="$(cd "$(dirname "$REPO_ROOT/$p")" 2>/dev/null && pwd -P)" || { printf '%s/%s\n' "$REPO_ROOT" "$p"; return 0; }
    printf '%s/%s\n' "$d" "$(basename "$p")"
  fi
}

is_relevant_wt_path() {
  local p="$1"
  [[ -n "$p" ]] || return 1
  case "$p" in
    # *.md also covers AGENTS.md, CLAUDE.md, GEMINI.md, and .github/copilot-instructions.md.
    "$SSOT_TARGET"|"$SSOT_TARGET/"*|*.md|*.MD|*.mdc|.cursorrules|.windsurfrules|.gitignore|*/.gitignore)
      return 0 ;;
  esac
  return 1
}

need_snapshot=0
if [[ ! -e "$SSOT_TARGET" || "$staged_del_on_disk" -eq 1 ]]; then
  need_snapshot=1
fi

if [[ "$need_snapshot" -eq 0 && -n "${GIT_INDEX_FILE:-}" ]]; then
  default_index="$(resolve_abs_path "$(git_clean rev-parse --git-path index)")"
  active_index="$(resolve_abs_path "$GIT_INDEX_FILE")"
  if [[ "$active_index" != "$default_index" ]]; then
    need_snapshot=1
  fi
fi

if [[ "$need_snapshot" -eq 0 ]]; then
  while IFS= read -r -d '' status; do
    IFS= read -r -d '' path1 || break
    path2=""
    if [[ "$status" == R* || "$status" == C* ]]; then
      IFS= read -r -d '' path2 || break
    fi
    if [[ "$status" == D* || "$status" == R* || "$status" == T* ]]; then
      need_snapshot=1
      break
    fi
    if is_relevant_wt_path "$path1" || is_relevant_wt_path "$path2"; then
      need_snapshot=1
      break
    fi
  done < <(git diff --name-status -z -M -- 2>/dev/null || true)
fi

if [[ "$need_snapshot" -eq 0 ]]; then
  if IFS= read -r -d '' _ < <(git ls-files --others --exclude-standard -z -- "$SSOT_TARGET" 2>/dev/null || true); then
    need_snapshot=1
  fi
fi

STAGE_DIR=""
cleanup() {
  [[ -z "$STAGE_DIR" ]] || rm -rf -- "$STAGE_DIR"
}
trap cleanup EXIT

check_target="$SSOT_TARGET"
if [[ "$need_snapshot" -eq 1 ]]; then
  STAGE_DIR="$(mktemp -d)"
  common_dir="$(git rev-parse --git-common-dir)"
  common_dir="$(cd "$common_dir" && pwd -P)"
  obj_fmt="$(git rev-parse --show-object-format 2>/dev/null || true)"
  init_args=()
  if [[ -n "$obj_fmt" && "$obj_fmt" != "sha1" ]]; then
    init_args+=("--object-format=$obj_fmt")
  fi
  git_clean init -q ${init_args[@]+"${init_args[@]}"} "$STAGE_DIR"
  {
    if [[ -n "${GIT_OBJECT_DIRECTORY:-}" ]]; then
      printf '%s\n' "$(cd "$GIT_OBJECT_DIRECTORY" && pwd -P)"
    fi
    printf '%s/objects\n' "$common_dir"
  } > "$STAGE_DIR/.git/objects/info/alternates"
  if [[ "$has_head" -eq 1 ]]; then
    head_sha="$(git rev-parse HEAD)"
    git_clean -C "$STAGE_DIR" update-ref HEAD "$head_sha"
  fi
  git ls-files --stage -z | git_clean -C "$STAGE_DIR" update-index -z --index-info
  git checkout-index -a -f --prefix="$STAGE_DIR/"
  check_target="$STAGE_DIR/$SSOT_TARGET"
fi

if [[ ! -e "$check_target" && ! -L "$check_target" ]]; then
  if [[ "$head_has_target" -eq 1 ]]; then
    echo "ssot-precommit: commit removes tracked SSOT target '$SSOT_TARGET' (which exists in HEAD and may hold confirmed invariants). Restore it, or bypass intentionally with --no-verify." >&2
    exit 1
  fi
  exit 0
fi

args=("$check_target")
if [[ "$has_head" -eq 1 ]]; then
  args+=("--since" "HEAD")
fi

set +e
python3 "$CHECKER" "${args[@]}"
rc=$?
set -e

if [[ "$rc" -ne 0 ]]; then
  echo "ssot-precommit: commit blocked by ssot-check.py (exit $rc). Fix errors above or bypass intentionally with --no-verify." >&2
  exit "$rc"
fi
exit 0
