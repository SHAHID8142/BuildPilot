# P9 Threat Model — SEO 2.0

**Author**: implementation agent (design author, not a User; not an approval)  
**Date**: 2026-10-06  
**Scope**: Roadmap P9 SEO 2.0 only. Does not authorise P9 implementation.  
**Prerequisite**: P9 Phase 1 requirements approved (commit `8873364`).  
**Companion**: `sps2/governance/P9-ARCHITECTURE.json`  

---

## 1. What P9 introduces

P9 introduces an **SEO 2.0 subsystem** under `domain/seo/` with:
- Metadata & canonical URL generation and validation
- `robots.txt` and XML sitemap generation and indexing controls
- Schema.org JSON-LD structured data and Open Graph / Twitter Card generators
- On-page structural hierarchy (H1, heading sequence) and internal link graph analyzers
- Media & image SEO validation (alt text, dimensions, filenames)
- URL architecture, redirect taxonomy (loop/chain detection), and pagination verification
- Core Web Vitals (CWV) layout-shift verification and static shift prevention
- Specialized modular dimensions (i18n, LocalBusiness, Ecommerce) with explicit N/A handling
- Pre-deployment audit tool with dual-mode CLI and deterministic `EV-SEO-*` evidence generation

While SEO is often perceived as non-executable content optimization, modern SEO engines generate executable HTML tags, parse untrusted web inputs, emit indexing directives, configure HTTP redirects, and serialize executable `<script type="application/ld+json">` blocks. This introduces distinct security and governance attack surfaces.

---

## 2. Assets to Protect

| Asset | Owner | Protected by |
|---|---|---|
| Site Reputation & Search Indexation | Project Owner | Accurate canonicals, robots.txt, and sitemap validation |
| Browser Context / DOM Integrity | End Users | HTML entity escaping, JSON-LD `<script>` tag breakout prevention |
| Redirection Infrastructure | System / Host | Strict local route validation, open redirect prevention |
| Internal Network Architecture | Host Environment | SSRF validation on canonical and sitemap URLs |
| Deployment Integrity (P13 Gate) | Release Manager | Deterministic pre-deployment audit tool with tamper-evident evidence |
| Governance Evidence Integrity | SPS 2.0 Governance | Zero invented performance thresholds; strict adherence to `CONF-001` |
| Project-Local State | Repository | Isolation boundaries; zero machine-global state writes; advisory rollback |

---

## 3. Threat Actors and Failure Modes

| Actor / Source | Failure Mode | Impact |
|---|---|---|
| Content Author (Admin) | Injects malicious script into meta title, description, or alt text | Stored XSS via meta tags or image attributes |
| Content Author (Admin) | Injects breakout string (`</script>`) into JSON-LD field | Arbitrary JavaScript execution in visitor browsers |
| Untrusted Content Input | Configures canonical URL or hreflang pointing to private IP | SSRF / internal host reconnaissance by crawlers |
| Untrusted Content Input | Configures HTTP redirect pointing to external phishing domain | Open redirect vulnerability |
| Malicious Sitemap Input | Provides XML sitemap with XML Entity references | XML External Entity (XXE) attack / local file disclosure |
| Route Generator | Writes `sitemap.xml` or `robots.txt` with path traversal (`../`) | Arbitrary file write / project escape |
| Route Generator | Lists administrative or secret staging routes in `robots.txt` | Sensitive administrative endpoint discovery |
| Malicious Web Payload | Feeds deeply nested HTML or recursive link chains to auditor | ReDoS / memory exhaustion denial of service |
| Build Tooling | Publishes unverified drafts or preview content into sitemap | Search engine cloaking / indexing unapproved content |
| Engineering Agent | Fabricates LCP or INP thresholds to pass performance checks | Breach of `CONF-001` invariant; falsified governance facts |
| Rogue Automation | Forges or tampers with `EV-SEO-*` audit evidence records | False Level 4 deployment gate clearance |
| Misconfigured SEO Tool | Writes cache or configuration outside project directory | Cross-project isolation breach |

---

## 4. Trust Boundaries

