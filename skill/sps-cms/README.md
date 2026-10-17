# ⚡ SPS-CMS (v2.3.0 Lead Inbox & Full Builder Standard)

> **The Definitive Universal Visual & Collection CMS Architect with Zero-SaaS Lead Capture & Inquiries Inbox, 1-Point Global Settings Sync, Tracking Scripts Injector, 100% Granular Surface Coverage, In-Context Popover Inspectors, Live Image Swapping, Gemini Flash AI Auto-Translation, and 1-Click Backups**  
> *Supports JavaScript/TypeScript (Astro, Next.js, Nuxt/Vue, SvelteKit), PHP (Laravel, Native), Python (Django, FastAPI), Go, Ruby, and Vanilla HTML across Windows (7/8/10/11), macOS, and Linux.*

---

## 🌟 Why SPS-CMS v2.3.0 is the Gold Standard for Client Websites

SPS-CMS bridges the gap between high-speed custom codebases and effortless non-technical client UX:
- **Zero-SaaS Lead Capture & Inquiries Inbox (`/admin/inquiries`):** Captures all client contact forms and booking requests locally without paying monthly third-party form fees (Formspree, Typeform). Features live unread lead badges, search, status filters (`New`, `Contacted`, `Closed`), 1-click direct WhatsApp chat, and 1-click CSV export!
- **1-Point Global Settings Sync (`/admin/settings`):** Manage Phone, WhatsApp, Support Email, Physical Address, Brand Logo, and Social Media links centrally. Updating in one spot instantly propagates across every header, footer, and booking box!
- **Analytics & Tracking Scripts Injector:** Cleanly paste Google Analytics (GA4), Meta/Facebook Pixel, or GTM scripts from `/admin/settings` with zero code edits.
- **100% Granular Surface Coverage:** ZERO hardcoded strings. Every single eyebrow, badge, headline, sublabel, stat number, stat label, button text, destination URL, image, and footer detail is individually editable live.
- **Zero Third-Party SaaS Fees:** Runs entirely on the client's own database (MySQL, SQLite, Postgres, Cloudflare D1) and storage (`/public/uploads`, R2, S3).
- **In-Context Visual Popover Inspector (Engine A):** Non-intrusive floating bottom dock. Click text, CTA buttons, or photos to edit labels, change URLs, or drop new images live on the page with zero accidental page redirection.
- **Gemini Flash AI Auto-Translation:** Instant 300ms translation sync across English, Bengali, Arabic (RTL), and any target language.
- **Polymorphic Collection Manager (Engine B):** Searchable Data Tables, auto-slug generators, visibility switches, and inspector sidebars for bulk entities (Real Estate, Doctors, Tour Packages, Products, Dishes).
- **Enterprise Security & 1-Click Backups:** MIME validation, size caps, and instant 1-click JSON database snapshot downloads.

```
┌────────────────────────────────────────────────────────────────────────┐
│               SPS-CMS v2.3.0 MASTER ARCHITECTURE OVERVIEW              │
├───────────────────────────────────┬────────────────────────────────────┤
│ 1. DATA LAYER (Host-Agnostic)     │ 2. STORAGE LAYER (Client-Owned)    │
│    • Native MySQL (cPanel/VPS)    │    • Local Server: /public/uploads │
│    • SQLite / LibSQL (Embedded)   │    • Cloudflare R2 / S3 Storage    │
│    • PostgreSQL / Neon / Supabase │    • Zero Third-Party Monthly Fee  │
│    • Cloudflare D1 (Edge Native)  │                                    │
├───────────────────────────────────┴────────────────────────────────────┤
│ 3. COMPLETE CLIENT & LEAD MANAGEMENT SUITE                             │
│    ┌──────────────────────────────────┬──────────────────────────────┐ │
│    │ Engine A: In-Context Visual      │ Engine B: Collection Hub     │ │
│    │ • Floating Bottom Dock           │ • Searchable Data Tables     │ │
│    │ • Eyebrows, Badges, Stat Labels  │ • Add/Edit Multi-Lang Forms  │ │
│    │ • Buttons, Links & Image Popover │ • Real Estate, Tours, Dishes │ │
│    │ • Zero accidental redirection    │ • Home Featured [ON/OFF]     │ │
│    │ • Live DOM update & publish      │ • Single Source of Truth     │ │
│    ├──────────────────────────────────┴──────────────────────────────┤ │
│    │ 📬 Zero-SaaS Inquiries Inbox (/admin/inquiries):                │ │
│    │ • Contact & booking form capture, WhatsApp chat & CSV export    │ │
│    ├─────────────────────────────────────────────────────────────────┤ │
│    │ ⚙️ Centralized Global Options Hub (/admin/settings):            │ │
│    │ • Phone, WhatsApp, Email, Address, Brand Logo, GA4/Pixels       │ │
│    └─────────────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────┤
│ 4. MULTI-LANGUAGE & GEMINI FLASH AI TRANSLATION                        │
│    • Language Switcher: [ 🇺🇸 EN | 🇧🇩 BN | 🇸🇦 AR (RTL) ]               │
│    • [✨ Auto-Translate with Gemini Flash] in ~300ms                   │
│    • Field-Level JSON Localization with Automatic Fallback             │
├────────────────────────────────────────────────────────────────────────┤
│ 5. DEFENSE & PORTABILITY LAYER                                         │
│    • 1-Click Full DB Snapshot Export/Backup (`/api/cms/backup`)        │
│    • Bulletproof MIME & Traversal Upload Security Guard                │
│    • Self-Enforcing Lock (GEMINI.md / AGENTS.md / CLAUDE.md)           │
│    • Windows (7, 8, 10, 11) PowerShell + macOS / Linux Zsh / Bash      │
│    • Skills.sh Registry (`npx skills add SHAHID8142/sps-cms`)          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 1-Click Cross-Platform Installation

### ⚡ Method 1: Via Skills.sh CLI (`npx skills`)
```bash
npx skills add SHAHID8142/sps-cms
```

### 🪟 Method 2: Windows (PowerShell 1-Click)
Open PowerShell and run:
```powershell
irm https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/install.ps1 | iex
```

### 🍎 Method 3: macOS & 🐧 Linux / WSL (Terminal 1-Click)
Open Terminal and run:
```bash
curl -fsSL https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/install.sh | bash
```

---

## 📄 License

MIT © [SHAHID8142](https://github.com/SHAHID8142)
