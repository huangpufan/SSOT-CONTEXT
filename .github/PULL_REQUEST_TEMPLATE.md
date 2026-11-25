## Summary

## Scope of change
- [ ] Installer (`install.sh`)
- [ ] Skill protocol (`skills/*/SKILL.md`)
- [ ] Reference docs (`skills/*/references/`)
- [ ] Templates (`skills/ssot-bootstrap/assets/templates/`)
- [ ] Bundle scripts (`skills/*/assets/scripts/`) or standalone tools (`tools/`)
- [ ] Tests / CI
- [ ] Docs (`README*`, `AGENTS.md`, `CHANGELOG.md`)

## Verification
- [ ] `bash tests/test-bundle-shape.sh` passes (shape, links/anchors, hygiene, and budgets)
- [ ] Relevant suites from `CONTRIBUTING.md#local-verification` pass (checker, context/benchmark, `tools/`, installer, and `shellcheck`)
- [ ] Protocol changes name the agent failure they fix and what they replace (`CONTRIBUTING.md`)
- [ ] If protocol changed, `VERSION` and `skills/ssot-preflight/SKILL.md` `metadata.protocol_version` are aligned
- [ ] Bilingual templates (`en/` + `zh/`) stay in file-name and structural parity if templates touched
- [ ] README reconciliation assessed (`CONTRIBUTING.md#readme-reconciliation`); `README.md` and `README.zh.md` updated together when user-facing behavior changed
- [ ] CHANGELOG entry added under `[Unreleased]` (Keep a Changelog style)

## Related issues
Closes #
