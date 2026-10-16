# SPS 2.0 — Repository Architecture

**Phase:** `PHASE-05` — planning only · **Status:** `AWAITING_USER_APPROVAL`
**Proposed as a NEW repository.** The legacy SPS repository is preserved as an immutable reference.

---

## 1. What SPS 2.0 is

An **orchestration and control framework**, not a skill:

| Layer | Responsibility |
|---|---|
| Control | State machine, gates, evidence, provenance, approval |
| Orchestration | Lifecycle, task decomposition, subagent coordination |
| Capability | Discovery, evaluation, ranking, project-local activation |
| Domain | CMS, SEO, frontend, backend, testing, security, deployment |
| Interop | Agent adapters, MCP/tool discovery, portable state |

**Not** a single prompt. **Not** a single skill. The legacy design conflates all of the above into Markdown read
by one agent — the root architectural limitation (see `SPS2-MIGRATION-MATRIX.md`).

---

## 2. Proposed repository tree

```
sps2/
├── README.md   VERSION   LICENSE
├── .github/workflows/            # CI: lint, validators, schema + policy checks
│
├── core/                         # (1) CORE ORCHESTRATION — agent-neutral
│   ├── SPEC.md                   # normative lifecycle + state machine
│   ├── lifecycle/  protocols/    # state defs; handoff/action/approval/evidence contracts
│   ├── gates/                    # phase-gate + enforcement definitions
│   └── adapters/                 # (3) AGENT INTEROPERABILITY
│       ├── README.md             # adapter contract (portable core / thin agent layer)
│       ├── registry.json         # known agents + capability declarations
│       ├── claude/ cursor/ codex/ gemini/ opencode/ antigravity/ generic/
│       └── contract.schema.json  # what an adapter MUST / MUST NOT do
│
├── governance/                   # (2) GOVERNANCE — machine-checkable
│   ├── SCHEMAS/                  # JSON Schemas: task, requirement, evidence, approval
│   ├── validators/               # deterministic, exit-code based
│   ├── policies/                 # enforcement levels, stop conditions
│   └── DECISIONS.md
│
├── capability/                   # (4)(5)(6)(7) DISCOVERY
│   ├── MODEL.md                  # lifecycle, claim taxonomy, ranking
│   ├── discovery/                # source adapters (registry, repo, MCP catalog)
│   ├── evaluation/               # 16 criteria + scoring
│   ├── security/                 # supply-chain gate
│   └── registry.schema.json
│
├── research/                     # (8) TECHNOLOGY RESEARCH workflow + cache schema
│
├── domain/                       # (12)-(18) DOMAIN SUBSYSTEMS
│   ├── cms/      # CMS 2.0 (roles, content model, sections)
│   ├── seo/      # SEO 2.0 — designed from scratch, NOT migrated
│   ├── frontend/ backend/ testing/ security/ deployment/
│   └── shared/   # vertical-slice methodology, asset system, no-emoji rule
│
├── assets/                       # (19) icon libraries, design tokens, seeds
├── docs/                         # (20) architecture, ADRs, roadmap, threat model
├── migration/                    # (21) migration plan, matrix, scripts
├── legacy/                       # (22) compatibility adapters + provenance manifest
└── schemas/                      # shared JSON Schemas referenced by all layers
```

### Project-local layout (what each consuming project gets)

```
project/
├── .sps/
│   ├── STATE.md  PROFILE.md  AGENTS.md  CLAUDE.md  GEMINI.md
│   ├── config/ memory/ skills/ mcp/ research/
│   ├── capabilities/registry.json
│   ├── evidence/ decisions/ tasks/ audits/
│   └── tools/                    # project-pinned validator copies
└── (application source)
```

---

## 3. Directory responsibilities

| # | Directory | Responsibility | Boundary |
|---|---|---|---|
| 1 | `core/` | Lifecycle, protocols, gates — **zero agent dependency** | Must never import an agent SDK |
| 2 | `governance/` | Schemas + deterministic validators | `bash` + `python3` only |
| 3 | `core/adapters/` | Per-agent translation | Core may not know adapters exist |
| 4 | `capability/` | Discovery, evaluation, security, ranking | No install without approval |
| 5 | `.sps/skills/` | Activated capabilities (project-local) | Never global by default |
| 6 | `.sps/mcp/` | Project-scoped MCP definitions | Project-scoped |
| 7 | `research/` + `.sps/research/` | Research workflow + cache | Project-local |
| 8–11 | `.sps/{config,memory,capabilities,mcp}` | Per-project state | Never machine-global |
| 12 | `domain/cms/` | CMS 2.0 | Vertical-slice coupled |
| 13 | `domain/seo/` | SEO 2.0 — **new design** | Legacy SEO is a phantom |
| 14–18 | `domain/{frontend,backend,testing,security,deployment}` | Playbooks + checklists | Each must produce evidence |
| 19 | `assets/` | Icon libraries, tokens, seeds | Versioned; no emoji |
| 20 | `docs/` | Architecture, ADRs, roadmap | ADR = decision provenance |
| 21 | `migration/` | Migration tooling + matrix | Plan only until approved |
| 22 | `legacy/` | Compatibility shims + provenance manifest | Read-only inputs; never edited |

**Architectural principle:** `core/` and `governance/` know nothing about agents, MCPs, or domains. Everything
above depends on those two. This one-way dependency is what makes SPS 2.0 portable.

---

## 4. What is NOT in SPS 2.0

- No monolithic `SKILL.md` holding all laws.
- No hardcoded `domain → skill` mapping table.
- No global skill installation as the default.
- No emoji in shipped UI, docs, or code.
- No agent-specific magic outside `core/adapters/`.
- No AI runtime, daemon, background service, or database server.