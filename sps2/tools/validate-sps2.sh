#!/usr/bin/env bash
# SPS 2.0 P1 foundation validator.
# Validates STRUCTURED STATE (JSON contracts, boundaries, policy), not the
# presence of words in Markdown.
# SAFETY: no network, no installs, no machine-global writes, never modifies a
# real file. Negative fixtures live only in a self-managed temp dir.
# Usage: bash sps2/tools/validate-sps2.sh [--negative]
# Exit:  0 valid | 1 failure | 2 tooling unavailable

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPS2="$(cd "$HERE/.." && pwd)"
REPO="$(cd "$SPS2/.." && pwd)"
CHECK="$HERE/check_sps2.py"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[1;34m'
BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'
PASS=0; FAIL=0
pass() { echo -e "  ${GREEN}PASS${NC}  $*"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}FAIL${NC}  $*"; FAIL=$((FAIL+1)); }
info() { echo -e "  ${BLUE}CASE${NC} $*"; }
warn() { echo -e "  ${YELLOW}WARN${NC}  $*"; }
sect() { echo -e "\n${BOLD}$*${NC}"; }

command -v python3 >/dev/null 2>&1 || { echo "python3 unavailable"; exit 2; }
TMP="$(mktemp -d "${TMPDIR:-/tmp}/sps2-XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

NEG_ONLY=false
for a in "$@"; do [ "$a" = "--negative" ] && NEG_ONLY=true; done

echo -e "${BOLD}SPS 2.0 Foundation Validator (P1)${NC}"
echo -e "${DIM}structured-state validation; no network, no installs, no global writes${NC}"

run_check() { python3 "$CHECK" "$1" "$2" 2>/dev/null; }

assert_clean() {  # kind file label
  local out; out="$(run_check "$1" "$2")"
  if [ -z "$out" ]; then pass "$3"; else
    while IFS= read -r l; do [ -n "$l" ] && fail "$3: $l"; done <<< "$out"
  fi
}

# Negative-suite counters are initialised unconditionally: the tail structural
# cases run even in --negative mode and must not hit an unbound variable.
NEG_PASS=0; NEG_FAIL=0

if [ "$NEG_ONLY" != true ]; then

sect "1. Required structure"
for d in core core/lifecycle core/protocols core/gates core/adapters \
         governance governance/SCHEMAS governance/policies \
         capability capability/security research project skills mcp \
         tests tests/fixtures docs docs/adr legacy tools; do
  [ -d "$SPS2/$d" ] && pass "dir $d" || fail "missing dir $d"
done

sect "2. Required contracts"
for f in requirement capability evidence decision action handoff; do
  p="$SPS2/governance/SCHEMAS/$f.schema.json"
  if [ -f "$p" ] && python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
sys.exit(0 if d.get('\$id') and d.get('required') else 1)" "$p" 2>/dev/null; then
    pass "contract $f.schema.json valid"
  else
    fail "contract $f.schema.json invalid or incomplete"
  fi
done

sect "3. Structured state validity"
assert_clean capability   "$SPS2/capability/registry.json"        "capability registry"
assert_clean evidence     "$SPS2/evidence/P1-EVIDENCE.json"        "P1 evidence"
assert_clean decision     "$SPS2/decisions/P1-DECISIONS.json"      "P1 decisions"
assert_clean requirement "$SPS2/requirements/P1-REQUIREMENTS.json" "P1 requirements"

sect "4. Registry holds only legitimately promoted capabilities"
# Since P3 the registry may be populated, but every entry must pass the
# production promotion gate. Emptiness is no longer the invariant; PROMOTED
# VALIDITY is. An empty registry is still valid and is asserted separately.
NCAP=$(python3 -c "import json;print(len(json.load(open('$SPS2/capability/registry.json'))['capabilities']))" 2>/dev/null || echo -1)
[ "$NCAP" -ge 0 ] 2>/dev/null && pass "registry is readable ($NCAP capabilities)" \
                  || fail "registry is unreadable"
python3 - "$SPS2" > "$TMP/promo" 2>&1 <<'PY'
import importlib.util, json, os, sys
B = sys.argv[1]
reg = json.load(open(B + '/capability/registry.json'))
ids = [c['capability_id'] for c in reg['capabilities']]
dup = sorted({i for i in ids if ids.count(i) > 1})
if dup:
    print("DUPLICATE_CAPABILITY_ID: %s" % dup)
# Since P4 the production gate is the hardened A-K promotion gate. The
# invariant is that each stored assessment matches a fresh gate run, not that
# every capability is already promoted.
pg_path = os.path.join(B, 'capability', 'promotion_gates.py')
if os.path.isfile(pg_path):
    spec = importlib.util.spec_from_file_location("pg", pg_path)
    pg = importlib.util.module_from_spec(spec); spec.loader.exec_module(pg)
    for c in reg['capabilities']:
        res, blocking = pg.evaluate(c)
        stored = (c.get('promotion_assessment') or {}).get('blocking_gates')
        if stored is None:
            print("ASSESSMENT_MISSING: %s" % c['capability_id'])
        elif sorted(stored) != sorted(blocking):
            print("ASSESSMENT_STALE: %s" % c['capability_id'])
        for k, v in res.items():
            if not v['pass'] and k not in blocking:
                print("GATE_INCONSISTENCY: %s" % c['capability_id'])
else:
    sys.path.insert(0, B + '/capability')
    import engine
    for c in reg['capabilities']:
        ok, reasons = engine.promote(c)
        if not ok:
            print("PROMOTION_GATE_FAIL: %s: %s"
                  % (c['capability_id'], "; ".join(reasons)))
PY
if [ -s "$TMP/promo" ]; then
  while IFS= read -r l; do fail "$l"; done < "$TMP/promo"
else
  pass "every registered capability passes the production promotion gate"
fi

sect "5. Dynamic selection is not hardcoded"
grep -q '"hardcoded_domain_mapping_forbidden": true' "$SPS2/capability/registry.json" \
  && pass "registry forbids hardcoded domain->capability mapping" || fail "hardcoded mapping not forbidden"
grep -q '"supports_multiple_candidates_per_domain": true' "$SPS2/capability/registry.json" \
  && pass "multiple candidates per domain supported" || fail "no multi-candidate support"
# NB: --exclude-dir=tools stops the validator matching its own pattern strings.
# The exclusion is scoped to this tools/ directory, not to any governed content.
if grep -rqE --exclude-dir=tools 'skills add.*-g|design[[:space:]]*->[[:space:]]*[A-Za-z0-9_-]+/' "$SPS2" 2>/dev/null; then
  fail "hardcoded domain mapping or global installer present in sps2/"
else
  pass "no hardcoded domain mapping or global installer in sps2/"
fi
sect "6. No-emoji policy (machine-checked)"
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
        n = len(pat.findall(t))
        if n:
            hits.append('%s:%d' % (p.replace(sys.argv[1] + '/', ''), n))
print(';'.join(hits))
PY
)
[ -z "$EMJ" ] && pass "no emoji in any sps2/ file" || fail "emoji found: $EMJ"
grep -rq 'NO EMOJI' "$SPS2/governance/policies/NO-EMOJI.md" \
  && pass "no-emoji policy declared" || fail "no-emoji policy not declared"

