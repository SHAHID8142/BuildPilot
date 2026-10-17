# NO EMOJI — global policy (DEC-0008, approved by User 2026-10-03)

**Rule:** SPS 2.0 uses **no emoji by default** in any generated artefact.

Applies to: UI, buttons, labels, documentation, code comments, generated copy,
status indicators, commit-message bodies, and agent output.

## Exception

Emoji may be used **only** when a specific project explicitly authorises them.
The authorisation must be recorded in that project's configuration. There is no
global exception and no implicit permission.

## Icons

Use an appropriate **icon library**. Icon libraries are **selectable capabilities**
(see `capability/registry.json`), not a globally pinned choice.

Pinning one icon library globally is prohibited for the same reason the legacy
`SKILL-GOVERNANCE.md` taste lock was a defect: a permanent preference cannot be
adapted to project requirements, bundle size, licensing, or platform.

## Enforcement

This rule is **machine-checked**, not merely documented:

- `tools/validate-sps2.sh` section 6 scans every file under `sps2/` for emoji and
  fails on any hit.
- Negative case **CASE O** proves the scan detects a planted violation.

A documented-but-unenforced rule would repeat the legacy `F-9` failure
(documentation asserting capability no code implements).