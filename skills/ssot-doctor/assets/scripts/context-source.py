#!/usr/bin/env python3
"""Track explicit source versions and saved-owner readback, never write owners.

See ../../references/source-integration.md for authority and evidence limits.
State belongs to one connector task/source, not the maintained context index.
"""

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def identity(source, item, revision):
    return digest(encoded([source, item, revision]))


def require_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    return value


def write_state(path, state):
    """Replace progress after durable write; a crash preserves the prior snapshot."""
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded(state) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextlib.contextmanager
def locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path) + ".lock", "a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("another operation holds this state lock") from error
        yield


def marker(record):
    return f"<!-- ssot-source:{record['key']} -->"


def find_record(state, item, revision):
    key = identity(state["source_id"], item, revision)
    if key not in state["items"]:
        raise ValueError("item/revision has not been imported")
    return state["items"][key]


def earlier(state, record):
    revision = record["item"].get("replaces")
    if revision is None:
        return None
    return state["items"].get(identity(state["source_id"], record["item"]["item_id"], revision))


def ancestors(state, record):
    result, seen = [], {record["key"]}
    while (record := earlier(state, record)) is not None:
        if record["key"] in seen:
            raise ValueError("cyclic source revision relationship")
        seen.add(record["key"])
        result.append(record)
    return result


def successors(state, record):
    return [{"revision": other["item"]["revision"], "status": other["status"],
             "operation": other["item"]["operation"]}
            for other in state["items"].values()
            if other["item"]["item_id"] == record["item"]["item_id"]
            and other["item"].get("replaces") == record["item"]["revision"]]


def history(state, record):
    """Known effects survive linear replacement and explicit branch selection."""
    return [other for other in state["items"].values() if other["key"] != record["key"]
            and other["item"]["item_id"] == record["item"]["item_id"]]


def peers(state, record):
    parent = record["item"].get("replaces")
    return [other for other in state["items"].values() if parent is not None
            and other["item"]["item_id"] == record["item"]["item_id"]
            and other["item"].get("replaces") == parent]


def refresh_relationships(state):
    for record in state["items"].values():
        if "replaces" not in record["item"]:
            continue
        conflicts = [c for c in record.get("conflicts", [])
                     if c.get("kind") not in {"unknown-target", "cyclic-revisions", "fork"}]
        parent = earlier(state, record)
        if parent is None:
            conflicts.append({"kind": "unknown-target", "revision": record["item"]["replaces"]})
        try:
            ancestors(state, record)
        except ValueError:
            conflicts.append({"kind": "cyclic-revisions"})
        group = peers(state, record)
        if len(group) > 1:
            resolution = state.get("fork_resolutions", {}).get(parent["key"] if parent else "")
            valid = resolution and resolution["members"] == sorted(r["key"] for r in group)
            if not valid or resolution["chosen"] != record["key"]:
                conflicts.append({"kind": "fork", "members": [r["item"]["revision"] for r in group],
                                  "chosen": resolution["chosen"] if valid else None})
        record["conflicts"] = conflicts
        if conflicts:
            if record["status"] != "conflict":
                record["before_conflict"] = record["status"]
            record["status"] = "conflict"
        elif record["status"] == "conflict":
            record["status"] = record.pop("before_conflict", "pending")


def known_captures(state, record):
    captures = []
    for alias, filename in state["owners"].items():
        try:
            data = Path(filename).read_bytes()
            count = data.count(marker(record).encode())
            if count:
                captures.append({"owner": alias, "path": filename, "marker_count": count,
                                 "file_digest": digest(data)})
        except OSError as error:
            captures.append({"owner": alias, "path": filename, "unavailable": str(error),
                             "missing": isinstance(error, FileNotFoundError)})
    return captures