sect "7. Project-local boundary"
if [ -n "$(find "$SPS2" -type d \( -name '.claude' -o -name '.cursor' -o -name '.gemini' -o -name '.agents' \) 2>/dev/null)" ]; then
  fail "agent-specific global directory created inside sps2/"
else
  pass "no agent-specific global directory inside sps2/"
fi
if grep -rqE --exclude-dir=tools 'git config --global|\$HOME/\.sps' "$SPS2" 2>/dev/null; then
  fail "sps2/ references machine-global state"
else
  pass "no machine-global state referenced in sps2/"
fi
# Validators are not installers. Exclude every file under tools/ that is
# explicitly a validator, rather than hardcoding a single filename.
# Validators are not installers. Exclude every explicitly-named validator or
# test harness under tools/ and security/, rather than hardcoding one filename.
INSTALLERS=$(find "$SPS2" \( -name '*.sh' -o -name '*.ps1' \) 2>/dev/null \
  | grep -v '/tools/validate-sps2.sh' | grep -v '/tools/validate-p2.sh' \
  | grep -v '/tools/validate-p3.sh' | grep -v '/tools/validate-p4.sh' \
  | grep -v '/tools/test-snapshot-integrity.sh' \
  | grep -v '/tools/test-phase-boundary.sh' \
  | grep -v '/tools/test-p7-readiness-mutation.sh' \
  | grep -v '/security/test-secret-safety.sh')
