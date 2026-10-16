#!/usr/bin/env python3
"""SPEC-2 anti-regression and cross-consumer consistency tests.

Two failure modes motivated this file:

1. DRIFT. Before SPEC-2, twelve independent agent-token lists existed across four
   languages with no shared constant. Nothing prevented a thirteenth. These tests
   fail if a hardcoded agent-token alternation reappears outside the single
   authoritative policy file.
2. DIVERGENT VERDICTS. The same decided_by value could be accepted by one
   validator and rejected by another depending on which list that validator
   happened to carry. These tests assert that every migrated consumer now
   returns the same policy verdict for the same input.

These tests check POLICY CONSISTENCY only. They prove nothing about identity:
a non-match does not establish that a human User decided. See
sps2/governance/attribution_policy.json and REQ-P5-04.
"""
import json
import os
import re
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPS2 = os.path.join(REPO, "sps2")
GOVERNANCE = os.path.join(SPS2, "governance")
POLICY_PATH = os.path.join(GOVERNANCE, "attribution_policy.json")

# The revision whose pre-consolidation token lists the provenance narrative in
# attribution_policy.json describes. It is PINNED, not "HEAD".
#
# Why pinned: TestKnownDivergencesAreAccurate recomputes what the policy says
# about the state of the tree BEFORE the SPEC-2 consolidation. Reading
# "HEAD:<path>" made those assertions depend on the moving HEAD, so they became
# self-referential and failed as soon as the consolidation itself was committed:
# HEAD then *was* the consolidated tree, so e.g. check_sps2.py no longer
# contained the '|ai|' literal the test looks for, and the historical denylist
# counts recomputed as zero. The facts being asserted are historical constants,
# so they must be read from a fixed historical revision.
#
# 788bf8a is the last revision before the consolidation and is an ancestor of
# every later revision, so this holds both before and after that work is
# committed. `git show <rev>:<path>` still proves the invariant: if a genuine
# historical list is reintroduced into a migrated consumer, the live drift
# detector (TestNoDriftingTokenLists) and the consumer-identity assertions
# still fail. Pinning only fixes WHICH revision the historical narration is
# compared against; it does not weaken any assertion.
BASELINE_REV = "788bf8a2892ee72705276c9d846626ca0470400d"

if GOVERNANCE not in sys.path:
    sys.path.insert(0, GOVERNANCE)
import attribution  # noqa: E402

# Consumers migrated under SPEC-2. Each is (module path, attribute name).
MIGRATED_CONSUMERS = [
    ("capability/engine.py", "AGENTISH"),
    ("capability/promotion_gates.py", "AGENTISH"),
    ("tools/check_p2.py", "AGENT"),
    ("tools/check_sps2.py", "AGENT"),
]

# Every declared token, for the drift detector. Built from the policy itself so
# this file never hardcodes a list of its own.
def _policy_tokens():
    with open(POLICY_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)["tokens"]


SCANNED_SUFFIXES = (".py", ".sh", ".json", ".ts", ".js", ".ps1", ".mjs")


def _iter_source_files():
    for root in (os.path.join(SPS2, "capability"), os.path.join(SPS2, "tools"),
                 os.path.join(SPS2, "governance"), os.path.join(SPS2, "p17"),
                 os.path.join(SPS2, "core"), os.path.join(SPS2, "tests"),
                 os.path.join(REPO, "domain"), os.path.join(SPS2)):
        if os.path.abspath(root) == os.path.abspath(SPS2):
            continue  # covered by the specific subtrees above
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for name in filenames:
                if name.endswith(SCANNED_SUFFIXES):
                    yield os.path.join(dirpath, name)


# Vocabulary-shaped literals that are NOT approver-attribution denylists.
# Each entry is (repo-relative path, anchor substring, reason). An allowlist
# entry is a claim that must stay true; adding to it is a governed change.
#
# Two categories are recognised and deliberately NOT migrated:
#
#  1. CORE-NEUTRALITY SCANS. REQ-P5-04 requires core/ to be vendor-neutral, so
#     these scan core source TEXT for vendor names using SUBSTRING matching.
#     They answer "does this file mention a vendor", not "whose name is on this
#     approval". Merging them would match "ai" inside availability / raised /
#     contains and flag every core module. See attribution_policy.json.
#  2. NON-IDENTITY LISTS. Adapter names (which codex/opencode adapters exist)
#     and filesystem config-directory globs, where the words are path segments.
# Exemptions are scoped to ONE EXACT LITERAL, never to a whole file. A
# per-file exemption would let any allowlisted file hide a brand-new denylist,
# which is precisely the unauthenticated-allowlist weakness this test exists to
# prevent. Comparison is whitespace-normalised so a literal may wrap lines.
_VENDOR_TUPLE = ('("cline", "claude", "codex", "cursor", "copilot", "windsurf", '
                 '"aider", "gemini", "opencode", "gpt")')
ALLOWED_VOCABULARIES = [
    ("sps2/tools/validate-p5.py", _VENDOR_TUPLE,
     "core-neutrality substring scan over sps2/core source (REQ-P5-04)"),
    ("sps2/tools/test-portability.py", _VENDOR_TUPLE,
     "core-neutrality substring scan over sps2/core source (REQ-P5-04)"),
    ("sps2/tests/test_p5.py", _VENDOR_TUPLE,
     "core-neutrality assertion for the same scan (REQ-P5-04)"),
    ("sps2/tools/validate-sps2.sh",
     r"\b(claude|cursor|codex|gemini|opencode|cline|antigravity)\b",
     "core-neutrality substring scan over sps2/core source (REQ-P5-04)"),
    ("sps2/tools/portability.py", '("codex", "opencode")',
     "adapter inventory for D-P3-A; not an approver denylist"),
    ("sps2/tools/test-p7-readiness-mutation.sh", "('codex','opencode')",
     "adapter-inventory mutation fixture; not an approver denylist"),
    ("sps2/tools/validate-p3.sh", "(sps|claude|codex|config)",
     "config-directory path glob; the words are path segments, not identities"),
]


def _drift_signatures(tokens):
    """Regexes matching the two shapes a hardcoded token list takes."""
    alt = "|".join(re.escape(t) for t in sorted(tokens, key=len, reverse=True))
    return [
        # NOTE: a deliberately ABSENT single-element signature.
        # A one-entry list - re.compile(r"\\bgrok\\b") or ("antigravity",) - is
        # indistinguishable from ordinary data: this repository legitimately
        # contains "codex"/"opencode" adapter ids, "opencode" allowlist entries
        # and agent-named test fixtures. A quoted-token scan flags 27 such data
        # sites and would train everyone to ignore this test. The gap is real
        # and is asserted explicitly by
        # test_single_element_lists_are_a_known_uncovered_gap below rather than
        # papered over with a guard that cries wolf.
        # r'\b(agent|ai|...)\b'  and  '(agent|ai|...)'
        re.compile(r"[\(\[]?\s*(?:%s)(?:\s*\|\s*(?:%s))+\s*[\)\]]?" % (alt, alt)),
        # ("cline", "claude", ...) / ('codex','opencode')
        re.compile(r"""\(\s*(['"])(?:%s)\1(?:\s*,\s*(?:(['"])(?:%s)\2))+\s*[^)]*\)"""
                    % (alt, alt)),
    ]


