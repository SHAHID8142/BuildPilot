#!/usr/bin/env bash
# SPS 2.0 P3 production capability validator.
# Tests ACTUAL structured behaviour: promotion gate, deterministic ranking,
# forced choice, staleness, provenance, approval attribution, project locality.
# SAFETY: no network, no installs, no machine-global writes, never modifies a
# real file. Negative fixtures live only in a self-managed temp dir.
# Usage: bash framework/sps2/tools/validate-p3.sh [--negative]
# Exit:  0 valid | 1 failure | 2 tooling unavailable

set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPS2="$(cd "$HERE/.." && pwd)"
REPO="$(cd "$SPS2/.." && pwd)"
CHECK="$HERE/check_p3.py"
ENGINE="$SPS2/capability/engine.py"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'
BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'
PASS=0; FAIL=0; NEG_PASS=0; NEG_FAIL=0
pass() { echo -e "  ${GREEN}PASS${NC}  $*"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}FAIL${NC}  $*"; FAIL=$((FAIL+1)); }
info() { echo -e "  ${BLUE}CASE${NC} $*"; }
warn() { echo -e "  ${YELLOW}WARN${NC}  $*"; }
sect() { echo -e "\n${BOLD}$*${NC}"; }

command -v python3 >/dev/null 2>&1 || { echo "python3 unavailable"; exit 2; }
TMP="$(mktemp -d "${TMPDIR:-/tmp}/sps2p3-XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

NEG_ONLY=false
for a in "$@"; do [ "$a" = "--negative" ] && NEG_ONLY=true; done

echo -e "${BOLD}SPS 2.0 P3 Production Capability Validator${NC}"
echo -e "${DIM}behavioural validation of gate, ranking, staleness and provenance${NC}"

# shared fixture generator (written only to the temp dir)
cat > "$TMP/mk.py" <<'FIXT'
import json, sys
d = {
  "capability_id": "CAP-SPS-900", "name": "fixture", "type": "DEV_TOOL",
  "domain": "governance", "purpose": "A valid fixture purpose for tests",
  "version": "1.0.0", "source": "SPS2_CORE", "licence": "KNOWN_PERMISSIVE",
  "licence_evidence": "fixture", "origin": "SPS_CORE",
  "provenance": {"origin": "fixture", "commit": "abc1234",
                 "fact_class": "FACT", "captured_at": "2026-10-03"},
  "security": {"status": "VERIFIED_SAFE", "evidence": "fixture",
               "fact_class": "EVIDENCE"},
  "compatibility": {"status": "COMPATIBLE", "agent_neutral": True,
                    "basis": "fixture"},
  "staleness": {"state": "CURRENT", "maintenance": "ACTIVE",
                "last_checked": "2026-10-03", "review_due": "2027-01-01"},
  "install_scope": "PROJECT_LOCAL", "evidence": ["EV-P3-001"],
  "confidence": "HIGH", "lifecycle_state": "CANDIDATE",
  "approval": {"state": "PENDING_USER_APPROVAL"},
  "verification": {"state": "UNVERIFIED", "evidence": []},
  "selection_policy": {"popularity_role": "TIE_BREAKER_ONLY"},
}
exec(sys.argv[1])
print(json.dumps(d))
FIXT

mk() { python3 "$TMP/mk.py" "$1" > "$TMP/f.json"; }

gate() {  # mutation expect-regex label
  mk "$1"
  local out; out="$(python3 "$CHECK" gate "$TMP/f.json" 2>&1)"
  if printf '%s\n' "$out" | grep -q 'REJECTED' \
     && printf '%s\n' "$out" | grep -qiE -- "$2"; then
    info "REJECTED -> $3"; NEG_PASS=$((NEG_PASS+1)); pass "$3 -> rejected"
  else
    info "NOT REJECTED (validator defect!) -> $3"
    NEG_FAIL=$((NEG_FAIL+1)); fail "$3 -> NOT rejected (out: ${out:-none})"
  fi
}

if [ "$NEG_ONLY" != true ]; then

sect "1. P3 deliverables present"
for f in capability/engine.py capability/registry.json \
         project/SELECTION-P3-0001.json tools/check_p3.py \
         requirements/P3-REQUIREMENTS.json evidence/P3-EVIDENCE.json \
         decisions/P3-DECISIONS.json tasks/P3-TASKS.md \
         handoff/HANDOFF-P3.json; do
  [ -f "$SPS2/$f" ] && pass "present $f" || fail "missing $f"
