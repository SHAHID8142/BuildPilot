# Parallel Subagent Playbook

Per-section parallel execution. One section at a time; inside a section,
specialist agents run in parallel, then results converge for the DoD.

## Section team (4 lanes)

| Lane | Agent | Responsibility | Output |
|---|---|---|---|
| CMS | `cms-agent` | schema, admin UI, content API, seed data, round-trip proof | cms-foundation.md + CMS code |
| UI/UX | `ui-agent` | storefront slice per taste direction, responsive, a11y | section UI + design-system.md update |
| Content/SEO | `content-agent` | copy drafting (SPS voice), meta, structured data, alt text | content-model.md + copy files |
| Test/Verify | `test-agent` | unit/lint/typecheck, live round-trip, Lighthouse, mobile viewport | verification evidence |

Optional 5th lane: `review-agent` (web-design-guidelines + impeccable critique)
runs after convergence, before the approval packet.

## Rules

1. **One section in flight.** Lanes run in parallel only within the current
   approved section. Never parallelize across sections.
2. **Shared state is serialized.** Only the orchestrator writes
   `./.sps/*.md`. Subagents return diffs/reports; the orchestrator merges into
   memory. Never two agents writing the same file concurrently
   (multi-agent write serialization).
3. **Surgical scope.** Each lane touches only its own files. CMS lane owns
   admin/schema/API; UI lane owns storefront components; overlap is resolved
   by the orchestrator.
4. **Evidence before claims.** Each lane must return actual verification
   output (test runs, screenshots, Lighthouse scores) — never "should pass"
   ([verification-before-completion] pattern).
5. **Taste single-sourcing.** All lanes read the ONE taste direction from the
   approved plan; UI lane is the only lane that applies taste skills.
6. **Karpathy laws apply to every lane.** Surgical edits, no speculative
   features, visible success criteria.
7. **Convergence gate.** Orchestrator merges lane outputs → runs SECTION-DOD →
   approval packet → user manual check → next section.

## Handoff format (lane → orchestrator)

```
Section: <id>
Lane: <cms|ui|content|test>
Done: <what shipped>
Files: <changed paths>
Verification: <actual command output / screenshot path>
Blockers: <none | list>
```

## Failure handling

- A lane fails verification → fix within the lane, re-run, re-report.
- Two lanes conflict on a file → orchestrator decides ownership, one lane
  redoes the merge.
- Section DoD fails → do not submit approval packet until green.

## Full-profile bonus lanes

When the project needs them (full profile / matching stack):
- `db-agent` (supabase / prisma skills) for schema-heavy sections
- `mobile-agent` (vercel-react-native-skills) for app sections