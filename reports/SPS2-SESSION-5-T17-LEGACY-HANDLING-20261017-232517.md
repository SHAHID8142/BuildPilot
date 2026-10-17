# SPS2 Session 5 — T-17 Robust Legacy-Skill Handling + VERSION 4.1.0

Timestamp: 2026-10-17 23:25 +06:00
Branch: `build/roadmap-p3-completion`
Commit: `223603b` (local; push batched until master-checklist audit findings fold in)

## 1. What was delivered

### T-17 — robust legacy-skill handling (user request: "the handle of the old SPS skill can we make it more robust?")

`install.sh` `sync_core_skill()` now:

1. **Backup-before-replace** — every existing `sps` / `sps-cms` / `sps-seo`
   dir in each of the 17 SYNC_PATHS hosts is copied to
   `~/.sps/backups/<skill>/<stamp>/` before `rm -rf` + reinstall. Last 3
   backups per skill are kept (oldest pruned).
2. **Per-host stamp hash** — backup stamps include a 6-char hash of the dest
   root (`shasum`), so two hosts synced in the same second can never overwrite
   each other's backups. (Found by sandboxed smoke test: the first version
   used timestamp+PID only, which collides across hosts in the same run.)
3. **Version detection** — the previously installed `VERSION` is read before
   replacement; the upgrade report records `old → new` per host.
4. **Upgrade report** — `~/.sps/last-upgrade.txt` lists every host's outcome
   (`upgraded` / `installed fresh` / `reinstalled same version`), printed as
   an "Upgrade report" section at the end of the install run, together with
   the restore path:
   `rm -rf <dest>/<skill> && cp -R ~/.sps/backups/<skill>/<stamp> <dest>/<skill>`
5. **Update path covered** — `scripts/sps-update.sh` delegates to
   `install.sh --yes`, so the same protection applies on every update.
6. **Docs** — `DYNAMIC-SKILLS.md` rule 3 now documents the backup/restore
   behavior for bundled-skill updates.

### VERSION 4.1.0

- `skill/sps/VERSION` 4.0.0 → 4.1.0 (minor: new capability, no breaking change)
- Stamps updated: `SKILL.md` header, `templates/agent.md`,
  `templates/audit-report.md`, `README.md`
- `CHANGELOG.md` entry for 4.1.0 (T-17 + this session's earlier work: law
  checker, design craft laws, context budget, lifecycle/consent laws)

## 2. Verification evidence

| Gate | Result |
|---|---|
| `bash -n install.sh` | PASS |
| Sandbox smoke test (fake HOME, 2 hosts, old 4.0.0 install) | PASS — backups created per host with distinct stamps, correct old content, report lists both hosts as `upgraded ~: 4.0.0 → 4.1.0`, second run reports `fresh` |
| `legacy_exceptions.py` (DEC-7301 pathspec incl. install.sh) | PASS after re-pin |
| `check_laws.py` | PASS |
| `lint-sps.sh` | PASS |
| Full Python battery | 1102 passed / 2 skipped |
| validate-p2 / p3 / p5 / sps2 | PASS (69/68/47/80 checks) |
| validate-p4 | 58/2 — the 2 `P7_ARTIFACT_CREATED` failures are the documented pre-existing red (DEC-7304 re-baseline), unchanged |
| Governance contract tests (`test_round26_governance_contracts`) | 38 OK |
| Law-checker tests (`test_law_checker`) | 9 OK |

Manifest re-pins: `install.sh`, `CHANGELOG.md`, `README.md` blob+sha256
updated in `legacy-exception-manifest.json`; `EXPECTED_MANIFEST_SHA256`
updated in `legacy_exceptions.py`; stage-0 ordering law followed (`git add`
before validator run).

## 3. Second-opinion status (honest, in-flight at report time)

- **T-17 adversarial verifier** (general-purpose agent): launched, still
  running. Scope: quoting/expansion bugs, prune-loop edge cases, set -u
  interactions, uninstall.sh interaction, stamp collision risk, manifest pin
  correctness. Findings will be folded in before the batched push; any
  confirmed defect gets fixed and re-verified.
- **Master-checklist audit** (`wf_42b5fe5f-2e8`, 10 sections ×
  audit→verify pipeline): 9/10 sections complete with all ~70 verify agents
  done except 8 security verifiers (CSRF, SSRF, SQLi, RLS, password hashing,
  email verification, log hygiene, LLM-input sanitization). Confirmed gaps
  will be closed in skill docs + law-checker markers and pushed in the same
  batch.

