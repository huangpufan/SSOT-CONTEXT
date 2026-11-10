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

- A Bash installer (`install.sh`) that copies skill bundles into an agent's config directory and may shell out to `git`, `curl`, and standard POSIX utilities.
- Test scaffolding under `tests/` and the read-only checker (`ssot-check.py`).
- Markdown protocol documents and templates under `skills/`.

The bundle does not run a long-lived service. The realistic attack surface is therefore the installer and the shell scripts it invokes. When reporting or reviewing a vulnerability, please flag any path in the installer that:

- Executes downloaded or templated content without integrity checks.
- Expands untrusted input into a shell command (`eval`, unquoted variables, command substitution from network sources).
- Writes outside the user-selected install target.

Markdown-only changes (protocols, templates, references) are generally out of scope unless they instruct an agent to take a destructive action without confirmation.
