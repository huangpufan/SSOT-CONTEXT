#!/usr/bin/env bash
# tests/test-installer-e2e.sh — end-to-end installer test
# Builds a fake $HOME, runs install.sh non-interactively, asserts artifacts.
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INSTALLER="$PROJECT_ROOT/install.sh"
PASS=0
FAIL=0
WORK_ROOT="$(mktemp -d)"
trap 'rm -rf "$WORK_ROOT"' EXIT

pass() { echo "  ok   : $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL : $1"; FAIL=$((FAIL+1)); }
assert_file() { [[ -f "$2" ]] && pass "$1" || fail "$1 (missing: $2)"; }
assert_no_file() { [[ ! -f "$2" ]] && pass "$1" || fail "$1 (should not exist: $2)"; }
assert_dir() { [[ -d "$2" ]] && pass "$1" || fail "$1 (missing: $2)"; }
assert_no_dir() { [[ ! -d "$2" ]] && pass "$1" || fail "$1 (should not exist: $2)"; }
assert_grep() { grep -q "$3" "$2" 2>/dev/null && pass "$1" || fail "$1 (grep '$3' failed in $2)"; }
assert_no_grep() { ! grep -q "$3" "$2" 2>/dev/null && pass "$1" || fail "$1 (unexpected match '$3' in $2)"; }

echo "=== test-installer-e2e ==="

# Scenario 1: global install, en lang, all agents
SCENARIO1="$WORK_ROOT/scenario1"
mkdir -p "$SCENARIO1"
HOME="$SCENARIO1" SOURCE_DIR="$PROJECT_ROOT" \
  bash "$INSTALLER" --non-interactive --agent claude --scope global --lang en --yes \
  >/dev/null 2>&1 || fail "scenario1 install exit code"

CLAUDE_BASE="$SCENARIO1/.claude/skills"
assert_dir "scenario1: claude base created" "$CLAUDE_BASE"
assert_no_file "scenario1: no bundle-level companion since 3.0" "$CLAUDE_BASE/SKILL_STYLE.md"
for skill in ssot-preflight ssot-bootstrap ssot-closeout ssot-audit ssot-doctor ssot-skill; do
  assert_file "scenario1: $skill SKILL.md" "$CLAUDE_BASE/$skill/SKILL.md"
  assert_file "scenario1: $skill openai.yaml" "$CLAUDE_BASE/$skill/agents/openai.yaml"
done
assert_dir "scenario1: templates dir flattened" "$CLAUDE_BASE/ssot-bootstrap/assets/templates"
assert_no_dir "scenario1: no en/ subdir in installed templates" "$CLAUDE_BASE/ssot-bootstrap/assets/templates/en"
assert_no_dir "scenario1: no zh/ subdir in installed templates" "$CLAUDE_BASE/ssot-bootstrap/assets/templates/zh"
assert_file "scenario1: root README template present" "$CLAUDE_BASE/ssot-bootstrap/assets/templates/ssot-readme.md"
assert_file "scenario1: memory model reference installed" "$CLAUDE_BASE/ssot-preflight/references/memory-model.md"
for reference in memory-layout writing-memory protection-departure; do
  if cmp -s "$PROJECT_ROOT/skills/ssot-preflight/references/$reference.md" "$CLAUDE_BASE/ssot-preflight/references/$reference.md"; then
    pass "scenario1: $reference reference installed intact"
  else
    fail "scenario1: $reference reference missing or changed"
  fi
done
assert_file "scenario1: bootstrap reference installed" "$CLAUDE_BASE/ssot-bootstrap/references/bootstrap.md"
# English-content check: should NOT contain CJK characters (python3 — macOS grep lacks -P)
if python3 -c "import sys,re; sys.exit(0 if re.search(r'[一-龥]', open(sys.argv[1], encoding='utf-8').read()) else 1)" "$CLAUDE_BASE/ssot-bootstrap/assets/templates/architecture.md" 2>/dev/null; then
  fail "scenario1: en templates should not contain Chinese"
else
  pass "scenario1: en templates have no Chinese"
fi
assert_file "scenario1: ssot-check.py installed" "$CLAUDE_BASE/ssot-doctor/assets/scripts/ssot-check.py"

# Scenario 2: project install, zh lang, claude only
SCENARIO2="$WORK_ROOT/scenario2"
mkdir -p "$SCENARIO2/project"
HOME="$SCENARIO2" SOURCE_DIR="$PROJECT_ROOT" \
  bash -c "cd '$SCENARIO2/project' && bash '$INSTALLER' --non-interactive --agent claude --scope project --lang zh --yes" \
  >/dev/null 2>&1 || fail "scenario2 install exit code"
PROJ_BASE="$SCENARIO2/project/.claude/skills"
assert_dir "scenario2: project skills dir" "$PROJ_BASE"
assert_no_file "scenario2: no bundle-level companion since 3.0" "$PROJ_BASE/SKILL_STYLE.md"
assert_file "scenario2: ssot-preflight installed at project" "$PROJ_BASE/ssot-preflight/SKILL.md"
# zh templates: should contain CJK (use python3 — macOS grep lacks -P)
if python3 -c "import sys,re; sys.exit(0 if re.search(r'[一-龥]', open(sys.argv[1], encoding='utf-8').read()) else 1)" "$PROJ_BASE/ssot-bootstrap/assets/templates/architecture.md" 2>/dev/null; then
  pass "scenario2: zh templates contain Chinese"
else
  fail "scenario2: zh templates expected Chinese content"
fi
# The installed checker must accept an SSOT/README.md built from the installed
# (flattened, translated) template once its placeholders are filled.
mkdir -p "$SCENARIO2/project/SSOT"
sed -e 's/<初建时考察的提交>//' "$PROJ_BASE/ssot-bootstrap/assets/templates/ssot-readme.md" \
  > "$SCENARIO2/project/SSOT/README.md"
assert_grep "scenario2: installed README uses format 4" "$SCENARIO2/project/SSOT/README.md" '^ssot_format: 4$'
for doc in product architecture process gotchas glossary; do
  cp "$PROJ_BASE/ssot-bootstrap/assets/templates/$doc.md" "$SCENARIO2/project/SSOT/$doc.md"
