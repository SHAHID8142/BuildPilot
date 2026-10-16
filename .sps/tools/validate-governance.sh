#!/usr/bin/env bash
# SPS governance validator — READ-ONLY.
#
# Verifies that project governance records are internally consistent.
#
# SAFETY CONTRACT (deliberate):
#   - makes NO network requests
#   - runs NO installer / uninstaller / updater
#   - writes NO files and NO machine-global state
#   - changes NO git configuration
#   Only reads files under .sps/ and runs `git` in read-only query mode.
#
# Usage:  bash .sps/tools/validate-governance.sh
# Exit:   0 = all checks passed | 1 = validation failure | 2 = tooling unavailable

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT" || exit 2

SPS=".sps"
EV="$SPS/evidence/PHASE-02-EVIDENCE.json"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'

PASS=0; FAIL=0
pass() { echo -e "  ${GREEN}PASS${NC}  $*"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}FAIL${NC}  $*"; FAIL=$((FAIL+1)); }
warn() { echo -e "  ${YELLOW}WARN${NC}  $*"; }
sect() { echo -e "\n${BOLD}$*${NC}"; }

echo -e "${BOLD}SPS Governance Validator${NC}"
echo -e "${DIM}read-only; no network, no installs, no writes${NC}"
echo -e "${DIM}root: $ROOT${NC}"

# ── tooling ───────────────────────────────────────────────────────────────────
command -v git >/dev/null 2>&1 || { echo "git unavailable"; exit 2; }
if command -v jq >/dev/null 2>&1; then JSON_ENGINE="jq"
elif command -v python3 >/dev/null 2>&1; then JSON_ENGINE="python3"
else echo "neither jq nor python3 available"; exit 2; fi
echo -e "${DIM}json engine: $JSON_ENGINE${NC}"

# Check helper. Runs the entire evidence-contract check set in ONE Python pass so
# the same logic works whether or not jq is installed (jq and python syntax for
# these queries are not interchangeable, so a single engine avoids dialect bugs).
check_evidence_contract() {
python3 - "$EV" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
recs = d.get('records', [])
req = ['id','task','requirement','command','expected','actual',
       'result','timestamp','test','maturity']
res_enum = {'PASS','FAIL','SKIP','BLOCKED','PENDING'}
mat_enum = {'DECLARED','IMPLEMENTED','VERIFIED','USER_APPROVED'}
fails = []
out = []
for f in req:
    n = sum(1 for r in recs if f not in r)
    out.append(('field:' + f, f"all records have '{f}'" if n == 0 else f"{n} record(s) missing '{f}'", n == 0))
n = sum(1 for r in recs if r.get('result') not in res_enum)
out.append(('result-enum', 'all result values within enum' if n == 0 else f"{n} invalid result value(s)", n == 0))
n = sum(1 for r in recs if r.get('maturity') not in mat_enum)
out.append(('maturity-enum', 'all maturity values within enum' if n == 0 else f"{n} invalid maturity value(s)", n == 0))
n = sum(1 for r in recs if r.get('result') == 'PASS' and not r.get('actual'))
out.append(('pass-has-output', 'every PASS record has real captured output' if n == 0 else f"{n} PASS record(s) have empty 'actual'", n == 0))
n = sum(1 for r in recs if r.get('result') in ('SKIP','BLOCKED') and len(r.get('actual') or '') < 20)
out.append(('skip-has-reason', 'every SKIP/BLOCKED record states a reason' if n == 0 else f"{n} SKIP/BLOCKED record(s) lack a stated reason", n == 0))
import re
bad = [r.get('task') for r in recs if not re.fullmatch(r'PHASE-02-T\d\d', str(r.get('task','')))]
out.append(('task-refs', 'all evidence task refs match PHASE-02-TNN' if not bad else f"{len(bad)} unknown task ref(s): {sorted(set(bad))}", not bad))
dup = [i for i in set(r.get('id') for r in recs)
       if sum(1 for r in recs if r.get('id') == i) > 1]
out.append(('unique-ids', 'all evidence IDs unique' if not dup else f"duplicate IDs: {dup}", not dup))
for key, msg, ok in out:
    print(('OK' if ok else 'ERR') + '\t' + msg)
PY
}

