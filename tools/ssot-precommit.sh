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
ORIG_PWD="$(pwd -P 2>/dev/null || pwd)"

SSOT_TARGET="${SSOT_DIR:-SSOT}"
while [[ "$SSOT_TARGET" != "/" && "$SSOT_TARGET" == */ ]]; do
  SSOT_TARGET="${SSOT_TARGET%/}"
done
while [[ "$SSOT_TARGET" == ./* && "$SSOT_TARGET" != "./" ]]; do
  SSOT_TARGET="${SSOT_TARGET#./}"
done
STRICT="${SSOT_PRECOMMIT_STRICT:-0}"
ALWAYS="${SSOT_PRECOMMIT_ALWAYS:-0}"

# Canonicalize relative Git routing env paths before cd "$REPO_ROOT" so split
# GIT_DIR/GIT_WORK_TREE or subdirectory direct invocations stay valid.
for _git_var in GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_SHALLOW_FILE; do
  _git_val="${!_git_var:-}"
  if [[ -n "$_git_val" && "$_git_val" != /* ]]; then
    export "${_git_var}=$ORIG_PWD/$_git_val"
  fi
done
unset _git_var _git_val

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$REPO_ROOT" ]] || exit 0
cd "$REPO_ROOT" || exit 0
REPO_ROOT_REAL="$(pwd -P)"

resolve_abs_path() {
  local p="$1" d
  if [[ "$p" == /* ]]; then
    if [[ -d "$p" ]]; then
      (cd "$p" 2>/dev/null && pwd -P) || printf '%s\n' "$p"
      return 0
    fi
    d="$(cd "$(dirname "$p")" 2>/dev/null && pwd -P)" || { printf '%s\n' "$p"; return 0; }
    printf '%s/%s\n' "$d" "$(basename "$p")"
  else
    if [[ -d "$REPO_ROOT/$p" ]]; then
      (cd "$REPO_ROOT/$p" 2>/dev/null && pwd -P) || printf '%s/%s\n' "$REPO_ROOT" "$p"
      return 0
    fi
    d="$(cd "$(dirname "$REPO_ROOT/$p")" 2>/dev/null && pwd -P)" || { printf '%s/%s\n' "$REPO_ROOT" "$p"; return 0; }
    printf '%s/%s\n' "$d" "$(basename "$p")"
  fi
}

# Canonicalize SSOT_TARGET relative to REPO_ROOT; fail loudly if it points outside the repo.
if [[ "$SSOT_TARGET" == /* ]]; then
  ssot_abs="$(resolve_abs_path "$SSOT_TARGET")"
  if [[ "$ssot_abs" == "$REPO_ROOT_REAL" ]]; then
    SSOT_TARGET="."
  elif [[ "$ssot_abs" == "$REPO_ROOT_REAL/"* ]]; then
    SSOT_TARGET="${ssot_abs#"$REPO_ROOT_REAL"/}"
  elif [[ "$SSOT_TARGET" == "$REPO_ROOT" ]]; then
    SSOT_TARGET="."
  elif [[ "$SSOT_TARGET" == "$REPO_ROOT/"* ]]; then
    SSOT_TARGET="${SSOT_TARGET#"$REPO_ROOT"/}"
  else
    echo "ssot-precommit: SSOT_DIR '$SSOT_TARGET' is outside repository root '$REPO_ROOT'" >&2
    exit 2
  fi
fi
if [[ "$SSOT_TARGET" == ".." || "$SSOT_TARGET" == ../* || "$SSOT_TARGET" == */../* || "$SSOT_TARGET" == */.. ]]; then
  echo "ssot-precommit: SSOT_DIR '$SSOT_TARGET' must stay inside repository root '$REPO_ROOT'" >&2
  exit 2
fi

