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
    echo "  CAUGHT  $label  ->  $(printf '%s' "$out" | grep -oE \
      'RECORD_OVERSTATES_P3|RECONCILIATION_INCOMPLETE|MAPPING_WITHOUT_EXECUTED_PHASE|INVALID_SATISFACTION|AMBIGUITY_RESOLUTION_DRIFT|CONF_001_NO_LONGER_UNRESOLVED|LCP_OR_INP_CLAIMED|INVENTED_THRESHOLD|PRODUCTION_COUNT_CHANGED|RUNTIME_STATE_PRESENT|CAP005_NOT_DEFERRED|P7_IMPLEMENTATION_ARTEFACT|P7_DECISION_[A-Z_]*|P7_B_WAIVED_OR_UNSPECIFIED|P7_C_[A-Z_]*|P7_D_THREAT_MODEL_NOT_REQUIRED' \
      | sort -u | tr '\n' ' ')"
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

# MUTATIONS FOR THE P7 READINESS DECISIONS
P7D="$REPO/sps2/decisions/P7-READINESS-DECISIONS.json"
mut "M9 P7 decision attributed to an agent" "$P7D" \
  "[d['approval'].__setitem__('decided_by','Cline') for d in d['decisions'] if d['decision_id']=='D-P7-B']"
mut "M10 P7 decision undated" "$P7D" \
  "[d['approval'].pop('decided_on',None) for d in d['decisions'] if d['decision_id']=='D-P7-A']"
mut "M11 D-P7-B downgraded into a waiver" "$P7D" \
  "[d.__setitem__('decision','Roadmap P3 is waived.') or d.pop('required_before_p7',None) for d in d['decisions'] if d['decision_id']=='D-P7-B']"
mut "M12 D-P7-C legacy exclusion removed" "$P7D" \
  "[d.__setitem__('explicitly_narrowed',['in scope: everything']) for d in d['decisions'] if d['decision_id']=='D-P7-C']"
mut "M13 D-P7-D threat model no longer required" "$P7D" \
  "[d.pop('required_before_p7',None) for d in d['decisions'] if d['decision_id']=='D-P7-D']"
mut "M14 a P7 decision left unbounded" "$P7D" \
  "[d.__setitem__('bounded_scope','') for d in d['decisions'] if d['decision_id']=='D-P7-C']"
mut "M15 D-P7-D removed entirely" "$P7D" \
  "d['decisions'] = [x for x in d['decisions'] if x['decision_id'] != 'D-P7-D']"
# M16/M17 fail only because the checks read structured fields: under a
# whole-record text search the legacy exclusion would still be found inside the
# quoted User wording, and any non-empty prerequisite list would look adequate.
mut "M16 D-P7-C narrowed scope emptied, quoted wording left intact" "$P7D" \
  "[d.__setitem__('explicitly_narrowed',[]) for d in d['decisions'] if d['decision_id']=='D-P7-C']"
mut "M17 D-P7-D prerequisites lose isolation and rollback" "$P7D" \
  "[d.__setitem__('required_before_p7',['a threat model']) for d in d['decisions'] if d['decision_id']=='D-P7-D']"
# M18/M19 protect the resolution record itself, so the audit's claim that all
# four ambiguities are RESOLVED is machine-backed rather than trusted.
mut "M18 AMB-PHASE-3 marked unresolved again" "$RECON" \
  "[a.__setitem__('resolved',False) for a in d['unresolved_ambiguity'] if a['id']=='AMB-PHASE-3']"
mut "M19 AMB-PHASE-2 re-pointed at the wrong decision" "$RECON" \
  "[a.__setitem__('resolved_by','D-P7-C') for a in d['unresolved_ambiguity'] if a['id']=='AMB-PHASE-2']"