# ── 1. required structure ─────────────────────────────────────────────────────
sect "1. Governance structure"
for f in "$SPS/STATE.md" "$SPS/GOVERNANCE.md" "$SPS/SCHEMA.md" \
         "$SPS/tasks/PHASE-02-TASKS.md" "$EV" \
         "$SPS/decisions/DEC-0001-git-init-no-remote.md" \
         "$SPS/decisions/DEC-0002-local-git-identity.md" \
         "$SPS/handoff/HANDOFF-CURRENT.md" "$SPS/audits/README.md"; do
  [ -f "$f" ] && pass "exists $f" || fail "missing $f"
done

# ── 2. JSON well-formedness ───────────────────────────────────────────────────
sect "2. Evidence JSON well-formedness"
if [ "$JSON_ENGINE" = "jq" ]; then
  jq empty "$EV" 2>/dev/null && pass "$EV parses as JSON" || fail "$EV is not valid JSON"
else
  python3 -c "import json;json.load(open('$EV'))" 2>/dev/null \
    && pass "$EV parses as JSON" || fail "$EV is not valid JSON"
fi

# ── 3 + 4. evidence contract and honesty rules ───────────────────────────────
sect "3. Evidence record contract"
sect "4. Honesty rules"
CONTRACT_OUT="$(check_evidence_contract)"
if [ -z "$CONTRACT_OUT" ]; then
  fail "evidence contract checker produced no output"
else
  while IFS=$'\t' read -r kind msg; do
    [ "$kind" = "OK" ] && pass "$msg" || fail "$msg"
  done <<< "$CONTRACT_OUT"
fi

# ── 5. traceability chain ────────────────────────────────────────────────────
sect "5. Traceability"
chain_ok=1
for id in PHASE-02-T01 PHASE-02-T02 PHASE-02-T03 PHASE-02-T04 PHASE-02-T05 \
          PHASE-02-T06 PHASE-02-T07 PHASE-02-T08 PHASE-02-T09 PHASE-02-T10; do
  grep -q "$id" "$SPS/tasks/PHASE-02-TASKS.md" 2>/dev/null || { fail "$id not in task register"; chain_ok=0; }
done
[ "$chain_ok" = "1" ] && pass "all 10 tasks present in the task register"

for id in DEC-0001 DEC-0002; do
  grep -rq "$id" "$SPS/decisions/" 2>/dev/null && pass "$id decision record exists" || fail "$id missing"
done

# ── 6. approval discipline ───────────────────────────────────────────────────
# DESIGN NOTE (revised after genuine user approval on 2026-10-03):
#   The previous rule was "no decided_by/approved_by may ever be populated".
#   That was correct while every approval was pending, but it made recording a
#   REAL user approval impossible - it would have failed the build.
#   The rule is now stronger, not weaker: an approval is valid ONLY when it is
#   attributed to an identifiable USER. An approval attributed to an agent, a
#   model, or a self-reference is rejected. Absence of an approval remains valid
#   (pending state); a FAKE approval is not.
sect "6. Approval discipline"

STATE_APPROVAL="$(grep -E '^\|[[:space:]]*\*\*Approval\*\*[[:space:]]*\|' "$SPS/STATE.md" \
  | grep -oE 'AWAITING_USER_APPROVAL|PENDING_USER_APPROVAL|APPROVED|REJECTED' | head -1 || true)"
CURRENT_PHASE="$(grep -E '^\|[[:space:]]*Phase ID[[:space:]]*\|' "$SPS/STATE.md" \
  | grep -oE 'PHASE-[0-9]+' | head -1 || true)"
case "$STATE_APPROVAL" in
  APPROVED)
    pass "STATE.md records $CURRENT_PHASE as APPROVED"
    # An APPROVED phase MUST carry an explicit, attributable user decision.
    # NOTE: every decision record must be individually attributed. Checking only
    # that *some* record is attributed would let one file mask another's gap -
    # a real bug found by negative test EV-P02-017.
    attributed=0
    total=0
    for d in "$SPS/decisions/"*.md; do
      [ -e "$d" ] || continue
      total=$((total+1))
      if grep -qE '\*\*Decided by:\*\*[[:space:]]*User' "$d"; then
        attributed=$((attributed+1))
      else
        fail "$(basename "$d") is APPROVED but not attributed to the User"
      fi
    done
    [ "$attributed" -eq "$total" ] && [ "$total" -gt 0 ] \
      && pass "all $total APPROVED decision records are attributed to the User"
    ;;
  AWAITING_USER_APPROVAL|PENDING_USER_APPROVAL)
    pass "STATE.md records $CURRENT_PHASE as awaiting user approval"
    ;;
  REJECTED)
    pass "STATE.md records $CURRENT_PHASE as rejected"
    ;;
  *)
    fail "STATE.md has no recognisable approval state (found: '${STATE_APPROVAL:-none}')"
    ;;