def _relpath(path):
    return os.path.relpath(os.path.abspath(path), REPO)


def _skip_paths():
    return {
        "sps2/governance/attribution.py",       # the single consumer
        "sps2/governance/attribution_policy.json",
        _relpath(os.path.abspath(__file__)),    # this detector
    }


def _norm(text):
    return re.sub(r"\s+", " ", text).strip()


def _scan_for_drift():
    tokens = set(_policy_tokens())
    signatures = _drift_signatures(tokens)
    skip = _skip_paths()
    hits = []
    for path in _iter_source_files():
        rel = _relpath(path)
        if rel in skip:
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except OSError:
            continue
        # Exemptions for THIS file are exact literals, not the whole file.
        exempt = [_norm(lit) for p, lit, _ in ALLOWED_VOCABULARIES if p == rel]
        for sig in signatures:
            for match in sig.finditer(text):
                found = _norm(match.group(0))
                # A signature may capture only part of a mixed literal (it stops
                # at words that are not policy tokens), so containment in either
                # direction is accepted. The literal is still pinned exactly.
                if any(found in e or e in found for e in exempt):
                    continue
                line = text.count("\n", 0, match.start()) + 1
                hits.append("%s:%d %s" % (rel, line, found[:70]))
    return sorted(set(hits))


class TestAuthoritativePolicyArtifact(unittest.TestCase):
    def test_policy_file_exists_and_is_json(self):
        self.assertTrue(os.path.isfile(POLICY_PATH), POLICY_PATH)
        with open(POLICY_PATH, "r", encoding="utf-8") as fh:
            policy = json.load(fh)
        self.assertIsInstance(policy.get("tokens"), list)

    def test_tokens_are_non_empty_strings(self):
        tokens = _policy_tokens()
        self.assertTrue(tokens)
        for token in tokens:
            self.assertIsInstance(token, str)
            self.assertTrue(token.strip())

    # The 17 ratified tokens, pinned literally. DEC-0025 (ATTRIBUTION-POLICY-DECISIONS)
    # admitted 'antigravity'; DEC-0026/0027 kept autonomous/self/script excluded.
    EXPECTED_TOKENS = frozenset({
        "agent", "ai", "assistant", "model", "bot", "claude", "cursor", "codex",
        "gemini", "opencode", "cline", "copilot", "windsurf", "aider",
        "chatgpt", "gpt", "antigravity",
    })

    def test_token_set_is_exactly_the_ratified_seventeen_tokens(self):
        tokens = set(_policy_tokens())
        with self.subTest():
            self.assertEqual(len(_policy_tokens()), len(self.EXPECTED_TOKENS),
                             "the token list has duplicate entries")
        self.assertEqual(
            tokens, self.EXPECTED_TOKENS,
            "the token set changed. Adding or REMOVING a token is a governed "
            "change requiring a User decision record (see "
            "attribution_policy.json schema_note). If a User decision has been "
            "recorded, update EXPECTED_TOKENS and the open decision record "
            "together. Added=%r Removed=%r"
            % (sorted(tokens - self.EXPECTED_TOKENS),
               sorted(self.EXPECTED_TOKENS - tokens)))

    def test_no_vendor_outside_the_approved_set(self):
        """Named explicitly so a plausible new vendor cannot slip in unnoticed."""
        # 'antigravity' is deliberately ABSENT: DEC-0025 admitted it.
        banned = {"grok", "devin", "replit", "kiro",
                  "self", "script", "autonomous"}
        self.assertFalse(
            set(_policy_tokens()) & banned,
            "a token with no approved basis entered the set")

    def test_matcher_derives_its_tokens_from_the_policy_file(self):
        """The compiled matcher must reflect the policy, not a private copy."""
        expected = r"\b(%s)\b" % "|".join(re.escape(t) for t in _policy_tokens())
        self.assertEqual(attribution.AGENTISH.pattern, expected)

    def test_matcher_remains_case_insensitive_and_boundary_anchored(self):
        """SPEC-2 preserves the approved matcher semantics exactly."""
        self.assertTrue(attribution.AGENTISH.flags & re.IGNORECASE)
        self.assertTrue(attribution.AGENTISH.pattern.startswith(r"\b("))
        self.assertTrue(attribution.AGENTISH.pattern.endswith(r")\b"))

    def test_policy_failure_is_loud_not_silent(self):
        """A missing or empty policy must raise, never degrade to an empty
        vocabulary that would admit every approver identity."""
        with self.assertRaises((ValueError, IOError, OSError)):
            attribution.load_agent_tokens(path=os.path.join(REPO, "no-such-policy.json"))


