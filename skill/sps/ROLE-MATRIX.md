# Role Matrix

For every chunk, the agent must declare and play the roles needed — not only
"frontend developer".

## How to use

1. List applicable roles for the chunk
2. For each role, state the acceptance check
3. Put the role list in the approval packet and todos
4. Do not mark the chunk done until each applicable role's check passes

## Common roles

| Role | Asks |
|---|---|
| Visitor | Is it clear, fast, trustworthy? |
| Customer | Can I complete the goal without confusion? |
| Owner / business | Does this support the business outcome? |
| Admin / CMS editor | Can I manage every content element safely? |
| Data steward | Validation, storage, privacy, backups? |
| Security | Authz, injection, secrets, upload safety? |
| Mobile user | Usable at 320px without hover dependency? |
| Accessibility | Keyboard, contrast, semantics, reduced motion? |
| Ops / deploy | Can we ship/rollback this slice? |
| Next agent / teammate | Markers + memory enough to continue? |

## Example: contact form

Roles: Visitor, Customer, Owner, Admin (lead inbox), Data steward, Security,
Mobile user, Accessibility.

Each role gets at least one concrete check in the todo list.
