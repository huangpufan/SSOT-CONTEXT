"""Deterministic knowledge fixture and independent outcome checks (no model calls)."""

import json
from pathlib import Path
import random
import subprocess
import sys

CASES = ("routed", "unrouted", "stale", "warm", "typo")
TASK = ("Implement express delivery in shipping.py according to the project's accepted contract. "
        "Keep standard delivery compatible and run python3 test_shipping.py. "
        "Keep policy documents and tests unchanged; report any documentation follow-up instead of writing it.")
WARM_TASK = ("The delivery policy has been updated by another maintainer since the previous task. "
             "Apply the current express promotion policy in shipping.py, preserve other behavior and run the tests. "
             "Keep policy documents and tests unchanged; report any documentation follow-up.")
SOURCE = '''def quote(zone, subtotal, weight, kind="physical", service="standard"):
    """Return a delivery quote in cents and business days."""
    if kind == "digital":
        return {"fee": 0, "days": 0}
    if service != "standard":
        raise ValueError("unsupported service")
    return {"fee": 600, "days": 6}
'''
PUBLIC_TEST = '''from shipping import quote
assert quote("north", 1200, 2) == {"fee": 600, "days": 6}
assert quote("south", 60000, 8) == {"fee": 600, "days": 6}
assert quote("north", 1200, 2, "digital") == {"fee": 0, "days": 0}
print("standard compatibility passed; these tests do not cover the express contract")
'''


def policy(seed):
    rng = random.Random(seed)
    return {"north": rng.randrange(1100, 1500, 10), "south": rng.randrange(2100, 2500, 10),
            "kg": rng.randrange(120, 200, 5), "threshold": rng.randrange(20000, 30000, 100),
            "updated": rng.randrange(32000, 40000, 100)}


def expected(p, zone, subtotal, weight, kind="physical", service="standard"):
    if kind == "digital":
        return {"fee": 0, "days": 0}
    if service == "standard":
        return {"fee": 600, "days": 6}
    if service != "express" or zone not in ("north", "south"):
        return "ValueError"
    fee = 0 if zone == "north" and subtotal >= p["threshold"] else p[zone] + p["kg"] * max(weight - 1, 0)
    return {"fee": fee, "days": 2 if zone == "north" else 4}


def samples(p):
    # Boundary values and a cross-owner invariant; public tests do not reveal these.
    return [[zone, subtotal, weight, kind, service]
            for zone in ("north", "south", "remote")
            for subtotal in (0, p["threshold"] - 1, p["threshold"], p["threshold"] + 1)
            for weight in (1, 3)
            for kind in ("physical", "digital")
            for service in ("standard", "express", "overnight")]