## 4. Limitations

- The push has NOT happened yet (DEPLOY-BUDGET: one push after the audit
  findings fold in). CI has not run on `223603b`.
- The smoke test used stubbed display helpers (ok/warn/note/section) rather
  than sourcing the full install.sh preamble; the functions under test were
  extracted verbatim from the file.
- The first smoke-test attempt was blocked by a Claude Code safety check
  (embedded `rm -rf` in a `bash -c` heredoc); the rewrite used an explicit
  script file with checkable paths instead. No workaround of the check
  occurred — the flagged command never ran.
- p4 remains red by design until the user ratifies the P7 artifact question.

## 5. Awaiting user (unchanged from session 4)

- PROP-20261017-path-derivation ratification
- DEC-7301/7302/7303/7305 formal ratification; C6/C7; push policy beyond
  DEC-0032; p4's `P7_ARTIFACT_CREATED` question

---

## Addendum (2026-10-17 23:45 +06:00)

### Post-report work, in order

1. **Master-checklist audit completed** (`wf_42b5fe5f-2e8`, 115 agents,
   4.62M tokens, 1773 tool uses): 106 raw gaps raised, **96 confirmed real**
   by independent verify agents (8 refuted as already covered, 2 verifiers
   still in flight at cutoff were mooted by the same edits). All 96 closed
   and pushed (`a392faf`):
   - SECTION-DOD 28–50: data-layer correctness, web/API hardening
     (CSRF/SSRF/LLM-injection/webhook signatures), session & auth hygiene,
     production posture (CSP/HSTS/log scrubbing), dependency & source
     hygiene, env validation, health/graceful-shutdown/backoff, privacy &
     legal surfaces, API contract versioning, hook/format automation,
     EXIF+RLS, security.txt, observability, uptime & alerts, resilience
     posture, spending guardrails
   - VERIFICATION-RECIPES: server-side caching, payload compression,
     connection pooling, background queues, debounce/re-render, new
     Test-isolation & pre-deploy recipe (mock time, mock APIs, E2E,
     load/stress, migration rollback, PITR), extended cleanup gate
   - DESIGN-GATE: Copy laws section (12 laws), error boundaries, text
     scaling, lang attribute, PWA completeness
   - MOBILE-LOW-END: minify + code-split + HTTP/2 checklist item
   - sps-seo: og:image 1200×630, noopener noreferrer, llms.txt, GSC
     verification, backlink strategy, SPF/DKIM/DMARC
   - check_laws.py: +15 DoD markers, +7 DESIGN-GATE markers;
     test_law_checker.py: 11 tests (2 new negative cases)
   - Coverage cross-check script confirmed all 96 items present in docs.

2. **CI green on 945ecce** (run 39054355422).

3. **Hover/touch law** (user-reported failure: agents keep designing
   hover-to-reveal patterns invisible on touch): MOBILE-LOW-END
   "Hover/touch law (hard guard)" — hover-gated content as sole access
   path banned; desktop hover = progressive enhancement via
   `@media (hover: hover)`; tooltips on focus AND tap; tap-first
   replacement patterns. DESIGN-GATE cross-ref + law-checker marker.
   Pushed `101effe`, CI green.

4. **T-17 adversarial review returned**: manifest pins verified clean +
   4 findings (1 MAJOR, 2 MINOR, 1 NIT). All 4 fixed and smoke-tested
   (fresh install: no backup churn; partial install: sps-cms backed up
   without sps; real upgrade: 4.0.0→4.1.0 report). uninstall.sh now
   preserves backups at ~/.sps-backups-uninstalled. Pushed `69b43b0`,
   CI green (run 39055012423).

5. **Legal/consent checklist audit launched** (`wf_366a6347-b5b`, 8
   sections from the user's Gemini legal list). At addendum time: 43/51
   agents done, 28 gaps confirmed / 0 refuted so far. Gap-closing batch
   to follow on completion (likely a new skill/sps/LEGAL-COMPLIANCE.md +
   SECTION-DOD pointers).

### Battery state at addendum time

1104 passed / 2 skipped; p2/p3/p5/sps2 green; p4 58/2 (documented
pre-existing); legacy check PASS; law check PASS; lint PASS.
