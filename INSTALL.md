# Install Guide (Agent-facing)

Use this guide when a user asks you to install or reinstall SSOT-CONTEXT in a **target repository or explicitly selected context workspace**. Preserve existing instructions and respond in the user's language. General context setup does not require Git; installer fetching prerequisites and the optional POSIX source CLI are separate from that data model.

For a new installation, finish the setup: install the bundle, verify the installed files, and merge the lifecycle instructions. Skill discovery is confirmed only after the agent session restarts. For updates, removal, local symlinks, troubleshooting, interrupted-install recovery, or 2.x/3.x migration, read [the maintenance and recovery guide](docs/2026-11-24-install-maintenance.md) instead of reading the fresh-install steps below.

## 1. Resolve the installation choices

Honor options the user already supplied. Otherwise use these defaults without asking them to reconfirm:

- **Agent:** the coding agent you are currently running as. Pass its canonical installer key explicitly; a machine may have several agents installed.
- **Scope:** `project` by default; use `global` for an explicit global-only request. For repositories that use Git worktrees or multiple clones, recommend `--scope global` (or gitignoring project skill directories such as `.agents/skills/` and `.claude/skills/`), because Git-tracked project copies can leave other worktrees stuck on older skill versions. When agents launch from a monorepo root above a nested subproject `SSOT/`, install skills at the monorepo root (or `--scope global`) and point to the subproject entry from root instructions; project skills installed only inside a subdirectory are missed when sessions start at the monorepo root. Install in both locations only when the user requests both. Run project commands from the target repository root.
- **Template language:** keep the repository's existing choice (`language` in `SSOT/README.md` front matter, `documentation_language` of an older `SSOT/STATUS.md`, or the installed template language on reinstall). For a new setup, use `zh` when the user is communicating in Chinese, otherwise `en`. A template choice never changes the language an existing SSOT is written in.
- **Version:** the current release from `main`. Add `--ref v2-final` only when the user wants to stay on the frozen v2 protocol.

If the target repository or agent identity cannot be determined from the current session, ask for that missing information. Routine defaults do not need a separate approval step.

