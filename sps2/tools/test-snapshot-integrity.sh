#!/usr/bin/env bash
# Mutation-test the historical-snapshot vs current-evaluation invariants.
# Each mutation must make validate-p4.sh FAIL. Restores the registry after each.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REG="$REPO/sps2/capability/registry.json"
BAK="$(mktemp)"
cp "$REG" "$BAK"
PASSN=0; FAILN=0

mutate() {  # mutate <label> <cid-prefix-filter> <python-body>
  local label="$1" filt="$2" expr="$3" out
  # Restore FIRST so every mutation starts from a known-good registry.
  cp "$BAK" "$REG"
  python3 - "$REG" "$filt" "$expr" <<'PY'
import json, sys
p, filt, body = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(p))
for c in d["capabilities"]:
    if c["capability_id"].startswith(filt):
        exec(body)
json.dump(d, open(p, "w"), indent=2)
PY
  if [ $? -ne 0 ]; then
    echo "  ERROR   $label (mutation did not apply)"
    FAILN=$((FAILN+1))
    cp "$BAK" "$REG"
    return
  fi
  out="$(bash "$REPO/sps2/tools/validate-p4.sh" 2>&1)"
  if printf '%s' "$out" | grep -q 'P4 PROMOTION VALID'; then
    echo "  MISSED  $label"
    FAILN=$((FAILN+1))
  else
    echo "  CAUGHT  $label  ->  $(printf '%s' "$out" | grep -oE 'GATE_SNAPSHOT[A-Z_]*|SNAPSHOT_[A-Z_]*|CURRENT_GATES_[A-Z_]*' | sort -u | tr '\n' ' ')"
    PASSN=$((PASSN+1))
  fi
  cp "$BAK" "$REG"
}

PROMOTED="CAP-P03-001"
echo "MUTATION TESTS — snapshot vs current invariants"
mutate "M1 declaration removed" "$PROMOTED" \
  "c['promotion_record'].pop('gate_snapshot_declaration', None)"
mutate "M2 snapshot relabelled as current" "$PROMOTED" \
  "c['promotion_record']['gate_snapshot_declaration']['gate_results_at_promotion_is']='CURRENT_EVALUATION'"
mutate "M3 difference undeclared" "$PROMOTED" \
  "c['promotion_record']['gate_snapshot_declaration']['differences_from_current']=[]"
mutate "M4 difference flag lies (says none expected)" "$PROMOTED" \
  "c['promotion_record']['gate_snapshot_declaration']['difference_is_expected_and_declared']=False"
mutate "M5 historical snapshot silently smoothed to H=true" "$PROMOTED" \
  "c['promotion_record']['gate_results_at_promotion']['H']=True"
mutate "M6 difference reason removed" "$PROMOTED" \
  "c['promotion_record']['gate_snapshot_declaration']['differences_from_current'][0]['reason']=''"
mutate "M7 preserved_unmodified flag falsified" "$PROMOTED" \
  "c['promotion_record']['gate_snapshot_declaration']['preserved_unmodified']=False"
mutate "M8 current evaluation marker removed" "$PROMOTED" \
  "c['promotion_record']['gate_snapshot_declaration'].pop('promotion_assessment_gates_is', None)"
# The deferred candidate's current gates must also equal a fresh recomputation.
mutate "M9 CAP005 current gates optimistically true" "CAP-P03-005" \
  "c['promotion_assessment']['gates']['K']['pass']=True"

cp "$BAK" "$REG"
rm -f "$BAK"
echo ""
if [ "$FAILN" -eq 0 ]; then
  echo "== SNAPSHOT MUTATION SUITE: $PASSN caught, $FAILN missed =="
  exit 0
fi
echo "== SNAPSHOT MUTATION SUITE: $PASSN caught, $FAILN MISSED =="
exit 1