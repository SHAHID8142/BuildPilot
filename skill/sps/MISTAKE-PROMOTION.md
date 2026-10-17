# Mistake → Rule Promotion

Use this after recording mistakes in `./.sps/mistakes.md`.

## Trigger

When the same class of mistake appears **2 or more times** in one project, or
the user says a lesson should stick permanently:

1. Stop and ask for promotion.
2. Do not silently rewrite personal defaults.
3. Offer exactly one of these scopes:

| Scope | Write to | When |
|---|---|---|
| Project-only rule | `./.sps/profile.md` | Default for project-specific lessons |
| Personal default | `~/.sps/personal-defaults.md` | Only with explicit user approval |
| Session-only reminder | chat / handoff note | Temporary, do not promote |

## Ask format

```markdown
## Mistake promotion

Similar mistake count: N
Pattern:
Proposed rule:
Suggested scope: project-only | personal-default | session-only

Approve promotion? (project-only / personal-default / session-only / skip)
```

## After approval

1. Write the rule to the chosen file.
2. Mark the mistake entries as `promoted: yes` with date and scope.
3. Mention the new rule in the next approval packet if relevant.

## Do not promote

- one-off typos
- stack choices that only apply to a single experiment
- host-specific quirks that belong in `./.sps/agent.md`
