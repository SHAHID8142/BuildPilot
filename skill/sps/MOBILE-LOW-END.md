# Mobile & Low-End Device Rules

Default for every UI creation task unless the user explicitly approves richer
mobile behavior:

**Minimal mobile. No fancy, buggy, or laggy effects on phones.**

## Hard defaults

1. Every UI section must be checked for responsiveness.
2. Low-end mobile support is required, not optional.
3. Mobile gets the simpler path by default.
4. Desktop may be richer only when mobile stays clean and fast.
5. Motion on mobile is opt-in. If the user does not approve it, skip it.
6. Hover-only interactions must never be the only way to use a control.
7. Heavy 3D, large video backgrounds, particle systems, and unoptimized Lottie
   are banned on mobile unless explicitly approved with a light fallback.

## Required breakpoints

At minimum, consider:

- 320px
- 375px
- 768px
- 1024px+

If the host cannot open a browser, still design and code for these widths and
state what remains manually unverified.

## What “minimal mobile” means

Prefer:

- static or lightly animated layouts
- CSS transforms only when cheap and purposeful
- compressed images / modern formats
- fewer DOM nodes on small screens
- touch-friendly tap targets
- content-first hierarchy

Avoid on mobile unless approved:

- hover micro-interactions as primary feedback
- parallax
- scroll-jacking
- autoplaying heavy media
- large blur stacks / expensive shadows
- continuous animation loops
- dual heavy animation libraries

## Dual-path rule

When desktop needs richer motion or visuals:

1. Keep a simple mobile path.
2. Gate rich effects behind breakpoints, reduced-motion, or explicit capability
   checks.
3. Say so in the approval packet.
4. Verify both paths before handoff.

## Asset budget

Enforce the defaults in [ASSET-BUDGET.md](ASSET-BUDGET.md).

Practical defaults:

- mobile hero ≤ 200 KB
- no autoplay heavy media on mobile
- motion libraries opt-in, not default on phones

## Blocking gate

No section approval and no handoff for UI work unless the packet includes:

- responsive plan for the chunk
- mobile behavior: minimal / dual / user-approved richer
- lag risks and how they were removed or deferred
- low-end notes (images, motion, JS weight)
- asset budget notes when media or motion is involved

## Verification checklist

- [ ] Layout holds at 320px without horizontal scroll
- [ ] Touch targets are usable
- [ ] No hover-only critical action
- [ ] Heavy assets are deferred, compressed, or removed on mobile
- [ ] Asset budget respected or explicitly approved
- [ ] Reduced-motion path exists if motion is present
- [ ] Mobile path does not feel laggy by design intent
