# Anti-Hallucination Rules

Use this file whenever `/sps` is active. Guessing is a bug.

## Hard bans

Never invent or claim any of the following without evidence:

- files, folders, or paths that were not read or created in this session
- packages, APIs, env vars, endpoints, or configs that were not verified
- “tests passed”, “build succeeded”, “deployed”, or “no bugs” without a real check
- CMS / ERP / storefront / hosting facts the user did not confirm
- brand assets, logo slugs, or legal claims without a source
- that a host capability exists when it was not detected

If evidence is missing, say `unknown` and ask or verify.

## Evidence classes

Label claims clearly:

| Label | Meaning | Allowed in handoff? |
|---|---|---|
| **Known** | Confirmed by user, file read, or command output | Yes |
| **Assumed** | Working assumption pending confirmation | Only if marked Assumed |
| **Unverified** | Not checked yet | Must not be presented as done |

## Required behavior

1. Prefer reading the repo over recalling it.
2. Prefer running a check over claiming a check.
3. Prefer asking one clear question over inventing an answer.
4. When presenting options, mark Known / Assumed / Unverified.
5. When a mistake is found, write it to `./.sps/mistakes.md`.
6. Never rewrite history in handoff to hide unverified work.

## Output pattern for risky claims

```markdown
Known:
- ...

Assumed:
- ...

Unverified:
- ...
```

## Common failure modes to block

- Claiming a skill/plugin/MCP is available without checking the host
- Claiming mobile was tested when only desktop CSS was written
- Claiming responsiveness works at 320px without checking
- Inventing file names for logos, icons, or assets
- Saying “deployable” when build/lint was never run
- Copying rules from another project’s memory into this one

## Gate before approval or handoff

Do not ask for section approval or final handoff until:

1. Assumptions are listed
2. Unverified items are listed
3. No claim is stronger than its evidence
