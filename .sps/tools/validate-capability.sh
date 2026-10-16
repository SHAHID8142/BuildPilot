#!/usr/bin/env bash
# SPS capability validator — Phase 04.
# Proves that INVALID CAPABILITY STATES ARE REJECTED.
#
# SAFETY: no network, no installs, no discovery, no global writes.
# Writes only inside a self-managed temp dir (removed on exit).
#
# Usage: bash .sps/tools/validate-capability.sh [--negative]
# Exit:  0 = valid | 1 = failure | 2 = tooling unavailable

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT" || exit 2

CAP=".sps/capability"
REG=".sps/capability/registry/PHASE-04-CAPABILITIES.json"
RES=".sps/research/PHASE-04-RESEARCH.json"

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[1;34m'
BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'
PASS=0; FAIL=0
pass() { echo -e "  ${GREEN}PASS${NC}  $*"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}FAIL${NC}  $*"; FAIL=$((FAIL+1)); }
info() { echo -e "  ${BLUE}CASE${NC} $*"; }
sect() { echo -e "\n${BOLD}$*${NC}"; }

command -v git >/dev/null 2>&1 || { echo "git unavailable"; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "python3 unavailable"; exit 2; }

TMP="$(mktemp -d "${TMPDIR:-/tmp}/sps-cap-XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

echo -e "${BOLD}SPS Capability Validator (Phase 04)${NC}"
echo -e "${DIM}no network, no installs, no discovery, no global writes${NC}"

check_registry() {
python3 - "$1" "$2" <<'PY'
import json, os, sys, re
path, research_path = sys.argv[1], sys.argv[2]
try:
    d = json.load(open(path))
except Exception as e:
    print("ERR\tnot valid JSON: %s" % e); sys.exit(0)
try:
    research = json.load(open(research_path))
except Exception:
    research = {"entries": []}
ready = {e.get("research_id"): (e.get("readiness") == "SUFFICIENT")
         for e in research.get("entries", [])}

try:
    sys.path.insert(0, os.path.join(os.getcwd(), 'sps2', 'governance'))
    import attribution as ATTR
except Exception as exc:
    print('ERR\tcanonical attribution policy unavailable: %s' % exc)
    raise SystemExit(1)
# SPEC-2: tokens come from the single authoritative policy; no local list.
SAFE = {"VERIFIED_SAFE", "REVIEWED_LOW_RISK"}
LIFE = ["DISCOVERED", "RESEARCHING", "EVALUATED", "PROPOSED", "PENDING_USER_APPROVAL",
        "APPROVED", "INSTALLING", "INSTALLED", "VERIFIED", "ACTIVE", "DEPRECATED",
        "REJECTED", "FAILED", "REMOVED"]

for c in d.get("capabilities", []):
    cid = c.get("capability_id", "<no id>")
    if not re.fullmatch(r'CAP-P\d\d-\d\d\d', str(cid)):
        print("ERR\t%s: capability_id does not match CAP-PNN-NNN" % cid); continue

    prov = c.get("provenance")
    if not prov or not prov.get("requirement"):
        print("ERR\t%s: missing provenance (requirement) - CASE A" % cid); continue
    if not c.get("source") or c.get("source") == "unknown":
        print("ERR\t%s: missing source - CASE B" % cid); continue

    ss = c.get("security_status")
    if ss not in {"VERIFIED_SAFE", "REVIEWED_LOW_RISK", "SUSPECTED_RISK",
                  "VULNERABLE", "UNKNOWN"}:
        print("ERR\t%s: invalid security_status %r" % (cid, ss)); continue
    if ss == "UNKNOWN" and c.get("security_assumed_safe") in SAFE:
        print("ERR\t%s: UNKNOWN security rendered as %r - CASE C"
              % (cid, c.get("security_assumed_safe"))); continue
    if ss in {"SUSPECTED_RISK", "VULNERABLE"} and c.get("install_scope") != "PROJECT_LOCAL":
        print("ERR\t%s: security %s but scope %s" % (cid, ss, c.get("install_scope"))); continue

    if c.get("install_scope") == "GLOBAL":
        who = (c.get("global_installation_authorized_by") or "").strip()
        if not who:
            print("ERR\t%s: install_scope GLOBAL without authorization - CASE D/N" % cid); continue
        if ATTR.AGENTISH.search(who):
            print("ERR\t%s: global install authorized by non-user %r - CASE D/N"
                  % (cid, who)); continue

    life = c.get("lifecycle_state")
    if life not in LIFE:
        print("ERR\t%s: invalid lifecycle_state %r" % (cid, life)); continue

    if LIFE.index(life) >= LIFE.index("EVALUATED"):
        ev = c.get("evaluation")
        if not ev or not ev.get("criteria") or not ev.get("selection_reason"):
            print("ERR\t%s: lifecycle %s without evaluation - CASE E" % (cid, life)); continue

    rid = c.get("research_id") or (c.get("provenance") or {}).get("research")
    if LIFE.index(life) >= LIFE.index("PROPOSED") and rid not in ready:
        print("ERR\t%s: research %r not SUFFICIENT - CASE F" % (cid, rid)); continue

    if c.get("approval_status") == "APPROVED":
        who = (c.get("approval_decided_by") or "").strip()
        if not who:
            print("ERR\t%s: APPROVED without a decider - CASE G" % cid); continue
        if ATTR.AGENTISH.search(who):
            print("ERR\t%s: APPROVED attributed to non-user %r - CASE G" % (cid, who)); continue

    if life in ("VERIFIED", "ACTIVE") and not (c.get("evidence") or []):
        print("ERR\t%s: lifecycle %s without evidence - CASE H" % (cid, life)); continue

    if c.get("agent_compatibility") == "AGENT_NEUTRAL" and c.get("agent_specific_dependency"):
        print("ERR\t%s: claims AGENT_NEUTRAL but depends on %r - CASE I"
              % (cid, c.get("agent_specific_dependency"))); continue

    if c.get("staleness") == "STALE" and c.get("presented_as_current") in (True, "true"):
        print("ERR\t%s: STALE presented as current - CASE J" % cid); continue

    fc = c.get("fact_class")
    if fc not in {"FACT", "EVIDENCE", "INFERENCE", "UNKNOWN"}:
        print("ERR\t%s: invalid fact_class %r" % (cid, fc)); continue
    if c.get("presented_as") == "known" and (fc == "UNKNOWN" or c.get("version") == "UNKNOWN"):
        print("ERR\t%s: UNKNOWN presented as known - CASE K" % cid); continue

    m = c.get("mcp")
    if m and c.get("type") == "MCP":
        tl = m.get("trust_level")
        if tl in ("UNTRUSTED", "UNKNOWN") and c.get("install_scope") != "PROJECT_LOCAL":
            print("ERR\t%s: MCP trust %s blocks install - CASE L" % (cid, tl)); continue

    if life == "ACTIVE" and c.get("replaces_active") and c.get("approval_status") != "APPROVED":
        print("ERR\t%s: replaces ACTIVE capability without approval - CASE M" % cid); continue

    print("OK\t%s satisfies the capability contract" % cid)
PY
}

# ── main ──────────────────────────────────────────────────────────────────────
NEG_ONLY=false
for a in "$@"; do [ "$a" = "--negative" ] && NEG_ONLY=true; done

if [ "$NEG_ONLY" != true ]; then
sect "1. Capability architecture files present"
for f in "$CAP/CAPABILITY-MODEL.md" "$CAP/SECURITY.md" "$CAP/PROVENANCE.md" \
         "$REG" "$RES"; do
  [ -f "$f" ] && pass "exists $f" || fail "missing $f"
done

sect "2. Model documents required concepts"
req() { grep -rqE "$2" "$CAP/$1" 2>/dev/null && pass "$1 mentions $3" || fail "$1 missing $3"; }
req CAPABILITY-MODEL.md 'SKILL-GOVERNANCE|only default taste operator' 'audit of hardcoded routing'
req CAPABILITY-MODEL.md 'DISCOVERED'        'lifecycle start state'
req CAPABILITY-MODEL.md 'PENDING_USER_APPROVAL' 'approval state'
req CAPABILITY-MODEL.md '`FACT`'            'FACT claim class'
req CAPABILITY-MODEL.md '`INFERENCE`'       'INFERENCE claim class'
req CAPABILITY-MODEL.md '`UNKNOWN`'         'UNKNOWN claim class'
req CAPABILITY-MODEL.md 'emoji|icon librar' 'no-emoji rule'
req CAPABILITY-MODEL.md 'review_due'        'staleness mechanism'
req SECURITY.md 'unknown security status is not a safe' 'UNKNOWN-is-unsafe rule'
req SECURITY.md 'MCP'                      'MCP evaluation contract'
req SECURITY.md 'install LOCALLY|project-local method|Project-Local' 'project-local activation rule'
req PROVENANCE.md 'runtime provenance tracking is' 'provenance honesty'
req PROVENANCE.md 'RSCH-P04'               'research cache'
req PROVENANCE.md 'agent_specific|agent-neutral' 'agent interop'
req PROVENANCE.md 'Shadow-run|shadow'      'migration plan'

sect "3. Schema defines Phase 04 contracts"
for s in 'Capability Contract' 'Research Contract' 'MCP Contract' \
         'Project-Local Installation Contract'; do
  grep -q "$s" .sps/SCHEMA.md && pass "SCHEMA.md defines $s" || fail "SCHEMA.md missing $s"
done

sect "4b. Requirement approval integrity (JSON)"
# The approval-discipline checks elsewhere scan Markdown decision records and
# registry capability records. Requirement JSON files carry their own
# approval_decided_by field and were NOT covered - a real gap found by negative
# test T2 during the Phase 04 approval transition.
for rq in .sps/requirements/*.json; do
  [ -e "$rq" ] || continue
  OUT2="$(python3 - "$rq" <<'PY'
import json, os, sys
try:
    sys.path.insert(0, os.path.join(os.getcwd(), 'sps2', 'governance'))
    import attribution as ATTR  # SPEC-2: single authoritative policy
except Exception as exc:
    # Without the policy this control cannot run. Say so; do not go quiet:
    # an empty OUT2 used to fall through every branch and record nothing.
    sys.stderr.write('canonical attribution policy unavailable: %s\n' % exc)
    raise SystemExit(2)
AGENT = ATTR.AGENTISH
d = json.load(open(sys.argv[1]))
errs = []
for r in d.get('requirements', []):
    rid = r.get('requirement_id', '<no id>')
    if r.get('approval_status') == 'APPROVED':
        who = (r.get('approval_decided_by') or '').strip()
        if not who:
            errs.append("%s: APPROVED with no approval_decided_by" % rid)
        elif AGENT.search(who):
            errs.append("%s: APPROVED attributed to non-user %r" % (rid, who))
        if not r.get('approved_at'):
            errs.append("%s: APPROVED without approved_at" % rid)
print("\n".join(errs) if errs else "CLEAN")
PY
)"
  _rc4b=$?
  if [ "$_rc4b" -ne 0 ]; then
    fail "$rq: requirement-approval control could not run (exit $_rc4b) - canonical policy unavailable"
  elif [ "$OUT2" = "CLEAN" ]; then
    pass "$rq: requirement approvals are properly attributed"
  elif [ -z "$OUT2" ]; then
    fail "$rq: requirement-approval control produced no output - refusing to pass"
  else
    while IFS= read -r line; do
      [ -n "$line" ] && fail "$rq: $line"
    done <<< "$OUT2"
  fi
done

sect "5. Registry and research cache integrity"
for j in "$REG" "$RES"; do
  python3 -c "import json;json.load(open('$j'))" 2>/dev/null \
    && pass "$j is valid JSON" || fail "$j is not valid JSON"
done
NCAP=$(python3 -c "import json;print(len(json.load(open('$REG'))['capabilities']))")
NRES=$(python3 -c "import json;print(len(json.load(open('$RES'))['entries']))")
pass "registry holds $NCAP capabilities (mechanism only, no fabrication)"
pass "research cache holds $NRES entries (mechanism only, no fabrication)"

sect "5. Registry records satisfy the capability contract"
OUT="$(check_registry "$REG" "$RES")"
NCAP_REG=$(python3 -c "import json;print(len(json.load(open('$REG'))['capabilities']))" 2>/dev/null || echo -1)
if [ "$NCAP_REG" -eq 0 ]; then
  # An empty registry is VALID in Phase 04: the mechanism exists, nothing is fabricated.
  pass "registry is empty (mechanism only) - nothing to validate yet"
elif echo "$OUT" | grep -q '^ERR'; then
  while IFS=$'\t' read -r kind msg; do
    [ "$kind" = "OK" ] && pass "$msg" || fail "$msg"
  done <<< "$OUT"
elif [ -z "$OUT" ]; then
  fail "registry has $NCAP_REG capabilities but the checker produced no output"
else
  while IFS=$'\t' read -r kind msg; do
    [ "$kind" = "OK" ] && pass "$msg" || fail "$msg"
  done <<< "$OUT"
fi

sect "6. Scope discipline (Phase 04 must not install or change machine-global state)"
for probe in skills/sps/SKILL-ROUTER.md skills/sps/SKILL-GOVERNANCE.md install.sh \
             skills/sps-cms/templates/auth/auth-helper.ts; do
  if [ -n "$(git diff --name-only HEAD -- "$probe" 2>/dev/null)" ]; then
    fail "MODIFIED out-of-scope file: $probe"
  else
    pass "untouched (out of scope): $probe"
  fi
done
if git remote | grep -q .; then fail "a remote was configured - forbidden in Phase 04"
else pass "no remote configured (unchanged)"; fi

sect "7. Phase 04 state"
grep -q 'AWAITING_USER_APPROVAL' .sps/STATE.md 2>/dev/null \
  && pass "STATE.md records Phase 04 as AWAITING_USER_APPROVAL" \
  || fail "STATE.md does not record AWAITING_USER_APPROVAL"
  # SPEC-2: agent attribution is judged by the single authoritative policy
  # (sps2/governance/attribution_policy.json) via attribution.py, never by a
  # local grep alternation.
  #
  # THREE-WAY EXIT CONTRACT - this control is fail-CLOSED:
  #   0 = scan completed, nothing found            -> pass
  #   1 = scan completed, agent name found         -> fail
  #   2 = scan could not run (policy unavailable)  -> fail, never "pass"
  # A bare `if cmd; then fail; else pass; fi` collapses 1 and 2 into one branch.
  python3 - <<'PY' > /dev/null 2>&1
import os, re, sys
try:
    sys.path.insert(0, os.path.join(os.getcwd(), 'sps2', 'governance'))
    import attribution as ATTR
except Exception as exc:
    # Exit 2 = the control could not run. It must never be read as 'clean'.
    sys.stderr.write('canonical attribution policy unavailable: %s\n' % exc)
    sys.exit(2)
rx = ATTR.AGENTISH
for root, _, files in os.walk('.sps'):
    for f in files:
        if not f.endswith(('.md', '.json')):
            continue
        try:
            txt = open(os.path.join(root, f), encoding='utf-8', errors='ignore').read()
        except OSError:
            continue
        for m in re.finditer(r'Decided by:?\*\*([^\n]*)', txt):
            if rx.search(m.group(1)):
                sys.exit(1)
sys.exit(0)
PY
  _rc=$?
  case "$_rc" in
    0) pass "no approval is attributed to an agent" ;;
    1) fail "an approval is attributed to an agent - only the User may approve" ;;
    *) fail "agent-attribution control could not run (exit $_rc) - canonical policy unavailable" ;;
  esac
fi  # end structural

# ══ NEGATIVE SUITE — CASE A..N ═══════════════════════════════════════════════
sect "NEGATIVE TESTS (CASE A-N) — invalid capability states must be rejected"

NEG_PASS=0; NEG_FAIL=0
run_case() {
  local label="$1" expect="$2" file="$3" out
  out="$(check_registry "$file" "$RESFIX" 2>&1)"
  if printf '%s' "$out" | grep -q '^ERR' && printf '%s' "$out" | grep -qiE "$expect"; then
    info "REJECTED as required -> $label"
    NEG_PASS=$((NEG_PASS+1)); pass "$label -> rejected"
  else
    info "NOT REJECTED (validator defect!) -> $label"
    NEG_FAIL=$((NEG_FAIL+1)); fail "$label -> NOT rejected (out: ${out:-none})"
  fi
}

# A valid baseline capability, mutated one way per case.
mkcap() { python3 .sps/tools/.cap-fixture.py "$1" > "$2"; }

python3 - "$RES" "$TMP" <<'PY'
import json, sys
res, tmp = sys.argv[1], sys.argv[2]
d = json.load(open(res))
d["entries"].append({"research_id": "RSCH-P04-900", "subject": "fixture",
  "subject_type": "CAPABILITY", "researched_at": "2026-10-03T00:00:00Z",
  "readiness": "SUFFICIENT", "version_checked": "1.0.0",
  "sources": [{"rank": 2, "type": "OFFICIAL_REPO",
               "url": "https://example.invalid",
               "accessed_at": "2026-10-03T00:00:00Z"}],
  "covered": {k: "COVERED" for k in ["official_documentation","current_version",
    "compatibility","ecosystem","recommended_practices","security_considerations",
    "relevant_tooling","mcp_tool_availability","testing_approach",
    "deployment_implications"]},
  "conclusions": [], "uncertainties": [], "decisions": [], "evidence": []})
json.dump(d, open(tmp + "/res.json", "w"))
PY
RESFIX="$TMP/res.json"

mkcap "pass" "$TMP/base.json"
# CASE 0 (positive control): a VALID capability MUST be accepted.
# Guards against a validator that rejects everything.
BASE_OUT="$(check_registry "$TMP/base.json" "$RESFIX" 2>&1)"
if echo "$BASE_OUT" | grep -q '^OK'; then
  info "ACCEPTED as required -> CASE 0 valid baseline capability"
  NEG_PASS=$((NEG_PASS+1)); pass "CASE 0  valid baseline accepted (positive control)"
else
  info "WRONGLY REJECTED (over-blocking validator!) -> CASE 0"
  NEG_FAIL=$((NEG_FAIL+1)); fail "CASE 0  valid baseline rejected (out: ${BASE_OUT:-none})"
fi

mkcap "c.pop('provenance')" "$TMP/A.json"
run_case "CASE A  capability without provenance" "CASE A" "$TMP/A.json"

mkcap "c['source']='unknown'" "$TMP/B.json"
run_case "CASE B  capability without source" "CASE B" "$TMP/B.json"

mkcap "c['security_status']='UNKNOWN';c['security_assumed_safe']='VERIFIED_SAFE'" "$TMP/C.json"
run_case "CASE C  UNKNOWN security rendered SAFE" "CASE C" "$TMP/C.json"

mkcap "c['install_scope']='GLOBAL'" "$TMP/D.json"
run_case "CASE D  global install unauthorized" "CASE D" "$TMP/D.json"

mkcap "c['lifecycle_state']='PROPOSED';c.pop('evaluation')" "$TMP/E.json"
run_case "CASE E  selection without evaluation" "CASE E" "$TMP/E.json"

mkcap "c['lifecycle_state']='PROPOSED';c['research_id']='RSCH-P04-UNKNOWN'" "$TMP/F.json"
run_case "CASE F  selection without research" "CASE F" "$TMP/F.json"

mkcap "c['approval_status']='APPROVED'" "$TMP/G.json"
run_case "CASE G  APPROVED without decider" "CASE G" "$TMP/G.json"

mkcap "c['approval_status']='APPROVED';c['approval_decided_by']='agent'" "$TMP/G2.json"
run_case "CASE G2 APPROVED by agent" "CASE G" "$TMP/G2.json"

mkcap "c['lifecycle_state']='VERIFIED';c['evidence']=[]" "$TMP/H.json"
run_case "CASE H  VERIFIED without evidence" "CASE H" "$TMP/H.json"

mkcap "c['agent_specific_dependency']='~/.claude/skills/x'" "$TMP/I.json"
run_case "CASE I  agent-specific dep as neutral" "CASE I" "$TMP/I.json"

mkcap "c['staleness']='STALE';c['presented_as_current']=True" "$TMP/J.json"
run_case "CASE J  stale presented as current" "CASE J" "$TMP/J.json"

mkcap "c['fact_class']='UNKNOWN';c['presented_as']='known'" "$TMP/K.json"
run_case "CASE K  UNKNOWN presented as known" "CASE K" "$TMP/K.json"

mkcap "c['type']='MCP';c['install_scope']='GLOBAL';c['global_installation_authorized_by']='User';c['mcp']={'trust_level':'UNTRUSTED'}" "$TMP/L.json"
run_case "CASE L  untrusted MCP installed" "CASE L" "$TMP/L.json"

mkcap "c['lifecycle_state']='ACTIVE';c['evidence']=['EV-P04-900'];c['replaces_active']=True" "$TMP/M.json"
run_case "CASE M  replaces ACTIVE without approval" "CASE M" "$TMP/M.json"

mkcap "c['install_scope']='GLOBAL';c['global_installation_authorized_by']='agent'" "$TMP/N.json"
run_case "CASE N  global install authorized by agent" "CASE D/N" "$TMP/N.json"

echo ""
if [ "$NEG_FAIL" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}== NEGATIVE SUITE: $NEG_PASS cases correctly rejected, 0 missed ==${NC}"
else
  echo -e "${RED}${BOLD}== NEGATIVE SUITE: $NEG_PASS rejected, $NEG_FAIL MISSED ==${NC}"
fi
echo ""
if [ "$FAIL" -eq 0 ] && [ "$NEG_FAIL" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}== CAPABILITY VALID: $PASS checks passed, 0 failed, $NEG_PASS negative cases enforced ==${NC}"
  exit 0
fi
echo -e "${RED}${BOLD}== CAPABILITY INVALID: $PASS passed, $FAIL failed, $NEG_FAIL negative cases missed ==${NC}"
exit 1
