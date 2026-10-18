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
   - SEO routed via `sps-seo` skill (fallback: `ai-seo`) per SKILL-ROUTER.md
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

13. All section copy is drafted (headlines, body, CTAs, alt text) — SPS drafts, user edits — and passes the copy gate: `bash scripts/sps-copycheck.sh <project> --mode deployment` exits 0 ([COPY-GATE.md](COPY-GATE.md)).
14. Content inventory for this section complete in `content-model.md`.
15. Drafted copy is loaded through the CMS/content layer (no hardcoded final copy).
16. Empty / loading / error / unpublished states handled.

---

## 5. Engineering & Workspace Hygiene

17. Components split (modular, focused, single concern); source files
    respect the split limits ([FILE-SPLITTING.md](FILE-SPLITTING.md)) —
    300-line soft / 500-line hard cap; files over the soft limit carry a
    written reason in the approval packet.
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
28. **Data-layer correctness:** monetary values stored as integers in the
    smallest unit (cents, never floats); timestamps stored in UTC (convert
    at the display edge); foreign-key constraints declared with explicit
    cascade rules (`ON DELETE`/`ON UPDATE` stated, not implied); multi-step
    writes wrapped in a transaction (partial failure leaves no half-state).
29. **Web/API hardening:** parameterized SQL only (no string-built queries);
    tight CORS (explicit origin allowlist, never `*` with credentials);
    CSRF protection on cookie-authenticated state-changing routes (SameSite
    is a layer, not the fix); rate limiting on auth + public write
    endpoints; webhook routes verify signatures before processing;
    user-supplied URLs are SSRF-guarded (no private/loopback/link-local
    fetches); prompts that embed user input are delimited and sanitized
    (injection-safe).
30. **Session & auth hygiene:** cookies set `HttpOnly` + `Secure` + `SameSite`;
    session tokens expire and refresh tokens rotate on use; passwords hashed
    with a modern KDF (bcrypt/argon2, never SHA/plain); user email verified
    before account actions that can affect others; MFA offered for admin
    accounts when the platform supports it.
31. **Production posture:** debug/toolbars off in production builds; security
    headers set (`Strict-Transport-Security`, `Content-Security-Policy`,
    `X-Frame-Options`/`frame-ancestors`); log scrubbing — no tokens,
    passwords, or personal data in log lines; sensitive data never in URLs.
32. **Dependency & source hygiene:** lockfile pinned (exact versions
    committed); unused dependencies removed; no `console.log` or TODO
    markers left in shipped code; no stubbed functions pretending to work
    (a stub is either implemented or explicitly gated behind a feature flag);
    no deprecated framework APIs.
33. **Env validation on startup:** required env vars are validated at boot
    with named errors (fail fast, not mid-request).
34. **Health endpoint:** the app exposes `/health` (or stack equivalent)
    returning dependency status; graceful shutdown drains in-flight
    requests; background jobs retry with exponential backoff and are
    idempotent (webhook retries never double-apply).
35. **Privacy & legal surfaces (public-facing projects):** cookie consent
    banner when any non-essential cookie/tracker loads; Privacy Policy and
    Terms pages exist and name the actual data collected; self-serve
    account deletion flow when the app has user accounts (regulatory
    baseline, and it's cheaper to build than to retrofit).
36. **API contract:** public/API routes are documented (OpenAPI/Swagger or
    equivalent in-repo doc) and versioned (`/api/v1/…`) so consumers
    survive changes; breaking changes bump the version, never silently
    reshape an existing route.
37. **Hook & format automation:** pre-commit hooks run lint/format so the
    cleanup gate is mechanical, not aspirational; an automated formatter
    (Prettier/ruff/stack equivalent) is configured and its output committed.
38. **Uploads scrubbed & DB tenancy:** uploaded images strip EXIF/GPS
    metadata before storage; multi-tenant data enforces row-level security
    (or an equivalent scoping check in every query path) — one tenant's ID
    in a URL must never read another tenant's row.
39. **security.txt:** production sites expose `/.well-known/security.txt`
    (contact for security reports) — a one-file signal that reports are
    welcome and where they go.

---

## 6. Deploy-Readiness (per section)

40. Build passes for the deploy target (e.g. `vercel build` / framework build).
41. Env vars used are documented in `./.sps/handoff.md` (never committed).
42. Section works on a preview/deploy URL, not only localhost.
43. **Observability wired before handoff:** structured JSON logging (one
    line per request/exception, parseable); frontend + backend error
    tracking reporting to a sink the owner actually sees (Sentry-class or
    the platform's built-in); basic performance monitoring on the critical
    routes. A crash on a real user's device must reach the owner, not
    vanish.
44. **Uptime & alerts:** external uptime monitoring on the production URL
    with an alert channel the owner checks (email/chat) — "the site is
    down" must be discovered by an alert, never by the owner's customer.
45. **Resilience posture matches the platform:** traffic/HA needs were
    asked at kickoff (expected traffic, uptime target); if the platform
    runs multiple instances, a load balancer sits in front; reverse
    proxy timeouts are set (no 60s hangs holding workers); feature flags
    gate any high-risk change so rollback is a toggle, not a redeploy.
46. **Spending guardrails:** cloud/AI API accounts used by the project have
    hard spending limits/budget alerts set — an integration bug can cost
    real money overnight.

---

## 7. Memory Updates

47. `handoff.md`, `content-model.md`, `section-registry.md` updated.
48. Any design pivots written to `design-system.md` + `changelog-sps.md`.

---

## 8. Approval Gate & Manual Check Loop

49. Send the appropriate Tier 1 or Tier 2 approval packet ([APPROVAL-PACKETS.md](APPROVAL-PACKETS.md)) before proceeding to the next section (unless in batch approval mode).
50. **Manual check loop:** the user checks the section live (storefront + CMS admin).
    - On feedback: fix items, re-run verification, resubmit.
    - Only after the user confirms OK does the next section start.
51. **Product proof — the section must demonstrate it runs:** backend/API →
    run the tests or boot the app and attach output; UI → screenshot or
    rendered-HTML evidence attached to the approval packet; docs-only →
    not applicable. A section is not done until the proof exists. The
    approval packet includes the proof, not a claim about it.
52. **Fresh-context review:** every section gets a review by an agent that
    did not author it (second opinion) before the approval packet is
    presented.
