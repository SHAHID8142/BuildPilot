#!/usr/bin/env bash
# SPS control validator — Phase 03.
#
# Proves that INVALID PROGRESSION IS REJECTED.
#
# SAFETY CONTRACT (deliberate):
#   - makes NO network requests
#   - runs NO installer / uninstaller / updater
#   - writes ONLY inside a self-managed temp dir (removed on exit)
#   - changes NO machine-global state and NO git configuration
#   - never modifies any real repository file
#
# Usage:
#   bash .sps/tools/validate-control.sh             # structural validation
#   bash .sps/tools/validate-control.sh --negative  # negative test suite (CASE A-F)
#
# Exit: 0 = valid | 1 = failure | 2 = tooling unavailable

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT" || exit 2

CONTROL=".sps/control"
EV3=".sps/evidence/PHASE-03-EVIDENCE.json"
REQ3=".sps/requirements/PHASE-03-REQUIREMENTS.json"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'
BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'

PASS=0; FAIL=0
pass() { echo -e "  ${GREEN}PASS${NC}  $*"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}FAIL${NC}  $*"; FAIL=$((FAIL+1)); }
info() { echo -e "  ${BLUE}CASE${NC} $*"; }
sect() { echo -e "\n${BOLD}$*${NC}"; }

command -v git >/dev/null 2>&1 || { echo "git unavailable"; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "python3 unavailable"; exit 2; }

TMP="$(mktemp -d "${TMPDIR:-/tmp}/sps-control-XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

echo -e "${BOLD}SPS Control Validator (Phase 03)${NC}"
echo -e "${DIM}read-only; no network, no installs, no machine-global writes${NC}"
echo -e "${DIM}root: $ROOT${NC}"

# ── helper: evaluate a requirement file; prints OK/ERR lines ─────────────────
check_requirements() {
python3 - "$1" <<'PY'
import json, os, sys, re
sys.path.insert(0, os.path.join(os.getcwd(), 'sps2', 'governance'))
try:
    import attribution as ATTR
except Exception as exc:
    print('ERR\tcanonical attribution policy unavailable: %s' % exc)
    raise SystemExit(1)
try:
    d = json.load(open(sys.argv[1]))
except Exception as e:
    print("ERR\trequirement file is not valid JSON: %s" % e); sys.exit(0)
reqs = d.get('requirements', [])
if not reqs:
    print("ERR\tno requirements found"); sys.exit(0)
VAGUE = re.compile(r'\b(good|nice|fast|robust|proper|appropriate|suitable|reasonable|as needed|etc\.?)\b', re.I)
VALID_IMPL = {'DECLARED', 'IMPLEMENTED'}
VALID_VER  = {'UNVERIFIED', 'VERIFIED'}
VALID_APP  = {'NOT_REQUIRED', 'PENDING_USER_APPROVAL', 'APPROVED', 'REJECTED'}
for r in reqs:
    rid = r.get('requirement_id', '<no id>')
    if not re.fullmatch(r'REQ-P\d\d-\d\d', rid):
        print("ERR\t%s: requirement_id does not match REQ-PNN-NN" % rid); continue
    ac = r.get('acceptance_criteria') or []
    if not ac:
        print("ERR\t%s: acceptance_criteria is empty (MISSING_REQUIREMENT)" % rid); continue
    vague = [c for c in ac if VAGUE.search(c or '')]
    if vague:
        print("ERR\t%s: acceptance criteria are not observable: %r" % (rid, vague[0][:50])); continue
    if r.get('implementation_status') not in VALID_IMPL:
        print("ERR\t%s: invalid implementation_status %r" % (rid, r.get('implementation_status'))); continue
    if r.get('implementation_status') == 'IMPLEMENTED' and not (r.get('implementation_refs') or []):
        print("ERR\t%s: IMPLEMENTED but no implementation_refs (UNVERIFIED_IMPLEMENTATION)" % rid); continue
    if r.get('verification_status') not in VALID_VER:
        print("ERR\t%s: invalid verification_status %r" % (rid, r.get('verification_status'))); continue
    if r.get('verification_status') == 'VERIFIED' and not (r.get('verification_refs') or []):
        print("ERR\t%s: VERIFIED but no verification_refs" % rid); continue
    if r.get('approval_status') not in VALID_APP:
        print("ERR\t%s: invalid approval_status %r" % (rid, r.get('approval_status'))); continue
    # A blocking condition must not coexist with a progression claim.
    if (r.get('blockers') or []) and r.get('approval_status') == 'APPROVED':
        print("ERR\t%s: blocker(s) %s present yet marked APPROVED - progression blocked" % (rid, r.get('blockers'))); continue
    if r.get('approval_status') == 'APPROVED':
        who = (r.get('approval_decided_by') or '').strip()
        if not who:
            print("ERR\t%s: APPROVED but approval_decided_by is empty" % rid); continue
        if ATTR.AGENTISH.search(who):
            print("ERR\t%s: APPROVED attributed to agent/model, not a user" % rid); continue
    if (r.get('verification_status') == 'VERIFIED'
            and r.get('approval_status') in ('NOT_REQUIRED', 'PENDING_USER_APPROVAL')
            and (r.get('priority') or '').upper() == 'CRITICAL'):
        print("ERR\t%s: CRITICAL verified but approval not received (PENDING_APPROVAL)" % rid); continue
    print("OK\t%s satisfies the requirement contract" % rid)
PY
}
# ── main ──────────────────────────────────────────────────────────────────────
NEG_ONLY=false
for a in "$@"; do [ "$a" = "--negative" ] && NEG_ONLY=true; done

