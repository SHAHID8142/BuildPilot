#!/usr/bin/env python3
"""Record the explicit User approval of phase P4 as a completed, verified phase.

Scope is deliberately bounded:
  - P4 requirements and decisions become APPROVED, attributed to the User.
  - The licence stays UNRESOLVED. No licence is invented or assumed.
  - Zero capabilities are promoted.
  - No P5 record is created and no P5 approval is implied.
  - Research gaps, the P3 incident classification and checkpoint a7767cf are
    left exactly as they were.
"""
import json

B = '/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main/sps2'
DATE = '2026-10-04'
APPROVER = 'User'

# Every approval must name an identifiable human approver. An approval
# attributed to an agent, a model, or this script is a fabricated approval and
# is rejected by validate-p4.sh.
APPROVAL = {
    'required': True,
    'state': 'APPROVED',
    'approved_by': APPROVER,
    'approved_on': DATE,
    'scope': 'P4 only: phase completion and verification. This approval does '
             'NOT authorise production promotion of any capability, does NOT '
             'resolve the licence question, and does NOT approve or begin P5.',
}


def load(p):
    return json.load(open(B + '/' + p))


def save(p, d):
    json.dump(d, open(B + '/' + p, 'w'), indent=2)
    open(B + '/' + p, 'a').write('\n')


def merge(approval):
    a = dict(approval or {})
    a.update(APPROVAL)
    return a


# ── requirements ────────────────────────────────────────────────────────────
req = load('requirements/P4-REQUIREMENTS.json')
for r in req['requirements']:
    r['approval'] = merge(r.get('approval'))
save('requirements/P4-REQUIREMENTS.json', req)

# ── decisions ───────────────────────────────────────────────────────────────
dec = load('decisions/P4-DECISIONS.json')
for d in dec['decisions']:
    d['approval'] = merge(d.get('approval'))
    if d.get('status') == 'PROPOSED':
        d['status'] = 'DECIDED'
# ── the licence decision, recorded as an explicit User decision ─────────────
dec['decisions'].append({
    'decision_id': 'DEC-0022',
    'title': 'The repository licence remains unresolved and was not chosen',
    'decision': 'No licence was selected, added or inferred. The repository '
                'licence is recorded as UNRESOLVED and gate D continues to '
                'block every production promotion until the User makes an '
                'explicit licence decision.',
    'reason': 'The user instructed that the licence must not be invented or '
              'assumed, and that it be recorded as unresolved unless an '
              'explicit licence decision is provided. Selecting a licence is a '
              'legal and ownership decision reserved to the User.',
    'evidence': ['EV-P4-018'],
    'alternatives': [
        {'option': 'Infer MIT or another permissive licence from the '
                   'project-authored source',
         'rejected_because': 'The user explicitly prohibited assuming a '
                             'licence. An unlicensed repository is '
                             'all-rights-reserved by default.'},
        {'option': 'Add a LICENSE file to unblock gate D',
         'rejected_because': 'Choosing a licence is a legal decision reserved '
                             'to the user and was explicitly withheld.'},
    ],
    'status': 'DECIDED',
    'approval': dict(APPROVAL),
    'unresolved': {
        'item': 'repository_licence',
        'state': 'UNRESOLVED',
        'resolved_by': 'User explicit licence decision (not yet given)',
        'blocking_gate': 'D',
    },
})
save('decisions/P4-DECISIONS.json', dec)
# ── handoff ─────────────────────────────────────────────────────────────────
ho = load('handoff/HANDOFF-P4.json')
h = ho['handoffs'][0]
h['current_state'] = 'APPROVED'
h['approved_by'] = APPROVER
h['approved_on'] = DATE
h['approval_scope'] = {
    'approved': [
        'P4 as a completed, verified phase, including its existing bounded '
        'scope and its outcome of zero production promotions.',
    ],
    'explicitly_not_approved': [
        'Any production promotion of any capability.',
        'Any licence selection or declaration. The licence remains UNRESOLVED.',
        'P5, and the beginning of any P5 work.',
        'Creation of a remote, or pushing anything.',
    ],
}
h['not_completed'] = [
    x for x in h.get('not_completed', [])
    if 'awaits a separate explicit instruction' not in x
] + [
    'Production promotion remains unapproved: P4 approval covers phase '
    'completion only and did not promote any capability.',
    'The repository licence is recorded UNRESOLVED by explicit user decision '
    '(DEC-0022); no licence was chosen or inferred.',
    'P5 remains NOT_STARTED and NOT_APPROVED; no P5 record was created.',
]
h['blockers'] = [
    b for b in h.get('blockers', [])
    if 'user legal decision' not in b.lower()
] + [
    'Gate D blocks all production promotion: the licence is UNRESOLVED by '
    'explicit user decision (DEC-0022) and no licence may be assumed.',
    'Production promotion itself remains unapproved by the user.',
]
h['next_allowed_action'] = (
    'Wait for an explicit user instruction. The next permitted actions are a '
    'licence decision and a separate production promotion approval, each of '
    'which the user must give explicitly. Do NOT begin P5 without instruction.'
)
h['forbidden_next_action'] = (
    'Do NOT start P5, do NOT promote any capability to production, do NOT '
    'select or add a licence, do NOT install any capability, skill, MCP or '
    'package, do NOT create a remote, do NOT push, do NOT modify the legacy '
    'implementation, do NOT purge checkpoint a7767cf, and do NOT perform '
    'Phase 01 remediation.'
)
save('handoff/HANDOFF-P4.json', ho)

print('requirements approved :', sum(
    1 for r in req['requirements'] if r['approval']['state'] == 'APPROVED'))
print('decisions approved    :', sum(
    1 for d in dec['decisions'] if d['approval']['state'] == 'APPROVED'))
print('handoff state         :', h['current_state'])
print('licence recorded as   :',
      [d for d in dec['decisions'] if d['decision_id'] == 'DEC-0022'][0]
      ['unresolved']['state'])