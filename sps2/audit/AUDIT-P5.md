# AUDIT-P5 — SPS 2.0 Implementation / Integration

Audit date: 2026-10-04
Auditor: implementation agent (not a User; this audit is not an approval)
Branch: `main`
Verdict: **IMPLEMENTED, VERIFIED and APPROVED** (User, 2026-10-04).
Scope: P5 implementation/integration only.
P6 remains NOT_STARTED / NOT_APPROVED.

---

## 1. Scope

P5 implemented the SPS 2.0 integration layer on top of the P1-P4 foundation:
core capability-engine integration, project-local selection, governance and
evidence wiring, the agent-neutral core boundary, and the adapter boundary.

Nothing outside that scope was started.

## 2. Three-axis status

| Axis | State | Basis |
|---|---|---|
| IMPLEMENTED | COMPLETE | Six new units exist and import |
| VERIFIED | COMPLETE | 35 validator checks, 39 unit tests, 12 negative cases |
| APPROVED | GIVEN | User, 2026-10-04, scope limited to P5 implementation/integration |

The agent did not approve its own work. The approval recorded here was given
explicitly by the User in session and is attributable to them.

## 3. Findings

### F1 — agent names had leaked into the core (RESOLVED)

The first draft of `registry_api.py` embedded a regex listing agent names in
order to reject agent-attributed approvals. That is a direct violation of the
rule the core must obey.

Resolution: the pattern moved to `sps2/governance/attribution.py`. The core now
takes the approval predicate as an injected argument and falls back to a
core-neutral state-and-date check. The governance predicate is strictly
stronger, so no control was lost to satisfy the architecture. A unit test
asserts the two predicates differ on an agent-named approver.

### F2 — a popularity test asserted something untrue (RESOLVED)

A test asserted that a popularity spike could not change the selection ordering
at all. The four promoted capabilities tie on score, so a spike legitimately
breaks the tie and the assertion was false.

Resolution: the invariant was restated as the correct one, that popularity can
never outrank an evidence-weighted score difference. A fixture now produces a
strict score gap and asserts the higher scorer stays first against a rival
holding 1e9 stars. The test became stronger, not weaker.

### F3 — the negative suite initially had inverted polarity (RESOLVED)

Each case reported "NOT rejected" precisely when the control correctly fired,
producing four false alarms. Polarity was corrected to "returns True when the
violation was NOT detected". Three cases were then over-corrected and restored.
Each case still constructs the bad state and confirms the control fires.

### F4 — a deferred capability's incomplete trace was reported as a defect (RESOLVED)

`verify` initially flagged `CAP-P03-005` for missing approval and verification
links. That is the correct state for a deferred candidate, not a defect. The
check now distinguishes: a promoted capability with an incomplete trace is a
failure; a deferred candidate with an incomplete trace is reported as expected.

### F5 — the bash validator could not be made to parse (RESOLVED)

bash consumes a heredoc body before completing the surrounding list, so a
heredoc placed directly in an `if` condition breaks the trailing `else`.
Chained file appends additionally glued a `fi` onto the following statement.
Rather than paper over this, the validator was reimplemented in Python. No
check was dropped in the rewrite.

## 4. Control review

| Control | Result |
|---|---|
| Agent-neutral core | PASS, with a positive control proving the check fires |
| Core free of adapter dependency | PASS |
| Project-local only, no global writes | PASS |
| Capability trace chain (10 links) | PASS for all four promoted |
| No silent ACTIVE or INSTALLED | PASS |
| Selection deterministic | PASS, three runs byte-identical |
| Popularity cannot outrank evidence | PASS |
| Agent-attributed approval rejected | PASS |
| CONF-001 still unresolved | PASS |
| No invented LCP/INP threshold | PASS |
| Legacy diff zero | PASS |
| Secret scan clean | PASS |
| Committed blob has no credential key | PASS |
| Checkpoint `a7767cf` preserved | PASS |
| P3 incident classification unchanged | PASS |
| MIT licence unchanged | PASS |
| SPS-CMS provenance not upgraded | PASS |
| No external dependency | PASS |
| Emoji policy | PASS |
| No P6 artefact | PASS |

## 5. Honesty statement

- The four promoted capabilities remain `EVALUATED`. They are **not** active,
  installed or runtime-traced. Nothing was installed.
- `CAP-P03-005` remains `DEFERRED` and unselectable behind gates F, H and K.
- `CONF-001` remains `UNRESOLVED`. No LCP or INP threshold was invented.
- SPS-CMS provenance remains `USER_ATTESTATION`, not independently verified.
- No dependency was added because none was needed.
- No stop condition was triggered and no judgement call was silently made.

## 6. Open items requiring a User decision

1. Approve the eight P5 requirements, or return them for rework.
2. Decide whether runtime activation should ever be implemented. If so, the
   exact lifecycle transition must be defined and approved first.
3. `CAP-P03-005` still needs an executable CLS verifier and a resolution of
   `CONF-001` before Gate K can be satisfied.
4. Confirm whether P5 should be committed as-is or amended.