class TestNoDriftingTokenLists(unittest.TestCase):
    """A hardcoded token list is how the twelve original lists appeared."""

    def test_no_hardcoded_agent_token_list_outside_the_policy(self):
        hits = _scan_for_drift()
        self.assertEqual(
            hits, [],
            "hardcoded agent-token list(s) reintroduced outside the authoritative "
            "policy: %r — consumers must consume attribution.AGENTISH" % (hits,))

    def test_allowlisted_vocabularies_still_exist_and_stay_justified(self):
        """Guards the allowlist itself: every entry names a literal that is
        really present, and carries a stated reason.

        If a core-neutrality scan is renamed or deleted its entry becomes an
        unverifiable excuse, and this fails rather than silently widening the
        exemption.
        """
        for rel, literal, why in ALLOWED_VOCABULARIES:
            with self.subTest(entry=rel + " :: " + literal[:40]):
                self.assertTrue(why.strip(), "allowlist entry needs a reason")
                path = os.path.join(REPO, rel)
                self.assertTrue(os.path.isfile(path), "missing: %s" % rel)
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
                self.assertIn(
                    _norm(literal), _norm(text),
                    "allowlisted literal %r is no longer present in %s; "
                    "remove or update the entry" % (literal, rel))

    def test_exemptions_are_scoped_per_literal_not_per_file(self):
        """A per-file exemption would hide any new denylist in that file.

        Assert the mechanism directly: a synthetic denylist injected into an
        ALLOWLISTED file must still be reported as drift.
        """
        rel = "sps2/tools/validate-p3.sh"
        # Composed only of policy tokens so the signature captures it whole.
        synthetic = r"\b(agent|ai|assistant|bot|model)\b"
        exempt = [_norm(lit) for p, lit, _ in ALLOWED_VOCABULARIES if p == rel]
        path = os.path.join(REPO, rel)
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
        injected = text + "\nAGENTISH = re.compile(r'%s', re.I)\n" % synthetic
        want = "(agent|ai|assistant|bot|model)"
        detected = [
            _norm(m.group(0))
            for sig in _drift_signatures(set(_policy_tokens()))
            for m in sig.finditer(injected)
            if not any(_norm(m.group(0)) in e or e in _norm(m.group(0)) for e in exempt)
        ]
        self.assertTrue(
            any(want == d or want in d for d in detected),
            "a new denylist inside an allowlisted file went unnoticed; "
            "detected=%r" % (detected,))

    def test_single_element_lists_are_a_known_uncovered_gap(self):
        """Documents what this detector deliberately does NOT catch.

        A one-entry denylist is indistinguishable from data, so it is not
        detected. This test pins that limitation so it cannot be mistaken for
        coverage. Closing it would need a structural signal (a literal passed
        straight to re.compile and used only for .search) and is deferred.
        """
        signatures = _drift_signatures(set(_policy_tokens()))
        probes = {
            "re.compile(r'\\bgrok\\b')": r"\bgrok\b",
            "AGENTS = ('antigravity',)": "('antigravity',)",
            "AGENTS = ['antigravity']": "['antigravity']",
        }
        for label, probe in probes.items():
            with self.subTest(probe=label):
                found = any(sig.search(probe) for sig in signatures)
                self.assertFalse(
                    found,
                    "single-element list %r is now detected; update this test "
                    "and the note in _drift_signatures to reflect the new "
                    "coverage" % (label,))

    def test_every_migrated_python_consumer_uses_the_same_object(self):
        for rel, attr in MIGRATED_CONSUMERS:
            with self.subTest(consumer=rel):
                path = os.path.join(SPS2, rel)
                d = os.path.join(SPS2, os.path.dirname(rel))
                if d not in sys.path:
                    sys.path.insert(0, d)
                name = os.path.splitext(os.path.basename(rel))[0]
                self.assertTrue(os.path.isfile(path), path)
                module = __import__(name)
                self.assertIs(getattr(module, attr), attribution.AGENTISH,
                              "%s does not consume the authoritative matcher" % rel)


class TestCrossConsumerConsistency(unittest.TestCase):
    """Every migrated consumer must return the SAME policy verdict."""

    AGENT_LIKE = ["ChatGPT", "GPT", "Claude", "Cline", "Agent", "assistant",
                   "copilot", "cursor", "codex", "gemini", "opencode",
                   "GPT-4", "gpt-4o", "model", "bot", "ai",
                   "Antigravity", "antigravity", "antigravity-cli",
                   "Antigravity CLI", "Antigravity/skills"]
    # Names the canonical policy must NOT reject.
    HUMAN = ["User", "USER", "Maryam", "Omar", "José", "Ада Лавлейс", "محمد",
             "O'Brien", "van der Berg", "Maitland", "Botany", "Aisling",
             "Aisha", "Kaitlyn", "Mai", "Coagent", "McCline", "Remodeler",
             "Gpta", "Gptson", "Jane Self", "Nora Script", "Autonomous Council"]
    # DEC-0025 admitted 'antigravity', so it belongs with agent-like values.
    OTHER = ["self", "Zzz", "unknown", ""]

    def test_antigravity_is_rejected_in_every_canonical_form(self):
        """DEC-0025: an Antigravity approver must be caught, not accepted."""
        for value in ("Antigravity", "antigravity", "ANTIGRAVITY",
                      "antigravity-cli", "Antigravity CLI", "antigravity/skills",
                      "~/.gemini/antigravity"):
            with self.subTest(value=value):
                self.assertTrue(
                    bool(attribution.AGENTISH.search(value)),
                    "%r must be rejected as an approver" % value)
                approval = {"state": "APPROVED", "decided_by": value,
                            "decided_on": "2026-10-13"}
                self.assertFalse(attribution.approval_is_user_attributable(approval))

    def test_antigravity_does_not_match_inside_a_larger_word(self):
        """\b semantics preserved: no substring matching was introduced."""
        for value in ("AntigravityHost", "antigravityx", "anti-gravity",
                      "MyAntigravity", "Antigravityian"):
            with self.subTest(value=value):
                self.assertFalse(
                    bool(attribution.AGENTISH.search(value)),
                    "%r must NOT match; adding a token must not widen to "
                    "substring matching" % value)

    def test_antigravity_creates_no_human_name_false_positive(self):
        """DEC-0025's rationale: it is a proper noun, not an English surname."""
        for value in ("Jane Self", "Nora Script", "Autonomous Council",
                      "Maryam", "Omar", "Jose", "Grace Hopper", "User"):
            with self.subTest(value=value):
                self.assertFalse(bool(attribution.AGENTISH.search(value)))

    def test_posctrl_g_fixture_is_still_rejected(self):
        """validate-p4.sh POSCTRL-G injects 'Agent (self-approved)'.

        It is rejected on the token 'Agent', not on 'self'. Removing 'self' from
        the policy therefore did NOT weaken that positive control - it is still
        non-vacuous. If this ever fails, the control has gone vacuous.
        """
        for value in ("Agent (self-approved)", "agent (self-approved)"):
            with self.subTest(value=value):
                self.assertTrue(bool(attribution.AGENTISH.search(value)))

    def test_self_referent_only_fixture_is_not_rejected_by_design(self):
        """Documents that POSCTRL-G's rejection comes from 'Agent', not 'self'.

        With the word 'Agent' removed, the same fixture is ACCEPTED. That is
        intentional: 'self' is not a policy token, and adding it would reject
        the legitimate surname 'Jane Self'. The open decision record carries the
        provenance question; this test pins the current, approved behaviour.
        """
        approval = {"state": "APPROVED", "decided_by": "Self (self-approved)",
                    "decided_on": "2026-10-13"}
        self.assertTrue(
            attribution.approval_is_user_attributable(approval),
            "'Self (self-approved)' is currently accepted by design; if this "
            "fails, 'self' became a token and the open decision record must be "
            "resolved before that change")
        self.assertFalse(bool(attribution.AGENTISH.search("Jane Self")))
        self.assertFalse(bool(attribution.AGENTISH.search("Nora Script")))
        self.assertFalse(bool(attribution.AGENTISH.search("Autonomous Council")))

    def _load(self):
        mods = {}
        for rel, attr in MIGRATED_CONSUMERS:
            d = os.path.join(SPS2, os.path.dirname(rel))
            if d not in sys.path:
                sys.path.insert(0, d)
            mods[rel] = getattr(__import__(os.path.splitext(os.path.basename(rel))[0]), attr)
        return mods

    def test_agent_like_values_are_rejected_identically_everywhere(self):
        mods = self._load()
        for value in self.AGENT_LIKE:
            expected = bool(attribution.AGENTISH.search(value))
            self.assertTrue(expected, "fixture assumption: %r should match" % value)
            for rel, rx in mods.items():
                with self.subTest(value=value, consumer=rel):
                    self.assertEqual(bool(rx.search(value)), expected)

    def test_human_names_are_not_rejected_identically_everywhere(self):
        mods = self._load()
        for value in self.HUMAN:
            expected = bool(attribution.AGENTISH.search(value))
            self.assertFalse(expected, "fixture assumption: %r should not match" % value)
            for rel, rx in mods.items():
                with self.subTest(value=value, consumer=rel):
                    self.assertEqual(bool(rx.search(value)), expected)

    def test_other_values_agree_even_where_policy_is_permissive(self):
        """self / unknown strings pass the canonical policy.

        They pass because it is not exhaustive. Consumers must still AGREE,
        which is the property SPEC-2 actually changed. This test documents the
        known coverage gap rather than asserting it is desirable.
        """
        mods = self._load()
        for value in self.OTHER:
            expected = bool(attribution.AGENTISH.search(value))
            for rel, rx in mods.items():
                with self.subTest(value=value, consumer=rel):
                    self.assertEqual(bool(rx.search(value)), expected)

    def test_predicate_agrees_with_matcher_across_the_corpus(self):
        corpus = self.AGENT_LIKE + self.HUMAN + self.OTHER
        for value in corpus:
            approval = {"state": "APPROVED", "decided_by": value,
                        "decided_on": "2026-10-13"}
            # The predicate additionally requires a non-blank decider, so a
            # blank value is rejected even though the matcher does not fire.
            expect_ok = bool(value.strip()) and not bool(attribution.AGENTISH.search(value))
            with self.subTest(value=value):
                self.assertEqual(attribution.approval_is_user_attributable(approval), expect_ok)


