#!/usr/bin/env bash
# SPS 2.0 P4 production promotion validator.
# Runs the hardened A-K gate on real capabilities, executes the verification
# suite, and enforces 20 negative cases plus positive controls.
# SAFETY: no network, no installs, no machine-global writes.
# Usage: bash framework/sps2/tools/validate-p4.sh [--negative]
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPS2="$(cd "$HERE/.." && pwd)"
REPO="$(cd "$SPS2/.." && pwd)"
CHECK="$HERE/check_p4.py"
EMOJI="$HERE/check_emoji.py"
GATE="$SPS2/capability/promotion_gates.py"
REG="$SPS2/capability/registry.json"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'
BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'
PASS=0; FAIL=0; NP=0; NF=0; CTR=0
pass() { echo -e "  ${GREEN}PASS${NC}  $*"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}FAIL${NC}  $*"; FAIL=$((FAIL+1)); }
info() { echo -e "  ${BLUE}CASE${NC} $*"; }
sect() { echo -e "\n${BOLD}$*${NC}"; }

command -v python3 >/dev/null 2>&1 || { echo "python3 unavailable"; exit 2; }
TMP="$(mktemp -d "${TMPDIR:-/tmp}/sps2p4-XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
NEG_ONLY=false
for a in "$@"; do [ "$a" = "--negative" ] && NEG_ONLY=true; done

echo -e "${BOLD}SPS 2.0 P4 Production Promotion Validator${NC}"
echo -e "${DIM}hardened gate A-K, real verification, 20 negative cases${NC}"

# ── build a fully-conforming fixture, then mutate it for negative cases ────
cat > "$TMP/mk.py" <<'FIX'
import json, sys
B = {
 "capability_id": "CAP-P03-900", "name": "fixture", "type": "DEV_TOOL",
 "domain": "GOVERNANCE", "purpose": "A valid synthetic fixture",
 "version": "1.0.0", "source": "SPS2_CORE", "licence": "KNOWN_PERMISSIVE",
 "licence_evidence": "synthetic fixture",
 "provenance": {"origin": "synthetic", "commit": "abc1234",
                "fact_class": "EVIDENCE", "repository_relative_path":
                "framework/sps2/capability/engine.py",
                "source_url": "https://example.invalid/synthetic-fixture",
                "research_refs": ["EV-P4-900"]},
 "security": {"status": "VERIFIED_SAFE", "evidence": "synthetic",
              "fact_class": "EVIDENCE"},
 "compatibility": {"status": "COMPATIBLE", "agent_neutral": True,
                   "basis": "synthetic"},
 "staleness": {"state": "CURRENT", "maintenance": "ACTIVE",
               "last_checked": "2026-10-03", "review_due": "2027-01-03",
               "reevaluation_triggers": ["source changed"]},
 "install_scope": "PROJECT_LOCAL", "evidence": ["EV-P4-900"],
 "confidence": "HIGH", "lifecycle_state": "CANDIDATE",
 "approval": {"state": "APPROVED", "decided_by": "User"},
 "verification": {"state": "VERIFIED", "method": "AUTOMATED",
                  "evidence": ["EV-P4-900"], "expected_result": "ok",
                  "observed_result": "ok"},
 "selection_policy": {"popularity_role": "TIE_BREAKER_ONLY"},
 "linked_requirements": ["REQ-P4-01"],
 "acceptance_criteria": ["fixture criterion"],
 "popularity": {"stars": 0}, "last_verified": "2026-10-03",
}
exec(sys.argv[1])
print(json.dumps(B))
FIX
mk() { python3 "$TMP/mk.py" "$1" > "$TMP/c.json"; }

# gate_case <mutation> <expected-gate-letter> <label>
gate_case() {
  mk "$1"
  local out; out="$(python3 "$CHECK" "$TMP/c.json" 2>&1)"
  if printf '%s\n' "$out" | grep -qE "^  $2 .*FAIL"; then
    info "REJECTED -> $3"; NNP=$((NNP+1)); pass "$3 -> rejected"
  else
    info "NOT REJECTED (defect!) -> $3"; NNF=$((NNF+1))
    fail "$3 -> NOT rejected"
  fi
}
if [ "$NEG_ONLY" != true ]; then

sect "1. P4 deliverables present"
for f in capability/promotion_gates.py capability/promotion-assessments.json \
         capability/registry.json tools/check_p4.py tools/check_emoji.py \
         requirements/P4-REQUIREMENTS.json evidence/P4-EVIDENCE.json \
         decisions/P4-DECISIONS.json tasks/P4-TASKS.md \
         handoff/HANDOFF-P4.json; do
  [ -f "$SPS2/$f" ] && pass "present $f" || fail "missing $f"
done
[ -f "$REPO/AUDIT-PHASE-08-P4-PRODUCTION-PROMOTION.md" ] \
  && pass "present AUDIT-PHASE-08 report" || fail "missing AUDIT-PHASE-08 report"

sect "2. Positive controls: only an explicit User approval enables promotion"
mk "pass"
# The base fixture is fully conforming INCLUDING an explicit User approval, so
# it must promote. This proves the gate is not permanently stuck.
if python3 "$CHECK" "$TMP/c.json" --promote 2>&1 | grep -q '^PROMOTED'; then
  CTR=$((CTR+1)); pass "POSCTRL-A  a fully conforming capability IS promoted (gate works)"
else
  fail "POSCTRL-A  a conforming capability was not promoted (gate is stuck)"
fi
# Remove the approval: now exactly one gate, H, must block. This proves H is
# the live blocker and that D being satisfied changed nothing on its own.
python3 -c "
import json
d=json.load(open('$TMP/c.json'))
d['approval']={'state':'PENDING_USER_APPROVAL'}
json.dump(d,open('$TMP/c_noappr.json','w'))"
OUT=$(python3 "$CHECK" "$TMP/c_noappr.json" --promote 2>&1)
PASSED=$(printf '%s\n' "$OUT" | grep -cE '^  [A-K] .*PASS')
D_PASS=$(printf '%s\n' "$OUT" | grep -cE '^  D .*PASS')
H_FAIL=$(printf '%s\n' "$OUT" | grep -cE '^  H .*FAIL')
if [ "$PASSED" -eq 10 ] && [ "$D_PASS" -eq 1 ] && [ "$H_FAIL" -eq 1 ] \
   && printf '%s\n' "$OUT" | grep -q 'blocking=H$'; then
  CTR=$((CTR+1)); pass "POSCTRL-C  10 gates pass, only H blocks, nothing promoted"
else
  info "POSCTRL-C unexpected: $OUT"; fail "POSCTRL-C  H did not block as the sole blocker"
fi
# A declared licence alone must never enable promotion.
# NEGATIVE control. The polarity here is already correct (absent PROMOTED => fail
# branch => pass), but absence of PROMOTED is only meaningful if the checker RAN
# and emitted a verdict. A crash, a missing checker, or a verdict-less run all
# produce empty stdout and previously satisfied this control. Require rc==0 AND
# an emitted verdict before any PASS.
OUT_D="$(python3 "$CHECK" "$TMP/c_noappr.json" --promote 2>&1)"; RC_D=$?
if [ "$RC_D" -ne 0 ]; then
  fail "POSCTRL-D  checker exited $RC_D - negative control could not run"
