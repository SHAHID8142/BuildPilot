# Capability Provenance, Research Cache & Interop

**Phase:** `PHASE-04` · **Status:** `AWAITING_USER_APPROVAL`

---

## 1. Provenance chain (§12)

```
requirement -> discovery -> research -> evaluation -> user decision
            -> installation -> verification -> usage
```

A break at any link invalidates the chain. Every active capability must be traceable end-to-end.

### Enforcement honesty

| Property | Status | Note |
|---|---|---|
| Records exist and are structurally complete | **ENFORCED** | `validate-capability.sh` |
| Chain ordering is complete at each step | **VALIDATED** | Validator checks ordering |
| Provenance is recorded truthfully | **DOCUMENTED** | Depends on agent honesty |
| Runtime provenance tracking | **DECLARED** | Not implemented — no runtime exists |

**No runtime provenance tracking is claimed.** Phase 04 provides records and checks, not a
live tracer.

---

## 2. Research cache (§11) — project-local

Stored in `.sps/research/`. **Never** in agent memory, model memory, or machine-global dirs.

| Field | Purpose |
|---|---|
| `research_id` | `RSCH-P04-001` |
| `subject` | Technology or capability researched |
| `researched_at` | ISO-8601 UTC |
| `sources[]` | Each with `rank` (1–6 per `CAPABILITY-MODEL.md` §5) and `url` |
| `version_checked` | Version observed |
| `conclusions[]` | Each tagged `FACT` / `EVIDENCE` / `INFERENCE` |
| `uncertainties[]` | Explicitly `UNKNOWN` items |
| `decisions[]` | What was concluded |
| `readiness` | `SUFFICIENT` / `INSUFFICIENT` |

**Rule:** a technology is `INSUFFICIENT` until its docs, version, compatibility, ecosystem,
practices, security, tooling, testing and deployment implications are recorded. Only a
`SUFFICIENT` entry may satisfy the research gate (`CASE F`).

**Durability:** a future agent opening this project tomorrow must reconstruct what was
researched and why, without any agent-specific memory.

---

## 3. Evaluation contract (§7)

| # | Criterion | Evidence expected |
|---|---|---|
| 1 | Functional fit | Requirement mapping |
| 2 | Technology compatibility | Version/framework matrix |
| 3 | Framework compatibility | Declared framework support |
| 4 | Agent compatibility | Agent-neutral or documented |
| 5 | Security | Security gate output |
| 6 | Maintenance/activity | Last release/commit — or `UNKNOWN` |
| 7 | Documentation quality | Official docs presence + quality |
| 8 | Stability | Release channel, breaking-change history |
| 9 | Version compatibility | Matches project constraints |
| 10 | Licence compatibility | Licence vs project policy |
| 11 | Performance implications | Measured or `UNKNOWN` |
| 12 | Community/adoption | Tie-breaker only, never primary |
| 13 | Installation complexity | Effort + global impact |
| 14 | Reversibility | Uninstall/rollback quality |
| 15 | Project-local compatibility | Runs without global changes |
| 16 | Long-term suitability | Roadmap, bus factor, lock-in risk |

**Rules:**
- Every criterion gets a value **or** an explicit `UNKNOWN` — silence is invalid.
- Selection records `selection_reason` referencing the deciding criteria.
- Rejected candidates record `rejection_reason` — comparing alternatives is the point.
- **Popularity is never the deciding criterion.**
- `UNKNOWN` on criteria 2, 3, 5, 9 or 10 blocks selection until researched.
---

## 4. Capability registry

`.sps/capability/registry/PHASE-04-CAPABILITIES.json` answers: *what is active, why selected,
where from, which version evaluated, how verified, how removed.*

Per-capability fields are defined in `SCHEMA.md` §12 and cover: identity, type, purpose,
domain, technology/framework/agent compatibility, source, official URL, repository URL,
version, release date, maintenance status, licence, security status, trust level, evidence,
quality and adoption indicators, known limitations, dependencies, install methods, rollback,
verification, research and verification timestamps, provenance, selection and rejection
reasons, approval status, lifecycle state, install scope, and `fact_class`.

---

## 5. Agent interoperability (§15)

**Consumption path — identical for every agent:**

```bash
cat .sps/STATE.md                                  # current phase + approval
cat .sps/capability/CAPABILITY-MODEL.md            # the model
jq .sps/capability/registry/PHASE-04-CAPABILITIES.json
bash .sps/tools/validate-capability.sh
```

**Portability guarantees:**
- Markdown + JSON only. No YAML parser, framework, or runtime dependency.
- `bash` + `python3`; `jq` optional (`python3` fallback).
- **Slash commands are NOT a mandatory dependency.**
- No proprietary memory, context, or directory mechanism required.

| Concern | Rule |
|---|---|
| Memory | Project-local files only; never agent-specific |
| Capability lists | The registry, not an agent's bundled defaults |
| Slash commands | Optional convenience layer |
| Private context | Must not be required to interpret the registry |
| Agent-specific dirs | Must not be written by the capability system |

Agent-compatibility claims must be **evidenced** — an agent-specific dependency presented as
agent-neutral is a validation failure (`CASE I`).

---

## 6. Migration plan from hardcoded routing (§8)

The existing system is **not removed** in Phase 04.

| Stage | Action | Status |
|---|---|---|
| 0 | Audit hardcoded routing (measured) | **Done** — `CAPABILITY-MODEL.md` §1 |
| 1 | Define contracts + empty registry | **Done** — this phase |
| 2 | Build validator | **Done** — `validate-capability.sh` |
| 3 | Populate registry from real research | **Deferred** — needs live research |
| 4 | Run discovery/evaluation for one domain | **Deferred** |
| 5 | Shadow-run: evaluate beside the router, log divergences | **Deferred** |
| 6 | User approves switching a domain | **Deferred** — needs approval |
| 7 | `SKILL-ROUTER.md` references the registry | **Deferred** |
| 8 | Retire hardcoded entries only where coverage is proven | **Deferred** |

**Constraint:** the legacy router remains authoritative until stage 6 is approved for a domain.
No silent switch-over.