class TestOpenDecisionRecordIsHonest(unittest.TestCase):
    """The antigravity/autonomous questions are OPEN. Keep the record honest.

    The danger this guards is a silent fix in either direction: adding the token
    because the gap 'looked wrong', or deleting the open question because it
    'looked settled'. Both would make the repository disagree with itself.
    """

    RECORD = os.path.join(SPS2, "decisions", "OPEN-DECISION-ATTRIBUTION-TOKEN-SET.json")

    def _record(self):
        self.assertTrue(os.path.isfile(self.RECORD), self.RECORD)
        with open(self.RECORD, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def test_record_is_superseded_and_points_at_the_binding_decisions(self):
        """T1/T2 were resolved by DEC-0025..0028; this record must say so."""
        rec = self._record()
        self.assertEqual(rec["state"], "SUPERSEDED")
        self.assertEqual(rec["resolved_on"], "2026-10-15")
        self.assertIsNone(rec["resolved_by"],
                          "this record grants no approval; it never did")
        self.assertEqual(sorted(rec["superseded_by"]),
                         ["DEC-0025", "DEC-0026", "DEC-0027", "DEC-0028"])
        for q in rec["open_questions"]:
            with self.subTest(question=q["id"]):
                self.assertEqual(q["closed_by"][:3], "DEC")
                self.assertIs(q["implemented_in_this_task"], True)

    def test_superseding_decision_record_exists_and_conforms(self):
        """The replacement record must be real, not merely referenced."""
        path = os.path.join(SPS2, "decisions", "ATTRIBUTION-POLICY-DECISIONS.json")
        self.assertTrue(os.path.isfile(path), path)
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        ids = {d["decision_id"] for d in doc["decisions"]}
        self.assertEqual(ids, {"DEC-0025", "DEC-0026", "DEC-0027", "DEC-0028"})
        for d in doc["decisions"]:
            with self.subTest(decision=d["decision_id"]):
                self.assertRegex(d["decision_id"], r"^DEC-[0-9]{4}$")
                for field in ("title", "decision", "reason", "evidence",
                              "alternatives", "approval"):
                    self.assertIn(field, d)
                self.assertGreaterEqual(len(d["evidence"]), 1)
                self.assertEqual(d["approval"]["state"], "APPROVED")
                self.assertEqual(d["approval"]["decided_by"], "User")

    def test_decision_record_token_set_matches_the_live_policy(self):
        """DEC-0025 states the canonical set; it must not drift from reality."""
        path = os.path.join(SPS2, "decisions", "ATTRIBUTION-POLICY-DECISIONS.json")
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        self.assertEqual(
            set(doc["canonical_token_set"]), set(_policy_tokens()),
            "ATTRIBUTION-POLICY-DECISIONS.json canonical_token_set has drifted "
            "from attribution_policy.json tokens[]")

    def test_decision_record_basis_cites_a_user_instruction(self):
        """Provenance must be a quote, not an invented approval artifact."""
        path = os.path.join(SPS2, "decisions", "ATTRIBUTION-POLICY-DECISIONS.json")
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        for d in doc["decisions"]:
            with self.subTest(decision=d["decision_id"]):
                basis = d["approval"].get("basis", "")
                self.assertIn("User", basis)
                self.assertRegex(basis, r"quoted verbatim|in session")

    def test_every_question_is_closed_by_a_decision_id(self):
        """The record is SUPERSEDED: each question must name its decision."""
        rec = self._record()
        for q in rec["open_questions"]:
            with self.subTest(question=q["id"]):
                self.assertIs(q["implemented_in_this_task"], True)
                self.assertRegex(q["closed_by"], r"^DEC-[0-9]{4}$")
                self.assertTrue(q["resolution"].strip())
        self.assertEqual(rec["questions_settled_without_a_new_decision"], [],
                         "nothing may be self-adjudicated; removals are governed "
                         "changes per attribution_policy.json schema_note")

    def test_open_token_questions_match_the_live_token_set(self):
        """If a token is admitted, its open question must be closed first.

        Adding 'antigravity' to the policy while T1 is still OPEN would mean the
        repository contains a token no decision authorised. This fails loudly so
        the change cannot be made quietly.
        """
        rec = self._record()
        # Derive from the record's own closure flag, NOT from a prose prefix.
        still_open = {q["token"] for q in rec["open_questions"]
                      if q.get("implemented_in_this_task") is False}
        tokens = set(_policy_tokens())
        for token in sorted(still_open):
            with self.subTest(token=token):
                self.assertNotIn(
                    token, tokens,
                    "%r was admitted to the token set while its question is still "
                    "OPEN. Resolve the decision record first." % token)
                self.assertFalse(bool(attribution.AGENTISH.search(token)))

    def test_closed_admission_is_consistent_between_record_and_policy(self):
        """T1 closed as ADMITTED, so the token must really be present."""
        rec = self._record()
        admitted = {q["token"] for q in rec["open_questions"]
                    if q.get("current_policy_behaviour", "").startswith("ADMITTED")}
        self.assertIn("antigravity", admitted,
                      "the superseded record should record antigravity as admitted")
        for token in sorted(admitted):
            with self.subTest(token=token):
                self.assertIn(token, _policy_tokens())
                self.assertTrue(bool(attribution.AGENTISH.search(token)))

    def test_antigravity_is_admitted_and_documented_as_such(self):
        """DEC-0025 moved it out of excluded_tokens and into admitted_tokens."""
        with open(os.path.join(GOVERNANCE, "attribution_policy.json"),
                  "r", encoding="utf-8") as fh:
            policy = json.load(fh)
        self.assertNotIn("antigravity", policy["excluded_tokens"],
                         "antigravity was admitted; it must not remain excluded")
        entry = policy["admitted_tokens"]["antigravity"]
        self.assertIn("DEC-0025", entry)
        self.assertIn("ADMITTED", entry)
        self.assertIn("antigravity-cli", entry,
                      "the entry must record the \b matching behaviour")

    def test_check_sps2_divergence_is_marked_resolved_not_lost(self):
        """The known_divergences entry must no longer claim a live gap."""
        with open(os.path.join(GOVERNANCE, "attribution_policy.json"),
                  "r", encoding="utf-8") as fh:
            entry = json.load(fh)["known_divergences"]["check_sps2.py"]
        self.assertIn("RESOLVED BY DEC-0025", entry)
        self.assertIn("restored", entry.lower())
        self.assertIn("It did NOT gain 'ai'", entry)

    def test_each_closed_question_matches_the_live_token_set(self):
        """A closed question must agree with what the matcher actually does."""
        rec = self._record()
        for q in rec["open_questions"]:
            with self.subTest(question=q["id"]):
                token = q["token"]
                self.assertTrue(token.strip())
                admitted = token in _policy_tokens()
                self.assertEqual(
                    admitted, bool(attribution.AGENTISH.search(token)),
                    "%r: record says %s but the matcher disagrees"
                    % (token, "admitted" if admitted else "excluded"))
        advisory = rec["advisory_assessment_not_a_ratification"]
        self.assertIn("ADVISORY", advisory["$comment"].upper())
        self.assertRegex(advisory["outcome"], r"^RATIFIED")
        self.assertTrue(advisory["tokens"])


# The pre-consolidation approver-token sites, enumerated from BASELINE_REV.
HEAD_SHELL_SITES = {
    "sps2/tools/validate-p3.sh": [206],
    "sps2/tools/validate-p4.sh": [246, 459, 338, 820],
    ".sps/tools/validate-capability.sh": [52, 180, 249],
    ".sps/tools/validate-control.sh": [90],
    ".sps/tools/validate-governance.sh": [172],
}
HEAD_PYTHON_DENYLISTS = [
    "sps2/governance/attribution.py", "sps2/capability/engine.py",
    "sps2/capability/promotion_gates.py", "sps2/tools/check_sps2.py",
    "sps2/tools/check_p2.py",
]


def _head_text(rel):
    """The content of ``rel`` at the pinned BASELINE_REV, not at the moving HEAD.

    See BASELINE_REV for why this is pinned. An unresolvable revision or path
    raises rather than degrading to "": returning "" would make the callers
    compare a prose constant against empty text and report a *misleading*
    "actual: 0" discrepancy, when the real problem is that the historical
    revision is unavailable (e.g. the suite is running from an export with no
    .git, or the pinned object is unreachable).
    """
    import subprocess
    proc = subprocess.run(["git", "show", BASELINE_REV + ":" + rel],
                          capture_output=True, text=True, cwd=REPO)
    if proc.returncode != 0:
        raise AssertionError(
            "cannot resolve %s at the pinned baseline %s (git exit %d): %s"
            "The historical provenance assertions require this object to be "
            "reachable; pinning it is what keeps them valid after the "
            "consolidation is committed."
            % (rel, BASELINE_REV, proc.returncode, proc.stderr.strip()))
    return proc.stdout


class TestKnownDivergencesAreAccurate(unittest.TestCase):
    """Recomputes the pre-consolidation facts from the pinned BASELINE_REV.

    Asserting that a prose string contains a word proves nothing, which is how
    three wrong factual claims survived into the policy file. These tests
    recompute each number and compare it to what the policy actually says.

    The baseline is pinned rather than taken from HEAD so the historical facts
    stay checkable after the consolidation is committed; see BASELINE_REV.
    """

    def _policy(self):
        with open(os.path.join(GOVERNANCE, "attribution_policy.json"),
                  "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _head_site_counts(self):
        out = {}
        for token in ("self", "script", "autonomous"):
            hits = 0
            for rel, lines in HEAD_SHELL_SITES.items():
                src = _head_text(rel).splitlines()
                for ln in lines:
                    if ln - 1 < len(src):
                        blob = " ".join(src[ln - 1:ln + 2])
                        if re.search(r"\b%s\b" % token, blob):
                            hits += 1
            py = sum(1 for f in HEAD_PYTHON_DENYLISTS
                     if re.search(r"\b%s\b" % token, _head_text(f)))
            out[token] = (hits, py)
        return out

    def test_total_shell_site_count_used_in_prose_is_correct(self):
        total = sum(len(v) for v in HEAD_SHELL_SITES.values())
        self.assertEqual(total, 10, "HEAD site map itself drifted")
        et = self._policy()["excluded_tokens"]
        for token in ("self", "script", "autonomous"):
            with self.subTest(token=token):
                self.assertIn("of the %d pre-consolidation shell "
                              "approver-token sites" % total, et[token],
                              "excluded_tokens.%s states a total site count that "
                              "does not match BASELINE_REV" % token)

    def test_shell_validators_entry_names_the_sites_it_relies_on(self):
        """It cites line numbers instead of a count, so check the citations."""
        entry = self._policy()["known_divergences"]["shell validators"]
        for token in ("self", "script", "autonomous"):
            self.assertIn(token, entry)
        for site in (":206", ":246", ":459"):
            self.assertIn(site, entry)
        self.assertIn("DEC-0027", entry)
        self.assertIn("DEC-0026", entry)
        self.assertIn("untouched", entry)

    def test_stated_site_counts_per_token_match_git_head(self):
        counts = self._head_site_counts()
        et = self._policy()["excluded_tokens"]
        for token, (hits, py) in counts.items():
            with self.subTest(token=token):
                self.assertEqual(py, 0,
                                 "%r unexpectedly present in a Python denylist; "
                                 "the provenance narrative must be updated" % token)
                self.assertIn(
                    "%d of the 10 pre-consolidation shell approver-token sites" % hits,
                    et[token],
                    "excluded_tokens.%s states a site count that does not match "
                    "BASELINE_REV (actual: %d)" % (token, hits))

    def test_stated_python_denylist_count_matches_git_head(self):
        n = len(HEAD_PYTHON_DENYLISTS)
        self.assertEqual(n, 5)
        et = self._policy()["excluded_tokens"]
        for token in ("self", "script", "autonomous"):
            with self.subTest(token=token):
                self.assertIn("NONE of the %d hardcoded Python denylists" % n,
                              et[token],
                              "excluded_tokens.%s misstates how many hardcoded "
                              "Python denylists existed at BASELINE_REV" % token)

    def test_check_sps2_divergence_does_not_claim_a_token_it_already_had(self):
        """check_sps2.py already had 'ai' at BASELINE_REV; claiming 'gained' is false."""
        old = _head_text("sps2/tools/check_sps2.py")
        self.assertRegex(old, r"r'[^']*\|ai\|[^']*'",
                         "BASELINE_REV check_sps2.py no longer contains 'ai'; update the map")
        gained = {"aider", "chatgpt", "gpt", "windsurf"}
        actual = set(_policy_tokens()) - set(re.findall(r"[a-z]+", old.split("AGENT = re.compile")[1][:200]))
        self.assertTrue(gained <= actual | {"agent", "ai", "assistant", "model", "bot",
                                            "claude", "cursor", "codex", "gemini",
                                            "opencode", "cline", "copilot"})
        entry = self._policy()["known_divergences"]["check_sps2.py"]
        self.assertIn("It did NOT gain 'ai'", entry)

    def test_baseline_rev_is_pinned_to_a_fixed_revision_not_head(self):
        """The historical referent must be an immutable revision, never "HEAD".

        Reverting BASELINE_REV to "HEAD" silently reintroduces the original
        defect: the provenance assertions would once again be checked against
        whatever revision happens to be checked out, and would fail as soon as
        the consolidation itself is committed.
        """
        self.assertRegex(BASELINE_REV, r"^[0-9a-f]{40}$",
                         "BASELINE_REV must be a full 40-hex object name")
        self.assertNotIn(BASELINE_REV.upper(), ("HEAD", "HEAD~1", "MAIN", "MASTER"),
                         "BASELINE_REV must not be a moving reference")

    def test_baseline_rev_is_reachable_from_head(self):
        """A pinned revision is only useful while the object still exists.

        An unreachable pin would make the provenance assertions error out on
        every run. Checking reachability here turns that into one clear
        failure instead of several confusing ones.
        """
        import subprocess
        proc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASELINE_REV, "HEAD"],
            capture_output=True, text=True, cwd=REPO)
        self.assertEqual(
            proc.returncode, 0,
            "BASELINE_REV %s is not an ancestor of HEAD (git exit %d); the "
            "historical provenance assertions can no longer be evaluated"
            % (BASELINE_REV, proc.returncode))

    def test_baseline_rev_resolves_for_every_referenced_path(self):
        """Every path the historical constants cite must exist at the pin.

        This proves the pin really points at pre-consolidation content rather
        than at the migrated tree, and it fails loudly if the revision or any
        path becomes unresolvable.
        """
        for rel in list(HEAD_SHELL_SITES) + list(HEAD_PYTHON_DENYLISTS):
            with self.subTest(path=rel):
                self.assertTrue(_head_text(rel).strip(),
                                "no content for %s at BASELINE_REV" % rel)

    def test_baseline_rev_still_holds_the_pre_consolidation_lists(self):
        """The pinned revision must be genuinely PRE-consolidation.

        At the pin, the Python consumers still carry their own hardcoded
        denylists. If someone repoints BASELINE_REV at a post-consolidation
        revision, these literals vanish and the provenance narrative becomes
        unverifiable — so assert the historical shape is really there.
        """
        for rel in HEAD_PYTHON_DENYLISTS:
            with self.subTest(path=rel):
                self.assertRegex(
                    _head_text(rel), r"re\.compile\(",
                    "%s has no compiled matcher at BASELINE_REV; the pin no "
                    "longer points at the pre-consolidation tree" % rel)
        # check_sps2.py is the one consumer that already carried 'ai'.
        self.assertIn("|ai|", _head_text("sps2/tools/check_sps2.py"))
        entry = self._policy()["known_divergences"]["check_sps2.py"]
        self.assertNotIn("Gained 'ai'", entry)
        self.assertIn("'aider', 'chatgpt', 'gpt'", entry)

    def test_no_regression_claim_is_backed_by_the_exact_user_checks(self):
        """The 'not_a_regression' entry asserts untouched exact-'User' checks.

        If someone later removes those checks the assertion would become false,
        so this test verifies they are still present in the validators.
        """
        def _read(rel):
            with open(os.path.join(SPS2, "tools", rel),
                      encoding="utf-8") as fh:
                return fh.read()
        p3 = _read("validate-p3.sh")
        p4 = _read("validate-p4.sh")
        self.assertIn('== "User"', p3, "validate-p3.sh lost its exact-'User' check")
        self.assertIn("!= 'User'", p4, "validate-p4.sh lost its exact-'User' check")


