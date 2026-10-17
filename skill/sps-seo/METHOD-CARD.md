# SPS-SEO Method Card

Read this document at the start of any SEO session.

---

## 1. Mandatory Step 0: The SEO Discovery Grill

Before writing any metadata, robots rules, or structured data, align with the
user on four parameters:

```
┌────────────────────────────────────────────────────────────────────────┐
│               SPS-SEO MANDATORY DISCOVERY GRILL                        │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Canonical Host & Scheme:                                            │
│    • Production origin (e.g. https://example.com) — ONE canonical      │
│    • www vs apex decision; redirects for the loser                     │
│    • Never canonicalize to localhost/loopback/private hosts            │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Indexing Scope:                                                     │
│    • Which routes are indexable vs noindex (admin, drafts, thank-you)  │
│    • Existing robots.txt directives that must be preserved             │
│    • Sitemap source: static routes, CMS items, or both                 │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Structured Data Type(s):                                            │
│    • LocalBusiness (NAP, hours, geo)?                                  │
│    • Product/Offer (price, currency, availability)?                    │
│    • Article (headline, author, dates)?                                │
│    • Multilingual → hreflang pairs with mandatory return links         │
├────────────────────────────────────────────────────────────────────────┤
│ 4. Enforcement Mode:                                                   │
│    • advisory during development; deployment gate before ship          │
│    • Who receives the audit report (section evidence packet)           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The 6-Step Loop (SKILL.md §📋) is the session spine

Discover → Metadata → Indexing → Structured data → Performance hygiene → Gate.
Do not skip to the audit at the end: the gate exists to verify, not to discover.

## 3. Anti-hallucination rules

- Metadata is **generated from real page content** (`generate_metadata_from_content`).
  If the content doesn't state it, the metadata doesn't claim it.
- CWV thresholds come from the engine's documented tables only —
  `assert_no_invented_thresholds` exists because invented numbers were a
  real failure mode.
- Never claim a sitemap URL is valid without the robots-allowance cross-check
  (`is_path_allowed_by_robots`).
- Never hand-edit tool output. Re-run.

## 4. Evidence discipline

Every SEO section ends with:
1. The deployment-mode audit report (text/md) attached to the section evidence.
2. The artifacts digest recorded — a later build change invalidates it.
3. Any warning dispositioned in writing (why it's acceptable, or fixed).
4. CRITICAL count of **zero** before the section's manual user check.
