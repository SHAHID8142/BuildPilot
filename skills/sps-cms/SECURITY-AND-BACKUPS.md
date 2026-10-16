# SPS-CMS Security Hardening & Automated Backup Standard

To ensure enterprise-grade security and zero data loss across any client hosting environment, SPS-CMS enforces strict security rules and automated backup protocols.

---

## 1. Bulletproof Upload Security Guard

All file upload endpoints (`/api/upload`) must strictly adhere to the following defensive rules:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   FILE UPLOAD DEFENSIVE PIPELINE                       │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Extension & MIME Whitelist:                                         │
│    • Allowed Extensions: .jpg, .jpeg, .png, .webp, .svg, .pdf, .mp4    │
│    • Hard Reject: .php, .phtml, .exe, .sh, .py, .js, .html, .htaccess  │
│                                                                        │
│ 2. MIME Magic Header Verification:                                     │
│    • Verifies actual file header bytes matches declared MIME type      │
│    • Prevents executable scripts disguised as .jpg                     │
│                                                                        │
│ 3. Filename Sanitization:                                              │
│    • Strip directory traversal (../, \\) and special characters        │
│    • Structure: timestamp-slugified-name.extension                     │
│                                                                        │
│ 4. Size & Quota Protection:                                            │
│    • Maximum 10MB per single image, 50MB per video                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 1-Click Automated Database Backups & Export

SPS-CMS includes built-in zero-dependency backup utilities:

### 1. JSON Snapshot Export (`/api/cms/backup`)
- Generates a full encrypted/compressed JSON snapshot of all pages, collections, and settings.
- Downloadable in 1-click from `/admin` settings.

### 2. Emergency Restore
- 1-click upload of snapshot restores the complete website content in under 1 second.
