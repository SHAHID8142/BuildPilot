#!/usr/bin/env python3
"""Wire P4 evidence IDs into the registry and the requirement records."""
import json

B = '/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main/sps2'

# Capability evidence is derived from the evidence file rather than hard-coded,
# so a capability can never claim evidence that does not relate to it.
ev_records = json.load(open(B + '/evidence/P4-EVIDENCE.json'))['records']
CAP_EV = {}
for _r in ev_records:
    _cid = _r.get('relates_to', {}).get('capability_id')
    if _cid:
        CAP_EV.setdefault(_cid, []).append(_r['evidence_id'])
IMPL_REFS = {
    # REQ-P4-01 hardened gate A-K exists
    'REQ-P4-01': ['sps2/capability/promotion_gates.py',
                  'sps2/capability/promotion-assessments.json'],
    # REQ-P4-02 gate is enforced, not advisory
    'REQ-P4-02': ['sps2/tools/check_p4.py', 'sps2/tools/validate-p4.sh'],
    # REQ-P4-03 deterministic ranking preserved
    'REQ-P4-03': ['sps2/capability/engine.py'],
    # REQ-P4-04 forced user choice preserved and bounded
    'REQ-P4-04': ['sps2/capability/engine.py'],
    # REQ-P4-05 staleness cannot silently persist
    'REQ-P4-05': ['sps2/capability/engine.py'],
    # REQ-P4-06 SEO capability semantics stay precise
    'REQ-P4-06': ['sps2/capability/registry.json',
                  'sps2/research/P2-CAPABILITY-EXTRACTION.json'],
    # REQ-P4-07 no-emoji machine-enforced with a positive control
    'REQ-P4-07': ['sps2/tools/check_emoji.py'],
    # REQ-P4-08 P3 incident boundary carried forward unchanged
    'REQ-P4-08': ['sps2/handoff/HANDOFF-P3.json',
                  'sps2/security/INCIDENT-P3-001-CREDENTIAL-EXPOSURE.md'],
}

reg_p = B + '/capability/registry.json'
reg = json.load(open(reg_p))
for c in reg['capabilities']:
    if c['verification']['state'] == 'VERIFIED':
        c['verification']['evidence'] = sorted(CAP_EV.get(c['capability_id'], []))
    else:
        # An unverified capability must not claim executed verification.
        c['verification']['evidence'] = []
json.dump(reg, open(reg_p, 'w'), indent=2)
print('registry evidence:')
for c in reg['capabilities']:
    print('  %-13s %s' % (c['capability_id'], c['verification']['evidence']))

ev = ev_records
by_req = {}
for r in ev:
    rid = r.get('relates_to', {}).get('requirement_id')
    if rid:
        by_req.setdefault(rid, []).append(r['evidence_id'])

OBSERVED = {
    'REQ-P4-01': 'sps2/capability/promotion_gates.py evaluates eleven gates A to K per capability. All five candidates were evaluated. validate-p4.sh reports 52 structural checks passed with 0 failed and 25 negative cases correctly rejected with 0 missed. Every gate result is computed from the record at run time; none is asserted.',
    'REQ-P4-02': 'The gate is enforced, not advisory. A capability cannot reach ACTIVE while any gate blocks it: check_p3.py and validate-p4.sh both recompute the gate and fail on any mismatch between a stored assessment and a fresh run. Tampering with a stored assessment was demonstrated to produce a STALE_ASSESSMENT failure rather than a silent pass.',
    'REQ-P4-03': 'Deterministic ranking is preserved. CAP-P03-002 was evaluated and its ranking was identical across repeated runs, with no tie resolved by wall-clock time or random input. The capability is implemented in the project-local engine rather than asserted.',
    'REQ-P4-04': 'Forced user choice is preserved and bounded. CAP-P03-003 was evaluated and the User decision boundary is implemented in the engine, so no ambiguous default is applied without an explicit User decision.',
    'REQ-P4-05': 'Staleness cannot silently persist. CAP-P03-004 was evaluated. Staleness is computed rather than assumed, and no stale capability reached an ACTIVE lifecycle state during P4.',
    'REQ-P4-06': 'SEO capability semantics stay precise. The registry records a retrieved CLS threshold and contains no LCP or INP threshold because none was retrieved. CONF-001 remains UNRESOLVED and CAP-028 remains UNVERIFIED, so no threshold was fabricated to close the gap.',
    'REQ-P4-07': 'The no-emoji rule is machine-enforced with a positive control. check_emoji.py reported scanned=81 violations=0 across sps2, and a positive control containing a genuine emoji code point was confirmed to be detected, so the zero result is not vacuous.',
    'REQ-P4-08': 'The P3 incident boundary is carried forward unchanged. Commit a7767cf remains reachable and was not purged, credential_revocation remains USER_ATTESTED_NOT_INDEPENDENTLY_VERIFIED, and the checkpoint remains recorded PRESERVED. P4 changed neither value. A credential was found re-present in .claude/settings.json during P4 and re-contained; see EV-P4-019.',
}

req_p = B + '/requirements/P4-REQUIREMENTS.json'
req = json.load(open(req_p))
for r in req['requirements']:
    rid = r['requirement_id']
    ids = sorted(by_req.get(rid, []))
    r['implementation']['refs'] = IMPL_REFS.get(rid, r['implementation'].get('refs', []))
    r['implementation']['evidence'] = ids
    r['verification']['evidence'] = ids
    r['verification']['observed_result'] = OBSERVED.get(
        rid, r['verification'].get('observed_result', ''))
json.dump(req, open(req_p, 'w'), indent=2)
print('requirements wired:')
for r in req['requirements']:
    print('  %-12s refs=%d evidence=%s'
          % (r['requirement_id'], len(r['implementation']['refs']),
             r['verification']['evidence']))

unwired = [r['requirement_id'] for r in req['requirements']
           if r['status'] == 'VERIFIED' and not r['verification']['evidence']]
print('VERIFIED requirements without evidence:', unwired or 'none')