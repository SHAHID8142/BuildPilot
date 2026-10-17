# Section Definition of Done (DoD)

A section may be submitted for approval only when every applicable item passes.
Mark N/A with reason when a system is disabled.

**One-Section-One-Go law:** each section ships UI + CMS + content + SEO +
Lighthouse + deploy-readiness together, then the user manually checks it live,
gives feedback, and the agent fixes before the next section starts.

---

## 1. Standardized Code Marker Syntax (B6)

To maintain clarity across multi-agent workflows, sections must be wrapped with standardized comment markers:

```html
<!-- SPS:SECTION name="hero" -->
<!-- SPS:CMS_FIELDS ["title", "subtitle", "cta_primary", "bg_image"] -->
<!-- SPS:READS_FROM db.getPageContent('/') -->
<section id="hero">
  ...
</section>
<!-- SPS:ENDSECTION -->
```

For JSX / TypeScript components:
```tsx
// SPS:SECTION name="featured_packages"
// SPS:CMS_FIELDS ["items", "eyebrow", "title"]
// SPS:READS_FROM db.getCollectionItems('packages')
```

---

## 2. Product & CMS Requirements

1. Storefront UI matches approved direction.
2. Content inventory complete in `content-model.md`.
3. CMS fields + admin UI cover that inventory (100% surface coverage).
4. Demo/seed/media replace/hide/delete works.
5. **Round-trip proof**: admin edit → database layer → live storefront.
6. Empty / loading / error / unpublished states handled.

---

## 3. Quality & Mobile Hard Gate

7. Mobile-first responsive (320px → 1440px) + [MOBILE-LOW-END.md](MOBILE-LOW-END.md).
8. A11y AA standards + `prefers-reduced-motion` compliance.
9. SEO/meta when page-level applicable:
   - title, meta description, canonical, Open Graph, structured data where relevant
   - SEO routed via `ai-seo` skill (or SPS `seo` fallback) per SKILL-ROUTER.md
10. **Lighthouse gate** (run on the live section):
    - Performance: >= 90
    - SEO: 100
    - Accessibility: 100
    - Best Practices: 100
    - Evidence: screenshot + scores attached to the approval packet
11. Zero lint/typecheck/build blockers.
12. Design gate laws respected (no fake dummy buttons, curated palette).

---

## 4. Content & CMS Copy (per-section, user-editable)

13. All section copy is drafted (headlines, body, CTAs, alt text) — SPS drafts, user edits.
14. Content inventory for this section complete in `content-model.md`.
15. Drafted copy is loaded through the CMS/content layer (no hardcoded final copy).
16. Empty / loading / error / unpublished states handled.

---

## 5. Engineering & Workspace Hygiene

17. Components split (modular, focused, single concern).
18. Standard agent markers present (`SPS:SECTION`, `SPS:CMS_FIELDS`, `SPS:READS_FROM`).
19. Code cleanup gate: dead code removed, imports organized.
20. Todos closed or explicitly deferred with reasons.
21. Security basics verified (input validation, traversal guards, auth check).
22. Workspace hygiene: zero duplicate assets left behind ([WORKSPACE-HYGIENE.md](WORKSPACE-HYGIENE.md)).
23. **No duplicate logic:** before adding a function/component, grep for an
    existing one; extending beats duplicating.
24. **No hardcoded environment config:** URLs, IDs, ports, and env-ish values
    come from config/env — never baked into source (secrets are a separate,
    stricter ban).
25. **Concurrency basics:** duplicate form submissions and double-click
    actions don't create duplicates; concurrent updates don't silently
    overwrite each other (last-write or optimistic lock — say which).
26. **Error messages are user-safe:** production failures never leak stack
    traces, SQL, file paths, or internal hosts; details go to logs only.
27. **Dependency health:** before a section ships, `npm audit` (or the
    stack's equivalent) runs; new highs are fixed or explicitly accepted
    by the user in the approval packet.

---

## 6. Deploy-Readiness (per section)

28. Build passes for the deploy target (e.g. `vercel build` / framework build).
29. Env vars used are documented in `./.sps/handoff.md` (never committed).
30. Section works on a preview/deploy URL, not only localhost.

---

## 7. Memory Updates

31. `handoff.md`, `content-model.md`, `section-registry.md` updated.
32. Any design pivots written to `design-system.md` + `changelog-sps.md`.

---

## 8. Approval Gate & Manual Check Loop

33. Send the appropriate Tier 1 or Tier 2 approval packet ([APPROVAL-PACKETS.md](APPROVAL-PACKETS.md)) before proceeding to the next section (unless in batch approval mode).
34. **Manual check loop:** the user checks the section live (storefront + CMS admin).
    - On feedback: fix items, re-run verification, resubmit.
    - Only after the user confirms OK does the next section start.