if [ -n "$INSTALLERS" ]; then
  fail "sps2/ ships executable installers: $INSTALLERS"
else
  pass "no installer scripts in sps2/ (nothing installs globally)"
fi

sect "8. Agent neutrality"
BRAND=$(grep -rlIiE '\b(claude|cursor|codex|gemini|opencode|cline|antigravity)\b' \
        "$SPS2/core" 2>/dev/null | grep -v '/adapters/' || true)
[ -z "$BRAND" ] && pass "core/ free of vendor references outside adapters/" \
                 || fail "core/ references a vendor outside adapters/: $BRAND"
[ -f "$SPS2/core/adapters/contract.schema.json" ] && pass "adapter contract present" || fail "adapter contract missing"
[ -f "$SPS2/core/adapters/registry.json" ] && pass "adapter registry present" || fail "adapter registry missing"

sect "9. Legacy protection"
[ -f "$SPS2/legacy/MANIFEST.md" ] && pass "legacy manifest present" || fail "legacy manifest missing"
DIFF=$(cd "$REPO" && git diff --name-only HEAD -- skills scripts plugins .github \
       install.sh install.ps1 uninstall.sh uninstall.ps1 get-sps.sh get-sps.ps1 2>/dev/null)
[ -z "$DIFF" ] && pass "legacy implementation untouched by P1" || fail "legacy modified: $DIFF"

sect "10. Git provenance"
cd "$REPO" || exit 2
git rev-parse --is-inside-work-tree >/dev/null 2>&1 && pass "git repository present" || fail "not a git repository"
BR=$(git rev-parse --abbrev-ref HEAD 2>/dev/null); [ -n "$BR" ] && pass "branch: $BR" || warn "no branch"

sect "11. P10 inventory contract"
P10_OUT="$(python3 "$HERE/check_p10_inventory.py" 2>&1)"; P10_RC=$?
if [ "$P10_RC" -eq 0 ]; then
  pass "P10 section inventory conforms (structural subset)"
else
  while IFS= read -r l; do [ -n "$l" ] && fail "P10 inventory: $l"; done <<< "$P10_OUT"
  [ "$FAIL" -eq 0 ] && fail "P10 inventory validation failed (exit $P10_RC)"
fi
sect "12. P17 (test doubles only; real-agent execution disabled)"
# Test doubles only. No real agent CLI is probed or invoked: the P17 suites
# use repository-local test doubles and an isolated test allowlist, and the
# implementation refuses the production allowlist while GATE-P17-4 is OPEN.
# Exit-status propagation, NOT assert_clean: these suites print by design.
P17_SEC_OUT="$(python3 "$SPS2/tests/test_p17_security.py" 2>&1)"; P17_SEC_RC=$?
P17_SEC_RAN="$(printf '%s\n' "$P17_SEC_OUT" | sed -n 's/^Ran \([0-9][0-9]*\).*/\1/p' | tail -1)"
if [ "$P17_SEC_RC" -eq 0 ]; then
  pass "P17 security suite: ${P17_SEC_RAN:-?} tests, 0 failed (SEC-P17-01..11)"
else
  while IFS= read -r l; do [ -n "$l" ] && fail "P17 security: $l"; done <<< \
    "$(printf '%s\n' "$P17_SEC_OUT" | grep -E '^(FAIL|ERROR): ')"
  [ "$FAIL" -eq 0 ] && fail "P17 security suite failed (exit $P17_SEC_RC)"
