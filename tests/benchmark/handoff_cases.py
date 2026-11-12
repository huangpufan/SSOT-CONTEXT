"""Cold handoff contracts: consumer deliverables and existing owners, without prescribed memory prose."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import uuid

CASES = ('reporting', 'editorial', 'museum')


def museum_fixture():
    # Independent-author confirmation, frozen before any outcome was observed.
    # The subject receives the normal prompt/owner, never this fixture record.
    return json.loads((Path(__file__).parent / 'fixtures/museum.json').read_text())


def contract(case, seed):
    if case == 'museum':
        return museum_fixture()['contract']
    tag = hashlib.sha256(f'{case}:{seed}'.encode()).hexdigest()[:8]
    if case == 'reporting':
        return {'modes': ['interactive', 'unattended'], 'initial': 'plain-text', 'replacement': 'markdown',
                'field': 'scope_' + tag, 'boundary': 'read_only', 'value': True,
                'private': 'diagnostic-' + tag, 'owner': 'docs/reporting.md', 'entry': 'SSOT/README.md',
                'output': 'policy.py', 'format': 4}
    if case == 'editorial':
        return {'modes': ['narration', 'quotation'], 'initial': 'house-style', 'replacement': 'verbatim',
                'field': 'attribution_' + tag, 'boundary': 'testimony_is_verified_fact', 'value': False,
                'private': 'diagnostic-' + tag, 'owner': 'creation/editorial.md', 'entry': 'CONTEXT.md',
                'output': 'publication_policy.json', 'format': 5}
    raise ValueError(case)


def expected(c, stale=False):
    updated = c['modes'][0] if c['format'] == 4 else c['modes'][1]
    return {mode: {'format': c['replacement'] if mode == updated and not stale else c['initial'],
                   'required_field': c['field'], c['boundary']: c['value']} for mode in c['modes']}


def prompts(c, capture_goal='automatic'):
    if capture_goal not in ('automatic', 'explicit'):
        raise ValueError('capture_goal must be automatic or explicit')
    if c['output'] == 'museum_label_policy.json':
        # This confirmation was authored with an explicit persistence goal.
        # Preserve its source words rather than appending the generic wording.
        return museum_fixture()['prompts']
    a, b = c['modes']
    changed = a if c['format'] == 4 else b
    other = b if changed == a else a
    turns = [f"We have decided the lasting policy: both {a} and {b} use {c['initial']}. "
            f"Each must include the field named exactly {c['field']}; {c['boundary']} remains {str(c['value']).lower()}. "
            "This is an accepted project decision, including for later collaborators. Give a short execution plan; do not implement the deliverable yet. "
            f"The temporary diagnostic token {c['private']} is only for this conversation: do not retain it in any project file.",
            f"Correction to the policy I just accepted: only {changed} now uses {c['replacement']} instead of {c['initial']}; "
            f"{other} still uses {c['initial']}. I accept this scoped replacement; retain the other accepted requirements. "
            "Give a brief updated plan; still do not implement the deliverable."]
    if capture_goal == 'explicit':
        goal = (" Save the accepted policy and enough decision provenance in the project's maintained documents "
                "for a later collaborator to determine what was accepted, what a scoped correction replaced, "
                "and which requirements remain in force. Use the existing document owners; no particular "
                "document format is required.")
        turns = [text + goal for text in turns]
    return turns


def consumer_prompt(c):
    if c['output'] == 'museum_label_policy.json':
        return museum_fixture()['consumer']
    modes = ', '.join(c['modes'])
    if c['format'] == 4:
        delivery = ("Implement policy.py with report_policy(mode). Return a dict with exactly these keys: format (lowercase string), required_field (the single exact field-name string), read_only (boolean); "
                    "raise ValueError for an unknown mode. Use only the standard library.")
    else:
        delivery = ("Create publication_policy.json, an object keyed by mode; each value has exactly format, required_field, "
                    "testimony_is_verified_fact; format is a lowercase string, required_field is the single exact field-name string, and testimony_is_verified_fact is boolean. It is consumed by our publishing system.")
    return (f"A previous collaborator settled policy for {modes}. The maintained entry is {c['entry']}. "
            f"Implement the currently accepted policy for both modes. {delivery} "
            f"Edit only {c['output']}; preserve the handoff documents. If a policy choice is absent, report the gap rather than invent it.")


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def build(root, c, kind='initial'):
    root.mkdir(parents=True)
    write(root, c['entry'], f"---\nssot_format: {c['format']}\nlanguage: en\n---\n# Maintained context\n\n"
          + ("## Invariants\n\nNo admitted constraints yet.\n\n## Open questions\n\nPolicy choices live in their owner.\n\n## Known traps and limits\n\nNone recorded.\n\n## Task routes\n\n" if c['format'] == 4 else "")
          + f"The current policy and its accepted changes belong to [Policy owner]({'../' if c['format'] == 4 else ''}{c['owner']}). "
          "Maintain this single owner; do not replace it with a task log.\n")
    body = '# Policy owner\n\nThis document owns the accepted policy and its reasons. Policy choices are not settled yet.\n'
    if kind in ('ceiling', 'stale'):
        policy = expected(c, stale=kind == 'stale')
        body = '# Policy owner\n\nThe user accepted the following policy for future collaborators.\n\n'
        for mode, values in policy.items():
            body += f"For {mode}, use {values['format']}, include the required field `{values['required_field']}`, and keep `{c['boundary']}` {str(c['value']).lower()}.\n\n"
        if kind == 'ceiling':
            body += 'This reflects the later scoped correction; the other mode and the independent boundary remain unchanged.\n'
    write(root, c['owner'], body)
    # Dirty, unrelated binary content is part of the preservation contract.
    (root / 'scratch.bin').write_bytes(b'\x80private-local-work\x00')
    write(root, 'note.txt', 'This task does not own this note.\n')


def handoff_files(repo):
    """Explicit transfer boundary: maintained Markdown owners, no logs/history/skills."""
    files = {}
    for name in ('SSOT', 'docs', 'creation'):
        base = repo / name
        if not base.exists():
            continue
        for path in base.rglob('*.md'):
            if path.is_symlink() or not path.resolve().is_relative_to(repo.resolve()):
                raise ValueError('handoff cannot follow outside/symlink owners')
            files[str(path.relative_to(repo))] = path.read_text()
    entry = repo / 'CONTEXT.md'
    if entry.is_file() and not entry.is_symlink():
        files['CONTEXT.md'] = entry.read_text()
    return files


def output_grade(repo, c, sandbox=None):
    target = repo / c['output']
    if not target.is_file() or target.is_symlink():
        return {'policy_matches': False, 'detail': 'deliverable absent or symlink'}
    try:
        if c['format'] == 5:
            observed = json.loads(target.read_text())
            unknown, errors = True, {}
        else:
            # Probe the actual function in isolation; oracle choices never enter the subject workspace.
            marker = "oracle-" + uuid.uuid4().hex + ":"
            script = ("import json,policy\n"
                      "result={}; errors={}\n"
                      f"for m in {c['modes']!r}:\n"
                      "    try: result[m]=policy.report_policy(m)\n"
                      "    except Exception as exc: errors[m]=type(exc).__name__+': '+str(exc)\n"
                      "try: policy.report_policy('unknown')\n"
                      "except ValueError: unknown=True\n"
                      "except Exception: unknown=False\n"
                      "else: unknown=False\n"
                      f"print({marker!r}+json.dumps({{'result':result,'errors':errors,'unknown':unknown}}))")
            process = subprocess.run((sandbox or []) + ['python3', '-B', '-c', script], cwd=repo,
                                     capture_output=True, text=True, timeout=10)
            if process.returncode:
                return {'policy_matches': False, 'detail': process.stderr[-1200:]}
            lines = [line[len(marker):] for line in process.stdout.splitlines() if line.startswith(marker)]
            if len(lines) != 1:
                return {"policy_matches": False, "detail": "function probe did not return its result"}
            result = json.loads(lines[0])
            observed, unknown, errors = result['result'], result['unknown'], result['errors']
        return {'policy_matches': json.dumps(observed, sort_keys=True) == json.dumps(expected(c), sort_keys=True) and unknown, 'observed': observed,
                'unknown_mode_rejected': unknown, 'mode_errors': errors}
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        return {'policy_matches': False, 'detail': str(exc)}


def private_scan(repo, token):
    """Scan literal bytes in all project regular files, including .git/.agents.

    Do not follow symlinks or decode compressed Git objects. This is a final
    snapshot check, not an event audit: a token written then removed is unseen.
    Return only booleans, never file contents from this privacy check.
    """
    found, complete = False, True
    def unavailable(_exc):
        nonlocal complete
        complete = False
    for folder, _dirs, files in os.walk(repo, followlinks=False, onerror=unavailable):
        for name in files:
            path = Path(folder) / name
            try:
                if not stat.S_ISREG(path.lstat().st_mode):
                    continue
                # A file replaced with a symlink between lstat/open must never
                # make the observer read a target outside the project.
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(fd, 'rb') as source:
                    if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                        complete = False
                        continue
                    tail = b''
                    while data := source.read(65536):
                        chunk = tail + data
                        found = found or token in chunk
                        tail = chunk[-max(len(token) - 1, 0):] if len(token) > 1 else b''
            except OSError:
                complete = False
    return found, complete


def writer_checks(repo, c, before, after):
    owner_dir = str(Path(c['owner']).parent)
    allowed = lambda p: p == c['entry'] or (p.endswith('.md') and p.startswith(owner_dir + '/'))
    changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
    # Newly created directories are permitted only beneath maintained owner roots.
    unauthorized = [p for p in changed if not allowed(p) and not
                    (p in after and after[p]['kind'] == 'directory' and (p == owner_dir or p.startswith(owner_dir + '/')))]
    try:
        files = handoff_files(repo)
        transferable = True
    except ValueError:
        files, transferable = {}, False
    private, private_complete = private_scan(repo, c['private'].encode())
    return {'owner_transfer_valid': transferable, 'write_scope_preserved': not unauthorized, 'private_token_not_retained': not private,
            'private_scan_complete': private_complete,
            'canonical_owner_retained': c['owner'] in files and c['entry'] in files}, unauthorized