# ══ STRUCTURAL VALIDATION ═══════════════════════════════════════════════════
if [ "$NEG_ONLY" != true ]; then

sect "1. Control model files present"
for f in "$CONTROL/CONTROL-MODEL.md" "$CONTROL/ENFORCEMENT.md" \
         "$CONTROL/ENFORCEMENT-VS-INSTRUCTION.md" "$EV3" "$REQ3"; do
  [ -f "$f" ] && pass "exists $f" || fail "missing $f"
done

sect "2. Control model documents the required concepts"
require() { grep -rqE "$2" "$CONTROL/$1" 2>/dev/null && pass "$1 mentions $3" || fail "$1 does NOT mention $3"; }
require CONTROL-MODEL.md 'DISCOVERY'            'DISCOVERY lifecycle stage'
require CONTROL-MODEL.md 'DELIVERED'            'DELIVERED lifecycle stage'
require CONTROL-MODEL.md '`DECLARED`'           'DECLARED truth'
require CONTROL-MODEL.md '`IMPLEMENTED`'        'IMPLEMENTED truth'
require CONTROL-MODEL.md '`VERIFIED`'           'VERIFIED truth'
require CONTROL-MODEL.md '`USER_APPROVED`'      'USER_APPROVED truth'
require CONTROL-MODEL.md '`AUTOMATED`'          'AUTOMATED verifier class'
require CONTROL-MODEL.md '`DESTRUCTIVE`'        'DESTRUCTIVE action class'
require CONTROL-MODEL.md '`CRITICAL`'           'CRITICAL risk level'
require CONTROL-MODEL.md 'rollback_verified'    'rollback contract fields'
require ENFORCEMENT.md 'APPROVAL_GATE'         'enforcement level 3'
require ENFORCEMENT.md 'HARD_GATE'             'enforcement level 4'
require ENFORCEMENT.md 'MISSING_USER_DECISION' 'stop condition codes'
require ENFORCEMENT.md 'MATERIAL_DECISION'     'no-assumption rule'
require ENFORCEMENT.md 'append-only'           'immutable evidence principle'
require ENFORCEMENT-VS-INSTRUCTION.md 'ENFORCED' 'enforced vs instructed distinction'

sect "3. Schema extends with Phase 03 contracts"
for s in 'Requirement Contract' 'Verification Contract' 'Agent Action Contract' \
         'Rollback Contract' 'Handoff Extension'; do
  grep -q "$s" .sps/SCHEMA.md && pass "SCHEMA.md defines $s" || fail "SCHEMA.md missing $s"
done
grep -q 'next_allowed_action' .sps/SCHEMA.md && pass "handoff defines next_allowed_action" || fail "missing next_allowed_action"
grep -q 'forbidden_next_action' .sps/SCHEMA.md && pass "handoff defines forbidden_next_action" || fail "missing forbidden_next_action"