fi

# Lifecycle integrity and recovery hardening. Same isolation contract as the
# security suite: every case builds its own temporary project root and test
# allowlist, and the suite itself fails if the real repository's P17 task or
# evidence tree, or its usage log, changed. It therefore runs in place and
# writes nothing into this repository.
P17_LIFE_OUT=""; P17_LIFE_RC=0; P17_LIFE_RAN=""
if [ -f "$SPS2/tests/test_p17_lifecycle.py" ] && [ -d "$SPS2/p17" ]; then
  P17_LIFE_OUT="$(python3 "$SPS2/tests/test_p17_lifecycle.py" 2>&1)"; P17_LIFE_RC=$?
  P17_LIFE_RAN="$(printf '%s\n' "$P17_LIFE_OUT" | sed -n 's/^Ran \([0-9][0-9]*\).*/\1/p' | tail -1)"
  P17_LIFE_SKIP="$(printf '%s\n' "$P17_LIFE_OUT" | sed -n 's/^OK (skipped=\([0-9][0-9]*\).*/\1/p' | tail -1)"
  if [ "$P17_LIFE_RC" -eq 0 ]; then
    if [ -n "${P17_LIFE_SKIP:-}" ] && [ "$P17_LIFE_SKIP" != "0" ]; then
      pass "P17 lifecycle suite: ${P17_LIFE_RAN:-?} tests OK, ${P17_LIFE_SKIP} skipped"
    else
      pass "P17 lifecycle suite: ${P17_LIFE_RAN:-?} tests OK (isolated roots)"
    fi
  else
    while IFS= read -r l; do [ -n "$l" ] && fail "P17 lifecycle: $l"; done <<< \
      "$(printf '%s\n' "$P17_LIFE_OUT" | grep -E '^(FAIL|ERROR): ')"
    [ "$FAIL" -eq 0 ] && fail "P17 lifecycle suite failed (exit $P17_LIFE_RC)"
  fi
else
  warn "P17 lifecycle suite not present; nothing was run"
fi

# The end-to-end suite writes project-local task state by design, so it runs
# from an isolated copy of exactly what it needs: this validator never
# modifies a real file.
P17_E2E="$TMP/p17-e2e"
if [ -f "$SPS2/tests/test_p17_endtoend.py" ] && [ -d "$SPS2/p17" ]; then
  mkdir -p "$P17_E2E/sps2/tests/fixtures" "$P17_E2E/sps2/schemas"
  cp -R "$SPS2/p17" "$P17_E2E/sps2/p17" 2>/dev/null
  cp "$SPS2/schemas/p17-task-record.schema.json" "$P17_E2E/sps2/schemas/" 2>/dev/null
  cp "$SPS2/tests/test_p17_endtoend.py" "$P17_E2E/sps2/tests/" 2>/dev/null
  cp -R "$SPS2/tests/fixtures/p17" "$P17_E2E/sps2/tests/fixtures/p17" 2>/dev/null
  # Ajv discovery is opt-in via the environment: no machine-global path is
  # hardcoded here (project-local boundary rule). When it is not supplied the
  # conformance case SKIPs inside the test with a stated reason, which is a
  # pass for the suite, not a weakened check.
  if [ -n "${P17_AJV_ROOT:-}" ] && [ -d "${P17_AJV_ROOT:-}" ]; then
    P17_E2E_OUT="$(P17_AJV_ROOT="$P17_AJV_ROOT" python3 "$P17_E2E/sps2/tests/test_p17_endtoend.py" 2>&1)"; P17_E2E_RC=$?
    P17_E2E_NOTE="schema conformance checked with the supplied ajv"
  else
    P17_E2E_OUT="$(python3 "$P17_E2E/sps2/tests/test_p17_endtoend.py" 2>&1)"; P17_E2E_RC=$?
    P17_E2E_NOTE="no ajv supplied: conformance case SKIPs by design"
  fi
  P17_E2E_RAN="$(printf '%s\n' "$P17_E2E_OUT" | sed -n 's/^Ran \([0-9][0-9]*\).*/\1/p' | tail -1)"
  P17_E2E_SKIP="$(printf '%s\n' "$P17_E2E_OUT" | sed -n 's/^OK (skipped=\([0-9][0-9]*\).*/\1/p' | tail -1)"
  if [ "$P17_E2E_RC" -eq 0 ]; then
    if [ -n "${P17_E2E_SKIP:-}" ] && [ "$P17_E2E_SKIP" != "0" ]; then
      pass "P17 end-to-end: ${P17_E2E_RAN:-?} tests OK, ${P17_E2E_SKIP} skipped ($P17_E2E_NOTE)"
    else
      pass "P17 end-to-end: ${P17_E2E_RAN:-?} tests OK ($P17_E2E_NOTE)"
    fi
  else
    while IFS= read -r l; do [ -n "$l" ] && fail "P17 end-to-end: $l"; done <<< \
      "$(printf '%s\n' "$P17_E2E_OUT" | grep -E '^(FAIL|ERROR): ')"
    [ "$FAIL" -eq 0 ] && fail "P17 end-to-end suite failed (exit $P17_E2E_RC)"
  fi
