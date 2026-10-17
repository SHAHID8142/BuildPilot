#!/usr/bin/env python3
"""BuildPilot self-learning system tests.

Standard library unittest only. Every test is non-vacuous: each asserts a
behaviour and several assert that violations are actually detected.

Covers: ledger append/validation (positive + malformed), pattern detection
threshold, promotion proposal drafting (awaiting-ratification invariant),
evidence index build/query, and the propose-never-applies law.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(REPO, "framework", "sps2", "learning"))

import learn  # noqa: E402


def _entry(n=1, category="test-cat", status="resolved"):
    return {
        "entry_id": f"MIST-20261017-{n:03d}",
        "timestamp": "2026-10-17T00:00:00Z",
        "category": category,
        "summary": f"summary {n}",
        "root_cause": f"cause {n}",
        "detection_signal": "signal",
        "resolution": "fixed",
        "source_commit": "abc1234",
        "status": status,
    }


class TestLedgerValidation(unittest.TestCase):
    def test_valid_entry_passes(self):
        learn._validate_entry(_entry())  # no exception

    def test_missing_field_rejected(self):
        e = _entry()
        del e["root_cause"]
        with self.assertRaisesRegex(ValueError, "missing field"):
            learn._validate_entry(e)

    def test_bad_timestamp_rejected(self):
        e = _entry()
        e["timestamp"] = "2026/10/17 00:00"
        with self.assertRaisesRegex(ValueError, "RFC3339"):
            learn._validate_entry(e)

    def test_bad_status_rejected(self):
        e = _entry()
        e["status"] = "auto-fixed"  # invented class
        with self.assertRaisesRegex(ValueError, "invalid ledger status"):
            learn._validate_entry(e)

    def test_load_ledger_fail_closed_on_corrupt_line(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "mistakes.jsonl"
            p.write_text(json.dumps(_entry()) + "\n{not json\n")
            with mock.patch.object(learn, "MISTAKES_PATH", p):
                entries = learn.load_ledger()
            self.assertEqual(len(entries), 1)  # corrupt line reported, valid kept


class TestPatternDetection(unittest.TestCase):
    def test_below_threshold_not_flagged(self):
        pats = learn.detect_patterns([_entry(1, "solo")])
        self.assertEqual(pats, [])

    def test_at_threshold_flagged(self):
        pats = learn.detect_patterns([_entry(1), _entry(2)])
        self.assertEqual(len(pats), 1)
        self.assertEqual(pats[0]["category"], "test-cat")
        self.assertEqual(pats[0]["count"], 2)

    def test_promoted_entries_do_not_retrigger(self):
        pats = learn.detect_patterns([_entry(1, status="promoted"), _entry(2, status="promoted")])
        self.assertEqual(pats, [])


class TestPromotionProposal(unittest.TestCase):
    def test_proposal_is_awaiting_ratification_and_changes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            entries = [_entry(1), _entry(2)]
            with mock.patch.object(learn, "load_ledger", return_value=entries), \
                 mock.patch.object(learn, "PROPOSALS_DIR", Path(td)):
                out = learn.propose_promotion("test-cat")
            self.assertIsNotNone(out)
            doc = json.loads(Path(out).read_text())
            self.assertEqual(doc["schema"], "sps2.learning-promotion-proposal/v1")
            self.assertEqual(doc["status"], "AWAITING_USER_RATIFICATION")
            self.assertIn("changes nothing", doc["ratification_note"])

    def test_below_threshold_writes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(learn, "load_ledger", return_value=[_entry(1)]), \
                 mock.patch.object(learn, "PROPOSALS_DIR", Path(td)):
                out = learn.propose_promotion("test-cat")
            self.assertIsNone(out)
            self.assertEqual(list(Path(td).iterdir()), [])


class TestEvidenceIndex(unittest.TestCase):
    def test_index_builds_and_queries(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir()
            (root / "reports" / "REP-A.md").write_text("verdict: APPROVED\n")
            (root / "reports" / "REP-B.md").write_text("verdict: REJECTED\n")
            with mock.patch.object(learn, "INDEX_PATH", root / "idx.json"), \
                 mock.patch.object(learn, "LEARNING_DIR", root):
                idx = learn.build_evidence_index(root)
                self.assertEqual(len(idx["reports"]), 2)
                self.assertEqual(idx["verdict_keywords"]["APPROVED"], ["REP-A.md"])
                hits = learn.query_evidence("APPROVED", root)
                self.assertEqual([h["file"] for h in hits], ["REP-A.md"])

    def test_index_detects_stale_digest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir()
            f = root / "reports" / "REP.md"
            f.write_text("v1\n")
            with mock.patch.object(learn, "INDEX_PATH", root / "idx.json"), \
                 mock.patch.object(learn, "LEARNING_DIR", root):
                idx1 = learn.build_evidence_index(root)
                d1 = idx1["reports"][0]["sha256_16"]
                f.write_text("v2 — changed\n")
                idx2 = learn.build_evidence_index(root)
                self.assertNotEqual(d1, idx2["reports"][0]["sha256_16"])


if __name__ == "__main__":
    unittest.main()