def build(repo, case, indexed, seed, documents=24):
    """Both arms get byte-identical facts; only index mode changes the entry links."""
    repo.mkdir(parents=True)
    for directory in ("SSOT", "docs", "docs/archive", "docs/operations"):
        (repo / directory).mkdir()
    p = policy(seed)
    (repo / "shipping.py").write_text(SOURCE)
    (repo / "test_shipping.py").write_text(PUBLIC_TEST)
    (repo / "note.txt").write_text("maintenence\n")
    (repo / ".gitignore").write_text("__pycache__/\n")
    (repo / "docs/product.md").write_text(
        "# Parcel desk\n\nA merchant-facing quotation module. It calculates prices without creating orders or charging cards. "
        "Standard delivery exists. Express was accepted but has not been implemented. "
        "[Delivery contract](shipping.md#express) owns express behavior. "
        "[Eligibility](eligibility.md#digital-goods) owns exclusions across all services.\n")
    (repo / "docs/architecture.md").write_text(
        "# Architecture\n\nshipping.py owns the pure quote function. There are no external services or databases. "
        "Read the [delivery contract](shipping.md#express) for accepted behavior and "
        "[eligibility](eligibility.md#digital-goods) for cross-service exceptions.\n")
    (repo / "docs/eligibility.md").write_text(
        "# Eligibility\n\n## Digital goods\n\nINV-01, confirmed by the maintainer on 2026-11-09: "
        "digital goods always return fee 0 and days 0, even for express, unknown services and remote zones. "
        "No physical parcel is sent. This exception is evaluated before service or zone validation.\n")
    (repo / "docs/shipping.md").write_text(
        "# Delivery contract\n\nThe maintainer accepted this contract on 2026-11-09. Standard delivery is implemented; "
        "express is planned, not yet built. The old proposal in archive is superseded.\n\n"
        "## Standard\n\nKeep the existing standard fee of 600 cents and 6 business days for physical goods.\n\n"
        "## Express\n\nPhysical express supports only north and south; other zones raise ValueError. "
        f"The first kilogram costs {p['north']} cents for north, {p['south']} cents for south. "
        f"Each kilogram above one adds {p['kg']} cents. Inputs in scope have nonnegative integer subtotals and positive integer weights. "
        "North takes 2 business days and south takes 4. Unknown services raise ValueError. "
        "Return the existing fee/days dictionary.\n\n"
        f"North express is free when subtotal is at least {p['threshold']} cents; south never gets this promotion. "
        "Free express keeps its delivery time.\n\n"
        "Before applying these rules, check [digital exclusions](eligibility.md#digital-goods).\n\n"
        "## Pickup experiments\n\nProposed, not accepted: parcel lockers and weekend pickup. No implementation is authorized by this note.\n")
    (repo / "docs/archive/delivery.md").write_text(
        "# Old delivery proposal\n\nSuperseded by [the accepted contract](../shipping.md#express). "
        "This proposal charged a flat 999 cents to every express order, including digital orders. "
        "It was rejected because digital orders have no parcel and actual physical costs differ by region.\n")
    # Plausible adjacent content, not repeated padding or hidden prompt instructions.
    subjects = ("returns", "warehouse", "support", "invoices", "tracking", "catalog")
    for n in range(documents):
        topic = subjects[n % len(subjects)]
        (repo / f"docs/operations/{topic}-{n:02}.md").write_text(
            f"# {topic.title()} workflow {n}\n\nThis operational note owns the {topic} queue for facility {n}. "
            "It concerns staff follow-up after order creation, not the quotation module.\n\n"
            "## Handoff\n\nThe current shift records the order identifier and unresolved customer question before transfer. "
            "A failed handoff stays with its current owner until receipt. Reopening a ticket does not create another order.\n\n"
            "## Escalation\n\nMissing stock and address corrections go to the regional operator. "
            "A delivery estimate is not a fulfillment commitment. Staff consult the order's actual service before promising a date.\n")
    route = ("| Express quotes or delivery promotions | [Express](../docs/shipping.md#express): prices, zones and timing | "
             "[Eligibility](../docs/eligibility.md#digital-goods) before applying any service |\n" if indexed else
             "| Delivery work | [Product](../docs/product.md), [Architecture](../docs/architecture.md) | Check applicable invariants |\n")
    if case == "unrouted":
        route = "| Staff handoff | [Operations](../docs/operations/) | Queue ownership |\n"
    if case == "stale":
        route = "| Express quotes | [Express](../docs/shipping-v0.md#express) | Check applicable invariants |\n"
    (repo / "SSOT/README.md").write_text(
        "---\nssot_format: 4\nlanguage: en\n---\n# Parcel desk\n\nMerchant delivery quotations; no orders or payments are created.\n\n"
        "## Map\n\n- [Product](../docs/product.md): promises and accepted work.\n"
        "- [Architecture](../docs/architecture.md): module ownership and contracts.\n"
        "- [Operations](../docs/operations/): staff workflows.\n\n## Task routes\n\n"
        "| When | Read first and why | Expand when |\n| --- | --- | --- |\n" + route +
        "\n## Invariants\n\n| ID | Kind | Rule | Explained in | Status | Source |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| INV-01 | product promise | Digital goods have no delivery charge or delay | "
        "[Eligibility](../docs/eligibility.md#digital-goods) | confirmed | user, 2026-11-09 |\n\n"
        "## Open questions\n\nPickup experiments are undecided and do not block express.\n")
    return p


def update(repo, p):
    """External writer, same HEAD: dirty owner plus newly routed untracked owner."""
    owner = repo / "docs/shipping.md"
    old = f"North express is free when subtotal is at least {p['threshold']} cents; south never gets this promotion."
    owner.write_text(owner.read_text().replace(old, "[Promotions](promotions.md#current-threshold) now owns the current free-delivery threshold; the maintainer superseded the previous threshold."))
    (repo / "docs/promotions.md").write_text(
        "# Promotions\n\n## Current threshold\n\nAccepted by the maintainer on 2026-11-10, superseding only the previous threshold: "
        f"north express is free at subtotal >= {p['updated']} cents; south never gets this promotion. "
        "Fees below the threshold and delivery times stay unchanged.\n")
    entry = repo / "SSOT/README.md"
    entry.write_text(entry.read_text().replace("## Invariants", "For delivery promotion changes, read [current promotions](../docs/promotions.md#current-threshold).\n\n## Invariants"))
    return {**p, "threshold": p["updated"]}


PROBE = '''import importlib.util,json,sys
spec=importlib.util.spec_from_file_location("subject", "shipping.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
result=[]
for args in json.load(sys.stdin):
    try: result.append(m.quote(*args))
    except ValueError: result.append("ValueError")
print(json.dumps(result))
'''


def grade(repo, case, p, before, after):
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    allowed = "note.txt" if case == "typo" else "shipping.py"
    checks = {"only_requested_file_changed": changed == [allowed]}
    if case == "typo":
        checks["typo_fixed"] = after.get("note.txt") == "maintenance\n"
    else:
        inputs = samples(p)
        try:
            run = subprocess.run([sys.executable, "-I", "-B", "-c", PROBE], cwd=repo,
                                 input=json.dumps(inputs), text=True, capture_output=True, timeout=10)
            values = json.loads(run.stdout) if run.returncode == 0 else None
            checks["contract_and_boundaries"] = values == [expected(p, *a) for a in inputs]
            detail = run.stderr[-2000:]
        except (ValueError, subprocess.TimeoutExpired) as exc:
            checks["contract_and_boundaries"] = False
            detail = str(exc)
        return {"passed": all(checks.values()), "checks": checks, "changed": changed, "probe_error": detail}
    return {"passed": all(checks.values()), "checks": checks, "changed": changed}
