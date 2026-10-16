# SPS 2.0 — Migration Matrix

**Phase:** `PHASE-05` · **Status:** `AWAITING_USER_APPROVAL`

Legacy SPS is **preserved unchanged** as an immutable reference. Nothing is redesigned in place.

---

## 1. Disposition vocabulary

`KEEP` reuse as-is · `REFACTOR` keep the idea, restructure the implementation · `REWRITE` discard the
implementation, keep the requirement · `REPLACE` swap approach · `DEPRECATE` still works, no new use ·
`ARCHIVE` move to read-only `legacy/` · `RESEARCH FIRST` cannot classify without new research ·
`NEVER COPY` must not enter SPS 2.0.

---

## 2. Matrix

| Component | Legacy evidence | Class | Rationale |
|---|---|---|---|
| **SPS core skill** | 50 md / 10 non-md | `REWRITE` | Doc-dominated and unenforceable; keep requirements, rebuild as `core/` + `governance/` |
| **State machine / lifecycle** | `STATE.md`, `GOVERNANCE.md` | `KEEP` | Phase 02–03 model is sound and validated (50+49 checks) |
| **Schemas** | `SCHEMA.md` §1–§16 | `REFACTOR` | Good contracts; convert to JSON Schema for machine validation |
| **Validators** | 4 validators, 24 negative cases | `KEEP` | Real enforcement; highest-value asset |
| **Evidence model** | `PHASE-0*-EVIDENCE.json` | `KEEP` | Append-only with honest FAIL/SKIP handling, already proven |
| **Approval discipline** | user-attribution checks | `KEEP` | Genuinely enforced; extend to JSON (Phase 04 gap) |
| **Capability model** | `.sps/capability/` (Phase 04) | `KEEP` | Correct shape; empty registry is correct |
| **Handoff contract** | `HANDOFF-CURRENT.md` | `REFACTOR` | Field set good; make action fields schema-enforced |
| **Skill router** | 20-row static table | `REPLACE` | Direct cause of Phase 01 F-2 |
| **Skill governance** | permanent taste operator (`:35`) | `REWRITE` | Permanent vendor preference is the defect |
| **Installers** | `install.sh` 432 LOC | `REWRITE` | Global-first: 27 global installs, 17 sync roots |
| **Update system** | `check-update` + `sps-update` 240 LOC | `REFACTOR` | Semver compare works; replace global reinstall |
| **Uninstall** | `uninstall.sh` 240 LOC, `rm -rf` sweeps | `REWRITE` | Path-guessing removal; use manifest-driven removal |
| **PowerShell parity** | 13 `.ps1` files | `RESEARCH FIRST` | Windows scope undecided |
| **Host adapters** | 8 in `skills/sps/hosts/` | `ARCHIVE` | Superseded by `core/adapters/` |
| **CMS skill** | 19 md / 37 code files | `RESEARCH FIRST` | Needs independent security + schema review before reuse |
| **CMS auth helper** | hardcoded secret fallback | `NEVER COPY` | Known vulnerability (`KI-01`) |
| **CMS admin TSX** | shipped admin templates | `RESEARCH FIRST` | Security posture unverified |
| **SEO** | **no skill exists** | `REWRITE` | Router names an `seo` fallback that does not exist — phantom dependency |
| **`data-sps-key` convention** | marker-based editing | `KEEP` | Reasonable coupling mechanism |
| **Section DoD / vertical slice** | 29-item checklist | `REFACTOR` | Right philosophy; make it a per-slice schema |
| **Templates** | 14 files | `ARCHIVE` | Framework-specific; regenerate under `domain/` |
| **Third-party skill list** | 27 hardcoded installs | `REPLACE` | Replaced by discovery + approval |
| **Anti-hallucination doc** | `ANTI-HALLUCINATION.md` | `REFACTOR` | Convert claims into enums + validator checks |
| **No-emoji rule** | absent | `NEW` | Required from scratch; global default |
| **MCP integration** | Context7 only | `RESEARCH FIRST` | Full discovery model needed |
| **README / CATALOG** | narrative + stale profiles | `REWRITE` | Contradicts 4.0.0; regenerate from registry |
| **CHANGELOG** | version history | `KEEP` | Useful provenance |
| **Root lock files** | bootstrap-created | `KEEP` | Portable interop mechanism |
| **Project-local `.sps/`** | 26 md / 7 json | `KEEP` | Correct direction, already validated |
| **Global `~/.sps/`** | personal-defaults, global-mistakes | `DEPRECATE` | Promote only on explicit user action |
| **`.claude-plugin/`** | v2.0.0 metadata (drifted) | `REPLACE` | Legacy packaging superseded |
| **Orphan debug scripts** | `test_*.sh`, `.test.out` | `ARCHIVE` | Development residue |
| **`.sps/tools/*.sh`** | Phase 02–04 validators | `KEEP` | Highest-value reusable asset |

---

## 3. Aggregate

| Class | Count |
|---|---|
| `KEEP` | 10 |
| `REFACTOR` | 8 |
| `REWRITE` | 6 |
| `REPLACE` | 4 |
| `ARCHIVE` | 4 |
| `DEPRECATE` | 1 |
| `RESEARCH FIRST` | 5 |
| `NEVER COPY` | 1 |

**Insight:** the legacy *governance layer* (Phases 02–04) is largely reusable. Its *distribution and selection
layer* (installers, router, hardcoded skill list) is what must be replaced.

---

## 4. Legacy preservation plan

- Legacy repository stays read-only, tagged `legacy-final`.
- SPS 2.0 starts as a **new repository**; no in-place redesign.
- `legacy/MANIFEST.md` records every imported artefact: origin, commit, licence, disposition, rationale.
- `RESEARCH FIRST` items stay outside SPS 2.0 until revalidated.
- `NEVER COPY` items are listed explicitly so a future agent cannot reintroduce them.