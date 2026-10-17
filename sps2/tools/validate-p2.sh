#!/usr/bin/env bash
# SPS 2.0 P2 research validator.
# Validates research records and the standing constraints that must survive
# research: no-emoji, legacy isolation, project-locality, registry protection.
# SAFETY: no network, no installs, no machine-global writes.
# Usage: bash sps2/tools/validate-p2.sh [--negative]
# Exit:  0 valid | 1 failure | 2 tooling unavailable

set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPS2="$(cd "$HERE/.." && pwd)"
REPO="$(cd "$SPS2/.." && pwd)"
CHECK="$HERE/check_p2.py"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'
BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'
PASS=0; FAIL=0; NEG_PASS=0; NEG_FAIL=0
pass() { echo -e "  ${GREEN}PASS${NC}  $*"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}FAIL${NC}  $*"; FAIL=$((FAIL+1)); }
info() { echo -e "  ${BLUE}CASE${NC} $*"; }
warn() { echo -e "  ${YELLOW}WARN${NC}  $*"; }
sect() { echo -e "\n${BOLD}$*${NC}"; }

command -v python3 >/dev/null 2>&1 || { echo "python3 unavailable"; exit 2; }
TMP="$(mktemp -d "${TMPDIR:-/tmp}/sps2p2-XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

NEG_ONLY=false
for a in "$@"; do [ "$a" = "--negative" ] && NEG_ONLY=true; done

echo -e "${BOLD}SPS 2.0 P2 Research Validator${NC}"
echo -e "${DIM}research-record validation; no network, no installs, no global writes${NC}"

run_check() { python3 "$CHECK" "$1" "$2" 2>/dev/null; }

# Fail-CLOSED clean assertion. Empty stdout is NOT a verdict: a checker that
# crashed, is missing, or exited non-zero silently also prints nothing.
# rc is captured on the SAME line as the command substitution so it is assigned
# in THIS shell; routing it through a helper invoked via $( ) would run that
# helper in a subshell and silently discard the status.
assert_clean() {
  local out rc
  out="$(python3 "$CHECK" "$1" "$2" 2>&1)"; rc=$?
  if [ "$rc" -ne 0 ]; then
    fail "$3: checker exited $rc - control could not run"
  elif [ -z "$out" ]; then
    pass "$3"
  else
    while IFS= read -r l; do [ -n "$l" ] && fail "$3: $l"; done <<< "$out"
  fi
}

if [ "$NEG_ONLY" != true ]; then

sect "1. Required P2 outputs"
for f in research/P2-ECOSYSTEM-MAP.md research/P2-COMPARATIVE-AUDIT.md \
         research/P2-CAPABILITY-MATRIX.json research/P2-SOURCES.json \
         research/P2-CAPABILITY-EXTRACTION.json \
         research/P2-INTEROPERABILITY-MATRIX.json \
         research/P2-CMS-SEO-AUDIT.md research/P2-SECURITY-AUDIT.md \
         research/P2-MEMORY-CONTEXT-AUDIT.md \
         research/P2-VERIFICATION-AUDIT.md \
         requirements/P2-REQUIREMENTS.json evidence/P2-EVIDENCE.json \
         tasks/P2-TASKS.md decisions/P2-DECISIONS.json \
         handoff/HANDOFF-P2.json; do
  [ -f "$SPS2/$f" ] && pass "present $f" || fail "missing $f"
done
[ -f "$REPO/AUDIT-PHASE-06-P2-CAPABILITY-INTELLIGENCE.md" ] \
  && pass "present AUDIT-PHASE-06 report" || fail "missing AUDIT-PHASE-06 report"

