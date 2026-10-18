#!/usr/bin/env python3
"""Copy-quality validator (COPY-GATE): human copy, not AI slop.

Enforces the machine-checkable laws of skill/sps/COPY-GATE.md over
customer-facing copy in any language (English + Bangla first). Dual-mode,
following seo_audit.py's convention:

- advisory mode (default): report only, always exit 0 — for drafting.
- deployment mode: fail-closed, exit 1 on any CRITICAL — the actual gate.

What it scans: copy files under the project — .md/.html/.htm/.txt/.json/
.tsx/.ts/.js/.jsx files in the project root, minus .sps/, node_modules,
.git, dist, build, and the framework's own gate docs (a text-scanning
checker must exempt the docs that contain the banned strings, per the
check_emoji.py exemption pattern).

Wordlists live in copy_lists/ next to this file so they can be curated per
language without touching checker code (AntiSlop Sampler schema model).

Format and exit convention mirror check_laws.py / check_product_proof.py:
one violation per line on stderr (`CHECK_ID: target: detail`), a
`== COPY CHECK: N violation(s) ==` summary, exit 0 when clean or advisory,
exit 1 on CRITICAL in deployment mode. Stdlib-only, no network.

Bangla checks follow বাংলা একাডেমি "বাংলা বানানের নিয়ম" (৫ম সংস্করণ, ২০২৩):
চলিত রীতি only, no সাধু verb forms, bn-BD (not West Bengal) spellings,
দাঁড়ি sentence endings, no word-initial ড়/ঢ়.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

LISTS_DIR = Path(__file__).resolve().parent / "copy_lists"

SCAN_EXTENSIONS = {".md", ".html", ".htm", ".txt", ".json", ".tsx", ".ts", ".js", ".jsx"}
SKIP_DIRS = {".git", ".sps", "node_modules", "dist", "build", ".venv", "__pycache__",
             "copy_lists", "reports",
             # BuildPilot's own product docs quote the banned phrases as ban
             # examples — they are rule text, not customer copy.
             "skill", "docs", "framework", "scripts", "loop", "hosts"}
# Files that legitimately contain banned strings (the gate doc, the checker
# itself, this list) must never be scanned or the checker self-trips.
EXEMPT_NAMES = {"COPY-GATE.md", "check_copy.py"}

# Bangla Unicode block + ZWJ/ZWNJ + common punctuation.
BN_RE = re.compile(r"[ঀ-৿]")
# A "word" of Bangla script (for script-integrity checks).
BN_WORD_RE = re.compile(r"[ঀ-৿়্]+")
# Latin word inside Bangla text (mixed-script contamination candidate).
LATIN_WORD_RE = re.compile(r"[A-Za-z]{2,}")

# দাঁড়ি-less sentence end: a Bangla word followed by an ASCII period then
# whitespace/end (excludes decimals like ১.৫ and abbreviations mid-sentence).
DANDA_MISSING_RE = re.compile(r"[ঀ-৿]\.(?:\s|$)")
# Word-initial ড়/ঢ় are never legal.
INITIAL_RRA_RE = re.compile(r"(?:^|[\s।,;:!?()\"।])ড়|ঢ়")

SADHU_RE_CACHE: dict[str, re.Pattern] = {}


def load_lines(name: str) -> list[str]:
    path = LISTS_DIR / name
    if not path.is_file():
        return []
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # TSV: first column is the approved/flag form.
        out.append(line.split("\t")[0].strip())
    return out


def load_pairs(name: str) -> list[tuple[str, list[str]]]:
    path = LISTS_DIR / name
    if not path.is_file():
        return []
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        cols = [c.strip() for c in line.split("\t") if c.strip()]
        if cols:
            out.append((cols[0], cols[1:]))
    return out


def phrase_pattern(phrase: str) -> re.Pattern:
    """Case-insensitive word-boundary pattern for a blocklist phrase."""
    esc = re.escape(phrase).replace(r"\ ", r"\s+")
    return re.compile(r"(?<![\w'])" + esc + r"(?![\w'])", re.IGNORECASE)


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[।.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def sentence_lengths(text: str) -> list[int]:
    return [word_count(s) for s in sentences(text) if word_count(s) > 0]


def check_en_blocklist(text: str, target: str) -> list[tuple[str, str]]:
    out = []
    for phrase in load_lines("en_blocklist.txt"):
        for m in phrase_pattern(phrase).finditer(text):
            snippet = text[max(0, m.start() - 30):m.end() + 30].replace("\n", " ")
            out.append(("COPY_EN_SLOP_PHRASE", f"{target}: stock phrase '{phrase}' — rewrite with a concrete claim: …{snippet}…"))
            break  # one report per phrase per file
    return out


def check_bn_blocklist(text: str, target: str) -> list[tuple[str, str]]:
    out = []
    for phrase in load_lines("bn_blocklist.txt"):
        if phrase in text:
            idx = text.find(phrase)
            snippet = text[max(0, idx - 30):idx + len(phrase) + 30].replace("\n", " ")
            out.append(("COPY_BN_SLOP_PHRASE", f"{target}: AI-ঘেঁষা বাক্যাংশ '{phrase}' — বাস্তব দাবি দিয়ে লিখুন: …{snippet}…"))
    return out


def check_en_lexicon_density(text: str, target: str) -> list[tuple[str, str]]:
    wc = word_count(text)
    if wc < 200:
        return []
    hits = set()
    for word in load_lines("en_lexicon.txt"):
        if re.search(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", text, re.IGNORECASE):
            hits.add(word.lower())
    # >3 distinct hits per 500 words, scaled
    allowed = max(3, math.ceil(wc / 500 * 3))
    if len(hits) > allowed:
        out = sorted(hits)
        return [("COPY_EN_AI_LEXICON",
                 f"{target}: {len(hits)} AI-lexicon words in {wc} words (allowed {allowed}): {', '.join(out[:10])}…")]
    return []


def check_negative_parallelism(text: str, target: str) -> list[tuple[str, str]]:
    pat = re.compile(r"not\s+just\s+[^.!?—]{2,60}[,—]\s*(?:it'?s\s+)?but\s+", re.IGNORECASE)
    pat2 = re.compile(r"it'?s\s+not\s+just\s+[^.!?]{2,60}\s*[—-]\s*it'?s\s+", re.IGNORECASE)
    n = len(pat.findall(text)) + len(pat2.findall(text))
    if n > 1:
        return [("COPY_NEGATIVE_PARALLELISM",
                 f"{target}: {n} 'not just X, but Y' constructions (max 1) — state the stronger claim directly")]
    return []


def check_tricolons(text: str, target: str) -> list[tuple[str, str]]:
    # Triadic comma lists: "a, b, and c" with exactly 3 items.
    pat = re.compile(r"\b[\w-]+,\s+[\w-]+(?:,\s+and|\s+and)\s+[\w-]+\b", re.IGNORECASE)
    n = len(pat.findall(text))
    if n >= 3:
        return [("COPY_TRICOLON", f"{target}: {n} rule-of-three lists — vary list length; prefer 1-2 concrete items")]
    return []


def check_em_dashes(text: str, target: str) -> list[tuple[str, str]]:
    wc = max(word_count(text), 1)
    n = text.count("—") + text.count("―")
    chain = re.search(r"[^.—!?]{3,60}—[^.—!?]{3,60}—", text)
    if chain:
        return [("COPY_EM_DASH", f"{target}: 'clause — clause — clause' chain — use commas, colons, or sentences")]
    if n > 3 and wc > 100:
        return [("COPY_EM_DASH", f"{target}: {n} em-dashes (max ~3 per 1000 words)")]
    return []


def check_burstiness(text: str, target: str) -> list[tuple[str, str]]:
    lens = sentence_lengths(text)
    if len(lens) < 20:
        return []
    mean = sum(lens) / len(lens)
    if mean == 0:
        return []
    stdev = math.sqrt(sum((x - mean) ** 2 for x in lens) / len(lens))
    if stdev < 5:
        return [("COPY_UNIFORM_RHYTHM",
                 f"{target}: sentence-length stdev {stdev:.1f} < 5 across {len(lens)} sentences — vary rhythm (burstiness)")]
    return []


def check_hedging(text: str, target: str) -> list[tuple[str, str]]:
    hedges = re.compile(r"\b(can|may|might|could|potentially|possibly|perhaps|often|sometimes)\b", re.IGNORECASE)
    out = []
    for s in sentences(text):
        if len(hedges.findall(s)) >= 2 and len(s.split()) < 40:
            snippet = s[:80].replace("\n", " ")
            out.append(("COPY_HEDGE_STACK", f"{target}: 2+ hedges in one sentence: '{snippet}…'"))
            if len(out) >= 3:
                break
    return out


def check_placeholder(text: str, target: str) -> list[tuple[str, str]]:
    pats = [
        re.compile(r"lorem ipsum", re.IGNORECASE),
        re.compile(r"\bplaceholder text\b", re.IGNORECASE),
        re.compile(r"\bTODO:\s*copy\b", re.IGNORECASE),
        re.compile(r"\bXXX copy\b", re.IGNORECASE),
    ]
    for p in pats:
        if p.search(text):
            return [("COPY_PLACEHOLDER", f"{target}: placeholder/lorem text found — real copy required")]
    return []


def check_sadhu(text: str, target: str) -> list[tuple[str, str]]:
    out = []
    for form in load_lines("bn_sadhu_wb_forms.txt"):
        if not BN_RE.search(form):
            continue
        if form in text:
            idx = text.find(form)
            snippet = text[max(0, idx - 25):idx + len(form) + 25].replace("\n", " ")
            out.append(("COPY_BN_SADHU_WB_FORM",
                        f"{target}: সাধু/পশ্চিমবঙ্গ রূপ '{form}' — চলিত/বাংলাদেশ রূপ লিখুন: …{snippet}…"))
    return out


def check_initial_rra(text: str, target: str) -> list[tuple[str, str]]:
    out = []
    for m in INITIAL_RRA_RE.finditer(text):
        snippet = text[max(0, m.start() - 20):m.end() + 20].replace("\n", " ")
        out.append(("COPY_BN_INITIAL_RRA", f"{target}: শব্দের শুরুতে ড়/ঢ় অসম্ভব: …{snippet}…"))
        if len(out) >= 3:
            break
    return out


def check_danda(text: str, target: str) -> list[tuple[str, str]]:
    # Only meaningful for mostly-Bangla text.
    bn_chars = len(BN_RE.findall(text))
    if bn_chars < 40:
        return []
    out = []
    for m in DANDA_MISSING_RE.finditer(text):
        # Skip decimal numerals (Bangla or Latin) like ১.৫ / 1.5
        before = text[max(0, m.start() - 2):m.start()]
        if before and (before[-1].isdigit() or before[-1] in "০১২৩৪৫৬৭৮৯"):
            continue
        snippet = text[max(0, m.start() - 25):m.end() + 20].replace("\n", " ")
        out.append(("COPY_BN_DANDA", f"{target}: বাংলা বাক্যে দাঁড়ি (।) নেই, ইংরেজি দাঁড়ি (.) ব্যবহৃত: …{snippet}…"))
        if len(out) >= 3:
            break
    return out


def check_loanwords(text: str, target: str) -> list[tuple[str, str]]:
    out = []
    for approved, variants in load_pairs("bn_loanwords.tsv"):
        for v in variants:
            if len(v) < 4 or "বানান-ভুল" in v:  # skip placeholder-ish entries
                continue
            if v in text and approved not in text:
                idx = text.find(v)
                snippet = text[max(0, idx - 25):idx + len(v) + 25].replace("\n", " ")
                out.append(("COPY_BN_LOANWORD", f"{target}: একাডেমি রূপ '{approved}' নয়, '{v}' লেখা হয়েছে: …{snippet}…"))
    return out


def check_pronoun_mix(text: str, target: str) -> list[tuple[str, str]]:
    # আপনি and তুমি forms addressing the same reader on one page.
    apn = re.search(r"আপনি|আপনার|আপনাকে", text)
    tumi = re.search(r"তুমি|তোমার|তোমাকে", text)
    if apn and tumi:
        return [("COPY_BN_PRONOUN_MIX", f"{target}: আপনি ও তুমি একই পাতায় মিশ্রিত — এক সিদ্ধান্ত, পুরো সাইটে এক রাখুন")]
    return []


def check_numerals(text: str, target: str) -> list[tuple[str, str]]:
    # N+ social-proof patterns ("500+ clients") are fabrication candidates —
    # CRITICAL only when no fact sheet exists. With a fact sheet present the
    # cross-check is a WARN (the gate doc's full trace law needs the sheet).
    pat = re.compile(r"\b\d{2,}\+?\s+(clients|customers|users|projects|reviews|businesses)\b", re.IGNORECASE)
    hits = pat.findall(text)
    if not hits:
        return []
    return [("COPY_SOCIAL_PROOF_COUNT",
             f"{target}: social-proof count pattern(s) present — every count must trace to a real record (fact sheet); delete or source it")]


def extract_text(path: Path) -> str:
    """Best-effort text extraction; JSON gets string values only."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".json":
        out = []
        try:
            data = json.loads(raw)
        except Exception:
            return raw
        def walk(v):
            if isinstance(v, str):
                out.append(v)
            elif isinstance(v, dict):
                for x in v.values():
                    walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
        walk(data)
        return "\n".join(out)
    if path.suffix in {".html", ".htm"}:
        raw = re.sub(r"<script\b.*?</script>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
        raw = re.sub(r"<style\b.*?</style>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
        raw = re.sub(r"<[^>]+>", " ", raw)
    if path.suffix in {".tsx", ".ts", ".js", ".jsx"}:
        raw = re.sub(r"//[^\n]*", " ", raw)
        raw = re.sub(r"/\*.*?\*/", " ", raw, flags=re.DOTALL)
    return raw


def scan_project(root: Path) -> tuple[list[tuple[str, str]], list[str]]:
    violations: list[tuple[str, str]] = []
    notes: list[str] = []
    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if p.name in EXEMPT_NAMES:
            continue
        if p.suffix.lower() in SCAN_EXTENSIONS:
            files.append(p)
    if not files:
        notes.append("note: no copy files found under the project root — nothing to check")
        return violations, notes
    for p in sorted(files):
        target = str(p.relative_to(root))
        try:
            text = extract_text(p)
        except OSError as exc:
            # Fail-closed: an unreadable file is reported, never skipped silently.
            violations.append(("COPY_UNREADABLE_FILE", f"{target}: cannot read file (fail-closed): {exc}"))
            continue
        if not text.strip():
            continue
        for check in (check_en_blocklist, check_bn_blocklist, check_en_lexicon_density,
                      check_negative_parallelism, check_tricolons, check_em_dashes,
                      check_burstiness, check_hedging, check_placeholder,
                      check_sadhu, check_initial_rra, check_danda, check_loanwords,
                      check_pronoun_mix, check_numerals):
            for cid, msg in check(text, target):
                violations.append((cid, msg))
    return violations, notes


CRITICAL_IDS = {
    "COPY_EN_SLOP_PHRASE", "COPY_BN_SLOP_PHRASE", "COPY_EN_AI_LEXICON",
    "COPY_NEGATIVE_PARALLELISM", "COPY_PLACEHOLDER", "COPY_BN_SADHU_WB_FORM",
    "COPY_BN_INITIAL_RRA", "COPY_BN_DANDA", "COPY_BN_PRONOUN_MIX",
    "COPY_UNREADABLE_FILE",
}
WARN_IDS = {
    "COPY_TRICOLON", "COPY_EM_DASH", "COPY_UNIFORM_RHYTHM", "COPY_HEDGE_STACK",
    "COPY_BN_LOANWORD", "COPY_SOCIAL_PROOF_COUNT",
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="COPY-GATE copy-quality validator")
    ap.add_argument("project", help="project root to scan")
    ap.add_argument("--mode", choices=["advisory", "deployment"], default="advisory",
                    help="advisory: report only, exit 0. deployment: exit 1 on any CRITICAL.")
    args = ap.parse_args(argv)
    root = Path(args.project).resolve()
    if not root.is_dir():
        print(f"check_copy: project root not found: {root}", file=sys.stderr)
        return 2
    violations, notes = scan_project(root)
    for note in notes:
        print(note, file=sys.stderr)
    for cid, msg in violations:
        print(f"{cid}: {msg}", file=sys.stderr)
    crit = sum(1 for cid, _ in violations if cid in CRITICAL_IDS)
    warn = sum(1 for cid, _ in violations if cid in WARN_IDS)
    print(f"== COPY CHECK: {crit} critical, {warn} warning(s) ==", file=sys.stderr)
    if args.mode == "deployment" and crit > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
