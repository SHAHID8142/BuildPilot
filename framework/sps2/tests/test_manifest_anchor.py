"""Trust-anchor contract tests for the exception-manifest hash pins.

The legacy-exception and import-exception manifests are each verified by a
module that pins the manifest's canonical SHA-256 as a constant INSIDE
itself, so a coordinated tamper could edit manifest + constant together and
pass every in-repo check. This module enforces the dual anchor added by the
audit fix: the same canonical hashes are pinned in
framework/sps2/governance/manifest-anchors.env (consumed by the sps-ci.yml validator-battery
step) and cross-checked here. A coordinated edit must now touch the
manifest, the module constant, AND the anchors file before anything drifts
silently — this test asserts equality among those three surfaces, and the
CI step recomputes from the anchors file independently. Accepted residual:
anyone with repo write can still edit all of these surfaces; final
detection remains git history + PR review.

WHY framework/sps2/governance/manifest-anchors.env AND NOT literals in sps-ci.yml itself:
sps-ci.yml is pinned in the legacy manifest, so embedding manifest hashes
in it would self-reference (workflow pins manifest hash; manifest pins
workflow bytes) and never converge. The anchors file is also pinned but
contains only hashes of other files — no cycle.
"""
import hashlib
import json
import re
import unittest
from pathlib import Path

from framework.sps2.governance import import_exceptions, legacy_exceptions

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "sps-ci.yml"
ANCHORS_FILE = REPO_ROOT / "framework" / "sps2" / "governance" / "manifest-anchors.env"

# Anchor lines in manifest-anchors.env: "<manifest-path>:<64-hex>".
_ANCHOR_LINE = re.compile(r"^(?P<manifest>[^#\s][^:]*):(?P<hash>[0-9a-f]{64})$", re.M)


def _canonical_sha256(path: Path) -> str:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    canon = json.dumps(parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _anchors() -> dict[str, str]:
    anchors: dict[str, str] = {}
    for match in _ANCHOR_LINE.finditer(ANCHORS_FILE.read_text(encoding="utf-8")):
        anchors[match.group("manifest")] = match.group("hash")
    return anchors


class TestAnchorsFileIsWired(unittest.TestCase):
    """The anchors file must exist, parse, and be consumed by the workflow."""

    def test_anchors_file_has_both_manifests(self):
        anchors = _anchors()
        self.assertIn(
            "framework/sps2/governance/legacy-exception-manifest.json", anchors
        )
        self.assertIn(
            "framework/sps2/governance/p10-p9-import-exception-manifest.json", anchors
        )

    def test_workflow_reads_the_anchors_file(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("manifest-anchors.env", text)
        self.assertIn("Governance manifest trust anchors", text)


class TestLegacyManifestAnchor(unittest.TestCase):
    """DEC-7301 legacy-exception manifest: module, anchors file, content agree."""

    MANIFEST_PATH = "framework/sps2/governance/legacy-exception-manifest.json"

    def _manifest(self) -> Path:
        return REPO_ROOT / self.MANIFEST_PATH

    def test_module_constant_matches_manifest_content(self):
        self.assertEqual(
            legacy_exceptions.EXPECTED_MANIFEST_SHA256,
            _canonical_sha256(self._manifest()),
        )

    def test_anchors_file_literal_matches_module_constant(self):
        anchors = _anchors()
        self.assertIn(self.MANIFEST_PATH, anchors, "anchor missing from manifest-anchors.env")
        self.assertEqual(
            anchors[self.MANIFEST_PATH],
            legacy_exceptions.EXPECTED_MANIFEST_SHA256,
        )


class TestImportManifestAnchor(unittest.TestCase):
    """DEC-7302 import-exception manifest: same dual-anchor contract."""

    MANIFEST_PATH = "framework/sps2/governance/p10-p9-import-exception-manifest.json"

    def _manifest(self) -> Path:
        return REPO_ROOT / self.MANIFEST_PATH

    def test_module_constant_matches_manifest_content(self):
        self.assertEqual(
            import_exceptions.EXPECTED_MANIFEST_SHA256,
            _canonical_sha256(self._manifest()),
        )

    def test_anchors_file_literal_matches_module_constant(self):
        anchors = _anchors()
        self.assertIn(self.MANIFEST_PATH, anchors, "anchor missing from manifest-anchors.env")
        self.assertEqual(
            anchors[self.MANIFEST_PATH],
            import_exceptions.EXPECTED_MANIFEST_SHA256,
        )


if __name__ == "__main__":
    unittest.main()
