# P2 Memory and Context Audit

Phase: roadmap P2 (audit phase 06). Research only.

## Governing question

> Do not add memory merely because another framework has it.

So each memory category found in the ecosystem was tested against: *does SPS need
it, or is it inherited cargo?*

---

## 1. Categories found in the ecosystem

| Category | Where observed | SPS verdict |
|---|---|---|
| Session memory | ECC `session-start.js` / `session-end.js` (SRC-002) | **ADAPT** as project-local state |
| Project memory | ECC `contexts/` (SRC-002) | **KEEP** as project-local files |
| User memory | `~/.claude/settings.local.json`, OpenCode global (SRC-004, SRC-007) | **REJECT** for SPS core |
| Agent memory | ECC instinct learning (SRC-002) | **REWRITE** — proposals only |
| Episodic / vector memory | Not observed in reviewed primary sources | **DEFER** — no evidence |
| Handoff artefacts | Anthropic filesystem artefacts (SRC-015); SPS `HANDOFF-*.json` | **KEEP** — already correct |
| Context compression | ECC `strategic-compact`, `pre-compact.js` (SRC-002) | **DEFER** — harness concern |
| Context retrieval | ECC `iterative-retrieval` (SRC-002) | **RESEARCH_FURTHER** |

---

## 2. What SPS actually needs

Three mechanisms, all already present in P1:

1. **Explicit state on disk** — phase, requirement, evidence, decisions. No
   hidden model memory; a fresh agent reconstructs everything from the repository.
2. **Evidence artefacts** — SRC-015 recommends writing subagent output to the
   filesystem and passing lightweight references, explicitly to avoid the
   "game of telephone" (CAP-019). This is already SPS's evidence model.
3. **Handoff documents** — the P1 handoff contract carries completed /
   not-completed / blockers / next-allowed / forbidden-next. This is the memory
   substitute SPS needs, and it is verifiable by a validator.

## 3. What SPS deliberately does not need

**Vector / episodic memory.** No primary source reviewed in P2 demonstrated a
requirement for it in a governance-first framework. Adding it now would be cargo
cult — importing complexity because a competitor has it. Deferred until a
requirement demonstrates the need.

**User-global memory.** Every harness ships a global layer (`~/.claude/`,
`~/.config/opencode/`). This is the single largest source of cross-project
contamination in the ecosystem. SPS core must not replicate it.

## 4. ECC's instinct approach — assessed

**Observed** (SRC-002): `continuous-learning-v2` is described as instinct-based
learning with confidence scoring, extracting patterns from sessions.

**Why this is REWRITE, not KEEP** (CAP-012):

- A confidence score is self-reported by the same system that wrote the rule. It
  is not independent evidence.
- If an extracted "instinct" becomes binding policy, the system has modified its
  own governance without user approval — directly violating the P1 requirement
  that approval must never be inferred.
- Learning that writes rules from one session generalises badly into another
  project, which is precisely the contamination SPS is designed to prevent.

**Required SPS adaptation**: learned patterns may be recorded only as
*proposals*, each carrying the evidence that prompted it, with `status:
PENDING_USER_APPROVAL` and `decided_by` reserved for a user. A pattern that no
user has approved must never gate a transition.

**Confidence on this assessment**: MEDIUM. ECC's v2 details were read from its
README description, not from a source-code audit of the learning logic. The
design critique holds regardless of implementation specifics, but the specifics
are unverified.

## 5. Context optimisation

ECC exposes `strategic-compact/`, `pre-compact.js` and `iterative-retrieval`
(SRC-002). These are compaction and retrieval strategies tied to a specific
harness's context window behaviour.

SPS verdict: **DEFER**. Context-window management belongs to the harness. SPS
should instead guarantee that *state is reconstructable from disk* so that
compaction, session restart or a different agent loses nothing. That property is
what actually matters for continuity, and it is testable; prompt-level compaction
tuning is not portable.

## 6. Recommendation summary

KEEP: explicit state, evidence artefacts, handoff documents.
ADAPT: session persistence (project-local only), context files.
REWRITE: instinct-based learning into evidence-gated proposals.
REJECT: user-global memory in SPS core.
DEFER: vector/episodic memory, compaction tuning.
RESEARCH_FURTHER: iterative retrieval.