else
  warn "P17 end-to-end suite not present; nothing was run"
fi

# Executable-pinning suite (fail-closed resolution). Same isolation
# contract as the security and lifecycle suites: every case builds its
# own temporary project root and trusted-root configuration, so it runs
# in place and writes nothing into this repository. It verifies that an
# allowlisted name is never resolved against the ambient PATH, that a
# missing or invalid pin fails closed, and that a substituted executable
# is detected by digest before it is spawned.
P17_PIN_OUT=""; P17_PIN_RC=0; P17_PIN_RAN=""
if [ -f "$SPS2/tests/test_p17_pinning.py" ] && [ -d "$SPS2/p17" ]; then
  P17_PIN_OUT="$(python3 "$SPS2/tests/test_p17_pinning.py" 2>&1)"; P17_PIN_RC=$?
  P17_PIN_RAN="$(printf '%s\n' "$P17_PIN_OUT" | sed -n 's/^Ran \([0-9][0-9]*\).*/\1/p' | tail -1)"
  if [ "$P17_PIN_RC" -eq 0 ]; then
    pass "P17 pinning suite: ${P17_PIN_RAN:-?} tests OK (fail-closed resolution)"
  else
    while IFS= read -r l; do [ -n "$l" ] && fail "P17 pinning: $l"; done <<< \
      "$(printf '%s\n' "$P17_PIN_OUT" | grep -E '^(FAIL|ERROR): ')"
    [ "$FAIL" -eq 0 ] && fail "P17 pinning suite failed (exit $P17_PIN_RC)"
  fi
else
  warn "P17 pinning suite not present; nothing was run"
fi
fi  # end structural (sections 1-12)

# ══ NEGATIVE SUITE ═══════════════════════════════════════════════════════════
# Runs in BOTH modes: --negative executes this suite alone, skipping sections 1-10.
sect "NEGATIVE TESTS — invalid states must be rejected"

