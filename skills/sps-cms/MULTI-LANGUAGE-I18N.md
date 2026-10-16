# Multi-Language (i18n), RTL & Gemini Flash Auto-Translate

SPS-CMS provides a seamless, non-technical client-friendly multi-language (i18n) engine featuring **Native Gemini Flash AI Auto-Translation**. Clients can edit content in one language, and the system automatically translates and synchronizes across all other languages with zero effort.

---

## 1. The Gemini Flash AI Auto-Translation Workflow

```
┌────────────────────────────────────────────────────────────────────────┐
│                   GEMINI FLASH AI TRANSLATION FLOW                     │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Client Types in Primary Language:                                   │
│    Client enters Title & Description in English (or any language).    │
│                                                                        │
│ 2. One-Click AI Translation:                                           │
│    Client clicks [ ✨ Auto-Translate All with Gemini Flash ]          │
│    (or automatically executes on "Save & Publish" if enabled).         │
│                                                                        │
│ 3. Millisecond Multilingual Sync:                                      │
│    • English ➜ Bengali (বাংলা)                                        │
│    • English ➜ Arabic (العربية with auto RTL formatting)              │
│    • Stored in Field-Level JSON in database in ~300ms.                 │
│                                                                        │
│ 4. Optional Manual Polish:                                             │
│    Client can switch tabs to fine-tune any specific translation.      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. API Key Configuration

The client only needs to provide their free or standard Google Gemini API key:

```env
# .env
GEMINI_API_KEY=AIzaSy...your-gemini-api-key
AUTO_TRANSLATE_ON_SAVE=true
```

---

## 3. How Multi-Language Works in the Admin UI

1. **Language Tabs:** `[ 🇺🇸 English (Default) | 🇧🇩 বাংলা | 🇸🇦 العربية (RTL) ]`.
2. **One-Click Magic Button:** `[ ✨ Auto-Translate with Gemini Flash ]` located right next to the language switcher.
3. **Automatic Fallback:** If a translation is omitted or AI key is not yet set, the system automatically renders the default language without breaking layouts or throwing 404s.
4. **RTL Support:** Arabic, Hebrew, and Persian fields automatically apply `dir="rtl"` with proper font tokens.
