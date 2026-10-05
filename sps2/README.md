# SPS 2.0

**Version:** `0.1.0-foundation` · **Status:** P1 foundation — `AWAITING_USER_APPROVAL`
**Lineage:** designed by Phase 05 (approved by User, 2026-10-03); foundation built in P1.

SPS 2.0 is an **orchestration and control framework** for AI-assisted software
development — not a single skill and not a single prompt.

> **This is not the legacy SPS.** The legacy implementation lives at the repository root
> (`skills/`, `scripts/`, `plugins/`, installers) and is **reference-only**. Nothing in
> `sps2/` may modify or depend on it. See `legacy/MANIFEST.md`.

---

## Architecture

```
sps2/
├── core/            agent-neutral orchestration: lifecycle, protocols, gates, adapters
├── governance/      contracts (JSON Schemas), validators, policies
├── capability/      capability model, registry, security gate (engine in P4)
├── research/        technology research gate (populated in P6)
├── project/         project-local layout definition
├── skills/          project-local skill layout (selection in P5)
├── mcp/             project-local MCP layout (discovery in later phase)
├── tests/           conformance suite + deliberately invalid fixtures
├── docs/            architecture docs and ADRs
├── legacy/          legacy protection manifest (read-only)
└── tools/           the P1 validator
```

### The one-way dependency rule

```
core/  +  governance/      agent-neutral, portable, deterministic
        ▲
        │  one-way (core MUST NOT import, reference or branch on an agent)
        │
   adapters/                thin, replaceable, deletable
```

**Portability test:** the core suite must pass with **every adapter deleted.**

---

## Roadmap P3 — Agent Interoperability

Delivered under the User decisions `D-P3-A..G`
(`decisions/ROADMAP-P3-DECISIONS.json`); **User approval of the delivered state
is still PENDING**, so the reconciliation record does not report roadmap P3 as
satisfied.

| Path | What it is |
|---|---|
| `core/adapters/contract.schema.json` | the adapter contract: one adapter's shape and its invariants |
| `core/adapters/registry.json` | the adapter set, its maturities and its detection metadata |
| `core/adapters/<agent_id>/adapter.json` | one declarative adapter, equal to its registry entry |
| `core/adapters/README.md` | the surface, its invariants and its deletion semantics |
| `tools/portability.py` | the delete-all operation, the `D-P3-A` bound, and its rehearsal |
| `tools/test-portability.py` | the portability conformance suite (4 criteria) |
| `RESUME.md` | the mechanical fresh-agent resume checklist |
| `evidence/ROADMAP-P3-EVIDENCE.json` | the recorded output behind every roadmap P3 claim |

Adapters: `generic` (DECLARED fallback) plus `codex` and `opencode`
(EXPERIMENTAL; no `VERIFIED` claim, because no agent has been exercised under
this authorisation). Adapters are declarative only, write nothing outside the
project and are deletable without touching the core.

```bash
python3 sps2/tools/portability.py                # rehearse delete-all, isolated copy
python3 sps2/tools/portability.py --verify       # check the delivered adapter state
python3 sps2/tools/test-portability.py           # full conformance suite
```

**New here with no prior memory?** Start at [`RESUME.md`](RESUME.md): it names
the canonical sources and answers the phase, task, next allowed action, what
was authorised, which adapters exist and why, what remains and the forbidden
actions.

---

## Global vs project-local

**Default: project-local.** Global state is exceptional and must be explicitly justified
and user-authorised.

| Class | Scope |
|---|---|
| Selected skills, capabilities, MCP config | **Project-local** |
| Capability registry, research cache, memory, decisions, evidence, tasks | **Project-local** |
| Icon library, design tokens | **Project-local** |
| This framework (`sps2/`) | Global (optional, read-only) |
| Machine-global installer | **Never** |

Two projects must be able to select **different** capabilities for the same domain with
no interference. Nothing is "install once, reuse forever".

---

## No emoji

**NO EMOJI by default** — in UI, buttons, labels, docs, code comments, generated copy and
status indicators. Use an appropriate icon library. Emoji are permitted only when a
specific project explicitly authorises them.

Icon libraries are **selectable capabilities**, not a globally pinned choice — pinning one
globally would recreate the legacy permanent-preference failure.

This rule is machine-checked by `tools/validate-sps2.sh`, not merely documented.

---

## Validation

```bash
bash sps2/tools/validate-sps2.sh              # structural + negative suite
bash sps2/tools/validate-sps2.sh --negative   # negative tests only
python3 sps2/tools/test-portability.py        # roadmap P3 portability conformance
```

Validates **structured state**, not the presence of words in Markdown. Exit `0` valid,
`1` failure, `2` tooling unavailable.

---

## What P1 deliberately does NOT implement

Dynamic discovery · skill selection · MCP discovery · CMS · SEO · application workflows ·
legacy migration · global installation · machine-global configuration · any Phase 01 remediation.

Two items in that list were later phases, and are now delivered or explicitly
deliberate:

- **Concrete agent adapters beyond the contract** — roadmap P3 added two
  declarative adapters (`codex`, `opencode`) and kept the `generic` fallback. No
  adapter is executable, installs nothing, and none is required for the system
  to work.
- **Global installation** — still not implemented and not authorised: no
  capability is installed, activated or promoted, and no machine-global state
  is written.

Those belong to later, separately approved phases.