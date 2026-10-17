# Global Settings & Site-Wide Single-Point Sync Architecture

Websites frequently contain recurring global brand and contact assets (e.g. Phone Number, WhatsApp, Office Address, Support Email, Brand Logo, Social Media URLs, and Announcement Banners) across multiple pages, headers, footers, and modal windows.

SPS-CMS guarantees a **1-Point Global Sync Engine**: updating a global variable in `/admin/settings` or on any live page immediately propagates across every page and component on the entire website.

---

## 1. The Global Settings Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   GLOBAL SETTINGS SINGLE SOURCE OF TRUTH               │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Centralized Global Options Hub (/admin/settings):                   │
│    • 🏢 Company & Brand: Site Name, Legal Title, Tagline, Brand Logo   │
│    • 📞 Contact & Support: Phone, WhatsApp, Support Email, Address     │
│    • 🌐 Social Media: Facebook, Instagram, LinkedIn, YouTube, X/Twitter│
│    • 📢 Header Announcement Bar & Footer Copyright Notice              │
│                                                                        │
│ 2. Universal Global Tagging (data-sps-key="global.*"):                 │
│    Any component rendering global data tags it with `global.*`:        │
│    • <span data-sps-key="global.phone">{settings.phone}</span>         │
│    • <span data-sps-key="global.email">{settings.email}</span>         │
│    • <img data-sps-key="global.logo" src={settings.logo} />            │
│                                                                        │
│ 3. Instant Site-Wide Propagation:                                      │
│    Editing the phone number in the footer or in `/admin/settings`      │
│    updates every single header, button, and contact box instantly!     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Global Data Storage (`__global__`)

Global variables are stored in the database under the singleton key `__global__`:

```json
{
  "company_name": "WanderLust Global Tours Ltd.",
  "phone": "+1 (800) 555-0199",
  "whatsapp": "+18005550199",
  "email": "vip@wanderlust-tours.com",
  "address": "742 Evergreen Terrace, Suite 500, New York, NY 10001",
  "logo_url": "/uploads/logo.svg",
  "facebook_url": "https://facebook.com/wanderlust",
  "instagram_url": "https://instagram.com/wanderlust",
  "linkedin_url": "https://linkedin.com/company/wanderlust"
}
```

---

## 3. Usage in Layouts & Components

```astro
---
import { getGlobalSettings } from '../lib/db';
const global = getGlobalSettings();
---

<!-- Header Phone -->
<a href={`tel:${global.phone}`} data-sps-key="global.phone" data-sps-type="text">
  <span data-sps-field="text">{global.phone}</span>
</a>

<!-- Footer Email -->
<a href={`mailto:${global.email}`} data-sps-key="global.email" data-sps-type="text">
  <span data-sps-field="text">{global.email}</span>
</a>
```