done
[ -f "$REPO/AUDIT-PHASE-07-P3-PRODUCTION-CAPABILITY.md" ] \
  && pass "present AUDIT-PHASE-07 report" || fail "missing AUDIT-PHASE-07 report"

sect "2. Production registry and selection record validate"
OUT=$(python3 "$CHECK" registry "$SPS2/capability/registry.json" 2>&1); RC=$?
if [ "$RC" -ne 0 ]; then
  fail "registry: checker exited $RC - control could not run"
elif [ -z "$OUT" ]; then
  pass "registry passes promotion gate and integrity checks"
else
  while IFS= read -r l; do [ -n "$l" ] && fail "registry: $l"; done <<< "$OUT"
fi
OUT=$(python3 "$CHECK" selection "$SPS2/capability/registry.json" \
      "$SPS2/project/SELECTION-P3-0001.json" 2>&1); RC=$?
if [ "$RC" -ne 0 ]; then
  fail "selection: checker exited $RC - control could not run"
elif [ -z "$OUT" ]; then
  pass "selection record is traceable and explained"
else
  while IFS= read -r l; do [ -n "$l" ] && fail "selection: $l"; done <<< "$OUT"
fi
for k in requirements evidence decisions; do
  case $k in
    requirements) p="$SPS2/requirements/P3-REQUIREMENTS.json" ;;
    evidence) p="$SPS2/evidence/P3-EVIDENCE.json" ;;
    decisions) p="$SPS2/decisions/P3-DECISIONS.json" ;;
  esac
  # Fail-CLOSED: OUT is empty both when the document is clean AND when the
  # checker crashed or exited non-zero silently. Check the exit status first.
  OUT=$(python3 "$CHECK" records "$k" "$p" 2>&1); RC=$?
  if [ "$RC" -ne 0 ]; then
    fail "$k: checker exited $RC - control could not run"
  elif [ -z "$OUT" ]; then
    pass "P3 $k validate"
  else
    while IFS= read -r l; do [ -n "$l" ] && fail "$k: $l"; done <<< "$OUT"
  fi
done
OUT=$(python3 "$CHECK" records handoff "$SPS2/handoff/HANDOFF-P3.json" 2>&1); RC=$?
if [ "$RC" -ne 0 ]; then
  fail "handoff: checker exited $RC - control could not run"
elif [ -z "$OUT" ]; then
  pass "P3 handoff validates"
else
  while IFS= read -r l; do [ -n "$l" ] && fail "handoff: $l"; done <<< "$OUT"
fi

sect "3. Approval is genuine, user-attributed and bounded"
# Approval may only ever be attributed to the user, never to an agent.
jq -e '[.requirements[] | select(.approval.state == "APPROVED")
        | .approval.decided_by] | length > 0 and all(. == "User")' \
  "$SPS2/requirements/P3-REQUIREMENTS.json" >/dev/null 2>&1 \
  && pass "every approved P3 requirement is attributed to User" \
  || fail "a P3 requirement approval is not user-attributed"
jq -e '[.decisions[] | select(.approval.state == "APPROVED")
        | .approval.decided_by] | length > 0 and all(. == "User")' \
  "$SPS2/decisions/P3-DECISIONS.json" >/dev/null 2>&1 \
  && pass "every approved P3 decision is attributed to User" \
  || fail "a P3 decision approval is not user-attributed"
jq -e '.handoffs[0].user_approval == "APPROVED"
       and (.handoffs[0].current_state | test("APPROVED"))' \
  "$SPS2/handoff/HANDOFF-P3.json" >/dev/null 2>&1 \
  && pass "P3 handoff reads APPROVED" || fail "P3 handoff state is wrong"

# The approval must stay bounded: P4 is NOT approved by it.
jq -e '.approval_scope.p4 == "NOT_APPROVED"' \
  "$SPS2/handoff/HANDOFF-P3.json" >/dev/null 2>&1 \
  && pass "P4 explicitly recorded as NOT_APPROVED" || fail "P4 approval scope missing"
jq -e '.approval_scope.credential_revocation | test("USER_ATTESTED")' \
  "$SPS2/handoff/HANDOFF-P3.json" >/dev/null 2>&1 \
  && pass "revocation recorded as USER_ATTESTED, not verified" \
  || fail "revocation classification missing"
