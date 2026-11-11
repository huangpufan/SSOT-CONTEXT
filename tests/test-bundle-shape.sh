#!/usr/bin/env bash
# tests/test-bundle-shape.sh — bundle structure, link integrity, and budgets
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
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

# 4. Relative links in SKILL.md and references resolve (fenced examples skipped).
check_links_in() {
  local file="$1" file_dir stripped target clean resolved failed=0
  file_dir="$(dirname "$file")"
  stripped="$(awk 'BEGIN{f=0} /^```/{f=!f; next} !f' "$file" | sed 's/`[^`]*`//g')"
  while IFS= read -r target; do
    clean="${target%%#*}"; clean="${clean%%\?*}"
    [[ -z "$clean" || "$clean" =~ ^[a-z]+:// ]] && continue
    resolved="$(cd "$file_dir" 2>/dev/null && python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$clean" 2>/dev/null || true)"
    if [[ -z "$resolved" || ! -e "$resolved" ]]; then
      echo "  FAIL : link broken in ${file#"$PROJECT_ROOT"/}: $clean"
      failed=1
    fi
  done < <(printf '%s\n' "$stripped" | grep -oE '\]\([^)]+\)' | sed -E 's/^\]\(([^)]+)\)$/\1/')
  return "$failed"
}
PROBE_DIR="$(mktemp -d)"
trap 'rm -rf "$PROBE_DIR"' EXIT
printf '[missing](missing.md#x)\n' > "$PROBE_DIR/probe.md"
check_links_in "$PROBE_DIR/probe.md" >/dev/null && fail "link check accepted a missing target" || pass "link check rejects a missing target"
printf '# E\n' > "$PROBE_DIR/e.md"
printf '[e](e.md#e) [x](https://example.test/m.md)\n\n```\n[y](missing.md)\n```\n' > "$PROBE_DIR/probe.md"
check_links_in "$PROBE_DIR/probe.md" >/dev/null && pass "link check accepts valid, external, and fenced links" || fail "link check rejected valid links"
LINK_FAILS=0
while IFS= read -r f; do
  check_links_in "$f" || LINK_FAILS=$((LINK_FAILS+1))
done < <(find "$SKILLS" -type f \( -name SKILL.md -o -path '*/references/*.md' \))
[[ $LINK_FAILS -eq 0 ]] && pass "all skill and reference links resolve" || fail "$LINK_FAILS file(s) have broken links"

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
HYGIENE_PATTERN="(${HOME_PATH_PATTERN}|${USERS_PATH_PATTERN}|${ORIGIN_NAME}|[0-9a-f]{40})"
HYGIENE_FILES=()
while IFS= read -r -d '' f; do
  grep -qE "$HYGIENE_PATTERN" "$PROJECT_ROOT/$f" && HYGIENE_FILES+=("$f")
done < <(git -C "$PROJECT_ROOT" ls-files -co --exclude-standard -z -- '*.md' '*.sh' '*.py' '*.yaml' '*.yml' '*.mjs' ':!:CHANGELOG.md')
[[ ${#HYGIENE_FILES[@]} -eq 0 ]] && pass "no local or consumer-project leakage" || fail "hygiene leakage in: ${HYGIENE_FILES[*]}"

# 8b. Paragraphs are one line each. Editors wrap text; a paragraph broken
# across short lines reads as ragged text, and agents copy the shape of the
# templates and skills into consumer documents. Uses the checker's own rule.
WRAPPED="$(python3 - "$PROJECT_ROOT" <<'PY'
import importlib.util, subprocess, sys
root = sys.argv[1]
spec = importlib.util.spec_from_file_location("check", f"{root}/skills/ssot-doctor/assets/scripts/ssot-check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)
files = subprocess.run(["git", "-C", root, "ls-files", "-co", "--exclude-standard", "*.md", ":!:research/"],
                       capture_output=True, text=True, check=True).stdout.split()
for name in files:
    with open(f"{root}/{name}", encoding="utf-8") as handle:
        lines = list(check.hard_wrapped_paragraphs(handle.read()))
    if lines:
        print(f"{name}:{lines[0]}")
PY
)"
[[ -z "$WRAPPED" ]] && pass "Markdown paragraphs are one line each" || fail "paragraphs broken across short lines: $(echo $WRAPPED)"

# 9. Budgets. These are hard limits on what agents load and what this
# repository maintains; see CONTRIBUTING.md "Protocol budgets" before raising
# one. Every file an agent may read at runtime counts.
words() { cat "$@" | wc -w | tr -d ' '; }
bytes() { cat "$@" | wc -c | tr -d ' '; }
budget() { # $1=label $2=value $3=limit $4=unit
  if [[ "$2" -le "$3" ]]; then pass "budget: $1 = $2 / $3 $4"; else fail "budget: $1 = $2 exceeds $3 $4"; fi
}
mapfile -t ENTRY_FILES < <(find "$SKILLS" -name SKILL.md | sort)
mapfile -t RUNTIME_FILES < <(find "$SKILLS" \( -name SKILL.md -o -path '*/references/*.md' \) -type f | sort)
budget "SKILL.md entrypoints" "$(words "${ENTRY_FILES[@]}")" 3600 words
budget "runtime protocol (SKILL.md + references)" "$(words "${RUNTIME_FILES[@]}")" 17000 words
for lang in en zh; do
  budget "templates/$lang" "$(bytes "$TEMPLATES/$lang"/*)" 16384 bytes
done
budget "checker" "$(bytes "$SKILLS/ssot-doctor/assets/scripts/ssot-check.py")" 51200 bytes
budget "skills/ total" "$(git -C "$PROJECT_ROOT" ls-files -co --exclude-standard -z -- skills | xargs -0 cat | wc -c | tr -d ' ')" 225280 bytes

echo
echo "=== RESULT: pass=$PASS fail=$FAIL ==="
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