done
mkdir -p "$SCENARIO2/project/SSOT/decisions"
if python3 "$PROJ_BASE/ssot-preflight/assets/scripts/read-context.py" "$SCENARIO2/project/SSOT/README.md" >"$SCENARIO2/context.log" 2>&1 &&
    grep -q '^## 5. Invariants$' "$SCENARIO2/context.log" &&
    ! grep -q '^### Human-decision evidence$' "$SCENARIO2/context.log"; then
  pass "scenario2: installed preflight reader returns bounded v4 context"
else
  fail "scenario2: installed preflight reader failed"
  cat "$SCENARIO2/context.log"
fi
if python3 "$PROJ_BASE/ssot-doctor/assets/scripts/ssot-check.py" "$SCENARIO2/project/SSOT" >"$SCENARIO2/check.log" 2>&1; then
  pass "scenario2: installed checker accepts an SSOT built from installed zh templates"
else
  fail "scenario2: installed checker rejects installed zh templates"
  cat "$SCENARIO2/check.log"
fi

# Scenario 3: multiple agents
SCENARIO3="$WORK_ROOT/scenario3"
mkdir -p "$SCENARIO3"
HOME="$SCENARIO3" SOURCE_DIR="$PROJECT_ROOT" \
  bash "$INSTALLER" --non-interactive --agent claude,codex --scope global --lang en --yes \
  >/dev/null 2>&1 || fail "scenario3 multi-agent install exit code"
assert_file "scenario3: claude installed" "$SCENARIO3/.claude/skills/ssot-preflight/SKILL.md"
assert_file "scenario3: codex installed" "$SCENARIO3/.codex/skills/ssot-preflight/SKILL.md"

# Scenario 4: upgrade scans and re-installs
SCENARIO4="$WORK_ROOT/scenario4"
mkdir -p "$SCENARIO4"
HOME="$SCENARIO4" SOURCE_DIR="$PROJECT_ROOT" \
  bash "$INSTALLER" --non-interactive --agent claude --scope global --lang en --yes >/dev/null 2>&1
# Touch a sentinel to ensure overwrite happens, and leave the companion file an
# older (pre-3.0) bundle installed, which this bundle no longer ships.
echo "OLD" > "$SCENARIO4/.claude/skills/ssot-preflight/SENTINEL"
printf '%s\n# old style guide\n' '<!-- SSOT-SKILL bundle companion; owned by install.sh -->' \
  > "$SCENARIO4/.claude/skills/SKILL_STYLE.md"
HOME="$SCENARIO4" SOURCE_DIR="$PROJECT_ROOT" \
  bash -c "cd '$SCENARIO4' && bash '$INSTALLER' --upgrade" >/dev/null 2>&1 || fail "scenario4 upgrade exit code"
# SKILL.md should still exist after upgrade
assert_file "scenario4: SKILL.md after upgrade" "$SCENARIO4/.claude/skills/ssot-preflight/SKILL.md"
assert_no_file "scenario4: sentinel replaced by upgrade" "$SCENARIO4/.claude/skills/ssot-preflight/SENTINEL"
assert_no_file "scenario4: retired owned companion removed by upgrade" "$SCENARIO4/.claude/skills/SKILL_STYLE.md"

# Scenario 5: uninstall
SCENARIO5="$WORK_ROOT/scenario5"
mkdir -p "$SCENARIO5"
HOME="$SCENARIO5" SOURCE_DIR="$PROJECT_ROOT" \
  bash "$INSTALLER" --non-interactive --agent claude --scope global --lang en --yes >/dev/null 2>&1
assert_file "scenario5: pre-uninstall SKILL.md exists" "$SCENARIO5/.claude/skills/ssot-preflight/SKILL.md"
HOME="$SCENARIO5" SOURCE_DIR="$PROJECT_ROOT" \
  bash "$INSTALLER" --uninstall --agent claude --scope global --yes >/dev/null 2>&1 || fail "scenario5 uninstall exit code"
assert_no_dir "scenario5: ssot-preflight removed" "$SCENARIO5/.claude/skills/ssot-preflight"
assert_no_dir "scenario5: ssot-skill removed" "$SCENARIO5/.claude/skills/ssot-skill"
assert_no_file "scenario5: owned companion removed" "$SCENARIO5/.claude/skills/SKILL_STYLE.md"
assert_dir "scenario5: base skills dir preserved" "$SCENARIO5/.claude/skills"

# Scenario 5b: install never touches an unowned shared-root file
SCENARIO5B="$WORK_ROOT/scenario5b"
mkdir -p "$SCENARIO5B/.claude/skills"
printf 'FOREIGN COMPANION\n' > "$SCENARIO5B/.claude/skills/SKILL_STYLE.md"
HOME="$SCENARIO5B" SOURCE_DIR="$PROJECT_ROOT" \
  bash "$INSTALLER" --non-interactive --agent claude --scope global --lang en --yes \
  >/dev/null 2>&1 || fail "scenario5b install exit code"
assert_grep "scenario5b: foreign companion preserved" "$SCENARIO5B/.claude/skills/SKILL_STYLE.md" "FOREIGN COMPANION"
assert_file "scenario5b: install proceeds beside a foreign file" "$SCENARIO5B/.claude/skills/ssot-preflight/SKILL.md"

# Keep the historical ownership signature independent of today's companion
# wording; deriving this fixture from the candidate tests the wrong version.
write_legacy_companion() {
  cat <<'LEGACY_COMPANION'
# SKILL.md Style — the grill-me distillation

This file is the acceptance standard for the *prose body* of every `SKILL.md`
in this bundle.
LEGACY_COMPANION
}

# Scenario 5bb: a pre-marker companion from an old bundle is retired on upgrade
SCENARIO5BB="$WORK_ROOT/scenario5bb"
mkdir -p "$SCENARIO5BB/.claude/skills"
for skill in ssot-preflight ssot-bootstrap ssot-closeout ssot-audit ssot-doctor ssot-skill; do
  mkdir -p "$SCENARIO5BB/.claude/skills/$skill"
  printf '%s\n' "# legacy $skill" > "$SCENARIO5BB/.claude/skills/$skill/SKILL.md"