```text
[ CMS Content Store (P8) ]
           │
           │ (Untrusted User Content: titles, descriptions, slugs, images)
           ▼
─────────────────── TRUST BOUNDARY 1: Content Ingestion ───────────────────
           ▼
[ SEO Generators (domain/seo/metadata, indexing, structured_data) ]
           │
           │ (Escaped HTML tags, sanitized JSON-LD, defused XML sitemaps)
           ▼
─────────────────── TRUST BOUNDARY 2: Public Markup Sink ──────────────────
           ▼
[ Public Web Document (<head>, <body>, sitemap.xml, robots.txt) ]
           ▲
           │ (Raw rendered HTML string or files)
─────────────────── TRUST BOUNDARY 3: Audit Ingestion ─────────────────────
           │
[ Safe HTML Streaming Parser (domain/seo/onpage.py) ]
           │
           ▼
[ Pre-Deployment Audit Runner (domain/seo/audit.py) ]
           │
           │ (Deterministic exit codes & SHA-256 evidence records)
           ▼
─────────────────── TRUST BOUNDARY 4: Deployment Gate (P13) ───────────────
           ▼
[ Deployment Readiness Gate & Evidence Store (sps2/evidence/) ]
```

---

## 5. Threat Categories and Mitigations

### 5.1 Stored XSS / Attribute Injection in Meta Tags and Titles
- **Threat**: User-supplied content (e.g. `"><script>alert(1)</script>`) placed in `<title>`, `<meta name="description" content="...">`, or `<img alt="...">`.
- **Mitigation**:
  - All metadata generation functions must pass user strings through `html.escape(value, quote=True)`.
  - Double quotes, single quotes, ampersands, and angle brackets are strictly converted to HTML entities.
  - Newlines (`\r`, `\n`) are stripped from title and meta content strings to prevent HTTP response splitting.

### 5.2 JSON-LD `<script>` Tag Breakout
- **Threat**: Attackers place `</script><script>alert('xss')</script>` inside JSON-LD entity fields (such as article headline or author name). In HTML documents, browsers terminate `<script>` blocks upon encountering the character sequence `</script>`, regardless of string literals in JSON.
- **Mitigation**:
  - The JSON-LD serializer must use `json.dumps()` followed by escaping the forward slash character: `json_str.replace("</script>", "<\\/script>").replace("<!--", "<\\!--")`.
  - Machine-testable invariant: Any serialized JSON-LD script tag never contains the unescaped literal substring `</script>` inside its content body.

