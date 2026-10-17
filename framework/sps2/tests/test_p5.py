#!/usr/bin/env python3
"""SPS 2.0 P5 unit tests.

Standard library unittest only. Every test is non-vacuous: each asserts a
behaviour and several assert that a violation is actually detected.

Covers positive, negative, boundary, malformed-input, approval-attribution,
project-local/global-boundary, provenance and security cases.
"""
import copy
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(REPO, "framework", "sps2", "core"))
sys.path.insert(0, os.path.join(REPO, "framework", "sps2", "governance"))

import adapter_registry as A        # noqa: E402
import attribution as G             # noqa: E402
import registry_api as R            # noqa: E402
import selection as S              # noqa: E402

# The governance layer supplies the stricter approval predicate so the core
# never needs to know what an agent name is.
APPROVER_OK = G.approval_is_user_attributable

REQUIREMENT = {"required_capabilities": [], "domains": ["governance"]}
GOOD_ADAPTER = {
    "agent_id": "example", "maturity": "DECLARED", "writes_global_state": False,
    "capabilities": {"shell": True}, "supports": ["markdown"],
    "fallbacks": {"mcp": "record as unavailable"}, "maintainer": "sps2-core",
}


class TestRegistryAccess(unittest.TestCase):
    """Positive and negative cases for the registry read path."""

    def test_positive_loads_real_registry(self):
        reg = R.load_registry()
        self.assertEqual(len(R.capabilities(reg)), 5)
        self.assertEqual(R.counts(reg)["promoted"], 4)

    def test_positive_by_id_finds_record(self):
        self.assertIsNotNone(R.by_id("CAP-P03-001"))
        self.assertEqual(R.by_id("CAP-P03-001")["name"], "promotion-gate")

    def test_negative_by_id_does_not_fabricate(self):
        self.assertIsNone(R.by_id("CAP-NOPE-999"))

    def test_malformed_registry_raises(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as fh:
            fh.write("{not json")
            p = fh.name
        try:
            with self.assertRaises(R.RegistryError):
                R.load_registry(p)
        finally:
            os.unlink(p)

    def test_malformed_shape_raises(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as fh:
            json.dump({"capabilities": "not-a-list"}, fh)
            p = fh.name
        try:
            with self.assertRaises(R.RegistryError):
                R.capabilities(R.load_registry(p))
        finally:
            os.unlink(p)

    def test_boundary_empty_registry(self):
        self.assertEqual(R.capabilities({"capabilities": []}), [])


class TestTraceChain(unittest.TestCase):
    """Every promoted capability must remain fully traceable."""

    def setUp(self):
        self.reg = R.load_registry()

    def test_positive_promoted_capability_trace_complete(self):
        for c in R.promoted(self.reg):
            checks, missing = R.trace(c, APPROVER_OK)
            self.assertEqual(missing, [],
                             "%s trace incomplete: %s"
                             % (c["capability_id"], missing))
            self.assertTrue(all(checks.values()))

    def test_trace_chain_covers_all_ten_links(self):
        _checks, missing = R.trace(R.by_id("CAP-P03-001", self.reg),
                                   APPROVER_OK)
        self.assertEqual(len(R.TRACE_CHAIN), 10)
        self.assertEqual(missing, [])

    def test_negative_missing_selection_breaks_trace(self):
        cap = copy.deepcopy(R.by_id("CAP-P03-001", self.reg))
        cap["selection"] = {}
        _checks, missing = R.trace(cap, APPROVER_OK)
        self.assertIn("selection", missing)

    def test_negative_missing_licence_evidence_breaks_trace(self):
        cap = copy.deepcopy(R.by_id("CAP-P03-001", self.reg))
        cap["licence_evidence"] = "  "
        _checks, missing = R.trace(cap, APPROVER_OK)
        self.assertIn("licence", missing)

    def test_negative_agent_attributed_approval_breaks_trace(self):
        cap = copy.deepcopy(R.by_id("CAP-P03-001", self.reg))
        cap["approval"] = {"state": "APPROVED", "decided_by": "Agent",
                           "decided_on": "2026-10-04"}
        _checks, missing = R.trace(cap, APPROVER_OK)
        self.assertIn("approval", missing)

    def test_negative_undated_approval_breaks_trace(self):
        cap = copy.deepcopy(R.by_id("CAP-P03-001", self.reg))
        cap["approval"] = {"state": "APPROVED", "decided_by": "User"}
        _checks, missing = R.trace(cap, APPROVER_OK)
        self.assertIn("approval", missing)

    def test_governance_predicate_is_stricter_than_core_default(self):
        """The injected governance check must catch what the core default misses."""
        agent = {"state": "APPROVED", "decided_by": "Agent",
                 "decided_on": "2026-10-04"}
        self.assertFalse(APPROVER_OK(agent))
        # The core default cannot tell an agent from a person; governance can.
        self.assertTrue(R.approval_is_user_attributable(agent))
        self.assertFalse(R.trace({"capability_id": "X", "name": "x",
                                  "approval": agent}, APPROVER_OK)[1] == [])


class TestRuntimeClaims(unittest.TestCase):
    """A capability may never silently claim a runtime state."""

    def test_positive_no_runtime_claims(self):
        for c in R.load_registry()["capabilities"]:
            self.assertFalse(R.claims_runtime(c),
                             "%s claims a runtime state" % c["capability_id"])

    def test_negative_active_is_detected(self):
        cap = copy.deepcopy(R.by_id("CAP-P03-001"))
        cap["lifecycle_state"] = "ACTIVE"
        self.assertTrue(R.claims_runtime(cap))

    def test_negative_installed_is_detected(self):
        cap = copy.deepcopy(R.by_id("CAP-P03-001"))
        cap["lifecycle_state"] = "INSTALLED"
        self.assertTrue(R.claims_runtime(cap))


class TestSelection(unittest.TestCase):
    """Selection is deterministic, project-local and promotion-respecting."""

    def setUp(self):
        self.reg = R.load_registry()

    def test_positive_only_promoted_are_eligible(self):
        eligible = {c["capability_id"] for c in S.eligible(self.reg)}
        self.assertEqual(eligible, {"CAP-P03-001", "CAP-P03-002",
                                    "CAP-P03-003", "CAP-P03-004"})

    def test_negative_deferred_capability_never_selectable(self):
        ranks = S.select(REQUIREMENT, self.reg)
        self.assertNotIn("CAP-P03-005", [r["capability_id"] for r in ranks])

    def test_negative_005_is_excluded_with_reasons(self):
        rec = S.selection_record("SELECTION-TEST", REQUIREMENT, self.reg)
        excl = {e["capability_id"]: e for e in rec["excluded_from_selection"]}
        self.assertIn("CAP-P03-005", excl)
        self.assertEqual(excl["CAP-P03-005"]["blocking_gates"],
                         ["F", "H", "K"])

    def test_determinism_same_fingerprint_repeatedly(self):
        f = {S.fingerprint(S.select(REQUIREMENT, self.reg)) for _ in range(8)}
        self.assertEqual(len(f), 1, "selection is not deterministic")

    def test_determinism_fingerprint_changes_with_pool(self):
        reg = copy.deepcopy(self.reg)
        reg["capabilities"] = [c for c in reg["capabilities"]
                               if c["capability_id"] != "CAP-P03-003"]
        self.assertNotEqual(S.fingerprint(S.select(REQUIREMENT, reg)),
                            S.fingerprint(S.select(REQUIREMENT, self.reg)))

    def test_selection_record_is_project_local(self):
        rec = S.selection_record("SELECTION-TEST", REQUIREMENT, self.reg)
        self.assertEqual(rec["scope"], "PROJECT_LOCAL")
        self.assertTrue(rec["agent_neutral"])

    def test_selection_is_not_self_approved(self):
        rec = S.selection_record("SELECTION-TEST", REQUIREMENT, self.reg)
        self.assertEqual(rec["approval"]["state"], "PENDING_USER_APPROVAL")

    def test_every_rank_is_explained(self):
        rec = S.selection_record("SELECTION-TEST", REQUIREMENT, self.reg)
        for r in rec["ranking"]:
            self.assertTrue(r["selection_reason"].strip())
            self.assertTrue(r["breakdown"])
            self.assertTrue(r["contributing_weights"])

    def test_popularity_is_only_a_tiebreaker(self):
        rec = S.selection_record("SELECTION-TEST", REQUIREMENT, self.reg)
        self.assertEqual(rec["popularity_role"], "TIE_BREAKER_ONLY")

    def test_negative_high_popularity_cannot_outrank_a_higher_score(self):
        """Popularity must never outrank an evidence-weighted score difference.

        The four governance capabilities tie on score, so a popularity spike
        legitimately breaks the tie. The real invariant is that popularity can
        never move a candidate ahead of one that scores strictly higher.
        """
        reg = copy.deepcopy(self.reg)
        # Give CAP-P03-004 a strictly higher evidence score by giving it a
        # domain the requirement asks for, then spike a rival's popularity.
        for c in reg["capabilities"]:
            if c["capability_id"] == "CAP-P03-004":
                c["domain"] = "GOVERNANCE-PRIORITY"
        for c in reg["capabilities"]:
            if c["capability_id"] == "CAP-P03-001":
                c["domain"] = "GOVERNANCE"
                c["popularity"] = {"stars": 10 ** 9}
        ranked = S.select({"required_capabilities": [],
                           "domains": ["GOVERNANCE-PRIORITY"]}, reg)
        order = [r["capability_id"] for r in ranked]
        self.assertEqual(order[0], "CAP-P03-004")
        top, second = ranked[0], ranked[1]
        self.assertGreater(top["score"], second["score"],
                           "fixture must produce a strict score difference")
        self.assertTrue(top["tie_breaker_used"] is False)
        # Even with a 1e9-star rival, the higher scorer stays first.
        self.assertNotEqual(order.index("CAP-P03-001"), 0)

    def test_ranks_are_contiguous_from_one(self):
        rec = S.selection_record("SELECTION-TEST", REQUIREMENT, self.reg)
        ranks = sorted(r["rank"] for r in rec["ranking"])
        self.assertEqual(ranks, list(range(1, len(ranks) + 1)))

    def test_scores_descend(self):
        rec = S.selection_record("SELECTION-TEST", REQUIREMENT, self.reg)
        scores = [r["score"] for r in rec["ranking"]]
        self.assertEqual(scores, sorted(scores, reverse=True))


class TestAdapterBoundary(unittest.TestCase):
    """The core must not depend on adapters; adapters must not go global."""

    def test_positive_real_registry_is_compliant(self):
        errs, summary = A.validate_registry()
        self.assertEqual(errs, [])
        self.assertTrue(summary["all_write_project_local"])

    def test_positive_core_is_adapter_free(self):
        self.assertEqual(A.core_is_adapter_free(), [])

    def test_positive_good_adapter_has_no_errors(self):
        self.assertEqual(A.validate_adapter(GOOD_ADAPTER), [])

    def test_negative_adapter_writing_global_state(self):
        bad = dict(GOOD_ADAPTER, writes_global_state=True)
        errs = A.validate_adapter(bad)
        self.assertTrue(any("ADAPTER_WRITES_GLOBAL_STATE" in e for e in errs))

    def test_negative_adapter_missing_fields(self):
        errs = A.validate_adapter({"agent_id": "x"})
        self.assertTrue(any("MISSING_FIELD" in e for e in errs))

    def test_negative_invalid_maturity(self):
        errs = A.validate_adapter(dict(GOOD_ADAPTER, maturity="PRODUCTION"))
        self.assertTrue(any("INVALID_MATURITY" in e for e in errs))

    def test_negative_non_read_only_detection(self):
        bad = dict(GOOD_ADAPTER, detection={"read_only": False})
        errs = A.validate_adapter(bad)
        self.assertTrue(any("ADAPTER_DETECTION_NOT_READ_ONLY" in e
                            for e in errs))

    def test_negative_duplicate_adapter_id(self):
        reg = {"adapters": [GOOD_ADAPTER, dict(GOOD_ADAPTER)]}
        errs, _ = A.validate_registry(reg)
        self.assertTrue(any("DUPLICATE_ADAPTER_ID" in e for e in errs))

    def _assert_malformed_is_reported(self, bad, expect):
        """A malformed entry must be reported, never fatal.

        `expect` identifies the contract violation. Each shape is checked alone
        AND beside a valid adapter, because that is where the summary callers
        render their messages from used to raise instead of returning.
        """
        for adapters in ([bad], [GOOD_ADAPTER, bad]):
            try:
                errs, _summary = A.validate_registry({"adapters": adapters})
            except Exception as exc:                    # a crash is the defect
                self.fail("validate_registry raised %s: %s"
                          % (type(exc).__name__, exc))
            self.assertTrue(any(expect in e for e in errs),
                            "expected %r in %r" % (expect, errs))

    def test_negative_missing_agent_id_at_real_maturity(self):
        self._assert_malformed_is_reported({"maturity": "EXPERIMENTAL"},
                                           "MISSING_FIELD: agent_id")

    def test_negative_null_agent_id(self):
        self._assert_malformed_is_reported(dict(GOOD_ADAPTER, agent_id=None),
                                           "INVALID_AGENT_ID")

    def test_negative_non_string_agent_id(self):
        self._assert_malformed_is_reported(dict(GOOD_ADAPTER, agent_id=42),
                                           "INVALID_AGENT_ID")

    def test_negative_unhashable_agent_id(self):
        self._assert_malformed_is_reported(dict(GOOD_ADAPTER, agent_id=["x"]),
                                           "INVALID_AGENT_ID")

    def test_negative_entry_is_not_an_object(self):
        for bad in ("opencode", 7, None):
            self._assert_malformed_is_reported(bad, "ADAPTER_NOT_AN_OBJECT")

    def test_negative_missing_or_non_string_maturity(self):
        for bad in (None, 7):
            self._assert_malformed_is_reported(
                dict(GOOD_ADAPTER, maturity=bad), "INVALID_MATURITY")

    def test_negative_detection_not_an_object(self):
        self._assert_malformed_is_reported(
            dict(GOOD_ADAPTER, detection="AGENTS.md"),
            "ADAPTER_DETECTION_NOT_AN_OBJECT")

    def test_malformed_entry_leaves_the_summary_renderable(self):
        """The summary callers build messages from stays sorted and string-only."""
        reg = {"adapters": [GOOD_ADAPTER, {"maturity": "EXPERIMENTAL"},
                            {"agent_id": None, "maturity": "EXPERIMENTAL"}]}
        _errs, summary = A.validate_registry(reg)
        self.assertEqual(summary["ids"], [GOOD_ADAPTER["agent_id"]])
        self.assertEqual(summary["maturities"], ["DECLARED", "EXPERIMENTAL"])

    def test_boundary_empty_adapter_registry(self):
        errs, summary = A.validate_registry({"adapters": []})
        self.assertEqual(errs, [])
        self.assertEqual(summary["adapters"], 0)


class TestAgentNeutrality(unittest.TestCase):
    """The core must not name a specific coding agent.

    The intended adapter surface (framework/sps2/core/adapters/) is the single
    sanctioned location for vendor-named adapters, consistent with
    validate-sps2.sh section 8 and core_is_adapter_free(). Everything else
    under framework/sps2/core/ must remain neutral (D-P3-G.2).
    """

    AGENTS = ("cline", "claude", "codex", "cursor", "copilot", "windsurf",
              "aider", "gemini", "opencode", "gpt")

    def _core_vendor_hits(self):
        core = os.path.join(REPO, "framework", "sps2", "core")
        hits = []
        for root, _dirs, files in os.walk(core):
            if "adapters" in root:
                continue
            for f in files:
                if not f.endswith((".py", ".json")):
                    continue
                with open(os.path.join(root, f)) as fh:
                    low = fh.read().lower()
                for a in self.AGENTS:
                    if a in low:
                        hits.append("%s references agent %r" % (f, a))
        return hits

    def test_positive_core_sources_name_no_agent_outside_adapters(self):
        self.assertEqual(self._core_vendor_hits(), [])

    def test_negative_unintended_vendor_reference_is_detected(self):
        probe = os.path.join(REPO, "framework", "sps2", "core", "_probe_vendor_tmp.json")
        with open(probe, "w") as fh:
            fh.write('{"note": "claude cursor"}\n')
        try:
            hits = self._core_vendor_hits()
            self.assertTrue(any("_probe_vendor_tmp" in h for h in hits))
        finally:
            os.unlink(probe)

    def test_positive_core_imports_stdlib_only(self):
        core = os.path.join(REPO, "framework", "sps2", "core")
        allowed = {"json", "os", "sys", "re", "hashlib", "argparse",
                   "importlib", "registry_api", "selection",
                   "adapter_registry", "__future__"}
        for f in os.listdir(core):
            if not f.endswith(".py"):
                continue
            with open(os.path.join(core, f)) as fh:
                for line in fh:
                    s = line.strip()
                    if s.startswith("import "):
                        mod = s.split()[1].split(".")[0]
                        self.assertIn(mod, allowed,
                                      "%s imports %s" % (f, mod))


if __name__ == "__main__":
    unittest.main(verbosity=2)
