# Asset Weight Budget

Default budgets for UI work unless the user explicitly approves higher limits.
These support the low-end mobile gate.

## Default mobile budgets

| Asset | Default budget | Notes |
|---|---|---|
| Hero image (mobile) | ≤ 200 KB | Prefer AVIF/WebP; provide dimensions |
| Inline content image | ≤ 120 KB | Lazy-load below the fold |
| Icon / logo SVG | prefer SVG | Raster icons ≤ 20 KB |
| Background video (mobile) | disabled by default | Use static poster instead |
| Lottie / motion JSON | disabled by default on mobile | Desktop-only unless approved |
| Animation libraries | 0–1 max | Prefer CSS; avoid stacking GSAP + Lottie + Three |
| Font files | ≤ 2 families, ≤ 2 weights each | Subset when possible |

## Hard bans on mobile unless approved

- autoplay video with sound
- looping full-bleed video backgrounds
- uncompressed PNG/JPEG heroes
- multiple continuous animation loops
- particle systems / heavy WebGL as the default path

## Desktop may exceed mobile

Desktop can use richer assets only when:

1. mobile keeps the cheaper path
2. the approval packet states both budgets
3. reduced-motion / data-saver behavior is considered

## Approval packet fields

For UI chunks that add media or motion, include:

- estimated asset weight
- mobile vs desktop delivery plan
- whether lazy-loading / posters / breakpoints are used

## Verification

Flag as Fail if:

- mobile ships a >200 KB hero without approval
- mobile autoplays heavy media
- motion libraries are loaded on mobile with no lightweight fallback
