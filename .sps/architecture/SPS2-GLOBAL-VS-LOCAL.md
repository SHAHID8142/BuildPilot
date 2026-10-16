# SPS 2.0 — Global vs Project-Local

**Phase:** `PHASE-05` · **Status:** `AWAITING_USER_APPROVAL`

**Hard requirement:** minimise global installation. Everything a project needs is project-local.

---

## 1. Legacy problem (measured, Phase 04 `EV-P04-010`)

| Measure | Value | Consequence |
|---|---|---|
| `install.sh` skill installs | 27, every one global (`-g`) | Project context ignored |
| Global path writes | 34 | Writes into `~` |
| Sync roots written | 17 host directories | Machine mutated per install |
| Taste preference | one permanent operator (`SKILL-GOVERNANCE.md:35`) | No project adaptation |
| `SKILL-ROUTER.md` | 20-row static `domain -> skill` table | Lookup, not judgement |

The legacy model installs a **fixed global stack** and hopes every project wants it.

---

## 2. SPS 2.0 classification

| Artefact | Scope | Rationale |
|---|---|---|
| SPS 2.0 core framework | **Global (optional)** | One copy per machine; read-only |
| Selected skills / capabilities | **Project-local** | Must match the project's stack and constraints |
| MCP servers | **Project-local** | Different projects need different tools and credentials |
| Project memory, decisions, tasks | **Project-local** | Belongs to the project, not the machine |
| Capability registry | **Project-local** | Selection is project-specific |
| Research cache | **Project-local** | Findings are project/tech-specific |
| Evidence, audit trail | **Project-local** | Provenance is project property |
| Validators | **Pinned per project** | A project must validate against its own rules |
| Icon library / design tokens | **Project-local** | Design system is a project decision |
| User global preferences | Global (minimal) | Only cross-project habits the user explicitly promotes |
| OS / shell / global agent config | **Never** | Out of scope entirely |

### What may be global
Only: the SPS 2.0 core itself, and user preferences explicitly promoted to "personal default".

### What must be project-local
Everything else. A capability is project-local **by default**; a global install is an exception requiring
explicit user request plus the same security and approval gates.

### What may be cached
Downloaded artefacts (registries, packages) in a **user cache dir**, with the *resolution* recorded
project-locally. A cache is not a source of truth — the lockfile in the project is.

### What must never become global
- MCP server definitions with credentials
- Project skills activated for one project
- Project decisions, evidence, or task state
- Anything the project's approval gate touched

---

## 3. Isolation between projects

```
project-A/.sps/  ──┐
                   ├─► zero shared mutable state
project-B/.sps/  ──┘
```

Two projects may use different skills for the same domain, with no interference. Enforced by:
1. Global installs require explicit user authorisation recorded in the registry.
2. Validators reject a `GLOBAL` scope without a user authorizer (Phase 04 `CASE D`/`N` — enforced).
3. Project scope is recorded per capability (`install_scope`).

---

## 4. Team reproducibility

A new teammate clones the project and gets the same environment because **the environment is described in
the repository**:

| Need | Source of truth |
|---|---|
| Which capabilities and versions | `.sps/capabilities/registry.json` + lockfile |
| How they were chosen | `selection_reason` + evaluation record |
| Project rules and constraints | `.sps/PROFILE.md`, `.sps/config/` |
| Architecture decisions | `.sps/decisions/` + `docs/adr/` |
| What is verified | `.sps/evidence/` |
| How to bootstrap | `docs/` + validator copies in `.sps/tools/` |

Bootstrap is a **project-scoped, deterministic, offline-capable** operation — not a machine mutation.
The legacy `curl | bash` global installer is **not** the SPS 2.0 onboarding path.

---

## 5. Enforcement

| Rule | Enforcement | Level |
|---|---|---|
| No global install without user authorisation | Validator (rejects) | 2 — BLOCKING |
| Global install authorised by an agent | Validator (rejects) | 2 — BLOCKING |
| Project state written outside `.sps/` | Validator (rejects) | 2 — BLOCKING |
| Agent-specific memory used as source of truth | Lint (rejects) | 2 — BLOCKING |
| Global install *requested* | User approval gate | 3 — APPROVAL_GATE |
| Destructive machine-global change | Never permitted | 4 — HARD_GATE |