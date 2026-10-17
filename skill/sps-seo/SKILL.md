---
name: sps-seo
description: >
  Technical SEO engineering standard for ALL web stacks (Astro, Next.js, Nuxt/Vue,
  SvelteKit, Laravel/PHP, Django/Python, Go, static HTML). Triggered when the user
  invokes /sps-seo or /sps seo, asks for SEO metadata, canonical URLs, robots.txt,
  sitemap.xml, schema.org JSON-LD structured data, Open Graph / Twitter cards,
  Core Web Vitals, hreflang/multilingual SEO, LocalBusiness / e-commerce schema,
  image alt/filename SEO, or a pre-deployment SEO audit. Enforces fail-closed
  deployment gating: a build with CRITICAL SEO findings must not ship.
---

# /sps-seo (v1.0.0 Technical SEO Standard)

`/sps-seo` is the SPS technical-SEO specialist. It turns any codebase's output
into a **search-engine-complete artifact**: correct metadata, canonical
integrity, governed robots/sitemap, JSON-LD structured data, Core Web Vitals
hygiene, and a fail-closed pre-deployment audit.

Read [METHOD-CARD.md](METHOD-CARD.md) at the start of every SEO session.

---

## 🌍 Capability Matrix

```
┌────────────────────────────────────────────────────────────────────────┐
│               SPS-SEO v1.0.0 CAPABILITY MATRIX                         │
├───────────────────┬────────────────────────────────────────────────────┤
│ Metadata Engine   │ title, description, canonical, robots meta, OG +  │
│                   │ Twitter cards — generated from content, validated │
│                   │ against length/duplication/private-host rules.    │
├───────────────────┼────────────────────────────────────────────────────┤
│ Indexing Gov.     │ robots.txt generation + parsing, sitemap.xml      │
│                   │ build (50k-URL limit enforced), sitemap index,    │
│                   │ path-allowance cross-check (URL allowed by robots)│
├───────────────────┼────────────────────────────────────────────────────┤
│ Canonical Law     │ Every page has exactly one canonical; absolute    │
│                   │ https; no private/loopback hosts; no cross-dupes. │
├───────────────────┼────────────────────────────────────────────────────┤
│ Structured Data   │ schema.org JSON-LD: LocalBusiness, Product/Offer, │
│                   │ Article; hreflang pairs validated for return links│
├───────────────────┼────────────────────────────────────────────────────┤
│ On-Page Analysis  │ heading hierarchy (single h1, no skips), link     │
│                   │ audit (broken anchors, nofollow hygiene)          │
├───────────────────┼────────────────────────────────────────────────────┤
│ Media SEO         │ image filenames, alt text, lazy-loading, explicit │
│                   │ dimensions (CLS protection), render_image_tag     │
├───────────────────┼────────────────────────────────────────────────────┤
│ Core Web Vitals   │ LCP / CLS / INP evaluation against documented     │
│                   │ thresholds — invented thresholds are rejected.    │
├───────────────────┼────────────────────────────────────────────────────┤
│ Deployment Audit  │ 19-dimension audit, dual mode: advisory (report   │
│                   │ only) vs deployment (exit 1 on ANY critical).     │
└───────────────────┴────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start

```bash
# Audit a build directory (advisory — report only, exit 0)
python3 framework/sps2/tools/seo_audit.py build/ --mode advisory

# Pre-deployment gate (exit 1 on any CRITICAL — use in CI)
python3 framework/sps2/tools/seo_audit.py build/ --mode deployment

# JSON report for tooling; markdown for the audit packet
python3 framework/sps2/tools/seo_audit.py build/ --mode deployment --format json
python3 framework/sps2/tools/seo_audit.py build/ --mode advisory --format md -o audit.md

# Single page / file target
python3 framework/sps2/tools/seo_audit.py build/index.html --mode advisory

# Optional dimension flags
python3 framework/sps2/tools/seo_audit.py build/ --mode deployment \
  --canonical https://example.com/ --multilingual --local --ecommerce
