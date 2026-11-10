# Install Guide (Agent-facing)

Use this guide when a user asks you to install, reinstall, update, or remove SSOT-CONTEXT. Work in the **user's target repository**, preserve existing instructions, and respond in the user's language.

For a new installation, finish the setup: install the bundle, verify the installed files, and merge the lifecycle instructions. Skill discovery is confirmed only after the agent session restarts.

For an update or removal, resolve the choices and download the installer, then follow [the maintenance section](#update-or-remove-an-existing-installation) instead of running a fresh installation.

## 1. Resolve the installation choices

Honor options the user already supplied. Otherwise use these defaults without asking them to reconfirm:

- **Agent:** the coding agent you are currently running as. Pass its canonical installer key explicitly; a machine may have several agents installed.
- **Scope:** `project` by default; use `global` for an explicit global-only request. Install in both locations only when the user requests both. Run project commands from the target repository root.
- **Template language:** keep the repository's existing choice: the `language` in `SSOT/README.md` front matter, the `documentation_language` of an older `SSOT/STATUS.md`, or the installed template language on reinstall. For a new setup, use `zh` when the user is communicating in Chinese, otherwise `en`. A template choice never changes the language an existing SSOT is written in.
- **Version:** the current release, from `main`. Add `--ref v2-final` only when the user wants to stay on the earlier v2 protocol (see [Update or remove](#update-or-remove-an-existing-installation)).

If the target repository or agent identity cannot be determined from the current session, ask for that missing information. Routine defaults do not need a separate approval step.

Common keys and project locations:

| Current agent | Key | Project skills directory |
|---|---|---|
| Claude Code | `claude-code` | `.claude/skills/` |
| Codex | `codex` | `.agents/skills/` |
| Cursor | `cursor` | `.agents/skills/` |
| Windsurf | `windsurf` | `.windsurf/skills/` |
| Gemini CLI | `gemini-cli` | `.agents/skills/` |
| GitHub Copilot | `github-copilot` | `.agents/skills/` |

For other agents or global locations, use the installer's `--list-agents` output. Its registry is the authority for paths; respect configuration overrides shown there.

## 2. Install the bundle

Check that Bash 4+, `git`, `curl`, and `python3` are available. On macOS, the system Bash is too old. If Homebrew Bash is already installed, use `"$(brew --prefix)/bin/bash"`; otherwise explain the missing prerequisite and install it only within the user's authorization.

Download the installer to a temporary directory so a failed download cannot look like a successful installation. Replace the placeholder values with the choices resolved above, then run:

```bash
ssot_agent='<agent-key>'
ssot_template_lang='<en-or-zh>'
ssot_scope='<project-or-global>'
ssot_install_dir="$(mktemp -d)"
printf 'Installer directory: %s\n' "$ssot_install_dir"
if ! curl -fsSL --connect-timeout 10 --max-time 60 --retry 2 \
  https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh \
  -o "$ssot_install_dir/install.sh"; then
  printf 'Installer download failed; setup has not run.\n' >&2
  exit 1
fi
```

For an installation, run:

```bash
bash "$ssot_install_dir/install.sh" --quickstart \
  --agent "$ssot_agent" --scope "$ssot_scope" --lang "$ssot_template_lang"
```

Check the download and installer results separately. Retain the printed temporary path and resolved choices if subsequent steps run in a new shell. A download failure means nothing was installed; an installer failure must be resolved before continuing to verification or instruction wiring. Preserve stderr and report the specific failure.

If the download fails for network reasons, the existing mirror is:

```text
https://gh-proxy.com/https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh
```

Retry the download using that URL, then run the same installer command. Do not treat invalid arguments, missing prerequisites, or verification failures as network problems.

If the user supplied a local SSOT-CONTEXT checkout, use its `install.sh` with `SOURCE_DIR` set to that checkout instead of downloading another copy. The installer normally fetches the current `main` bundle; `--ref <branch-or-tag>` fetches another one, and `SOURCE_DIR` selects a local source. The two cannot be combined.

If the user requested both scopes, run the installation once for each scope and verify both locations. Installation does not create or migrate the target repository's `SSOT/`.

## 3. Verify the installed bundle

Read the actual target path from installer output and check that location. Replace the placeholder below with it:

```bash
ssot_skills_dir='<installed-skills-directory>'
for ssot_skill in ssot-preflight ssot-bootstrap ssot-closeout ssot-audit ssot-doctor ssot-skill; do
  test -f "$ssot_skills_dir/$ssot_skill/SKILL.md" || exit 1
  test -f "$ssot_skills_dir/$ssot_skill/agents/openai.yaml" || exit 1
done
# 4.x (the default): the checker must start.
python3 "$ssot_skills_dir/ssot-doctor/assets/scripts/ssot-check.py" --help >/dev/null
# v2 (installed with --ref v2-final) instead:
#   SSOT_TEST_PACKAGE_SHAPE_ONLY=1 bash "$ssot_skills_dir/ssot-doctor/assets/scripts/test/run-tests.sh"
```

Also inspect the installed bootstrap templates: they should use the selected language directly under `ssot-bootstrap/assets/templates/`, without `en/` and `zh/` subdirectories. Read the installed `ssot-preflight/SKILL.md` `metadata.protocol_version` and include it in the result.

These checks verify the installation, not the health of the user's repository documentation. Do not run an SSOT review or bootstrap as part of installation unless the user requested that work.

## 4. Wire the skills into the repo's agent-instructions file

The installer prints the `SSOT-CONTEXT:BEGIN` / `SSOT-CONTEXT:END` block from the selected-language bootstrap `adapter-thin.md` template. That template is the shared source for installation and later bootstrap; the skill protocols own the detailed behavior. Merge the printed block into the target repository's existing instructions; discovery alone does not establish when a skill should run. When upgrading an installation with `SSOT-SKILL:BEGIN` / `SSOT-SKILL:END` markers, replace that old block with the new one rather than appending a second block. A global-only installation without a target repository stops after verification and reports that each consuming repository still needs these instructions; it does not authorize editing global agent instructions.

Make clear that these are instructions for the agent: apply the skills automatically when their conditions match, without waiting for the user to name each skill. Users should be able to describe ordinary repository tasks after setup and restart. Explicit skill invocation remains an optional way to request a focused check or diagnose a missed trigger.

| Agent | Instruction entry |
|---|---|
| Claude Code | `CLAUDE.md` |
| Codex / OpenAI-style agents | `AGENTS.md` |
| Cursor | `.cursor/rules/ssot.mdc`, or the repository's existing `.cursorrules` |
| Windsurf | `.windsurf/rules/ssot.md`, or the repository's existing `.windsurfrules` |
| Gemini CLI | `GEMINI.md` |
| Other agents | Their supported repository-instruction entry |

Read existing instructions first. Follow any pointer or symlink to the repository's shared instruction owner, and update that one source. Keep one marked block in that owner so future updates can replace just this section. Reconcile older, unmarked SSOT instructions in place; preserve unrelated instructions and avoid duplicate blocks. Adapt the heading level if needed, preserving the routes and exceptions. Copy only the marked block from the template, not the template's surrounding explanation. When creating a tool-specific rules file, use that agent's supported activation format.

Before finishing, reread the resulting file and confirm it covers:

- automatic preflight for substantive work, immediate closeout capture of accepted durable decisions, and batch-end reconciliation, with bootstrap (only with the user's agreement) and doctor selected by their conditions;
- the skip cases for chat, pure command execution, and meaning-preserving typo/format edits, while explicit SSOT requests still route to a skill;
- loading the selected skill's full instructions, and reporting a missing skill honestly;
- for a 4.x installation, no leftover instructions from an older SSOT setup, such as running `$ssot-audit` for protocol lag, advancing `tracked_*` fields, or reading `STATUS.md` first (a v2 installation keeps those, and uses the block from its own `adapter-thin.md`);
- preserving existing project rules, user decisions, and commit/push authorization.

Do not copy or apply SSOT-CONTEXT's own `AGENTS.md` to the user's repository. It governs maintenance of the bundle source, including its release and commit conventions.

## 5. Report the result and restart step

Remove the temporary installer directory you created after verification. Report:

- the installed version, agent, scope, target path, and template language;
- the instruction file updated, or why its existing block already suffices;
- which installed-file checks passed;
- that the user must restart the agent session to load the skills and repository instructions, then can describe tasks as usual.

Explain that the agent handles the lifecycle: preflight before substantive work, an offer to bootstrap when `SSOT/` is missing or unfinished, immediate capture of accepted durable decisions through closeout, and reconciliation before finishing a substantive batch, with doctor used for checks and catch-up. Do not hand routine skill invocation back to the user as a manual checklist. Do not claim the skills are active before restart and discovery are confirmed. Do not ask the user to choose a global installation again after a successful project-only setup.

## Update or remove an existing installation

Resolve the target agent and scope as above. To update, use the downloaded installer:

```bash
# Update only the selected agent and scope.
# Omit --lang to preserve its installed template language.
bash "$ssot_install_dir/install.sh" --upgrade --agent "$ssot_agent" --scope "$ssot_scope"
```

To remove the installation instead:

```bash
bash "$ssot_install_dir/install.sh" --uninstall --agent "$ssot_agent" --scope "$ssot_scope" --yes
```

A scoped upgrade honors both `--agent` and `--scope`. Bare `--upgrade` scans every supported location in the current project and globally; use it only when that broader update was requested. Shared directories are updated once, and agents sharing a directory share the same installation.

After removal, verify the bundle files are absent. Preserve generated `SSOT/` documentation and unrelated skills. Reconcile obsolete trigger instructions with any remaining SSOT installation; the installer itself does not edit instruction files. Remove the temporary installer directory afterward.

After an update, repeat verification and reconcile the instruction block, then request a session restart. Installing new skill files never changes the repository's `SSOT/` by itself.

### Failed or interrupted replacement

Replacement is recoverable per installation location. The installer prepares the new bundle first, then keeps the previous skill directories and owned companions as backups until every replacement succeeds. An error before commit, or an INT/TERM cancellation, restores that location's previous installation. Locations already completed by a multi-location command remain updated. The lock prevents another install, upgrade or uninstall from modifying the same location while it is active; it does not make the separate directory moves invisible to concurrent readers.

If the error says **installation changes completed**, replacement already committed and only temporary-file or lock cleanup failed. Verify the complete installed bundle before cleaning the reported owned artifacts; a nonzero exit alone does not mean the old version is still installed.

If rollback cannot finish, or an installer is killed with SIGKILL, keep the reported recovery directory. Further operations refuse to overwrite pending recovery state. A regular `.ssot-skill-lock` file records the installer PID followed by its staging directory; that directory's `.ssot-transaction` records the installation location, PID and intended slots. The PID is a clue, not proof that the same process is still running. Establish that the owning installer has stopped before clearing its lock or recovering its files.

For an active recovery marker, work within the existing installation write authorization and preserve evidence:

1. Create an owned recovery directory on the same filesystem, for example with `mktemp -d "$ssot_skills_dir/.ssot-skill-recovered.XXXXXX"`. Read the transaction first and limit recovery to its SSOT skill/companion names. Leave unrelated skills, shared-root files and project memory alone.
2. Each entry in `.backup/` is a previous entry: move any current entry of the same name into the recovery directory, then rename the backup back into place. Preserve symlinks as links. If a slot has a `.touched/` marker but no `.had-old/` marker, it was absent before this attempt; move its current entry aside too. Untouched slots, and prior entries already restored without a remaining backup, stay in place. Stop if the saved state cannot account for a slot or a move fails; preserve the remaining files.
3. Verify the recovered previous bundle, language, companion ownership and shared instruction identity. Move the resolved transaction directory into the owned recovery directory, outside the scanned `.ssot-skill-install.*` names. Clear only a lock whose directory field still names that stopped transaction; another installer's lock stays. Retry the original command and verify the new installed files and integrations before removing the retained owned recovery artifacts.

Without an active transaction marker, staging may be from preparation or from a completed replacement whose cleanup failed. Inspect and verify the current installation; do not infer that it needs rollback merely because backup files exist. The installer never guesses that a lock is stale or discards another attempt's backups automatically. These steps recover filesystem replacement, not a consumer's SSOT migration or an intentionally cancelled uninstall.

### Check the transition, not only the new installation

Before replacing an older bundle, note its installed version and any repository instructions, hooks or scripts that call its tools. Afterward, verify those integrations against the files actually installed. A successful copy does not prove the old workflow still runs. Preserve the existing blocking/nonblocking behavior and run each changed command; do not substitute a health check for a migration operation or a Markdown reader.

| Transition | Required reconciliation |
| --- | --- |
| v2 memory → format 4 | With migration agreement, follow bootstrap section 7: extract unique ledger content, retain decisions and rule status, reconcile all instruction entries and inbound links, and replace retired tool calls before finishing. |
| v3 memory → format 4 | Follow bootstrap section 8, including instruction/tooling reconciliation. Keep existing owners and the review watermark; do not perform v2 ledger deletion merely because the bundle was old. |
| Protocol upgrade within format 4 | Verify installed tools and instruction wiring. Do not rewrite memory, advance a watermark or initiate history catch-up solely because the bundle version changed. |
| 4.3 reader → 4.4 or later | If local integration calls `ssot-preflight/assets/scripts/read-context.py`, replace that call with ordinary Markdown reads under preflight's current reading rules. `ssot-check.py` is a checker, not a reader replacement. No data-format migration is needed. |

The installer prints the current block but does not edit project instructions or callers. A marked block can be replaced in place; inspect unmarked legacy directives and shared instruction owners too. Preserve unrelated project rules and show proposed edits outside the block before applying them, within existing authorization. If the user requested only a bundle update, leave old-format memory unchanged and report migration as a separate step. An interrupted agreed migration resumes from `SSOT/BOOTSTRAP.md`, checking that record against the actual tree before continuing.

### Upgrading from 2.x or 3.x to 4.0

Version 4.0 uses `ssot_format: 4`: `SSOT/README.md` routes to maintained repository-local owners, including documents outside `SSOT/`. Explain the boundary before upgrading:

- Agents read v2 and v3 memory but do not write to it until the user agrees to migrate with `$ssot-bootstrap`. Installing skills never migrates consumer documents.
- A v3 migration preserves knowledge, invariant IDs and statuses, and existing owner paths. A v2 migration additionally extracts durable content before removing certification ledgers and repoints scripts using retired v2 tools. Preserve unique uncommitted material before removing anything; migration is one commit with no unrelated changes.
- Every installation that writes the repository must use v4 before migration; old v3 agents otherwise misread external-owner routes. To retain v3, choose a v3 release with `--ref`.
- Reconcile the instruction block and restart the session. Decision capture saves accepted durable confirmations, corrections, rejections, and scope limits immediately; batch closeout reconciles final behavior. Setup and catch-up inspect accessible project-related AI conversations, including later additions to existing threads, without putting private raw transcripts in the repository. Report inaccessible sources and examined ranges; commit watermarks do not certify conversation coverage. No automatic background collection or zero-omission guarantee is provided.

- To stay on v2 instead, upgrade with `--ref v2-final`, which installs the frozen last v2 release (2.86):

```bash
bash "$ssot_install_dir/install.sh" --upgrade --agent "$ssot_agent" --scope "$ssot_scope" --ref v2-final
```


## Project rename compatibility

SSOT-CONTEXT was previously named SSOT-SKILL. The six skill directory names remain stable, including the `ssot-skill` compatibility router, so existing prompts and installations continue to work. `SSOT_CONTEXT_REPO_URL` overrides the installer source; the legacy `SSOT_SKILL_REPO_URL` remains a fallback, and the new variable takes precedence when both are set. Installer lock, staging and companion ownership names retain their legacy spelling so upgrades still detect interrupted transactions and remove only companions they own. The project memory directory remains `SSOT/`.
