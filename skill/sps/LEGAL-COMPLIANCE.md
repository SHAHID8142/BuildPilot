# Legal & Compliance Gate

Conditional laws: an item applies when the project actually has that
surface (payments, email, accounts, UGC, AI features, app stores). Mark
N/A with reason when the surface doesn't exist — never skip silently.
Discovery (COMPANY-LIFECYCLE Phase 0) must ask which surfaces apply so
this gate is scoped at kickoff, not at delivery.

## 1. Legal agreements & disclosures (public sites)

- Privacy Policy + Terms of Service pages exist and name the actual data
  collected (SECTION-DOD #35) — plus a **dedicated Cookie Policy** page
  when any non-essential cookie loads.
- **Clickwrap**: sign-up requires active acceptance of ToS + Privacy
  Policy (checkbox/inline confirm, never pre-checked, never
  browse-wrap-only).
- **Refund & Cancellation Policy** published when money changes hands.
- **EULA** for downloadable software / mobile apps.
- **SLA** only when the client contractually promises uptime tiers.
- **Company identity in the footer**: legal name, physical address,
  registration number (jurisdiction-dependent — confirm with the client).
- **DMCA/Copyright takedown policy** when hosting user-generated content.
- **Acceptable Use Policy (AUP)** for platforms with user content or APIs:
  prohibited content/conduct rules + the contractual basis for suspending
  abusive users (rate limiting is a technical control; the AUP is the
  legal one — a client needs both).
- Legal policies are **version-controlled** (dated changelog section or
  repo history) and users are **notified by email before material
  changes** take effect (when emails exist).

## 2. Consent architecture (cookies & tracking)

- Consent banner blocks ALL non-essential analytics/ad scripts until
  explicit consent — loading GTM/analytics first and "honoring" the
  choice later is not compliance.
- **Granular toggles** (Analytics / Marketing / Functional), all
  marketing/newsletter boxes **unchecked by default**.
- **"Reject All" is visually equal to "Accept All"** (same size and
  prominence — dark patterns fail GDPR audits).
- Every consent action is **logged** (timestamp, user ID when known,
  policy version) — an audit trail, not a console.log.
- **Persistent footer link** to revisit/revoke consent at any time.
- **Honor Global Privacy Control (GPC)** browser signals automatically.
- **JIT device permissions**: camera/location/mic prompts fire only when
  the user triggers the feature that needs them — never on page load.

## 3. Data privacy & user rights (GDPR/CCPA-class)

Beyond SECTION-DOD #35 (Privacy Policy, account deletion):
- **Cascade deletion** across every table, storage bucket, and
  third-party API — "deleted" that survives in a bucket is a breach.
- **Purge deleted records from backups** within the retention window the
  client's jurisdiction requires (document the window).
- **Self-serve data export**: users can download their personal data
  (JSON/CSV) without emailing support.
- **Data minimization**: collect only fields the app actually needs —
  every extra field in a signup form needs a justification.
- **Automated retention jobs** purge inactive/expired personal records
  (cron/queue, not good intentions).
- **DPAs signed with every vendor** handling user data; keep a published
  sub-processor list for products with user accounts.
- **"Do Not Sell or Share My Personal Information"** link for
  California traffic (CCPA/CPRA) when data is shared with third parties.
- **Age gate / parental consent** when the product targets or admits
  minors (COPPA <13, GDPR-K <16 by member state).
- **Regional data residency routing** when the client's market mandates
  in-country storage (surface in platform research, Phase 1).
- **Encrypt PII at rest** (disk/DB-level encryption, not app-level
  obfuscation).

## 4. Payments & subscriptions (when money flows)

- **PCI-DSS scope elimination**: use a compliant processor (Stripe-
  class); raw card numbers never touch your servers or logs.
- **Total price upfront**: taxes/VAT/fees shown before checkout, not
  sprung at the final step (drip pricing is also an FTC dark pattern).
- **Recurring billing needs explicit consent**: the subscription terms
  (amount + frequency) are affirmed at signup, stated again before a
  free trial converts, and a **reminder email goes out before
  auto-renewal** where jurisdictions require it (EU, California).
- **Click-to-cancel**: cancellation is online, self-serve, and no harder
  than signup — as many steps as it took to subscribe, never
  "email us to cancel".
- **Tax invoices** show buyer/seller tax IDs and itemized VAT/GST when
  the client's market requires them (EU B2B especially).
- **KYC/AML** before building anything that moves money between users
  (marketplaces, wallets) — flag it at discovery; this is a legal
  prerequisite, not a feature.
- **Mobile IAP rules**: digital goods consumed in-app must use Apple/
  Google IAP (guideline 3.1.1 / Payments policy) — a Stripe link in an
  iOS app gets it rejected.

## 5. Communications & marketing law (email/SMS)

- **Double opt-in** on marketing lists (confirm-subscribe, no
  single-click list additions).
- Every marketing email: **visible one-click unsubscribe** + the
  **`List-Unsubscribe` header** + a **valid physical postal address**
  (CAN-SPAM/GDPR/PECR baseline).
- **Transactional ≠ marketing pipelines**: receipts, password resets,
  and security alerts come from a separate stream with no promo content
  injected — mixing them both breaks consent law and deliverability.
- **SMS/WhatsApp**: explicit written opt-in before automated sends;
  honor STOP/UNSUBSCRIBE replies automatically (processed, not
  forwarded to an inbox).

## 6. IP, open source & licensing

- **License audit on dependencies**: no viral copyleft (AGPL/GPL-class)
  in shipped proprietary code unless the client explicitly accepts it —
  check with a license scanner, not vibes.
- **THIRD-PARTY-NOTICES / attribution file** generated for the shipped
  bundle when required by the licenses in use.
- **Font licenses**: commercial embedding licenses verified for all
  custom fonts (desktop licenses ≠ web embedding ≠ app embedding).
- **Asset licenses**: commercial usage rights verified for icons,
  illustrations, sound effects, stock media — "it was on a free site"
  is not a license check.
- **ToS content-ownership clause**: who owns user-uploaded content and
  what license the user grants the platform — required for any UGC
  surface.

## 7. AI governance (when AI features ship)

Beyond SECTION-DOD #29 (LLM input sanitization):
- **Disclose the bot**: the UI says when the user is talking to an AI
  agent, not a human (EU AI Act / FTC baseline).
- **AI-training opt-out** setting when user data could train models.
- **PII stripping before external LLM calls**; prefer **Zero Data
  Retention** API tiers for enterprise accounts.
- **Moderation filters** on AI inputs and outputs (illegal content
  cannot pass through unfiltered).
- **C2PA provenance metadata** on AI-generated media where the target
  market requires it.
- Fabricated claims, fake metrics, fake reviews, fake counters, and
  **fake urgency timers that reset on refresh** are banned twice over —
  DESIGN-GATE anti-slop list AND consumer-protection law.

## 8. Accessibility, sector & incident readiness

- WCAG 2.1 AA (SECTION-DOD #8) is also **legal**, not just quality:
  ADA (US) and the European Accessibility Act (2025) both bite.
- **Accessibility Statement** page with a contact channel for reporting
  barriers (EAA requirement).
- **HIPAA BAAs** before touching health data — if the client mentions
  health records, this is a stop-and-consult moment, not a build task.
- **Immutable audit logs** of admin/data-access actions (SOC 2/ISO 27001
  readiness) for B2B products that will face security review.
- **Report Abuse / Flag button** on user-generated content surfaces.
- **App-store Data Safety / Privacy Nutrition labels** filled accurately
  at submission (wrong labels = takedown).
- **Incident response plan documented** before launch: who does what
  within the 72-hour GDPR breach-notification window — written down,
  not improvised during the breach.

## Gate mechanics

- Scope at kickoff: the Phase 0 questionnaire records which of the 8
  sections apply; the lifecycle plan lists the applicable items.
- Verify at delivery: the Phase 4 pre-delivery checklist walks this file
  section by section; every applicable item is PASS / N-A-with-reason.
- Client jobs: legal documents are drafted as templates and flagged for
  the client's counsel — the agent never presents boilerplate as legal
  advice.
