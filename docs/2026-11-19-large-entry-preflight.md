# Preflight in a large development repository

A development entry with hundreds of invariant rows exposed an ambiguity in 5.4. The preflight steps called for reading the entry and finding applicable rules. The memory model also said that every task reads the register. In several actual sessions the first tool call read the entire entry, its response was truncated, and subsequent calls had to find relevant passages in the same file.

The first candidate explained bounded reading inside the skill body. Both installed trial tasks still read the whole entry, with one doing so before opening the skill. A skill-only revision moves the trigger to the skill description and puts the initial header and heading scan at the point where the task first opens the entry. Then the reader searches the register in place and opens full matching rules and linked explanations. The search still covers cross-topic and general protections. A recovery retry with that revision still opened the full entry before the skill. The final candidate moves the ordering instruction into the bilingual development instruction blocks that agents get on launch. This works with existing format-4 entries and their Markdown owners.

## How it was checked

Two read-only tasks came from actual work in the development consumer. One asks about when a report becomes read and whether it survives removal of its source checkout. The other asks for a recovery test matrix that exercises missing receipts, revoked permission, stop, late results and repeated recovery. In both cases the reader needed protections from more than one topic. A command lookup checks the nearby skip path.

Each arm installed the bundle into an isolated copy of the same project fixture. The baseline used the project's existing instruction block and the final candidate applied the updated block by the documented installation step. The native Codex 0.170.0 receipts identify GPT‑6.1 Terra at medium reasoning. A tool receipt tracks the entry reads, and the answers were checked against the project contracts and cited implementations. The experiment measures planning and reading on these tasks. The fixture contains the contracts and code needed for static review and a subset of the project's tracked assets. The application and its production data were outside the trial.

| Task | First output that included the entry, 5.4 → 5.5 | Whole-turn input tokens, 5.4 → 5.5 |
| --- | ---: | ---: |
| Report and reading protection | 241,207 → 385 bytes | 232,018 → 238,906 |
| Recovery and authorization | 262,231 → 385 bytes | 284,264 → 237,652 |

The native command observer counts UTF-8 output on the whole command, including any files read in the same command. These bytes describe command output. The runtime can apply its own truncation before passing output to the model. In both 5.5 runs the skill was opened first and the first entry command listed headings. Both answers preserved the applicable constraints and their source evidence. The 5.5 report case also noticed a status conflict between the register and a newer owner. The simple lookup returned the command without loading preflight or reading the entry in either arm.

The initial read shrank in both cases. Later searches could still be broad, and total input moved in opposite directions. These two pairs establish the observed route and outcomes. The frozen fixture omitted some unrelated benchmark assets, so optional catalog checks in several runs reported missing fixtures. Four interrupted attempts have reading traces and lack closed turn receipts. They remain outside the whole-turn comparison. The trials neither estimate reliability across repositories nor establish a general token saving.
