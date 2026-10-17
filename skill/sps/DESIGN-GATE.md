# Design Gate (portable source of truth)

SPS-owned design laws. Specialist skills (`hallmark`, `impeccable`,
`web-design-guidelines`, Anthropic `frontend-design`) are enhancers only.
If a specialist skill is missing, still enforce this file.

## Global defaults (unless project profile overrides)

1. **No eyebrows** on public marketing UI (mono/uppercase kickers above headlines).
2. **Seamless sections** — minimal section gaps; continuous editorial flow.
3. **No separator chrome** — no thin divider lines, fake `<hr>` energy, or
   decorative rules between sections unless the user explicitly requests one.
4. **Palette discipline** — stay inside the planned minimal palette.
5. **Research before design** — gather references / trends / constraints online
   (or via available tools) before first UI; on redesign requests, re-research
   UI+UX aspects, then propose improvements.
6. **Human, not template** — reject generic AI-slop layouts (Inter/Roboto default
   stacks, purple-on-white clichés, card spam, badge clutter) unless the brief
   asks for that look.
7. **Mobile-first composition** — design the small screen truthfully; enrich
   desktop without breaking mobile.

## Design Research Packet (required before UI / redesign)

```markdown
## Design Research Packet
- Brief inference:
- References checked:
- Trends / patterns considered:
- Rejected slop patterns:
- Palette + type plan:
- Motion budget (desktop / mobile):
- Known / Assumed / Unverified:
```

## Craft laws (typography, surfaces, space, motion, forms)

Concrete, checkable rules — an agent that skips these produces the
"AI-generated" look. They apply unless the project profile overrides.

**Typography & hierarchy**
- Distinct display font for headings + high-legibility sans for body;
  monospace for code/IDs/live data.
- `font-variant-numeric: tabular-nums` on prices, tables, timers, metrics.
- Fluid headings via `clamp()`; tight line-height (1.1–1.25) on display
  sizes, relaxed (1.5–1.65) on body; body measure 60–75ch.
- Letter-spacing: −0.02em…−0.04em on >24px headings; +0.04em…+0.08em on
  uppercase micro-labels.
- `text-wrap: balance` on headlines, `pretty` on body; left-align body
  blocks >2 lines. Hierarchy via weight + color, not size alone.

**Color & surfaces**
- 60-30-10 rule (background / surface / accent).
- Dark mode: tinted charcoal (`#090A0F`-ish), never pure `#000`; elevation
  = lighter surface steps, not drop shadows. Light mode: off-white
  (`#FAFAFA`-ish), never stark `#FFF`.
- Neutrals tinted 2–5% with the brand hue; translucent borders
  (`rgba(255,255,255,.08)` dark / `rgba(0,0,0,.06)` light).
- Dark cards get a 1px inset **top-edge highlight**
  (`inset 0 1px 0 rgba(255,255,255,.05–.1)`) — the lit-from-above depth cue.
- Badges/status pills: background = semantic color at ~10% opacity, text =
  high-contrast same-hue tone — never a solid saturated fill.
- Semantic tokens for success/warning/danger/info; never color alone for
  status (icon/text must carry it); WCAG AA contrast (4.5:1 body, 3:1 large).
- Theme switching: default to `prefers-color-scheme`, persist an explicit
  user toggle override, crossfade the swap (no flash of wrong theme).

**Space & layout**
- Strict 4px/8px spacing unit. Inner padding < outer gap (proximity).
- Primary feature blocks use **asymmetric Bento-style grids** (one dominant
  cell + supporting cells), never uniform equal-width card rows.
- Nested radii: `inner = outer − padding`. No cards inside cards; separate
  groups with background shifts or 1px dividers, not more boxes.
- ≥25% of the viewport stays whitespace. Primary mobile actions in the
  bottom thumb zone. Grid: `auto-fit` + `minmax()` for fluid columns.
- Sticky only for table headers, contextual toolbars, checkout summaries.

**Components & depth**
- One primary CTA per view; three button tiers (solid / outlined / ghost).
  No `rounded-full` on every button.
- Multi-layer low-opacity shadows, never one harsh shadow.
- One icon library, uniform stroke width (1.5px or 2px), optically aligned
  with text.
- Loading skeletons match loaded geometry; custom empty states (graphic +
  explanation + creation CTA); custom 404 that routes back to core pages.
- `backdrop-filter: blur(12px)` + translucent surface for floating bars.
- 1–2% SVG noise over large gradient backgrounds (kills banding).

**Motion & feedback**
- Spring/deceleration curves (`cubic-bezier(0.22,1,0.36,1)`), never linear;
  micro-interactions 150–250ms; `scale(0.98)` on `:active`.
- Animate only `transform`/`opacity`. Stagger list entrances 30–50ms/item.
- Distinct `:hover`/`:focus-visible`/`:active`/`:disabled` on every
  interactive control; `:focus-visible` = 2px offset ring.
- Optimistic UI for toggles/likes/creates; all decorative motion off under
  `prefers-reduced-motion`.

**Forms & input**
- Persistent labels above fields (no placeholder-as-label); validate on
  blur, not per keystroke; recovery instructions under the invalid field.
- Autofocus the first field when opening a modal or auth screen (with
  focus-trap and return-focus-on-close).
- Correct `inputmode` + `autocomplete`; auto-format cards/phones/dates;
  password visibility toggle.
- <5 options → segmented control/radio cards, not a dropdown; >5 inputs →
  multi-step with progress; touch targets ≥44×44px.

**Power-user patterns (dashboard/app UI)**
- Command palette (Cmd/Ctrl+K) for global search/actions; shortcut badges
  in menus AND tooltips; slide-over drawers instead of stacked modals.
- Undo toast for deletions; confirm modals only for permanent destruction.
- Data tables: numeric columns right-aligned, text left-aligned, ellipsis
  + hover-title for overflow; nav labels 1–2 words.

## Anti-slop ban list (extends law 7)

Default Tailwind purple/indigo/neon-cyan gradients · rows of 3 identical
feature cards with circular icon badges · neon glow shadows on dark
buttons · generic stock photography (prefer interactive UI previews or
custom diagrams) · Lorem ipsum (use realistic domain data) · vague hero
text · fake counters/review stars/invented metrics · "Made with AI"
badges · decorative floating blobs.

## Specialist skills

See [SKILL-ROUTER.md](SKILL-ROUTER.md). Prefer one primary taste skill + optional
polish. Do not stack hallmark + taste-skill + frontend-design + ui-ux-pro-max.