jq -e '.approval_scope.forensic_checkpoint_a7767cf | test("PRESERVED")' \
  "$SPS2/handoff/HANDOFF-P3.json" >/dev/null 2>&1 \
  && pass "forensic checkpoint a7767cf recorded as PRESERVED" \
  || fail "forensic checkpoint scope missing"

# P3 asserted every capability stayed at CANDIDATE. That was correct while no
# promotion had been approved. P4 now records an explicit User production
# approval, so the invariant becomes: a capability may advance beyond CANDIDATE
# ONLY if it carries its own attributable User approval. Unapproved candidates
# must still be at CANDIDATE.
python3 - "$SPS2" > "$TMP/lc" 2>&1 <<'PY'
import json, os, sys
B = sys.argv[1]
PROMOTED_STATES = {'EVALUATED', 'ACTIVE', 'PROMOTED', 'APPROVED', 'INSTALLED'}
reg = json.load(open(B + '/capability/registry.json'))
for c in reg['capabilities']:
    ap = c.get('approval') or {}
    user_ok = (ap.get('state') == 'APPROVED'
               and ap.get('decided_by') == 'User'
               and 'production promotion' in (ap.get('scope') or ''))
    lc = c.get('lifecycle_state')
    # Only a *promoted* lifecycle state requires User approval. CANDIDATE,
    # DEFERRED and REJECTED are legitimate classifications without approval.
    if lc in PROMOTED_STATES and not user_ok:
        print("LIFECYCLE_WITHOUT_USER_APPROVAL: %s state=%s approval=%s/%s"
              % (c['capability_id'], lc, ap.get('state'), ap.get('decided_by')))
    if user_ok and not c.get('promotion_record'):
        print("APPROVED_WITHOUT_PROMOTION_RECORD: %s" % c['capability_id'])
PY
if [ -s "$TMP/lc" ]; then
  while IFS= read -r l; do fail "$l"; done < "$TMP/lc"
else
  pass "every capability past CANDIDATE carries its own User approval"
fi
jq -e '[.capabilities[].install_scope] | all(. == "PROJECT_LOCAL")' \
  "$SPS2/capability/registry.json" >/dev/null 2>&1 \
  && pass "every capability remains PROJECT_LOCAL" \
  || fail "a capability is not project-local"

# The forensic checkpoint must still exist: approval does not authorise cleanup.
if git -C "$REPO" cat-file -t a7767cf5f761cab4aa633c1cbc7604f83e4d14f8 \
     >/dev/null 2>&1; then
  pass "forensic checkpoint a7767cf preserved (not purged)"
else
  fail "forensic checkpoint a7767cf was purged"
fi

sect "3. Promotion gate positive control"
mk "pass"
GATE_OUT="$(python3 "$CHECK" gate "$TMP/f.json" 2>&1)"
if printf '%s\n' "$GATE_OUT" | grep -q '^PROMOTED$'; then
  NEG_PASS=$((NEG_PASS+1)); pass "POSCTRL-1  a valid capability IS promoted"
else
  info "WRONGLY REJECTED (over-blocking) -> POSCTRL-1: $GATE_OUT"
  NEG_FAIL=$((NEG_FAIL+1)); fail "POSCTRL-1  valid capability was wrongly rejected"
fi

sect "4. Registry composition and project-locality"
NCAP=$(jq -r '.capabilities|length' "$SPS2/capability/registry.json")
NDEF=$(jq -r '.deferred|length' "$SPS2/capability/registry.json")
pass "registry holds $NCAP promoted capabilities and $NDEF deferred/rejected records"
jq -e '[.capabilities[].install_scope] | all(. == "PROJECT_LOCAL")' \
  "$SPS2/capability/registry.json" >/dev/null 2>&1 \
  && pass "every registered capability is PROJECT_LOCAL" \
  || fail "a registered capability is not project-local"
