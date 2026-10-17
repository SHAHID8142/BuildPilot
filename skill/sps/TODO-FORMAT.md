# Todo Format

Every section/chunk must have a written todo list in
`./.sps/section-todos/<section>.md` (and host todo tooling when available).

## Template

```markdown
# Section: <name>
Status: planning | building | blocked | awaiting-approval | approved
Plan summary:
Skills to use:
Roles:

## Tasks
- [ ] id: S1-01
  task:
  why:
  how:
  evidence:
  status: todo | doing | done | deferred
```

## Rules

1. Break sections into the smallest safe tasks
2. Include CMS tasks in the same list when CMS is enabled
3. Include cleanup + round-trip proof tasks before approval
4. Update status as work proceeds
5. Deferred tasks need a reason and a follow-up owner/section
