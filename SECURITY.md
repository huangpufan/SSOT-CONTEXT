# Security Policy

## Supported Versions

The current `main` branch is the only supported version. Tagged releases on `main` track the bundle's `VERSION` file; fixes land on `main` and are picked up by re-running the installer.

| Version       | Supported |
| ------------- | --------- |
| `main` (HEAD) | Yes       |
| Older tags    | No        |

## Reporting a Vulnerability

Please **do not** file public GitHub issues for security reports.

Email: huangpufan.cn@gmail.com

You can expect an acknowledgement within 48 hours. After triage we will coordinate a fix, a disclosure window, and (when appropriate) a CVE.

## Threat Surface

SSOT-CONTEXT ships:

- A Bash installer (`install.sh`) that copies skill bundles into an agent's config directory, shells out to `git`, `curl`, and standard POSIX utilities, and—only when explicitly invoked with `--sync-block <file>`—replaces the `SSOT-CONTEXT:BEGIN` / `SSOT-CONTEXT:END` block in the user-specified instruction file.
- Bundle Python scripts under `skills/ssot-doctor/assets/scripts/`: the read-only structural checker (`ssot-check.py`) and the opt-in POSIX source adapter (`context-source.py`), which persists connector metadata/receipts and enforces withdrawal boundaries.
- Opt-in repository tools under `tools/`: `tools/link-local.py` (replaces explicitly selected skill directories with symlinks to a local checkout while moving originals into a backup directory) and `tools/ssot-precommit.sh` (a Git pre-commit hook that checks staged index snapshots via `ssot-check.py`).
- Test scaffolding under `tests/` and Markdown protocol documents and templates under `skills/`.

The bundle does not run a long-lived service. The realistic attack surface is therefore the installer, bundle scripts, and repository tools (`install.sh`, `skills/*/assets/scripts/*.py`, and `tools/*`). When reporting or reviewing a vulnerability, please flag any path that:

- Executes downloaded or templated content without integrity checks, or expands untrusted input into a shell command (`eval`, unquoted variables, command substitution from network sources).
- Writes outside the user-selected install target (or outside the marked instruction block passed to `--sync-block`, the explicit `--state` path passed to `context-source.py`, or the explicit `--base`/`--backup-root` paths passed to `tools/link-local.py`).
- Follows symlinks or traverses paths outside the authorized repository/space boundary to read restricted/withdrawn sources or modify unrelated files.

Download integrity note: piping remote scripts over HTTPS trusts the serving origin. Where network access to `raw.githubusercontent.com` is blocked, third-party mirrors such as the `gh-proxy.com` fallback noted in `INSTALL.md` introduce an additional third-party proxy in the download path; security-sensitive environments should inspect a pinned Git checkout locally and install with `SOURCE_DIR` instead of executing scripts fetched through a third-party mirror.

Markdown-only changes (protocols, templates, references) are generally out of scope unless they instruct an agent to take a destructive action without confirmation or bypass a restricted-source / permission boundary.