# An APPROVED capability is only legitimate if the User granted it. The agent
# may never mark a capability APPROVED on its own authority.
python3 - "$SPS2" > "$TMP/ap" 2>&1 <<'PY'
import json, re, sys
B = sys.argv[1]
sys.path.insert(0, B + '/governance')
import attribution as ATTR
AGENTISH = ATTR.AGENTISH  # SPEC-2: single authoritative policy
reg = json.load(open(B + '/capability/registry.json'))
for c in reg['capabilities']:
    ap = c.get('approval') or {}
    if ap.get('state') != 'APPROVED':
        continue
    who = (ap.get('decided_by') or '').strip()
    if not who:
        print("APPROVED_WITHOUT_DECIDER: %s" % c['capability_id'])
    elif AGENTISH.search(who):
        print("APPROVED_BY_AGENT: %s decided_by=%s"
              % (c['capability_id'], who))
    if not (ap.get('decided_on') or '').strip():
        print("APPROVED_UNDATED: %s" % c['capability_id'])
    if 'production promotion' not in (ap.get('scope') or ''):
        print("APPROVED_OUTSIDE_PROMOTION_SCOPE: %s scope=%s"
              % (c['capability_id'], ap.get('scope')))
PY
if [ -s "$TMP/ap" ]; then
  while IFS= read -r l; do fail "$l"; done < "$TMP/ap"
else
  pass "every APPROVED capability is attributable to the User"
fi
jq -e '[.deferred[].reason] | all(. != null and length > 10)' \
  "$SPS2/capability/registry.json" >/dev/null 2>&1 \
  && pass "every deferred candidate carries a stated reason" \
  || fail "a deferred candidate has no reason"

sect "5. Research stays research"
jq -e '[.capabilities[].origin] | all(. != "RESEARCH_ONLY")' \
  "$SPS2/capability/registry.json" >/dev/null 2>&1 \
  && pass "no research-only record appears in production" \
  || fail "research-only record leaked into production"
jq -e '.conflicts[0].resolution | test("UNRESOLVED")' \
  "$SPS2/research/P2-SOURCES.json" >/dev/null 2>&1 \
  && pass "CONF-001 (LCP/INP) still UNRESOLVED" || fail "CONF-001 was silently closed"
jq -e '.capabilities[] | select(.capability_id=="CAP-028") | .status == "UNVERIFIED"' \
  "$SPS2/research/P2-CAPABILITY-EXTRACTION.json" >/dev/null 2>&1 \
  && pass "CAP-028 still UNVERIFIED" || fail "CAP-028 was upgraded"

sect "6. Determinism and popularity discipline"
DET=$(python3 - "$ENGINE" <<'PY'
import importlib.util, itertools, json, sys
spec = importlib.util.spec_from_file_location("eng", sys.argv[1])
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)
reg = json.load(open(sys.argv[1].replace("/capability/engine.py",
                                        "/capability/registry.json")))
caps = reg["capabilities"]
req = {"domains": ["seo"], "required_capabilities": []}
print(len({eng.select(list(p), req)["fingerprint"]
           for p in itertools.islice(itertools.permutations(caps), 24)}))
PY
)
[ "$DET" = "1" ] && pass "ranking identical across 24 input permutations" \
  || fail "ranking is NOT deterministic ($DET distinct results)"
jq -e '.popularity_role == "TIE_BREAKER_ONLY" and .recency_role == "TIE_BREAKER_ONLY"' \
  "$SPS2/project/SELECTION-P3-0001.json" >/dev/null 2>&1 \
  && pass "popularity and recency declared as tie-breakers only" \
  || fail "popularity/recency role misdeclared"
jq -e '.provenance.runtime_tracing == false' \
  "$SPS2/project/SELECTION-P3-0001.json" >/dev/null 2>&1 \
  && pass "provenance does not overclaim runtime tracing" \
  || fail "provenance overclaims runtime tracing"

sect "7. Forced user choice is respected"
FC=$(python3 - "$ENGINE" <<'PY'
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("eng", sys.argv[1])
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)
reg = json.load(open(sys.argv[1].replace("/capability/engine.py",
                                        "/capability/registry.json")))
caps = reg["capabilities"]; req = {"domains": ["seo"], "required_capabilities": []}
res = eng.select(caps, req)
last = res["ranking"][-1]["capability_id"]
forced, info = eng.apply_forced_choice(res["ranking"], last, caps)
ok1 = forced[0]["capability_id"] == last and info["forced"]
bad = json.loads(json.dumps(caps[-1]))
bad["capability_id"] = "CAP-SPS-901"
bad["security"] = {"status": "VULNERABLE", "evidence": "x", "fact_class": "EVIDENCE"}
res2 = eng.rank(caps + [bad], req)
f2, i2 = eng.apply_forced_choice(res2, "CAP-SPS-901", caps + [bad])
ok2 = (not i2["forced"]) and "MANDATORY_SAFECY" in i2["reason"]
print("yes" if (ok1 and ok2) else "no")
PY
)
[ "$FC" = "yes" ] && pass "forced choice honoured, and blocked by safety constraints" \
  || fail "forced-choice behaviour is incorrect"

