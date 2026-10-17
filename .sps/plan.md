# SPS Project Plan

Status: draft | pending-approval | approved | rejected | superseded
Approved by:
Approved date:

## 1. Goal & success criteria

- Goal:
- Success criteria (measurable, one per line):
  - 

## 2. Stack

| Layer | Choice | Known / Assumed / Unverified |
|---|---|---|
| Frontend |  |  |
| Backend / data |  |  |
| CMS |  |  |
| Auth |  |  |
| Deploy |  |  |
| Mobile policy |  |  |
| Test tooling |  |  |

## 3. Section inventory (build order)

One section at a time. Each section ships UI + CMS + content + SEO + tests
together, then stops for the user's manual check.

| # | Section | CMS-coupled | Taste skill | Deploy step |
|---|---|---|---|---|
| 1 | Navbar / foundation |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |

## 4. CMS plan

- Foundation first: auth / admin shell / content API / media / seed (yes/no)
- Per-section coupling: storefront + CMS controls ship together
- CMS skill: `sps-cms` (SHAHID8142/sps-cms) — mandatory when CMS enabled

## 5. Design direction

- Direction (1-2 sentences):
- Taste skill (from SKILL-ROUTER):
- Palette / type / motion notes:

## 6. SEO & Lighthouse target (per section)

- Performance: >= 90
- SEO: 100
- Accessibility: 100
- Best Practices: 100
- Structured data / meta plan:

## 7. Deploy

- Target:
- Readiness steps (domain, env, build, preview):

## 8. Mobile behavior

- Low-end dual path needed? (yes/no)
- Asset budget max 1.5MB initial payload

## 9. Subagent plan (per section)

| Section | Agents in parallel | Roles |
|---|---|---|
|  | CMS, UI/UX, test, review |  |

## 10. Verification plan (per section)

- Unit / typecheck / lint:
- CMS round-trip proof:
- Lighthouse run:
- Manual check loop: user verifies live, feedback, fix, next section

## Open questions

1.
2.

## Approval

- [ ] Plan approved — start section 1
- [ ] Changes requested: