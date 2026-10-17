#!/usr/bin/env python3
"""Plain-language gate renderer (T-35).

When a project opts in by putting `language: plain` in `.sps/agent.md`, gate
messages (kickoff, G1, G2, approval packet, handoff) are shown from the plain
templates in framework/sps2/templates/plain-gates/ instead of the technical
defaults. Without the opt-in this module is inert — the default path never
calls it, so default output stays byte-identical.

API:
    is_plain(project_root) -> bool
        True iff .sps/agent.md exists and contains a `language: plain` line.
        Tolerates spacing and a trailing comment; never matches other values
        (e.g. `language: technical`).

    render(project_root, gate, **fields) -> str
        Returns the plain template for `gate` with {placeholders} substituted
        from fields. Unknown {placeholders} are replaced with
        `<fill in: name>` rather than crashing — a missing field must never
        break the message.

Fail-closed convention (same as the other sps2 checkers):
    unknown gate or missing template file -> PLAIN_GATE_MISSING on stderr,
    exit 1. Never a silently wrong message.

CLI:
    python3 plain_language.py render <project_root> <gate> [--field k=v ...]
    python3 plain_language.py is-plain <project_root>     # prints true/false, exit 0

Stdlib-only, project-local, agent-neutral.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

GATES = ("kickoff", "g1", "g2", "approval-packet", "handoff")
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "plain-gates"

# `language: plain`, tolerating spacing and a trailing comment. Anchored so
# `language: technical` (or any other value) cannot match.
_PLAIN_LINE = re.compile(r"^\s*language\s*:\s*plain\b\s*(#.*)?$", re.MULTILINE)
# Any other explicit value — used only to keep is_plain honest about the
# "plain" prefix not leaking onto other words (handled by \b above).

FALLBACK = "<fill in: {name}>"


def is_plain(project_root: str | Path) -> bool:
    """True iff .sps/agent.md exists and sets `language: plain`."""
    agent_md = Path(project_root) / ".sps" / "agent.md"
    if not agent_md.is_file():
        return False
    try:
        text = agent_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return bool(_PLAIN_LINE.search(text))


def render(project_root: str | Path, gate: str, **fields: str) -> str:
    """Render the plain template for `gate` with {placeholders} filled."""
    gate = str(gate).strip().lower()
    if gate not in GATES:
        print(f"PLAIN_GATE_MISSING: unknown gate '{gate}' — expected one of: "
              f"{', '.join(GATES)}", file=sys.stderr)
        raise SystemExit(1)
    template_path = TEMPLATE_DIR / f"{gate}.md"
    if not template_path.is_file():
        print(f"PLAIN_GATE_MISSING: no plain template for gate '{gate}' at "
              f"{template_path}", file=sys.stderr)
        raise SystemExit(1)
    try:
        template = template_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"PLAIN_GATE_MISSING: cannot read template for gate '{gate}': "
              f"{exc}", file=sys.stderr)
        raise SystemExit(1)

    def _sub(match: re.Match[str]) -> str:
        name = match.group(1)
        value = fields.get(name)
        if value is None or str(value) == "":
            return FALLBACK.format(name=name)
        return str(value)

    return re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", _sub, template)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="plain_language.py",
        description="Render plain-language gate messages (language: plain mode).")
    sub = parser.add_subparsers(dest="command", required=True)

    p_render = sub.add_parser("render", help="render a gate's plain message")
    p_render.add_argument("project_root")
    p_render.add_argument("gate")
    p_render.add_argument("--field", action="append", default=[],
                          metavar="K=V", help="template field, repeatable")

    p_isplain = sub.add_parser("is-plain", help="print true/false, exit 0")
    p_isplain.add_argument("project_root")

    args = parser.parse_args(argv)
    if args.command == "is-plain":
        print("true" if is_plain(args.project_root) else "false")
        return 0

    fields: dict[str, str] = {}
    for item in args.field:
        key, sep, value = item.partition("=")
        if not sep:
            print(f"PLAIN_GATE_MISSING: bad --field '{item}' — expected K=V",
                  file=sys.stderr)
            return 1
        fields[key] = value
    print(render(args.project_root, args.gate, **fields))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
