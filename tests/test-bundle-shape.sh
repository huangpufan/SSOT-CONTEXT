#!/usr/bin/env bash
# tests/test-bundle-shape.sh — bundle structure, link integrity, and budgets
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1
SKILLS="$PROJECT_ROOT/skills"
TEMPLATES="$SKILLS/ssot-bootstrap/assets/templates"
BUNDLE_SKILLS=(ssot-preflight ssot-bootstrap ssot-closeout ssot-doctor ssot-audit ssot-skill)
LIFECYCLE_SKILLS=(ssot-preflight ssot-bootstrap ssot-closeout ssot-doctor)
PASS=0
FAIL=0
pass() { echo "  ok   : $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL : $1"; FAIL=$((FAIL+1)); }

echo "=== test-bundle-shape ==="

# 1. VERSION and the preflight protocol_version are the same number.
VERSION_CONTENT="$(tr -d '[:space:]' < "$PROJECT_ROOT/VERSION" 2>/dev/null || true)"
PREFLIGHT_VERSION="$(sed -nE 's/^[[:space:]]*protocol_version:[[:space:]]*"?([^"]+)"?[[:space:]]*$/\1/p' "$SKILLS/ssot-preflight/SKILL.md" | head -1)"
if [[ -n "$VERSION_CONTENT" && "$VERSION_CONTENT" == "$PREFLIGHT_VERSION" ]]; then
  pass "VERSION ($VERSION_CONTENT) matches ssot-preflight protocol_version"
else
  fail "VERSION='$VERSION_CONTENT' != ssot-preflight protocol_version='$PREFLIGHT_VERSION'"
fi

# 2. Every skill has frontmatter (name matches its directory, a description),
# a non-empty body, and agent metadata that names it.
for skill in "${BUNDLE_SKILLS[@]}"; do
  file="$SKILLS/$skill/SKILL.md"
  if [[ ! -f "$file" ]]; then fail "$skill: SKILL.md missing"; continue; fi
  name="$(awk '/^---$/{n++; next} n==1 && /^name:/{sub(/^name:[[:space:]]*/,""); print; exit}' "$file")"
  [[ "$name" == "$skill" ]] && pass "$skill: name matches" || fail "$skill: name '$name' does not match directory"
  grep -qE '^description: .{40,}' "$file" && pass "$skill: description present" || fail "$skill: description missing or too short"
  body="$(awk '/^---$/{n++; next} n>=2' "$file" | tr -d '[:space:]')"
  [[ -n "$body" ]] && pass "$skill: body present" || fail "$skill: body empty"
  yaml="$SKILLS/$skill/agents/openai.yaml"
  if [[ -f "$yaml" ]] && grep -q 'display_name:' "$yaml" && grep -q "\\\$$skill" "$yaml"; then
    pass "$skill: openai.yaml present and names \$$skill"
  else
    fail "$skill: openai.yaml missing, or default_prompt does not name \$$skill"
  fi
done

# 3. Lifecycle skills route to the shared memory model (one owner, linked).
for skill in ssot-bootstrap ssot-closeout ssot-doctor; do
  if grep -q 'ssot-preflight/references/memory-model.md' "$SKILLS/$skill/SKILL.md"; then
    pass "$skill links the memory model"
  else
    fail "$skill does not link ssot-preflight/references/memory-model.md"
  fi
done
grep -q 'references/memory-model.md' "$SKILLS/ssot-preflight/SKILL.md" &&
  pass "ssot-preflight links the memory model" || fail "ssot-preflight does not link the memory model"

# 4. Relative links and heading anchors resolve across skills and repository docs
# (fenced examples, inline code, consumer templates, and research/ skipped).
check_links() {
  python3 -B - "$PROJECT_ROOT" "$@" <<'PY'
import importlib.util
import os
import subprocess
import sys
from urllib.parse import unquote

root = sys.argv[1]
mode = sys.argv[2]
spec = importlib.util.spec_from_file_location("check", f"{root}/skills/ssot-doctor/assets/scripts/ssot-check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

if mode == "--repo":
    base = root
    raw = subprocess.run(
        ["git", "-C", root, "ls-files", "-co", "--exclude-standard", "-z", "--",
         "*.md", ":!:research/", ":!:skills/ssot-bootstrap/assets/templates/"],
        capture_output=True, text=True, check=True,
    ).stdout
    paths = [os.path.join(root, rel) for rel in filter(None, raw.split("\0"))]
else:
    base = mode
    paths = sys.argv[3:]

failed = 0
for path in paths:
    rel = os.path.relpath(path, base)
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    for number, raw_target in check.link_targets(text):
        target = raw_target.strip()
        if not target or check.SCHEME_RE.match(target):
            continue
        resolved, fragment = check.resolve(path, target)
        if not os.path.exists(resolved):
            print(f"  FAIL : broken link in {rel}:{number}: {target}")
            failed += 1
            continue
        if fragment and os.path.isfile(resolved):
            line_anchor = check.LINE_ANCHOR_RE.match(fragment)
            if line_anchor:
                with open(resolved, encoding="utf-8", errors="replace") as target_handle:
                    length = sum(1 for _ in target_handle)
                if int(line_anchor.group(1)) > length:
                    print(f"  FAIL : line anchor past end of file in {rel}:{number}: {target}")
                    failed += 1
            elif resolved.lower().endswith(".md") and unquote(fragment) not in check.anchors(resolved):
                print(f"  FAIL : missing heading anchor in {rel}:{number}: {target}")
                failed += 1

sys.exit(1 if failed else 0)
PY
}
PROBE_DIR="$(mktemp -d)"
trap 'rm -rf "$PROBE_DIR"' EXIT
mkdir -p "$PROBE_DIR/skills/s"
printf '# E\n' > "$PROBE_DIR/e.md"
printf '[missing](missing.md#x)\n' > "$PROBE_DIR/probe-doc.md"
check_links "$PROBE_DIR" "$PROBE_DIR/probe-doc.md" >/dev/null && fail "link check accepted a broken relative link in a top-level doc" || pass "link check rejects a broken relative link in a top-level doc"
printf '[bad](../../e.md#bad-anchor)\n' > "$PROBE_DIR/skills/s/SKILL.md"
check_links "$PROBE_DIR" "$PROBE_DIR/skills/s/SKILL.md" >/dev/null && fail "link check accepted a broken heading anchor in a skill file" || pass "link check rejects a broken heading anchor in a skill file"
printf '[e](e.md#e) [x](https://example.test/m.md) `[z](missing.md#bad)`\n\n```\n[y](missing.md#bad)\n```\n' > "$PROBE_DIR/probe.md"
check_links "$PROBE_DIR" "$PROBE_DIR/probe.md" >/dev/null && pass "link check accepts valid anchors, external URLs, inline code, and fenced examples" || fail "link check rejected valid links"
if check_links --repo; then
  pass "all skill, reference, top-level, docs, and test Markdown links and anchors resolve"
else
  fail "one or more repository Markdown links or heading anchors are broken"
fi

# Repository documentation follows the filename convention in CONTRIBUTING.md.
if python3 - <<'PY'
from datetime import date
from pathlib import Path
import re
import subprocess

pattern = re.compile(
    r'([0-9]{4}-[0-9]{2}-[0-9]{2})-'
    r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*'
    r'(?:-v[0-9]+\.[0-9]+(?:\.[0-9]+)?)?'
    r'\.[a-z][a-z0-9]*'
)
paths = subprocess.check_output(['git', 'ls-files', '-co', '--exclude-standard', '-z', '--', 'docs/'])
invalid = []
for path in filter(None, paths.decode().split('\0')):
    match = pattern.fullmatch(Path(path).name)
    if match:
        try:
            date.fromisoformat(match[1])
            continue
        except ValueError:
            pass
    invalid.append(path)
if invalid:
    raise SystemExit("Invalid docs filename(s), see CONTRIBUTING.md:\n" + "\n".join(invalid))
PY
then pass "docs filenames follow the naming convention"
else fail "docs filenames must follow the naming convention"
fi

# 5. Templates: both languages, same file names, nothing stray at the root,
# and the shapes other parts of the bundle depend on.
check_adapter() {
  python3 - "$1" "${LIFECYCLE_SKILLS[@]}" <<'PY'
import pathlib, re, sys
lines = pathlib.Path(sys.argv[1]).read_text().splitlines()
begin, end = "<!-- SSOT-CONTEXT:BEGIN -->", "<!-- SSOT-CONTEXT:END -->"
if lines.count(begin) != 1 or lines.count(end) != 1 or lines.index(begin) >= lines.index(end):
    sys.exit("instruction block needs exactly one ordered marker pair")
block = "\n".join(lines[lines.index(begin) + 1:lines.index(end)])
missing = [skill for skill in sys.argv[2:] if not re.search(r"\$" + re.escape(skill) + r"(?![\w-])", block)]
if missing:
    sys.exit("instruction block is missing routes: " + ", ".join(missing))
PY
}
adapter_probe="$PROBE_DIR/adapter.md"
{
  printf '<!-- SSOT-CONTEXT:BEGIN -->\n'
  printf '$%s\n' "${LIFECYCLE_SKILLS[@]}"
  printf '<!-- SSOT-CONTEXT:END -->\n'
} > "$adapter_probe"
check_adapter "$adapter_probe" >/dev/null 2>&1 && pass "adapter check accepts managed lifecycle routes" || fail "adapter check rejected valid routes"
sed '/SSOT-CONTEXT:END/d' "$adapter_probe" > "$PROBE_DIR/missing-marker.md"
check_adapter "$PROBE_DIR/missing-marker.md" >/dev/null 2>&1 && fail "adapter check accepted missing marker" || pass "adapter check rejects missing marker"
sed -e 's/SSOT-CONTEXT:BEGIN/SSOT-CONTEXT:TEMP/' -e 's/SSOT-CONTEXT:END/SSOT-CONTEXT:BEGIN/' -e 's/SSOT-CONTEXT:TEMP/SSOT-CONTEXT:END/' "$adapter_probe" > "$PROBE_DIR/reversed.md"
check_adapter "$PROBE_DIR/reversed.md" >/dev/null 2>&1 && fail "adapter check accepted reversed markers" || pass "adapter check rejects reversed markers"
{
  printf '<!-- SSOT-CONTEXT:BEGIN -->\n<!-- SSOT-CONTEXT:END -->\n'
  printf '$%s\n' "${LIFECYCLE_SKILLS[@]}"
} > "$PROBE_DIR/outside-routes.md"
check_adapter "$PROBE_DIR/outside-routes.md" >/dev/null 2>&1 && fail "adapter check accepted routes outside block" || pass "adapter check rejects routes outside block"
if [[ -d "$TEMPLATES/en" && -d "$TEMPLATES/zh" ]]; then
  if diff <(cd "$TEMPLATES/en" && find . -type f | sort) <(cd "$TEMPLATES/zh" && find . -type f | sort) >/dev/null; then
    pass "templates en/zh file parity"
  else
    fail "templates en/ and zh/ have different files"
  fi
  STRAY="$(find "$TEMPLATES" -maxdepth 1 -type f | head -1)"
  [[ -z "$STRAY" ]] && pass "no stray templates at the root" || fail "stray template at the root: $STRAY"
  for lang in en zh; do
    for spec in ssot-readme.md:4 context-readme.md:5; do
      readme="$TEMPLATES/$lang/${spec%:*}"
      if head -5 "$readme" | grep -q "^ssot_format: ${spec#*:}$" && head -5 "$readme" | grep -q '^language: '; then
        pass "$lang: ${spec%:*} carries format ${spec#*:} and language"
      else
        fail "$lang: ${spec%:*} lacks format ${spec#*:} or language"
      fi
    done
    for name in adapter-thin.md context-adapter.md; do
      if check_adapter "$TEMPLATES/$lang/$name"; then
        pass "$lang: $name has ordered markers and managed lifecycle routes"
      else
        fail "$lang: $name has invalid markers or lifecycle routes"
      fi
    done
  done
else
  fail "templates en/ and zh/ must both exist"
fi

# 6. Protocol text read by agents stays in English (inline code may quote
# headings or values in other languages).
CN_FILES=()
while IFS= read -r f; do
  if sed 's/`[^`]*`//g' "$f" | python3 -c "import sys,re; sys.exit(0 if re.search(r'[一-龥]', sys.stdin.read()) else 1)"; then
    CN_FILES+=("${f#"$PROJECT_ROOT"/}")
  fi
done < <(find "$SKILLS" -type f \( -name SKILL.md -o -path '*/references/*.md' \))
[[ ${#CN_FILES[@]} -eq 0 ]] && pass "SKILL.md and references are English" || fail "Chinese prose in: ${CN_FILES[*]}"

# 7. Every Markdown fence closes.
FENCE_FAILS=()
while IFS= read -r -d '' f; do
  line="$(awk '/^```/{ if(!o){o=1;s=FNR} else {o=0} } END{ if(o) print s }' "$PROJECT_ROOT/$f")"
  [[ -n "$line" ]] && FENCE_FAILS+=("$f:$line")
done < <(git -C "$PROJECT_ROOT" ls-files -co --exclude-standard -z -- '*.md')
[[ ${#FENCE_FAILS[@]} -eq 0 ]] && pass "all Markdown fences close" || fail "unclosed fences: ${FENCE_FAILS[*]}"

# 8. Public hygiene: no local-machine paths, consumer-project names, or real
# commit SHAs in shipped files and tests.
HOME_PATH_PATTERN="$(printf '/%s/[^\\\\`[:space:]]+' 'home')"
USERS_PATH_PATTERN="$(printf '/%s/[^\\\\`[:space:]]+' 'Users')"
ORIGIN_NAME="$(printf 'sisy%s' 'phus')"
COMMIT_SHA_PATTERN='(^|[^0-9a-f])[0-9a-f]{40}([^0-9a-f]|$)'
HYGIENE_PATTERN="(${HOME_PATH_PATTERN}|${USERS_PATH_PATTERN}|${ORIGIN_NAME}|${COMMIT_SHA_PATTERN})"
JSON_HYGIENE_PATTERN="(${HOME_PATH_PATTERN}|${USERS_PATH_PATTERN}|${ORIGIN_NAME})"
COMMIT_SHA_40="$(printf '%040d' 0)"
COMMIT_SHA_64="$(printf '%064d' 0)"
COMMIT_SHA_TEST_ERRORS=0
for sample in "$COMMIT_SHA_40" "commit=$COMMIT_SHA_40."; do
  if ! printf '%s\n' "$sample" | grep -qE "$COMMIT_SHA_PATTERN"; then
    COMMIT_SHA_TEST_ERRORS=$((COMMIT_SHA_TEST_ERRORS + 1))
  fi
done
for sample in "$COMMIT_SHA_64" "sha256=$COMMIT_SHA_64."; do
  if printf '%s\n' "$sample" | grep -qE "$COMMIT_SHA_PATTERN"; then
    COMMIT_SHA_TEST_ERRORS=$((COMMIT_SHA_TEST_ERRORS + 1))
  fi
done
[[ "$COMMIT_SHA_TEST_ERRORS" -eq 0 ]] && pass "hygiene rejects complete 40-hex tokens and permits SHA-256, bare or in text" || fail "commit SHA hygiene calibration"
printf '{"archive": "/%s/probe/x"}\n' 'home' > "$PROBE_DIR/leak.json"
printf '{"commit": "%s", "archive": "<local-home>/x"}\n' "$COMMIT_SHA_40" > "$PROBE_DIR/clean.json"
if grep -qE "$JSON_HYGIENE_PATTERN" "$PROBE_DIR/leak.json" && ! grep -qE "$JSON_HYGIENE_PATTERN" "$PROBE_DIR/clean.json"; then
  pass "JSON hygiene rejects local-machine paths while permitting 40-hex commit IDs"
else
  fail "JSON hygiene calibration"
fi
HYGIENE_ERRORS=()
while IFS= read -r -d '' f; do
  if grep -qE "$HYGIENE_PATTERN" "$PROJECT_ROOT/$f"; then
    # Report the location and reason without echoing private content.
    hit="$(grep -anEm1 "$HYGIENE_PATTERN" "$PROJECT_ROOT/$f")"
    content="${hit#*:}"
    if [[ "$content" =~ $COMMIT_SHA_PATTERN ]]; then
      reason="full commit ID; abbreviate public commit links"
    elif [[ "$content" == *"$ORIGIN_NAME"* ]]; then
      reason="consumer project name"
    else
      reason="local machine path"
    fi
    HYGIENE_ERRORS+=("$f:${hit%%:*} ($reason)")
  fi
done < <(git -C "$PROJECT_ROOT" ls-files -co --exclude-standard -z -- '*.md' '*.sh' '*.py' '*.yaml' '*.yml' '*.mjs' ':!:CHANGELOG.md')
while IFS= read -r -d '' f; do
  if grep -qE "$JSON_HYGIENE_PATTERN" "$PROJECT_ROOT/$f"; then
    # Report the location and reason without echoing private content.
    hit="$(grep -anEm1 "$JSON_HYGIENE_PATTERN" "$PROJECT_ROOT/$f")"
    content="${hit#*:}"
    if [[ "$content" == *"$ORIGIN_NAME"* ]]; then
      reason="consumer project name"
    else
      reason="local machine path"
    fi
    HYGIENE_ERRORS+=("$f:${hit%%:*} ($reason)")
  fi
done < <(git -C "$PROJECT_ROOT" ls-files -co --exclude-standard -z -- '*.json' ':!:research/')
[[ ${#HYGIENE_ERRORS[@]} -eq 0 ]] && pass "no local or consumer-project leakage (including tracked JSON)" || fail "hygiene leakage in: ${HYGIENE_ERRORS[*]}"

# 8b. Paragraphs are one line each. Editors wrap text; a paragraph broken
# across short lines reads as ragged text, and agents copy the shape of the
# templates and skills into consumer documents. Uses the checker's own rule.
if ! WRAPPED="$(python3 -B - "$PROJECT_ROOT" <<'PY'
import importlib.util, subprocess, sys
root = sys.argv[1]
spec = importlib.util.spec_from_file_location("check", f"{root}/skills/ssot-doctor/assets/scripts/ssot-check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)
files = subprocess.run(["git", "-C", root, "ls-files", "-co", "--exclude-standard", "-z", "*.md", ":!:research/"],
                       capture_output=True, text=True, check=True).stdout.split("\0")
for name in filter(None, files):
    with open(f"{root}/{name}", encoding="utf-8") as handle:
        lines = list(check.hard_wrapped_paragraphs(handle.read()))
    if lines:
        print(f"{name}:{lines[0]}")
PY
)"; then
  fail "could not inspect Markdown paragraphs"
elif [[ -n "$WRAPPED" ]]; then
  fail "paragraphs broken across short lines: $WRAPPED"
else
  pass "Markdown paragraphs are one line each"
fi

# 8c. No duplicate unittest method names across tracked Python test files
# (Python silently overwrites earlier same-named methods in a class).
check_duplicate_tests() {
  python3 -B - "$PROJECT_ROOT" "$@" <<'PY'
import ast
import os
import subprocess
import sys

root = sys.argv[1]
mode = sys.argv[2]
if mode == "--repo":
    base = root
    raw = subprocess.run(
        ["git", "-C", root, "ls-files", "-co", "--exclude-standard", "-z", "--", "tests/*.py"],
        capture_output=True, text=True, check=True,
    ).stdout
    paths = [os.path.join(root, rel) for rel in filter(None, raw.split("\0"))]
else:
    base = mode
    paths = sys.argv[3:]

duplicates = []
for path in paths:
    rel = os.path.relpath(path, base)
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=rel)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        seen = set()
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_"):
                if item.name in seen:
                    duplicates.append(f"{rel}:{item.lineno} ({node.name}.{item.name})")
                seen.add(item.name)

if duplicates:
    print("\n".join(duplicates))
    sys.exit(1)
PY
}
cat > "$PROBE_DIR/dup_test.py" <<'PY'
class ProbeTest:
    def test_same(self):
        pass
    def test_same(self):
        pass
PY
check_duplicate_tests "$PROBE_DIR" "$PROBE_DIR/dup_test.py" >/dev/null && fail "duplicate-test check accepted duplicate test_ methods" || pass "duplicate-test check rejects duplicate test_ methods"
if DUP_TESTS="$(check_duplicate_tests --repo)"; then
  pass "all Python test classes under tests/ have unique test_* method names"
else
  fail "duplicate test_* method(s): $DUP_TESTS"
fi

# 9. Budgets. These guard the always-loaded cost surface (skill catalog and
# managed adapter blocks), model-read protocol text, and distribution tooling
# separately; see CONTRIBUTING.md "Protocol budgets" before raising one.
words() { cat "$@" | wc -w | tr -d ' '; }
bytes() { cat "$@" | wc -c | tr -d ' '; }
budget() { # $1=label $2=value $3=limit $4=unit
  if [[ "$2" -le "$3" ]]; then pass "budget: $1 = $2 / $3 $4"; else fail "budget: $1 = $2 exceeds $3 $4"; fi
}
mapfile -t ENTRY_FILES < <(find "$SKILLS" -name SKILL.md | sort)
mapfile -t RUNTIME_FILES < <(find "$SKILLS" \( -name SKILL.md -o -path '*/references/*.md' \) -type f | sort)
mapfile -t SCRIPT_FILES < <(find "$SKILLS" -path '*/assets/scripts/*.py' -type f | sort)
HOT_RUNTIME_FILES=(
  "$SKILLS/ssot-preflight/SKILL.md"
  "$SKILLS/ssot-bootstrap/SKILL.md"
  "$SKILLS/ssot-closeout/SKILL.md"
  "$SKILLS/ssot-doctor/SKILL.md"
  "$SKILLS/ssot-audit/SKILL.md"
  "$SKILLS/ssot-skill/SKILL.md"
  "$SKILLS/ssot-preflight/references/memory-model.md"
  "$SKILLS/ssot-preflight/references/memory-layout.md"
  "$SKILLS/ssot-preflight/references/writing-memory.md"
  "$SKILLS/ssot-preflight/references/protection-departure.md"
  "$SKILLS/ssot-closeout/references/decision-capture.md"
  "$SKILLS/ssot-closeout/references/batch-closeout.md"
)
COLD_RUNTIME_FILES=(
  "$SKILLS/ssot-bootstrap/references/area-mining.md"
  "$SKILLS/ssot-bootstrap/references/bootstrap.md"
  "$SKILLS/ssot-bootstrap/references/migration.md"
  "$SKILLS/ssot-bootstrap/references/mining.md"
  "$SKILLS/ssot-doctor/references/conversation-catchup.md"
  "$SKILLS/ssot-doctor/references/source-integration.md"
  "$SKILLS/ssot-doctor/references/structural-review.md"
  "$SKILLS/ssot-preflight/references/context-spaces.md"
  "$SKILLS/ssot-preflight/references/context-tiering.md"
  "$SKILLS/ssot-preflight/references/source-retention.md"
)
if diff <(printf '%s\n' "${RUNTIME_FILES[@]}" | sort) <(printf '%s\n' "${HOT_RUNTIME_FILES[@]}" "${COLD_RUNTIME_FILES[@]}" | sort) >/dev/null; then
  pass "hot/cold runtime file partition covers every SKILL.md and reference"
else
  fail "hot/cold runtime file partition is out of sync with skills/"
fi
budget "SKILL.md entrypoints" "$(words "${ENTRY_FILES[@]}")" 3600 words
budget "hot-path runtime protocol (SKILL.md + daily references)" "$(words "${HOT_RUNTIME_FILES[@]}")" 9200 words
budget "conditional/cold runtime branches" "$(words "${COLD_RUNTIME_FILES[@]}")" 10400 words
if CORE_CATALOG_BYTES="$(python3 -B - "$SKILLS" "${LIFECYCLE_SKILLS[@]}" <<'PY'
import pathlib, re, sys
root = pathlib.Path(sys.argv[1])
total = 0
for name in sys.argv[2:]:
    txt = (root / name / "SKILL.md").read_text(encoding="utf-8")
    m_name = re.search(r"^name:\s*(.+)$", txt, re.M)
    m_desc = re.search(r"^description:\s*(.+)$", txt, re.M)
    if not (m_name and m_desc):
        sys.exit(1)
    total += len(f"{m_name.group(1).strip()}: {m_desc.group(1).strip()}".encode("utf-8"))
print(total)
PY
)" && (( CORE_CATALOG_BYTES > 0 )); then
  budget "always-loaded core-4 skill catalog (name + description)" "$CORE_CATALOG_BYTES" 600 bytes
else
  fail "could not measure core-4 skill catalog"
fi
if CATALOG_BYTES="$(python3 -B - "$SKILLS" <<'PY'
import pathlib, re, sys
root = pathlib.Path(sys.argv[1])
total = 0
for p in sorted(root.glob("*/SKILL.md")):
    txt = p.read_text(encoding="utf-8")
    m_name = re.search(r"^name:\s*(.+)$", txt, re.M)
    m_desc = re.search(r"^description:\s*(.+)$", txt, re.M)
    if not (m_name and m_desc):
        sys.exit(1)
    total += len(f"{m_name.group(1).strip()}: {m_desc.group(1).strip()}".encode("utf-8"))
print(total)
PY
)" && (( CATALOG_BYTES > 0 )); then
  budget "always-loaded full-6 skill catalog (with legacy shims)" "$CATALOG_BYTES" 768 bytes
else
  fail "could not measure always-loaded skill catalog"
fi
for lang in en zh; do
  for tpl in adapter-thin.md context-adapter.md; do
    if BLOCK_BYTES="$(python3 -B - "$TEMPLATES/$lang/$tpl" <<'PY'
import pathlib, re, sys
txt = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
m = re.search(r"(<!-- SSOT-CONTEXT:BEGIN -->.*?<!-- SSOT-CONTEXT:END -->)", txt, re.S)
if not m:
    sys.exit(1)
print(len(m.group(1).encode("utf-8")))
PY
)" && (( BLOCK_BYTES > 0 )); then
      budget "managed block $lang/$tpl" "$BLOCK_BYTES" 1600 bytes
    else
      fail "could not measure managed block $lang/$tpl"
    fi
  done
  budget "templates/$lang" "$(bytes "$TEMPLATES/$lang"/*)" 16384 bytes
done
SCRIPT_BYTES="$(bytes "${SCRIPT_FILES[@]}")"
budget "checker" "$(bytes "$SKILLS/ssot-doctor/assets/scripts/ssot-check.py")" 65536 bytes
budget "bundle scripts" "$SCRIPT_BYTES" 98304 bytes
if TOTAL_BYTES="$(git -C "$PROJECT_ROOT" ls-files -co --exclude-standard -z -- skills | xargs -0 cat | wc -c)" && (( TOTAL_BYTES > 0 )); then
  RUNTIME_ASSET_BYTES=$((TOTAL_BYTES - SCRIPT_BYTES))
  budget "runtime assets (skills/ excluding scripts)" "$RUNTIME_ASSET_BYTES" 163840 bytes
  budget "skills/ total" "$TOTAL_BYTES" 262144 bytes
else
  fail "could not measure the runtime files in skills/"
fi

echo
echo "=== RESULT: pass=$PASS fail=$FAIL ==="
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