is_format4_readme_stream() {
  awk '
    NR == 1 { sub(/\r$/, ""); if ($0 != "---") exit 1; next }
    { sub(/\r$/, "") }
    $0 == "---" { exit (found ? 0 : 1) }
    /^ssot_format:[ \t]*["'\'']?4["'\'']?([ \t]+#.*)?[ \t]*$/ { found = 1 }
    END { if (!found) exit 1 }
  '
}

# If SSOT_DIR names a Format-4 README.md inside a subdirectory (e.g. SSOT/README.md),
# normalize SSOT_TARGET to its containing SSOT directory before trigger/snapshot checks
# so non-.md files inside SSOT/ (such as .bootstrap/) trigger and are materialized.
if [[ "$(basename "$SSOT_TARGET")" == "README.md" && "$SSOT_TARGET" == */* ]]; then
  f4_match=0
  if git cat-file -e ":$SSOT_TARGET" 2>/dev/null && git cat-file -p ":$SSOT_TARGET" 2>/dev/null | is_format4_readme_stream; then
    f4_match=1
  elif [[ -f "$SSOT_TARGET" ]] && is_format4_readme_stream < "$SSOT_TARGET"; then
    f4_match=1
  elif git rev-parse --verify --quiet HEAD >/dev/null 2>&1 && git cat-file -e "HEAD:$SSOT_TARGET" 2>/dev/null && git cat-file -p "HEAD:$SSOT_TARGET" 2>/dev/null | is_format4_readme_stream; then
    f4_match=1
  fi
  if [[ "$f4_match" -eq 1 ]]; then
    SSOT_TARGET="$(dirname "$SSOT_TARGET")"
  fi
fi

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
      if [[ "$SSOT_TARGET" == "." || "$p" == "$SSOT_TARGET" || "$p" == "$SSOT_TARGET/"* || "$p" == *.[mM][dD] || "$p" == *.[mM][dD][cC] || "$p" == ".cursorrules" || "$p" == ".windsurfrules" ]]; then
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
  local xdg="${XDG_CONFIG_HOME:-${HOME:+$HOME/.config}}"
  local -a candidates=(
    "$REPO_ROOT/.agents/skills/$rel"
    "$REPO_ROOT/.claude/skills/$rel"
    "$REPO_ROOT/.windsurf/skills/$rel"
    "$REPO_ROOT/.dsh/skills/$rel"
  )
  [[ -n "$SCRIPT_DIR" ]] && candidates+=("$SCRIPT_DIR/../skills/$rel")
  [[ -n "${CODEX_HOME:-}" ]] && candidates+=("$CODEX_HOME/skills/$rel")
  [[ -n "${CLAUDE_CONFIG_DIR:-}" ]] && candidates+=("$CLAUDE_CONFIG_DIR/skills/$rel")
  [[ -n "${DSH_HOME:-}" ]] && candidates+=("$DSH_HOME/skills/$rel")
  if [[ -n "$xdg" ]]; then
    candidates+=(
      "$xdg/opencode/skills/$rel"
      "$xdg/agents/skills/$rel"
    )
  fi
  if [[ -n "${HOME:-}" ]]; then
    candidates+=(
      "$HOME/.agents/skills/$rel"
      "$HOME/.codex/skills/$rel"
      "$HOME/.claude/skills/$rel"
      "$HOME/.cursor/skills/$rel"
      "$HOME/.copilot/skills/$rel"
      "$HOME/.gemini/config/skills/$rel"
      "$HOME/.gemini/skills/$rel"
      "$HOME/.gemini/antigravity/skills/$rel"
      "$HOME/.gemini/antigravity-cli/skills/$rel"
      "$HOME/.codeium/windsurf/skills/$rel"
      "$HOME/.dsh/skills/$rel"
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

is_relevant_wt_path() {
  local p="$1"
  [[ -n "$p" ]] || return 1
  case "$p" in
    # *.[mM][dD] also covers AGENTS.md, CLAUDE.md, GEMINI.md, and .github/copilot-instructions.md.
    "$SSOT_TARGET"|"$SSOT_TARGET/"*|*.[mM][dD]|*.[mM][dD][cC]|.cursorrules|.windsurfrules|.gitignore|*/.gitignore)
      return 0 ;;
  esac
  return 1
}

need_snapshot=0
if [[ ! -e "$SSOT_TARGET" || "$staged_del_on_disk" -eq 1 ]]; then
  need_snapshot=1
fi

if [[ "$need_snapshot" -eq 0 && ( -n "${GIT_DIR:-}" || -n "${GIT_WORK_TREE:-}" ) ]]; then
  if ! git_clean rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    # ssot-check.py strips GIT_DIR/GIT_WORK_TREE; split Git repos require a self-contained snapshot.
    need_snapshot=1
  fi
fi

if [[ "$need_snapshot" -eq 0 && -n "${GIT_INDEX_FILE:-}" ]]; then
  # Preserve GIT_DIR/GIT_WORK_TREE while unsetting GIT_INDEX_FILE so split repos do not fail.
  if default_index_raw="$(env -u GIT_INDEX_FILE git rev-parse --git-path index 2>/dev/null)" && [[ -n "$default_index_raw" ]]; then
    default_index="$(resolve_abs_path "$default_index_raw")"
    active_index="$(resolve_abs_path "$GIT_INDEX_FILE")"
    if [[ "$active_index" != "$default_index" ]]; then
      need_snapshot=1
    fi
  else
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

# Any untracked non-ignored file anywhere in the repo could satisfy a staged Format-4 external link.
if [[ "$need_snapshot" -eq 0 ]]; then
  if IFS= read -r -d '' _ < <(git ls-files --others --exclude-standard -z -- 2>/dev/null || true); then
    need_snapshot=1
  fi
fi

STAGE_DIR=""
cleanup() {
  [[ -z "$STAGE_DIR" ]] || rm -rf -- "$STAGE_DIR"
}
trap cleanup EXIT

stage_targeted_snapshot() {
  python3 -B - "$REPO_ROOT" "$STAGE_DIR" "$SSOT_TARGET" "$CHECKER" <<'PY'
import ast
import importlib.util
import os
import subprocess
import sys

repo, stage, ssot_target, checker = sys.argv[1:5]
routing_env = {
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_SHALLOW_FILE", "GIT_PREFIX", "GIT_IMPLICIT_WORK_TREE",
}
clean_env = {k: v for k, v in os.environ.items() if k not in routing_env}


def is_import_safe_checker(path):
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    defs = set()
    assigns = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef)):
            continue
        if isinstance(node, ast.FunctionDef):
            defs.add(node.name)
            continue
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigns.add(target.id)
            continue
        if isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Constant):
                continue
            if (isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Attribute)
                    and isinstance(node.value.func.value, ast.Name)
                    and node.value.func.attr == "update"):
                continue
            return False
        if isinstance(node, ast.If):
            test = node.test
            if (isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name) and test.left.id == "__name__"
                    and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)
                    and len(test.comparators) == 1
                    and isinstance(test.comparators[0], ast.Constant)
                    and test.comparators[0].value == "__main__"):
                continue
            return False
        return False
    return {"link_targets", "resolve", "read_text", "front_matter"}.issubset(defs) and "SCHEME_RE" in assigns