class TestMalformedPolicyFailsVisibly(unittest.TestCase):
    """Regression: no malformed policy may yield empty stdout.

    The shell harness (validate-sps2.sh:36-43, validate-p2.sh:36-42) invokes the
    checkers with `2>/dev/null` and its assert_clean helper treats an EMPTY
    stdout as a PASS. Any policy input that makes the checker die with a
    traceback on stderr therefore terminates the process with empty stdout and
    is silently scored as clean — the exact false-PASS class the import guard in
    check_sps2.py exists to prevent.

    A policy that is valid JSON but not an object (a list, string, number,
    boolean or null) used to do exactly that: `policy.get("tokens")` raised
    AttributeError, which the guard's except tuple did not catch. These tests
    pin the contract: every malformed input must produce a NON-EMPTY stdout
    line, exit 0, and no traceback.
    """

    # Valid JSON, wrong top-level type. Each of these previously escaped as an
    # uncaught AttributeError at attribution.py's `policy.get("tokens")`.
    NON_OBJECT_DOCUMENTS = ["[]", '"a string"', "null", "42", "true", '["tokens"]']

    # Malformed or well-formed-but-unusable JSON objects.
    MALFORMED_DOCUMENTS = [
        "{ not json",
        "",
        "{}",
        '{"tokens": null}',
        '{"tokens": []}',
        '{"tokens": [1, 2]}',
        '{"tokens": "agent"}',
        '{"other": 1}',
    ]

    def _load_with(self, text, tmpdir):
        """Call load_agent_tokens against a policy file holding `text`."""
        path = os.path.join(tmpdir, "attribution_policy.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return attribution.load_agent_tokens(path=path)

    def test_non_object_policy_raises_value_error_not_attribute_error(self):
        """The failure type is part of the contract the guards rely on.

        check_sps2.py and check_p2.py catch Exception, but the documented and
        narrowest surface is ValueError; asserting it here keeps the failure
        typed and prevents a future refactor from reintroducing a bare
        AttributeError that reads as a programming bug rather than bad input.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            for text in self.NON_OBJECT_DOCUMENTS:
                with self.subTest(document=text):
                    with self.assertRaises(ValueError) as ctx:
                        self._load_with(text, tmpdir)
                    self.assertNotIsInstance(ctx.exception, AttributeError)
                    self.assertIn("JSON object", str(ctx.exception))

    def test_malformed_policy_always_raises(self):
        """A malformed policy must never silently degrade to an empty token set."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            for text in self.MALFORMED_DOCUMENTS:
                with self.subTest(document=text):
                    with self.assertRaises((ValueError, IOError, OSError)):
                        self._load_with(text, tmpdir)

    def _isolated_tree(self, tmpdir, policy_text):
        """A throwaway copy of the files the checkers need, plus `policy_text`.

        The checkers resolve POLICY_PATH from __file__, so exercising a broken
        policy requires an actual file beside a copy of attribution.py. This
        copies those files into `tmpdir` rather than mutating the real
        sps2/governance/attribution_policy.json: a crash mid-test must never be
        able to leave the repository's authoritative policy corrupted.
        """
        gov = os.path.join(tmpdir, "sps2", "governance")
        tools = os.path.join(tmpdir, "sps2", "tools")
        os.makedirs(gov)
        os.makedirs(tools)
        for rel, dest in (
            (os.path.join("governance", "attribution.py"), gov),
            (os.path.join("tools", "check_sps2.py"), tools),
            (os.path.join("tools", "check_p2.py"), tools),
        ):
            src = os.path.join(SPS2, rel)
            with open(src, "r", encoding="utf-8") as fh:
                body = fh.read()
            with open(os.path.join(dest, os.path.basename(src)), "w",
                      encoding="utf-8") as fh:
                fh.write(body)
        with open(os.path.join(gov, "attribution_policy.json"), "w",
                  encoding="utf-8") as fh:
            fh.write(policy_text)
        return tmpdir

    def _run_checker(self, tree, rel, kind, payload):
        import subprocess
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as tf:
            tf.write(payload)
            tmp_name = tf.name
        try:
            return subprocess.run(
                [sys.executable, os.path.join(tree, rel), kind, tmp_name],
                capture_output=True, text=True, cwd=tree)
        finally:
            os.unlink(tmp_name)

    def test_guarded_consumers_never_emit_empty_stdout_on_bad_policy(self):
        """End-to-end: run the real checkers against every malformed policy.

        This is the assertion that actually protects the shell harness. It runs
        each checker as a SUBPROCESS, exactly as validate-sps2.sh /
        validate-p2.sh do, with stderr discarded, and requires non-empty stdout.
        A regression that reintroduces a traceback-plus-empty-stdout failure
        fails here.

        Runs against an isolated copy of the tree, so the authoritative policy
        file is never touched.
        """
        import tempfile
        checkers = [
            ("sps2/tools/check_sps2.py", "decision", '{"decisions": []}'),
            ("sps2/tools/check_p2.py", "sources", '{"records": []}'),
        ]
        for text in self.NON_OBJECT_DOCUMENTS + self.MALFORMED_DOCUMENTS:
            with tempfile.TemporaryDirectory() as tmpdir:
                tree = self._isolated_tree(tmpdir, text)
                for rel, kind, payload in checkers:
                    with self.subTest(document=text, checker=rel):
                        proc = self._run_checker(tree, rel, kind, payload)
                        # stderr is discarded by the shell harness; only stdout
                        # emptiness decides PASS, so stdout must never be empty.
                        self.assertNotEqual(
                            proc.stdout.strip(), "",
                            "%s produced EMPTY stdout for policy %r; the shell "
                            "harness scores empty stdout as PASS"
                            % (rel, text))
                        self.assertIn("ERR", proc.stdout,
                                      "%s did not report a visible error for "
                                      "policy %r" % (rel, text))
                        self.assertEqual(proc.returncode, 0,
                                         "%s changed its documented exit code "
                                         "(always 0; inspect stdout for ERR "
                                         "lines) for policy %r"
                                         % (rel, text))
                        self.assertNotIn("Traceback", proc.stderr,
                                         "%s crashed with a traceback for "
                                         "policy %r" % (rel, text))

    def test_absent_policy_is_isolated_and_reported(self):
        """A missing policy file is a visible ERR, verified in an isolated tree."""
        import tempfile
        for rel, kind, payload in (
                ("sps2/tools/check_sps2.py", "decision", '{"decisions": []}'),
                ("sps2/tools/check_p2.py", "sources", '{"records": []}')):
            with self.subTest(checker=rel):
                with tempfile.TemporaryDirectory() as tmpdir:
                    tree = self._isolated_tree(tmpdir, "{}")
                    os.unlink(os.path.join(tree, "sps2", "governance",
                                           "attribution_policy.json"))
                    proc = self._run_checker(tree, rel, kind, payload)
                    self.assertIn("ERR", proc.stdout)
                    self.assertEqual(proc.returncode, 0)

    def test_valid_policy_still_produces_clean_empty_stdout(self):
        """The fix must not make a HEALTHY run look like a failure.

        Guards against over-correction: with a real policy in place a clean
        input must still give empty stdout and exit 0.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(POLICY_PATH, "r", encoding="utf-8") as fh:
                good = fh.read()
            tree = self._isolated_tree(tmpdir, good)
            proc = self._run_checker(tree, "sps2/tools/check_sps2.py",
                                     "decision", '{"decisions": []}')
        self.assertEqual(proc.stdout.strip(), "",
                         "a clean run must stay clean: %r" % proc.stdout)
        self.assertEqual(proc.returncode, 0)

    def test_checkers_share_one_canonical_predicate_under_a_good_policy(self):
        """Both guarded checkers must expose the SAME matcher object.

        Guards the consolidation invariant from the subprocess boundary: a
        regression that gives either checker its own token list is caught here.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(POLICY_PATH, "r", encoding="utf-8") as fh:
                good = fh.read()
            tree = self._isolated_tree(tmpdir, good)
            code = (
                "import sys, os\n"
                "sys.path.insert(0, os.path.join(%r, 'sps2', 'governance'))\n"
                "sys.path.insert(0, os.path.join(%r, 'sps2', 'tools'))\n"
                "import attribution, check_p2, check_sps2\n"
                "assert check_p2.AGENT is attribution.AGENTISH, 'check_p2'\n"
                "assert check_sps2.AGENT is attribution.AGENTISH, 'check_sps2'\n"
                "print('OK')\n" % (tree, tree))
            import subprocess
            proc = subprocess.run([sys.executable, "-c", code],
                                  capture_output=True, text=True, cwd=tree)
        self.assertEqual(proc.stdout.strip(), "OK",
                         "predicate identity broken: %s%s"
                         % (proc.stdout, proc.stderr))


class TestCheckerDocumentShapesFailVisibly(unittest.TestCase):
    """The same empty-stdout-as-PASS class, reached through the DATA document.

    TestMalformedPolicyFailsVisibly covers a broken *policy*. These cover a
    broken *input document* while the policy is healthy — a separate path that
    an import-time guard does not protect. validate-p2.sh scores an empty
    stdout as a clean PASS, so a checker that tracebacks with nothing on stdout
    reports success on input it never validated.
    """

    NON_OBJECT_DOCUMENTS = ["null", "[]", "[1,2]", "42", "3.14", "true",
                            '"a string"']

    def _run(self, tree, rel, kind, payload):
        import subprocess
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as tf:
            tf.write(payload)
            tmp_name = tf.name
        try:
            return subprocess.run(
                [sys.executable, os.path.join(tree, rel), kind, tmp_name],
                capture_output=True, text=True, cwd=tree)
        finally:
            os.unlink(tmp_name)

    def _isolated_tree(self, tmpdir):
        gov = os.path.join(tmpdir, "sps2", "governance")
        tools = os.path.join(tmpdir, "sps2", "tools")
        os.makedirs(gov)
        os.makedirs(tools)
        for rel, dest in (("governance/attribution.py", gov),
                          ("tools/check_p2.py", tools),
                          ("tools/check_sps2.py", tools),
                          ("governance/attribution_policy.json", gov)):
            src = os.path.join(SPS2, rel)
            with open(src, "r", encoding="utf-8") as fh:
                body = fh.read()
            with open(os.path.join(dest, os.path.basename(src)), "w",
                      encoding="utf-8") as fh:
                fh.write(body)
        return tmpdir

    def test_non_object_input_document_is_reported_not_crashed(self):
        """A healthy policy plus a non-object DOCUMENT must still emit ERR.

        check_p2.py previously called .get() on the parsed document, so a
        top-level list/number/null raised AttributeError, escaped main(), and
        left stdout empty — a silent PASS under validate-p2.sh.
        """
        import tempfile
        for text in self.NON_OBJECT_DOCUMENTS:
            with self.subTest(document=text):
                with tempfile.TemporaryDirectory() as tmpdir:
                    tree = self._isolated_tree(tmpdir)
                    proc = self._run(tree, "sps2/tools/check_p2.py",
                                     "sources", text)
                self.assertNotEqual(
                    proc.stdout.strip(), "",
                    "check_p2.py produced EMPTY stdout for document %r; the "
                    "harness scores empty stdout as PASS" % text)
                self.assertIn("ERR", proc.stdout)
                self.assertEqual(proc.returncode, 0)
                self.assertNotIn("Traceback", proc.stderr)

    def test_check_sps2_reports_non_object_document_too(self):
        """The same shape through check_sps2.py, which already guarded it.

        Pinned so the two checkers cannot drift apart again: the fix that made
        check_sps2.py safe was never applied to check_p2.py.
        """
        import tempfile
        for text in self.NON_OBJECT_DOCUMENTS:
            with self.subTest(document=text):
                with tempfile.TemporaryDirectory() as tmpdir:
                    tree = self._isolated_tree(tmpdir)
                    proc = self._run(tree, "sps2/tools/check_sps2.py",
                                     "decision", text)
                self.assertIn("ERR", proc.stdout)
                self.assertEqual(proc.returncode, 0)
                self.assertNotIn("Traceback", proc.stderr)

    def test_healthy_document_under_a_healthy_policy_stays_clean(self):
        """Positive control: the guards must not fire on a valid document."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tree = self._isolated_tree(tmpdir)
            proc = self._run(tree, "sps2/tools/check_p2.py", "sources",
                             '{"records": []}')
        self.assertEqual(proc.stdout.strip(), "",
                         "a clean document must stay clean: %r" % proc.stdout)
        self.assertEqual(proc.returncode, 0)


class TestP3RecordsModeActuallyChecks(unittest.TestCase):
    """check_p3.py's `records` mode dispatched on the wrong argv slot.

    It passed argv[3] (the path) as the KIND, so no branch in check_records
    matched, no check ran, and stdout was always empty. validate-p3.sh:103
    scores empty stdout as PASS, so every P3 record file was validated
    vacuously. The mode must select the kind from argv[2].
    """

    def _run_records(self, kind, payload):
        import subprocess
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as tf:
            tf.write(payload)
            tmp_name = tf.name
        try:
            return subprocess.run(
                [sys.executable, os.path.join(SPS2, "tools", "check_p3.py"),
                 "records", kind, tmp_name],
                capture_output=True, text=True, cwd=REPO)
        finally:
            os.unlink(tmp_name)

    def test_a_corrupt_requirements_record_is_reported(self):
        """A record with a bogus id and a missing criterion must be caught."""
        payload = ('{"requirements": [{"requirement_id": "BOGUS",'
                   ' "acceptance_criteria": [],'
                   ' "verification": {"state": "VERIFIED"},'
                   ' "approval": {"state": "APPROVED", "decided_by": "Claude"}}]}')
        proc = self._run_records("requirements", payload)
        self.assertNotEqual(
            proc.stdout.strip(), "",
            "check_p3.py records produced EMPTY stdout for a corrupt record; "
            "validate-p3.sh:103 scores that as PASS")
        self.assertIn("ERR", proc.stdout)

    def test_a_corrupt_decision_record_is_reported(self):
        """The 'missing reason or evidence' check must be reachable via CLI."""
        payload = '{"decisions": [{"decision_id": "DEC-0001", "state": "APPROVED"}]}'
        proc = self._run_records("decisions", payload)
        self.assertIn("missing reason or evidence", proc.stdout)

    def test_the_kind_argument_selects_the_branch(self):
        """Different kinds must not behave identically.

        Under the defect every kind returned empty stdout, because the kind
        never matched. A corrupt document of one kind must produce output while
        a well-formed document of another produces none.
        """
        corrupt = '{"requirements": [{"requirement_id": "NOPE"}]}'
        good = '{"decisions": []}'
        self.assertIn("ERR", self._run_records("requirements", corrupt).stdout)
        self.assertEqual(
            self._run_records("decisions", good).stdout.strip(), "",
            "a well-formed, empty decision set should report nothing")


if __name__ == "__main__":
    unittest.main()