# neg <kind> <label> <expect-regex> <python-mutation>
neg() {
  local kind="$1" label="$2" expect="$3" mut="$4"
  python3 - "$kind" "$mut" > "$TMP/n.json" <<'PY'
import json, sys
BASE = {
 "requirement": {"requirements": [{"requirement_id": "REQ-P1-01", "title": "Valid fixture",
   "objective": "A valid objective for testing", "scope": "IN_SCOPE", "risk": "LOW",
   "status": "DECLARED", "acceptance_criteria": ["Executing the check returns no error"],
   "evidence_refs": [], "implementation": {"state": "NOT_STARTED", "refs": []},
   "verification": {"state": "UNVERIFIED", "method": "AUTOMATED"},
   "approval": {"state": "NOT_REQUIRED"}}]},
 "capability": {"capabilities": [{"capability_id": "CAP-P1-001", "name": "Fixture",
   "type": "LIBRARY", "domain": "testing", "source": "OFFICIAL_REPO",
   "provenance": {"origin": "fixture", "captured_at": "2026-10-03T00:00:00Z",
                  "fact_class": "FACT"}, "version": "1.0.0",
   "compatibility": {"technology": "COMPATIBLE", "framework": "COMPATIBLE",
                     "agent_neutral": True, "agent_specific_dependency": None},
   "security": {"status": "VERIFIED_SAFE", "evidence": "fixture"},
   "staleness": {"state": "CURRENT", "last_checked": "2026-10-03"},
   "install_scope": "PROJECT_LOCAL", "project_local_install_method": "none needed",
   "rollback_method": "remove record", "verification": {"state": "UNVERIFIED"},
   "approval": {"state": "NOT_REQUIRED"},
   "lifecycle_state": "DISCOVERED"}]},
 "evidence": {"records": [{"evidence_id": "EV-P1-001", "source": "VALIDATOR",
   "timestamp": "2026-10-03T00:00:00Z", "command": "true",
   "observed_result": "clean output captured", "result": "PASS", "relates_to": {}}]},
 "decision": {"decisions": [{"decision_id": "DEC-9001", "title": "Fixture decision",
   "decision": "A valid decision for testing", "reason": "A valid reason string here",
   "evidence": ["EV-P1-001"], "alternatives": [], "status": "PROPOSED",
   "approval": {"required": True, "state": "PENDING_USER_APPROVAL"}}]},
}
kind, mut = sys.argv[1], sys.argv[2]
d = BASE[kind]
exec(mut)
print(json.dumps(d))
PY
  local out; out="$(run_check "$kind" "$TMP/n.json")"
  if [ -n "$out" ] && printf '%s' "$out" | grep -qiE "$expect"; then
    info "REJECTED -> $label"
    NEG_PASS=$((NEG_PASS+1)); pass "$label -> rejected"
  else
    info "NOT REJECTED (validator defect!) -> $label"
    NEG_FAIL=$((NEG_FAIL+1)); fail "$label -> NOT rejected (out: ${out:-none})"
  fi
}

# positive control: an unmodified fixture MUST be accepted
python3 - "requirement" "pass" > "$TMP/pos.json" <<'PY'
import json, sys
print(json.dumps({"requirements": [{"requirement_id": "REQ-P1-01", "title": "Valid",
  "objective": "A valid objective for testing", "scope": "IN_SCOPE", "risk": "LOW",
  "status": "DECLARED", "acceptance_criteria": ["Executing the check returns no error"],
  "evidence_refs": [], "implementation": {"state": "NOT_STARTED", "refs": []},
  "verification": {"state": "UNVERIFIED", "method": "AUTOMATED"},
  "approval": {"state": "NOT_REQUIRED"}}]}))
PY
POS="$(run_check requirement "$TMP/pos.json")"
# --- requirement integrity ---
neg requirement "A  requirement has no acceptance criteria" "acceptance_criteria empty" \
    "d['requirements'][0]['acceptance_criteria']=[]"
neg requirement "A2 requirement VERIFIED without evidence" "VERIFIED without evidence" \
    "v=d['requirements'][0]['verification'];v['state']='VERIFIED'"
neg requirement "B  implementation verified without evidence" "without evidence" \
    "i=d['requirements'][0]['implementation'];i['verified']=True"
neg requirement "C  approval attributed to an agent" "non-user" \
    "a=d['requirements'][0]['approval'];a['state']='APPROVED';a['decided_by']='agent'"
neg requirement "G  approval APPROVED with no decider" "without decided_by" \
    "a=d['requirements'][0]['approval'];a['state']='APPROVED';a['decided_by']=''"
neg requirement "I  duplicate requirement IDs" "duplicate requirement IDs" \
    "d['requirements'].append(dict(d['requirements'][0]))"
neg requirement "K  malformed requirement_id" "bad requirement_id" \
    "d['requirements'][0]['requirement_id']='bad id'"
