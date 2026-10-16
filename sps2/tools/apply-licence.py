#!/usr/bin/env python3
"""Record the user-selected MIT licence on every registry capability.

Gate D requires three things: a classification in LICENCE_KNOWN, a
licence_evidence string, and a licence file tracked by git. The user selected
MIT on 2026-10-04 after the provenance prerequisite was satisfied by user
attestation. This records that decision. It does not promote anything.
"""
import json

B = '/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main/sps2'
DATE = '2026-10-04'

CLASSIFICATION = 'KNOWN_PERMISSIVE'   # MIT
CONCRETE = 'MIT'
EVIDENCE = (
    'The user selected the MIT licence for the SPS 2.0 repository on '
    + DATE + '. A LICENSE file exists at the repository root and is tracked. '
    'The applicable licence is MIT, classified KNOWN_PERMISSIVE. The licence '
    'prerequisite was satisfied by USER_ATTESTATION of skills/sps-cms '
    'provenance, which was NOT independently verified. No third-party code '
    'was identified and none was relicensed. This licence statement was not '
    'independently verified as legally valid.'
)

p = B + '/capability/registry.json'
reg = json.load(open(p))
for c in reg['capabilities']:
    c['licence'] = CLASSIFICATION
    c['licence_name'] = CONCRETE
    c['licence_evidence'] = EVIDENCE
    c['licence_decided_by'] = 'User'
    c['licence_decided_on'] = DATE
json.dump(reg, open(p, 'w'), indent=2)
print('licence recorded on %d capabilities: %s (%s)'
      % (len(reg['capabilities']), CONCRETE, CLASSIFICATION))
for c in reg['capabilities']:
    print('  %-13s licence=%s name=%s'
          % (c['capability_id'], c['licence'], c['licence_name']))