esac

# Reject approvals attributed to an agent/model rather than a human.
  # SPEC-2: agent attribution is judged by the single authoritative policy
  # (sps2/governance/attribution_policy.json) via attribution.py, never by a
  # local grep alternation.
  #
  # THREE-WAY EXIT CONTRACT - this control is fail-CLOSED:
  #   0 = scan completed, nothing found            -> pass
  #   1 = scan completed, agent name found         -> fail
  #   2 = scan could not run (policy unavailable)  -> fail, never "pass"
  # A bare `if VAR="$(helper)"; then fail; else pass; fi` collapses cases 1 and 2
  # into the same branch; that is exactly the defect this control previously had
  # (its grep exited 2 on an invalid ERE and always took the pass branch).
  agent_flagged_md() {
    python3 - "$SPS" <<'PYEOF'
import os, re, sys
try:
    sys.path.insert(0, os.path.join(os.getcwd(), 'sps2', 'governance'))
    import attribution as ATTR
except Exception as exc:
    # Exit 2 = the control could not run. It must never be read as 'clean'.
    sys.stderr.write('canonical attribution policy unavailable: %s\n' % exc)
    sys.exit(2)
rx = re.compile(r'Decided by:?\*\*([^\n]*)')
for base, _, files in os.walk(sys.argv[1]):
    for f in files:
        if not f.endswith(('.md', '.json')):
            continue
        try:
            txt = open(os.path.join(base, f), encoding='utf-8', errors='ignore').read()
        except OSError:
            continue
        for m in rx.finditer(txt):
            if ATTR.AGENTISH.search(m.group(1)):
                print(os.path.join(base, f))
                sys.exit(1)
sys.exit(0)
PYEOF
  }
  agent_flagged_json() {
    python3 - "$SPS" <<'PYEOF'
import os, re, sys
try:
    sys.path.insert(0, os.path.join(os.getcwd(), 'sps2', 'governance'))
    import attribution as ATTR
except Exception as exc:
    # Exit 2 = the control could not run. It must never be read as 'clean'.
    sys.stderr.write('canonical attribution policy unavailable: %s\n' % exc)
    sys.exit(2)
rx = re.compile(r'\"(?:decided_by|approved_by)\"\s*:\s*\"([^\"]*)\"')
for base, _, files in os.walk(sys.argv[1]):
    for f in files:
        if not f.endswith('.json'):
            continue
        try:
            txt = open(os.path.join(base, f), encoding='utf-8', errors='ignore').read()
        except OSError:
            continue
        for m in rx.finditer(txt):
            if ATTR.AGENTISH.search(m.group(1)):
                print(os.path.join(base, f))
                sys.exit(1)
sys.exit(0)
PYEOF
  }

  # Reject approvals attributed to an agent/model rather than a human.
  AGENT_MD="$(agent_flagged_md)"; _rc=$?
  case "$_rc" in
    0) if [ -n "$AGENT_MD" ]; then
         fail "agent attribution scan reported a hit with no path: $AGENT_MD"
       else
         pass "no approval is attributed to an agent, model, or bot"
       fi ;;
    1) fail "an approval is attributed to an agent/model - only the User may approve: $AGENT_MD" ;;
    *) fail "agent-attribution markdown control could not run (exit $_rc) - canonical policy unavailable" ;;
  esac

  # JSON approval records must not name an agent. SPEC-2: this control previously
  # used the POSIX-ERE negative lookahead '(?!User)', which BSD grep cannot
  # compile; grep exited 2, the non-zero status selected the pass branch, and the
  # control therefore never enforced anything. It is replaced by the canonical
  # policy applied to JSON approval fields, which is what its own message claimed,
  # under the same three-way fail-closed contract.
  AGENT_JSON="$(agent_flagged_json)"; _rc=$?
  case "$_rc" in
    0) if [ -n "$AGENT_JSON" ]; then
         fail "JSON agent scan reported a hit with no path: $AGENT_JSON"
       else
         pass "no JSON approval field is self-populated by an agent"
       fi ;;
    1) fail "a JSON decided_by/approved_by names an agent: $AGENT_JSON" ;;
    *) fail "JSON agent-attribution control could not run (exit $_rc) - canonical policy unavailable" ;;
  esac

