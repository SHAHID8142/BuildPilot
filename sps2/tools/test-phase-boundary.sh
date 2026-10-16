#!/usr/bin/env bash
# Mutation-test the phase-aware P6 boundary in validate-p5.py section 14.
# Each mutation must make validate-p5.sh-equivalent (validate-p5.py) FAIL.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEC="$REPO/sps2/decisions/P6-DECISIONS.json"
REG="$REPO/sps2/capability/registry.json"
BAK="$(mktemp)"
cp "$DEC" "$BAK"
PASSN=0; FAILN=0

mutate() {  # mutate <label> <target> <python-body>
  local label="$1" target="$2" body="$3" out
  cp "$BAK" "$DEC"
  python3 - "$target" "$body" <<'PY'
import json, sys
p, body = sys.argv[1], sys.argv[2]
d = json.load(open(p))
exec(body)
json.dump(d, open(p, "w"), indent=2)
PY
  if [ $? -ne 0 ]; then
    echo "  ERROR   $label (mutation did not apply)"; FAILN=$((FAILN+1)); return
  fi
  out="$(python3 "$REPO/sps2/tools/validate-p5.py" 2>&1)"
  if printf '%s' "$out" | grep -q 'P5 IMPLEMENTATION VALID'; then
    echo "  MISSED  $label"; FAILN=$((FAILN+1))
  else
    echo "  CAUGHT  $label  ->  $(printf '%s' "$out" | grep -oE \
      'P6_DECISION_[A-Z_]*|RUNTIME_STATE_PRESENT|PRODUCTION_COUNT_CHANGED|CAP005_NOT_DEFERRED|P7_ARTIFACT_CREATED' \
      | sort -u | tr '\n' ' ')"
    PASSN=$((PASSN+1))
  fi
  cp "$BAK" "$DEC"
}

echo "MUTATION TESTS — phase-aware P6 boundary"
mutate "M1 D-P6-1 decision removed" "$DEC" \
  "d['decisions'] = [x for x in d['decisions'] if x['decision_id'] != 'D-P6-1']"
mutate "M2 D-P6-2 decision removed" "$DEC" \
  "d['decisions'] = [x for x in d['decisions'] if x['decision_id'] != 'D-P6-2']"
mutate "M3 D-P6-1 attributed to an agent" "$DEC" \
  "[x['approval'].__setitem__('decided_by', 'Cline') for x in d['decisions'] if x['decision_id'] == 'D-P6-1']"
mutate "M4 D-P6-2 approval state downgraded" "$DEC" \
  "[x['approval'].__setitem__('state', 'PENDING_USER_APPROVAL') for x in d['decisions'] if x['decision_id'] == 'D-P6-2']"
mutate "M5 D-P6-1 undated" "$DEC" \
  "[x['approval'].pop('decided_at', None) for x in d['decisions'] if x['decision_id'] == 'D-P6-1']"

cp "$BAK" "$DEC"
REQB="$REPO/sps2/requirements/P6-REQUIREMENTS.json"
RB="$(mktemp)"; cp "$REQB" "$RB"
mutate_req() {  # mutate_req <label> <python-body>
  local label="$1" body="$2" out
  cp "$RB" "$REQB"
  python3 - "$REQB" "$body" <<'PY'
import json, sys
p, body = sys.argv[1], sys.argv[2]
d = json.load(open(p))
exec(body)
json.dump(d, open(p, "w"), indent=2)
PY
  if [ $? -ne 0 ]; then
    echo "  ERROR   $label (mutation did not apply)"; FAILN=$((FAILN+1)); return
  fi
  out="$(python3 "$REPO/sps2/tools/validate-p6.py" 2>&1)"
  if printf '%s' "$out" | grep -q 'P6 RESEARCH VALID'; then
    echo "  MISSED  $label"; FAILN=$((FAILN+1))
  else
    echo "  CAUGHT  $label  ->  $(printf '%s' "$out" | grep -oE 'P6_APPROVAL_[A-Z_]*|P6_REQUIREMENT_APPROVAL_NOT_USER|P6_PHASE_APPROVAL_MISSING' | sort -u | tr '\n' ' ')"
    PASSN=$((PASSN+1))
  fi
  cp "$RB" "$REQB"
}
mutate_req "M6 P6 approval attributed to an agent" \
  "d['phase_completion_approval']['decided_by'] = 'Cline'"
mutate_req "M7 P6 approval undated" \
  "d['phase_completion_approval'].pop('decided_on', None)"
mutate_req "M8 P6 approval scope broadened" \
  "d['phase_completion_approval']['scope'] = 'FULL_AUTHORITY'"
mutate_req "M9 approval drops the P7 exclusion" \
  "d['phase_completion_approval']['explicitly_not_approved'] = [x for x in d['phase_completion_approval']['explicitly_not_approved'] if 'P7' not in x]"
mutate_req "M10 a requirement approval forged to an agent" \
  "d['requirements'][0]['approval']['decided_by'] = 'Agent'"
mutate_req "M11 preserved state claims CONF-001 resolved" \
  "d['phase_completion_approval']['preserved_state']['CONF-001'] = 'RESOLVED'"

cp "$RB" "$REQB"
rm -f "$RB" "$BAK"
echo ""
if [ "$FAILN" -eq 0 ]; then
  echo "== PHASE BOUNDARY MUTATION SUITE: $PASSN caught, $FAILN missed =="
  exit 0
fi
echo "== PHASE BOUNDARY MUTATION SUITE: $PASSN caught, $FAILN MISSED =="
exit 1