sect "4. Phase 03 requirement records"
OUT="$(check_requirements "$REQ3")"
if [ -z "$OUT" ]; then
  fail "requirement checker produced no output"
else
  while IFS=$'\t' read -r kind msg; do
    [ "$kind" = "OK" ] && pass "$msg" || fail "$msg"
  done <<< "$OUT"
fi

sect "5. Phase 03 evidence records (append-only discipline)"
if [ -f "$EV3" ]; then
  python3 - "$EV3" <<'PY'
import json, sys, re
d = json.load(open(sys.argv[1]))
recs = d.get('records', [])
ids = [r.get('id') for r in recs]
dup = sorted({i for i in ids if ids.count(i) > 1})
print(("OK\tall %d evidence IDs unique" % len(ids)) if not dup else ("ERR\tduplicate evidence IDs: %s" % dup))
bad = [r.get('id') for r in recs if r.get('result') not in {'PASS','FAIL','SKIP','BLOCKED','PENDING'}]
print("OK\tall result values within enum" if not bad else "ERR\tinvalid result enum: %s" % bad)
empty = [r.get('id') for r in recs if r.get('result') == 'PASS' and not r.get('actual')]
print("OK\tevery PASS record carries verbatim output" if not empty else "ERR\tPASS without actual output: %s" % empty)
badid = [i for i in ids if not re.fullmatch(r'EV-P\d\d-\d\d\d', str(i))]
print("OK\tall evidence IDs match EV-PNN-NNN" if not badid else "ERR\tmalformed evidence IDs: %s" % badid)
PY
else
  fail "$EV3 not found"
fi

sect "6. Scope discipline (Phase 03 must not fix Phase 01 findings)"
for probe in skills/sps-cms/templates/auth/auth-helper.ts skills/sps/SKILL.md install.sh; do
  if [ -n "$(git diff --name-only HEAD -- "$probe" 2>/dev/null)" ]; then
    fail "MODIFIED out-of-scope file: $probe"
  else
    pass "untouched (out of scope): $probe"
  fi
done
fi  # end structural validation

# ══ NEGATIVE TEST SUITE ═════════════════════════════════════════════════════
# Each case builds a deliberately invalid artefact inside a temp dir and asserts
# the validator REJECTS it. A case that is NOT rejected is itself a validator

sect "NEGATIVE TESTS (CASE A-F) - invalid progression must be rejected"

NEG_PASS=0; NEG_FAIL=0
run_case() {
  local label="$1" expect="$2" file="$3" out
  out="$(check_requirements "$file" 2>&1)"
  if printf '%s' "$out" | grep -q '^ERR' && printf '%s' "$out" | grep -qiE "$expect"; then
    info "REJECTED as required -> $label"
    NEG_PASS=$((NEG_PASS+1)); pass "$label -> rejected"
  else
    info "NOT REJECTED (validator defect!) -> $label"
    NEG_FAIL=$((NEG_FAIL+1)); fail "$label -> NOT rejected (out: ${out:-none})"
  fi
}

mk() { python3 -c "import json,sys;d=json.load(sys.stdin);exec(sys.argv[1]);print(json.dumps({'requirements':[d]}))" "$1"; }

base_req() {
cat <<'JSON'
{"requirement_id":"REQ-P03-90","title":"Negative test fixture",
 "description":"Fixture used only by the negative suite.","source":"test",
 "priority":"MEDIUM","scope":"IN_SCOPE",
 "acceptance_criteria":["Executing the checker returns ERR for this fixture"],
 "dependencies":[],"implementation_status":"DECLARED","implementation_refs":[],
 "verification_status":"UNVERIFIED","verification_refs":[],
 "approval_status":"NOT_REQUIRED","approval_decided_by":"","blockers":[],
 "evidence":[],"related_tasks":[],"related_decisions":[]}
JSON
}

base_req | mk "d['acceptance_criteria']=[]" > "$TMP/caseA.json"
run_case "CASE A  acceptance criteria missing" "acceptance_criteria is empty" "$TMP/caseA.json"

