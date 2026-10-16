# Auto-Sync & Single Source of Truth Protocol

A major flaw in naive headless CMS setups is data fragmentation: editing a product's price in an admin form fails to update the Homepage slider, or editing a title produces a 404 broken slug.

SPS-CMS eliminates this entirely with three mathematical synchronization laws.

---

## 1. The Single Source of Truth Law

A dynamic entity (Product, Package, Service) is stored **exactly once** in the database. Every storefront location queries the same record with deterministic filters:

```
                          ┌───────────────────────────┐
                          │   sps_collections Table   │
                          │   (Single Source of Truth)│
                          └─────────────┬─────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────┐
│ 1. Homepage Grid      │   │ 2. Archive Grid       │   │ 3. Detail Page        │
│ WHERE collection =    │   │ WHERE collection =    │   │ WHERE collection =    │
│ 'packages' AND        │   │ 'packages' AND        │   │ 'packages' AND        │
│ show_on_homepage = 1  │   │ status = 'published'  │   │ slug = :slug          │
└───────────────────────┘   └───────────────────────┘   └───────────────────────┘
```

### Auto-Sync Behavior:
- When a client edits the price of "Bali Tour" from `$650` to `$580` in `/admin`, **zero frontend cache clearance is needed**; all three queries read the updated database row immediately.
- When a client toggles `Show on Homepage` to `OFF`, the package immediately disappears from the Homepage Featured section while remaining visible on the `/packages` archive page.

---

## 2. The Auto-Slug & Zero-404 Guarantee

Broken URLs destroy client trust and SEO. SPS-CMS enforces strict slug lifecycle rules:

1. **Auto-Generation:**
   - As the client types the title ("5 Days in Bali & Nusa Penida"), the slug input automatically generates a sanitized version (`5-days-in-bali-nusa-penida`).
2. **Sanitization Rules:**
   - Lowercase all ASCII characters.
   - Replace spaces and special characters with single dashes (`-`).
   - Strip leading/trailing dashes.
   - Remove unsafe URL characters (`?`, `&`, `#`, `%`, `/`).
3. **Uniqueness & Conflict Prevention:**
   - If a package named "Bali Tour" exists (`slug: bali-tour`), creating another with the same title automatically appends a suffix (`slug: bali-tour-2`).
4. **Permanent Canonical Route:**
   - Detail pages MUST use dynamic parameters:
     - In Astro: `src/pages/[collection]/[slug].astro`
     - In Next.js: `app/[collection]/[slug]/page.tsx`

---

## 3. The Instant Revalidation Contract

To achieve millisecond updates without full site rebuilds:

### In Astro (SSR / Hybrid Mode):
- Use Astro Server Endpoints (`src/pages/api/cms/*.ts`) or `Astro Actions`.
- Database queries inside `.astro` files execute on-demand at request time, ensuring fresh data on every page refresh.

### In Next.js (App Router):
- Use Server Actions (`'use server'`) with `revalidatePath('/[collection]')`, `revalidatePath('/')`, and `revalidatePath('/[collection]/[slug]')`.
- Updates become visible across the CDN in under 100 milliseconds.
