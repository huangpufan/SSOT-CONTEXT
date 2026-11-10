# Installer replacement and recovery evidence

The old installer deleted an installed skill directory before moving its replacement into place. A failed move then removed staging during exit cleanup, leaving neither the previous skill nor the candidate. This report covers the repair authorized during the [evolution review](../docs/evolution-review-2026-11-10.md). The installed skill protocol remains 4.5 and the consumer format remains 4.

## Result and ownership

`install.sh` now prepares a complete candidate, acquires a per-location lock and renames previous entries into a private backup directory before promotion. A transaction marker remains until every skill and owned companion has been replaced or retired. Pre-commit failure restores entries in reverse order; newly created slots are removed. INT and TERM use the same exit cleanup with cancellation status. A successful commit removes the marker before garbage collection, so a cleanup failure reports completed installation changes rather than reverting a fully applied bundle.

The temporary record owns only this filesystem operation. Prior-presence and touched-slot markers let a stopped transaction distinguish old entries from newly created ones. Failed compensation retains the remaining backups and refuses subsequent install/upgrade/uninstall at that location. SIGKILL cannot execute a trap, so its lock and transaction remain. The lock token retains its PID and directory even when a post-commit cleanup removes staging but cannot unlink the lock. No stale lock is guessed away. The [installation guide](../INSTALL.md#failed-or-interrupted-replacement) owns the operator/agent recovery steps.

This is per-location failure recovery, not simultaneous publication of all skill directories or an all-locations transaction. Concurrent readers do not acquire the mutation lock. Intentional uninstall is not given rollback semantics, but it refuses to destroy an active or pending installation transaction. Project memory and agent instruction files are outside this replacement operation.

## Executed cases

[test-installer-recovery.py](test-installer-recovery.py) invokes the real CLI using owned temporary sources, project and home. Two source generations carry different markers; complete new file hashes, permission bits, symlink targets and selected-language layout are compared with the source. Rollback compares the full prior installation, including directory modes and unrelated files. Every project path contains spaces and `[]` to exercise literal-path handling. Fault binaries intercept only selected `mv`/`rm` calls; signal cases target only the installer's owned child process. Injection markers are checked so a missing fault cannot count as success.

| Boundary or sequence | Observation |
| --- | --- |
| First promotion fails | Previous installation restored byte-for-byte; clean retry installs the complete new bundle. |
| Later promotion fails | Earlier promoted skills also return to their previous generation; retry succeeds. |
| Moving an old entry to backup fails | That original entry remains in place; earlier replacements roll back. |
| INT or TERM during promotion | Exit 130/143 and the previous installation restored. |
| Failed first installation | No partial bundle remains; unrelated files are unchanged. |
| Owned companion replacement fails | The old companion and all skills return. |
| Companion retired, then commit fails | Retirement is undone; successful retry retires it only at commit. |
| Old skill is a directory symlink | Rollback restores the link without changing its external target. |
| Unowned companion is a dangling symlink | Replacement refuses before mutation and preserves the link. |
| Restoring a backup fails | Old backup retained, rerun/upgrade/uninstall refuse without altering saved state; controlled recovery restores the old bundle and retry succeeds. |
| Removing a new entry during compensation fails | Both old backup and new target remain; controlled recovery preserves the new entry separately and restores the old bundle. |
| SIGKILL after a backup rename | Exit -9, backup and transaction retained, even with the primary skill absent; upgrade reports recovery state, then controlled recovery and retry succeed. |
| Post-commit staging cleanup fails | New bundle is complete, the lock is released, retained backups are not silently discarded by a later successful upgrade. |
| Post-commit lock cleanup fails | New bundle is complete; the lock retains owner metadata, blocks a rerun, and an explicitly verified stopped owner can be cleared before retry. |
| Another installer enters an active location | Second command refuses, the paused transaction is unchanged, and the first completes after release. |
| Uninstall enters an active location | Same refusal and unchanged-state check; the first installer completes. |
| Successful scoped upgrade | Selected Chinese templates stay flat; unrelated skill and shared-root content stay unchanged. |

The eighteen tests cover these boundaries; their number is not a coverage denominator. The continuous failure → restore → retry and incomplete recovery → refusal → controlled recovery → retry paths observe the actual installed files, not only exit status. Linux execution uses Bash 5.2.21 and Python 3.12.3. Both Linux and macOS CI run the same suite, with Homebrew Bash selected explicitly on macOS.

## Baseline, producer repairs and scope

The three original symptom tests were also run against `install.sh` exported from `146beb8`: both promotion-failure tests fail because the previous installation is not restored, and the dangling-companion test fails because the unowned link is replaced. All three run against the same temporary current source fixtures, isolating the installer implementation. Exporting the baseline does not modify the working tree:

```bash
baseline_dir=$(mktemp -d)
git show 146beb8:install.sh > "$baseline_dir/install.sh"
SSOT_TEST_INSTALLER="$baseline_dir/install.sh" python3 tests/test-installer-recovery.py \
  RecoveryTest.test_first_promotion_failure_restores_every_previous_file \
  RecoveryTest.test_later_promotion_failure_restores_already_replaced_skills \
  RecoveryTest.test_unowned_dangling_companion_link_is_never_replaced
```

Two initial fault modes accidentally fired during promotion instead of at commit/cleanup. The fault producer now gates each mode to its named seam, and the tests check the recorded seam. A new-source checksum check also initially assumed the recreated template directory must have the source directory's permission bits; the existing installer correctly follows the caller's umask there. The final oracle checks directory presence and all new file bytes/modes, while rollback still checks prior directory modes. No user permission policy was changed to satisfy the test.

The restricted-PATH fetched-source e2e fixture now includes standard `ln` and `cat`, preserving its actual purpose of excluding GNU `timeout`. Recovery scanning quotes the literal directory prefix instead of sending a project path containing `[]` through an unescaped glob pattern. A regression first observed the missing recovery-path diagnostic and now passes.

Remote commit `146beb8` was fast-forwarded before implementation. Its checker-budget setting remains 50 KiB. Its duplicate test method was observed being silently overwritten by unittest; a source-level uniqueness regression failed before deduplication and now passes. The changelog's unsupported 1,712-byte checker-growth claim is corrected: no checker implementation changed in that commit or this repair.

Local validation runs the eighteen recovery cases, 108 existing installer checks, 119 checker regressions, 48 bundle checks, fifteen continuity/migration self-tests, ten reading-benchmark self-tests, shell/Python syntax and ShellCheck. Exact pushed-commit CI remains a separate publication gate. These filesystem tests do not establish arbitrary power-loss recovery, protection against non-cooperating external writers, whole-host deployment, or model compliance with every prose instruction. No new billable model runs were needed for this installer repair.
