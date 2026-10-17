# Inquiries, Form Capture & Lead Management Architecture

Every commercial website requires lead capture (Contact Forms, Booking Inquiries, Quote Requests, Newsletter Subscriptions). 

SPS-CMS eliminates third-party form SaaS subscriptions (e.g. Formspree, Typeform, HubSpot) by providing a **100% Self-Contained, Zero-Dependency Lead Capture & Inbox Engine**.

---

## 1. How the Inquiries Engine Works

```
┌────────────────────────────────────────────────────────────────────────┐
│                   SPS-CMS LEAD CAPTURE & INBOX FLOW                    │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Public Front-End Form:                                              │
│    Any standard HTML/React form submits via POST to                    │
│    `/api/cms/submit-form` with JSON or FormData.                       │
│                                                                        │
│ 2. Bulletproof Validation & Storage:                                   │
│    • Sanitize fields (Name, Email, Phone, Message, Package / Subject)  │
│    • Store directly in local database (`sps_inquiries`)               │
│    • Optional instant Webhook (Telegram / WhatsApp / Discord / Email)  │
│                                                                        │
│ 3. Centralized Inquiries Inbox (/admin/inquiries):                     │
│    • Live unread notification badges in sidebar                        │
│    • Searchable list table with Status pills (New, Contacted, Closed)  │
│    • 1-Click WhatsApp direct chat button (`https://wa.me/...`)         │
│    • 1-Click CSV Export for CRM imports                                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. API Endpoint (`/api/cms/submit-form`)

```typescript
// Payload format:
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "phone": "+1 555 0199",
  "subject": "Booking Inquiry for Bali 5-Day Tour",
  "message": "We are a family of 4 looking to book for November."
}
```

---

## 3. Database Schema for `sps_inquiries`

```sql
CREATE TABLE IF NOT EXISTS sps_inquiries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT,
  subject TEXT,
  message TEXT NOT NULL,
  status TEXT DEFAULT 'new', -- 'new', 'contacted', 'closed'
  data_json TEXT, -- extra custom fields (e.g. travel dates, guests)
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```