Common keys and project locations (for other agents or global locations, run `install.sh --list-agents`; for Antigravity legacy global paths, see [Antigravity surface locations](docs/2026-11-24-install-maintenance.md#antigravity-surface-locations)):

| Current agent | Key | Project skills directory |
|---|---|---|
| Claude Code | `claude-code` | `.claude/skills/` |
| Codex | `codex` | `.agents/skills/` |
| Cursor | `cursor` | `.agents/skills/` |
| Windsurf | `windsurf` | `.windsurf/skills/` |
| Gemini CLI | `gemini-cli` | `.agents/skills/` |
| Antigravity App / shared App and CLI setup | `antigravity-app` (alias `agy`) | `.agents/skills/` |
| Standalone Antigravity IDE | `antigravity` | `.agents/skills/` |
| Antigravity CLI with its legacy global location | `antigravity-cli` | `.agents/skills/` |
| GitHub Copilot | `github-copilot` | `.agents/skills/` |
| DeepSeek Harness (`dsh`) | `dsh` | `.dsh/skills/` (global: `~/.dsh/skills/` or `$DSH_HOME/skills`) |

## 2. Install the bundle

Check that Bash 4+, `git`, `curl`, and `python3` are available. On macOS, use Homebrew Bash (`"$(brew --prefix)/bin/bash"`). Download the installer to a temporary directory so a failed download cannot look like a successful installation, replace the placeholders, and run:

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
bash "$ssot_install_dir/install.sh" --quickstart \
  --agent "$ssot_agent" --scope "$ssot_scope" --lang "$ssot_template_lang"
```

Check download and installer exit codes separately, preserve stderr, and report the specific failure. If download fails for network reasons, retry with `https://gh-proxy.com/https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh` and pass `--allow-mirror` (or `SSOT_ALLOW_MIRROR=1`) if GitHub clone also needs the mirror (`gh-proxy.com` is an opt-in third-party mirror, disabled by default; inspect the downloaded script before executing it when supply-chain integrity matters, or fetch from a local GitHub checkout; see [SECURITY.md](SECURITY.md)). If the user supplied a local checkout, run its `install.sh` with `SOURCE_DIR` set to that checkout (`SOURCE_DIR` and `--ref` cannot be combined). Installation does not create or migrate the target repository's `SSOT/`.

## 3. Verify the installed bundle

Read the actual target path from installer output and check that location:

```bash
ssot_skills_dir='<installed-skills-directory>'
for ssot_skill in ssot-preflight ssot-bootstrap ssot-closeout ssot-doctor; do
  test -f "$ssot_skills_dir/$ssot_skill/SKILL.md" || exit 1
  test -f "$ssot_skills_dir/$ssot_skill/agents/openai.yaml" || exit 1
done
python3 "$ssot_skills_dir/ssot-doctor/assets/scripts/ssot-check.py" --help >/dev/null
```

Fresh installations copy only the four lifecycle skills above so new workspaces avoid always-loaded catalog overhead from legacy compatibility shims (`ssot-audit`, `ssot-skill`). Pass `--with-legacy-shims` if older prompts invoke those names; `--upgrade` preserves them automatically when already present. Confirm templates are flattened into the selected language directly under `ssot-bootstrap/assets/templates/` (without `en/` and `zh/` subdirectories) and read `metadata.protocol_version` from the installed `ssot-preflight/SKILL.md`. Do not run an SSOT review or bootstrap as part of installation unless the user asked for it.

## 4. Wire the skills into the repo's agent-instructions file

The installer prints the `SSOT-CONTEXT:BEGIN` / `SSOT-CONTEXT:END` block from the selected-language `adapter-thin.md` template without editing your files. Merge the block into the target repository's existing instructions; discovery alone does not establish when a skill should run. A global-only installation without a target repository stops after verification and does not edit global instructions. If the file already carries a managed `SSOT-CONTEXT` or legacy `SSOT-SKILL` block, you can check and refresh only that block with `bash "$ssot_install_dir/install.sh" --check-block <file>` and `--sync-block <file>` (offline lookup follows file-to-agent affinity, honors optional `--agent <key>` / `--scope <project|global>`, warns on version skew across installed agents, and refuses to silently downgrade a block that already matches a newer installed copy).

**Choose the block first** from what is already in the target (entry front matter, existing SSOT blocks, instruction files, top-level README and layout; do not search outside the target):

- **Existing marked entry: no question.** `ssot_format: 4` or a v2/v3 `SSOT/` uses `adapter-thin.md` (migration stays separate). `ssot_format: 5` uses `context-adapter.md` with that entry.
- **No entry, clearly software: no question.** Build manifests, source code and tests with no contrary signal use `adapter-thin.md`.
- **No entry, otherwise: ask one question before editing.** Ask when the folder looks like a registry, notes, research, creative work, life domain or organization, has no Git repository or almost only prose, or has conflicting signals. Recommend a mode, name the signals, the entry path and every file outside the marked block you would change.

For a general space, use the installed selected-language `context-adapter.md`, replacing `ENTRY` with the agreed entry. The agreement also covers the minimum valid entry (`ssot_format: 5`, `language`, writer requirement sentence and invariants section from `context-readme.md`), preserving existing content and running `ssot-check.py` against the entry. If the user declines both modes, leave the skills installed and edit no instruction file.

| Agent | Instruction entry |
|---|---|
| Claude Code | `CLAUDE.md` |
| Codex / OpenAI-style agents | `AGENTS.md` |
| Cursor | `.cursor/rules/ssot.mdc`, or existing `.cursorrules` |
| Windsurf | `.windsurf/rules/ssot.md`, or existing `.windsurfrules` |
| Gemini CLI | `GEMINI.md` |
| Antigravity App / CLI / IDE | Existing `AGENTS.md`, `GEMINI.md`, or supported project rules pointing to that owner |
| GitHub Copilot | `.github/copilot-instructions.md` |
| DeepSeek Harness (`dsh`) | `AGENTS.md` |
| Other agents | Their supported repository-instruction entry |

Read existing instructions first, follow any symlink/pointer to the shared instruction owner, keep one ordered marked block, preserve unrelated instructions, and copy only the marked block (never copy SSOT-CONTEXT's own `AGENTS.md`). Reread the resulting file to verify it covers automatic preflight, immediate closeout capture, batch reconciliation, skip cases (chat, pure commands, typos), honest missing-skill reporting, and no leftover v2 directives.

## 5. Report the result and restart step

Remove the temporary installer directory after verification. Report the installed version, agent, scope, target path, template language, the instruction file updated, which installed-file checks passed, and that the user must restart the agent session to load the skills and instructions. Make clear that the agent applies the lifecycle automatically once restarted; do not hand routine skill invocation back to the user as a manual checklist, and do not claim skills are active before restart and discovery are confirmed.

## When a skill appears unavailable

See [troubleshooting and child-repository discovery](docs/2026-11-24-install-maintenance.md#when-a-skill-appears-unavailable).

## Link local installations to one checkout

See [local symlink setup with `tools/link-local.py`](docs/2026-11-24-install-maintenance.md#link-local-installations-to-one-checkout).

## Update or remove an existing installation

Run `install.sh --upgrade --agent <key> --scope <project|global>` (or `--uninstall ... --yes`), then check and refresh the repository's managed instruction block with `install.sh --check-block <file> [--agent <key> --scope <project|global>]` and `--sync-block <file>`—using a local checkout, a freshly downloaded copy as in step 2, or `curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- <flags>`. Full procedures and transition rules are in [update, removal, and transitions](docs/2026-11-24-install-maintenance.md#update-or-remove-an-existing-installation).

## Failed or interrupted replacement

See [interrupted replacement and SIGKILL lock recovery](docs/2026-11-24-install-maintenance.md#failed-or-interrupted-replacement).

## Upgrading from 2.x or 3.x to 4.0

See [2.x / 3.x upgrade boundaries and `--ref v2-final`](docs/2026-11-24-install-maintenance.md#upgrading-from-2x-or-3x-to-40).

## Project rename compatibility

SSOT-CONTEXT was previously named SSOT-SKILL; existing installations and `--upgrade` preserve the `ssot-audit` and `ssot-skill` compatibility shims automatically (fresh installs omit them by default and accept `--with-legacy-shims` if needed), and legacy installer markers remain compatible. See [rename compatibility details](docs/2026-11-24-install-maintenance.md#project-rename-compatibility).
