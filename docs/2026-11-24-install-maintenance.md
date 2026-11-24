# Installation Maintenance, Symlinks, Recovery, and Legacy Upgrades

This reference holds the operational procedures moved out of [INSTALL.md](../INSTALL.md) so fresh installations stay short and cheap. Keep using [INSTALL.md](../INSTALL.md) for a new installation and initial instruction wiring.

## Antigravity surface locations

Antigravity surfaces share the project path (`.agents/skills/`). The App key (`antigravity-app`, alias `agy`) uses `~/.gemini/config/skills`, the current shared App/CLI/IDE global location. Existing `antigravity` and `antigravity-cli` keys retain the legacy global locations supported by the standalone IDE and CLI respectively; the App does not consume those legacy locations. This preserves scoped upgrades and uninstalls of existing installations. Choose the key for the actual surface and inspect existing copies before a global change; installing to a new location does not migrate or remove an old one. Compare discovered versions in a fresh session when multiple locations exist. See [Google's skill locations](https://antigravity.google/docs/skills). A project-only request does not authorize changing machine-wide installations.

## When a skill appears unavailable

Check the actual workspace and agent surface, the installed path (including symlink resolution), then a fresh session's skill catalog and an actual read of the selected `SKILL.md` and protocol version. A file check alone proves neither discovery nor execution; a model's claim to have used a skill needs a matching read or load receipt. If the catalog contains the skill but it was not selected, inspect the instruction route and request trigger before adding another copy. If new files are absent from an old session, start a new conversation in the intended workspace. Antigravity CLI also documents `/skills reload`; in the App, `/ssot-doctor` explicitly selects a focused review. Ordinary requests should still select the appropriate skill automatically.

For an authorized workspace with independently launched child repositories, check discovery from each intended launch root. A parent installation and a link to parent context are separate: in Codex, project skills installed only above a child's Git root were absent from child-start sessions. Use an existing visible global installation or install at the authorized child root, and retain the child's instruction routes to its own and relevant parent context. Do not assume directory nesting makes either skills or parent instructions visible, or install into unrelated children. See the [child-start evidence](../tests/context/trials-5.2.md).

## Link local installations to one checkout

Use this only when the user wants local installations to follow a persistent source checkout. Changes and new files in that checkout become visible through the links immediately; already loaded sessions still need refresh or restart. It does not fetch remote changes in the background. Keep the source checkout in place and keep frozen trial bundles as independent copies.

`tools/link-local.py` replaces only the six named SSOT skill directories in explicitly selected existing installations. It preserves surrounding skill-directory symlinks and unrelated skills, deduplicates shared locations, and moves originals into a required external backup directory with a recovery manifest. It refuses source replacement, unknown skill owners, changes since planning and cross-filesystem backup moves. A normal failure restores touched originals; after a process kill, inspect the saved manifest and originals before resuming. Backups can contain local modifications and should stay private.

Run from the persistent SSOT-CONTEXT checkout. Repeat `--base` for additional **actual** agent skills directories; inventory and distinguish source checkouts, active installations and historical/generated trial snapshots before selecting them:

```bash
python3 tools/link-local.py --base /path/to/project/.agents/skills
python3 tools/link-local.py --base /path/to/project/.agents/skills \
  --apply --backup-root /path/to/private/ssot-installation-backups
```

The first command only prints a plan. Links point directly to the checkout's skill directories, including both `assets/templates/en/` and `assets/templates/zh/`; choose the consumer's declared documentation language when using those templates. This avoids a second generated copy that can become stale. Verify link targets, tools, template reads and a fresh agent session after conversion. A local source edit through any linked installation changes the shared source; maintain skill changes in that owner.

A linked installation applies to the paths you selected. A separate Git worktree can still get older tracked copies of the same skills from its checked-out commit. Verify the installation from the worktree where the agent will actually start, including the version it opens. Because linked skills advance automatically while copied `SSOT-CONTEXT:BEGIN/END` blocks in `AGENTS.md` or `CLAUDE.md` do not, run `bash install.sh --check-block <file>` and `--sync-block <file>` after pulling new releases.

If installed copies are tracked by Git, conversion appears as deleted tracked files and new directory links. Agree whether the links are local-only or part of the repository's distribution before committing them. Do not hide changes with index flags or push machine-dependent paths without authorization. To restore a local-only conversion, use its exact saved paths and originals; do not reset unrelated work.

## Update or remove an existing installation

For an installation already linked to a persistent local checkout, update that checkout instead of running the copy installer. Repoint it with the local-link command above if its source moved. The normal installer still produces independent copies and can replace links when explicitly used to reinstall; do not silently change an agreed live installation back to copies.

Resolve the target agent and scope as in [INSTALL.md](../INSTALL.md#1-resolve-the-installation-choices). To update, use the downloaded installer:

```bash
# Update only the selected agent and scope.
# Omit --lang to preserve its installed template language.
bash "$ssot_install_dir/install.sh" --upgrade --agent "$ssot_agent" --scope "$ssot_scope"

# Check and refresh only the managed SSOT-CONTEXT:BEGIN/END block in place (supports formats 4 and 5):
bash "$ssot_install_dir/install.sh" --check-block AGENTS.md
bash "$ssot_install_dir/install.sh" --sync-block AGENTS.md
```

To remove the installation instead:

```bash
bash "$ssot_install_dir/install.sh" --uninstall --agent "$ssot_agent" --scope "$ssot_scope" --yes
```

A scoped upgrade honors both `--agent` and `--scope`. Bare `--upgrade` scans every supported location in the current project and globally; use it only when that broader update was requested. Shared directories are updated once, and agents sharing a directory share the same installation.

After removal, verify the bundle files are absent. Preserve generated `SSOT/` documentation and unrelated skills. Reconcile obsolete trigger instructions with any remaining SSOT installation; `--upgrade` and `--uninstall` never edit instruction files on their own. Remove the temporary installer directory afterward.

After an update, check the worktree where the agent will start. Read back the resolved preflight file and its protocol version, the entry named by the project's instructions, and the marked block in the actual instruction owner. A linked skill can advance while that block still uses older wording. Use `--check-block <file>` to verify whether the managed block matches the installed release, and `--sync-block <file>` (adding `--entry <path>` only if a custom format-5 block cannot be auto-parsed) to replace only the marked section while preserving all other text and symlinks. Preserve custom instructions with equivalent behavior. [Reconcile an outdated block](../INSTALL.md#4-wire-the-skills-into-the-repos-agent-instructions-file) within the requested installation scope.

Restart and verify discovery. When checking reading behavior, use an ordinary task in that worktree and inspect its first entry read and its answer. For substantive work outside the bounded route, preflight starts from the entry's header and headings (which may be read in the same step as the selected `SKILL.md` before opening linked sources). A bounded lookup checks the current entry's ownership and permissions before reading its owner. A single approved prose change goes directly to closeout after those checks. A catalog listing alone cannot show that order.

## Failed or interrupted replacement

Replacement is recoverable per installation location. The installer prepares the new bundle first, then keeps the previous skill directories and owned companions as backups until every replacement succeeds. An error before commit, or an INT/TERM cancellation, restores that location's previous installation. Locations already completed by a multi-location command remain updated. The lock prevents another install, upgrade or uninstall from modifying the same location while it is active; it does not make the separate directory moves invisible to concurrent readers.

If the error says **installation changes completed**, replacement already committed and only temporary-file or lock cleanup failed. Verify the complete installed bundle before cleaning the reported owned artifacts; a nonzero exit alone does not mean the old version is still installed.

If rollback cannot finish, or an installer is killed with SIGKILL, keep the reported recovery directory. Further operations refuse to overwrite pending recovery state. A regular `.ssot-skill-lock` file records the installer PID followed by its staging directory; that directory's `.ssot-transaction` records the installation location, PID and intended slots. The PID is a clue, not proof that the same process is still running. Establish that the owning installer has stopped before clearing its lock or recovering its files.

For an active recovery marker, work within the existing installation write authorization and preserve evidence:

1. Create an owned recovery directory on the same filesystem, for example with `mktemp -d "$ssot_skills_dir/.ssot-skill-recovered.XXXXXX"`. Read the transaction first and limit recovery to its SSOT skill/companion names. Leave unrelated skills, shared-root files and project memory alone.
2. Each entry in `.backup/` is a previous entry: move any current entry of the same name into the recovery directory, then rename the backup back into place. Preserve symlinks as links. If a slot has a `.touched/` marker but no `.had-old/` marker, it was absent before this attempt; move its current entry aside too. Untouched slots, and prior entries already restored without a remaining backup, stay in place. Stop if the saved state cannot account for a slot or a move fails; preserve the remaining files.
3. Verify the recovered previous bundle, language, companion ownership and shared instruction identity. Move the resolved transaction directory into the owned recovery directory, outside the scanned `.ssot-skill-install.*` names. Clear only a lock whose directory field still names that stopped transaction; another installer's lock stays. Retry the original command and verify the new installed files and integrations before removing the retained owned recovery artifacts.

Without an active transaction marker, staging may be from preparation or from a completed replacement whose cleanup failed. Inspect and verify the current installation; do not infer that it needs rollback merely because backup files exist. The installer never guesses that a lock is stale or discards another attempt's backups automatically. These steps recover filesystem replacement, not a consumer's SSOT migration or an intentionally cancelled uninstall.

## Check the transition, not only the new installation

Before replacing an older bundle, note its installed version and any repository instructions, hooks or scripts that call its tools. Afterward, verify those integrations against the files actually installed. A successful copy does not prove the old workflow still runs. Preserve the existing blocking/nonblocking behavior and run each changed command; do not substitute a health check for a migration operation or a Markdown reader.

| Transition | Required reconciliation |
| --- | --- |
| v2 memory → format 4 | With migration agreement, follow bootstrap section 7: extract unique ledger content, retain decisions and rule status, reconcile all instruction entries and inbound links, and replace retired tool calls before finishing. |
| v3 memory → format 4 | Follow bootstrap section 8, including instruction/tooling reconciliation. Keep existing owners and the review watermark; do not perform v2 ledger deletion merely because the bundle was old. |
| Protocol upgrade within format 4 | Verify installed tools and refresh the managed instruction block (`--check-block` / `--sync-block`). Do not rewrite memory, advance a watermark or initiate history catch-up solely because the bundle version changed. |
| Bundle 5.0+ with existing development format 4 | Keep format 4, its owners and normal authorized writing. No format-5 conversion is required. |
| Explicit new general space or agreed generalization to format 5 | Preserve owners/content, use the general adapter with the actual entry, require known writers to upgrade or remain discoverably read-only, and validate source/record semantics. Do not downgrade to satisfy an older checker. |
| 4.3 reader → 4.4 or later | If local integration calls `ssot-preflight/assets/scripts/read-context.py`, replace that call with ordinary Markdown reads under preflight's current reading rules. `ssot-check.py` is a checker, not a reader replacement. No data-format migration is needed. |

For unfinished general spaces sharing a directory, use 5.8+ for participating writers. Older 5.x writers may attribute a neighboring `BOOTSTRAP.md` to the wrong entry. An existing, clearly identified single-space checkpoint can be resumed in place.

[Selected-file checks](../skills/ssot-preflight/references/source-retention.md#selected-mechanical-checks) require the 5.9+ checker for format-5 spaces or 5.10+ for format-4 repositories. With an older installation, check the permitted files manually or upgrade before running Doctor over restricted routes.

Normal install and upgrade commands print the current block without editing project instructions or callers; use `--sync-block <file>` when you explicitly want to replace a marked block in place, and inspect unmarked legacy directives and shared instruction owners too. Preserve unrelated project rules and show proposed edits outside the block before applying them, within existing authorization. If the user requested only a bundle update, leave old-format memory unchanged and report migration as a separate step. An interrupted agreed migration resumes from `SSOT/BOOTSTRAP.md`, checking that record against the actual tree before continuing.

## Upgrading from 2.x or 3.x to 4.0

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

SSOT-CONTEXT was previously named SSOT-SKILL. The six skill directory names remain stable, including the `ssot-skill` compatibility router, so existing prompts and installations continue to work. `SSOT_CONTEXT_REPO_URL` overrides the installer source; the legacy `SSOT_SKILL_REPO_URL` remains a fallback, and the new variable takes precedence when both are set. Installer lock, staging and companion ownership names retain their legacy spelling so upgrades still detect interrupted transactions and remove only companions they own. Development memory keeps `SSOT/`; a general space can retain its explicitly wired entry and current owners.