done
write_legacy_companion > "$SCENARIO5BB/.claude/skills/SKILL_STYLE.md"
HOME="$SCENARIO5BB" SOURCE_DIR="$PROJECT_ROOT" \
  bash "$INSTALLER" --non-interactive --agent claude --scope global --lang en --yes \
  >/dev/null 2>&1 || fail "scenario5bb legacy companion migration exit code"
assert_no_file "scenario5bb: legacy companion retired" "$SCENARIO5BB/.claude/skills/SKILL_STYLE.md"
assert_grep "scenario5bb: legacy skill bundle is upgraded" \
  "$SCENARIO5BB/.claude/skills/ssot-preflight/SKILL.md" \
  "protocol_version: \"$(cat "$PROJECT_ROOT/VERSION" | tr -d '[:space:]')\""

# Scenario 5bc: the legacy title alone never authorizes takeover
SCENARIO5BC="$WORK_ROOT/scenario5bc"
mkdir -p "$SCENARIO5BC/.claude/skills"
write_legacy_companion > "$SCENARIO5BC/.claude/skills/SKILL_STYLE.md"
HOME="$SCENARIO5BC" SOURCE_DIR="$PROJECT_ROOT" \
  bash "$INSTALLER" --non-interactive --agent claude --scope global --lang en --yes \
  >/dev/null 2>&1 || fail "scenario5bc install exit code"
assert_grep "scenario5bc: legacy-looking file without the old bundle is not claimed" \
  "$SCENARIO5BC/.claude/skills/SKILL_STYLE.md" "the grill-me distillation"

# Scenario 5c: uninstall preserves a companion replaced by another owner
SCENARIO5C="$WORK_ROOT/scenario5c"
mkdir -p "$SCENARIO5C"
HOME="$SCENARIO5C" SOURCE_DIR="$PROJECT_ROOT" \
  bash "$INSTALLER" --non-interactive --agent claude --scope global --lang en --yes >/dev/null 2>&1
printf 'FOREIGN AFTER INSTALL\n' > "$SCENARIO5C/.claude/skills/SKILL_STYLE.md"
HOME="$SCENARIO5C" SOURCE_DIR="$PROJECT_ROOT" \
  bash "$INSTALLER" --uninstall --agent claude --scope global --yes >/dev/null 2>&1 || fail "scenario5c uninstall exit code"
assert_grep "scenario5c: uninstall preserves foreign companion" "$SCENARIO5C/.claude/skills/SKILL_STYLE.md" "FOREIGN AFTER INSTALL"

# Scenario 6: --version
VERSION_OUTPUT="$(bash "$INSTALLER" --version 2>&1)"
EXPECTED_VERSION="$(cat "$PROJECT_ROOT/VERSION" 2>/dev/null | tr -d '[:space:]')"
if [[ -n "$EXPECTED_VERSION" && "$VERSION_OUTPUT" == *"$EXPECTED_VERSION"* ]]; then
  pass "scenario6: --version prints $EXPECTED_VERSION"
else
  fail "scenario6: --version output ('$VERSION_OUTPUT')"
fi

# Scenario 7: --help
HELP_OUTPUT="$(bash "$INSTALLER" --help 2>&1)"
if [[ "$HELP_OUTPUT" == *"USAGE"* || "$HELP_OUTPUT" == *"usage"* ]]; then
  pass "scenario7: --help has USAGE section"
else
  fail "scenario7: --help missing USAGE"
fi

# Scenario 8: non-interactive missing args should fail
SCENARIO8_OUT="$(SSOT_NONINTERACTIVE=1 bash "$INSTALLER" 2>&1)"
SCENARIO8_RC=$?
if [[ $SCENARIO8_RC -ne 0 ]]; then
  pass "scenario8: non-interactive without args exits non-zero"
else
  fail "scenario8: non-interactive should fail without args"
fi

# Scenario 9: legacy alias --agent claude resolves to claude-code
SCENARIO9="$WORK_ROOT/scenario9"
mkdir -p "$SCENARIO9/project"
HOME="$SCENARIO9" SOURCE_DIR="$PROJECT_ROOT" \
  bash -c "cd '$SCENARIO9/project' && bash '$INSTALLER' --non-interactive --agent claude --scope project --lang en --yes" \
  >/dev/null 2>&1 || fail "scenario9 alias install exit code"
assert_file "scenario9: alias claude resolved to claude-code → .claude/skills" "$SCENARIO9/project/.claude/skills/ssot-preflight/SKILL.md"

# Scenario 10: install new Vercel-aligned agent (gemini-cli → .agents/skills)
SCENARIO10="$WORK_ROOT/scenario10"
mkdir -p "$SCENARIO10/project"
HOME="$SCENARIO10" SOURCE_DIR="$PROJECT_ROOT" \
  bash -c "cd '$SCENARIO10/project' && bash '$INSTALLER' --non-interactive --agent gemini-cli --scope project --lang en --yes" \
  >/dev/null 2>&1 || fail "scenario10 gemini-cli install exit code"
assert_file "scenario10: gemini-cli project install at .agents/skills" "$SCENARIO10/project/.agents/skills/ssot-preflight/SKILL.md"

# Scenario 11: dedup for agents sharing the same install path
SCENARIO11="$WORK_ROOT/scenario11"
mkdir -p "$SCENARIO11/project"
SCEN11_LOG="$(HOME="$SCENARIO11" SOURCE_DIR="$PROJECT_ROOT" \
  bash -c "cd '$SCENARIO11/project' && bash '$INSTALLER' --non-interactive --agent cline,dexto,loaf --scope project --lang en --yes" 2>&1)"
assert_file "scenario11: dedup installs once at shared path" "$SCENARIO11/project/.agents/skills/ssot-preflight/SKILL.md"
if echo "$SCEN11_LOG" | grep -qi "skipping"; then
  pass "scenario11: dedup warning emitted"
else
  fail "scenario11: expected 'skipping' dedup warning"
fi

