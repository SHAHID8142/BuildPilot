# Legacy Repository Protection

The legacy SPS implementation at the repository root is **REFERENCE ONLY** during
SPS 2.0 development. It is not modified, imported, or depended upon by `sps2/`.

---

## Rules

1. **Never modify** legacy files (`skills/`, `scripts/`, `plugins/`, installers,
   `.github/`, `README.md`, `CHANGELOG.md`, `CATALOG.md`).
2. **Read** legacy files when reference is needed.
3. **Never copy** a legacy mechanism merely because it exists there.

## Explicitly not to be copied

| Legacy mechanism | Why |
|---|---|
| Hardcoded secrets (`sps-cms` auth fallback) | Known vulnerability (Phase 01 F-3 / `KI-01`) |
| Global installers (`install.sh`, 27 global skill installs) | Violates the project-local model |
| Static skill allow-lists (`SKILL-ROUTER.md` 20-row map) | Causes permanent preference; root cause of F-2 |
| Permanent vendor locks (`SKILL-GOVERNANCE.md:35`) | Cannot adapt to project requirements |
| Phantom dependencies (router names a non-existent `seo` skill) | Documentation asserting what does not exist |
| Documentation-only enforcement | Phase 01 F-9: strings in Markdown are not behaviour |

## What may be reused (with independent revalidation)

| Item | Condition |
|---|---|
| Governance state model + validators (Phase 02-04) | Parity-tested during migration (P14) |
| Capability model contracts | Re-validated against the P1 contracts |
| `data-sps-key` CMS coupling convention | Reviewed in P8 |
| Evidence and approval discipline | Ported, then parity-tested |

## Enforcement

`sps2/tools/validate-sps2.sh` section 9 asserts that
`git diff --name-only HEAD -- skills scripts plugins .github <installers>`
is **empty**. Any P1 change to legacy files fails validation.