# The same boundary, seen through every PHASE validator rather than the
# readiness checker. Each guard must reject a forged or gutted decision record
# AND still admit the legitimate one, which is the entire point of
# distinguishing a decision record from a deliverable. Without the control
# legs, a guard that had silently reverted to a blanket P7 ban would look
# equally healthy.
echo ""
echo "MUTATION TESTS — the same boundary through each phase validator"
V_N=0; V_M=0
run_val() {  # run_val <p4|p5|p6>
  case "$1" in
    p4) bash "$REPO/sps2/tools/validate-p4.sh" 2>&1 ;;
    p5) python3 "$REPO/sps2/tools/validate-p5.py" 2>&1 ;;
    p6) python3 "$REPO/sps2/tools/validate-p6.py" 2>&1 ;;
  esac
}
val_mark() {  # val_mark <p4|p5|p6>
  case "$1" in
    p4) echo 'P4 PROMOTION VALID' ;;
    p5) echo 'P5 IMPLEMENTATION VALID' ;;
    p6) echo 'P6 RESEARCH VALID' ;;
  esac
}
verdict() {  # verdict <label> <p4|p5|p6> <caught|admitted>
  local label="$1" v="$2" want="$3" out
  out="$(run_val "$v")"
  if printf '%s' "$out" | grep -q "$(val_mark "$v")"; then
    if [ "$want" = "admitted" ]; then
      echo "  CONTROL ($v) admits the legitimate record: $label"
    else
      echo "  MISSED  ($v) $label"; V_M=$((V_M+1))
    fi
  elif [ "$want" = "admitted" ]; then
    echo "  FAIL    ($v) blanket-ban regression, rejected: $label"
    V_M=$((V_M+1))
  else
    echo "  CAUGHT  ($v) $label  ->  $(printf '%s' "$out" \
      | grep -oE 'P7_[A-Z_]+' | sort -u | tr '\n' ' ')"
    V_N=$((V_N+1))
  fi
}
v_mut() {  # v_mut <label> <validator> <python-body applied to the record>
  local label="$1" v="$2" body="$3" bak
  bak="$(mktemp)"; cp "$P7D" "$bak"
  python3 - "$P7D" "$body" <<'PY'
import json, sys
p, body = sys.argv[1], sys.argv[2]
d = json.load(open(p))
exec(body)
json.dump(d, open(p, "w"), indent=2)
PY
  verdict "$label" "$v" caught
  cp "$bak" "$P7D"; rm -f "$bak"
}
AGENT_ATTRIB="[d['approval'].__setitem__('decided_by','Cline') for d in d['decisions'] if d['decision_id']=='D-P7-A']"
DELETE_ONE="d['decisions'] = [x for x in d['decisions'] if x['decision_id'] != 'D-P7-C']"
v_mut "V1 D-P7-A attributed to an agent" p4 "$AGENT_ATTRIB"
v_mut "V2 D-P7-B loses its roadmap P3 prerequisites" p4 \
  "[d.pop('required_before_p7',None) for d in d['decisions'] if d['decision_id']=='D-P7-B']"
v_mut "V3 D-P7-D resolves the wrong ambiguity" p4 \
  "[d.__setitem__('resolves_ambiguity','AMB-PHASE-1') for d in d['decisions'] if d['decision_id']=='D-P7-D']"
v_mut "V4 a readiness decision deleted" p4 "$DELETE_ONE"
v_mut "V5 D-P7-A attributed to an agent" p5 "$AGENT_ATTRIB"
v_mut "V6 a readiness decision deleted" p5 "$DELETE_ONE"
v_mut "V7 D-P7-A attributed to an agent" p6 "$AGENT_ATTRIB"
v_mut "V8 a readiness decision deleted" p6 "$DELETE_ONE"

# A deliverable must still be forbidden outright, even with a valid record.
PLANT="$REPO/sps2/tasks/P7-TASKS.md"
if [ -e "$PLANT" ]; then
  echo "  ERROR   planted P7 deliverable: path already exists"; V_M=$((V_M+1))
else
  : > "$PLANT"
  verdict "planted P7 deliverable" p4 caught
  verdict "planted P7 deliverable" p5 caught
  verdict "planted P7 deliverable" p6 caught
  rm -f "$PLANT"
fi

# CONTROLS: the intact record must be ADMITTED by every guard.
verdict "intact record, no false alarm" p4 admitted
verdict "intact record, no false alarm" p5 admitted
verdict "intact record, no false alarm" p6 admitted

FAILN=$((FAILN+V_M))
echo ""
if [ "$FAILN" -eq 0 ]; then
  echo "== P7 READINESS MUTATION SUITE: $PASSN caught, 0 missed (readiness) + $V_N caught, 0 missed (phase validators) =="
  exit 0
fi
echo "== P7 READINESS MUTATION SUITE: $PASSN caught, $FAILN MISSED =="
exit 1