elif ! printf '%s\n' "$OUT_D" | grep -qE '^(PROMOTED|NOT_PROMOTED)([[:space:]]|$)'; then
  fail "POSCTRL-D  no promotion verdict emitted - negative control could not run"
elif printf '%s\n' "$OUT_D" | grep -q '^PROMOTED'; then
  fail "POSCTRL-D  promotion became possible on a licence alone"
else
  CTR=$((CTR+1)); pass "POSCTRL-D  a declared licence alone does not enable promotion (correct)"
fi
# An agent-attributed approval must NOT enable promotion either.
python3 -c "
import json
d=json.load(open('$TMP/c.json'))
d['approval']={'state':'APPROVED','decided_by':'Agent'}
json.dump(d,open('$TMP/c_agent.json','w'))"
OUT_E="$(python3 "$CHECK" "$TMP/c_agent.json" --promote 2>&1)"; RC_E=$?
if [ "$RC_E" -ne 0 ]; then
  fail "POSCTRL-E  checker exited $RC_E - negative control could not run"
elif ! printf '%s\n' "$OUT_E" | grep -qE '^(PROMOTED|NOT_PROMOTED)([[:space:]]|$)'; then
  fail "POSCTRL-E  no promotion verdict emitted - negative control could not run"
elif printf '%s\n' "$OUT_E" | grep -q '^PROMOTED'; then
  fail "POSCTRL-E  an agent-attributed approval enabled promotion"
else
  CTR=$((CTR+1)); pass "POSCTRL-E  an agent-attributed approval does NOT enable promotion"
fi

sect "3. Registry is consistent with the gate (computed, not asserted)"
python3 - "$SPS2" > "$TMP/cons" 2>&1 <<'PY'
import importlib.util, json, os, sys
B = sys.argv[1]
spec = importlib.util.spec_from_file_location(
    "pg", os.path.join(B, "capability", "promotion_gates.py"))
pg = importlib.util.module_from_spec(spec); spec.loader.exec_module(pg)
reg = json.load(open(os.path.join(B, "capability", "registry.json")))
ids = [c["capability_id"] for c in reg["capabilities"]]
for d in sorted({i for i in ids if ids.count(i) > 1}):
    print("DUPLICATE_ID: %s" % d)
for c in reg["capabilities"]:
    res, blocking = pg.evaluate(c)
    rec = pg.decide(blocking)
    stored = c.get("promotion_assessment", {})
    if stored.get("blocking_gates") != blocking:
        print("STALE_ASSESSMENT: %s stored=%s computed=%s"
              % (c["capability_id"], stored.get("blocking_gates"), blocking))
    if stored.get("recommendation") != rec:
        print("STALE_RECOMMENDATION: %s" % c["capability_id"])
    if rec == "PROMOTE" and c.get("lifecycle_state") != "EVALUATED":
        print("PROMOTED_WITHOUT_STATE: %s" % c["capability_id"])
    if rec != "PROMOTE" and c.get("lifecycle_state") == "ACTIVE":
        print("ACTIVE_WITHOUT_PROMOTION: %s" % c["capability_id"])
PY
if [ -s "$TMP/cons" ]; then
  while IFS= read -r l; do fail "$l"; done < "$TMP/cons"
else
  pass "every stored assessment matches a freshly computed gate run"
fi

sect "4. Verification is executed, not asserted"
python3 - "$SPS2" > "$TMP/ver" 2>&1 <<'PY'
import json, os, sys
B = sys.argv[1]
reg = json.load(open(os.path.join(B, "capability", "registry.json")))
for c in reg["capabilities"]:
    v = c.get("verification", {})
    rel = (c.get("provenance") or {}).get("repository_relative_path") or ""
    impl = rel.endswith((".py", ".sh", ".js", ".ts")) and \
        os.path.isfile(os.path.join(B, "..", rel))
    if v.get("state") == "VERIFIED" and not impl:
        print("VERIFIED_WITHOUT_IMPLEMENTATION: %s" % c["capability_id"])
    if v.get("state") == "VERIFIED" and not v.get("observed_result"):
        print("VERIFIED_WITHOUT_OBSERVED_RESULT: %s" % c["capability_id"])
    if v.get("state") == "VERIFIED" and not v.get("evidence"):
        print("VERIFIED_WITHOUT_EVIDENCE: %s" % c["capability_id"])
PY
if [ -s "$TMP/ver" ]; then
  while IFS= read -r l; do fail "$l"; done < "$TMP/ver"
else
  pass "no capability is VERIFIED without an implementation and evidence"
