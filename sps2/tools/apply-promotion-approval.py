#!/usr/bin/env python3
"""Record the explicit User production-promotion approval (Gate H).

The User approved promotion ONLY for capabilities that already satisfy every
other gate. CAP-P03-005 is explicitly excluded: its gates F and K are
unsatisfied, and this script does not touch it, does not bypass F or K, and
invents no LCP or INP evidence.
"""
import importlib.util
import json

REPO = '/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main'
B = REPO + '/sps2'
DATE = '2026-10-04'
APPROVER = 'User'

# The User named these four explicitly, each conditioned on all gates passing.
APPROVED = ['CAP-P03-001', 'CAP-P03-002', 'CAP-P03-003', 'CAP-P03-004']
# Explicitly excluded by the User. Never granted approval.
EXCLUDED = ['CAP-P03-005']

spec = importlib.util.spec_from_file_location(
    'pg', B + '/capability/promotion_gates.py')
pg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pg)

p = B + '/capability/registry.json'
reg = json.load(open(p))

for c in reg['capabilities']:
    cid = c['capability_id']
    if cid in EXCLUDED:
        # Record the exclusion explicitly. No approval is written.
        c['approval'] = {
            'state': 'PENDING_USER_APPROVAL',
            'decided_by': None,
            'note': 'Explicitly NOT approved for promotion by the User on '
                    + DATE + '. Gates F (no executable CLS verifier) and K '
                    '(CONF-001 unresolved) are unsatisfied. Neither gate was '
                    'bypassed and no LCP or INP evidence was invented.',
        }
        continue
    if cid not in APPROVED:
        continue

    # Re-evaluate first. Approval is written ONLY if every other gate passes.
    res, blocking = pg.evaluate(c)
    others = [g for g in blocking if g != 'H']
    if others:
        c['approval'] = {
            'state': 'PENDING_USER_APPROVAL',
            'note': 'User approval was conditional on all gates passing. '
                    'Not granted because %s still block.' % ','.join(others),
        }
        print('  %s NOT approved; still blocked by %s' % (cid, others))
        continue

    passing = sorted(g for g, v in res.items() if v['pass'])
    c['approval'] = {
        'state': 'APPROVED',
        'required': True,
        'decided_by': APPROVER,
        'decided_on': DATE,
        'scope': 'production promotion only',
        'explicitly_not_approved': [
            'P5, and the beginning of any P5 work.',
            'Promotion of CAP-P03-005, which remains blocked by gates F and K.',
            'Installing any skill, MCP, dependency or external software.',
        ],
        'gates_passed_at_approval': passing + ['H'],
        'evidence': 'User instruction: "I explicitly approve production '
                    'promotion under Gate H for the capabilities that already '
                    'satisfy every other required gate."',
    }
    c['promotion_record'] = {
        'promoted': True,
        'promoted_on': DATE,
        'promoted_by': APPROVER,
        'previous_lifecycle_state': c.get('lifecycle_state'),
        'previous_approval_state': 'PENDING_USER_APPROVAL',
        'previous_blocking_gates': sorted(blocking),
        'gate_results_at_promotion': {k: v['pass'] for k, v in
                                      sorted(res.items())},
        'gate_reasons': {k: v['reason'] for k, v in sorted(res.items())},
        'basis': 'Gate H satisfied by explicit User approval; every other '
                 'gate A-K computed and passing at promotion time.',
        'not_based_on': ['popularity', 'recency', 'research interest',
                         'recency of verification'],
    }
    print('  %s APPROVED by %s; all other gates pass (%s)'
          % (cid, APPROVER, ','.join(passing)))

for c in reg['capabilities']:
    if c['capability_id'] in EXCLUDED:
        c['promotion_record'] = {
            'promoted': False,
            'state': 'DEFER',
            'reason': 'Gates F and K unsatisfied: no executable CLS verifier '
                      'exists, and CONF-001 is unresolved. Gate H approval was '
                      'withheld by the User. Neither gate was bypassed.',
            'classified_on': DATE,
        }

json.dump(reg, open(p, 'w'), indent=2)
print('approval recorded; now recompute assessments')