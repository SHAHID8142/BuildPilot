# `/sps sync` — CMS / storefront debt mode

Primary command: `/sps sync` (Aliases: `/sps cms-sync`, `/sps couple`).

## When to use

- Pending projects blocked on CMS
- Legacy storefront built before admin controls
- Audit found CMS debt

## Flow

1. Boot `/sps` memory + host lock
2. Run or refresh audit focusing on CMS coupling
3. Write `./.sps/cms-debt.md` (section-by-section debt list)
4. Ensure CMS Foundation exists (build if missing)
5. For each indebted section, run the CMS-coupled section loop
6. Prove round-trips; update registry; stop for approvals
7. Do not redesign the whole site unless the user asks — prefer coupling first

## Output

- `cms-debt.md` with statuses
- Updated `content-model.md`
- Handoff pointing at the next indebted section