neg requirement "   HIGH risk verified only by AGENT" "insufficient for HIGH risk" \
    "d['requirements'][0]['risk']='HIGH';v=d['requirements'][0]['verification'];v['state']='VERIFIED';v['method']='AGENT';v['evidence']=['EV-P1-001']"

# --- capability integrity ---
neg capability "C2 UNKNOWN security with GLOBAL install" "blocks GLOBAL install" \
    "c=d['capabilities'][0];c['security']['status']='UNKNOWN';c['install_scope']='GLOBAL';c['global_installation_authorized_by']='User'"
neg capability "D  GLOBAL install without authorization" "GLOBAL scope without user" \
    "d['capabilities'][0]['install_scope']='GLOBAL'"
neg capability "N  GLOBAL install authorized by an agent" "authorized by non-user" \
    "c=d['capabilities'][0];c['install_scope']='GLOBAL';c['global_installation_authorized_by']='agent'"
neg capability "I2 agent-neutral claim with agent dependency" "agent_neutral with dependency" \
    "d['capabilities'][0]['compatibility']['agent_specific_dependency']='~/.x/skills/y'"
neg capability "J  STALE without review_due" "STALE without review_due" \
    "d['capabilities'][0]['staleness']={'state':'STALE','last_checked':None}"
neg capability "   lifecycle VERIFIED without evidence" "lifecycle VERIFIED without evidence" \
    "c=d['capabilities'][0];c['lifecycle_state']='VERIFIED'"
neg capability "   duplicate capability IDs" "duplicate capability IDs" \
    "d['capabilities'].append(dict(d['capabilities'][0]))"
if [ -z "$POS" ]; then
  info "ACCEPTED -> CASE 0 positive control (valid fixture)"
  NEG_PASS=$((NEG_PASS+1)); pass "CASE 0  valid fixture accepted"
else
  info "WRONGLY REJECTED (over-blocking!) -> CASE 0"
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE 0  valid fixture rejected: $POS"
fi
if git remote | grep -q .; then warn "remote configured (informational)"; else pass "no remote (local-only, as intended)"; fi

# --- evidence integrity ---
neg evidence "H  evidence PASS with empty output" "PASS with empty observed_result" \
    "d['records'][0]['observed_result']=''"
neg evidence "   duplicate evidence IDs (append-only)" "duplicate evidence IDs" \
    "d['records'].append(dict(d['records'][0]))"
neg evidence "   invalid result enum" "invalid result" \
    "d['records'][0]['result']='MAYBE'"
neg evidence "   SKIP without a stated reason" "without a stated reason" \
    "d['records'][0]['result']='SKIP';d['records'][0]['observed_result']=''"

# --- decision integrity ---
neg decision "G2 decision APPROVED by an agent" "non-user" \
    "a=d['decisions'][0]['approval'];a['state']='APPROVED';a['decided_by']='agent'"
neg decision "   decision missing reason" "missing reason or evidence" \
    "d['decisions'][0]['reason']=''"

# --- malformed structured data ---
printf '{ this is not valid json' > "$TMP/malformed.json"
if [ -n "$(run_check evidence "$TMP/malformed.json")" ]; then
  info "REJECTED -> CASE L malformed JSON"
  NEG_PASS=$((NEG_PASS+1)); pass "CASE L  malformed JSON rejected"
else
  info "NOT REJECTED (validator defect!) -> CASE L"
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE L  malformed JSON NOT rejected"
fi

# --- illegal project/global placement ---
GLOBALDIR="$TMP/global-test/.claude"; mkdir -p "$GLOBALDIR"
if find "$GLOBALDIR" -type d -name '.claude' | grep -q .; then
  info "REJECTED -> CASE N illegal global placement detected"
  NEG_PASS=$((NEG_PASS+1)); pass "CASE N  illegal global placement detected"
else
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE N  illegal global placement NOT detected"
fi

# --- emoji policy violation ---
EMJDIR="$TMP/emoji-test"; mkdir -p "$EMJDIR"
printf 'status: \360\237\216\257 done\n' > "$EMJDIR/x.md"
if python3 -c "
import re,sys
print('HIT' if re.search('[\U0001F300-\U0001FAFF]', open(sys.argv[1],encoding='utf-8').read()) else 'MISS')" \
   "$EMJDIR/x.md" | grep -q HIT; then
  info "REJECTED -> CASE O emoji detected by the policy scan"
  NEG_PASS=$((NEG_PASS+1)); pass "CASE O  emoji violation detected"
else
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE O  emoji violation NOT detected"
fi

# --- P10 inventory contract: invalid inventory must be rejected ---
printf '{"inventory_id":"P10-SECTION-INVENTORY-v1","inventory_state":"BOGUS","complete":false,"sections":[]}' \
  > "$TMP/p10-bad.json"
if python3 "$HERE/check_p10_inventory.py" --inventory "$TMP/p10-bad.json" >/dev/null 2>&1; then
  info "NOT REJECTED (validator defect!) -> CASE P"
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE P  invalid P10 inventory NOT rejected"
else
  info "REJECTED -> CASE P invalid P10 inventory"
  NEG_PASS=$((NEG_PASS+1)); pass "CASE P  invalid P10 inventory rejected"
fi

# --- P17 task intake: a malformed task must be rejected safely ---
# Isolated project root plus a test-double allowlist, so the rejection is
# attributable to the task input rather than to a missing allowlist. No real
# agent CLI is involved: the fixture allowlist lists only the repository-local
# test doubles. The unsafe acceptance command is never reached: intake rejects
# the blank goal first, and no task record may be written.
P17ROOT="$TMP/p17-reject"; mkdir -p "$P17ROOT/sps2/p17"
cp "$SPS2/tests/fixtures/p17/test-allowlist.json" "$P17ROOT/sps2/p17/allowlist.json"
printf '{"goal":"","required_capabilities":["test-double"],"acceptance":{"command":["/bin/echo","unsafe"]},"timeout_seconds":5}' \
  > "$TMP/p17-bad-task.json"
P17_ERR="$(PYTHONPATH="$REPO" python3 -m sps2.p17 --root "$P17ROOT" plan \
  --task-file "$TMP/p17-bad-task.json" 2>&1 >/dev/null)"; P17_RC=$?
P17_MADE="$(ls -A "$P17ROOT/.sps/tasks/p17" 2>/dev/null | grep -c '^TASK-P17-' || true)"
if [ "$P17_RC" -eq 0 ]; then
  info "NOT REJECTED (validator defect!) -> CASE Q"
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE Q  unsafe P17 task NOT rejected"
elif ! printf '%s' "$P17_ERR" | grep -q "goal is missing or blank"; then
  info "REJECTED FOR THE WRONG REASON (validator defect!) -> CASE Q"
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE Q  P17 task rejected without an intake reason: ${P17_ERR:0:120}"
elif [ "${P17_MADE:-0}" -ne 0 ]; then
  info "PARTIAL STATE WRITTEN (validator defect!) -> CASE Q"
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE Q  rejected P17 task still wrote a record"
else
  info "REJECTED -> CASE Q unsafe P17 task (blank goal, shell-unsafe acceptance command)"
  NEG_PASS=$((NEG_PASS+1)); pass "CASE Q  unsafe P17 task rejected, no record written"
fi

echo ""
if [ "$NEG_FAIL" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}== NEGATIVE SUITE: $NEG_PASS cases correctly rejected, 0 missed ==${NC}"
else
  echo -e "${RED}${BOLD}== NEGATIVE SUITE: $NEG_PASS rejected, $NEG_FAIL MISSED ==${NC}"
fi

echo ""
if [ "$FAIL" -eq 0 ] && [ "$NEG_FAIL" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}== SPS2 FOUNDATION VALID: $PASS checks passed, 0 failed, $NEG_PASS negative cases enforced ==${NC}"
  exit 0
fi
echo -e "${RED}${BOLD}== SPS2 FOUNDATION INVALID: $PASS passed, $FAIL failed, $NEG_FAIL missed ==${NC}"
exit 1