base_req | mk "d['acceptance_criteria']=['Build a good homepage']" > "$TMP/caseA2.json"
run_case "CASE A2 acceptance criteria not observable" "not observable" "$TMP/caseA2.json"

base_req | mk "d['implementation_status']='IMPLEMENTED';d['implementation_refs']=['f.ts:1'];d['verification_status']='VERIFIED';d['verification_refs']=[]" > "$TMP/caseB.json"
run_case "CASE B  VERIFIED but no verification_refs" "VERIFIED but no verification_refs" "$TMP/caseB.json"

base_req | mk "d['priority']='CRITICAL';d['implementation_status']='IMPLEMENTED';d['implementation_refs']=['f.ts:1'];d['verification_status']='VERIFIED';d['verification_refs']=['VER-P03-900'];d['approval_status']='PENDING_USER_APPROVAL'" > "$TMP/caseC.json"
run_case "CASE C  CRITICAL verified, approval missing" "PENDING_APPROVAL" "$TMP/caseC.json"

base_req | mk "d['blockers']=['FAILED_TEST'];d['approval_status']='APPROVED';d['approval_decided_by']='User'" > "$TMP/caseD.json"
run_case "CASE D  blocker present yet APPROVED" "blocker" "$TMP/caseD.json"

base_req | mk "d['approval_status']='APPROVED';d['approval_decided_by']='agent'" > "$TMP/caseE.json"
run_case "CASE E  approval attributed to an agent" "attributed to agent" "$TMP/caseE.json"

base_req | mk "d['approval_status']='APPROVED';d['approval_decided_by']=''" > "$TMP/caseE2.json"
run_case "CASE E2 approval with no decider" "approval_decided_by is empty" "$TMP/caseE2.json"

cat > "$TMP/caseF.json" <<'JSON'
{"schema":"sps.evidence/v1","records":[
 {"id":"EV-P03-900","result":"PASS","actual":""},
 {"id":"EV-P03-900","result":"PASS","actual":"ok"},
 {"id":"EV-P03-901","result":"MAYBE","actual":"x"}]}
JSON
FOUT="$(python3 - "$TMP/caseF.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1])); recs = d.get('records', [])
ids = [r.get('id') for r in recs]
dup = sorted({i for i in ids if ids.count(i) > 1})
errs = []
if dup: errs.append("duplicate evidence IDs: %s" % dup)
bad = [r.get('id') for r in recs if r.get('result') not in {'PASS','FAIL','SKIP','BLOCKED','PENDING'}]
if bad: errs.append("invalid result enum: %s" % bad)
empty = [r.get('id') for r in recs if r.get('result') == 'PASS' and not r.get('actual')]
if empty: errs.append("PASS without actual output: %s" % empty)
print("ERR\t" + "; ".join(errs) if errs else "OK\tclean")
PY
)"
if printf '%s' "$FOUT" | grep -q '^ERR' \
   && printf '%s' "$FOUT" | grep -qE 'duplicate evidence IDs' \
   && printf '%s' "$FOUT" | grep -qE 'invalid result enum' \
   && printf '%s' "$FOUT" | grep -qE 'PASS without actual output'; then
  info "DETECTED as required -> CASE F tampering (dup id + bad enum + erased output)"
  NEG_PASS=$((NEG_PASS+1)); pass "CASE F  tampered evidence -> detected"
else
  info "NOT DETECTED (validator defect!) -> CASE F"
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE F  tampered evidence -> NOT detected"
fi

echo ""
if [ "$NEG_FAIL" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}== NEGATIVE SUITE: $NEG_PASS cases correctly rejected, 0 missed ==${NC}"
else
  echo -e "${RED}${BOLD}== NEGATIVE SUITE: $NEG_PASS rejected, $NEG_FAIL MISSED ==${NC}"
fi

echo ""
if [ "$FAIL" -eq 0 ] && [ "$NEG_FAIL" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}== CONTROL VALID: $PASS checks passed, 0 failed, $NEG_PASS negative cases enforced ==${NC}"
  exit 0
fi
echo -e "${RED}${BOLD}== CONTROL INVALID: $PASS passed, $FAIL failed, $NEG_FAIL negative cases missed ==${NC}"
exit 1