def impacts(state, record):
    """Locate registered and in-flight effects without opening source material."""
    found = {}
    def add(alias, path, evidence, **extra):
        key = alias, path
        if key not in found:
            found[key] = {"item_id": record["item"]["item_id"], "revision": record["item"]["revision"],
                          "owner": alias, "path": path, "evidence": []}
        found[key]["evidence"].append(evidence)
        found[key].update(extra)
    for alias in record.get("targets", []):
        add(alias, state["owners"][alias], "declared-target")
    for ref in record.get("references", []):
        add(ref["owner"], ref["path"], "completed-reference")
    for receipt_id in record.get("receipts", []):
        ref = state["receipts"][receipt_id]
        add(ref["owner"], ref["path"], "readback", receipt_id=receipt_id)
    for capture in known_captures(state, record):
        if capture.get("marker_count"):
            add(capture["owner"], capture["path"], "located-capture", marker_count=capture["marker_count"])
        elif capture["owner"] in record.get("targets", []) and not capture.get("missing"):
            add(capture["owner"], capture["path"], "unavailable", error=capture.get("unavailable"))
    return list(found.values())


def item_view(state, record):
    old = earlier(state, record)
    return {"item_id": record["item"]["item_id"], "revision": record["item"]["revision"],
            "operation": record["item"]["operation"],
            "status": record["status"], "reason": record.get("reason"),
            "outcome": record.get("outcome"), "targets": record.get("targets"),
            "references": record.get("references", []), "successors": successors(state, record),
            "conflicts": record.get("conflicts", []), "receipts": record.get("receipts", []),
            "affected_references": [] if old is None else [
                {**ref, "current_path": state["owners"].get(ref["owner"])} for ref in old.get("references", [])],
            "replaced_revision_available": old is not None if "replaces" in record["item"] else None}


def read_source(state, record):
    """Reopen original export; state carries metadata/digests, not source prose."""
    source = json.loads(Path(record["locator"]["path"]).read_text())
    if not isinstance(source, dict):
        raise ValueError("saved export is no longer an object")
    if source.get("source_id") != state["source_id"] or source.get("scope") != state["scope"]:
        raise ValueError("source identity/scope changed at its saved locator")
    item = source["items"][record["locator"]["index"]]
    if digest(encoded(item)) != record["digest"]:
        raise ValueError("source item changed at its saved locator; import and reconcile explicitly")
    return item


def import_source(args, state):
    if state is not None and state.get("source_status") == "withdrawn":
        raise ValueError("source use was withdrawn; further import is disabled")
    source = json.loads(args.export.read_text())
    if not isinstance(source, dict):
        raise ValueError("export must be an object")
    source_id = require_text(source.get("source_id"), "source_id")
    scope = require_text(source.get("scope"), "scope")
    items = source.get("items")
    if not isinstance(items, list):
        raise ValueError("items must be a list")
    if source_id != args.source_id or scope != args.scope:
        raise ValueError("export identity/scope differs from trusted CLI configuration")
    if state is None:
        state = {"schema": 1, "source_id": source_id, "scope": scope,
                 "source_status": "active", "owners": {}, "items": {}, "receipts": {}}
    if state.get("source_status") == "withdrawn":
        raise ValueError("source use was withdrawn; further import is disabled")
    if state["source_id"] != source_id or state["scope"] != scope:
        raise ValueError("source identity/scope differs from this state; reconcile explicitly")
    bind_owners(state, args.owner)
    # Validate the complete export before changing any source-unit progress.
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each item must be an object")
        for field in ("item_id", "revision", "source_ref"):
            require_text(item.get(field), field)
        if item.get("operation") not in {"upsert", "correction", "withdrawal"}:
            raise ValueError("operation must be upsert, correction or withdrawal")
        if item["operation"] != "withdrawal" and not ("content" in item or "artifact" in item):
            raise ValueError("item needs content or an artifact pointer")
        if item["operation"] != "upsert":
            require_text(item.get("replaces"), "replaces")
            if item["replaces"] == item["revision"]:
                raise ValueError("a revision cannot replace itself")
    for index, item in enumerate(items):
        key = identity(source_id, item["item_id"], item["revision"])
        checksum = digest(encoded(item))
        metadata = {field: item[field] for field in ("item_id", "revision", "operation", "source_ref", "replaces")
                    if field in item}
        locator = {"path": str(args.export.resolve()), "index": index}
        if key not in state["items"]:
            state["items"][key] = {"key": key, "digest": checksum, "item": metadata,
                                    "locator": locator, "status": "pending"}
            if item["operation"] == "upsert" and any(
                    other["key"] != key and other["item"]["item_id"] == item["item_id"]
                    and other["item"]["operation"] == "upsert" for other in state["items"].values()):
                state["items"][key]["conflicts"] = [{"kind": "ambiguous-revision", "reason": "later revision must name replaces"}]
                state["items"][key]["before_conflict"] = "pending"
                state["items"][key]["status"] = "conflict"
        elif state["items"][key]["digest"] != checksum:
            record = state["items"][key]
            conflict = {"digest": checksum, "item": metadata, "locator": locator}
            if conflict not in record.setdefault("conflicts", []):
                record["conflicts"].append(conflict)
            if record["status"] != "conflict":
                record["before_conflict"] = record["status"]
            record["status"] = "conflict"
        else:
            state["items"][key]["locator"] = locator
    refresh_relationships(state)
    return state, {"source_id": source_id, "scope": scope,
                   "conflicting_imports": [item["item_id"] for item in items
                       if state["items"][identity(source_id, item["item_id"], item["revision"])]["status"] == "conflict"],
                   "items": [item_view(state, record) for record in state["items"].values()]}


