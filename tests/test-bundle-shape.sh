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

# 2. Every skill has valid YAML frontmatter (name matches its directory, description >= 40 chars
# supporting single-line and multiline block scalars), a non-empty body, and valid openai.yaml
# metadata with display_name, short_description, and default_prompt naming $<skill>.
PROBE_DIR="$(mktemp -d)"
trap 'rm -rf "$PROBE_DIR"' EXIT

parse_frontmatter_field() {
  python3 -B - "$1" "$2" <<'PY'
import pathlib, re, sys

text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
target_key = sys.argv[2]
lines = text.splitlines()
if not lines or lines[0].strip() != "---":
    sys.exit(1)
end = None
for idx in range(1, len(lines)):
    if lines[idx].strip() == "---":
        end = idx
        break
if end is None:
    sys.exit(1)
fm = lines[1:end]

def unquote(val):
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
        return val[1:-1]
    return val

i = 0
while i < len(fm):
    m = re.match(r"^([A-Za-z0-9_-]+):[ \t]*(.*)$", fm[i])
    if not m:
        i += 1
        continue
    key, raw = m.group(1), m.group(2).strip()
    if raw in (">", ">-", ">+", "|", "|-", "|+"):
        block = []
        i += 1
        while i < len(fm) and (fm[i] == "" or fm[i].startswith((" ", "\t"))):
            block.append(fm[i])
            i += 1
        non_empty = [ln for ln in block if ln.strip()]
        indent = min((len(ln) - len(ln.lstrip(" \t")) for ln in non_empty), default=0)
        stripped = [ln[indent:] if len(ln) >= indent else "" for ln in block]
        while stripped and not stripped[-1].strip():
            stripped.pop()
        if raw.startswith(">"):
            val = " ".join(ln.strip() for ln in stripped if ln.strip())
        else:
            val = "\n".join(stripped)
    else:
        val = unquote(raw)
        i += 1
    if key == target_key:
        print(val)
        sys.exit(0)
sys.exit(1)
PY
}

check_openai_yaml() {
  python3 -B - "$1" "$2" <<'PY'
import pathlib, re, sys

path = pathlib.Path(sys.argv[1])
skill = sys.argv[2]
if not path.is_file():
    sys.exit(f"missing {path}")
lines = path.read_text(encoding="utf-8").splitlines()
in_interface = False
seen = {}
for lineno, raw in enumerate(lines, 1):
    stripped = raw.strip()
    if not stripped or stripped.startswith("#"):
        continue
    if not raw.startswith((" ", "\t")):
        if stripped == "interface:":
            in_interface = True
            continue
        in_interface = False
        if not re.match(r"^[A-Za-z0-9_-]+:\s*", raw):
            sys.exit(f"invalid top-level YAML at line {lineno}")
        continue
    if not in_interface:
        continue
    m = re.match(r"^[ \t]+([A-Za-z0-9_-]+):[ \t]*(.*)$", raw)
    if not m:
        sys.exit(f"invalid interface entry at line {lineno}")
    key, val = m.group(1), m.group(2).strip()
    if key in seen:
        sys.exit(f"duplicate key '{key}' at line {lineno}")
    if not val:
        sys.exit(f"empty value for '{key}' at line {lineno}")
    if val[0] in ("'", '"'):
        if len(val) < 2 or val[-1] != val[0]:
            sys.exit(f"unterminated quote for '{key}' at line {lineno}")
        val = val[1:-1].strip()
    elif val[0] in ("[", "{"):
        sys.exit(f"unsupported/malformed flow scalar for '{key}' at line {lineno}")
    if not val:
        sys.exit(f"blank value for '{key}' at line {lineno}")
    seen[key] = val

for req in ("display_name", "short_description", "default_prompt"):
    if req not in seen:
        sys.exit(f"missing required key '{req}'")
if not re.search(r"\$" + re.escape(skill) + r"(?![\w-])", seen["default_prompt"]):
    sys.exit(f"default_prompt does not reference ${skill}")
PY
}

cat > "$PROBE_DIR/folded-skill.md" <<'MD'
---
name: probe-skill
description: >-
  Read SSOT before substantive work in a repository or declared space.
  Follow bounded lookup routes.
---
# Body
MD
FOLDED_DESC="$(parse_frontmatter_field "$PROBE_DIR/folded-skill.md" description 2>/dev/null || true)"
[[ "$FOLDED_DESC" == "Read SSOT before substantive work in a repository or declared space. Follow bounded lookup routes." ]] &&
  pass "frontmatter parser folds multiline YAML description scalars" ||
  fail "frontmatter parser failed on multiline YAML description ('$FOLDED_DESC')"
cat > "$PROBE_DIR/body-only.md" <<'MD'
---
name: probe-skill
---
description: This is in the body and must never count as frontmatter description.
MD
parse_frontmatter_field "$PROBE_DIR/body-only.md" description >/dev/null 2>&1 &&
  fail "frontmatter parser accepted description from Markdown body" ||
  pass "frontmatter parser ignores keys outside YAML frontmatter"
