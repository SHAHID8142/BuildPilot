# PLAIN-LANGUAGE (T-35)

Plain-language mode rewrites every user-facing gate message into words an
8th-grade reader can follow. It is **opt-in per project** and **inert when
unset**: if a project does not opt in, every gate message stays byte-identical
to the current technical style. Nothing in the default path changes.

## The law

When a project's `.sps/agent.md` contains a `language: plain` line, all
user-facing gate messages — kickoff, G1, G2, approval packets, and handoff —
must be shown using the plain templates in
`framework/sps2/templates/plain-gates/` instead of the technical defaults.

Each plain template:

- starts with one bolded line: `**What you're deciding:** ...` — a one-sentence
  summary of the choice in front of the user;
- uses 8th-grade vocabulary and short sentences (no jargon, no acronyms
  without a plain-word explanation);
- fills `{placeholders}` (e.g. `{project}`, `{section}`, `{options}`) from the
  gate's own data, never leaving raw braces the user has to guess at.

## How to opt in

Add one line to the project's `.sps/agent.md`:

```
language: plain
```

Spacing before/after the value and a trailing comment are tolerated
(`language:   plain   # client is non-technical`). Any other value —
`technical`, `plain-language`, anything else — means the technical default.
No `.sps/agent.md` at all also means the technical default.

## Technical default is unchanged

`language: plain` changes **only the wording shown to the user**. It does not:

- skip, weaken, or reorder any gate, check, or approval step;
- change what evidence the gates require;
- alter any file the framework writes for itself (plans, packets, ledgers).

The default (no `language` line, or `language: technical`) produces exactly
today's messages.

## Gate → template mapping

| Gate            | Plain template (framework/sps2/templates/plain-gates/) | Helper tool                    |
|-----------------|--------------------------------------------------------|--------------------------------|
| Kickoff         | `kickoff.md`                                           | `plain_language.py render <root> kickoff` |
| G1 confirm      | `g1.md`                                                | `plain_language.py render <root> g1`      |
| G2 confirm      | `g2.md`                                                | `plain_language.py render <root> g2`      |
| Approval packet | `approval-packet.md`                                   | `plain_language.py render <root> approval-packet` |
| Handoff         | `handoff.md`                                           | `plain_language.py render <root> handoff` |

`is_plain(project_root)` (in `framework/sps2/tools/plain_language.py`) is the
single decision point: gates call it first and only then reach for the plain
template. Unknown gates and missing templates fail closed with a
`PLAIN_GATE_MISSING` error (stderr, exit 1) — never a silently wrong message.

## Module registration note

Test module for CI registration: `framework.sps2.tests.test_plain_language`.
