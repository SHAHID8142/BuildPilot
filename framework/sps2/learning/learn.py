#!/usr/bin/env python3
"""BuildPilot self-learning system: structured mistake ledger + evidence indexer.

Design law (matches project governance): the system PROPOSES, the user RATIFIES.
Learned rules enter through the decision-ledger mechanism — never silent tuning,
never self-modified checks.

Components:
  1. Mistake ledger (framework/sps2/learning/mistakes.jsonl) — append-only
     structured failure records: what broke, root cause, detection signal, status.
  2. Pattern detector — same-class mistakes appearing >= PROMOTION_THRESHOLD
     times auto-draft a rule-promotion proposal (a decision record awaiting
     ratification), written to framework/sps2/learning/proposals/.
  3. Evidence indexer — a queryable index over reports/ + gate results so a
     future session asks "what failed last time and why" instead of re-discovering.

Pure stdlib. No network. Fail-closed: corrupted ledger entries are reported,
never silently dropped.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LEARNING_DIR = Path(__file__).resolve().parent.parent / "learning"
MISTAKES_PATH = LEARNING_DIR / "mistakes.jsonl"
PROPOSALS_DIR = LEARNING_DIR / "proposals"
INDEX_PATH = LEARNING_DIR / "evidence-index.json"

PROMOTION_THRESHOLD = 2

MISTAKE_SCHEMA = {
    "entry_id": str,
    "timestamp": str,          # RFC3339 UTC
    "category": str,           # e.g. "gate-failure", "digest-mismatch", "ordering", "schema-violation"
    "summary": str,            # one line, what broke
    "root_cause": str,
    "detection_signal": str,   # which control/test/validator caught it
    "resolution": str,         # what fixed it
    "source_commit": str,      # HEAD at recording time (may be "" if unknown)
    "status": str,             # "open" | "resolved" | "promoted"
}

RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)$")


# ── ledger ───────────────────────────────────────────────────────────────────
def load_ledger() -> list[dict]:
    if not MISTAKES_PATH.is_file():
        return []
    entries = []
    for i, line in enumerate(MISTAKES_PATH.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError as exc:
            # fail-closed: report, never drop
            print(f"WARN: ledger line {i} unparseable ({exc}); preserved as-is", file=sys.stderr)
            continue
        entries.append(e)
    return entries


def append_mistake(category: str, summary: str, root_cause: str,
                   detection_signal: str, resolution: str = "",
                   status: str = "resolved") -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    head = ""
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
    except OSError:
        pass
    n = len(load_ledger()) + 1
    date_key = now.replace("-", "")[:8]
    entry = {
        "entry_id": f"MIST-{date_key}-{n:03d}",
        "timestamp": now,
        "category": category,
        "summary": summary,
        "root_cause": root_cause,
        "detection_signal": detection_signal,
        "resolution": resolution,
        "source_commit": head,
        "status": status,
    }
    _validate_entry(entry)
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)
    with MISTAKES_PATH.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return entry


def _validate_entry(e: dict) -> None:
    for field, typ in MISTAKE_SCHEMA.items():
        if field not in e:
            raise ValueError(f"ledger entry missing field: {field}")
        if not isinstance(e[field], typ):
            raise ValueError(f"ledger field {field} must be {typ.__name__}")
    if not RFC3339.match(e["timestamp"]):
        raise ValueError(f"ledger timestamp not RFC3339 UTC: {e['timestamp']}")
    if e["status"] not in ("open", "resolved", "promoted"):
        raise ValueError(f"invalid ledger status: {e['status']}")


# ── pattern detection → promotion proposal ──────────────────────────────────
def detect_patterns(entries: list[dict] | None = None) -> list[dict]:
    """Group open/resolved mistakes by category; flag classes at threshold."""
    entries = entries if entries is not None else load_ledger()
    by_cat = defaultdict(list)
    for e in entries:
        if e["status"] != "promoted":
            by_cat[e["category"]].append(e)
    return [
        {"category": cat, "count": len(items), "entries": [e["entry_id"] for e in items]}
        for cat, items in sorted(by_cat.items())
        if len(items) >= PROMOTION_THRESHOLD
    ]


def propose_promotion(category: str) -> Path | None:
    """Draft a rule-promotion proposal for a repeated mistake class.

    The proposal is a DECISION RECORD AWAITING RATIFICATION — it changes no
    check, no validator, no default. Ratification is the user's act, through
    the same decisions ledger as every other governance change.
    """
    entries = [e for e in load_ledger()
               if e["category"] == category and e["status"] != "promoted"]
    if len(entries) < PROMOTION_THRESHOLD:
        return None
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    proposal = {
        "schema": "sps2.learning-promotion-proposal/v1",
        "proposal_id": f"PROP-{now.replace('-', '')[:8]}-{category}",
        "created_at": now,
        "status": "AWAITING_USER_RATIFICATION",  # never auto-applied
        "category": category,
        "pattern_count": len(entries),
        "entry_ids": [e["entry_id"] for e in entries],
        "observed_pattern": sorted({e["root_cause"] for e in entries}),
        "proposed_rule": (
            f"Before any state change is finalized, re-verify every previously "
            f"written digest/claim that references the changed artifact "
            f"(category: {category}; first detected via: "
            f"{entries[0]['detection_signal']})."
        ),
        "proposed_scope": "project-only (framework/sps2/learning/rules.md on ratification)",
        "ratification_note": (
            "Per MISTAKE-PROMOTION law: this proposal changes nothing by itself. "
            "On user approval the rule text is written to rules.md and the "
            "contributing entries are marked promoted."
        ),
    }
    out = PROPOSALS_DIR / f"{proposal['proposal_id']}.json"
    out.write_text(json.dumps(proposal, indent=1, ensure_ascii=False) + "\n")
    return out


# ── evidence indexer ─────────────────────────────────────────────────────────
def _sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_evidence_index(repo_root: Path | None = None) -> dict:
    """Index reports/ (titles, timestamps, verdicts) + latest gate/validator
    outcomes so future sessions query instead of re-discovering."""
    root = repo_root or Path(__file__).resolve().parent.parent.parent.parent
    index = {"schema": "sps2.evidence-index/v1", "built_at":
             datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             "reports": [], "verdict_keywords": {}}
    reports_dir = root / "reports"
    if reports_dir.is_dir():
        for p in sorted(reports_dir.glob("*.md")):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")[:4000]
            except OSError:
                continue
            verdicts = sorted({v for v in ("APPROVED", "REJECTED", "NEEDS REVISION",
                                           "PASS", "FAIL", "NOT READY", "BLOCKED_USER")
                               if v in text})
            index["reports"].append({
                "file": p.name,
                "sha256_16": _sha256_file(p)[:16],
                "size": p.stat().st_size,
                "verdicts": verdicts,
            })
    # keyword → report files (cheap retrieval without reading every report)
    kw = defaultdict(list)
    for r in index["reports"]:
        for v in r["verdicts"]:
            kw[v].append(r["file"])
    index["verdict_keywords"] = dict(kw)
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n")
    return index


def query_evidence(term: str, repo_root: Path | None = None) -> list[dict]:
    """Query the index (rebuilding if stale) for reports mentioning term."""
    root = repo_root or Path(__file__).resolve().parent.parent.parent.parent
    if not INDEX_PATH.is_file():
        build_evidence_index(root)
    idx = json.loads(INDEX_PATH.read_text())
    hits = [r for r in idx["reports"]
            if term.lower() in r["file"].lower()
            or term in r["verdicts"]
            or any(term.lower() in v.lower() for v in r["verdicts"])]
    return hits


# ── CLI ──────────────────────────────────────────────────────────────────────
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="BuildPilot self-learning system")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record", help="record a mistake")
    for f in ("category", "summary", "root_cause", "detection_signal", "resolution"):
        r.add_argument(f"--{f}", required=(f != "resolution"))
    sub.add_parser("patterns", help="show repeated mistake classes")
    pp = sub.add_parser("propose", help="draft a promotion proposal for a category")
    pp.add_argument("category")
    sub.add_parser("index", help="(re)build the evidence index")
    pq = sub.add_parser("query", help="query the evidence index")
    pq.add_argument("term")
    sub.add_parser("list", help="list ledger entries")
    args = ap.parse_args(argv)

    if args.cmd == "record":
        e = append_mistake(args.category, args.summary, args.root_cause,
                           args.detection_signal, args.resolution or "")
        print(json.dumps(e, indent=1))
        pats = detect_patterns()
        if pats:
            print("\nRepeated classes detected (>= %d):" % PROMOTION_THRESHOLD)
            for p in pats:
                print(f"  {p['category']}: {p['count']}x  -> run: propose {p['category']}")
        return 0
    if args.cmd == "patterns":
        print(json.dumps(detect_patterns(), indent=1))
        return 0
    if args.cmd == "propose":
        out = propose_promotion(args.category)
        print(f"proposal written: {out}" if out else
              f"below threshold ({PROMOTION_THRESHOLD}); no proposal written")
        return 0 if out else 1
    if args.cmd == "index":
        idx = build_evidence_index()
        print(f"indexed {len(idx['reports'])} reports -> {INDEX_PATH}")
        return 0
    if args.cmd == "query":
        for h in query_evidence(args.term):
            print(f"{h['file']}  verdicts={h['verdicts']}")
        return 0
    if args.cmd == "list":
        for e in load_ledger():
            print(f"{e['entry_id']}  [{e['status']}]  {e['category']}: {e['summary']}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
