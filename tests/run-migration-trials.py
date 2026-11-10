#!/usr/bin/env python3
"""Opt-in native migration trials. Preparation and grading never call a model."""
import argparse
import json
import inspect
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "benchmark"))
import run as bench


def fixture(repo, case):
    repo.mkdir();(repo/'SSOT').mkdir();(repo/'docs').mkdir()
    (repo/'SSOT/README.md').write_text('''---
    ssot_format: 3
    language: en
    ---
    # Parcel Desk

    Parcel Desk computes delivery quotes. Project memory explains protected behavior.

    ## Map

    [Architecture](architecture.md) explains retry identity.

    ## Task routes

    | Task | Read first |
    | --- | --- |
    | Retry changes | [Architecture](architecture.md#retry-identity) |

    ## Invariants

    | ID | Kind | Rule | Explained in | Status | Source |
    | --- | --- | --- | --- | --- | --- |
    | INV-01 | product promise | Retry retains the original payment identity | [Retry identity](architecture.md#retry-identity) | confirmed | user, 2026-11-01 |
    | INV-02 | product promise | Quote lifetime is 17 minutes | [Lifetime](architecture.md#quote-lifetime) | candidate | inferred from a test |

    ## Open questions

    Should manual export retain expired quotes? This blocks only export work.
    ''')
    (repo/'SSOT/architecture.md').write_text('''# Architecture

    ## Retry identity

    The user said on 2026-11-01: "Retry retains the original payment identity". This protects clients from duplicate charges. A timeout after charging does not permit another charge. Delivery completion is separate from payment completion.

    ## Quote lifetime

    A test uses 17 minutes. No human approval was found; do not treat this as confirmed.
    ''')
    (repo/'AGENTS.md').write_text('''# Project instructions

    Never publish payment credentials.

    Before every task read SSOT/STATUS.md, run $ssot-audit for protocol lag and update tracked_protocol.

    <!-- SSOT-SKILL:BEGIN -->
    Use $ssot-preflight before substantive work and $ssot-closeout at the end.
    <!-- SSOT-SKILL:END -->
    ''')
    (repo/'check-memory.sh').write_text('#!/bin/sh\nbash .agents/skills/ssot-doctor/assets/scripts/ssot-lint.sh SSOT\n')
    (repo/'.gitignore').write_text('.ssot-work/\n.agents/\n')
    for name in ("SSOT/README.md", "SSOT/architecture.md", "AGENTS.md"):
        path = repo / name
        path.write_text(inspect.cleandoc(path.read_text()) + "\n")

    def git(*args):
        return subprocess.check_output(["git", "-c", "core.hooksPath=/dev/null",
            "-c", "commit.gpgsign=false", "-c", "maintenance.auto=false", "-c", "gc.auto=0",
            "-c", "user.name=Trial", "-c", "user.email=trial@example.invalid",
            "-C", str(repo), *args], text=True,
            env={**os.environ, "GIT_AUTHOR_DATE": "2026-11-10T00:00:00Z",
                 "GIT_COMMITTER_DATE": "2026-11-10T00:00:00Z"})

    git("init", "-q")
    git("add", ".")
    git("commit", "-qm", "v3 fixture")
    sha = git("rev-parse", "HEAD").strip()
    p=repo/'SSOT/README.md';p.write_text(p.read_text().replace('language: en','language: en\nreviewed_through: '+sha))
    git("add", ".")
    git("commit", "-qm", "record review boundary")
    # Model a recorded checkpoint, not a random dirty tree.
    if case == 'resume':
     (repo/'SSOT/BOOTSTRAP.md').write_text(f'''# SSOT setup in progress

    Kind: migration from v3. Started from commit: {sha}.

    ## Done

    User agreed to migration to format 4 and editing SSOT, AGENTS.md and check-memory.sh. All writer installations now support format 4. Existing memory and rules were inventoried; no content relocation is needed. Canonical owners remain in place. No conversation export is supplied; source coverage is limited to these recorded decisions.

    ## Next

    Finish format migration, instruction wiring and tooling reconciliation, then validate. Owner files and invariant statuses must be preserved. Newcomer review can be done by the lead because helpers are unavailable for this migration; no new rule mining is needed.
    ''')

    checkpoint = repo / "SSOT/BOOTSTRAP.md"
    if checkpoint.exists():
        checkpoint.write_text(inspect.cleandoc(checkpoint.read_text()) + "\n")
    return sha