sect "2. Research records validate"
assert_clean sources     "$SPS2/research/P2-SOURCES.json"                "sources"
assert_clean capability  "$SPS2/research/P2-CAPABILITY-EXTRACTION.json"  "capability extraction"
assert_clean interop     "$SPS2/research/P2-INTEROPERABILITY-MATRIX.json" "interop matrix"
assert_clean requirements "$SPS2/requirements/P2-REQUIREMENTS.json"       "P2 requirements"
assert_clean evidence    "$SPS2/evidence/P2-EVIDENCE.json"                "P2 evidence"
assert_clean decision    "$SPS2/decisions/P2-DECISIONS.json"             "P2 decisions"
assert_clean handoff     "$SPS2/handoff/HANDOFF-P2.json"                  "P2 handoff"
sect "3. Capability matrix links to the extraction"
python3 - "$SPS2" > "$TMP/caps_ok" 2>&1 <<'PY'
import json, sys
B = sys.argv[1]
e = json.load(open(B + '/research/P2-CAPABILITY-EXTRACTION.json'))
m = json.load(open(B + '/research/P2-CAPABILITY-MATRIX.json'))
ids = {c['capability_id'] for c in e['capabilities']}
missing = [r['capability_id'] for r in m['capabilities']
           if r['capability_id'] not in ids]
if missing:
    print("matrix references unknown capability ids: %s" % missing)
if not m.get('capabilities'):
    print("matrix is empty")
PY
if [ -s "$TMP/caps_ok" ]; then
  while IFS= read -r l; do fail "capability matrix: $l"; done < "$TMP/caps_ok"
else
  pass "capability matrix entries all exist in the extraction"
fi

sect "4. Research findings kept OUT of the production registry"
# Since P3 the registry may be populated by legitimately promoted capabilities,
# but P2 research output must never appear there. The invariant is provenance,
# not emptiness: every registered capability must trace to a P3 promotion gate
# result, never be a P2 research record.
python3 - "$SPS2" > "$TMP/leak" 2>&1 <<'PY'
import json, os, sys
B = sys.argv[1]
reg = json.load(open(B + '/capability/registry.json'))
ex = json.load(open(B + '/research/P2-CAPABILITY-EXTRACTION.json'))
research_only = {c['capability_id'] for c in ex['capabilities']}
for c in reg.get('capabilities', []):
    cid = c.get('capability_id')
    if cid in research_only:
        print("RESEARCH_ONLY_LEAK: %s is a P2 research record" % cid)
    if str(c.get('origin', '')).upper() == 'RESEARCH_ONLY':
        print("RESEARCH_ONLY_LEAK: %s declares origin RESEARCH_ONLY" % cid)
    if not c.get('provenance', {}).get('commit'):
        print("UNTRACEABLE_PROVENANCE: %s has no commit" % cid)
PY
if [ -s "$TMP/leak" ]; then
  while IFS= read -r l; do fail "$l"; done < "$TMP/leak"
else
  pass "no P2 research record appears in the production registry"