cat > "$PROBE_DIR/bad-openai.yaml" <<'YAML'
interface:
  display_name: [broken: yaml: $probe-skill
YAML
check_openai_yaml "$PROBE_DIR/bad-openai.yaml" probe-skill >/dev/null 2>&1 &&
  fail "openai.yaml check accepted malformed YAML missing required keys" ||
  pass "openai.yaml check rejects malformed YAML and missing keys"
cat > "$PROBE_DIR/wrong-ref.yaml" <<'YAML'
interface:
  display_name: "Probe $probe-skill"
  short_description: "Short summary"
  default_prompt: "Missing the skill token here."
YAML
check_openai_yaml "$PROBE_DIR/wrong-ref.yaml" probe-skill >/dev/null 2>&1 &&
  fail "openai.yaml check accepted default_prompt without \$skill" ||
  pass "openai.yaml check requires \$skill inside default_prompt"

for skill in "${BUNDLE_SKILLS[@]}"; do
  file="$SKILLS/$skill/SKILL.md"
  if [[ ! -f "$file" ]]; then fail "$skill: SKILL.md missing"; continue; fi
  name="$(parse_frontmatter_field "$file" name 2>/dev/null || true)"
  [[ "$name" == "$skill" ]] && pass "$skill: name matches" || fail "$skill: name '$name' does not match directory"
  desc="$(parse_frontmatter_field "$file" description 2>/dev/null || true)"
  [[ ${#desc} -ge 40 ]] && pass "$skill: description present" || fail "$skill: description missing or too short (${#desc} chars)"
  body="$(awk '/^---$/{n++; next} n>=2' "$file" | tr -d '[:space:]')"
  [[ -n "$body" ]] && pass "$skill: body present" || fail "$skill: body empty"
  yaml="$SKILLS/$skill/agents/openai.yaml"
  if check_openai_yaml "$yaml" "$skill" >/dev/null 2>&1; then
    pass "$skill: openai.yaml valid and default_prompt names \$$skill"
  else
    fail "$skill: openai.yaml invalid ($(check_openai_yaml "$yaml" "$skill" 2>&1))"
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
# Skill links must also hold after installation (stay inside skills/, avoid
# absolute paths, avoid unflattened templates/{en,zh}/, and keep core-4 skills
# free of links to opt-in legacy shims).
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

base_real = os.path.realpath(base)
skills_real = os.path.realpath(os.path.join(base, "skills"))
core_skills = {"ssot-preflight", "ssot-bootstrap", "ssot-closeout", "ssot-doctor"}
shim_skills = {"ssot-audit", "ssot-skill"}

def inside(parent, child):
    try:
        return os.path.commonpath([parent, child]) == parent
    except ValueError:
        return False

failed = 0
for path in paths:
    rel = os.path.relpath(path, base)
    path_real = os.path.realpath(path)
    in_skills = inside(skills_real, path_real)
    src_skill = os.path.relpath(path_real, skills_real).split(os.sep)[0] if in_skills else None
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    for number, raw_target in check.link_targets(text):
        target = raw_target.strip()
        if not target or check.SCHEME_RE.match(target):
            continue
        if unquote(target).startswith("/"):
            print(f"  FAIL : absolute path link in {rel}:{number}: {target}")
            failed += 1
            continue
        resolved, fragment = check.resolve(path, target)
        res_real = os.path.realpath(resolved)
        if not inside(base_real, res_real):
            print(f"  FAIL : link escapes repository root in {rel}:{number}: {target}")
            failed += 1
            continue
        if in_skills:
            if not inside(skills_real, res_real):
                print(f"  FAIL : skill link escapes skills/ bundle in {rel}:{number}: {target}")
                failed += 1
                continue
            rel_skills = os.path.relpath(res_real, skills_real).replace(os.sep, "/")
            if (rel_skills in ("ssot-bootstrap/assets/templates/en", "ssot-bootstrap/assets/templates/zh")
                    or rel_skills.startswith("ssot-bootstrap/assets/templates/en/")
                    or rel_skills.startswith("ssot-bootstrap/assets/templates/zh/")):
                print(f"  FAIL : skill link targets unflattened template dir in {rel}:{number}: {target}")
                failed += 1
                continue
            dst_skill = rel_skills.split("/")[0]
            if src_skill in core_skills and dst_skill in shim_skills:
                print(f"  FAIL : core skill links to opt-in legacy shim in {rel}:{number}: {target}")
                failed += 1
                continue
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
mkdir -p "$PROBE_DIR/skills/ssot-preflight" "$PROBE_DIR/skills/ssot-audit" "$PROBE_DIR/skills/ssot-bootstrap/assets/templates/en"
printf '# E\n' > "$PROBE_DIR/e.md"
printf '# Target\n' > "$PROBE_DIR/skills/ssot-preflight/target.md"
printf '# Audit\n' > "$PROBE_DIR/skills/ssot-audit/SKILL.md"
printf '# Adapter\n' > "$PROBE_DIR/skills/ssot-bootstrap/assets/templates/en/adapter-thin.md"
printf '[missing](missing.md#x)\n' > "$PROBE_DIR/probe-doc.md"
check_links "$PROBE_DIR" "$PROBE_DIR/probe-doc.md" >/dev/null && fail "link check accepted a broken relative link in a top-level doc" || pass "link check rejects a broken relative link in a top-level doc"
printf '[bad](target.md#bad-anchor)\n' > "$PROBE_DIR/skills/ssot-preflight/SKILL.md"
check_links "$PROBE_DIR" "$PROBE_DIR/skills/ssot-preflight/SKILL.md" >/dev/null && fail "link check accepted a broken heading anchor in a skill file" || pass "link check rejects a broken heading anchor in a skill file"
printf '[escape](../../e.md#e)\n' > "$PROBE_DIR/skills/ssot-preflight/escape.md"
check_links "$PROBE_DIR" "$PROBE_DIR/skills/ssot-preflight/escape.md" >/dev/null && fail "link check accepted a skill link escaping skills/" || pass "link check rejects a skill link escaping skills/"
printf '[abs](/etc/hosts)\n' > "$PROBE_DIR/skills/ssot-preflight/abs.md"
check_links "$PROBE_DIR" "$PROBE_DIR/skills/ssot-preflight/abs.md" >/dev/null && fail "link check accepted an absolute POSIX path link" || pass "link check rejects an absolute POSIX path link"
printf '[shim](../ssot-audit/SKILL.md)\n' > "$PROBE_DIR/skills/ssot-preflight/shim.md"
check_links "$PROBE_DIR" "$PROBE_DIR/skills/ssot-preflight/shim.md" >/dev/null && fail "link check accepted a core-4 skill linking to a legacy shim" || pass "link check rejects a core-4 skill linking to a legacy shim"
printf '[tpl](../ssot-bootstrap/assets/templates/en/adapter-thin.md)\n' > "$PROBE_DIR/skills/ssot-preflight/unflat.md"
check_links "$PROBE_DIR" "$PROBE_DIR/skills/ssot-preflight/unflat.md" >/dev/null && fail "link check accepted an unflattened templates/<lang>/ link" || pass "link check rejects an unflattened templates/<lang>/ link"
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

  # Structural, frontmatter-key, skill-token, & placeholder parity across en/
  # and zh/ templates, plus negative probes.
  check_template_parity() {
    python3 -B - "$1" "$2" <<'PY'
import pathlib, re, sys

en_dir, zh_dir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
sep_re = re.compile(r"^\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?$")

def strip_non_prose(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"^```.*?^```", "", text, flags=re.S | re.M)
    return text

def frontmatter_keys(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    keys = []
    for line in lines[1:]:
        if line.strip() == "---":
            return keys
        m = re.match(r"^([A-Za-z_][\w-]*):[ \t]*", line)
        if m:
            keys.append(m.group(1))
    return []

def skill_tokens(text):
    return sorted(set(re.findall(r"\$ssot-[a-z0-9-]+", text)))

def structure(path):
    raw = path.read_text(encoding="utf-8")
    clean = strip_non_prose(raw)
    headings = [len(m.group(1)) for m in re.finditer(r"^(#{1,6})\s+\S", clean, re.M)]
    tables = []
    for line in clean.splitlines():
        s = line.strip()
        if s.startswith("|") and sep_re.match(s):
            cells = [c.strip() for c in s.strip("|").split("|")]
            tables.append(len(cells))
    return headings, tables, frontmatter_keys(raw), skill_tokens(raw)

def managed_entry_count(path):
    text = path.read_text(encoding="utf-8")
    m = re.search(r"<!-- SSOT-CONTEXT:BEGIN -->(.*?)<!-- SSOT-CONTEXT:END -->", text, re.S)
    if not m:
        return -1
    return len(re.findall(r"\bENTRY\b", m.group(1)))

errors = []
en_files = sorted(p.relative_to(en_dir) for p in en_dir.rglob("*") if p.is_file())
zh_files = sorted(p.relative_to(zh_dir) for p in zh_dir.rglob("*") if p.is_file())
if en_files != zh_files:
    errors.append("en/ and zh/ file sets differ")
for rel in en_files:
    if rel.suffix.lower() != ".md":
        continue
    en_h, en_t, en_fm, en_sk = structure(en_dir / rel)
    zh_h, zh_t, zh_fm, zh_sk = structure(zh_dir / rel)
    if en_h != zh_h:
        errors.append(f"{rel}: heading levels en={en_h} != zh={zh_h}")
    if en_t != zh_t:
        errors.append(f"{rel}: table column counts en={en_t} != zh={zh_t}")
    if en_fm != zh_fm:
        errors.append(f"{rel}: frontmatter keys en={en_fm} != zh={zh_fm}")
    if en_sk != zh_sk:
        errors.append(f"{rel}: $ssot-* tokens en={en_sk} != zh={zh_sk}")
if (en_dir / "context-adapter.md").is_file() and (zh_dir / "context-adapter.md").is_file():
    en_e = managed_entry_count(en_dir / "context-adapter.md")
    zh_e = managed_entry_count(zh_dir / "context-adapter.md")
    if en_e < 1 or en_e != zh_e:
        errors.append(f"context-adapter.md managed ENTRY count en={en_e}, zh={zh_e}")
if errors:
    sys.exit("; ".join(errors))
PY
  }
  mkdir -p "$PROBE_DIR/tpl-bad/en" "$PROBE_DIR/tpl-bad/zh"
  printf '# Title\n\n## A\n\n| A | B |\n|---|---|\n' > "$PROBE_DIR/tpl-bad/en/doc.md"
  printf '# 标题\n\n## A\n\n## Extra\n\n| A | B |\n|---|---|\n' > "$PROBE_DIR/tpl-bad/zh/doc.md"
  check_template_parity "$PROBE_DIR/tpl-bad/en" "$PROBE_DIR/tpl-bad/zh" >/dev/null 2>&1 &&
    fail "template parity accepted mismatched en/zh headings" ||
    pass "template parity rejects mismatched en/zh headings"
  printf '# 标题\n\n## A\n\n| A | B | C |\n|---|---|---|\n' > "$PROBE_DIR/tpl-bad/zh/doc.md"
  check_template_parity "$PROBE_DIR/tpl-bad/en" "$PROBE_DIR/tpl-bad/zh" >/dev/null 2>&1 &&
    fail "template parity accepted mismatched en/zh table columns" ||
    pass "template parity rejects mismatched en/zh table columns"
  printf -- '---\nssot_format: 4\nlanguage: en\n---\n# Title\n' > "$PROBE_DIR/tpl-bad/en/doc.md"
  printf -- '---\nssot_format: 4\n---\n# 标题\n' > "$PROBE_DIR/tpl-bad/zh/doc.md"
  check_template_parity "$PROBE_DIR/tpl-bad/en" "$PROBE_DIR/tpl-bad/zh" >/dev/null 2>&1 &&
    fail "template parity accepted mismatched en/zh frontmatter keys" ||
    pass "template parity rejects mismatched en/zh frontmatter keys"
  printf '# Title\n\nUse `$ssot-preflight` and `$ssot-closeout`.\n' > "$PROBE_DIR/tpl-bad/en/doc.md"
  printf '# 标题\n\n只用 `$ssot-preflight`。\n' > "$PROBE_DIR/tpl-bad/zh/doc.md"
  check_template_parity "$PROBE_DIR/tpl-bad/en" "$PROBE_DIR/tpl-bad/zh" >/dev/null 2>&1 &&
    fail "template parity accepted mismatched en/zh \$ssot-* tokens" ||
    pass "template parity rejects mismatched en/zh \$ssot-* tokens"
  rm -f "$PROBE_DIR/tpl-bad/en/doc.md" "$PROBE_DIR/tpl-bad/zh/doc.md"
  printf '<!-- SSOT-CONTEXT:BEGIN -->\nENTRY defines ENTRY\n<!-- SSOT-CONTEXT:END -->\n' > "$PROBE_DIR/tpl-bad/en/context-adapter.md"
  printf '<!-- SSOT-CONTEXT:BEGIN -->\nENTRY defines space\n<!-- SSOT-CONTEXT:END -->\n' > "$PROBE_DIR/tpl-bad/zh/context-adapter.md"
  check_template_parity "$PROBE_DIR/tpl-bad/en" "$PROBE_DIR/tpl-bad/zh" >/dev/null 2>&1 &&
    fail "template parity accepted mismatched ENTRY placeholder counts" ||
    pass "template parity rejects mismatched ENTRY placeholder counts"
  if PARITY_ERR="$(check_template_parity "$TEMPLATES/en" "$TEMPLATES/zh" 2>&1)"; then
    pass "templates en/zh match in heading outlines, table columns, frontmatter keys, \$ssot-* tokens, and ENTRY count"
  else
    fail "templates en/zh structural parity failed: $PARITY_ERR"
  fi

  # 5b. Materialized template & flattened-bundle smoke checks:
  # (a) Shipped en/ and zh/ Format-4 (with decisions/, research/, BOOTSTRAP.md,
  #     and stripped reviewed_through placeholder) and Format-5 skeletons pass
  #     ssot-check.py with 0 errors AND 0 warnings.
  # (b) Flattened core-4 skill bundles (matching install.sh --quickstart) have 0 broken links.
  CHECKER_SCRIPT="$SKILLS/ssot-doctor/assets/scripts/ssot-check.py"
  check_smoke_clean() {
    local out rc
    out="$(python3 -B "$CHECKER_SCRIPT" "$1" 2>&1)"
    rc=$?
    if [[ $rc -ne 0 ]] || ! grep -q 'PASS - 0 error(s), 0 warning(s)' <<< "$out"; then
      printf '%s\n' "$out"
      return 1
    fi
  }
  for lang in en zh; do
    f4_dir="$PROBE_DIR/smoke-$lang/f4/SSOT"
    mkdir -p "$f4_dir/decisions" "$f4_dir/research"
    for tf in "$TEMPLATES/$lang"/*.md; do
      base="$(basename "$tf")"
      case "$base" in
        ssot-readme.md) sed '/^reviewed_through:/d' "$tf" > "$f4_dir/README.md" ;;
        decision.md) cp "$tf" "$f4_dir/decisions/0001-example.md" ;;
        research.md) cp "$tf" "$f4_dir/research/example.md" ;;
        bootstrap-progress.md) cp "$tf" "$f4_dir/BOOTSTRAP.md" ;;
        adapter-thin.md|context-adapter.md|context-readme.md) ;;
        *) cp "$tf" "$f4_dir/$base" ;;
      esac
    done
    if f4_out="$(check_smoke_clean "$f4_dir")"; then
      pass "$lang: materialized Format-4 template skeleton passes ssot-check.py (0 errors, 0 warnings)"
    else
      fail "$lang: materialized Format-4 template skeleton failed ssot-check.py: $f4_out"
    fi
    f5_dir="$PROBE_DIR/smoke-$lang/f5"
    mkdir -p "$f5_dir"
    cp "$TEMPLATES/$lang/context-readme.md" "$f5_dir/CONTEXT.md"
    if f5_out="$(check_smoke_clean "$f5_dir/CONTEXT.md")"; then
      pass "$lang: materialized Format-5 context-readme.md passes ssot-check.py (0 errors, 0 warnings)"
    else
      fail "$lang: materialized Format-5 context-readme.md failed ssot-check.py: $f5_out"
    fi

    flat_root="$PROBE_DIR/flat-$lang"
    mkdir -p "$flat_root/skills"
    for skill in "${LIFECYCLE_SKILLS[@]}"; do
      cp -R "$SKILLS/$skill" "$flat_root/skills/$skill"
    done
    flat_tpl="$flat_root/skills/ssot-bootstrap/assets/templates"
    cp -R "$flat_tpl/$lang"/. "$flat_tpl/"
    rm -rf "$flat_tpl/en" "$flat_tpl/zh"
    mapfile -t FLAT_DOCS < <(find "$flat_root/skills" -type f -name '*.md' ! -path '*/assets/templates/*' | sort)
    if check_links "$flat_root" "${FLAT_DOCS[@]}"; then
      pass "$lang: flattened core-4 installed bundle has valid relative links and anchors"
    else
      fail "$lang: flattened core-4 installed bundle has broken links"
    fi
  done
  cp "$PROBE_DIR/smoke-en/f5/CONTEXT.md" "$PROBE_DIR/smoke-en/f5/WARN.md"
  printf '\nLine one of a short wrapped paragraph.\nLine two of the same wrapped paragraph.\nLine three of the same wrapped paragraph.\n' >> "$PROBE_DIR/smoke-en/f5/WARN.md"
  check_smoke_clean "$PROBE_DIR/smoke-en/f5/WARN.md" >/dev/null 2>&1 &&
    fail "template smoke check accepted a warning in materialized template" ||
    pass "template smoke check rejects warnings in materialized template"
  printf '\n- [Missing](missing.md)\n' >> "$PROBE_DIR/smoke-en/f5/CONTEXT.md"
  check_smoke_clean "$PROBE_DIR/smoke-en/f5/CONTEXT.md" >/dev/null 2>&1 &&
    fail "template smoke check accepted a broken link in materialized template" ||
    pass "template smoke check rejects a broken link in materialized template"
else
  fail "templates en/ and zh/ must both exist"
fi

# 5c. Cross-file mechanical sync gates (CHANGELOG version heading, installer vs
# checker instruction-file tuple, and README.md vs README.zh.md structural/link parity).
check_changelog_version() {
  python3 -B - "$1" "$2" <<'PY'
import pathlib, re, sys
text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
version = sys.argv[2].strip()
if not re.search(r"^## \[" + re.escape(version) + r"\](?:[ \t]|$)", text, re.M):
    sys.exit(f"missing '## [{version}]' heading in {sys.argv[1]}")
PY
}
printf '# Changelog\n\n## [5.19] - 2026-11-25\n' > "$PROBE_DIR/CHANGELOG-missing.md"
check_changelog_version "$PROBE_DIR/CHANGELOG-missing.md" "$VERSION_CONTENT" >/dev/null 2>&1 &&
  fail "changelog check accepted missing VERSION heading" ||
  pass "changelog check rejects missing VERSION heading"
if CHANGELOG_ERR="$(check_changelog_version "$PROJECT_ROOT/CHANGELOG.md" "$VERSION_CONTENT" 2>&1)"; then
  pass "CHANGELOG.md contains release heading for VERSION ($VERSION_CONTENT)"
else
  fail "CHANGELOG.md version check failed: $CHANGELOG_ERR"
fi

check_instruction_files_sync() {
  python3 -B - "$1" "$2" <<'PY'
import ast, pathlib, re, sys
inst_text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
chk_text = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
m = re.search(r"BLOCK_INSTRUCTION_FILES=\((.*?)\)", inst_text, re.S)
if not m:
    sys.exit("BLOCK_INSTRUCTION_FILES not found in install.sh")
inst_files = re.findall(r'"([^"]+)"', m.group(1))
tree = ast.parse(chk_text, filename=sys.argv[2])
chk_files = None
for node in tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "INSTRUCTION_FILES":
                chk_files = list(ast.literal_eval(node.value))
if not inst_files or not chk_files or inst_files != chk_files:
    sys.exit(f"install.sh={inst_files} != ssot-check.py={chk_files}")
PY
}
printf 'BLOCK_INSTRUCTION_FILES=(\n  "AGENTS.md"\n  "CLAUDE.md"\n)\n' > "$PROBE_DIR/install-drift.sh"
printf 'INSTRUCTION_FILES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md")\n' > "$PROBE_DIR/checker-drift.py"
check_instruction_files_sync "$PROBE_DIR/install-drift.sh" "$PROBE_DIR/checker-drift.py" >/dev/null 2>&1 &&
  fail "instruction-file sync accepted mismatched install.sh and ssot-check.py lists" ||
  pass "instruction-file sync rejects mismatched install.sh and ssot-check.py lists"
if SYNC_ERR="$(check_instruction_files_sync "$PROJECT_ROOT/install.sh" "$SKILLS/ssot-doctor/assets/scripts/ssot-check.py" 2>&1)"; then
  pass "install.sh BLOCK_INSTRUCTION_FILES matches ssot-check.py INSTRUCTION_FILES"
else
  fail "instruction-file sync failed: $SYNC_ERR"
fi

check_readme_parity() {
  python3 -B - "$PROJECT_ROOT" "$1" "$2" <<'PY'
import importlib.util, pathlib, sys
root, en_path, zh_path = sys.argv[1:4]
spec = importlib.util.spec_from_file_location("check", f"{root}/skills/ssot-doctor/assets/scripts/ssot-check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

def summarize(path):
    text = pathlib.Path(path).read_text(encoding="utf-8")
    levels = [lvl for _, lvl, _ in check.headings(text)]
    links = [t.strip() for _, t in check.link_targets(text) if t.strip() and not t.strip().startswith("#")]
    return levels, links

en_h, en_l = summarize(en_path)
zh_h, zh_l = summarize(zh_path)
errors = []
if en_h != zh_h:
    errors.append(f"heading levels en={en_h} != zh={zh_h}")
if en_l != zh_l:
    errors.append(f"non-local links differ (en={len(en_l)}, zh={len(zh_l)})")
if errors:
    sys.exit("; ".join(errors))
PY
}
printf '# Title\n\n## Intro\n\n[Install](./INSTALL.md)\n' > "$PROBE_DIR/README-en.md"
printf '# 标题\n\n## 简介\n\n### 多余\n\n[安装](./INSTALL.md)\n' > "$PROBE_DIR/README-zh-h.md"
check_readme_parity "$PROBE_DIR/README-en.md" "$PROBE_DIR/README-zh-h.md" >/dev/null 2>&1 &&
  fail "README parity accepted mismatched heading outline" ||
  pass "README parity rejects mismatched heading outline"
printf '# 标题\n\n## 简介\n\n无链接。\n' > "$PROBE_DIR/README-zh-l.md"
check_readme_parity "$PROBE_DIR/README-en.md" "$PROBE_DIR/README-zh-l.md" >/dev/null 2>&1 &&
  fail "README parity accepted missing non-local link" ||
  pass "README parity rejects missing non-local link"
if README_ERR="$(check_readme_parity "$PROJECT_ROOT/README.md" "$PROJECT_ROOT/README.zh.md" 2>&1)"; then
  pass "README.md and README.zh.md match in heading outline and shared non-local links"
else
  fail "README.md / README.zh.md parity failed: $README_ERR"
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

# 7. Every Markdown fence closes (CommonMark §4.5: backtick & tilde fences,
# up to 3-space indentation, backtick-free info strings, length-matched closers).
check_fences() {
  python3 -B - "$PROJECT_ROOT" "$@" <<'PY'
import os, re, subprocess, sys

root = sys.argv[1]
mode = sys.argv[2]
if mode == "--repo":
    raw = subprocess.run(
        ["git", "-C", root, "ls-files", "-co", "--exclude-standard", "-z", "--", "*.md"],
        capture_output=True, text=True, check=True,
    ).stdout
    paths = [(rel, os.path.join(root, rel)) for rel in filter(None, raw.split("\0"))]
else:
    paths = [(os.path.basename(p), p) for p in sys.argv[2:]]

fence_re = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
fails = []
for label, path in paths:
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    open_char = None
    open_len = 0
    open_line = 0
    for lineno, line in enumerate(lines, 1):
        m = fence_re.match(line)
        if open_char is None:
            if m:
                marker, info = m.group(1), m.group(2)
                if marker[0] == "`" and "`" in info:
                    continue  # CommonMark §4.5: inline code span, not a fence opener
                open_char, open_len, open_line = marker[0], len(marker), lineno
        else:
            if m and m.group(1)[0] == open_char and len(m.group(1)) >= open_len and not m.group(2).strip():
                open_char, open_len, open_line = None, 0, 0
    if open_char is not None:
        fails.append(f"{label}:{open_line}")

if fails:
    print(" ".join(fails))
    sys.exit(1)
PY
}
printf '````markdown\n  ```py\n  x = 1\n  ```\n````\n\n~~~text\nok\n~~~\n\n```inline``` and prose\n' > "$PROBE_DIR/fences-ok.md"
check_fences "$PROBE_DIR/fences-ok.md" >/dev/null 2>&1 &&
  pass "fence check accepts nested backticks, tilde fences, indented fences, and line-start inline code" ||
  fail "fence check rejected valid CommonMark fences or line-start inline code"
printf '~~~\nunclosed tilde\n' > "$PROBE_DIR/fences-bad-tilde.md"
check_fences "$PROBE_DIR/fences-bad-tilde.md" >/dev/null 2>&1 &&
  fail "fence check accepted unclosed tilde fence" ||
  pass "fence check rejects unclosed tilde fence"
printf '  ```python\n  x = 1\n' > "$PROBE_DIR/fences-bad-indent.md"
check_fences "$PROBE_DIR/fences-bad-indent.md" >/dev/null 2>&1 &&
  fail "fence check accepted unclosed indented fence" ||
  pass "fence check rejects unclosed indented fence"
if FENCE_ERR="$(check_fences --repo)"; then
  pass "all Markdown fences close"
else
  fail "unclosed fences: $FENCE_ERR"
fi

# 8. Public hygiene: no local-machine paths, consumer-project names (case-insensitive),
# or real commit SHAs in shipped files, CHANGELOG, and tests.
HOME_PATH_PATTERN="$(printf '/%s/[^\\\\`[:space:]]+' 'home')"
USERS_PATH_PATTERN="$(printf '/%s/[^\\\\`[:space:]]+' 'Users')"
ORIGIN_NAME="$(printf 'sisy%s' 'phus')"
ORIGIN_NAME_CAP="$(printf 'Sisy%s' 'phus')"
COMMIT_SHA_PATTERN='(^|[^0-9a-f])[0-9a-f]{40}([^0-9a-f]|$)'
HYGIENE_PATTERN="(${HOME_PATH_PATTERN}|${USERS_PATH_PATTERN}|${COMMIT_SHA_PATTERN})"
JSON_HYGIENE_PATTERN="(${HOME_PATH_PATTERN}|${USERS_PATH_PATTERN})"
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
printf 'Mention of %s project.\n' "$ORIGIN_NAME_CAP" > "$PROBE_DIR/origin-cap.md"
if grep -qE "$JSON_HYGIENE_PATTERN" "$PROBE_DIR/leak.json" && ! grep -qE "$JSON_HYGIENE_PATTERN" "$PROBE_DIR/clean.json"; then
  pass "JSON hygiene rejects local-machine paths while permitting 40-hex commit IDs"
else
  fail "JSON hygiene calibration"
fi
if grep -qiF "$ORIGIN_NAME" "$PROBE_DIR/origin-cap.md"; then
  pass "hygiene matches consumer project name case-insensitively"
else
  fail "hygiene missed capitalized consumer project name"
fi
HYGIENE_ERRORS=()
while IFS= read -r -d '' f; do
  if grep -qiF "$ORIGIN_NAME" "$PROJECT_ROOT/$f"; then
    hit="$(grep -aniFm1 "$ORIGIN_NAME" "$PROJECT_ROOT/$f")"
    HYGIENE_ERRORS+=("$f:${hit%%:*} (consumer project name)")
  elif grep -qE "$HYGIENE_PATTERN" "$PROJECT_ROOT/$f"; then
    # Report the location and reason without echoing private content.
    hit="$(grep -anEm1 "$HYGIENE_PATTERN" "$PROJECT_ROOT/$f")"
    content="${hit#*:}"
    if [[ "$content" =~ $COMMIT_SHA_PATTERN ]]; then
      reason="full commit ID; abbreviate public commit links"
    else
      reason="local machine path"
    fi
    HYGIENE_ERRORS+=("$f:${hit%%:*} ($reason)")
  fi
done < <(git -C "$PROJECT_ROOT" ls-files -co --exclude-standard -z -- '*.md' '*.sh' '*.py' '*.yaml' '*.yml' '*.mjs')
while IFS= read -r -d '' f; do
  if grep -qiF "$ORIGIN_NAME" "$PROJECT_ROOT/$f"; then
    hit="$(grep -aniFm1 "$ORIGIN_NAME" "$PROJECT_ROOT/$f")"
    HYGIENE_ERRORS+=("$f:${hit%%:*} (consumer project name)")
  elif grep -qE "$JSON_HYGIENE_PATTERN" "$PROJECT_ROOT/$f"; then
    # Report the location and reason without echoing private content.
    hit="$(grep -anEm1 "$JSON_HYGIENE_PATTERN" "$PROJECT_ROOT/$f")"
    HYGIENE_ERRORS+=("$f:${hit%%:*} (local machine path)")
  fi
done < <(git -C "$PROJECT_ROOT" ls-files -co --exclude-standard -z -- '*.json' ':!:research/')
[[ ${#HYGIENE_ERRORS[@]} -eq 0 ]] && pass "no local or consumer-project leakage (including CHANGELOG.md and tracked JSON)" || fail "hygiene leakage in: ${HYGIENE_ERRORS[*]}"

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

# 8c. No duplicate unittest class names, top-level test_* functions, or
# test_* method names across tracked Python test files (Python silently
# overwrites earlier same-named classes/methods).
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
    seen_classes = set()
    seen_top_tests = set()
    for item in tree.body:
        if isinstance(item, ast.ClassDef):
            if item.name in seen_classes:
                duplicates.append(f"{rel}:{item.lineno} (duplicate class {item.name})")
            seen_classes.add(item.name)
        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_"):
            if item.name in seen_top_tests:
                duplicates.append(f"{rel}:{item.lineno} (duplicate function {item.name})")
            seen_top_tests.add(item.name)
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
cat > "$PROBE_DIR/dup_class.py" <<'PY'
class SameTest:
    def test_one(self):
        pass
class SameTest:
    def test_two(self):
        pass
PY
check_duplicate_tests "$PROBE_DIR" "$PROBE_DIR/dup_class.py" >/dev/null && fail "duplicate-test check accepted duplicate class names" || pass "duplicate-test check rejects duplicate class names"
if DUP_TESTS="$(check_duplicate_tests --repo)"; then
  pass "all Python test files under tests/ have unique class and test_* names"
else
  fail "duplicate test class or test_* name(s): $DUP_TESTS"
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
  "$SKILLS/ssot-preflight/references/memory-model.md"
  "$SKILLS/ssot-preflight/references/memory-layout.md"
  "$SKILLS/ssot-preflight/references/task-continuation.md"
  "$SKILLS/ssot-preflight/references/writing-memory.md"
  "$SKILLS/ssot-preflight/references/protection-departure.md"
  "$SKILLS/ssot-closeout/references/decision-capture.md"
  "$SKILLS/ssot-closeout/references/batch-closeout.md"
)
COLD_RUNTIME_FILES=(
  "$SKILLS/ssot-audit/SKILL.md"
  "$SKILLS/ssot-skill/SKILL.md"
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
budget "hot-path runtime protocol (core-4 SKILL.md + daily references)" "$(words "${HOT_RUNTIME_FILES[@]}")" 9200 words
budget "conditional/cold runtime branches (incl. legacy shims)" "$(words "${COLD_RUNTIME_FILES[@]}")" 10400 words
measure_catalog_bytes() {
  local total=0 skill_file name desc entry
  for skill_file in "$@"; do
    name="$(parse_frontmatter_field "$skill_file" name 2>/dev/null)" || return 1
    desc="$(parse_frontmatter_field "$skill_file" description 2>/dev/null)" || return 1
    entry="${name}: ${desc}"
    total=$((total + $(printf '%s' "$entry" | wc -c)))
  done
  printf '%d\n' "$total"
}
FOLDED_CATALOG_BYTES="$(measure_catalog_bytes "$PROBE_DIR/folded-skill.md" 2>/dev/null || echo 0)"
EXPECTED_FOLDED_BYTES="$(printf '%s' 'probe-skill: Read SSOT before substantive work in a repository or declared space. Follow bounded lookup routes.' | wc -c | tr -d ' ')"
[[ "$FOLDED_CATALOG_BYTES" -eq "$EXPECTED_FOLDED_BYTES" ]] &&
  pass "catalog byte measurement counts full folded multiline YAML descriptions" ||
  fail "catalog byte measurement miscounted multiline YAML description ($FOLDED_CATALOG_BYTES != $EXPECTED_FOLDED_BYTES)"
CORE_SKILL_FILES=()
for skill in "${LIFECYCLE_SKILLS[@]}"; do
  CORE_SKILL_FILES+=("$SKILLS/$skill/SKILL.md")
done
if CORE_CATALOG_BYTES="$(measure_catalog_bytes "${CORE_SKILL_FILES[@]}")" && (( CORE_CATALOG_BYTES > 0 )); then
  budget "always-loaded core-4 skill catalog (name + description)" "$CORE_CATALOG_BYTES" 600 bytes
else
  fail "could not measure core-4 skill catalog"
fi
if CATALOG_BYTES="$(measure_catalog_bytes "${ENTRY_FILES[@]}")" && (( CATALOG_BYTES > 0 )); then
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
  mapfile -t TPL_LANG_FILES < <(find "$TEMPLATES/$lang" -type f | sort)
  budget "templates/$lang" "$(bytes "${TPL_LANG_FILES[@]}")" 16384 bytes
done
SCRIPT_BYTES="$(bytes "${SCRIPT_FILES[@]}")"
budget "checker" "$(bytes "$SKILLS/ssot-doctor/assets/scripts/ssot-check.py")" 98304 bytes
budget "bundle scripts" "$SCRIPT_BYTES" 131072 bytes
if TOTAL_BYTES="$(git -C "$PROJECT_ROOT" ls-files -co --exclude-standard -z -- skills | xargs -0 cat | wc -c)" && (( TOTAL_BYTES > 0 )); then
  RUNTIME_ASSET_BYTES=$((TOTAL_BYTES - SCRIPT_BYTES))
  budget "runtime assets (skills/ excluding scripts)" "$RUNTIME_ASSET_BYTES" 163840 bytes
  budget "skills/ total" "$TOTAL_BYTES" 294912 bytes
else
  fail "could not measure the runtime files in skills/"
fi

echo
echo "=== RESULT: pass=$PASS fail=$FAIL ==="
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
