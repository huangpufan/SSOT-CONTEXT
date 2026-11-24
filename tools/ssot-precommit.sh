#!/usr/bin/env bash
# Opt-in host-agnostic Git pre-commit guard for SSOT-CONTEXT.
# Lives outside skills/ (zero protocol words, zero model tokens).
# Skips immediately when staged changes stay outside SSOT/, Markdown owners,
# and file deletions/renames; otherwise runs ssot-check.py before commit.
set -euo pipefail

SSOT_TARGET="${SSOT_DIR:-SSOT}"
STRICT="${SSOT_PRECOMMIT_STRICT:-0}"
ALWAYS="${SSOT_PRECOMMIT_ALWAYS:-0}"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$REPO_ROOT" ]] || exit 0
cd "$REPO_ROOT" || exit 0

[[ -e "$SSOT_TARGET" ]] || exit 0

should_check=0
if [[ "$ALWAYS" == "1" ]]; then
  should_check=1
else
  # Inspect staged changes: trigger on SSOT/ paths, any .md file, or any delete/rename.
  # git diff --cached works on both normal commits and unborn HEAD (initial commit).
  while IFS= read -r -d '' status; do
    IFS= read -r -d '' path1 || break
    path2=""
    if [[ "$status" == R* || "$status" == C* ]]; then
      IFS= read -r -d '' path2 || break
    fi
    if [[ "$status" == D* || "$status" == R* ]]; then
      should_check=1
      break
    fi
    for p in "$path1" "$path2"; do
      [[ -n "$p" ]] || continue
      if [[ "$p" == "$SSOT_TARGET" || "$p" == "$SSOT_TARGET/"* || "$p" == *.md || "$p" == *.MD ]]; then
        should_check=1
        break 2
      fi
    done
  done < <(git diff --cached --name-status -z -M -- 2>/dev/null || true)
fi

[[ "$should_check" -eq 1 ]] || exit 0

find_checker() {
  if [[ -n "${SSOT_CHECKER:-}" ]]; then
    [[ -f "$SSOT_CHECKER" ]] && { printf '%s\n' "$SSOT_CHECKER"; return 0; }
    return 1
  fi
  local script_dir cand
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local -a candidates=(
    "$REPO_ROOT/.agents/skills/ssot-doctor/assets/scripts/ssot-check.py"
    "$REPO_ROOT/.claude/skills/ssot-doctor/assets/scripts/ssot-check.py"
    "$REPO_ROOT/.windsurf/skills/ssot-doctor/assets/scripts/ssot-check.py"
    "$script_dir/../skills/ssot-doctor/assets/scripts/ssot-check.py"
    "${HOME:-}/.agents/skills/ssot-doctor/assets/scripts/ssot-check.py"
    "${HOME:-}/.claude/skills/ssot-doctor/assets/scripts/ssot-check.py"
    "${HOME:-}/.gemini/config/skills/ssot-doctor/assets/scripts/ssot-check.py"
  )
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

args=("$SSOT_TARGET")
if git rev-parse --verify --quiet HEAD >/dev/null 2>&1; then
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