fi
LEAK=$(python3 -c "
import json
d=json.load(open('$SPS2/research/P2-CAPABILITY-EXTRACTION.json'))
print(sum(1 for c in d['capabilities'] if c.get('in_production_registry')))" 2>/dev/null || echo 1)
[ "$LEAK" = "0" ] && pass "no P2 extraction claims registry membership" \
                 || fail "$LEAK P2 capabilities claim registry membership"
# Every registered capability must carry a promotion assessment consistent
# with the CURRENT production gate (hardened A-K since P4).
python3 - "$SPS2" > "$TMP/gatechk" 2>&1 <<'PY'
import importlib.util, json, os, sys
B = sys.argv[1]
reg = json.load(open(B + '/capability/registry.json'))
pg_path = os.path.join(B, 'capability', 'promotion_gates.py')
if os.path.isfile(pg_path):
    spec = importlib.util.spec_from_file_location("pg", pg_path)
    pg = importlib.util.module_from_spec(spec); spec.loader.exec_module(pg)
    for c in reg.get('capabilities', []):
        res, blocking = pg.evaluate(c)
        stored = (c.get('promotion_assessment') or {}).get('blocking_gates')
        if stored is None:
            print("ASSESSMENT_MISSING: %s" % c['capability_id'])
        elif sorted(stored) != sorted(blocking):
            print("ASSESSMENT_STALE: %s" % c['capability_id'])
else:
    sys.path.insert(0, B + '/capability')
    import engine
    for c in reg.get('capabilities', []):
        ok, reasons = engine.promote(c)
        if not ok:
            print("PROMOTION_GATE_FAIL: %s: %s"
                  % (c['capability_id'], "; ".join(reasons)))
PY
if [ -s "$TMP/gatechk" ]; then
  while IFS= read -r l; do fail "$l"; done < "$TMP/gatechk"
else
  pass "every registered capability passes the P3 promotion gate"
fi

sect "5. Unresolved conflicts recorded, not reconciled"
jq -e '.conflicts | length > 0' "$SPS2/research/P2-SOURCES.json" >/dev/null 2>&1 \
  && pass "conflicts block present and non-empty" || fail "no conflict recorded"
jq -e '.conflicts[0].resolution | test("UNRESOLVED")' "$SPS2/research/P2-SOURCES.json" >/dev/null 2>&1 \
  && pass "CONF-001 left explicitly UNRESOLVED" || fail "conflict was silently reconciled"
jq -e '.capabilities[] | select(.capability_id=="CAP-028") | .sps_recommendation == "RESEARCH_FURTHER"' \
  "$SPS2/research/P2-CAPABILITY-EXTRACTION.json" >/dev/null 2>&1 \
  && pass "unverified thresholds held at RESEARCH_FURTHER" || fail "unverified claim was promoted"

sect "6. Interoperability honesty"
jq -e '[.records[].support[]] | all(. == "native" or . == "adapter" or . == "partial" or . == "external" or . == "unavailable" or . == "unknown")' \
  "$SPS2/research/P2-INTEROPERABILITY-MATRIX.json" >/dev/null 2>&1 \
  && pass "all support values are from the declared classification" || fail "invalid support value present"
jq -e '[.records[].support[] | select(. == "unknown")] | length > 0' \
  "$SPS2/research/P2-INTEROPERABILITY-MATRIX.json" >/dev/null 2>&1 \
  && pass "unknown recorded where support was not verified" || warn "no unknown values recorded"
if jq -e '[.records[] | select((tostring | ascii_downcase) | test("universal"))] | length > 0' \
   "$SPS2/research/P2-INTEROPERABILITY-MATRIX.json" >/dev/null 2>&1; then
  fail "a capability is claimed universal"
else
  pass "no capability is claimed universal"
fi
sect "7. Standing constraints survive research"
EMJ=$(python3 - "$SPS2" <<'PY'
import os, sys, re
pat = re.compile('[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]')
hits = []
for root, dirs, files in os.walk(sys.argv[1]):
    dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules'}]
    for f in files:
        p = os.path.join(root, f)
        try:
            t = open(p, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        if pat.search(t):
            hits.append(p.replace(sys.argv[1] + '/', ''))
print(';'.join(hits))
PY
)
[ -z "$EMJ" ] && pass "no emoji in any sps2 file including research" || fail "emoji found: $EMJ"

LEGACY_OUT="$(python3 "$SPS2/governance/legacy_exceptions.py" \
  --root "$REPO" --baseline c11da27 \
  --pathspec skills --pathspec scripts --pathspec plugins --pathspec .github \
  --pathspec templates --pathspec README.md --pathspec CHANGELOG.md \
  --pathspec CATALOG.md --pathspec '*.sh' --pathspec '*.ps1' \
  --exclude-prefix sps2/ 2>&1)"
if [ $? -eq 0 ]; then
  pass "legacy repository matches the DEC-7301 pinned exception"
else
  while IFS= read -r line; do [ -n "$line" ] && fail "$line"; done <<< "$LEGACY_OUT"
fi

if grep -rqE --exclude-dir=tools 'git config --global|\$HOME/\.claude|\$HOME/\.codex|\$HOME/\.config' "$SPS2" 2>/dev/null; then
  fail "sps2 references machine-global state"
else
  pass "no machine-global path referenced in sps2"
fi

sect "8. No external code or artefact imported"
if find "$SPS2" \( -name 'node_modules' -o -name 'package-lock.json' \
   -o -name '*.whl' -o -name '*.tar.gz' \) 2>/dev/null | grep -q .; then
  fail "external build artefact present in sps2"
else
  pass "no external build artefact or dependency lock in sps2"
fi

sect "9. Approval is genuine, user-attributed and bounded"
# Approval may only ever be attributed to the user, never to an agent.
jq -e '[.requirements[] | select(.approval.state == "APPROVED")
        | .approval.decided_by] | length > 0 and all(. == "User")' \
  "$SPS2/requirements/P2-REQUIREMENTS.json" >/dev/null 2>&1 \
  && pass "every approved P2 requirement is attributed to User" \
  || fail "a P2 requirement approval is not user-attributed"
jq -e '[.decisions[] | select(.approval.state == "APPROVED")
        | .approval.decided_by] | length > 0 and all(. == "User")' \
  "$SPS2/decisions/P2-DECISIONS.json" >/dev/null 2>&1 \
  && pass "every approved P2 decision is attributed to User" \
  || fail "a P2 decision approval is not user-attributed"