sect "8. Legacy and machine-global protection"
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
if grep -rqE --exclude-dir=tools 'git config --global|\$HOME/\.(sps|claude|codex|config)' "$SPS2" 2>/dev/null; then
  fail "sps2 references machine-global state"
else
  pass "no machine-global path referenced in sps2"
fi
if find "$SPS2" \( -name 'node_modules' -o -name 'package-lock.json' -o -name '*.whl' \) \
   2>/dev/null | grep -q .; then
  fail "external dependency artefact present"
else
  pass "no dependency installed or vendored"
fi
if git -C "$REPO" --no-pager diff HEAD -- .sps/ | grep -q .; then
  fail "legacy .sps/ governance was modified"
else
  pass "legacy .sps/ governance untouched"
fi

sect "9. No emoji and no credential material"
python3 "$SPS2/security/scan_secrets.py" "$SPS2" --quiet \
  && pass "no credential-shaped value under framework/sps2/" \
  || fail "credential-shaped value detected under framework/sps2/"
python3 "$SPS2/security/scan_secrets.py" "$REPO" --quiet \
  && pass "no credential-shaped value in the repository" \
  || fail "credential-shaped value detected in the repository"
[ -f "$SPS2/security/INCIDENT-P3-001-CREDENTIAL-EXPOSURE.md" ] \
  && pass "INCIDENT-P3-001 record present" || fail "incident record missing"
if grep -rqE 'sk-or-v1-[A-Za-z0-9]{32,}' "$SPS2/security/INCIDENT-P3-001-CREDENTIAL-EXPOSURE.md" \
   "$SPS2/evidence/SEC-P3-INCIDENT-EVIDENCE.json" 2>/dev/null; then
  fail "incident documentation contains a credential value"
else
  pass "incident documentation contains no credential value"
fi
[ -f "$SPS2/security/scan_secrets.py" ] && pass "secret scanner present" \
  || fail "secret scanner missing"
[ -f "$SPS2/security/test-secret-safety.sh" ] \
  && pass "secret-safety negative test present" || fail "negative test missing"

sect "10. Credential must not be in any reachable commit"
# This check must never pass vacuously. An earlier version read the token from
# the working-tree .claude/settings.json and skipped the whole scan when that
# file was absent, so a harness deletion silently turned this into a false
# PASS. It is now key-based and always evaluates every commit. No credential
# value is printed.
if python3 - "$REPO" <<'PY' > "$TMP/credscan" 2>&1
import json, subprocess, sys
R = sys.argv[1]
PATH = '.claude/settings.json'
KEYS = ('ANTHROPIC_AUTH_TOKEN', 'OPENROUTER_KEY', 'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY')
PRESERVED_CHECKPOINT = 'a7767cf5f761cab4aa633c1cbc7604f83e4d14f8'
shas = subprocess.run(['git', '-C', R, 'rev-list', '--all'],
                      capture_output=True, text=True, check=True).stdout.split()
offenders = []
for s in shas:
    raw = subprocess.run(['git', '-C', R, 'show', '%s:%s' % (s, PATH)],
                         capture_output=True, text=True).stdout
    if not raw.strip():
        continue
    try:
        env = (json.loads(raw) or {}).get('env') or {}
    except Exception:
        continue
    if any(k in env for k in KEYS):
        offenders.append(s)
others = [s for s in offenders if s != PRESERVED_CHECKPOINT]
if others:
    for s in others:
        print("CREDENTIAL_IN_COMMIT: %s" % s[:12])
elif offenders == [PRESERVED_CHECKPOINT]:
    # Documented, accepted condition: the only credential-bearing commit is the
    # forensic checkpoint the user ordered preserved. Purging it would require a
    # history rewrite, which is forbidden. This is reported, never hidden.
    print("PRESERVED_CHECKPOINT_HOLDS_CREDENTIAL: %s (accepted by user "
          "decision; removal would require a forbidden history rewrite)"
          % PRESERVED_CHECKPOINT[:12])