def grade(repo, case, before, watermark):
    after = bench.transport.snapshot(repo)
    if case == "readonly":
        return {"all_files_unchanged": before == after}
    index = after.get("SSOT/README.md", "")
    instructions = after.get("AGENTS.md", "")
    checker = repo / ".agents/skills/ssot-doctor/assets/scripts/ssot-check.py"
    checked = subprocess.run([sys.executable, "-B", str(checker), str(repo / "SSOT")],
                             capture_output=True, text=True)
    wrapper = subprocess.run(["sh", "check-memory.sh"], cwd=repo, capture_output=True, text=True)
    rows = lambda text: [line for line in text.splitlines() if line.startswith("| INV-")]
    expected_block = (checker.parents[3] / "ssot-bootstrap/assets/templates/en/adapter-thin.md").read_text()
    def block(text):
        return text.partition("<!-- SSOT-SKILL:BEGIN -->")[2].partition("<!-- SSOT-SKILL:END -->")[0]
    return {
        "format4": "ssot_format: 4" in index,
        "review_watermark_preserved": f"reviewed_through: {watermark}" in index,
        "rules_sources_statuses_preserved": len(rows(index)) == 2 and rows(index) == rows(before["SSOT/README.md"]),
        "owner_bytes_preserved": after.get("SSOT/architecture.md") == before["SSOT/architecture.md"],
        "open_question_preserved": "Should manual export retain expired quotes?" in index,
        "credential_rule_preserved": "Never publish payment credentials." in instructions,
        "legacy_instructions_removed": all(token not in instructions for token in
                                           ("SSOT/STATUS.md", "tracked_protocol", "protocol lag")),
        "one_current_instruction_block": instructions.count("<!-- SSOT-SKILL:BEGIN -->") == 1
                                         and block(instructions).strip() == block(expected_block).strip(),
        "obsolete_wrapper_replaced_and_runs": "ssot-lint.sh" not in after.get("check-memory.sh", "")
                                               and wrapper.returncode == 0 and "ssot-check: PASS" in wrapper.stdout,
        "checker_passes": checked.returncode == 0 and "ssot-check: PASS" in checked.stdout,
        "checkpoint_removed_last_state": "SSOT/BOOTSTRAP.md" not in after,
        "write_scope": set(k for k in set(before) | set(after) if before.get(k) != after.get(k))
                       <= {"SSOT/README.md", "SSOT/BOOTSTRAP.md", "AGENTS.md", "check-memory.sh"},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", choices=("migrate", "resume", "readonly"), default="resume")
    parser.add_argument("--run-models", action="store_true")
    parser.add_argument("--cap", type=int, default=240)
    args = parser.parse_args()
    if args.run_models and os.environ.get("CI"):
        parser.error("Model calls are forbidden in CI")
    root = args.output.resolve()
    if not any(root.is_relative_to(p.resolve()) for p in (Path("/tmp"), Path("/var/tmp"))):
        parser.error("Use an output under /tmp or /var/tmp for isolation")
    root.mkdir(exist_ok=False)
    bundle = root / "bundle"
    bundle.mkdir()
    shutil.copytree(args.bundle.resolve() / "skills", bundle / "skills", ignore=shutil.ignore_patterns("__pycache__"))
    harness = root / "harness"
    (harness / "benchmark").mkdir(parents=True)
    for path in (HERE / "run-migration-trials.py", HERE / "run-performance-trials.py",
                 HERE / "benchmark/run.py", HERE / "benchmark/cases.py"):
        shutil.copy2(path, harness / path.relative_to(HERE))
    repo = root / "repo"
    watermark = fixture(repo, args.case)
    (repo / ".agents").mkdir(exist_ok=True)
    # This symlink denotes the installed tools. They are mounted read-only during execution.
    (repo / ".agents/skills").symlink_to(bundle / "skills", target_is_directory=True)
    before = bench.transport.snapshot(repo)
    checker = repo / ".agents/skills/ssot-doctor/assets/scripts/ssot-check.py"
    precheck = subprocess.run([sys.executable, "-B", str(checker), str(repo / "SSOT")],
                             capture_output=True, text=True)
    if precheck.returncode != 3 or "ERROR" in precheck.stdout or "v3 layout" not in precheck.stdout:
        raise RuntimeError("Fixture must be well-formed legacy memory before any model call: " + precheck.stdout)
    prompt = (f"Work only in the current isolated repository. Skills are at {bundle / 'skills'} and .agents/skills. "
              "Read SKILL.md when needed. Do not commit, push, install dependencies, access other projects or invoke other models. "
              "Helpers are unavailable.\nUser task: ")
    tasks = {
        "resume": "Continue the already agreed SSOT v3 to v4 migration recorded in SSOT/BOOTSTRAP.md. Finish it, verify the saved result, and report the scope and any remaining gaps. The existing write authorization remains in force; do not ask for it again. Retain the existing owners, protected rules and review watermark.",
        "migrate": "I agree to migrate SSOT from v3 to v4 and authorize changes to SSOT, AGENTS.md and check-memory.sh, including removing obsolete SSOT instructions outside the managed block. All writer installations support format 4. Retain owners, rule IDs/statuses and review watermark; reconcile instruction/tooling remnants and verify. No source conversation export is supplied. Do not mine new rules. Use your own newcomer review because helpers are unavailable.",
        "readonly": "Review only what upgrading these v3 repository documents to v4 would require. This task is strictly read-only: do not migrate, create a checkpoint or edit any file. Separate a bundle upgrade from memory migration and report the needed changes.",
    }
    prompt += tasks[args.case]
    plan = {"case": args.case, "model": bench.transport.MODEL, "watermark": watermark,
            "bundle_manifest": bench.manifest(bundle), "harness_manifest": bench.manifest(harness),
            "fixture": before, "prompt": prompt, "cap": args.cap}
    bench.save(root / "plan.json", plan)
    if not args.run_models:
        print(f"Prepared {args.case} in {root}; no models called. Use a new output with --run-models for a live run.")
        return
    run_dir = root / "run"
    run_dir.mkdir()
    home = root / "home"
    command = bench.isolated_command(repo, bundle, home)
    summary = bench.transport.execute_turn(root, run_dir, repo, prompt, 1, args.cap,
                                           sandbox_command=command, codex_home=home)
    checks = grade(repo, args.case, before, watermark)
    checks["native_completion"] = summary["returncode"] == 0 and summary["completed"]
    checks["allowed_model"] = summary.get("native_models") == [bench.transport.MODEL]
    checks["frozen_inputs"] = bench.manifest(bundle) == plan["bundle_manifest"] and bench.manifest(harness) == plan["harness_manifest"]
    bench.save(root / "verdict.json", {"checks": checks, "pass": all(checks.values())})
    print(json.dumps({"case": args.case, "checks": checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
