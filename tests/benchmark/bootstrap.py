#!/usr/bin/env python3
"""Opt-in installed setup and document-only handoff for two frozen repository cases."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

import run
from bootstrap_usage import summarize


WRITER = ("I agree to set up repository SSOT for this project now. Keep existing authoritative documents in place. "
          "Use the installed bootstrap skill and finish as far as the available evidence permits. Only this repository "
          "contains project sources for this exercise. You may write SSOT, ignored work notes and the managed "
          "instruction block. Leave implementation, tests and existing decisions intact. Report completion, gaps "
          "and what was checked. Use only gpt-6.1-terra for any helpers.")
READERS = {
    "shift": ("Read only the maintained project documentation starting at SSOT/README.md. A weekend handoff failed "
              "and one party wants to assign the rotation team or clear the slot. What should our scheduler do? "
              "What changes if both confirm, and on an ordinary weekday? Where is the authority, has the "
              "implementation been shown to enforce all of it, and is setup complete?"),
    "links": ("Read only the maintained documentation, starting at SSOT/README.md. A maintainer plans using two "
              "aliases of one skills directory, then someone edits a planned installed skill, or the second symlink "
              "creation fails. Explain expected effects on originals, backups, unrelated entries and a later rerun. "
              "What is known from evidence and what has a human approved? Cite owners. Work read-only."),
}


CLI_READER = ("Use only the maintained guidance. You are in the root of a complete source checkout. The existing "
              "skill bases are ../baseA and ../baseB, and ../backups is available on their filesystem outside the "
              "checkout. Give the exact two shell commands to preview the plan and then apply it using those paths "
              "and the default source. If the plan is empty, can you omit the backup-directory option on apply? "
              "Work read-only. Do not run the commands or read implementation code.")


def fixture(workspace, case):
    if case == "shift":
        (workspace / "README.md").write_text(
            "# Shift board\n\nRecords shift vacancies. Scheduling authority and exceptions are in [Shift policy](policy.md).\n")
        (workspace / "policy.md").write_text(
            "# Shift policy\n\nOn 2026-10-20 the scheduling owner approved keeping the previous assignee on a failed "
            "handoff. Never clear the assignment. Only on a weekend support shift may the rotation team take over, "
            "and only when both parties confirm.\n")
        (workspace / "shift.py").write_text(
            "def assigned(previous, substitute, confirmed):\n    return substitute if confirmed else previous\n")
    else:
        source = Path(__file__).resolve().parents[2]
        for name in ("tools/link-local.py", "tests/test-local-links.py"):
            path = workspace / name
            path.parent.mkdir()
            path.write_bytes(subprocess.check_output(["git", "show", "4377d49:" + name], cwd=source))
        (workspace / "README.md").write_text(
            "# Local skill links\n\nMaintainers use tools/link-local.py to link local skill installations to a shared "
            "checkout. Run python3 tests/test-local-links.py to exercise the file operations in temporary directories.\n")


def phase(root, directory, workspace, visible, prompt, installed):
    home = directory / "codex-home"
    result = run.transport.execute_turn(root, directory, workspace, prompt, 1, 1200,
                                        sandbox_command=run.isolated_command(workspace, visible, home),
                                        codex_home=home, capture_checkpoints=False, model="gpt-6.1-terra",
                                        installed_mode=installed)
    print(json.dumps({k: result[k] for k in ("native_identity_state", "completed", "returncode", "seconds")}),
          flush=True)
    usage = summarize(directory)
    run.save(directory / "usage.json", usage)
    if usage["observation_issues"]:
        raise SystemExit("Usage receipts are incomplete; inspect usage.json")
    if not result["completed"] or result["returncode"]:
        raise SystemExit("Native phase incomplete; preserve this output directory")
    return result


def handoff(root, source, directory, case, prompt=None):
    directory.mkdir(parents=True, exist_ok=False)
    workspace = directory / "workspace"
    shutil.copytree(source, workspace, ignore=shutil.ignore_patterns(".agents", ".git", ".ssot-work", "__pycache__"))
    run.init_git(workspace)
    # Leave routed instruction owners readable while disabling automatic instruction loading.
    empty = directory / "empty"
    empty.mkdir()
    result = phase(root, directory, workspace, empty, prompt or READERS[case], installed=False)
    if result["tree_changed_paths"]:
        raise SystemExit("Reader modified the transferred project")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=READERS, required=True)
    parser.add_argument("--bundle", type=Path, required=True, help="Checkout of the protocol under test")
    parser.add_argument("--output", type=Path, required=True, help="New isolated directory under /tmp or /var/tmp")
    parser.add_argument("--run-models", action="store_true", help="Run the billable writer and reader after preparation")
    args = parser.parse_args()
    if args.run_models and os.environ.get("CI"):
        parser.error("Native trials are disabled in CI")
    root = args.output.resolve()
    if not any(base in root.parents for base in (Path("/tmp").resolve(), Path("/var/tmp").resolve())):
        parser.error("The isolation harness requires an output under /tmp or /var/tmp")
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    bundle = root / "bundle"
    bundle.mkdir()
    for name in ("install.sh", "VERSION"):
        shutil.copy2(args.bundle / name, bundle / name)
    shutil.copytree(args.bundle / "skills", bundle / "skills", ignore=shutil.ignore_patterns("__pycache__"))
    workspace = root / "writer/workspace"
    workspace.mkdir(parents=True)
    fixture(workspace, args.case)
    subprocess.run(["bash", str(bundle / "install.sh"), "--quickstart", "--agent", "codex", "--scope", "project",
                    "--lang", "en"], env={**os.environ, "SOURCE_DIR": str(bundle)}, cwd=workspace, check=True,
                   stdout=subprocess.DEVNULL)
    adapter = (workspace / ".agents/skills/ssot-bootstrap/assets/templates/adapter-thin.md").read_text()
    (workspace / "AGENTS.md").write_text(adapter[adapter.index("<!-- SSOT-CONTEXT:BEGIN -->"):])
    (workspace / ".gitignore").write_text(".agents/\n__pycache__/\n")
    run.init_git(workspace)
    run.save(root / "plan.json", {"case": args.case, "bundle_files": run.manifest(bundle),
                                  "writer": WRITER, "reader": READERS[args.case],
                                  "cli_reader": CLI_READER if args.case == "links" else None, "model": "gpt-6.1-terra"})
    if not args.run_models:
        return

    phase(root, workspace.parent, workspace, bundle, WRITER, installed=True)
    handoff(root, workspace, root / "reader", args.case)
    if args.case == "links":
        handoff(root, workspace, root / "reader-cli", args.case, prompt=CLI_READER)


if __name__ == "__main__":
    main()