raise SystemExit(1 if others else 0)
PY
then
  if [ -s "$TMP/credscan" ]; then
    while IFS= read -r l; do warn "$l"; done < "$TMP/credscan"
  fi
  pass "no commit outside the preserved checkpoint contains a credential"
else
  fail "a reachable commit outside the preserved checkpoint contains a credential"
fi
if python3 "$SPS2/tools/test-history-credential-check.py" >/dev/null 2>&1; then
  pass "history-credential check mutation test: all 4 scenarios correct"
else
  fail "history-credential check mutation test FAILED"
fi
if git -C "$REPO" check-ignore -q .claude/settings.local.json 2>/dev/null; then
  pass "local agent settings are gitignored as a prevention measure"
else
  warn "local agent settings are not gitignored"
fi

sect "11. No emoji"
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
[ -z "$EMJ" ] && pass "no emoji in any sps2 file" || fail "emoji found: $EMJ"

fi  # end structural

# Cases A-O are mandated by the P3 brief. Each asserts that a real gate rule
# rejects the invalid state, not merely that a string is absent.
sect "NEGATIVE TESTS — invalid P3 states must be rejected"

# A. duplicate capability ID (enforced at registry level)
mk "pass"
python3 - "$TMP/f.json" "$TMP/dup.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
json.dump({"capabilities": [d, dict(d)]}, open(sys.argv[2], "w"))
PY
if python3 "$CHECK" registry "$TMP/dup.json" 2>&1 | grep -q 'DUPLICATE_CAPABILITY_ID'; then
  info "REJECTED -> A  duplicate capability ID"; NEG_PASS=$((NEG_PASS+1))
  pass "A  duplicate capability ID -> rejected"
else
  info "NOT REJECTED -> A"; NEG_FAIL=$((NEG_FAIL+1)); fail "A  duplicate capability ID NOT rejected"
fi

# B. missing evidence
gate "d['evidence']=[]" "MISSING_FIELD.*evidence|MISSING_EVIDENCE" "B  missing evidence"
# C. fabricated provenance
gate "d['provenance']['origin']=''" "FABRICATED_PROVENANCE" "C  fabricated provenance"
# D. unknown security presented as safe
gate "d['security']={'status':'VERIFIED_SAFE','fact_class':'FACT'}" \
     "UNSUPPORTED_SECURITY" "D  unknown security marked safe"
# E. agent-attributed approval
gate "d['approval']={'state':'APPROVED','decided_by':'agent'}" \
     "AGENT_ATTRIBUTED_APPROVAL" "E  agent-attributed approval"
# F. approval without user attribution
gate "d['approval']={'state':'APPROVED','decided_by':''}" \
     "MISSING_USER_ATTRIBUTION" "F  approval without user attribution"
# G. stale capability without review
gate "d['staleness']={'state':'STALE','maintenance':'ACTIVE','last_checked':'2026-10-03'}" \
     "STALE_WITHOUT_REVIEW" "G  stale without review"
# G2. stale treated as active
gate "d['staleness']={'state':'STALE','maintenance':'ACTIVE','last_checked':'2026-10-03','review_due':'2027-01-01'};d['lifecycle_state']='ACTIVE';d['verification']={'state':'VERIFIED','evidence':['EV-P3-001']}" \
     "STALE_AS_ACTIVE" "G2 stale treated as ACTIVE"
# H. unsupported compatibility claim
gate "d['compatibility']={'status':'COMPATIBLE','agent_neutral':False,'basis':'x'}" \
     "UNSUPPORTED_COMPATIBILITY" "H  unsupported compatibility claim"
# I. global capability without authorization
gate "d['install_scope']='GLOBAL'" "GLOBAL_WITHOUT_AUTHORIZATION" "I  global without authorization"
# J. malformed capability record
gate "d['capability_id']='not-an-id'" "INVALID_ID" "J  malformed capability record"
# M. invalid lifecycle transition
gate "d['lifecycle_state']='ACTIVE';d['verification']={'state':'VERIFIED','evidence':[]}" \
     "UNVERIFIED_IMPLEMENTATION" "M  invalid lifecycle transition"