def bind_owners(state, bindings, reason=None):
    for binding in bindings:
        alias, separator, filename = binding.partition("=")
        if not separator or not alias or not filename:
            raise ValueError("owner binding must be ALIAS=FILE")
        path = str(Path(filename).resolve())
        old_path = state["owners"].get(alias)
        if old_path and old_path != path:
            if not reason:
                raise ValueError("owner alias already has another path; bind --reason requires deliberate route repair")
            data = Path(path).read_bytes()
            try:
                prior = Path(old_path).read_bytes()
            except FileNotFoundError:
                prior = b""  # an authorized move may already have removed the old path
            affected = [r for r in state["items"].values()
                        if any(ref["owner"] == alias for ref in r.get("references", []))
                        or any(state["receipts"][receipt]["owner"] == alias for receipt in r.get("receipts", []))
                        or marker(r).encode() in prior]
            if any(data.count(marker(r).encode()) != 1 for r in affected):
                raise ValueError("replacement owner must retain each known source marker; repair/move owner first")
            state.setdefault("binding_history", []).append(
                {"owner": alias, "from": old_path, "to": path, "reason": reason})
        state["owners"][alias] = path


def process(args, state):
    if args.command == "status":
        return {"source_id": state["source_id"], "scope": state["scope"], "owners": state["owners"],
                "source_status": state.get("source_status", "active"),
                "withdrawal_reason": state.get("withdrawal_reason"),
                "last_error": state.get("last_error"),
                "known_impacts": [impact for record in state["items"].values() for impact in impacts(state, record)],
                "items": [item_view(state, record) for record in state["items"].values()]}
    if args.command == "withdraw-source":
        state["source_status"], state["withdrawal_reason"] = "withdrawn", args.reason
        return {"source_status": "withdrawn", "reason": args.reason,
                "known_references": [impact for record in state["items"].values() for impact in impacts(state, record)],
                "evidence_limit": "source processing stopped; reconcile listed owners separately; originals retained"}
    if state.get("source_status") == "withdrawn":
        raise ValueError("source use was withdrawn; processing disabled, use status for known impacts")
    if args.command == "bind":
        bind_owners(state, args.owner, args.reason)
        return {"owners": state["owners"], "binding_history": state.get("binding_history", [])}
    record = find_record(state, args.item, args.revision)
    if args.command == "resolve-fork":
        group = peers(state, record)
        parent = earlier(state, record)
        if len(group) < 2 or parent is None:
            raise ValueError("resolution requires a known parent and competing sibling revisions")
        resolution = {"chosen": record["key"], "members": sorted(r["key"] for r in group), "reason": args.reason}
        state.setdefault("fork_resolutions", {})[parent["key"]] = resolution
        refresh_relationships(state)
        return {"resolution": resolution, "revisions": [item_view(state, r) for r in group],
                "evidence_limit": "caller must have a source/decision basis; this does not merge content or grant authority"}
    newer = successors(state, record)
    if newer and not (args.command == "inspect" and args.history):
        raise ValueError("a successor revision is known; process it, or inspect --history read-only")
    if args.command == "inspect":
        source_item = read_source(state, record)
        if args.history:
            return {**item_view(state, record), "untrusted_source": source_item, "read_only_history": True,
                    "evidence_limit": "historical source read does not enable targets/readback/completion"}
        if args.retry and record["status"] in {"failed", "needs-decision"}:
            record.pop("reason", None)
            record["status"] = "pending"
        if record["status"] == "pending":
            record["status"] = "inspected"
        record["inspected_digest"] = record["digest"]
        return {**item_view(state, record), "source_id": state["source_id"], "scope": state["scope"],
                "untrusted_source": source_item, "marker": marker(record),
                "ancestor_impacts": [impact for old in history(state, record) for impact in impacts(state, old)],
                "history_versions": [old["item"] for old in history(state, record)],
                "artifact_verification": "export item/locator only; artifact bytes are not opened or hashed",
                "existing_captures": known_captures(state, record)}
    if record.get("conflicts"):
        raise ValueError("source version has unresolved conflicts; inspect/status retain their details")
    for old in ancestors(state, record):
        # Content identity conflicts also invalidate descendants, not just graph conflicts.
        if old.get("conflicts"):
            raise ValueError(f"ancestor revision {old['item']['revision']} has unresolved conflicts; "
                             "reconcile it before advancing")
    if args.command in {"defer", "fail"}:
        if record["status"] == "completed":
            raise ValueError("completed history stays recorded; import a correction/withdrawal revision")
        record["status"] = "needs-decision" if args.command == "defer" else "failed"
        record["reason"] = args.reason
        return item_view(state, record)
    if record.get("inspected_digest") != record["digest"]:
        raise ValueError("inspect this exact source version before readback/completion")
    if record["status"] in {"failed", "needs-decision"}:
        raise ValueError("resolve the blocker, then inspect --retry before continuing")
    if args.command == "no-update":
        old = earlier(state, record)
        effects = [effect for r in [record, *history(state, record)] for effect in impacts(state, r)
                   if any(e != "declared-target" for e in effect["evidence"])]
        if effects:
            raise ValueError("existing derived references require reconciliation and saved-owner readback")
        record["status"], record["outcome"], record["reason"] = "completed", "no-update", args.reason
        return item_view(state, record)
    if args.command == "targets":
        if any(alias not in state["owners"] for alias in args.owner):
            raise ValueError("every target owner must be explicitly bound")
        targets = sorted(set(args.owner))
        if record["status"] == "completed":
            raise ValueError("completed history is immutable; use a new revision")
        if record.get("targets") is not None and record["targets"] != targets and not args.reason:
            raise ValueError("changing declared targets requires an explicit reason")
        record["targets"] = targets
        if args.reason:
            record["target_reason"] = args.reason
        return item_view(state, record)
    if not record.get("targets"):
        raise ValueError("declare every intended owner with targets before readback/completion")
    if args.command == "readback":
        if args.owner not in state["owners"]:
            raise ValueError("owner alias is not explicitly bound")
        if args.owner not in record["targets"]:
            raise ValueError("owner is outside this item's declared target set")
        path = state["owners"][args.owner]
        data = Path(path).read_bytes()
        if data.count(marker(record).encode()) != 1:
            raise ValueError("saved owner must contain exactly one matching source marker")
        receipt = {"key": record["key"], "item_digest": record["digest"], "owner": args.owner,
                   "path": path, "file_digest": digest(data)}
        receipt_id = digest(encoded(receipt))
        state["receipts"][receipt_id] = receipt
        if receipt_id not in record.setdefault("receipts", []):
            record["receipts"].append(receipt_id)
        if record["status"] != "completed":
            record["status"] = "readback-ready"
        return {"receipt_id": receipt_id, "receipt": receipt, "saved_owner_text": data.decode("utf-8"),
                "evidence_limit": "saved linkage/readback only; semantic correctness and authority require review"}
    references = []
    for receipt_id in args.receipt:
        receipt = state["receipts"].get(receipt_id)
        if not receipt or receipt["key"] != record["key"] or receipt["item_digest"] != record["digest"]:
            raise ValueError("receipt does not belong to this inspected source version")
        if receipt["path"] != state["owners"].get(receipt["owner"]):
            raise ValueError("owner binding changed after readback; read back its new location")
        data = Path(receipt["path"]).read_bytes()
        if digest(data) != receipt["file_digest"] or data.count(marker(record).encode()) != 1:
            raise ValueError("owner changed after readback; read back again")
        references.append(receipt)
    old = earlier(state, record)
    affected = set(record["targets"]) | {impact["owner"] for old in [record, *history(state, record)]
        for impact in impacts(state, old) if any(e != "declared-target" for e in impact["evidence"])}
    if not affected.issubset({r["owner"] for r in references}):
        raise ValueError("read back every known affected owner before completing this revision")
    if record["status"] == "completed":
        if {encoded(ref) for ref in record.get("references", [])} != {encoded(ref) for ref in references}:
            raise ValueError("completed references are immutable; use a new revision")
        return item_view(state, record)  # Retry order does not rewrite saved history.
    record["references"] = references
    record["status"], record["outcome"] = "completed", "recorded"
    return item_view(state, record)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    global_commands = ("import", "status", "bind", "withdraw-source")
    for command in (*global_commands, "inspect", "defer", "fail", "targets", "no-update", "resolve-fork", "readback", "complete"):
        sub = commands.add_parser(command)
        sub.add_argument("--state", type=Path, required=True)
        if command == "import":
            sub.add_argument("export", type=Path)
            sub.add_argument("--source-id", required=True, help="trusted allowed source identity")
            sub.add_argument("--scope", required=True, help="trusted allowed source scope")
            sub.add_argument("--owner", action="append", default=[])
        if command not in global_commands:
            sub.add_argument("--item", required=True)
            sub.add_argument("--revision", required=True)
        if command == "inspect":
            sub.add_argument("--retry", action="store_true")
            sub.add_argument("--history", action="store_true", help="read historical source without enabling writes")
        if command in {"defer", "fail", "no-update", "withdraw-source", "resolve-fork"}:
            sub.add_argument("--reason", required=True)
        if command in {"bind", "targets"}:
            sub.add_argument("--owner", action="append", required=True)
            sub.add_argument("--reason")
        if command == "readback":
            sub.add_argument("--owner", required=True)
        if command == "complete":
            sub.add_argument("--receipt", action="append", required=True)
    args = parser.parse_args()
    args.state = args.state.resolve()
    try:
        with locked(args.state):
            state = json.loads(args.state.read_text()) if args.state.exists() else None
            original = json.loads(json.dumps(state))
            try:
                if state is not None and (not isinstance(state, dict) or state.get("schema") != 1):
                    raise ValueError("unsupported or damaged connector state")
                if args.command == "import":
                    state, result = import_source(args, state)
                elif state is None:
                    raise ValueError("state not found; import an explicitly scoped source first")
                else:
                    result = process(args, state)
            except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
                if isinstance(original, dict) and original.get("schema") == 1 and args.command != "status":
                    original["last_error"] = {"operation": args.command, "reason": str(error)}
                    if args.command not in global_commands:
                        record = original["items"].get(identity(original["source_id"], args.item, args.revision))
                        if record and record["status"] not in {"completed", "conflict", "needs-decision"}:
                            record["status"], record["reason"] = "failed", str(error)
                    write_state(args.state, original)
                raise
            if args.command != "status":
                write_state(args.state, state)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if (args.command == "import" and result["conflicting_imports"]) or (
                    args.command == "inspect" and result["status"] == "conflict"):
                return 1
        return 0
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