# Scenario 12: --list-agents prints 65+ agents including claude-code and gemini-cli
LIST_OUTPUT="$(bash "$INSTALLER" --list-agents 2>&1)"
LIST_COUNT="$(echo "$LIST_OUTPUT" | grep -cE '^  [a-z][a-z0-9_-]+ +' || echo 0)"
if [[ "$LIST_COUNT" -ge 60 ]]; then
  pass "scenario12: --list-agents prints $LIST_COUNT agents (>=60)"
else
  fail "scenario12: --list-agents printed $LIST_COUNT agents (expected >=60)"
fi
if echo "$LIST_OUTPUT" | grep -qE '^  claude-code '; then
  pass "scenario12: --list-agents includes claude-code"
else
  fail "scenario12: --list-agents missing claude-code"
fi
if echo "$LIST_OUTPUT" | grep -qE '^  gemini-cli '; then
  pass "scenario12: --list-agents includes gemini-cli"
else
  fail "scenario12: --list-agents missing gemini-cli"
fi

# Scenario 13: promptscript has no global install location — must fail loudly
SCENARIO13="$WORK_ROOT/scenario13"
mkdir -p "$SCENARIO13"
HOME="$SCENARIO13" SOURCE_DIR="$PROJECT_ROOT" \
  bash "$INSTALLER" --non-interactive --agent promptscript --scope global --lang en --yes \
  >/dev/null 2>&1
SCEN13_RC=$?
if [[ $SCEN13_RC -ne 0 ]]; then
  pass "scenario13: promptscript global install exits non-zero"
else
  fail "scenario13: promptscript global install should fail"
fi

# Scenario 14: --quickstart with SSOT_AGENT env autodetect → project install
SCENARIO14="$WORK_ROOT/scenario14"
mkdir -p "$SCENARIO14/project"
SCEN14_LOG="$(HOME="$SCENARIO14" SOURCE_DIR="$PROJECT_ROOT" SSOT_AGENT=claude-code \
  bash -c "cd '$SCENARIO14/project' && bash '$INSTALLER' --quickstart" 2>&1)"
SCEN14_RC=$?
if [[ $SCEN14_RC -eq 0 ]]; then
  pass "scenario14: --quickstart with SSOT_AGENT=claude-code exits 0"
else
  fail "scenario14: --quickstart exit code ($SCEN14_RC); log: $SCEN14_LOG"
fi
assert_file "scenario14: project install landed at .claude/skills" "$SCENARIO14/project/.claude/skills/ssot-preflight/SKILL.md"
assert_file "scenario14: ssot-skill shim installed too" "$SCENARIO14/project/.claude/skills/ssot-skill/SKILL.md"
if echo "$SCEN14_LOG" | grep -q "also install globally"; then
  pass "scenario14: post-install prints global install hint"
else
  fail "scenario14: missing 'also install globally' hint"
fi

# Scenario 15: --quickstart with CLAUDECODE=1 signature env (no SSOT_AGENT)
SCENARIO15="$WORK_ROOT/scenario15"
mkdir -p "$SCENARIO15/project"
SCEN15_LOG="$(HOME="$SCENARIO15" SOURCE_DIR="$PROJECT_ROOT" CLAUDECODE=1 \
  bash -c "unset SSOT_AGENT; cd '$SCENARIO15/project' && bash '$INSTALLER' --quickstart" 2>&1)"
SCEN15_RC=$?
if [[ $SCEN15_RC -eq 0 ]]; then
  pass "scenario15: --quickstart with CLAUDECODE=1 exits 0"
else
  fail "scenario15: --quickstart exit code ($SCEN15_RC); log: $SCEN15_LOG"
fi
assert_file "scenario15: project install landed at .claude/skills via CLAUDECODE=1" "$SCENARIO15/project/.claude/skills/ssot-preflight/SKILL.md"

# Scenario 16: --quickstart --scope global → global install, no project hint
SCENARIO16="$WORK_ROOT/scenario16"
mkdir -p "$SCENARIO16"
SCEN16_LOG="$(HOME="$SCENARIO16" SOURCE_DIR="$PROJECT_ROOT" SSOT_AGENT=claude-code \
  bash "$INSTALLER" --quickstart --scope global 2>&1)"
SCEN16_RC=$?
if [[ $SCEN16_RC -eq 0 ]]; then
  pass "scenario16: --quickstart --scope global exits 0"
else
  fail "scenario16: --quickstart --scope global exit code ($SCEN16_RC); log: $SCEN16_LOG"
fi
assert_file "scenario16: global install landed at \$HOME/.claude/skills" "$SCENARIO16/.claude/skills/ssot-preflight/SKILL.md"
if echo "$SCEN16_LOG" | grep -q "also install globally"; then
  fail "scenario16: global scope should NOT print 'also install globally' hint"
else
  pass "scenario16: global scope omits project-only hint"
fi

# Scenario 17: no tty + no flag → actionable die message
SCENARIO17="$WORK_ROOT/scenario17"
mkdir -p "$SCENARIO17/project"
# Closing stdin (< /dev/null) AND running outside a tty simulates curl|bash without /dev/tty.
SCEN17_LOG="$(HOME="$SCENARIO17" SOURCE_DIR="$PROJECT_ROOT" \
  bash -c "cd '$SCENARIO17/project' && bash '$INSTALLER' < /dev/null" 2>&1)"
SCEN17_RC=$?
if [[ $SCEN17_RC -ne 0 ]]; then
  pass "scenario17: no-tty no-flag invocation exits non-zero"
else
  fail "scenario17: should fail without flags + no tty"
fi
if echo "$SCEN17_LOG" | grep -q "no tty available"; then
  pass "scenario17: error mentions 'no tty available'"
else
  fail "scenario17: missing 'no tty available' in error; log: $SCEN17_LOG"
fi
if echo "$SCEN17_LOG" | grep -q -- "--quickstart"; then
  pass "scenario17: error suggests --quickstart"
else
  fail "scenario17: missing --quickstart suggestion; log: $SCEN17_LOG"
fi
if echo "$SCEN17_LOG" | grep -q -- "--agent"; then
  pass "scenario17: error suggests --agent"
else
  fail "scenario17: missing --agent suggestion; log: $SCEN17_LOG"
fi

