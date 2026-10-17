# Handoff Checkpoint (Mandatory Verification Loop)

**Law:** no work is handed back to the user until it has passed a written
verification checkpoint. The checkpoint runs AFTER the build, BEFORE the
handoff. An unchecked handoff is an incomplete task.

## The loop (run in order; every step leaves evidence)

1. **Re-read the request.** Write down (in the handoff or todo) what the
   user actually asked for, in one or two sentences. If the work does not
   map 1:1 to that sentence, it is not done.
2. **Static verification.** Run the full local battery the project defines:
   tests, typecheck, lint, validators, and any project gates (for this
   repo: the full pytest/unittest sweep — not a subset — plus
   validate-sps2/p2/p3 and the P10 gate). All green, or every red item is
   either fixed or explicitly explained as pre-existing with proof.
   Client/lifecycle projects: handoff requires
   `python3 framework/sps2/tools/check_kickoff.py <project>` to pass —
   proof the kickoff questionnaire was answered before any build
   (COMPANY-LIFECYCLE.md Phase 0).
3. **Live verification.** Exercise the changed behavior for real — run the
   command, load the page, do the install/uninstall round-trip, whatever
   proves the change works outside of unit tests. A fix that was never
   executed is not a fix.
3b. **Meaningful-test audit** (project/app work): read the tests that
   passed for the changed behavior — do they actually assert the outcome,
   or do they pass vacuously (no assertions, tautological checks, mocks
   answering everything)? A vacuous test is a FAIL, not a pass.
3c. **Clean-environment test** (delivery handoffs): from a fresh clone +
   the written setup docs only, install and run the app. If the docs
   miss a step, the docs are not done.
4. **Adversarial second opinion.** For any non-trivial change, a second
   agent (or a fresh self-review pass with refutation instructions)
   attempts to find flaws. Findings are fixed or refuted with evidence
   before the handoff.
4b. **Self-verification loop.** Before any "task complete" claim, the agent
   runs the relevant machine checks itself — the law checker
   (`check_laws.py`), the validators affected by the change, and the local
   test battery — and ATTACHES the output to the handoff. Claiming done
   with unverified work violates this checkpoint; "it should pass" is not
   evidence.
5. **Honesty audit.** Every claim in the summary/report must be traceable
   to a command output, a file, or a commit. Claims written from intent
   instead of evidence are the defect class to hunt here.
6. **Checkpoint record.** Append to `./.sps/handoff.md` (or the task's
   todo entry): what was verified, with what command, and the result.
   Format: `CHECKPOINT <date>: <verdict PASS/FAIL> — <what ran> — <result>`.
6b. **Backup before hand-back.** Run `bash scripts/sps-backup.sh snapshot`
   at every G1, G2, section approval, and handoff, so `.sps/` state at each
   gate is recoverable (restore: `sps-backup.sh restore <snapshot> --yes`).

## Gating rule

The handoff message may only be sent after step 6 records a PASS. If any
step fails, the task returns to `doing` — the user is told what failed and
what is being fixed, but the work is not handed over as done.

## Robustness requirements

- The checkpoint must run against the FINAL state (after the last edit);
  stale verification of an earlier state does not count.
- "Trust me, it works" is never a checkpoint result. Evidence or it failed.
- Pre-existing failures do not block a handoff when identified with proof
  (commit where they were introduced, reproduction command), but they must
  be named in the handoff, not hidden.