try:
    if not is_import_safe_checker(checker):
        sys.exit(10)
    spec = importlib.util.spec_from_file_location("ssot_chk_helper", checker)
    chk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chk)
    if not all(hasattr(chk, attr) for attr in ("link_targets", "resolve", "read_text", "front_matter", "SCHEME_RE")):
        sys.exit(10)
except BaseException:
    sys.exit(10)

raw = subprocess.run(["git", "ls-files", "--stage", "-z"], cwd=repo, capture_output=True, check=True).stdout
entries = []
all_paths = set()
all_dirs = set()
initial = []
submodules = []
ssot_prefix = "" if ssot_target == "." else ssot_target + "/"

for rec in raw.split(b"\0"):
    if not rec:
        continue
    meta, _, p_bytes = rec.partition(b"\t")
    parts_meta = meta.split(b" ")
    if len(parts_meta) < 3 or parts_meta[2] != b"0":
        continue
    mode = parts_meta[0].decode("ascii", "replace")
    p = p_bytes.decode("utf-8", "surrogateescape")
    entries.append((mode, p))
    all_paths.add(p)
    segs = p.split("/")
    for i in range(1, len(segs)):
        all_dirs.add("/".join(segs[:i]))
    if mode == "160000":
        submodules.append(p)
        continue
    low = p.lower()
    if (
        mode == "120000"
        or ssot_target == "."
        or p == ssot_target
        or p.startswith(ssot_prefix)
        or low.endswith((".md", ".mdc"))
        or p in (".cursorrules", ".windsurfrules", ".gitignore")
        or p.endswith("/.gitignore")
    ):
        initial.append(p)

if initial:
    inp = b"\0".join(p.encode("utf-8", "surrogateescape") for p in initial) + b"\0"
    subprocess.run(
        ["git", "checkout-index", "-f", "--prefix=" + stage + "/", "--stdin", "-z"],
        cwd=repo, input=inp, check=True,
    )

# Mark 160000 submodule gitlinks with a nested .git boundary so ssot-check.py
# treats them as unpopulated submodules (INFO) instead of false broken-link ERROR.
for sub in submodules:
    os.makedirs(os.path.join(stage, sub, ".git"), exist_ok=True)