# Scenario 18: generated caches in source are never copied into installs
SCENARIO18="$WORK_ROOT/scenario18"
FAKE_SRC="$WORK_ROOT/fake-src"
mkdir -p "$SCENARIO18" "$FAKE_SRC"
cp -R "$PROJECT_ROOT/skills" "$FAKE_SRC/skills"
cp "$PROJECT_ROOT/VERSION" "$FAKE_SRC/VERSION"
mkdir -p "$FAKE_SRC/skills/ssot-doctor/assets/scripts/__pycache__"
printf 'junk\n' > "$FAKE_SRC/skills/ssot-doctor/assets/scripts/__pycache__/x.cpython-312.pyc"
printf 'junk\n' > "$FAKE_SRC/skills/ssot-preflight/.DS_Store"
HOME="$SCENARIO18" SOURCE_DIR="$FAKE_SRC" \
  bash "$INSTALLER" --non-interactive --agent claude --scope global --lang en --yes \
  >/dev/null 2>&1 || fail "scenario18 install exit code"
assert_file "scenario18: install from fake source works" "$SCENARIO18/.claude/skills/ssot-preflight/SKILL.md"
if find "$SCENARIO18/.claude/skills" \( -name "__pycache__" -o -name "*.pyc" -o -name ".DS_Store" \) | grep -q .; then
  fail "scenario18: generated cache files leaked into install"
else
  pass "scenario18: __pycache__/.DS_Store excluded from install"
fi

# Scenario 19: upgrade selection is read-only here, with isolated registry paths.
# In particular, --scope project must never select a global installation.
SCENARIO19="$WORK_ROOT/scenario19"
mkdir -p "$SCENARIO19"
if SSOT_TEST_INSTALLER="$INSTALLER" SSOT_TEST_ROOT="$SCENARIO19" bash <<'SH' >"$SCENARIO19/check.log" 2>&1
source <(sed '/^main "\$@"$/d' "$SSOT_TEST_INSTALLER")
cd "$SSOT_TEST_ROOT"
ALL_AGENTS=(claude-code codex cursor)
AGENT_LABELS=([claude-code]=Claude [codex]=Codex [cursor]=Cursor)
AGENT_PROJECT_BASES=([claude-code]=.claude/skills [codex]=.agents/skills [cursor]=.agents/skills)
AGENT_GLOBAL_BASES=([claude-code]="$PWD/global/claude" [codex]="$PWD/global/shared" [cursor]="$PWD/global/shared")
for base in .claude/skills .agents/skills global/claude global/shared; do
  mkdir -p "$base/ssot-preflight"
