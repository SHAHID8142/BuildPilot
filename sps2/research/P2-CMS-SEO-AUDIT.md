# P2 CMS and SEO Audit

Phase: roadmap P2 (audit phase 06). Research only. No CMS or SEO code was written.

---

## 1. CMS-first requirement (user-mandated)

> If CMS is declared during planning, the implementation must be CMS-ready from the
> beginning rather than building a hardcoded frontend first and retrofitting CMS
> later.

**Evidence status**: this is a *user policy*, not an ecosystem finding. Sources
support the individual mechanisms below; they do not establish "CMS-first" as a
universal industry standard. Recorded honestly as such.

### Pattern SPS should adopt

```text
requirement declares CMS
  -> content model defined BEFORE page components
  -> data access layer abstracted behind a typed content interface
  -> page components render from that interface, never from hardcoded literals
  -> draft/preview separation present from the first route
  -> SEO metadata derived from content fields, not hand-written per page
```

**Evidence**: Next.js documents Draft Mode as a first-class routing capability
(SRC-019) and separates ISR caching from draft behaviour. This supports
"design the content boundary before the page", because the framework already
treats draft vs published as an architectural concern rather than a later patch.

**Open gap**: content-modelling discipline (schema design, versioning, role
separation, media libraries, audit logs) was **not** established from a primary
source in P2. The Contentful reference returned HTTP 429 and was not retried in
depth. CAP-032 is therefore `RESEARCH_FURTHER`, not `KEEP`.

### What must not happen

A frontend must never be built such that adding a CMS requires rewriting page
components. If content is hardcoded, the CMS requirement was violated even if the
final site is "CMS-powered".

---

## 2. SEO as a first-class capability (user-mandated)

SEO must not be an optional afterthought. The P2 audit separates it into four
distinct roles, because conflating them is what produced the legacy defect where
a "SEO" skill did not exist but a router referenced it.

| Role | SPS artefact | Status |
|---|---|---|
| **Policy** (non-negotiable rules) | canonical URL required; one H1; images need alt text | Proposed, not yet enforced |
| **Capability** (discrete ability) | technical SEO audit; metadata generation | Proposed |
| **Skill** (executable workflow) | metadata templating; sitemap generation | Proposed |
| **Verifier** (blocks without evidence) | SEO checks that fail a transition | Proposed |

### Evidence-backed SEO coverage

From SRC-016 (Google Search Central, official):
- XML sitemaps and sitemap indexes
- `robots.txt` and `noindex` control
- Canonicalisation for duplicate content
- Structured data (JSON-LD eligible for rich results)
- Meta descriptions, titles, image alt text
- Search Console integration and monitoring

From SRC-017 (web.dev, official): **CLS good <= 0.1, CLS poor > 0.25**, confirmed
verbatim with stated derivation ("shifts from 0.15 and higher were consistently
perceived as disruptive"; 0.1 "strikes a better balance between quality of
experience and achievability").

### Unresolved: LCP and INP thresholds

**The numeric LCP and INP thresholds were not retrieved.** SRC-018 confirms LCP,
CLS and INP are the Core Web Vitals set, but the threshold table was absent from
the retrieved content, and two further attempts did not recover it.

Recorded as **CONF-001 / CAP-028 / `RESEARCH_FURTHER`**, confidence LOW.

> SPS 2.0 must NOT encode unverified LCP or INP numbers into a verifier.

An SEO verifier shipping a guessed threshold would be exactly the legacy failure
mode: a mechanism that looks like verification but encodes a fabricated fact.

### Remaining SEO areas not yet researched in P2

hreflang, pagination, redirects taxonomy, JavaScript-rendering implications,
international SEO, local SEO, entity/knowledge-graph, schema validation tooling,
search-console automation. These are named in the brief; none was researched to
evidenced depth in P2 and none is claimed.

---

## 3. Rendering and caching as verifiable evidence

From SRC-019: the `x-nextjs-cache` header exposes `HIT`, `STALE`, `MISS` and
`REVALIDATED`.

**Opportunity**: this is a concrete instance of the general rule SPS needs —
*system state should be observable in a machine-readable form, not inferred from
narrative*. The same pattern applies to deployment verification and CMS publish
state (CAP-030).

**Caveat recorded**: SRC-019 also documents that the default filesystem cache is
per-instance, so on-demand revalidation only invalidates the instance that
received the request. Any SPS verifier asserting global cache coherence from a
single request would be wrong.

---

## 4. Recommendations

1. Content model precedes page components whenever CMS is in scope — **policy**.
2. CMS capabilities stay project-local and separately verifiable (never bundled).
3. SEO splits into policy / capability / skill / verifier, with the **verifier**
   being the only component that can block a transition.
4. Encode only **verified** thresholds (CLS yes; LCP/INP no).
5. Content-modelling depth, hreflang, international and local SEO are
   `RESEARCH_FURTHER`.