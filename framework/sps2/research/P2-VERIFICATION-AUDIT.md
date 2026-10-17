# P2 Verification and Evaluation Audit

Phase: roadmap P2 (audit phase 06). Research only.

## The mandatory distinction

Four levels must never be conflated:

| Level | Statement | Enforced? |
|---|---|---|
| 1 | "The agent was told to test" | No. A prompt is not a mechanism. |
| 2 | "The agent ran tests" | Partially. Output exists, nothing gated on it. |
| 3 | "The system required tests" | Yes. A validator refuses the transition. |
| 4 | "The system prevented progression without valid evidence" | Yes. Strongest. |

SPS 2.0 operates at **level 4**. This is already proven in P1: the validator
refused 25 deliberately invalid fixtures and the phase could not advance without
recorded evidence.

---

## 1. What the ecosystem offers

| Mechanism | Source | Level reached | Limit |
|---|---|---|---|
| `verification-loop`, `eval-harness` skills | SRC-002 | 1-2 | Named skills; loop mechanism not source-audited |
| `tdd-workflow`, per-language testing skills | SRC-002 | 1 | Method guidance |
| Codex Security CLI / SDK, SARIF, CI severity policy | SRC-009 | 3 | Scoped to security findings only |
| `allow_managed_hooks_only` | SRC-008 | 4 | Narrow: hooks only, not general verification |
| Claude Code permission modes + sandbox | SRC-006 | 3-4 | Controls *action*, not evidence quality |
| Checkpoint-based evaluation | SRC-015 | 2-3 | Vendor-internal; evaluates outcome, not gate |
| **`sps2/tools/validate-sps2.sh`** | P1, verified | **4** | Structural/state scope only |

**Finding**: no reviewed system demonstrated a *general* level-4 mechanism — where
an arbitrary task cannot be marked verified without independently captured
evidence. Codex's `allow_managed_hooks_only` is the closest observed primitive,
and it governs hooks, not verification.

## 2. Why this is SPS's strongest differentiator

The legacy SPS failed at exactly this point (Phase 01 finding F-9): documentation
asserted behaviour that no code implemented. "Always verify" was a prompt.

SPS closes this structurally:

- `implementation.verified` requires non-empty evidence (P1 negative case B).
- `verification.state: VERIFIED` requires evidence (case A2).
- `VERIFIED` without `decided_by` is refused (case G).
- Approval attributed to a non-user is refused (case C).
- High-risk requirements cannot be verified by an AGENT method alone.

These are **validator-enforced refusals**, not guidance.

## 3. Independent verification — the fresh-context principle

SRC-015 recommends evaluating whether the agent "achieved the correct final
state", allowing alternative paths, and using discrete checkpoints for complex
workflows (CAP-020).

SPS translation:

- Fresh-context review = a reviewer with no prior conversation state, validating
  against artefacts on disk. This is exactly why evidence is a file.
- Reproducibility = re-running the validator must produce the same verdict.
- Anti-pattern rejected: an evaluator that shares the implementer's context
  inherits its assumptions.

## 4. Capability-level verification (from SRC-009)

Codex Security emits **SARIF** with severity policy evaluable in CI. The transferable
insight is not the tool but the output shape:

```text
verification result -> machine-readable record -> policy decides pass/fail
```

SPS already does this in JSON (`EV-*` records). For future SEO, security and
deployment verifiers, the contract should be: **verifiers emit structured
evidence; a policy evaluates it; the transition gate consumes the verdict.** No
verifier may self-declare success in prose.

## 5. Gaps P2 did not close

- No independent reproduction of the Anthropic 90.2% figure (vendor-internal).
- ECC's `verification-loop` and `eval-harness` were read from README descriptions;
  the loop implementation was **not** source-audited.
- Visual regression, accessibility automation, contract testing, deployment smoke
  testing: named in the brief, **not** researched in P2.
- No baseline exists for verification *cost* (latency/token overhead of gates).

## 6. Recommendations

1. Keep level-4 refusal as the core invariant; never soften a validator to pass.
2. Add a positive control to every verifier (P1 pattern) so over-blocking is
   detectable.
3. Require verifiers to emit structured evidence; forbid prose self-assessment.
4. Prefer checkpoint evaluation over step-by-step validation (SRC-015).
5. Treat ECC's verification skills as RESEARCH_FURTHER until source-audited.
6. Dedicated verification research (visual, a11y, contract, deployment) is
   required before those verifiers can be specified.