### 5.3 SSRF via Canonical URLs, Hreflang, and Sitemaps
- **Threat**: Canonical URLs or sitemap URLs configured with internal or loopback IP addresses (e.g. `http://127.0.0.1:8080/admin` or `http://169.254.169.254/`).
- **Mitigation**:
  - All URLs evaluated by the SEO subsystem must pass scheme validation (strictly `http://` or `https://`).
  - Hostnames are validated: private and reserved IP blocks (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`) are strictly rejected.
  - Sitemaps only accept absolute URLs matching the site's configured canonical origin.

### 5.4 Open Redirects in Redirect Taxonomy
- **Threat**: Redirect taxonomy entries specifying arbitrary external destination domains (e.g. `/login -> https://evil.com/phish`).
- **Mitigation**:
  - The redirect validator verifies that redirect targets are relative paths (starting with `/`) or match the trusted canonical site domain.
  - Any external destination redirect triggers an explicit `CRITICAL` audit failure unless tagged with an explicit external allowlist flag.

### 5.5 XML External Entity (XXE) and XML Bombs in Sitemap Parsing
- **Threat**: Loading external XML sitemaps or parsing untrusted sitemap XML using vulnerable XML parsers allowing `<!DOCTYPE` entity expansion.
- **Mitigation**:
  - Generation: Sitemaps are emitted using safe, defused string construction or standard `xml.etree.ElementTree` without entity expansion.
  - Parsing/Auditing: `xml.etree.ElementTree.iterparse` is configured with `resolve_entities=False`, and XML processing rejects any document containing `<!DOCTYPE` or `<!ENTITY`.

### 5.6 Path Traversal in Export Destinations
- **Threat**: Exporting `robots.txt` or `sitemap.xml` with path traversal in filenames (`../../public/robots.txt`).
- **Mitigation**:
  - Destination file paths are strictly resolved using `pathlib.Path.resolve()`.
  - Export functions verify that the canonical resolved destination path is strictly within the project's authorized output directory.

### 5.7 Information Disclosure via `robots.txt`
- **Threat**: Listing private administrative routes, staging paths, or secret APIs under `Disallow:`, disclosing their existence to crawlers and public attackers.
- **Mitigation**:
  - The `robots.txt` generator includes an advisory linter check flagging disallow rules that target administrative, auth, or internal API paths.
  - Recommends using `noindex` HTTP response headers rather than public `robots.txt` disallows for sensitive routes.

### 5.8 Denial of Service via Deep HTML Recursion or Cyclic Link Graphs
- **Threat**: Pathological HTML with thousands of nested tags or infinite cyclic internal links causing stack overflows or infinite loops during audits.
- **Mitigation**:
  - HTML parser uses a linear streaming `html.parser.HTMLParser` without recursion.
  - Link graph analysis tracks a `visited_urls` set to prevent cyclic loops.
  - The audit runner enforces maximum page count and file size limits (default: max 10MB per page, max 5,000 pages per audit).

### 5.9 Preview vs Published Content Leakage
- **Threat**: Unapproved draft or preview pages inadvertently included in the XML sitemap or given `index, follow` directives.
- **Mitigation**:
  - The indexing engine integrates with P8's `Content.status`: only records with `status == "published"` are eligible for inclusion in the XML sitemap.
  - Draft and preview pages are automatically assigned `<meta name="robots" content="noindex, nofollow">`.

### 5.10 Evidence Tampering & Falsification
- **Threat**: Fabricating an audit report or generating invalid evidence to bypass deployment gates.
- **Mitigation**:
  - Every pre-deployment audit outputs an immutable evidence record conforming to `sps2.evidence/v1`.
  - Evidence records include execution timestamp, exact command line, exit code, number of checks passed/failed, and SHA-256 hashes of audited output files.

### 5.11 Preservation of CONF-001 Performance Boundary
- **Threat**: Implementing Core Web Vitals checks by inventing unretrieved numeric thresholds (e.g. claiming LCP $\le$ 2.5s or INP $\le$ 200ms without verified source derivation).
- **Mitigation**:
  - `domain/seo/cwv.py` encodes ONLY verified CLS ($\le 0.1$ good, $> 0.25$ poor from SRC-017).
  - LCP and INP metrics are strictly marked `N/A — unretrieved research threshold (CONF-001)`.
  - Pre-deployment audit asserts regex scan over all SEO code and evidence ensuring no numeric threshold for LCP or INP is fabricated.

### 5.12 Cross-Project Isolation & Zero Legacy Diff
- **Threat**: Writing persistent SEO state to machine-global locations (`~/.sps/`) or modifying legacy repository files (`skills/`, `scripts/`).
- **Mitigation**:
  - All SEO files reside strictly under `domain/seo/` and `sps2/`.
  - Advisory rollback contract: deleting `domain/seo/` completely restores pre-P9 state with zero orphaned references.
  - Legacy diff remains strictly `0`.

---

## 6. Safeguards and Validation Requirements

1. **Output Safety**: Automated unit tests prove HTML escaping and JSON-LD script breakout escaping on malicious probe strings (`"><script>`, `</script><script>`).
2. **SSRF Guard**: Automated negative tests prove private IP addresses in canonicals and redirects are rejected.
3. **XXE Guard**: Negative tests prove DOCTYPE entity expansion in sitemaps is rejected.
4. **CONF-001 Check**: Static code and configuration scans assert zero invented LCP/INP values.
5. **Advisory Rollback Test**: Rehearsal proves deleting `domain/seo/` leaves SPS2 core validators passing.
6. **Stdlib-Only Scan**: Validator proves zero third-party dependencies imported across `domain/seo/`.

---

## 7. Explicit Prohibited Behaviours

- Inventing or hardcoding any numeric LCP or INP threshold (`CONF-001`).
- Shipping without a pre-deployment audit step (Roadmap forbidden rule).
- Importing or installing any third-party package (`beautifulsoup4`, `lxml`, `requests`, etc.).
- Writing state outside the project directory.
- Modifying legacy repository files.
- Bypassing CRITICAL audit failures in deployment mode without explicit user authorization.
- Self-approval of any gate.
