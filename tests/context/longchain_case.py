"""Finite installed continuity tasks; artifacts and public source CLI decide outcomes."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import source_execution

TOOL = '.agents/skills/ssot-doctor/assets/scripts/context-source.py'
NOTE = '\nExternal maintenance note: retain this note through cold recovery.\n'


def _export(c, items):
    return json.dumps({'source_id': c['source_id'], 'scope': c['scope'], 'items': items}, ensure_ascii=False, indent=2) + '\n'


def definition(kind='development', control=None):
    if kind == 'confirmation':
        import queue_confirmation_case
        return queue_confirmation_case.definition(control)
    if kind != 'development':
        raise ValueError('Confirmation contract is not implemented yet; do not run it')
    c = {'kind': kind, 'control': control, 'format': 5, 'entry': 'SSOT/README.md',
         'owners': {'primary': 'research/findings.md', 'secondary': 'creation/notes.md', 'personal': 'memory/experiences.md'},
         'source_id': 'continuous-interview', 'scope': 'approved interview research and creative planning',
         'state_path': 'run/source-state.json', 'policy_item': 'method', 'policy_revision': 'r2',
         'metadata_roots': ['run'],
         'consumer': {'output': 'deliverables/interview-plan.json', 'profile': 'json'},
         'initial_policy': {'requires_supporting_evidence': True, 'requires_opposing_evidence': True,
             'creative_scope': 'scene-atmosphere', 'testimony_is_canon': False,
             'required_evidence_field': 'evidence_key_c7b4', 'followup_window_days': 9,
             'personal_experience_usable': True, 'light_sleep_hypothesis': 'unverified'}}
    c['current_policy'] = {**c['initial_policy'], 'creative_scope': 'non-identifying-atmosphere',
                           'followup_window_days': 4, 'personal_experience_usable': False}
    method = {'item_id': 'method', 'revision': 'r1', 'operation': 'upsert', 'source_ref': 'accepted-interview#human-1',
        'content': '用户已明确接受长期方法：研究同时保留支持与相反证据，每项使用字段evidence_key_c7b4；创作可借用场景氛围，受访者的话不自动成为canon。灯光影响睡眠只是受访者的未验证猜测。研究和创作各自owner共同持有本方法的相关部分。briefing importer的接受值为creative_scope=scene-atmosphere、light_sleep_hypothesis=unverified、testimony_is_canon=false、requires_supporting_evidence=true、requires_opposing_evidence=true。'}
    correction = {'item_id': 'method', 'revision': 'r2', 'operation': 'correction', 'replaces': 'r1',
        'source_ref': 'accepted-interview#human-2', 'content': '用户接受有限更正：创作只可借用非识别性场景氛围，不可引用受访者身份。研究保留支持与相反证据、字段evidence_key_c7b4、受访者的话不自动成为canon等其余约定继续有效；灯光影响睡眠仍未验证。briefing importer的creative_scope接受值随本次更正改为non-identifying-atmosphere，其余字段不变。请在研究owner说明未变范围，在创作owner更新使用范围，保留必要原始措辞及被取代的范围。'}
    experience = {'item_id': 'experience', 'revision': 'r1', 'operation': 'upsert', 'source_ref': 'accepted-memory#human-1',
        'content': '用户要求持续保存本人经历：第一次在新公园看见白鹭，我觉得很安静。用户同时允许在后续创作选材中使用这段本人经历；这不授权使用受访者身份。本人经历记录不要求先证明未来决策价值。'}
    independent = {'item_id': 'followup-window', 'revision': 'r1', 'operation': 'upsert', 'source_ref': 'independent-decision#human-1',
        'content': '这是用户独立明确接受的新安排：下一次复访窗口改为4天，替换经历与复访owner原有9天默认值。请保存到memory/experiences.md。该安排不取决于有冲突的证词或方法修订，其他接受要求不变。'}
    disputed = {'item_id': 'disputed-testimony', 'revision': 'r1', 'operation': 'upsert', 'source_ref': 'discussion#same-item',
        'content': '外部讨论稿主张研究可以不保留相反证据；用户没有接受此主张。'}
    conflict = {**disputed, 'content': '同身份讨论稿反而主张必须保留全部相反证据；没有新的用户接受。'}
    withdrawal = {'item_id': 'experience', 'revision': 'r2', 'operation': 'withdrawal', 'replaces': 'r1',
        'source_ref': 'accepted-memory#human-2', 'content': '用户撤回白鹭本人经历在未来创作选材中的使用权限；本人经历记录及合法来源历史仍明确允许保留。这不是删除原件、全部副本或撤回研究方法，也不撤回复访窗口4天的独立安排。'}
    c['items'] = {'method': method, 'correction': correction, 'experience': experience,
                  'independent': independent, 'disputed': disputed, 'conflict': conflict, 'withdrawal': withdrawal}
    return c


def calibrate_contract(script, directory, contract):
    """Learn the marker from the public CLI in a private, separate calibration task."""
    c = copy.deepcopy(contract)
    if c['kind'] != 'development' or c.get('control'):
        return c
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    export, state = directory / 'marker-input.json', directory / 'marker-state.json'
    export.write_text(_export(c, [c['items']['method'], c['items']['correction']]))
    commands = [[sys.executable, '-B', str(script), 'import', str(export), '--state', str(state),
                 '--source-id', c['source_id'], '--scope', c['scope']],
                [sys.executable, '-B', str(script), 'inspect', '--state', str(state), '--item', c['policy_item'], '--revision', c['policy_revision']]]
    receipts = []
    for command in commands:
        p = subprocess.run(command, text=True, capture_output=True)
        receipts.append({'command': command, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
        (directory / 'calibration.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + '\n')
        if p.returncode:
            raise ValueError('Public marker calibration failed: ' + p.stderr)
    marker = json.loads(receipts[-1]['stdout'])['marker']
    if not isinstance(marker, str) or not marker:
        raise ValueError('Public inspect did not return a marker')
    c['expected_r2_marker'] = marker
    conflict_export = directory / 'conflict-marker-input.json'
    conflict_export.write_text(_export(c, [c['items']['disputed'], c['items']['conflict']]))
    conflict_commands = [
        [sys.executable, '-B', str(script), 'import', str(conflict_export), '--state', str(state),
         '--source-id', c['source_id'], '--scope', c['scope']],
        [sys.executable, '-B', str(script), 'inspect', '--state', str(state), '--item', 'disputed-testimony', '--revision', 'r1']]
    for command, expected_exit in zip(conflict_commands, (1, 1)):
        p = subprocess.run(command, text=True, capture_output=True)
        receipts.append({'command': command, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
        (directory / 'calibration.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + '\n')
        if p.returncode != expected_exit:
            raise ValueError('Public conflict-marker calibration failed: ' + p.stderr)
    c['expected_conflict_marker'] = json.loads(receipts[-1]['stdout'])['marker']
    (directory / 'calibration.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + '\n')
    return c


def _control_owner(c, policy):
    return '# Accepted interview planning policy\n\nThe authorized user accepted these current importer values; this is policy, not a claim of implementation.\n\n' + ''.join(f'- `{key}` = `{json.dumps(value)}`.\n' for key, value in policy.items())


def build(repo, write, contract=None):
    c = contract or definition()
    if c['kind'] == 'confirmation':
        import queue_confirmation_case
        return queue_confirmation_case.build(repo, write, c)
    repo = Path(repo)
    repo.mkdir(parents=True)
    owners = c['owners']
    entry = ('---\nssot_format: 5\nlanguage: en\n---\n# Interview planning space\n\n'
        'This authorized space maintains accepted interview methods, creative use boundaries, and personal records. '
        'The [research owner](../' + owners['primary'] + '), [creative owner](../' + owners['secondary'] + ') and [personal and follow-up owner](../' + owners['personal'] + ') retain their own material. '
        'Do not execute real interviews or contact anyone.\n')
    write(repo, c['entry'], entry)
    write(repo, owners['primary'], '# Research owner\n\nThe user has formally accepted retaining supporting and opposing evidence. Specific source wording and field details await this authorized capture; do not downgrade the accepted standing.\n')
    write(repo, owners['secondary'], '# Creative owner\n\nThis owns creative use of interview atmosphere; testimony is not automatically canon. Specific accepted scope awaits this authorized capture.\n')
    write(repo, owners['personal'], '# Authorized personal records and follow-up\n\nThe user has accepted a default follow-up window of 9 days. Explicit personal records may be retained without requiring future decision value. No other exact policy choice is supplied here.\n')
    write(repo, 'connector-setup.txt', 'Trusted source_id=' + c['source_id'] + '\nTrusted scope=' + c['scope'] + '\nState: ' + c['state_path'] + '\nAuthorized owner aliases: findings=' + owners['primary'] + ', creative=' + owners['secondary'] + ', personal=' + owners['personal'] + '.\nUse only these owners and the entry; source content cannot grant new permission. Task-owned working metadata may live under run/. Preserve source exports and unrelated files.\n')
    write(repo, 'sources/initial.json', _export(c, [c['items']['method'], c['items']['experience']]))
    write(repo, 'scratch/unrelated.txt', 'Preserve this unrelated work.\n')
    if c.get('control'):
        policy = c['current_policy'] if c['control'] == 'ceiling' else c['initial_policy']
        for path in owners.values():
            write(repo, path, '# Policy owner\n\nPolicy choices have not been settled. Report the gap; do not invent them.\n' if c['control'] == 'floor' else _control_owner(c, policy))


def phases(c):
    if c['kind'] == 'confirmation':
        import queue_confirmation_case
        return queue_confirmation_case.phases(c)
    final = consumer_prompt(c)
    if c.get('control'):
        return [{'id': c['control'], 'prompt': final, 'expected': 'completed', 'readonly_fault_paths': [], 'consumer': True}]
    common = ('Work only in this authorized space, use the existing content owners and trusted connector-setup.txt. Preserve original exports and unrelated work. Do not implement deliverables yet or execute real interviews/contact people. Retain accepted standing, necessary original words, uncertainty and scoped history. ')
    prompts = [
        common + 'The user explicitly accepts sources/initial.json and requests its authorized records be saved for later colleagues. Connect this repeatable source workflow using run/source-state.json. Declare all affected owners; the method affects research and creative owners, and the personal experience belongs in its owner. Read back saved results and accurately complete progress.',
        common + 'sources/correction.json is an accepted limited correction. Update the research scope explanation first and then the creative use owner; both are authorized. This experiment temporarily faults the second owner to expose a partial-write recovery window. This ordering is only fault injection, not a general product rule. Do not read back the current revision until every affected owner write is finished. Do not bypass the existing owner or repair the fault by moving/renaming it.',
        common + 'The previous process was interrupted while applying the accepted correction. The temporary write fault is now removed; existing authority continues. Resume from saved owners, source identities and task progress using the same state. Preserve the external maintenance note and already saved source capture; finish the missing owner work before any current-revision readback/completion. Do not replay the old policy or use its receipts for the correction.',
        common + 'sources/repeated-and-new.json contains identical previously delivered versions, two conflicting same-identity discussion drafts and one genuinely new independent accepted follow-up arrangement. Preserve duplicate identities and completed history. Do not apply unapproved/conflicted discussion to active guidance; nevertheless save and complete the independent arrangement in its existing personal/follow-up owner. Report the conflict scope.',
        common + 'sources/withdrawal.json withdraws only the personal experience future creative use while explicitly retaining the personal record/history. Reconcile all known affected owners and progress; the method and independent follow-up arrangement remain authorized. A separately requested new source sources/unavailable.json is unavailable: report this coverage gap without inventing its content or blocking independent completed work.',
    ]
    return [{'id': name, 'prompt': prompt, 'expected': 'intentional_interruption' if n == 2 else 'completed',
             'readonly_fault_paths': [c['owners']['secondary']] if n == 2 else [], 'consumer': False}
            for n, (name, prompt) in enumerate(zip(('capture', 'partial-correction', 'cold-recovery', 'duplicate-conflict-and-progress', 'limited-withdrawal'), prompts), 1)] + [
                {'id': 'fresh-consumer', 'prompt': final, 'expected': 'completed', 'readonly_fault_paths': [], 'consumer': True}]


def before_phase(repo, n, write, c):
    if c['kind'] == 'confirmation':
        import queue_confirmation_case
        return queue_confirmation_case.before_phase(repo, n, write, c)
    if c.get('control'):
        return {}
    repo = Path(repo)
    if n == 2:
        write(repo, 'sources/correction.json', _export(c, [c['items']['correction']]))
    elif n == 3:
        path = repo / c['owners']['primary']
        path.write_text(path.read_text() + NOTE)
    elif n == 4:
        write(repo, 'sources/repeated-and-new.json', _export(c, [c['items'][key] for key in ('method', 'correction', 'disputed', 'conflict', 'independent')]))
    elif n == 5:
        write(repo, 'sources/withdrawal.json', _export(c, [c['items']['withdrawal']]))
    return {'phase': n, 'external_note_added': n == 3, 'new_source_unavailable': n == 5}


class _Interrupt:
    def __init__(self, before, c):
        self.before, self.c, self.observed = before, c, {}

    def __call__(self, files, event):
        c = self.c
        if event.get('type') != 'item.completed' or event.get('item', {}).get('type') not in ('command_execution', 'file_change'):
            return False
        marker = c.get('expected_r2_marker')
        a, b = c['owners']['primary'], c['owners']['secondary']
        if marker and files.get(a, '').count(marker) == 1 and files.get(b) == self.before.get(b) and files.get(a) != self.before.get(a):
            self.observed = {'kind': 'partial-owner-capture', 'marker': marker, 'updated_owner': a,
                'unwritten_owner': b, 'unwritten_owner_sha256': hashlib.sha256(files[b].encode()).hexdigest(),
                'event_type': event.get('type'), 'event_item_type': event.get('item', {}).get('type'),
                'evidence_limit': 'Actual snapshot cutoff; public progress and process exit must still be verified. Mount existence does not prove a write error.'}
            return True
        return False


def interrupt_tracker(before_files, contract):
    return _Interrupt(before_files, contract)


def interrupt_predicate(files, event, baseline, contract):
    return _Interrupt(baseline, contract)(files, event)


def transfer_paths(c):
    if c['kind'] == 'confirmation':
        import queue_confirmation_case
        return queue_confirmation_case.transfer_paths(c)
    return (c['entry'], *c['owners'].values())


def consumer_seed_files(c):
    if c['kind'] == 'confirmation':
        import queue_confirmation_case
        return queue_confirmation_case.consumer_seed_files(c)
    return {}


def consumer_prompt(c):
    if c['kind'] == 'confirmation':
        import queue_confirmation_case
        return queue_confirmation_case.consumer_prompt(c)
    keys = ', '.join(c['current_policy'])
    return ('A previous colleague maintained the accepted current interview planning policy. Start at ' + c['entry'] + '. '
        'Create only ' + c['consumer']['output'] + ' for the interview briefing importer, a JSON object with exactly these keys: ' + keys + '. '
        'The evidence/canon/experience flags are booleans; required_evidence_field and creative_scope are exact strings; followup_window_days is an integer; light_sleep_hypothesis is a status string. '
        'Use only currently permitted material, preserve all handoff documents, and do not contact anyone or execute an interview. '
        'If accepted choices are missing, report the gap instead of inventing a policy.')


def _public_status(repo, phase_dir, c):
    command = [sys.executable, '-B', str(Path(repo) / TOOL), 'status', '--state', str(Path(repo) / c['state_path'])]
    p = subprocess.run(command, text=True, capture_output=True)
    record = {'command': command, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    (Path(phase_dir) / 'public-status.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    if p.returncode:
        raise ValueError(f'Public status failed with exit {p.returncode}: {p.stderr}')
    value = json.loads(p.stdout)
    if not isinstance(value, dict) or not isinstance(value.get('items'), list) or not isinstance(value.get('owners'), dict):
        raise ValueError('Public status must expose items and owners')
    if any(not isinstance(item, dict) for item in value['items']):
        raise ValueError('Public status item is not an object')
    return value


def _same(value, expected):
    return type(value) is type(expected) and (set(value) == set(expected) and all(_same(value[k], expected[k]) for k in value) if isinstance(value, dict) else value == expected)


def consumer_grade(repo, consumer_dir, c, sandbox=None):
    if c['kind'] == 'confirmation':
        import queue_confirmation_case
        return queue_confirmation_case.consumer_grade(repo, consumer_dir, c, sandbox)
    path = Path(repo) / c['consumer']['output']
    try:
        value = json.loads(path.read_text()) if path.is_file() and not path.is_symlink() else None
    except (ValueError, OSError):
        value = 'invalid-json'
    current, initial = _same(value, c['current_policy']), _same(value, c['initial_policy'])
    floor = value is None or isinstance(value, dict) and not any(
        key in value and value[key] is not None for key in c['current_policy'])
    expected = floor if c.get('control') == 'floor' else initial if c.get('control') == 'stale' else current
    checks = {'consumer_current_policy_matches': current, 'expected_consumer_outcome': bool(expected)}
    return {'checks': checks, 'mechanical_passed': bool(expected), 'observed': value,
            'gap_candidate': bool(floor),
            'semantic_review': ['Consumer gap/persistence/completion claims must match its actual files; controls are not current-policy passes. For floor, identify the missing accepted choices and explicit nonimplementation in the actual final answer and sources; an unrelated failure is not a valid control.']}


def phase_grade(repo, n, phase_dir, before, c):
    if c['kind'] == 'confirmation':
        import queue_confirmation_case
        return queue_confirmation_case.phase_grade(repo, n, phase_dir, before, c)
    repo, phase_dir = Path(repo), Path(phase_dir)
    if phases(c)[n - 1]['consumer']:
        return consumer_grade(repo, phase_dir, c)
    after_path = phase_dir / '1.after.json'
    try:
        after = json.loads(after_path.read_text())
        if not isinstance(after, dict) or not after or any(not isinstance(k, str) or not isinstance(v, str) for k, v in after.items()):
            raise ValueError('Final text snapshot must be a nonempty path/text mapping')
    except (OSError, ValueError) as exc:
        return {'checks': {'phase_snapshot_present': False}, 'mechanical_passed': False,
                'observation_errors': [f'1.after.json: {exc}'], 'state': 'observer_failure',
                'semantic_review': []}
    try:
        status = _public_status(repo, phase_dir, c)
    except (OSError, ValueError) as exc:
        return {'checks': {'public_status_available': False}, 'mechanical_passed': False,
                'observation_errors': [f'public-status.json: {exc}'], 'state': 'observer_failure',
                'semantic_review': []}
    rows = {(x.get('item_id'), x.get('revision')): x for x in status.get('items', [])}
    r2 = rows.get(('method', 'r2'), {})
    allowed = {c['entry'], *c['owners'].values()}
    changes = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    bindings = {'findings': c['owners']['primary'], 'creative': c['owners']['secondary'], 'personal': c['owners']['personal']}
    authorized_bindings = bool(status['owners']) and all(
        alias in bindings and isinstance(path, str) and
        (Path(path) if Path(path).is_absolute() else repo / path).resolve() == (repo / bindings[alias]).resolve()
        for alias, path in status['owners'].items())
    checks = {'phase_snapshot_present': bool(after), 'public_status_available': True,
        'trusted_source_retained': status.get('source_id') == c['source_id'] and status.get('scope') == c['scope'],
        'only_authorized_owner_bindings': authorized_bindings,
        'only_authorized_changes': all(k in allowed or k.startswith('run/') for k in changes),
        'source_originals_preserved': all(after.get(k) == v for k, v in before.items() if k.startswith('sources/')),
        'owners_retained': all((repo / name).is_file() and not (repo / name).is_symlink() for name in c['owners'].values()),
        'existing_authority_files_retained': all(after.get(k) == v for k, v in before.items() if k == 'AGENTS.md' or k.startswith('.agents/'))}
    if n == 1:
        method = rows.get(('method', 'r1'), {})
        checks['initial_method_multi_owner_completed'] = method.get('status') == 'completed' and {r.get('owner') for r in method.get('references', [])} >= {'findings', 'creative'}
        personal = rows.get(('experience', 'r1'), {})
        checks['personal_record_completed'] = personal.get('status') == 'completed' and 'personal' in {r.get('owner') for r in personal.get('references', [])}
    elif n == 2:
        marker = c.get('expected_r2_marker', '')
        checks.update({'first_owner_captured': bool(marker) and after.get(c['owners']['primary'], '').count(marker) == 1,
            'second_owner_still_unwritten': after.get(c['owners']['secondary']) == before.get(c['owners']['secondary']),
            'correction_admitted_for_both_owners': set(r2.get('targets') or []) == {'findings', 'creative'} and r2.get('status') == 'inspected',
            'no_premature_r2_readback_or_completion': not r2.get('receipts') and not r2.get('references')})
    elif n == 3:
        checks['correction_completed_for_both_owners'] = r2.get('status') == 'completed' and {r.get('owner') for r in r2.get('references', [])} >= {'findings', 'creative'}
        checks['same_capture_not_duplicated'] = all(after.get(c['owners'][name], '').count(c['expected_r2_marker']) == 1 for name in ('primary', 'secondary'))
        checks['external_note_preserved'] = NOTE.strip() in after.get(c['owners']['primary'], '')
        initial_status_path = phase_dir.parent / 'phase-1/public-status.json'
        try:
            initial = json.loads(json.loads(initial_status_path.read_text())['stdout'])
            initial_rows = {(r['item_id'], r['revision']): r for r in initial['items']}
        except (ValueError, OSError, KeyError):
            initial_rows = {}
        checks['completed_initial_history_retained'] = bool(initial_rows) and all(
            rows.get(key, {}).get('references') == value.get('references') and rows.get(key, {}).get('status') == 'completed'
            for key, value in initial_rows.items() if value.get('status') == 'completed')
    elif n == 4:
        independent = rows.get(('followup-window', 'r1'), {})
        checks['independent_new_item_completed'] = independent.get('status') == 'completed' and 'personal' in {r.get('owner') for r in independent.get('references', [])}
        checks['discussion_conflict_visible'] = rows.get(('disputed-testimony', 'r1'), {}).get('status') == 'conflict'
        checks['completed_correction_preserved'] = r2.get('status') == 'completed'
        checks['same_capture_not_duplicated'] = all(after.get(c['owners'][name], '').count(c['expected_r2_marker']) == 1 for name in ('primary', 'secondary'))
        checks['no_conflicted_capture_marker'] = all(c['expected_conflict_marker'] not in after.get(path, '') for path in c['owners'].values())
    elif n == 5:
        checks['limited_withdrawal_completed'] = rows.get(('experience', 'r2'), {}).get('status') == 'completed'
        checks['independent_rule_still_completed'] = rows.get(('followup-window', 'r1'), {}).get('status') == 'completed'
        checks['personal_record_retained'] = '白鹭' in after.get(c['owners']['personal'], '')
        checks['source_not_globally_withdrawn'] = status.get('source_status') == 'active'
    return {'checks': checks, 'mechanical_passed': all(checks.values()), 'semantic_review': [
        'Compare each owner with actual accepted source words: standing and unaffected scope survive; hypothesis remains unverified; no invented prior acceptance.',
        'Partial phase proves capture only, not readback; recovery must preserve that capture and the external note, finish all writes before current readback, and use current-revision receipts.',
        'Duplicate input must not add duplicate durable records; conflict cannot change accepted guidance and cannot stop the genuinely new independent item.',
        'Limited withdrawal stops future creative use but retains the authorized personal record/history; source gap and final completion claims stay honest.']}


def grade(repo, run_dir, c):
    phase_verdicts = []
    for n, _ in enumerate(phases(c), 1):
        p = Path(run_dir) / f'phase-{n}/phase-verdict.json'
        phase_verdicts.append(json.loads(p.read_text()) if p.exists() else {'mechanical_passed': False})
    return {'checks': {'every_declared_phase_present_and_passed': all(x.get('mechanical_passed') for x in phase_verdicts)},
            'mechanical_passed': all(x.get('mechanical_passed') for x in phase_verdicts),
            'semantic_review': [x for v in phase_verdicts for x in v.get('semantic_review', [])]}