# Decision records belonging to the CURRENT phase must be resolved.
#
# Scoped deliberately: a phase that is itself awaiting approval may legitimately
# carry PENDING decisions (they are part of what is awaiting approval). Only
# decisions from an APPROVED phase must be resolved. Before this scoping the rule
# was implicitly Phase-02-specific and broke as soon as Phase 03 opened - a real
# defect found by re-running the Phase 02 validator after Phase 03 work began.
for d in "$SPS/decisions/"*.md; do
  [ -e "$d" ] || continue
  b="$(basename "$d")"
  # Which phase does this decision belong to?
  dphase="$(grep -E '\*\*Phase / Task:\*\*' "$d" | grep -oE 'PHASE-[0-9]+' | head -1 || true)"
  is_pending=0
  grep -qE '^-[[:space:]]*\*\*Approval:\*\*[[:space:]]*`(PENDING_USER_APPROVAL|AWAITING_USER_APPROVAL)`' "$d" && is_pending=1
  # A decision raised inside a phase that is ITSELF still awaiting approval is
  # legitimately pending - it is part of what the user is being asked to approve.
  # Only a decision belonging to an already-APPROVED phase must be resolved.
  if [ "$STATE_APPROVAL" = "APPROVED" ] && [ "$dphase" != "$CURRENT_PHASE" ]; then
    if [ "$is_pending" = "1" ]; then
      fail "$b still PENDING but $dphase is approved - decisions must be resolved"
    else
      pass "$b is in a resolved approval state"
    fi
  elif [ "$is_pending" = "1" ]; then
    pass "$b is PENDING within ${dphase:-current} - awaiting approval (correct)"
  else
    pass "$b is in a resolved approval state"
  fi
done

# ── 7. secret hygiene in governance files ────────────────────────────────────
sect "7. Governance secret hygiene"
HITS=$(grep -rInE "(api[_-]?key|secret|password|token)[[:space:]]*[:=][[:space:]]*[\"'][^\"']{16,}[\"']" \
       "$SPS/STATE.md" "$SPS/GOVERNANCE.md" "$SPS/SCHEMA.md" \
       "$SPS/tasks/PHASE-02-TASKS.md" "$EV" \
       "$SPS/decisions/"*.md "$SPS/handoff/HANDOFF-CURRENT.md" "$SPS/audits/README.md" 2>/dev/null | wc -l | tr -d ' ')
[ "$HITS" = "0" ] && pass "no secret-shaped literals in governance files" \
                 || fail "$HITS potential secret literal(s) in governance files"

# ── 8. git safety (read-only queries only) ───────────────────────────────────
sect "8. Git provenance (read-only)"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  pass "working tree is a Git repository"
  BR=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  [ -n "$BR" ] && pass "active branch: $BR" || warn "could not read branch"
  N=$(git rev-list --count HEAD 2>/dev/null || echo 0)
  { [ "$N" -ge 1 ] 2>/dev/null; } && pass "commit count: $N" || fail "no commits found"
  if git remote | grep -q .; then
    pass "remote(s) configured: $(git remote | tr '\n' ' ')"
  else
    warn "REMOTE_NOT_CONFIGURED (documented; not an error)"
  fi
else
  fail "not a Git repository - Phase 02 provenance missing"
fi

# ── 9. ignore-rule behaviour ─────────────────────────────────────────────────
sect "9. Ignore-rule behaviour"
for probe in .env .env.local app.pem id_rsa secret.p12; do
  git check-ignore -q "$probe" 2>/dev/null && pass "ignored: $probe" || fail "NOT ignored: $probe"
done
for probe in README.md install.sh skills/sps/SKILL.md .sps/STATE.md; do
  git check-ignore -q "$probe" 2>/dev/null && fail "WRONGLY ignored: $probe" || pass "tracked OK: $probe"
done

# ── summary ──────────────────────────────────────────────────────────────────
echo ""
if [ "$FAIL" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}== GOVERNANCE VALID: $PASS checks passed, 0 failed ==${NC}"
  exit 0
fi
echo -e "${RED}${BOLD}== GOVERNANCE INVALID: $PASS passed, $FAIL failed ==${NC}"
exit 1
[ "$n" = "0" ] && pass "all maturity values within enum" || fail "$n invalid maturity value(s)"