# General context direction and implementation boundary

## Accepted direction and delivery boundary

On 2026-11-10 the user approved extending SSOT-CONTEXT from development memory to maintaining bounded long-term context for repositories, research, creation, personal domains and organizations. The question answered was the coordinator's complete general-context proposal: preserve development ability while extending spaces/owners, content types, source-integration continuity, forgetting semantics and the acceptance route. The user answered: “同意，请你推进具体的落地吧。同样，调用 6.1sol 具体做全部执行，过程中，你只做具体的任务分发以及检查，决策和 review。然后调用其他的前面提到的模型帮你 review。持续推进落地直到完全符合预期。” The coordinator directly checked this exchange in the present conversation and forwarded the necessary question/answer to the implementation agent. This records the supplied human acceptance; the implementation agent has not separately inspected an original export, and no conversation ID is invented. The design discussions are recommendations, not behavior evidence.

The accepted outcome is a maintained context space with clear content owners. A space can retain its current directories, tools and canonical documents; Git and a unified root are optional. A top-level space owns cross-domain goals, relationships, tradeoffs and contracts rather than only listing children. Routing helps discover related knowledge and constraints, while existing authorization determines which owners may be edited. This work does not authorize changing consuming projects or reading private journals.

The extension must preserve existing development behavior: confirmed and protective candidate rules, departure review, evidence distinct from acceptance, immediate decision capture and readback, partial replacement, current dirty/untracked owners, old-format read-only handling, preservation-aware migration, cold recovery, relevant reading and whole-task cost. Candidate retains its specific meaning: an inferred rule supported by evidence that people protect the outcome, followed by default. It is not a label for research hypotheses or guesses about people. Formally recorded accepted historical decisions retain their standing when the original exchange is unavailable.

Context may contain facts, hypotheses, decisions and constraints, preferences and goals, experiences and expressions, and changing state. Evidence, normative acceptance and time/scope are separate judgments, expressed where needed rather than imposed as a universal item schema. Explicitly or continuously authorized records of experience are eligible for preservation even when they do not change future decisions. Agent-initiated knowledge extraction remains selective. Original materials, long-term knowledge/records, current working context and live task/runtime state retain distinct owners. Multimodal summaries cite the original and inspected range; a summary does not verify itself.

The lifecycle includes authorized acquisition, understanding/ownership, updating, task-specific selection and feedback from results or corrections. Stopping use, retaining superseded history, withdrawing permission to use material and physically deleting material are different operations. A skill cannot independently guarantee background collection, source completeness or deletion of every copy.

## Source integration

Deliver a small source/catch-up contract and a reference implementation. Inputs identify the source, authorized scope and stable item/version. Semantic interpretation and canonical owner updates remain with the agent and that owner's rules. Tooling handles identity, duplicate detection, recovery and processing state: owner content must be saved and verifiably read back before processing progress advances. Repeated input must not duplicate durable writing; interruption must resume safely. Inaccessible input, failures and items needing a human decision remain visible. Corrections and withdrawals must locate affected derived references. Processing state belongs to the connector/task owner, not a permanent README governance ledger. Source originals are not deleted by this workflow.

## Compatibility and delivery gates

Existing development consumers using format 4 continue normal read/write behavior without a release-triggered migration. General spaces use format 5 so discovered entries take old writers' read-only branch; compatibility is not established merely because an older parser ignores new fields. Scoped native compatibility and branch-cost observations belong to the linked result account; final release acceptance remains separate. The four primary skill entrypoints and old compatibility names remain.

First freeze the 4.5 baseline, then run mixed non-development cases before changing agent instructions. Add conditional guidance for demonstrated gaps, and extract shared rules only with evidence. Native baseline/candidate runs use the same model and retain failed attempts, actual artifacts, source/harness manifests and per-turn receipts. Quality and protection take priority over elapsed time, total tokens and maintenance cost; new-domain gains cannot offset development regressions. Mechanical checking remains bounded to mechanically decidable properties.

