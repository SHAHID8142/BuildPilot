# SPS2 Technical Completion Master TODO

Timestamp: 2026-10-17 08:49:25 +06:00

## Operating Rules

- DEC-7301, DEC-7302, and DEC-7303 remain **UNAPPROVED**.
- The Round 26 record's purported User approval is disputed and must not be relied on.
- The append-only correction sidecar is preserved and does not rewrite the subject record.
- No staging, commit, push, merge, rebase, deployment, publication, release, dependency installation, network action, or CI change is authorized.
- Preserve every pre-existing modified and untracked file.

No separate subagent execution mechanism is available in this environment. The required decomposition is therefore emulated through clearly separated investigation and implementation batches. Each batch is reviewed and verified before moving to the next.

## Master TODO

| ID | Priority | Workstream | Task | Owner | Dependencies | Risk | Acceptance criteria | Status |
|---|---:|---|---|---|---|---|---|---|
| T0.1 | P0 | W0 | Reconcile live branch, HEAD, staged/unstaged/untracked state, stashes, reports, and backup reference | Codex | none | Low | Actual baseline recorded; all pre-existing paths preserved; backup commit verified without remote mutation | IN_PROGRESS |
| T0.2 | P0 | W0 | Build no-touch inventory for user-owned, governance-sensitive, disputed, and P10-protected files | Codex | T0.1 | Medium | Explicit no-touch list recorded, including `.claude/settings.json`, Round 26 record/sidecar, P10 evidence/inventory, backend manifest, CI, and historical reports | TODO |
| T0.3 | P0 | W0 | Map architecture, test entry points, validators, manifests, contracts, generated files, and high-risk directories | Codex | T0.1 | Medium | Repository map distinguishes code, tests, governance, generated artifacts, and policy-sensitive paths | TODO |
| T1.1 | P1 | W1 | Inventory all 35 test modules, tracked/untracked status, commands, skips, and environmental limitations | Codex | T0.1 | Low | Complete test inventory and exact offline commands recorded | TODO |
| T1.2 | P1 | W1 | Review tests for false positives, fragile assumptions, duplicated coverage, and disputed-policy assertions | Codex | T1.1 | Medium | Each finding classified code-owned, policy-owned, baseline, environment, or informational | TODO |
| T1.3 | P1 | W1 | Add only authorized, clearly code-owned tests or strengthen existing tests without weakening controls | Codex | T1.2 | Medium | Any added test has explicit rationale, focused run evidence, and no CI change | TODO |
| T2.1 | P1 | W2 | Audit updater, installer/bootstrap, checker, cache, path, symlink, and fallback behavior | Codex | T0.1 | High | Destructive paths, fail-closed behavior, and mirror parity verified non-destructively | TODO |
| T2.2 | P1 | W2 | Investigate four check-update mirror validator failures without expanding DEC-7301 or weakening validators | Codex | T2.1 | High | Failures classified; if policy-owned, precise remediation options and impacts documented | TODO |
| T2.3 | P2 | W2 | Fix genuine code-owned updater defects only | Codex | T2.1 | High | Focused tests and mirror/syntax checks pass; no unauthorized scope expansion | TODO |
| T3.1 | P1 | W3 | Audit decision schemas, manifests, hash pins, identifier compatibility, checkers, and correction sidecar | Codex | T0.1 | High | Manifest hashes and fail-closed behavior verified; no false approval attribution introduced | TODO |
| T3.2 | P1 | W3 | Classify all validator failures as code-owned, baseline, policy-dependent, or missing prerequisite | Codex | T3.1 | Medium | Every failure mapped to evidence and owner | TODO |
| T3.3 | P2 | W3 | Fix only code-owned governance validator defects while preserving exit semantics and policy | Codex | T3.2 | High | Focused tests pass; historical records unchanged | TODO |
| T4.1 | P1 | W4 | Audit P10 gate, frontend, SEO isolation, dynamic import, rollback rehearsal, and protected state | Codex | T0.1 | High | Gate remains read-only and fail-closed; protected fields and absent backend manifest verified | TODO |
| T4.2 | P1 | W4 | Determine whether rollback success contract can be restored policy-neutrally | Codex | T4.1 | High | If not, retain honest failing rehearsal and document safe options/impacts | TODO |
| T4.3 | P2 | W4 | Fix only demonstrably code-owned P10/frontend/SEO defects | Codex | T4.2 | High | Focused and related suites pass; no policy decision implied | TODO |
| T5.1 | P1 | W5 | Audit P2/P3/P4/P5 capability validators and P7 prerequisites | Codex | T0.1 | Medium | Baseline, policy, missing-artifact, and code defects separated | TODO |
| T5.2 | P2 | W5 | Improve tests/docs only where contract-preserving and authorized | Codex | T5.1 | Medium | No governance re-baselining; focused evidence recorded | TODO |
| T6.1 | P2 | W6 | Review developer/operator documentation for stale or contradictory implementation guidance | Codex | T0.3 | Medium | Stale factual docs identified; only safe factual corrections made | TODO |
| T7.1 | P1 | W7 | Integrate any accepted changes chunk-by-chunk and run focused tests | Codex | T1–T6 | High | Status checked before/after each chunk; no unrelated files staged or modified | TODO |
| T7.2 | P0 | W7 | Run full offline matrix, real P10 gate, validator matrix, syntax, mirrors, whitespace, and integrity checks | Codex | T7.1 | High | Actual exits, counts, skips, and failures recorded; no result masked | TODO |
| T7.3 | P0 | W7 | Produce final completion report and handoff for Claude and QA | Codex | T7.2 | Medium | New timestamped report includes TODO dispositions, evidence, blockers, and handoff checklist | TODO |

## Deferred / Blocked

| Topic | Reason |
|---|---|
| Ratifying, rejecting, or amending DEC-7301–7303 | Explicit User decision required |
| Expanding the eight-path updater exception | Would effectively ratify DEC-7301 |
| Adding a P10 dynamic-import exception | Would amend DEC-7302 |
| Restoring the successful rollback rehearsal via policy exception | Requires governance decision |
| Restoring or retaining `.claude/settings.json` | Provenance unresolved |
| Correcting historical governance records | Governance authorization required |
| P10 approval, publication, backend manifest, gate evidence, slice history, exposure observation, deployment audit | Product/release prerequisites and authorization required |
| CI changes or adding untracked modules to CI | Explicitly unauthorized |

