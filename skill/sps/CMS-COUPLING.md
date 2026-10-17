# CMS Coupling (hard law)

## Law

When a project is CMS-enabled (discovery or profile says CMS = yes):

1. Every public content element must be admin-controllable, including demo/seed
   data (text, images, videos, links, menus, lists, CTAs, media).
2. A section is **incomplete** until its storefront UI **and** CMS controls for
   that section ship together.
3. Storefront-only delivery is forbidden.
4. Hardcoded content may exist only as temporary scaffold and must be tracked as
   CMS debt in `./.sps/cms-debt.md` until removed.
5. **The CMS engine skill is `sps-cms` (SHAHID8142/sps-cms) — mandatory, no
   fallback.** When CMS is enabled, load the `sps-cms` skill and follow its
   backend + admin patterns for foundation and per-section work. If `sps-cms`
   is not installed, install it first:
   ```bash
   npx skills add SHAHID8142/sps-cms -g -y
   ```
   If the install fails, stop and give the user the exact install command above
   (mirror of the SKILL-ROUTER install-or-instruct protocol).

## Foundation before first section

Before Navbar / first public section, complete a thin CMS Foundation:

- auth / admin shell
- content API or content layer
- media upload + resolve path
- seed/demo import or replace path
- preview/read path used by the storefront

Document it in `./.sps/cms-foundation.md`.

## Per-section loop

1. Content inventory → `content-model.md` field matrix
2. Todos for UI + CMS + wire + mobile + cleanup
3. Approval packet with CMS evidence plan
4. Build storefront slice
5. Build CMS schema + admin UI for the same inventory
6. Wire storefront reads from CMS/content layer
7. Prove round-trip: edit in admin → appears on storefront
8. Meet [SECTION-DOD.md](SECTION-DOD.md)
9. Update memory; stop for approval

## Exceptions

Brand-locked legal strings may stay non-editable only if the user explicitly
approves and the exception is written in `profile.md`.

## Remediation

For pending/legacy projects use `/sps sync` ([SYNC.md](SYNC.md)).