All execution in this task, including native test subjects, is explicitly authorized to use GPT-6.1 Sol. This task-scoped authorization overrides the repository's older model restriction for this work; it does not change the permanent model policy. After native quality/reading review, the coordinator accepted 17,000 runtime words and 220 KiB of skills as this release's ceilings and the observed bounded cost tradeoff. This is an engineering judgment within the task, not a user endorsement of higher costs or a performance-improvement claim. Existing entrypoint, checker and template ceilings remain; [CONTRIBUTING](../CONTRIBUTING.md#protocol-budgets) owns the gates.

The implementation and scoped acceptance evidence are recorded in the [mechanical report](../tests/trials-5.0.md), [native report](../tests/context/trials-5.0.md) and [native result account](../tests/context/results/context-evolution-5.0-2026-11-10.json). The coordinator reviewed the actual principal owners/responses and accepted the bounded behavior/cost evidence; final Git publication/CI are separate observations. Task scratch remains separate. No source-completeness or universal model-compliance claim follows, and later mechanical deltas are not relabelled as full final-hash native trials.

## Entry and compatibility contract

The coordinator accepted this format/discovery direction during implementation; scoped native observations are retained in the result account. General spaces use a distinct format, while development format 4 remains supported. General semantics differ in authorized-record admission and owner boundaries; silently adding fields to 4 would let old writers apply the wrong rules. When old 4.5 actually discovers the entry, 5 reaches its existing non-4 read-only branch. Arbitrary locations are not automatically discovered: wire recognized read-only routes for known old writers and disclose gaps. Its obsolete suggestion to migrate an unknown format to 4 is not permission to downgrade. A marker is an instruction boundary, not protection against an arbitrary writer bypassing it.

```yaml
---
ssot_format: 5
language: en
---
```

No domain profile, item schema, space ID or Git field is required. The entry's prose names the space's purpose, scope, sensitive boundaries and authoritative owners. Stable source identity belongs to the integration state, not a required context-space registry. Existing format 4 retains its existing front matter and semantics.

Discovery first uses the entry explicitly named by the user or applicable agent instructions. In a repository without an explicit entry, retain the `SSOT/README.md` convention. Outside a repository, use a supplied entry; do not search a user's home for personal context, invent a root or create a new space without agreement. Multiple explicit entries are related spaces, not candidates from which to guess a single global owner. Establish applicable parent backlinks through authorized child instructions/entry/workspace routes. Do not change third-party repositories without authorization. If no supported direct-child entry can discover the parent, report that gap rather than claiming the upper constraint is active. Follow only routes relevant to the task and authorized read scope. The selected entry fixes the context root; repository boundaries and write authorization remain separate facts.

| Consumer | New bundle reading | New bundle writing | Old 4.5 writer expectation |
| --- | --- | --- | --- |
| Existing development format 4, Git repository | Current development path | Existing authorized format-4 upkeep, no migration duty | Existing behavior |
| Existing development format 4, no Git | Current model and its evidence limits | Existing owner authorization; Git-only checks unavailable | Existing behavior; no historical protection certification |
| General format 5, Git repository | Conditional general-space route plus relevant protected rules | Named authorized owners, with per-owner evidence and scope | Read as knowledge; no protocol writes or format conversion without agreement |
| General format 5, no Git | Explicit entry and relevant owner routes | Same semantic gates; no Git prerequisite | Read as knowledge; no protocol writes or format conversion without agreement |
| Legacy v2/v3 or unknown marker | Read as knowledge | Existing migration/agreement gates | Existing legacy behavior |
| External owner linked from any entry | Read within applicable scope | Only with pre-existing or explicit authorization covering that owner | Routing alone grants no write permission |
| Independently authorized owner workflow | Its own recording rules | Its existing authorization, without treating a new format as understood | Its existing explicit-write exception remains; no claim that old skills understand format 5 |

No format-4-to-5 conversion is required for development consumers. New general spaces use 5; an existing owner may remain outside the entry directory. An explicitly approved generalization preserves existing owners, rules, source history and data, with a checkpoint when needed. New readers understand both 4 and 5; old readers remain useful for knowledge reading within their discovery boundaries. The candidate bundle is 5.0, while consumer format 4 remains supported for writing.

## Source implementation interface and state paths

The maintained interface is [source-integration.md](../skills/ssot-doctor/references/source-integration.md), with [context-source.py](../skills/ssot-doctor/assets/scripts/context-source.py). This design record owns the accepted direction, not a second copy of command syntax. Source scope comes from trusted invocation/configuration and is compared with export data. State retains metadata/digests/locators rather than source prose; actual artifact bytes require separate inspection. One-off authorized owner recording does not require this tool.

| Starting state / event | Guard and responsibility | Result and observable surface |
| --- | --- | --- |
| Export → import | Caller declares allowed source/scope and explicit owner bindings; tool compares identity and content digest | New versions pending; exact duplicate leaves prior outcomes intact; changed bytes under one revision or unknown replacement target becomes visible conflict |
| Pending → inspect | Tool reopens original export at locator and checks exact item digest | Inspected version, untrusted content, existing captures in bound owners, actual-artifact verification limit |
| Inspected → semantic routing | Agent applies source evidence, acceptance, admission and owner authorization; bind/targets names all intended owners | Explicit target set, or visible human blocker/failure, or reasoned no-update outcome without invented knowledge |
| Owner update → readback | Agent updates originals under owner rules, preserving source marker; tool opens each declared owner | Saved text and digest-bound receipt; ready is not completed |
| Ready → complete | All declared and previously affected owners have valid receipts, current file bytes and bindings match | This version completed with registered references; stale/missing receipts fail visibly |
| Crash after owner write / readback | New process inspects source identity and existing markers, then reuses capture or valid receipt | No need to replay durable writing; connector state does not transact external owner files |
| Failed / human blocker → retry | Actual blocker resolved, then explicit inspect --retry | Processing reopens without silently discarding the previous gap |
| New correction / withdrawal | Named earlier revision must be known; agent reconciles all registered affected owners | New revision and preserved historical linkage, with new readbacks before completion |
| Competing siblings → explicit resolution | Actual source/authorized basis selects one branch for the current exact sibling set; tooling grants no authority | Selected branch can continue, other history/actual effects stay visible; a later sibling requires a new choice |
| Owner moved → bind with reason | New authorized file retains known markers; existing receipts for old binding cannot advance new work | Explicit route history and new readbacks, rather than blind append at a stale destination |
| Source-level withdrawal | Explicit caller request; tool disables further import/processing | Source withdrawn plus list of registered impacts; owners still need authorized reconciliation; originals are retained |

The tool proves these mechanical boundaries only. It cannot establish semantic correctness, authority from a source's own scope, all downstream copies or deletion completeness. The agent/host controls output logs and other copies; state metadata is also controlled task data. Source progress is a version/owner account, not a README governance ledger or completeness certificate.