# O. unapproved research-only capability in production
gate "d['origin']='RESEARCH_ONLY'" "RESEARCH_ONLY_LEAK" "O  research-only capability promoted"
# K. deterministic ranking violation (selection record with reordered scores)
python3 - "$SPS2" "$TMP/badrank.json" <<'PY'
import json, sys
sel = json.load(open(sys.argv[1] + "/project/SELECTION-P3-0001.json"))
r = sel["ranking"]; r[0]["score"], r[-1]["score"] = r[-1]["score"], r[0]["score"]
json.dump(sel, open(sys.argv[2], "w"))
PY
if python3 "$CHECK" selection "$SPS2/capability/registry.json" "$TMP/badrank.json" 2>&1 \
     | grep -q 'DETERMINISM_VIOLATION'; then
  info "REJECTED -> K  deterministic ranking violation"; NEG_PASS=$((NEG_PASS+1))
  pass "K  deterministic ranking violation -> rejected"
else
  info "NOT REJECTED -> K"; NEG_FAIL=$((NEG_FAIL+1)); fail "K  ranking violation NOT rejected"
fi

# L. forced user selection being overridden
python3 - "$ENGINE" > "$TMP/forced.txt" 2>&1 <<'PY'
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("eng", sys.argv[1])
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)
reg = json.load(open(sys.argv[1].replace("/capability/engine.py",
                                        "/capability/registry.json")))
caps = reg["capabilities"]; req = {"domains": ["seo"], "required_capabilities": []}
res = eng.select(caps, req)
chosen = res["ranking"][-1]["capability_id"]
forced, info = eng.apply_forced_choice(res["ranking"], chosen, caps)
print("OVERRIDDEN" if forced[0]["capability_id"] != chosen else "HONOURED")
PY
if grep -q 'HONOURED' "$TMP/forced.txt"; then
  info "REJECTED -> L  forced user choice silently overridden"; NEG_PASS=$((NEG_PASS+1))
  pass "L  forced user choice NOT overridden -> enforced"
else
  info "FORCED CHOICE WAS OVERRIDDEN (defect) -> L"; NEG_FAIL=$((NEG_FAIL+1))
  fail "L  forced user choice was overridden"
fi

# N. missing rollback information
python3 - "$SPS2" "$TMP/noroll.json" <<'PY'
import json, sys
sel = json.load(open(sys.argv[1] + "/project/SELECTION-P3-0001.json"))
sel.pop("rollback", None)
json.dump(sel, open(sys.argv[2], "w"))
PY
if python3 "$CHECK" selection "$SPS2/capability/registry.json" "$TMP/noroll.json" 2>&1 \
     | grep -q 'MISSING_ROLLBACK'; then
  info "REJECTED -> N  missing rollback information"; NEG_PASS=$((NEG_PASS+1))
  pass "N  missing rollback information -> rejected"
else
  info "NOT REJECTED -> N"; NEG_FAIL=$((NEG_FAIL+1)); fail "N  missing rollback NOT rejected"
fi

# POSCTRL-2: a valid selection record is accepted
POS2=$(python3 "$CHECK" selection "$SPS2/capability/registry.json" \
         "$SPS2/project/SELECTION-P3-0001.json" 2>&1); POS2_RC=$?
if [ "$POS2_RC" -ne 0 ]; then
  info "WRONGLY REJECTED -> POSCTRL-2 (checker exited $POS2_RC)"
  NEG_FAIL=$((NEG_FAIL+1)); fail "POSCTRL-2  positive control could not run: $POS2"
elif [ -z "$POS2" ]; then
  info "ACCEPTED -> POSCTRL-2 valid selection record"
  NEG_PASS=$((NEG_PASS+1)); pass "POSCTRL-2  valid selection record accepted"
else
  info "WRONGLY REJECTED -> POSCTRL-2"
  NEG_FAIL=$((NEG_FAIL+1)); fail "POSCTRL-2  valid selection record rejected"
fi

echo ""
if [ "$NEG_FAIL" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}== P3 NEGATIVE SUITE: $NEG_PASS cases correctly rejected, 0 missed ==${NC}"
else
  echo -e "${RED}${BOLD}== P3 NEGATIVE SUITE: $NEG_PASS rejected, $NEG_FAIL MISSED ==${NC}"
fi

echo ""
if [ "$FAIL" -eq 0 ] && [ "$NEG_FAIL" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}== P3 PRODUCTION VALID: $PASS checks passed, 0 failed, $NEG_PASS negative/positive controls enforced ==${NC}"
  exit 0
fi
echo -e "${RED}${BOLD}== P3 PRODUCTION INVALID: $PASS passed, $FAIL failed, $NEG_FAIL missed ==${NC}"
exit 1