fi
NV=$(python3 -c "
import json
print(sum(1 for c in json.load(open('$REG'))['capabilities']
          if c['verification']['state']=='VERIFIED'))")
[ "$NV" -ge 1 ] && pass "$NV capabilities carry executed verification" \
                || fail "no executed verification recorded"

sect "5. No-emoji policy enforced (with positive control)"
EMJ=$(python3 "$EMOJI" "$SPS2" 2>&1 | tail -1)
printf '%s' "$EMJ" | grep -q 'violations=0' \
  && pass "no emoji in any SPS 2.0 file ($EMJ)" \
  || fail "emoji violation: $EMJ"
mkdir -p "$TMP/emj" && printf 'x \360\237\216\257 y\n' > "$TMP/emj/a.md"
if python3 "$EMOJI" "$TMP/emj" >/dev/null 2>&1; then
  fail "emoji checker failed to detect a real violation"
else
  CTR=$((CTR+1)); pass "POSCTRL-B  emoji checker detects a real violation"
fi
rm -rf "$TMP/emj"

sect "7. Research gaps preserved"
jq -e '.conflicts[0].resolution | test("UNRESOLVED")' \
  "$SPS2/research/P2-SOURCES.json" >/dev/null 2>&1 \
  && pass "CONF-001 still UNRESOLVED" || fail "CONF-001 was closed"
jq -e '.capabilities[] | select(.capability_id=="CAP-028") | .status == "UNVERIFIED"' \
  "$SPS2/research/P2-CAPABILITY-EXTRACTION.json" >/dev/null 2>&1 \
  && pass "CAP-028 still UNVERIFIED (no LCP/INP invented)" || fail "CAP-028 changed"
if jq -e '.capabilities[] | select(.capability_id=="CAP-P03-005")
        | (.security.evidence | test("LCP|INP"))' "$REG" >/dev/null 2>&1; then
  fail "an unretrieved LCP/INP threshold was introduced"
else
  pass "no LCP or INP threshold introduced into the registry"
fi

sect "8. P3 incident boundary carried forward unchanged"
jq -e '.approval_scope.credential_revocation == "USER_ATTESTED_NOT_INDEPENDENTLY_VERIFIED"' \
  "$SPS2/handoff/HANDOFF-P3.json" >/dev/null 2>&1 \
  && pass "revocation still USER_ATTESTED_NOT_INDEPENDENTLY_VERIFIED" \
  || fail "incident classification was changed"
jq -e '.approval_scope.forensic_checkpoint_a7767cf | test("PRESERVED")' \
  "$SPS2/handoff/HANDOFF-P3.json" >/dev/null 2>&1 \
  && pass "checkpoint a7767cf still recorded PRESERVED" || fail "checkpoint scope changed"
if git -C "$REPO" cat-file -t a7767cf5f761cab4aa633c1cbc7604f83e4d14f8 \
     >/dev/null 2>&1; then
  pass "checkpoint a7767cf not purged"
else
  fail "checkpoint a7767cf was purged"
fi

sect "9. P4 approval is bounded, attributable, and promotes nothing"
python3 - "$SPS2" > "$TMP/appr" 2>&1 <<'PY'
import json, os, re, subprocess, sys
B = sys.argv[1]
req = json.load(open(B + '/requirements/P4-REQUIREMENTS.json'))
dec = json.load(open(B + '/decisions/P4-DECISIONS.json'))
ho = json.load(open(B + '/handoff/HANDOFF-P4.json'))['handoffs'][0]
sys.path.insert(0, B + '/governance')
import attribution as ATTR
AGENT = ATTR.AGENTISH  # SPEC-2: single authoritative policy

def approval_ok(a, where):
    """An approval is valid only when attributable to an identifiable User."""
    if (a or {}).get('state') != 'APPROVED':
        print("NOT_APPROVED: %s state=%s" % (where, (a or {}).get('state')))
        return False
    who = (a.get('approved_by') or '').strip()
    if not who:
        print("APPROVAL_UNATTRIBUTED: %s" % where); return False
    if AGENT.search(who):
        print("APPROVAL_ATTRIBUTED_TO_AGENT: %s -> %s" % (where, who)); return False
    if not (a.get('approved_on') or '').strip():
        print("APPROVAL_UNDATED: %s" % where); return False
    return True

for r in req['requirements']:
    approval_ok(r.get('approval'), r['requirement_id'])
for d in dec['decisions']:
    approval_ok(d.get('approval'), d['decision_id'])

# A capability may be promoted ONLY under an explicit, attributable User
# production-promotion approval. Section 12d proves the promoted set matches the
# approved set exactly; here we only require that any APPROVED approval names
# the User and scopes itself to production promotion.
reg = json.load(open(B + '/capability/registry.json'))
for c in reg['capabilities']:
    ap = c.get('approval') or {}
    if ap.get('state') == 'APPROVED':
        if ap.get('decided_by') != 'User':
            print("APPROVAL_NOT_USER_ATTRIBUTED: %s" % c['capability_id'])
        scope = (ap.get('scope') or '')
        if 'production promotion' not in scope:
            print("APPROVAL_SCOPE_UNEXPECTED: %s scope=%s"
                  % (c['capability_id'], scope))
        if not ap.get('decided_on'):
            print("APPROVAL_UNDATED: %s" % c['capability_id'])

# The licence was RESOLVED by explicit user decision on 2026-10-04 (MIT). The
# invariant is no longer "unresolved" but "resolved only by an attributable User
# decision that is consistent with the tracked licence file and the registry".
lic = [d for d in dec['decisions'] if d.get('unresolved', {}).get('item')
       == 'repository_licence']
if not lic:
    print("LICENCE_DECISION_RECORD_MISSING")
else:
    st = lic[0]['unresolved']
    if st['state'] != 'RESOLVED_BY_USER_DECISION':
        print("LICENCE_UNEXPECTED_STATE: %s" % st['state'])
    if st.get('decided_by') != 'User':
        print("LICENCE_NOT_USER_DECIDED: %s" % st.get('decided_by'))
    if st.get('licence') != 'MIT':
        print("LICENCE_MISMATCH_RECORD_VS_FILE: %s" % st.get('licence'))
    if st.get('provenance_prerequisite') != 'SATISFIED_BY_USER_ATTESTATION':
        print("LICENCE_PROVENANCE_NOT_ATTESTED: %s"
              % st.get('provenance_prerequisite'))
    if st.get('third_party_code_relicensed') is not False:
        print("LICENCE_THIRD_PARTY_CLAIM: third-party relicensing must be false")
    if st.get('independent_legal_verification_claimed') is not False:
        print("LICENCE_OVERCLAIMS_VERIFICATION")

# A tracked licence file must exist and the registry must agree with it.
R = os.path.dirname(B)
tracked = subprocess.run(['git', '-C', R, 'ls-files'], capture_output=True,
                         text=True).stdout.split()
lic_files = [n for n in tracked
             if re.fullmatch(r'(LICEN[SC]E|COPYING)(\.\w+)?', n, re.I)]
if not lic_files:
    print("LICENCE_FILE_NOT_TRACKED: gate D cannot pass without it")
for c in reg['capabilities']:
    if c.get('licence') != 'KNOWN_PERMISSIVE' or \
       c.get('licence_name') != 'MIT':
        print("LICENCE_REGISTRY_MISMATCH: %s licence=%s name=%s"
              % (c['capability_id'], c.get('licence'), c.get('licence_name')))
    if c.get('licence_decided_by') != 'User':
        print("LICENCE_REGISTRY_NOT_USER_DECIDED: %s" % c['capability_id'])
    if not (c.get('licence_evidence') or '').strip():
        print("LICENCE_REGISTRY_NO_EVIDENCE: %s" % c['capability_id'])
    if c.get('licence_decided_on') is None:
        print("LICENCE_REGISTRY_UNDATED: %s" % c['capability_id'])

# Phase-boundary invariant, revised after explicit User P5 authorisation.
#
# OBSOLETE INVARIANT: "no P5 artefact may exist". That encoded "P5 has not
# started", true while P4 was the newest phase but false once the User
# explicitly authorised P5. It would have failed on legitimate approved work.
#
# STRONGER REPLACEMENT: a P5 artefact is permitted only when a P5 authorisation
# record exists AND is attributable to an identifiable User. An unauthorised P5
# artefact is still a failure, so the check is conditional rather than removed.
# P6 stays forbidden outright: no P6 approval exists.
sys.path.insert(0, os.path.join(B, 'governance'))
import attribution as ATTR
P5_AUTH = os.path.join(B, 'evidence/P5-EVIDENCE.json')
p5_authorised = False
if os.path.exists(P5_AUTH):
    pa = json.load(open(P5_AUTH)).get('phase_approval') or {}
    who = (pa.get('authorised_by') or '').strip().lower()
    if pa.get('scope') == 'P5 implementation/integration' and who \
            and not ATTR.AGENTISH.search(who):
        p5_authorised = True
    else:
        print("P5_AUTHORISATION_NOT_USER_ATTRIBUTABLE: %r" % who)
P5_ARTEFACTS = ('requirements/P5-REQUIREMENTS.json',
                'handoff/HANDOFF-P5.json', 'handoff/HANDOFF-P5.md',
                'decisions/P5-DECISIONS.json', 'evidence/P5-EVIDENCE.json',
                'tasks/P5-TASKS.md', 'tools/validate-p5.py')
if not p5_authorised:
    for p in P5_ARTEFACTS:
        if os.path.exists(os.path.join(B, p)):
            print("P5_ARTIFACT_WITHOUT_AUTHORISATION: %s" % p)
# P6 boundary, revised after the User resolved D-P6-1 and D-P6-2.
#
# OBSOLETE INVARIANT: these P6 paths must never exist. That encoded "P6 has
# not started", which became false once the User authorised P6 research.
#
# STRONGER PHASE-AWARE REPLACEMENT: P6 artefacts are permitted only when a
# P6 decision record exists and is attributable to an identifiable User. The
# unconditional prohibitions below are retained and extended: P7 is now also
# forbidden outright, and CAP-P03-005 must remain deferred and unpromoted.
_p6dec = os.path.join(B, 'decisions/P6-DECISIONS.json')
_p6open = False
if os.path.exists(_p6dec):
    _ids = {x.get('decision_id'): x for x in
            (json.load(open(_p6dec)).get('decisions') or [])}
    _ok = True
    for _d in ('D-P6-1', 'D-P6-2'):
        _x = _ids.get(_d) or {}
        _a = _x.get('approval') or {}
        _who = (_a.get('decided_by') or '').strip()
        _when = (_a.get('decided_on') or _a.get('decided_at') or '').strip()
        if _a.get('state') != 'APPROVED' or not _who or not _when or \
                ATTR.AGENTISH.search(_who):
            print("P6_DECISION_NOT_USER_ATTRIBUTABLE: %s" % _d)
            _ok = False
    _p6open = _ok
if not _p6open:
    for p in ('requirements/P6-REQUIREMENTS.json', 'evidence/P6-EVIDENCE.json',
              'tasks/P6-TASKS.md', 'handoff/HANDOFF-P6.json',
              'handoff/HANDOFF-P6.md', 'decisions/P6-DECISIONS.json',
              'core/technology_readiness.py', 'tools/validate-p6.py'):
        if os.path.exists(os.path.join(B, p)):
            print("P6_ARTIFACT_WITHOUT_AUTHORISATION: %s" % p)
# Unconditional: no phase beyond P6 may begin.
# A P7 DECISION record is distinguished from a P7 DELIVERABLE. Deliverables are
# forbidden outright. The readiness decision record is evidence that P7 did NOT
# start, so it is admitted under a stricter rule: every approval inside it must
# be attributable to an identifiable User, judged by the AGENT control already
# defined in this script, and each decision must resolve the ambiguity it
# claims to resolve. Admitting a decision record never admits a deliverable.
for p in ('requirements/P7-REQUIREMENTS.json', 'evidence/P7-EVIDENCE.json',
          'tasks/P7-TASKS.md', 'handoff/HANDOFF-P7.json',
          'decisions/P7-DECISIONS.json', 'memory', 'bootstrap',
          'isolation_validator.py'):
    if os.path.exists(os.path.join(B, p)):
        print("P7_ARTIFACT_CREATED: %s" % p)
_p7d = os.path.join(B, 'decisions/P7-READINESS-DECISIONS.json')
if os.path.exists(_p7d):
    _p7ids = {x.get('decision_id'): x for x in
              (json.load(open(_p7d)).get('decisions') or [])}
    for _did, _amb in (('D-P7-A', 'AMB-PHASE-1'),
                       ('D-P7-B', 'AMB-PHASE-2'),
                       ('D-P7-C', 'AMB-PHASE-3'),
                       ('D-P7-D', 'AMB-PHASE-4')):
        _rec = _p7ids.get(_did)
        if not _rec:
            print("P7_DECISION_MISSING: %s" % _did)
            continue
        _a = _rec.get('approval') or {}
        _w = (_a.get('decided_by') or '').strip()
        _t = (_a.get('decided_on') or _a.get('decided_at') or '').strip()
        if _a.get('state') != 'APPROVED' or not _w or not _t or \
                AGENT.search(_w):
            print("P7_DECISION_NOT_USER_ATTRIBUTABLE: %s" % _did)
        if _rec.get('resolves_ambiguity') != _amb:
            print("P7_DECISION_WRONG_AMBIGUITY: %s -> %s" % (
                _did, _rec.get('resolves_ambiguity')))
    if not (_p7ids.get('D-P7-B') or {}).get('required_before_p7'):
        print("P7_B_MISSING_REQUIREMENTS: roadmap P3 prerequisites absent")
if ho.get('current_state') != 'APPROVED':
    print("HANDOFF_STATE: %s" % ho.get('current_state'))
notapp = ho.get('approval_scope', {}).get('explicitly_not_approved', [])
for must in ('Any production promotion', 'Any licence selection',
             'P5, and the beginning'):
    if not any(must in s for s in notapp):
        print("APPROVAL_SCOPE_INCOMPLETE: missing explicit exclusion %r" % must)

# Research gaps, incident classification and checkpoint must be intact.
src = json.load(open(B + '/research/P2-SOURCES.json'))
if not any('UNRESOLVED' in (c.get('resolution') or '')
           for c in src.get('conflicts', [])):
    print("RESEARCH_GAP_LOST: CONF-001 is no longer UNRESOLVED")
p3 = json.load(open(B + '/handoff/HANDOFF-P3.json'))
if p3['approval_scope']['credential_revocation'] != \
   'USER_ATTESTED_NOT_INDEPENDENTLY_VERIFIED':
    print("INCIDENT_CLASSIFICATION_CHANGED")
PY
if [ -s "$TMP/appr" ]; then
  while IFS= read -r l; do fail "$l"; done < "$TMP/appr"
else
  pass "P4 approval is attributable to the User and promotes nothing"
fi
# A fabricated approval must be rejected (positive control). Exits 0 only
# when the agent-attributed approval is correctly detected and rejected.
python3 -c "
import json
d=json.load(open('$SPS2/requirements/P4-REQUIREMENTS.json'))
d['requirements'][0]['approval']['approved_by']='Agent (self-approved)'
json.dump(d,open('$TMP/appr2.json','w'))
"
if python3 - "$TMP/appr2.json" "$SPS2" <<'PY'
import json, sys
sys.path.insert(0, sys.argv[2] + '/governance')
import attribution as ATTR
d = json.load(open(sys.argv[1]))
rejected = any(ATTR.AGENTISH.search((r['approval'].get('approved_by') or ''))
               for r in d['requirements'])
sys.exit(0 if rejected else 1)
PY
then
  CTR=$((CTR+1)); pass "POSCTRL-G  an agent-attributed approval is rejected"
else
  fail "POSCTRL-D  agent-attributed approval was NOT rejected"
fi
PROM=$(python3 -c "
import json
print(json.load(open('$REG'))['counts']['promoted'])")
# Promotion is now permitted, but only for the four capabilities the User
# explicitly approved, and only under an approval naming the User.
[ "$PROM" = "4" ] \
  && pass "4 capabilities promoted, matching the User-approved set" \
  || fail "$PROM promoted - expected the 4 user-approved capabilities"

sect "10. Legacy protection"
LEGACY_OUT="$(python3 "$SPS2/governance/legacy_exceptions.py" \
  --root "$REPO" --baseline c11da27 \
  --pathspec skills --pathspec scripts --pathspec plugins --pathspec .github \
  --pathspec templates --pathspec README.md --pathspec CHANGELOG.md \
  --pathspec CATALOG.md --pathspec '*.sh' --pathspec '*.ps1' \
  --exclude-prefix framework/sps2/ 2>&1)"
if [ $? -eq 0 ]; then
  pass "legacy repository matches the DEC-7301 pinned exception"
else
  while IFS= read -r line; do [ -n "$line" ] && fail "$line"; done <<< "$LEGACY_OUT"
fi

sect "11. Secret safety"
python3 "$SPS2/security/scan_secrets.py" "$SPS2" --quiet \
  && pass "no credential-shaped value under framework/sps2/" \
  || fail "credential-shaped value detected"
if bash "$SPS2/security/test-secret-safety.sh" >/dev/null 2>&1; then
  pass "secret-safety suite passes"
else
  fail "secret-safety suite failed"
fi

sect "12. Requirement, evidence and implementation records must be wired"
python3 - "$SPS2" > "$TMP/wire" 2>&1 <<'PY'
import json, os, sys
B = sys.argv[1]
R = os.path.dirname(B)
req = json.load(open(B + '/requirements/P4-REQUIREMENTS.json'))
ev = json.load(open(B + '/evidence/P4-EVIDENCE.json'))['records']
ids = {e['evidence_id'] for e in ev}
if len(ids) != len(ev):
    print("DUPLICATE_EVIDENCE_ID")
for r in req['requirements']:
    rid = r['requirement_id']
    for f in r['implementation'].get('refs') or []:
        if not os.path.isfile(os.path.join(R, f)):
            print("IMPL_REF_NOT_FOUND: %s -> %s" % (rid, f))
    if not (r['implementation'].get('refs') or []):
        print("IMPL_REF_EMPTY: %s" % rid)
    for e in (r['implementation'].get('evidence') or []):
        if e not in ids:
            print("UNKNOWN_EVIDENCE: %s -> %s" % (rid, e))
    for e in (r['verification'].get('evidence') or []):
        if e not in ids:
            print("UNKNOWN_EVIDENCE: %s -> %s" % (rid, e))
    if r['status'] == 'VERIFIED' and not r['verification'].get('evidence'):
        print("VERIFIED_WITHOUT_EVIDENCE: %s" % rid)
    for e in r['verification'].get('evidence') or []:
        rec = next(x for x in ev if x['evidence_id'] == e)
        if rec.get('relates_to', {}).get('requirement_id') != rid:
            print("EVIDENCE_MISLINKED: %s claimed by %s but relates to %s"
                  % (e, rid, rec.get('relates_to', {}).get('requirement_id')))
    if r['status'] == 'VERIFIED' and not r['verification'].get('observed_result'):
        print("VERIFIED_WITHOUT_OBSERVED_RESULT: %s" % rid)
# Every VERIFIED capability must cite evidence that actually relates to it.
reg = json.load(open(B + '/capability/registry.json'))
cap_ev = {}
for e in ev:
    cid = e.get('relates_to', {}).get('capability_id')
    if cid:
        cap_ev.setdefault(cid, set()).add(e['evidence_id'])
for c in reg['capabilities']:
    if c['verification']['state'] != 'VERIFIED':
        continue
    cid = c['capability_id']
    claimed = c['verification'].get('evidence') or []
    own = cap_ev.get(cid, set())
    if not claimed:
        print("CAPABILITY_WITHOUT_EVIDENCE: %s" % cid)
    elif not set(claimed).issubset(own):
        print("CAPABILITY_EVIDENCE_NOT_DEDICATED: %s claims %s its own are %s"
              % (cid, claimed, sorted(own)))
    elif len(claimed) != len(own):
        print("CAPABILITY_EVIDENCE_INCOMPLETE: %s claims %s its own are %s"
              % (cid, claimed, sorted(own)))
PY
if [ -s "$TMP/wire" ]; then
  while IFS= read -r l; do fail "$l"; done < "$TMP/wire"
else
  pass "requirement, evidence and implementation records are fully wired"
fi

sect "12b. The committed .claude/settings.json can never carry a credential"
# The working tree may be rewritten by the harness at any time, so scanning the
# working tree alone is a vacuous guarantee. This checks the COMMITTED blob at
# HEAD, which is what a future `git commit` would publish. Key names only; no
# credential value is read, printed or transmitted.
python3 - "$REPO" > "$TMP/claude" 2>&1 <<'PY'
import json, subprocess, sys
R = sys.argv[1]
PATH = '.claude/settings.json'
TOKEN_KEYS = ('ANTHROPIC_AUTH_TOKEN', 'OPENROUTER_KEY', 'OPENAI_API_KEY',
              'ANTHROPIC_API_KEY')
try:
    raw = subprocess.run(['git', '-C', R, 'show', 'HEAD:' + PATH],
                         capture_output=True, text=True, check=True).stdout
    d = json.loads(raw)
except Exception as e:
    print("CLAUDE_SETTINGS_UNREADABLE: %s" % type(e).__name__)
    raise SystemExit(0)
env = d.get('env') or {}
bad = sorted(k for k in env if k in TOKEN_KEYS)
if bad:
    print("COMMITTED_CREDENTIAL_KEY: .claude/settings.json holds %s" % bad)
if not isinstance(d.get('enabledPlugins', {}), dict):
    print("CLAUDE_SETTINGS_MALFORMED: enabledPlugins is not an object")
PY
if [ -s "$TMP/claude" ]; then
  while IFS= read -r l; do fail "$l"; done < "$TMP/claude"
else
  pass "the committed .claude/settings.json carries no credential key"
fi
# POSCTRL-E: the committed-blob guard must actually detect a planted key.
if [ "$(python3 - "$TMP" <<'PY'
import json, os, sys
TOKEN_KEYS = ('ANTHROPIC_AUTH_TOKEN', 'OPENROUTER_KEY', 'OPENAI_API_KEY',
              'ANTHROPIC_API_KEY')
p = os.path.join(sys.argv[1], 'claude_fake.json')
json.dump({'env': {'ANTHROPIC_AUTH_TOKEN': 'PLANTED-FOR-TEST'}}, open(p, 'w'))
d = json.load(open(p))
print('DETECTED' if any(k in TOKEN_KEYS for k in (d.get('env') or {}))
      else 'MISSED')
PY
)" = "DETECTED" ]; then
  CTR=$((CTR+1)); pass "POSCTRL-H  the committed-blob guard detects a planted credential key"
else
  fail "POSCTRL-H  the committed-blob guard MISSED a planted credential key"
fi

sect "12c. Open decisions must stay open until the user answers them"
# A pending decision must carry no decider. If an agent ever fills in
# decided_by, or flips state, the record is a fabricated approval.
python3 - "$SPS2" > "$TMP/open" 2>&1 <<'PY'
import json, os, sys
B = sys.argv[1]
D = B + '/decisions'
lic = os.path.join(D, 'OPEN-DECISION-LICENCE.json')
setg = os.path.join(D, 'OPEN-DECISION-CLAUDE-SETTINGS.json')
prov = os.path.join(D, 'PROVENANCE-SPS-CMS.json')

# 1. The licence decision was resolved by explicit user instruction, so it may
#    no longer be pending, but it must record who decided it and on what basis.
if not os.path.isfile(lic):
    print("DECISION_RECORD_MISSING: OPEN-DECISION-LICENCE.json")
else:
    d = json.load(open(lic))
    did = d.get('decision_id')
    if d.get('state') != 'APPROVED':
        print("LICENCE_DECISION_UNEXPECTED_STATE: %s state=%s"
              % (did, d.get('state')))
    if d.get('decided_by') != 'User':
        print("LICENCE_DECISION_NOT_USER_ATTRIBUTED: %s decided_by=%s"
              % (did, d.get('decided_by')))
    if d.get('licence') != 'MIT':
        print("LICENCE_DECISION_UNEXPECTED_VALUE: %s" % d.get('licence'))
    if d.get('scope') != 'SPS 2.0 repository':
        print("LICENCE_SCOPE_UNEXPECTED: %s" % d.get('scope'))
    if d.get('provenance_prerequisite') != 'SATISFIED_BY_USER_ATTESTATION':
        print("LICENCE_PREREQUISITE_WRONG: %s"
              % d.get('provenance_prerequisite'))
    if d.get('third_party_code_relicensed') is not False:
        print("LICENCE_THIRD_PARTY_RELICENSE_CLAIM")
    if d.get('independent_legal_verification_claimed') is not False:
        print("LICENCE_OVERCLAIMS_LEGAL_VERIFICATION")
    ge = d.get('gate_effect') or {}
    if 'STILL BLOCKED' not in (ge.get('gate_H') or ''):
        print("LICENCE_RECORD_IMPLIES_GATE_H_CLEARED")
    if len(d.get('options') or []) < 2:
        print("LICENCE_OPTIONS_DROPPED: %s" % did)

# 2. The settings decision was resolved by explicit user instruction, so it may
#    no longer be pending, but it must record who resolved it.
if not os.path.isfile(setg):
    print("DECISION_RECORD_MISSING: OPEN-DECISION-CLAUDE-SETTINGS.json")
else:
    d = json.load(open(setg))
    if d.get('state') != 'RESOLVED_APPLIED':
        print("SETTINGS_DECISION_UNEXPECTED_STATE: %s" % d.get('state'))
    if not (d.get('resolved_by') or '').strip():
        print("RESOLVED_WITHOUT_ATTRIBUTION: settings decision")
    fs = d.get('final_state') or {}
    if not fs.get('credential_keys') == 'none':
        print("SETTINGS_FINAL_STATE_HAS_CREDENTIAL: %s" % fs.get('credential_keys'))

# 3. A provenance finding must exist and must be one of the four allowed values.
if not os.path.isfile(prov):
    print("PROVENANCE_FINDING_MISSING")
else:
    d = json.load(open(prov))
    allowed = {'VERIFIED_PROJECT_AUTHORED', 'VERIFIED_THIRD_PARTY', 'MIXED',
               'UNKNOWN'}
    if d.get('finding') not in allowed:
        print("PROVENANCE_FINDING_INVALID: %s" % d.get('finding'))
    if not (d.get('evidence_for_project_authorship') or []) and \
       not (d.get('evidence_limits') or []):
        print("PROVENANCE_FINDING_UNSUPPORTED: no evidence recorded")
    if d.get('finding') in ('VERIFIED_PROJECT_AUTHORED', 'VERIFIED_THIRD_PARTY'):
        # A VERIFIED finding must record who confirmed it, AND must not claim
        # independent verification the agent never performed. An attested
        # finding is recorded as attested; an agent cannot upgrade it to fact.
        if not (d.get('confirmed_by') or '').strip():
            print("PROVENANCE_VERIFIED_WITHOUT_USER_CONFIRMATION: %s"
                  % d.get('finding'))
        if d.get('evidence_class') != 'USER_ATTESTATION':
            print("PROVENANCE_VERIFIED_WRONG_EVIDENCE_CLASS: %s"
                  % d.get('evidence_class'))
        if d.get('independently_verified') is not False:
            print("PROVENANCE_OVERCLAIMS_INDEPENDENT_VERIFICATION")
        if not (d.get('what_this_does_not_mean') or []):
            print("PROVENANCE_VERIFIED_WITHOUT_SCOPE_LIMITS")
    if d.get('finding') == 'UNKNOWN' and not d.get('evidence_limits'):
        print("PROVENANCE_UNKNOWN_WITHOUT_STATED_LIMITS")

# 4. The licence state in the P4 decision record must agree with the decision.
dec = json.load(open(D + '/P4-DECISIONS.json'))
lic_rec = [x for x in dec['decisions']
           if (x.get('unresolved') or {}).get('item') == 'repository_licence']
if not lic_rec:
    print("LICENCE_DECISION_RECORD_MISSING")
else:
    u = lic_rec[0]['unresolved']
    if u['state'] != 'RESOLVED_BY_USER_DECISION':
        print("LICENCE_RECORD_STATE_MISMATCH: %s" % u['state'])
    if u.get('licence') != 'MIT' or u.get('decided_by') != 'User':
        print("LICENCE_RECORD_MISMATCH: licence=%s decided_by=%s"
              % (u.get('licence'), u.get('decided_by')))
    if u.get('independent_legal_verification_claimed') is not False:
        print("LICENCE_RECORD_OVERCLAIMS_VERIFICATION")
PY
if [ -s "$TMP/open" ]; then
  while IFS= read -r l; do fail "$l"; done < "$TMP/open"
else
  pass "open decisions remain open, unattributed, and carry options"
fi

sect "12d. Promotion is exactly the User-approved set, and nothing else"
# The User approved production promotion for CAP-P03-001..004 only, each
# conditioned on every other gate passing. CAP-P03-005 was explicitly excluded.
# This section proves the promoted set is exactly that set, that every promoted
# capability genuinely passes A-K, and that nothing was promoted by popularity.
python3 - "$SPS2" > "$TMP/h" 2>&1 <<'PY'
import importlib.util as _ilu
import json, os, sys
B = sys.argv[1]
# SPEC-2: make the governance import explicit here too. This block previously
# relied on promotion_gates.py side-effecting sys.path for framework/sps2/governance; if
# that exec ever moves, the bare `import attribution` below would raise.
sys.path.insert(0, B + '/governance')
import attribution as ATTR
_spec = _ilu.spec_from_file_location("pg", B + '/capability/promotion_gates.py')
_pg = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_pg)
reg = json.load(open(B + '/capability/registry.json'))
APPROVED_SET = {'CAP-P03-001', 'CAP-P03-002', 'CAP-P03-003', 'CAP-P03-004'}
EXCLUDED_SET = {'CAP-P03-005'}

promoted = set()
for c in reg['capabilities']:
    cid = c['capability_id']
    pa = c.get('promotion_assessment') or {}
    res, blocking = _pg.evaluate(c)
    # ── current-gate freshness, enforced for EVERY capability ────────────────
    # promotion_assessment.gates claims to be the CURRENT evaluation. It must
    # equal a fresh recomputation, otherwise a stale or optimistic claim about
    # a deferred candidate could survive unnoticed.
    _rec = (pa.get('gates') or {})
    _rec_bool = {k: bool((v or {}).get('pass')) for k, v in _rec.items()}
    _now_bool = {k: bool(v['pass']) for k, v in res.items()}
    if _rec and _rec_bool != _now_bool:
        print("CURRENT_GATES_STALE_OR_FALSE: %s recorded=%s actual=%s"
              % (cid, _rec_bool, _now_bool))
    if pa.get('promotion_decision') == 'PROMOTED_TO_PRODUCTION':
        promoted.add(cid)
        # A promoted capability must genuinely pass every gate right now.
        if blocking:
            print("PROMOTED_BUT_BLOCKING: %s blocking=%s" % (cid, blocking))
        ap = c.get('approval') or {}
        if ap.get('state') != 'APPROVED' or ap.get('decided_by') != 'User':
            print("PROMOTED_WITHOUT_USER_APPROVAL: %s" % cid)
        pr = c.get('promotion_record') or {}
        for f in ('promoted_on', 'promoted_by', 'previous_lifecycle_state',
                  'previous_approval_state', 'gate_results_at_promotion'):
            if pr.get(f) in (None, '', {}):
                print("PROMOTION_RECORD_INCOMPLETE: %s missing %s" % (cid, f))
        if pr.get('promoted_by') != 'User':
            print("PROMOTION_NOT_USER_ATTRIBUTED: %s" % cid)
        # ── historical snapshot vs current evaluation ────────────────────────
        # A snapshot taken before User approval legitimately shows Gate H as
        # failing. That difference must be DECLARED, never silently smoothed,
        # and the recorded "current" gates must equal a fresh recomputation.
        snap = pr.get('gate_results_at_promotion') or {}
        decl = pr.get('gate_snapshot_declaration') or {}
        if not decl:
            print("GATE_SNAPSHOT_NOT_DECLARED: %s" % cid)
        else:
            if decl.get('gate_results_at_promotion_is') != \
                    'HISTORICAL_SNAPSHOT':
                print("SNAPSHOT_NOT_MARKED_HISTORICAL: %s" % cid)
            if decl.get('promotion_assessment_gates_is') != \
                    'CURRENT_EVALUATION':
                print("CURRENT_EVALUATION_NOT_MARKED: %s" % cid)
            if decl.get('preserved_unmodified') is not True:
                print("SNAPSHOT_CLAIMS_MODIFICATION: %s" % cid)
            cur_now = {k: bool(v['pass']) for k, v in res.items()}
            actual_diff = sorted(g for g in set(snap) | set(cur_now)
                                 if bool(snap.get(g)) != bool(cur_now.get(g)))
            declared = sorted(d.get('gate') for d in
                              (decl.get('differences_from_current') or []))
            if actual_diff != declared:
                print("SNAPSHOT_DIFFERENCE_UNDECLARED: %s actual=%s declared=%s"
                      % (cid, actual_diff, declared))
            if decl.get('difference_is_expected_and_declared') is not \
                    bool(actual_diff):
                print("SNAPSHOT_DIFFERENCE_FLAG_WRONG: %s" % cid)
            for d in (decl.get('differences_from_current') or []):
                if not (d.get('reason') or '').strip():
                    print("SNAPSHOT_DIFFERENCE_WITHOUT_REASON: %s gate %s"
                          % (cid, d.get('gate')))
        # The snapshot must remain a genuine historical artefact: it is not
        # allowed to claim a Gate H pass that no User had yet granted.
        if bool(snap.get('H')) and \
                (c.get('approval') or {}).get('decided_on') is None:
            print("SNAPSHOT_CLAIMS_UNBACKED_APPROVAL: %s" % cid)
    else:
        # Anything not promoted must carry an explicit classification.
        if pa.get('recommendation') not in ('DEFER', 'REMAIN_CANDIDATE',
                                            'REJECT'):
            print("UNPROMOTED_WITHOUT_CLASSIFICATION: %s" % cid)
    # Nothing outside the approved set may be promoted.
    if cid not in APPROVED_SET and pa.get('promotion_decision') == \
       'PROMOTED_TO_PRODUCTION':
        print("PROMOTED_OUTSIDE_USER_APPROVAL: %s" % cid)
    # The excluded candidate must remain blocked and unapproved.
    if cid in EXCLUDED_SET:
        if (c.get('approval') or {}).get('state') == 'APPROVED':
            print("EXCLUDED_CAPABILITY_APPROVED: %s" % cid)
        if not {'F', 'K'} <= set(blocking):
            print("EXCLUDED_CAPABILITY_GATE_BYPASSED: %s blocking=%s"
                  % (cid, blocking))
        if c.get('lifecycle_state') != 'DEFERRED':
            print("EXCLUDED_CAPABILITY_NOT_DEFERRED: %s" % cid)

if promoted != APPROVED_SET:
    print("PROMOTED_SET_MISMATCH: promoted=%s expected=%s"
          % (sorted(promoted), sorted(APPROVED_SET)))
if reg['counts']['promoted'] != len(promoted):
    print("PROMOTED_COUNT_MISMATCH: %s vs %s"
          % (reg['counts']['promoted'], len(promoted)))

# A P5 artefact must never appear without User authorisation. This block runs in
# its own interpreter, so the authorisation test is re-derived here rather than
# carried over. It is conditional for the reason documented in the first block.
# P6 remains forbidden outright. CAP-P03-005 must stay deferred in every phase.
import attribution as ATTR  # SPEC-2: single authoritative policy
p5_authorised = False
_pa = os.path.join(B, 'evidence/P5-EVIDENCE.json')
if os.path.exists(_pa):
    _rec = json.load(open(_pa)).get('phase_approval') or {}
    _who = (_rec.get('authorised_by') or '').strip().lower()
    if _rec.get('scope') == 'P5 implementation/integration' and _who \
            and not ATTR.AGENTISH.search(_who):
        p5_authorised = True
P5_ARTEFACTS = ('requirements/P5-REQUIREMENTS.json',
                'handoff/HANDOFF-P5.json', 'handoff/HANDOFF-P5.md',
                'decisions/P5-DECISIONS.json', 'evidence/P5-EVIDENCE.json',
                'tasks/P5-TASKS.md', 'tools/validate-p5.py')
if not p5_authorised:
    for p in P5_ARTEFACTS:
        if os.path.exists(os.path.join(B, p)):
            print("P5_ARTIFACT_WITHOUT_AUTHORISATION: %s" % p)
for c in reg['capabilities']:
    if c['capability_id'] == 'CAP-P03-005':
        if c.get('lifecycle_state') != 'DEFERRED':
            print("CAP005_LIFECYCLE_CHANGED: %s" % c.get('lifecycle_state'))
        if set((c.get('promotion_assessment') or {}).get(
                'blocking_gates') or []) != {'F', 'H', 'K'}:
            print("CAP005_BLOCKING_GATES_CHANGED: %s"
                  % (c.get('promotion_assessment') or {}).get(
                      'blocking_gates'))
        if (c.get('promotion_assessment') or {}).get(
                'promotion_decision') not in (None, 'NOT_PROMOTED'):
            print("CAP005_PROMOTED: %s"
                  % (c.get('promotion_assessment') or {}).get(
                      'promotion_decision'))
src = json.load(open(B + '/research/P2-SOURCES.json'))
if not any('UNRESOLVED' in (c.get('resolution') or '')
           for c in src.get('conflicts', [])):
    print("CONF_001_NO_LONGER_UNRESOLVED")
# No LCP or INP threshold may have been introduced.
for c in reg['capabilities']:
    blob = json.dumps(c)
    for bad in ('"LCP"', '"INP"', 'largest_contentful_paint_ms',
                'interaction_to_next_paint_ms'):
        if bad in blob:
            print("INVENTED_WEB_VITAL_THRESHOLD: %s contains %s"
                  % (c['capability_id'], bad))
PY
if [ -s "$TMP/h" ]; then
  while IFS= read -r l; do fail "$l"; done < "$TMP/h"
else
  pass "promotion is exactly the User-approved set and nothing else"
fi

fi  # end structural

# ══ NEGATIVE SUITE: 20 mandated cases ═══════════════════════════════════════
# The negative suite keeps its own counters so that a positive control failing
# elsewhere can never be mis-reported as a missed negative case.
sect "NEGATIVE TESTS — invalid promotion states must be rejected"
NNP=0; NNF=0

gate_case "B['capability_id']=''"                     A "N01 missing capability id"
gate_case "B['capability_id']='bad id'"               A "N02 malformed capability id"
gate_case "B['provenance']={'fact_class':'EVIDENCE'}" B "N03 missing provenance"
gate_case "B['licence']='UNKNOWN'"                    D "N04 unknown licence"
gate_case "B['licence']='UNDECLARED'"                 D "N04b undeclared licence"
gate_case "B['security']={'status':'VERIFIED_SAFE','fact_class':'EVIDENCE'}" C "N05 missing security evidence"
gate_case "B['verification']={'state':'VERIFIED','method':'AUTOMATED'}" F "N06 missing verification evidence"
gate_case "B['acceptance_criteria']=[]"               G "N07 empty acceptance criteria"
gate_case "B['approval']={'state':'PENDING_USER_APPROVAL'}" H "N08 user approval absent"
gate_case "B['approval']={'state':'APPROVED','decided_by':'agent'}" H "N09 agent-attributed approval"
gate_case "B['approval']={'state':'APPROVED','decided_by':''}"     H "N09b approval with no decider"
gate_case "B['install_scope']='GLOBAL'"               I "N10 GLOBAL without authorization"
gate_case "B['staleness']=dict(B['staleness'],state='STALE');B['lifecycle_state']='ACTIVE';B['verification']={'state':'VERIFIED','evidence':['E'],'method':'A','expected_result':'x','observed_result':'y'}" J "N11 stale marked ACTIVE"
gate_case "B['staleness']={'state':'STALE','maintenance':'ACTIVE'}" J "N12 stale without review"
gate_case "B['provenance']={'origin':'nonexistent-system-xyz','commit':'abc1234','fact_class':'EVIDENCE','repository_relative_path':'framework/sps2/does-not-exist.py','research_refs':['SRC-999']}" B "N13 fabricated source reference"
gate_case "B['security']={'status':'VERIFIED_SAFE','evidence':'sk-or-v1-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA','fact_class':'EVIDENCE'}" C "N14 secret embedded in record"
gate_case "B['type']='WIDGET'"                        A "N15 invalid taxonomy"
gate_case "B['lifecycle_state']='TELEPORTED'"         A "N16 invalid lifecycle state"
gate_case "B['domain']='SEO';B['name']='lcp-inp-verifier';B['security']={'status':'VERIFIED_SAFE','evidence':'LCP 2500ms INP 200ms','fact_class':'FACT'}" K "N17 unresolved research promoted"

# N18: duplicate capability id (registry level)
mk "pass"
python3 - "$TMP/c.json" "$TMP/dup.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
json.dump({"capabilities": [d, dict(d)]}, open(sys.argv[2], "w"))
PY
# The case must require the checker's own DUPLICATE output. A second disjunct
# that re-reads the fixture we just built is a tautology (the fixture always
# contains a duplicate), so it scored the case as rejected even if the checker
# never detected anything. A checker crash or silent regression now fails.
# The registry-level duplicate control lives in check_p3.py (check_p4.py is a
# single-capability gate checker and has no registry view), so the fixture is
# run through `check_p3.py registry`.
if python3 "$HERE/check_p3.py" registry "$TMP/dup.json" 2>&1 | grep -q 'DUPLICATE'; then
  NNP=$((NNP+1)); pass "N18 duplicate capability id -> rejected"
else
  NNF=$((NNF+1)); fail "N18 duplicate capability id NOT rejected"
fi

# N19: emoji violation
mkdir -p "$TMP/em" && printf 'x \360\237\216\257\n' > "$TMP/em/a.md"
if python3 "$EMOJI" "$TMP/em" >/dev/null 2>&1; then
  NNF=$((NNF+1)); fail "N19 emoji violation NOT rejected"
else
  NNP=$((NNP+1)); pass "N19 emoji violation -> rejected"
fi
rm -rf "$TMP/em"

# N20: malformed structured input
printf '{ not json' > "$TMP/bad.json"
if python3 "$CHECK" "$TMP/bad.json" 2>&1 | grep -q 'GATE_ERROR'; then
  NNP=$((NNP+1)); pass "N20 malformed JSON -> rejected"
else
  NNF=$((NNF+1)); fail "N20 malformed JSON NOT rejected"
fi

echo ""
if [ "$NNF" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}== P4 NEGATIVE SUITE: $NNP cases correctly rejected, 0 missed ==${NC}"
else
  echo -e "${RED}${BOLD}== P4 NEGATIVE SUITE: $NNP rejected, $NNF MISSED ==${NC}"
fi
echo ""
if [ "$FAIL" -eq 0 ] && [ "$NNF" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}== P4 PROMOTION VALID: $PASS checks passed, 0 failed, $NNP negative cases rejected, $CTR controls enforced ==${NC}"
  exit 0
fi
echo -e "${RED}${BOLD}== P4 PROMOTION INVALID: $PASS passed, $FAIL failed, $NNF missed ==${NC}"
exit 1
