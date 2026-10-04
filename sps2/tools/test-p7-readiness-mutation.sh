#!/usr/bin/env bash
# Mutation-test the P7 readiness invariants.
# Each mutation must make validate-p7-readiness.py FAIL. Registry restored.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RECON="$REPO/sps2/decisions/ROADMAP-EXECUTION-RECONCILIATION.json"
CACHE="$REPO/sps2/research/cache.json"
SRC="$REPO/sps2/research/P2-SOURCES.json"
REG="$REPO/sps2/capability/registry.json"
PASSN=0; FAILN=0
mut() {  # mut <label> <target> <python-body>
  local label="$1" target="$2" body="$3" bak out
  bak="$(mktemp)"; cp "$target" "$bak"
  python3 - "$target" "$body" <<'PY'
import json, sys
p, body = sys.argv[1], sys.argv[2]
d = json.load(open(p))
exec(body)
json.dump(d, open(p, "w"), indent=2)
PY
  if [ $? -ne 0 ]; then
    echo "  ERROR   $label (mutation did not apply)"; FAILN=$((FAILN+1))
    cp "$bak" "$target"; rm -f "$bak"; return
  fi
  out="$(python3 "$REPO/sps2/tools/validate-p7-readiness.py" 2>&1)"
  if printf '%s' "$out" | grep -q 'P7 READINESS RECORDED'; then
    echo "  MISSED  $label"; FAILN=$((FAILN+1))
  else
    echo "  CAUGHT  $label  ->  $(printf '%s' "$out" | grep -oE 'RECORD_OVERSTATES_P3|RECONCILIATION_INCOMPLETE|CONF_001_NO_LONGER_UNRESOLVED|LCP_OR_INP_CLAIMED|INVENTED_THRESHOLD|PRODUCTION_COUNT_CHANGED|RUNTIME_STATE_PRESENT|CAP005_NOT_DEFERRED|P7_IMPLEMENTATION_ARTEFACT' | sort -u | tr '\n' ' ')"
    PASSN=$((PASSN+1))
  fi
  cp "$bak" "$target"; rm -f "$bak"
}

echo "MUTATION TESTS — P7 readiness invariants"
mut "M1 roadmap P3 overstated as satisfied" "$RECON" \
  "[m.__setitem__('satisfaction','SATISFIED') for m in d['mapping'] if m['roadmap_phase']=='P3']"
mut "M2 roadmap P3 removed from mapping" "$RECON" \
  "d['mapping'] = [m for m in d['mapping'] if m['roadmap_phase'] != 'P3']"
mut "M3 roadmap P5 removed from mapping" "$RECON" \
  "d['mapping'] = [m for m in d['mapping'] if m['roadmap_phase'] != 'P5']"
mut "M4 mapping loses its executed phase" "$RECON" \
  "[m.__setitem__('executed_as','') for m in d['mapping'] if m['roadmap_phase']=='P4']"
mut "M5 CONF-001 silently closed" "$SRC" \
  "d['conflicts'][0]['resolution'] = 'RESOLVED by inference'"
mut "M6 LCP threshold asserted as observed" "$CACHE" \
  "[e['observed_facts'].__setitem__('LCP_thresholds','2.5') for e in d['entries'] if e['technology_id']=='TECH-WEB-VITALS']"
mut "M7 CAP-05 promoted" "$REG" \
  "[c.__setitem__('lifecycle_state','ACTIVE') for c in d['capabilities'] if c['capability_id']=='CAP-P03-005']"
mut "M8 a fifth production capability promoted" "$REG" \
  "[c['promotion_assessment'].__setitem__('promotion_decision','PROMOTED_TO_PRODUCTION') for c in d['capabilities'] if c['capability_id']=='CAP-P03-005']"

echo ""
if [ "$FAILN" -eq 0 ]; then
  echo "== P7 READINESS MUTATION SUITE: $PASSN caught, $FAILN missed =="
  exit 0
fi
echo "== P7 READINESS MUTATION SUITE: $PASSN caught, $FAILN MISSED =="
exit 1