stage_real = os.path.realpath(stage)
checked_out = set(initial)
extra_files = set()
extra_dirs = set()


def note_target(resolved):
    for root_ref, candidate in ((stage, resolved), (stage_real, os.path.realpath(resolved))):
        try:
            rel_t = os.path.relpath(candidate, root_ref).replace(os.sep, "/")
        except ValueError:
            continue
        if rel_t.startswith("..") or rel_t == ".":
            continue
        if rel_t in all_paths and rel_t not in checked_out:
            extra_files.add(rel_t)
        elif rel_t in all_dirs:
            extra_dirs.add(rel_t)


for rel in initial:
    if not rel.lower().endswith(".md"):
        continue
    full = os.path.join(stage, rel)
    if not os.path.isfile(full):
        continue
    try:
        text = chk.read_text(full)
    except OSError:
        continue
    for _, target in chk.link_targets(text):
        t = target.strip()
        if not t or chk.SCHEME_RE.match(t):
            continue
        resolved, _ = chk.resolve(full, t)
        note_target(resolved)

for mode, p in entries:
    if mode != "120000":
        continue
    full = os.path.join(stage, p)
    if os.path.islink(full):
        link = os.readlink(full)
        if not os.path.isabs(link):
            note_target(os.path.normpath(os.path.join(os.path.dirname(full), link)))

if extra_files:
    inp = b"\0".join(p.encode("utf-8", "surrogateescape") for p in sorted(extra_files)) + b"\0"
    subprocess.run(
        ["git", "checkout-index", "-f", "--prefix=" + stage + "/", "--stdin", "-z"],
        cwd=repo, input=inp, check=True,
    )
    checked_out |= extra_files

for d in sorted(extra_dirs):
    os.makedirs(os.path.join(stage, d), exist_ok=True)

skip = [p for mode, p in entries if mode != "160000" and p not in checked_out]
if skip:
    inp = b"\0".join(p.encode("utf-8", "surrogateescape") for p in skip) + b"\0"
    subprocess.run(
        ["git", "-C", stage, "update-index", "--skip-worktree", "-z", "--stdin"],
        env=clean_env, input=inp, check=True,
    )
PY
}

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
    if [[ -n "${GIT_ALTERNATE_OBJECT_DIRECTORIES:-}" ]]; then
      IFS=':' read -r -a alt_dirs <<< "$GIT_ALTERNATE_OBJECT_DIRECTORIES"
      for alt_dir in "${alt_dirs[@]}"; do
        [[ -n "$alt_dir" && -d "$alt_dir" ]] && printf '%s\n' "$(cd "$alt_dir" && pwd -P)"
      done
    fi
    printf '%s/objects\n' "$common_dir"
  } > "$STAGE_DIR/.git/objects/info/alternates"
  if [[ "$has_head" -eq 1 ]]; then
    head_sha="$(git rev-parse HEAD)"
    git_clean -C "$STAGE_DIR" update-ref HEAD "$head_sha"
  fi
  shallow_file="${GIT_SHALLOW_FILE:-}"
  if [[ -z "$shallow_file" ]]; then
    shallow_file="$(git rev-parse --git-path shallow 2>/dev/null || true)"
  fi
  if [[ -n "$shallow_file" && -f "$shallow_file" ]]; then
    cp "$shallow_file" "$STAGE_DIR/.git/shallow"
  fi
  git ls-files --stage -z | git_clean -C "$STAGE_DIR" update-index -z --index-info
  if ! stage_targeted_snapshot; then
    git checkout-index -a -f --prefix="$STAGE_DIR/"
    python3 -B - "$REPO_ROOT" "$STAGE_DIR" <<'PY'
import os, subprocess, sys
repo, stage = sys.argv[1:3]
raw = subprocess.run(["git", "ls-files", "--stage", "-z"], cwd=repo, capture_output=True, check=True).stdout
for rec in raw.split(b"\0"):
    if rec.startswith(b"160000 "):
        _, _, p_bytes = rec.partition(b"\t")
        if p_bytes:
            os.makedirs(os.path.join(stage, p_bytes.decode("utf-8", "surrogateescape"), ".git"), exist_ok=True)
PY
  fi
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
python3 -B "$CHECKER" "${args[@]}"
rc=$?
set -e

if [[ "$rc" -ne 0 ]]; then
  echo "ssot-precommit: commit blocked by ssot-check.py (exit $rc). Fix errors above or bypass intentionally with --no-verify." >&2
  exit "$rc"
fi
exit 0
