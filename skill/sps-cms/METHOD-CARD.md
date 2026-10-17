# SPS-CMS Method Card (Universal & Host-Agnostic)

Read this document at the start of any CMS build, refactor, or sync session.

---

## 1. Mandatory Step 0: The Infrastructure & Content Discovery Grill

Before generating or writing any CMS code, the agent **MUST grill and align with the user** on four critical parameters:

```
┌────────────────────────────────────────────────────────────────────────┐
│               SPS-CMS MANDATORY DISCOVERY GRILL                        │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Host & Deploy Target:                                               │
│    • cPanel / Shared Host (e.g. Hostinger, Namecheap, Bluehost)        │
│    • VPS / Cloud Server (Ubuntu, Docker, PM2, Node SSR)               │
│    • Edge / Serverless (Cloudflare Pages, Vercel, Netlify)             │
│    • Container / PaaS (Railway, Render, DigitalOcean App Platform)     │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Database Engine Selection:                                          │
│    • Native MySQL / MariaDB (Default for cPanel/Shared/VPS)            │
│    • Embedded SQLite / LibSQL (Zero-config for Node/VPS/Turso)         │
│    • PostgreSQL (Dedicated DB / Supabase self-hosted / Neon)           │
│    • Cloudflare D1 (Edge native for Cloudflare Pages)                  │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Media Storage Strategy:                                             │
│    • Local Server Disk (/public/uploads) - Zero cost                   │
│    • Cloudflare R2 / S3-compatible bucket - Scalable client storage    │
├────────────────────────────────────────────────────────────────────────┤
│ 4. Bulk Collections Inventory:                                         │
│    • What bulk items exist? (e.g. Real Estate Properties, Doctors,     │
│      Tour Packages, Products, Menu Dishes, Courses, Case Studies, etc.)│
│    • What custom fields are required for each?                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The 6-Step Implementation Loop

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│    Step 0     │ ──> │    Step 1     │ ──> │    Step 2     │
│Discovery Grill│     │  cms.config   │     │   DB Setup    │
└───────────────┘     └───────────────┘     └───────────────┘
                                                    │
                                                    ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│    Step 5     │ <── │    Step 4     │ <── │    Step 3     │
│Roundtrip DoD  │     │ Engine A & B  │     │/admin & Upload│
│ Verification  │     │ Wiring & Sync │     │  Auth Routes  │
└───────────────┘     └───────────────┘     └───────────────┘
```

### Step 0: Grill & Align
Confirm host, database type, storage, and collection list with the user.

### Step 1: Declare Schema (`cms.config.ts`)
Map all discovered bulk entities into `cms.config.ts` with custom field types (text, number, richtext, image, gallery, date, select, repeater, boolean toggles).

### Step 2: Database Layer Setup
Run migration for target database (MySQL, Postgres, SQLite, or D1). Create universal tables:
- `sps_pages` (for Engine A)
- `sps_collections` (for Engine B)
- `sps_media` (for file assets)
- `sps_settings` (for site-wide settings)

### Step 3: Admin Dashboard & Auth
Scaffold `/admin` shell with dynamic navigation sidebar reflecting all declared collections. Wire cookie-based session auth and upload handler.

### Step 4: Engine A & B Construction
- **Engine B (Collections):** Render dynamic Data Tables and Add/Edit forms with inspector sidebar and real-time auto-slug generator.
- **Engine A (Visual In-Context):** Mount `<AdminOverlay />` and `<EditableText />` islands on public pages for logged-in admins.

### Step 5: Frontend Wiring & Auto-Sync Verification
Connect Homepage queries, archive grids, and `/[collection]/[slug]` detail routes. Run the 5-point roundtrip verification gate before declaring completion.