jq -e '.handoffs[0].user_approval == "APPROVED"
       and (.handoffs[0].current_state | test("APPROVED"))' \
  "$SPS2/handoff/HANDOFF-P2.json" >/dev/null 2>&1 \
  && pass "P2 handoff reads APPROVED" || fail "P2 handoff state is wrong"

# The approval must be bounded: P2 research only, P3 not approved.
jq -e '.approval_scope.p3 == "NOT_APPROVED"' \
  "$SPS2/handoff/HANDOFF-P2.json" >/dev/null 2>&1 \
  && pass "P3 explicitly recorded as NOT_APPROVED" || fail "P3 approval scope missing"
jq -e '.approval_scope.production_capability_registry | test("NOT_APPROVED")' \
  "$SPS2/handoff/HANDOFF-P2.json" >/dev/null 2>&1 \
  && pass "registry explicitly recorded as NOT approved" || fail "registry scope missing"

# Approving P2 research must NOT have populated the registry at approval time.
# Since P3 the registry may legitimately hold promoted capabilities, so the
# check is provenance (every entry traces to a promotion gate), not emptiness.
if python3 - "$SPS2/capability/registry.json" <<'PY' >/dev/null 2>&1
import json, sys
reg = json.load(open(sys.argv[1]))
raise SystemExit(1 if any(not c.get('provenance', {}).get('commit')
                         for c in reg.get('capabilities', [])) else 0)
PY
then
  pass "every registry entry carries a traceable commit"
else
  fail "a registry entry lacks traceable provenance"
