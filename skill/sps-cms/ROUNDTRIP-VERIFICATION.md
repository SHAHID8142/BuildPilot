# Roundtrip Verification Protocol (DoD)

To eliminate broken releases and avoid days of after-sales client support, no CMS feature or section is marked complete until the **SPS-CMS Roundtrip Verification Gate** passes with recorded proof.

---

## The 5-Point Verification Checklist

### 1. Creation & Seed Gate
- [ ] Create a sample dynamic entity (e.g. `Bali Luxury Villa Escape`, price: `$850`, `show_on_homepage = 1`) via the `/admin` collection form.
- [ ] Ensure the form submits cleanly with zero console or network errors (200 OK).

### 2. Auto-Sync & Multi-Page Propagation Gate
- [ ] **Homepage Check:** Visit `/` and verify the newly added item appears in the Featured Grid.
- [ ] **Archive Check:** Visit `/packages` and verify the item appears in the collection list.
- [ ] **Detail Page Check:** Click the item or visit `/packages/bali-luxury-villa-escape` and verify the full page renders with 200 OK.

### 3. Update & Mutation Gate
- [ ] Edit the item in `/admin`: change the price to `$799` and title to `Bali Luxury Beach Villa`.
- [ ] Refresh the frontend pages and verify all three pages (Home, Archive, Detail) display the updated values immediately.
- [ ] Toggle `Show on Homepage` to `OFF` in `/admin`.
- [ ] Refresh `/` and verify the item disappears from the Homepage while remaining intact on `/packages`.

### 4. Local Media Upload Gate
- [ ] Drag and drop an image (`.jpg` or `.webp`) into the featured image field.
- [ ] Verify the file is physically created in `/public/uploads/` on the server disk.
- [ ] Verify the image renders with correct dimensions and natural aspect ratio on the frontend.

### 5. Layout & Mobile Gate
- [ ] Test the `/admin` dashboard and collection forms at mobile viewports (375px - 414px).
- [ ] Test public pages with `<AdminOverlay />` active to verify no horizontal overflow or UI breakage.

---

## Evidence Format for Task Handoff

When closing a task, the coding agent MUST record evidence in this format:

```markdown
### CMS Roundtrip Verification Proof
- **Item Created:** Bali Luxury Beach Villa (ID: 14)
- **Initial Price:** $850 ➜ **Updated Price:** $799
- **Homepage Visibility Toggle:** Verified (ON shows in Grid, OFF hides from Grid)
- **Detail Route Verified:** `/packages/bali-luxury-beach-villa` (HTTP 200)
- **Media Asset Verified:** `/uploads/1723849120-bali-villa.webp` (Loaded from disk)
- **Zero Errors:** Console clean, DB queries verified.
```
