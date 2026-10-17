#!/usr/bin/env python3
"""Recompute and store P4 promotion assessments using the current gate."""
import importlib.util
import json

REPO = '/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main'
B = REPO + '/sps2'
D = "2026-10-03"

spec = importlib.util.spec_from_file_location(
    'pg', B + '/capability/promotion_gates.py')
pg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pg)

p = B + '/capability/registry.json'
reg = json.load(open(p))
promoted, assessments = [], []
for c in reg['capabilities']:
    res, blocking = pg.evaluate(c)
    rec = pg.decide(blocking)
    c['promotion_assessment'] = {
        'assessed_phase': 'P4',
        'gates': {k: {'gate': v['gate'], 'pass': v['pass'], 'reason': v['reason']}
                  for k, v in sorted(res.items())},
        'blocking_gates': blocking,
        'recommendation': rec,
        'promotion_decision': ('PROMOTED_TO_PRODUCTION' if rec == 'PROMOTE'
                              else 'NOT_PROMOTED'),
    }
    # Lifecycle wording must stay honest about what actually happened. Nothing
    # was installed, so a promoted capability is EVALUATED and approved for
    # production, not ACTIVE. A deferred capability is DEFERRED explicitly.
    if rec == 'PROMOTE':
        c['lifecycle_state'] = 'EVALUATED'
    elif rec == 'DEFER':
        c['lifecycle_state'] = 'DEFERRED'
    else:
        c['lifecycle_state'] = 'CANDIDATE'
    assessments.append({'capability_id': c['capability_id'], 'name': c['name'],
                        'blocking_gates': blocking, 'recommendation': rec,
                        'gate_results': {k: v['pass'] for k, v in
                                         sorted(res.items())}})
    if rec == 'PROMOTE':
        promoted.append(c['capability_id'])

reg['counts'] = {'total': len(reg['capabilities']), 'promoted': len(promoted),
                 'candidate': len(reg['capabilities']) - len(promoted),
                 'deferred': len(reg.get('deferred') or [])}
json.dump(reg, open(p, 'w'), indent=2)
json.dump({'schema': 'sps2.promotion-assessments/v1', 'phase': 'P4',
           'generated': D,
           'note': ('Each candidate was evaluated independently by the hardened '
                    'gate. Gate results are computed, never asserted. A failed '
                    'gate was not worked around.'),
           'recommendations': ['PROMOTE', 'REMAIN_CANDIDATE', 'DEFER', 'REJECT'],
           'assessments': assessments,
           'counts': {'total': len(assessments), 'promoted': len(promoted)}},
          open(B + '/capability/promotion-assessments.json', 'w'), indent=2)
print('promoted:', promoted)
print('counts  :', reg['counts'])
for a in assessments:
    print('  %-13s %-30s %-20s %s'
          % (a['capability_id'], a['name'], str(a['blocking_gates']),
             a['recommendation']))