```

---

## 📋 The 6-Step SEO Implementation Loop

1. **Discover** — enumerate routes/pages, the canonical host, and the CMS
   content source (if `/sps-cms` is coupled, sitemap URLs come from CMS items).
2. **Metadata** — generate title/description/OG/Twitter from real page content;
   never invent facts not present in the content. Validate canonicals: absolute
   https, no loopback/private hosts, one per page.
3. **Indexing** — emit `robots.txt` + `sitemap.xml` into the build root. Every
   sitemap URL must be allowed by robots; sitemap must not exceed the 50,000-URL
   limit (engine-enforced: `SitemapLimitError` rather than truncating). The
   sitemap spec's 50MB uncompressed size limit is NOT engine-enforced — keep
   sitemaps well under it (split into a sitemap index if a build approaches it).
4. **Structured data** — add JSON-LD matching the page's real type. `--local`
   validates LocalBusiness (NAP consistency), `--ecommerce` validates
   Product/Offer (price/currency/availability), `--multilingual` validates
   hreflang return-links.
5. **Performance hygiene** — images get alt text, explicit width/height, and
   lazy-loading below the fold; `font-display` checked in CSS; CWV scores come
   only from the documented threshold tables.
6. **Gate** — run the deployment-mode audit. **CRITICAL = do not deploy.**
   Warnings need a noted reason in the section report. Attach the audit report
   (text or md) to the section's evidence.

---

## 🚦 Fail-Closed Deployment Law

- `--mode deployment` exits **1** on any CRITICAL finding. This is the gate —
  never deploy past it, never edit findings out of the report to pass.
- Advisory mode (`--mode advisory`) always exits 0 and is for development
  iteration only. It is **not** a deployment approval.
- The audit report carries an `Artifacts Digest` (sha256 of the audited tree).
  If the build changes after the audit, the audit is stale — re-run it.
- Never hand-edit a generated audit report. Re-run the tool.

## 🧩 Stack Notes

| Stack | Where metadata goes | Notes |
|---|---|---|
| Static HTML | `<head>` directly | use `render_html_meta_tags()` output |
| Astro | `<head>` in layouts | sitemap integration optional; engine output is authoritative |
| Next.js | `metadata` export / Head | canonical from `metadataBase` — verify rendered HTML |
| Nuxt/SvelteKit | `useHead` / `<svelte:head>` | verify rendered output, not just source |
| Laravel/Django/Go | template partial | render server-side; audit the built HTML |

**Verification rule:** the audit runs on **rendered build output**, not source
templates. A correct template with a broken render is a FAIL.

## 🔗 Relationship to /sps and /sps-cms

- `/sps audit` routes here for the SEO dimension of a section audit.
- With `/sps-cms` coupled: published CMS content feeds
  `generate_sitemap_from_cms_items()`; sitemap `lastmod` follows the publish
  timestamp. Storefront + CMS controls ship together (SPS law).
- The BuildPilot framework engine lives at `framework/domain/seo/` — this skill
  is its user-facing standard; keep them in sync.

---

## Hardening Rules (engine-grounded additions)

- **LCP/CLS are engine-evaluated, never asserted:** `evaluate_lcp()` is
  observation-gated (returns unevaluated without a real observation — do not
  fabricate a pass); `evaluate_cls` requires a measured value. Static proxies
  (`analyze_font_display_html`, `analyze_static_shift_prevention`) are code
  checks, not performance proofs — name which one you ran.
- **Thresholds:** Core Web Vitals thresholds come from the engine's config
  (`validate_cwv_config`); `assert_no_invented_thresholds` exists precisely
  because inventing numbers is the classic failure. Never hardcode a
  "good score" that the engine doesn't define.
- **Sitemap/robots invariants:** unpublished records are excluded from
  sitemaps by the generator (strictly, not best-effort); every sitemap URL
  must be robots-allowed; canonical URLs are validated (absolute https, no
  loopback/private hosts). Draft previews stay noindex — never hand-write a
  canonical or robots directive that contradicts the publication state.
- **Structured data:** JSON-LD must match the page's real content; the
  engine's specialized validators (LocalBusiness/`--local`,
  Product/Offer/`--ecommerce`, hreflang/`--multilingual`) are the arbiters —
  don't hand-roll schema checks the engine already runs.
- **Deployment mode is fail-closed:** run audits with `--mode deployment` in
  handoffs; CRITICAL findings exit non-zero and must be fixed before the
  handoff checkpoint, not waived.
- **Share & AI-discovery surfaces:** every indexable page ships a
  purpose-designed social share image (og:image sized 1200×630, not a reused
  logo); external links that open in a new tab carry
  `rel="noopener noreferrer"`; an `llms.txt` at the site root describes the
  site for AI crawlers (what the site is, key pages, contact) alongside
  robots.txt/sitemap.xml.
- **Search Console & off-page:** Google Search Console (or Bing Webmaster)
  verification is part of delivery, not an afterthought — the verification
  record and a first indexing check land in the handoff; a basic backlink
  strategy (directories, partner links, content worth citing) is proposed
  in the lifecycle plan for client jobs rather than left unstated.
- **Email deliverability (when the project sends email):** SPF, DKIM, and
  DMARC DNS records are set and verified before launch — unauthenticated
  mail lands in spam and burns the domain's reputation.