done
ARG_AGENT=codex
ARG_SCOPE=project
scan_upgrade_targets
[[ ${#UPGRADE_ROWS[@]} -eq 1 && "${UPGRADE_ROWS[0]}" == codex\|project\|* ]]
ARG_AGENT=claude
ARG_SCOPE=global
scan_upgrade_targets
[[ ${#UPGRADE_ROWS[@]} -eq 1 && "${UPGRADE_ROWS[0]}" == claude-code\|global\|* ]]
ARG_AGENT=""
ARG_SCOPE=""
scan_upgrade_targets
[[ ${#UPGRADE_ROWS[@]} -eq 4 ]]
# A directory symlink is also one physical installation.
ln -s .agents .cursor-alias
AGENT_PROJECT_BASES[cursor]=.cursor-alias/skills
ARG_SCOPE=project
scan_upgrade_targets
[[ ${#UPGRADE_ROWS[@]} -eq 2 ]]
SH
then
  pass "scenario19: upgrade honors scope/agent/alias and visits shared paths once"
else
  fail "scenario19: upgrade selection or physical-path deduplication is wrong"
fi

# Scenario 20: multiple detected agents are not evidence of the active agent.
SCENARIO20="$WORK_ROOT/scenario20"
mkdir -p "$SCENARIO20"
if env -i PATH="$PATH" SSOT_TEST_INSTALLER="$INSTALLER" bash <<'SH' >"$SCENARIO20/check.log" 2>&1
source <(sed '/^main "\$@"$/d' "$SSOT_TEST_INSTALLER")
DETECTED_AGENTS=(claude-code codex)
if autodetect_agent; then exit 1; fi
DETECTED_AGENTS=(codex)
[[ "$(autodetect_agent)" == codex ]]
DETECTED_AGENTS=(claude-code codex)
CLAUDECODE=1
[[ "$(autodetect_agent)" == claude-code ]]
SH
then
  pass "scenario20: ambiguous detection fails; unique and active-agent detection work"
else
  fail "scenario20: quickstart silently chooses among multiple detected agents"
fi

# Scenario 21: a downloaded installer can clone without GNU timeout (macOS),
# and removes its fetched source and staging directories after success/failure.
SCENARIO21="$WORK_ROOT/scenario21"
mkdir -p "$SCENARIO21/bin" "$SCENARIO21/tmp" "$SCENARIO21/project" "$SCENARIO21/source"
cp "$INSTALLER" "$SCENARIO21/install.sh"
# Clone a snapshot of the working tree, not HEAD: the downloaded installer and
# its source bundle must describe the same candidate before it is committed.
cp -R "$PROJECT_ROOT/skills" "$SCENARIO21/source/skills"
cp "$PROJECT_ROOT/VERSION" "$SCENARIO21/source/VERSION"
git -C "$SCENARIO21/source" init -q
git -C "$SCENARIO21/source" symbolic-ref HEAD refs/heads/main
git -C "$SCENARIO21/source" add skills VERSION
git -C "$SCENARIO21/source" -c core.hooksPath=/dev/null -c commit.gpgsign=false \
  -c user.name=SSOT-test -c user.email=ssot-test@example.invalid commit -qm 'installer source fixture'
for utility in bash git dirname mkdir mktemp rm tr cp mv tput head grep awk sed find basename tar curl; do
  ln -s "$(command -v "$utility")" "$SCENARIO21/bin/$utility"
done
if (cd "$SCENARIO21/project" && env -u SOURCE_DIR PATH="$SCENARIO21/bin" TMPDIR="$SCENARIO21/tmp" \
  SSOT_SKILL_REPO_URL="$SCENARIO21/source" bash "$SCENARIO21/install.sh" \
  --quickstart --agent claude-code --scope project --lang en) >"$SCENARIO21/check.log" 2>&1; then
  pass "scenario21: fetched-source installation works without GNU timeout"
else
  fail "scenario21: fetched-source installation failed without GNU timeout"
  cat "$SCENARIO21/check.log"
fi
assert_file "scenario21: fetched bundle installed" "$SCENARIO21/project/.claude/skills/ssot-preflight/SKILL.md"
if [[ -z "$(find "$SCENARIO21/tmp" -mindepth 1 -print -quit)" ]]; then
  pass "scenario21: fetched source is cleaned up"
else
  fail "scenario21: fetched source leaked after installation"
fi
if [[ -f "$SCENARIO21/project/.claude/skills/ssot-preflight/SKILL.md" ]]; then
  cp "$SCENARIO21/project/.claude/skills/ssot-preflight/SKILL.md" "$SCENARIO21/before.md"
  # Fail while staging a replacement, before any installed skill is removed.
  rm "$SCENARIO21/bin/cp"
  printf '#!/bin/sh\nexit 73\n' > "$SCENARIO21/bin/cp"
  chmod +x "$SCENARIO21/bin/cp"
  if (cd "$SCENARIO21/project" && env -u SOURCE_DIR PATH="$SCENARIO21/bin" TMPDIR="$SCENARIO21/tmp" \
    SSOT_SKILL_REPO_URL="$SCENARIO21/source" bash "$SCENARIO21/install.sh" \
    --quickstart --agent claude-code --scope project --lang en) >"$SCENARIO21/failure.log" 2>&1; then
    fail "scenario21: failed staging must not report success"
  else
    pass "scenario21: staging failure is reported"
  fi
  if cmp -s "$SCENARIO21/before.md" "$SCENARIO21/project/.claude/skills/ssot-preflight/SKILL.md" &&
     [[ -z "$(find "$SCENARIO21/tmp" -mindepth 1 -print -quit)" ]] &&
     [[ -z "$(find "$SCENARIO21/project" -name '.ssot-skill-install.*' -print -quit)" ]]; then
    pass "scenario21: staging failure preserves installed content and cleans temporary files"
  else
    fail "scenario21: staging failure damaged content or leaked temporary files"
  fi
fi

# Scenario 22: exercise the real scoped update/removal commands. All selected
# writable locations are temporary; no user-global installation may be touched.
SCENARIO22="$WORK_ROOT/scenario22"
mkdir -p "$SCENARIO22/project/SSOT" "$SCENARIO22/project/.agents/skills/ssot-preflight" \
  "$SCENARIO22/global/skills/ssot-preflight" "$SCENARIO22/project/.claude/skills/other-skill"
printf 'project documentation\n' > "$SCENARIO22/project/SSOT/README.md"
printf 'user instructions\n' > "$SCENARIO22/project/AGENTS.md"
printf 'other agent\n' > "$SCENARIO22/project/.agents/skills/ssot-preflight/SKILL.md"
printf 'global install\n' > "$SCENARIO22/global/skills/ssot-preflight/SKILL.md"
printf 'other skill\n' > "$SCENARIO22/project/.claude/skills/other-skill/SKILL.md"
if (cd "$SCENARIO22/project" && SOURCE_DIR="$PROJECT_ROOT" \
  bash "$INSTALLER" --quickstart --agent claude-code --scope project --lang zh) >"$SCENARIO22/install.log" 2>&1; then
  printf 'old bundle\n' > "$SCENARIO22/project/.claude/skills/ssot-preflight/SENTINEL"
  if (cd "$SCENARIO22/project" && SOURCE_DIR="$PROJECT_ROOT" CLAUDE_CONFIG_DIR="$SCENARIO22/global" \
    bash "$INSTALLER" --upgrade --agent claude --scope project) >"$SCENARIO22/upgrade.log" 2>&1; then
    pass "scenario22: scoped upgrade succeeds with an agent alias"
  else
    fail "scenario22: scoped upgrade failed"
    cat "$SCENARIO22/upgrade.log"
  fi
  assert_no_file "scenario22: selected bundle refreshed" "$SCENARIO22/project/.claude/skills/ssot-preflight/SENTINEL"
  if cmp -s "$PROJECT_ROOT/skills/ssot-bootstrap/assets/templates/zh/ssot-readme.md" \
    "$SCENARIO22/project/.claude/skills/ssot-bootstrap/assets/templates/ssot-readme.md"; then
    pass "scenario22: upgrade preserves installed template language"
  else
    fail "scenario22: upgrade changed template language"
  fi
  assert_grep "scenario22: global install untouched" "$SCENARIO22/global/skills/ssot-preflight/SKILL.md" '^global install$'
  assert_grep "scenario22: other agent untouched" "$SCENARIO22/project/.agents/skills/ssot-preflight/SKILL.md" '^other agent$'
  if (cd "$SCENARIO22/project" && bash "$INSTALLER" --uninstall --agent claude --scope project --yes) \
    >"$SCENARIO22/uninstall.log" 2>&1; then
    pass "scenario22: scoped uninstall succeeds"
  else
    fail "scenario22: scoped uninstall failed"
  fi
  assert_no_dir "scenario22: selected bundle removed" "$SCENARIO22/project/.claude/skills/ssot-preflight"
  assert_grep "scenario22: project documentation preserved" "$SCENARIO22/project/SSOT/README.md" '^project documentation$'
  assert_grep "scenario22: user instructions preserved" "$SCENARIO22/project/AGENTS.md" '^user instructions$'
  assert_grep "scenario22: unrelated skill preserved" "$SCENARIO22/project/.claude/skills/other-skill/SKILL.md" '^other skill$'
else
  fail "scenario22: setup install failed"
  cat "$SCENARIO22/install.log"
fi
if bash "$INSTALLER" --uninstall --agent promptscript --scope global --yes >"$SCENARIO22/unsupported.log" 2>&1; then
  fail "scenario22: unsupported global removal must fail without a target"
else
  pass "scenario22: unsupported global removal is rejected"
fi
if (cd "$SCENARIO22/project" && bash "$INSTALLER" --upgrade --agent nonexistent-agent --scope project) \
  >"$SCENARIO22/invalid.log" 2>&1; then
  fail "scenario22: invalid upgrade agent must fail"
else
  pass "scenario22: invalid upgrade agent is rejected"
fi
bash "$INSTALLER" --list-agents >"$SCENARIO22/agents.log" 2>&1
assert_grep "scenario22: agent listing includes project paths" "$SCENARIO22/agents.log" 'PROJECT PATH'

# Scenario 23: installation and bootstrap must deliver the same instructions.
# These are output/packaging checks; prompt behavior is reviewed separately.
SCENARIO23="$WORK_ROOT/scenario23"
mkdir -p "$SCENARIO23"
if python3 - "$PROJECT_ROOT" "$SCENARIO23" <<'PY'
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

root, work = map(Path, sys.argv[1:])
begin, end = '<!-- SSOT-SKILL:BEGIN -->', '<!-- SSOT-SKILL:END -->'
source = work / 'source'
shutil.copytree(root / 'skills', source / 'skills')
shutil.copy2(root / 'VERSION', source / 'VERSION')
templates = source / 'skills/ssot-bootstrap/assets/templates'

def block(text):
    assert text.count(begin) == text.count(end) == 1
    return text[text.index(begin):text.index(end) + len(end)]

def run(project, label, *args):
    result = subprocess.run(
        ['bash', str(root / 'install.sh'), *args, '--agent', 'codex', '--scope', 'project'],
        cwd=project, env=dict(os.environ, SOURCE_DIR=str(source)),
        text=True, capture_output=True, timeout=30,
    )
    (work / (label + '.log')).write_text(result.stdout + result.stderr)
    return result

def snapshot(directory):
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob('*') if path.is_file()
    }

for lang in ('en', 'zh'):
    project = work / lang
    project.mkdir()
    (project / 'AGENTS.md').write_text('# Existing instructions\nKeep the project rules.\n')
    (project / 'CLAUDE.md').symlink_to('AGENTS.md')
    original_instructions = (project / 'AGENTS.md').read_bytes()
    template = templates / lang / 'adapter-thin.md'
    expected = block(template.read_text())
    assert len(template.read_text().splitlines()) <= 50
    for route in ('preflight', 'bootstrap', 'closeout', 'doctor'):
        assert ('$ssot-' + route) in expected, route
    assert 'SSOT-generated' not in expected and '<project-name>' not in expected and '<项目名>' not in expected
    for action in ('install', 'upgrade'):
        args = ('--quickstart', '--lang', lang) if action == 'install' else ('--upgrade',)
        result = run(project, lang + '-' + action, *args)
        assert result.returncode == 0, result.stdout + result.stderr
        assert block(result.stdout) == expected, (lang, action, 'printed instructions differ')
        installed = project / '.agents/skills/ssot-bootstrap/assets/templates/adapter-thin.md'
        assert block(installed.read_text()) == expected, (lang, action, 'bootstrap instructions differ')
        assert (project / 'AGENTS.md').read_bytes() == original_instructions
        assert (project / 'CLAUDE.md').is_symlink()
        assert not (project / 'SSOT').exists()
    print('  verified: ' + lang + ' install/upgrade output equals bootstrap instructions; existing entry files preserved')

# Invalid instructions must fail before replacing any installed file.
project = work / 'en'
installed_before = snapshot(project / '.agents/skills')
template = templates / 'en/adapter-thin.md'
original = template.read_text()
invalid = {
    'missing-block': original.replace(block(original), ''),
    'unclosed-block': original.replace(end, ''),
    'duplicate-block': original + '\n' + block(original),
    'empty-block': original.replace(block(original), begin + '\n' + end),
    'missing-route': original.replace('$ssot-closeout', 'removed-route'),
}
for label, content in invalid.items():
    template.write_text(content)
    result = run(project, label, '--upgrade')
    assert result.returncode != 0, label + ' should fail'
    assert 'instruction block' in result.stderr, result.stderr
    assert snapshot(project / '.agents/skills') == installed_before, label + ' changed existing installation'
    assert not list((project / '.agents/skills').glob('.ssot-skill-install.*'))
    print('  verified: ' + label + ' rejects upgrade and preserves installed files')
template.write_text(original)

# Flat sources (such as an installed bundle) use the same extraction path.
flat = work / 'flat-templates'
shutil.copytree(templates / 'en', flat)
shutil.rmtree(templates)
shutil.move(str(flat), str(templates))
result = run(project, 'flat-source', '--upgrade')
assert result.returncode == 0, result.stdout + result.stderr
assert block(result.stdout) == block(original)
print('  verified: flat template source retains the shared instructions')
PY
then
  pass "scenario23: shared instructions survive install/upgrade and reject malformed sources safely"
else
  fail "scenario23: instruction output, template parity, or failure preservation is wrong"
fi

# Scenario 24: --ref installs a tagged generation instead of main. The fixture
# repository has an older tagged bundle (different protocol version, still
# shipping the pre-3.0 companion file) and the current bundle on main.
SCENARIO24="$WORK_ROOT/scenario24"
REF_SRC="$SCENARIO24/source"
mkdir -p "$REF_SRC" "$SCENARIO24/home"
cp -R "$PROJECT_ROOT/skills" "$REF_SRC/skills"
cp "$PROJECT_ROOT/VERSION" "$REF_SRC/VERSION"
sed -i.bak 's/protocol_version: "[^"]*"/protocol_version: "2.99-fixture"/' "$REF_SRC/skills/ssot-preflight/SKILL.md"
rm -f "$REF_SRC/skills/ssot-preflight/SKILL.md.bak"
printf '%s\n# old style guide\n' '<!-- SSOT-SKILL bundle companion; owned by install.sh -->' > "$REF_SRC/skills/SKILL_STYLE.md"
git -C "$REF_SRC" init -q
git -C "$REF_SRC" symbolic-ref HEAD refs/heads/main
REF_GIT=(git -C "$REF_SRC" -c core.hooksPath=/dev/null -c commit.gpgsign=false -c user.name=SSOT-test -c user.email=ssot-test@example.invalid)
"${REF_GIT[@]}" add -A && "${REF_GIT[@]}" commit -qm 'old generation' && "${REF_GIT[@]}" tag old-gen
sed -i.bak 's/protocol_version: "[^"]*"/protocol_version: "3.99-fixture"/' "$REF_SRC/skills/ssot-preflight/SKILL.md"
rm -f "$REF_SRC/skills/ssot-preflight/SKILL.md.bak"
"${REF_GIT[@]}" add -A && "${REF_GIT[@]}" commit -qm 'v3 generation' && "${REF_GIT[@]}" tag v3-gen
rm -rf "$REF_SRC/skills" && cp -R "$PROJECT_ROOT/skills" "$REF_SRC/skills"
"${REF_GIT[@]}" add -A && "${REF_GIT[@]}" commit -qm 'current generation'
CURRENT_VERSION="$(tr -d '[:space:]' < "$PROJECT_ROOT/VERSION")"

ref_install() { # $1=project dir, rest=extra args
  local project="$1"; shift
  mkdir -p "$project"
  (cd "$project" && env -u SOURCE_DIR HOME="$SCENARIO24/home" SSOT_SKILL_REPO_URL="$REF_SRC" \
    bash "$INSTALLER" --non-interactive --agent claude-code --scope project --lang en --yes "$@")
}
if ref_install "$SCENARIO24/tagged" --ref old-gen >"$SCENARIO24/tagged.log" 2>&1; then
  pass "scenario24: --ref <tag> install succeeds"
else
  fail "scenario24: --ref <tag> install failed"; cat "$SCENARIO24/tagged.log"
fi
assert_grep "scenario24: --ref installs the tagged protocol" \
  "$SCENARIO24/tagged/.claude/skills/ssot-preflight/SKILL.md" 'protocol_version: "2.99-fixture"'
assert_grep "scenario24: a tagged bundle's companion is still installed" \
  "$SCENARIO24/tagged/.claude/skills/SKILL_STYLE.md" "owned by install.sh"
ref_install "$SCENARIO24/default" >"$SCENARIO24/default.log" 2>&1 || fail "scenario24: default install failed"
assert_grep "scenario24: without --ref, main is installed" \
  "$SCENARIO24/default/.claude/skills/ssot-preflight/SKILL.md" "protocol_version: \"$CURRENT_VERSION\""
ref_install "$SCENARIO24/tagged" --ref main >"$SCENARIO24/back.log" 2>&1 || fail "scenario24: moving back to main failed"
assert_grep "scenario24: replacing 2.x with current format prints the upgrade note" "$SCENARIO24/back.log" "read-only for agents until migrated"
assert_no_file "scenario24: moving from the tag to main retires the companion" \
  "$SCENARIO24/tagged/.claude/skills/SKILL_STYLE.md"
ref_install "$SCENARIO24/legacy-chain" --ref old-gen >"$SCENARIO24/chain-old.log" 2>&1 || fail "scenario24: chain setup failed"
ref_install "$SCENARIO24/legacy-chain" --ref v3-gen >"$SCENARIO24/chain-v3.log" 2>&1 || fail "scenario24: legacy 2-to-3 upgrade failed"
assert_grep "scenario24: legacy 2-to-3 warning preserved" "$SCENARIO24/chain-v3.log" "read-only for agents until migrated"
ref_install "$SCENARIO24/legacy-chain" --ref main >"$SCENARIO24/chain-v4.log" 2>&1 || fail "scenario24: 3-to-4 upgrade failed"
assert_grep "scenario24: 3-to-4 warns about old memory" "$SCENARIO24/chain-v4.log" "v2 or v3 SSOT are read-only"
ref_install "$SCENARIO24/legacy-chain" --ref main >"$SCENARIO24/chain-same.log" 2>&1 || fail "scenario24: same-major reinstall failed"
if grep -q 'read-only for agents until migrated' "$SCENARIO24/chain-same.log"; then
  fail "scenario24: same-major reinstall emits a migration warning"
else
  pass "scenario24: same-major reinstall omits the migration warning"
fi
if ref_install "$SCENARIO24/bad" --ref 'old-gen;rm -rf /' >"$SCENARIO24/bad.log" 2>&1; then
  fail "scenario24: an invalid --ref must be rejected"
else
  assert_grep "scenario24: invalid --ref is explained" "$SCENARIO24/bad.log" "invalid --ref"
fi
assert_no_dir "scenario24: rejected --ref installs nothing" "$SCENARIO24/bad/.claude/skills/ssot-preflight"
if (cd "$SCENARIO24" && SOURCE_DIR="$PROJECT_ROOT" bash "$INSTALLER" --non-interactive --agent claude-code \
  --scope project --lang en --yes --ref old-gen) >"$SCENARIO24/conflict.log" 2>&1; then
  fail "scenario24: --ref with SOURCE_DIR must be rejected"
else
  assert_grep "scenario24: --ref/SOURCE_DIR conflict is explained" "$SCENARIO24/conflict.log" "cannot be combined"
fi
# Run from a local checkout: an explicit --ref must not fall back to it.
mkdir -p "$SCENARIO24/checkout"
cp "$INSTALLER" "$SCENARIO24/checkout/install.sh"
cp -R "$PROJECT_ROOT/skills" "$SCENARIO24/checkout/skills"
mkdir -p "$SCENARIO24/from-checkout"
if (cd "$SCENARIO24/from-checkout" && env -u SOURCE_DIR HOME="$SCENARIO24/home" SSOT_SKILL_REPO_URL="$REF_SRC" \
  bash "$SCENARIO24/checkout/install.sh" --non-interactive --agent claude-code --scope project --lang en --yes \
  --ref old-gen) >"$SCENARIO24/checkout.log" 2>&1; then
  assert_grep "scenario24: --ref from a local checkout still fetches the ref" \
    "$SCENARIO24/from-checkout/.claude/skills/ssot-preflight/SKILL.md" 'protocol_version: "2.99-fixture"'
else
  fail "scenario24: --ref from a local checkout failed"; cat "$SCENARIO24/checkout.log"
fi

echo
echo "=== RESULT: pass=$PASS fail=$FAIL ==="
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
