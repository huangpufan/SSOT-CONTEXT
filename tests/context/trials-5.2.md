# Entry discovery and withdrawal evidence for 5.2

Version 5.2 repairs checker format precedence, source withdrawal reporting and retry history. It also documents an observed installation boundary. Two proposed entry-resolution rules were tested and withdrawn because they did not meet their acceptance criterion. This report retains those failed proposals; it does not claim that final 5.2 makes agents resolve nested entries more reliably.

## Actual installation and cold entry

The official local-source installer used frozen 5.1 (`d34aca5`) in the existing mixed format-5 parent / format-4 child fixture. Codex 0.167.1 `debug prompt-input` showed the project skills at the mono root, but no skills or parent instructions when launched at the independent child Git root or its `src/`. Child instructions were present. Installing at the authorized child root restored the catalog; its instruction file retained both local and parent context routes. A non-Git nested launch likewise did not discover ancestor-only installation/instructions; that attempt stopped at its zero-model probe. Wiring and installing at its intended launch scope restored discovery without creating Git or a parallel SSOT.

A fresh `gpt-6.1-terra` session at the child `src/` completed an independent variable rename and preserved the payment identity protection. It initially read relative parent/local entries against the current directory, failed, then recovered to the correct owners. The actual host prompt wrapped the inherited child AGENTS content as “instructions for” the launch `src/`, losing its declaring-file location. This is a host-information boundary as well as an instruction interpretation problem.

The first candidate added an instruction-relative/repository-root sentence to four skill entry guards. A second made absolute-path resolution an explicit first action. Both still performed wrong-base entry reads. Neither caused an unsafe payment change; neither met the stated routing criterion. Both clauses were removed, rather than declaring success from correct final code or adding more unproven instructions. The candidate's named non-Git control and its baseline both read the accepted method and produced two actionable checklist items: do not collect names, and retain supporting as well as contradictory observations. Existing context stayed unchanged. Typo model controls were not run after the proposed broad rule was withdrawn.

| Observation | Seconds | Native input + output tokens | Result |
| --- | ---: | ---: | --- |
| Initial child, 5.1 | 47.995 | 188204 | Correct final task; wrong-base reads recovered |
| First path clause | 49.000 | 188739 | Same routing criterion failed |
| Same-fixture baseline for second clause | 46.231 | 186563 | Correct final task; wrong-base reads recovered |
| Second path clause | 48.401 | 189508 | Same routing criterion failed |
| Named non-Git baseline | 27.322 | 91521 | Correct checklist, context preserved |
| Named non-Git second clause | 33.704 | 92702 | Correct checklist, context preserved |

All six completed native turns identify `gpt-6.1-terra`, medium reasoning. Cached input is included in the token figures; these are not billing estimates. One observation per variant is no population reliability or performance estimate. Only the second child pair used the same configured parent/child installation languages. Full-workspace snapshots establish changes; the inherited recorder's own `changed_paths` only covers its launch subdirectory and would miss the parent-owned code edit. The [machine inventory](results/context-evolution-5.2-2026-11-12.json) retains identities, raw-artifact hashes, usage and these limits. Raw probes and runs remain under `/tmp/ssot-r2-child-discovery` and `/tmp/ssot-evolution-20261112-r2`.

## Public tool boundaries

- A format-6 or vendor-format entry alongside `STATUS.md` previously produced a migration-to-4 recommendation. Current checks reject that classification while retaining markerless v2 and explicit v3 migration recognition. The checker remains read-only, verified by the existing filesystem-digest harness.
- After completing source capture, moving an owner without rebinding leaves a known old reference. Withdrawal now succeeds immediately, preserves that reference and reports the missing current binding through `unavailable_owners`; it neither invents the new path nor scans unbound files. Later source inspection remains blocked.
- Repeating withdrawal keeps its original reason, but re-observes current availability. A missing unused declared target still permits a justified `no-update`: unavailability is not fabricated evidence of a derived record. Public subprocess tests cover these distinct transitions.

These are tool repairs and installation evidence, not proof that a source marker establishes semantic correctness or that all derived copies are discoverable. The next benchmark redesign requested by the user will examine the exposed observation and task-coverage limits before further SSOT optimization.