fi
# P2 extraction must still claim zero registry membership.
LEAKN=$(python3 -c "
import json
d=json.load(open('$SPS2/research/P2-CAPABILITY-EXTRACTION.json'))
print(sum(1 for c in d['capabilities'] if c.get('in_production_registry')))" 2>/dev/null || echo -1)
if [ "$LEAKN" = "0" ]; then
  pass "P2 research records still claim no registry membership"
else
  fail "$LEAKN P2 research records claim registry membership"
fi

# Unresolved research gaps must survive the approval unchanged.
jq -e '.conflicts[0].resolution | test("UNRESOLVED")' \
  "$SPS2/research/P2-SOURCES.json" >/dev/null 2>&1 \
  && pass "CONF-001 still UNRESOLVED after approval" || fail "CONF-001 was silently closed"
jq -e '.capabilities[] | select(.capability_id=="CAP-028")
       | .sps_recommendation == "RESEARCH_FURTHER" and .status == "UNVERIFIED"' \
  "$SPS2/research/P2-CAPABILITY-EXTRACTION.json" >/dev/null 2>&1 \
  && pass "CAP-028 gap preserved (UNVERIFIED, RESEARCH_FURTHER)" \
  || fail "CAP-028 gap was altered by approval"
grep -q 'PARTIAL' "$SPS2/tasks/P2-TASKS.md" \
  && pass "PARTIAL research tasks preserved as documented" || fail "PARTIAL tasks were removed"

fi  # end structural
# ══ NEGATIVE SUITE ═══════════════════════════════════════════════════════════
# Runs in BOTH modes; --negative executes this suite alone.
sect "NEGATIVE TESTS — invalid P2 records must be rejected"

neg() {  # kind label expect-regex python-mutation
  local kind="$1" label="$2" expect="$3" mut="$4"
  python3 - "$kind" "$mut" > "$TMP/n.json" <<'PY'
import json, sys
BASE = {
 "sources": {"sources": [
   {"source_id": "SRC-001", "url": "https://example.org/a", "project": "X",
    "source_type": "OFFICIAL_REPO", "source_rank": 1, "accessed": "2026-10-03",
    "relevance": "architecture evidence", "claims_supported": "structure"}],
  "conflicts": []},
 "capability": {"known_source_ids": ["SRC-001"], "capabilities": [
   {"capability_id": "CAP-001", "capability": "fixture", "source": "X",
    "status": "IMPLEMENTED", "evidence": ["SRC-001"], "confidence": "HIGH",
    "harness_scope": ["Claude Code"], "sps_recommendation": "KEEP",
    "in_production_registry": False}]},
 "interop": {"records": [
   {"capability": "fixture", "support": {"Claude Code": "native", "Codex": "unknown"},
    "confidence": "HIGH", "basis": "official docs"}]},
}
kind, mut = sys.argv[1], sys.argv[2]
d = json.loads(json.dumps(BASE[kind]))
exec(mut)
print(json.dumps(d))
PY
  local out; out="$(run_check "$kind" "$TMP/n.json")"
  if [ -n "$out" ] && printf '%s' "$out" | grep -qiE "$expect"; then
    info "REJECTED -> $label"; NEG_PASS=$((NEG_PASS+1)); pass "$label -> rejected"
  else
    info "NOT REJECTED (validator defect!) -> $label"
    NEG_FAIL=$((NEG_FAIL+1)); fail "$label -> NOT rejected (out: ${out:-none})"
  fi
}

# CASE P0 positive control: a valid record MUST be accepted
python3 -c "
import json
json.dump({'known_source_ids':['SRC-001'],'capabilities':[{'capability_id':'CAP-001',
 'capability':'fixture','source':'X','status':'IMPLEMENTED','evidence':['SRC-001'],
 'confidence':'HIGH','harness_scope':['Claude Code'],'sps_recommendation':'KEEP',
 'in_production_registry':False}]}, open('$TMP/pos.json','w'))"
P0="$(python3 "$CHECK" capability "$TMP/pos.json" 2>&1)"; P0_RC=$?
if [ "$P0_RC" -ne 0 ]; then
  info "WRONGLY REJECTED (over-blocking) -> CASE P0 (checker exited $P0_RC)"
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE P0  positive control could not run: $P0"
elif [ -z "$P0" ]; then
  info "ACCEPTED -> CASE P0 positive control"
  NEG_PASS=$((NEG_PASS+1)); pass "CASE P0  valid capability record accepted"
else
  info "WRONGLY REJECTED (over-blocking) -> CASE P0"
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE P0  valid record rejected: $P0"
fi

# --- source integrity ---
neg sources "P1  source with missing URL"          "missing or non-http url" \
    "d['sources'][0]['url']=''"
neg sources "P2  source with invalid rank"         "source_rank must be" \
    "d['sources'][0]['source_rank']=9"
neg sources "P3  source with missing access date"  "accessed must be" \
    "d['sources'][0]['accessed']='recently'"
neg sources "P4  duplicate source ids"             "duplicate source IDs" \
    "d['sources'].append(dict(d['sources'][0]))"
neg sources "P5  low-rank source not marked"       "must be marked SIGNAL_ONLY" \
    "d['sources'][0]['source_rank']=6"
neg sources "P6  conflict without a resolution"    "no recorded resolution" \
    "d['conflicts']=[{'id':'C1'}]"

# --- capability fabrication and integrity ---
neg capability "P7  capability with no evidence"   "FABRICATED_CAPABILITY" \
    "d['capabilities'][0]['evidence']=[]"
neg capability "P8  unsupported recommendation"    "not in taxonomy" \
    "d['capabilities'][0]['sps_recommendation']='AWESOME'"
neg capability "P9  duplicate capability ids"      "duplicate capability IDs" \
    "d['capabilities'].append(dict(d['capabilities'][0]))"
neg capability "P10 capability leaked to registry" "leaked into the production registry" \
    "d['capabilities'][0]['in_production_registry']=True"
neg capability "P11 citation of an unknown source" "cites unknown source" \
    "d['capabilities'][0]['evidence']=['SRC-999']"
neg capability "P12 UNVERIFIED promoted to KEEP"   "must be RESEARCH_FURTHER" \
    "d['capabilities'][0]['status']='UNVERIFIED'"
neg capability "P13 unsupported harness claimed"   "unsupported harness" \
    "d['capabilities'][0]['harness_scope']=['Claude Code','Windsurf 9']"
neg capability "P14 malformed capability id"        "bad capability_id" \
    "d['capabilities'][0]['capability_id']='cap 1'"

# --- interoperability honesty ---
neg interop "P15 unsupported harness in matrix"    "unsupported harness" \
    "d['records'][0]['support']['Emacs 27']='native'"
neg interop "P16 invalid support classification"  "invalid support value" \
    "d['records'][0]['support']['Codex']='works fine'"
neg interop "P17 universal claim without evidence" "claims universality" \
    "d['records'][0]['support']['Codex']='universal'"
neg interop "P18 HIGH confidence without basis"    "HIGH confidence without" \
    "d['records'][0]['basis']=''"

# --- malformed structured data ---
printf '{ not valid json at all' > "$TMP/malformed.json"
if [ -n "$(run_check sources "$TMP/malformed.json")" ]; then
  info "REJECTED -> CASE P19 malformed JSON"
  NEG_PASS=$((NEG_PASS+1)); pass "CASE P19  malformed JSON rejected"
else
  info "NOT REJECTED -> CASE P19"
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE P19  malformed JSON NOT rejected"
fi

# --- stale research record ---
python3 -c "
import json
json.dump({'records':[{'evidence_id':'EV-P2-001','result':'PASS',
 'observed_result':'x'*40,'timestamp':'2018-05-01T00:00:00Z'}]}, open('$TMP/stale.json','w'))"
if [ -n "$(run_check evidence "$TMP/stale.json")" ]; then
  info "REJECTED -> CASE P20 stale research record"
  NEG_PASS=$((NEG_PASS+1)); pass "CASE P20  stale research record rejected"
else
  info "NOT REJECTED -> CASE P20"
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE P20  stale research record NOT rejected"
fi

# --- approval attribution ---
python3 -c "
import json
json.dump({'requirements':[{'requirement_id':'REQ-P2-01','title':'t',
 'objective':'o'*20,'acceptance_criteria':['c'*20],'risk':'HIGH',
 'implementation':{'state':'NOT_STARTED','refs':[]},
 'verification':{'state':'UNVERIFIED','method':'AUTOMATED'},
 'approval':{'state':'APPROVED','decided_by':'agent'}}]}, open('$TMP/appr.json','w'))"
if [ -n "$(run_check requirements "$TMP/appr.json")" ]; then
  info "REJECTED -> CASE P21 approval attributed to an agent"
  NEG_PASS=$((NEG_PASS+1)); pass "CASE P21  agent-attributed approval rejected"
else
  info "NOT REJECTED -> CASE P21"
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE P21  agent-attributed approval NOT rejected"
fi

echo ""
if [ "$NEG_FAIL" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}== P2 NEGATIVE SUITE: $NEG_PASS cases correctly rejected, 0 missed ==${NC}"
else
  echo -e "${RED}${BOLD}== P2 NEGATIVE SUITE: $NEG_PASS rejected, $NEG_FAIL MISSED ==${NC}"
fi

echo ""
if [ "$FAIL" -eq 0 ] && [ "$NEG_FAIL" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}== P2 RESEARCH VALID: $PASS checks passed, 0 failed, $NEG_PASS negative cases enforced ==${NC}"
  exit 0
fi
echo -e "${RED}${BOLD}== P2 RESEARCH INVALID: $PASS passed, $FAIL failed, $NEG_FAIL missed ==${NC}"
exit 1
